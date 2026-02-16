import json
import logging
import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, TypedDict
from urllib import error, request

from pipeline_common.config import JobStageName
from pipeline_common.contracts import utc_now_iso
from pipeline_common.settings import LineageEmitterSettings
from .constants import EventType, OpenLineageSchemaUrl
from .contracts import LineageEmitterConfig

logger = logging.getLogger(__name__)


class OpenLineageDataset(TypedDict, total=False):
    """Typed shape for one OpenLineage dataset descriptor."""

    namespace: str
    name: str
    facets: Mapping[str, Any]


@dataclass(init=False)
class LineageEmitter:
    """Best-effort OpenLineage emitter for Marquez."""

    lineage_url: str
    namespace: str
    producer: str
    timeout_seconds: float
    job_stage: JobStageName | None = None
    dataset_namespace: str | None = None
    run_id: str | None = None
    run_facets: dict[str, Any] = field(default_factory=dict)
    inputs: list[OpenLineageDataset] = field(default_factory=list)
    outputs: list[OpenLineageDataset] = field(default_factory=list)

    def __init__(
        self,
        lineage_settings: LineageEmitterSettings,
        lineage_config: LineageEmitterConfig,
    ) -> None:
        """Build lineage emitter from runtime settings and lineage config."""
        self._init_lineage_settings(lineage_settings)
        self._init_lineage_config(lineage_config)
        self._init_run_state()

    def generate_run_id(self) -> None:
        """Create a new lineage run id, store it, and reset input/output state."""
        self.reset_io()
        self.run_id = str(uuid.uuid4())

    def start_run(
        self,
        job_stage: str | JobStageName | None = None,
        run_facets: Mapping[str, Any] | None = None,
    ) -> None:
        """Create run id and emit START event."""
        if job_stage is not None:
            self.job_stage = job_stage
        self.generate_run_id()
        self.set_run_facets(run_facets or {})
        self.emit_start()

    def complete_run(self) -> None:
        """Emit COMPLETE event for the current in-memory run state."""
        self.emit_complete()

    def fail_run(
        self,
        error_message: str,
        run_id: str | None = None,
    ) -> None:
        """Emit FAIL event for one run id."""
        if run_id is not None:
            self.run_id = run_id
        self.emit_fail(error_message=error_message)

    def reset_io(self) -> None:
        """Clear current input/output lineage datasets for one run."""
        self.run_id = None
        self.run_facets = {}
        self.inputs.clear()
        self.outputs.clear()

    def set_run_facets(self, run_facets: Mapping[str, Any]) -> None:
        """Set run facets that will be attached to START/COMPLETE/FAIL events for one run."""
        self.run_facets = self._run_facets(run_facets)

    def add_input(
        self,
        dataset: OpenLineageDataset,
    ) -> None:
        """Add one OpenLineage input dataset descriptor."""
        self.inputs.append(self._dataset(dataset))

    def add_output(
        self,
        dataset: OpenLineageDataset,
    ) -> None:
        """Add one OpenLineage output dataset descriptor."""
        self.outputs.append(self._dataset(dataset))

    def emit_start(self) -> None:
        """Emit START run event."""
        self.emit_event(
            event_type=EventType.START,
            run_facets=self.run_facets,
        )

    def emit_complete(self) -> None:
        """Emit COMPLETE run event."""
        self.emit_event(
            event_type=EventType.COMPLETE,
            run_facets=self.run_facets,
        )

    def emit_fail(
        self,
        error_message: str,
    ) -> None:
        """Emit FAIL run event with error facet."""
        run_facets = dict(self.run_facets)
        run_facets.update(self.build_error_message_facet(error_message))
        self.emit_event(
            event_type=EventType.FAIL,
            run_facets=run_facets,
        )

    def emit_event(
        self,
        event_type: EventType,
        run_facets: Mapping[str, Any],
    ) -> None:
        """Best-effort event sender for one OpenLineage event."""
        try:
            payload = self.build_run_event_payload(
                event_type=event_type,
                run_facets=run_facets,
            )
            self._post(payload)
        except OSError as exc:
            logger.warning("Lineage emit failed: %s", exc)

    def build_run_event_payload(
        self,
        event_type: EventType,
        run_facets: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Build one OpenLineage RunEvent payload without side effects."""
        if self.run_id is None:
            raise ValueError("run_id is not set; call start_run() before emitting events")
        return {
            "eventType": event_type.value,
            "eventTime": utc_now_iso(),
            "run": {"runId": self.run_id, "facets": self._run_facets(run_facets)},
            "job": {"namespace": self._job_namespace(), "name": self._job_name()},
            "producer": self.producer,
            "schemaURL": OpenLineageSchemaUrl.RUN_EVENT.value,
            "inputs": self.inputs,
            "outputs": self.outputs,
        }

    def build_error_message_facet(self, error_message: str) -> dict[str, Any]:
        """Build OpenLineage errorMessage run facet payload."""
        return {
            "errorMessage": {
                "_producer": self.producer,
                "_schemaURL": OpenLineageSchemaUrl.ERROR_MESSAGE_RUN_FACET.value,
                "message": error_message,
                "programmingLanguage": "python",
            }
        }

    def _init_lineage_settings(self, lineage_settings: LineageEmitterSettings) -> None:
        self.lineage_url = lineage_settings.lineage_url

    def _init_lineage_config(self, lineage_config: LineageEmitterConfig) -> None:
        self.namespace = str(lineage_config.namespace).strip()
        if not self.namespace:
            raise ValueError("LineageEmitterConfig.namespace must be a non-empty string")
        self.producer = str(lineage_config.producer).strip()
        if not self.producer:
            raise ValueError("LineageEmitterConfig.producer must be a non-empty string")
        self.job_stage = lineage_config.job_stage
        self.dataset_namespace = self._dataset_namespace(lineage_config.dataset_namespace)
        self.timeout_seconds = lineage_config.timeout_seconds

    def _init_run_state(self) -> None:
        self.run_id = None
        self.run_facets = {}
        self.inputs = []
        self.outputs = []

    def _dataset(self, dataset: OpenLineageDataset) -> OpenLineageDataset:
        facets = dataset.get("facets")
        namespace_value = dataset.get("namespace", self.dataset_namespace)
        if namespace_value is None:
            raise ValueError("Dataset namespace is missing and no default dataset_namespace is configured")
        namespace = self._canonical_namespace(str(namespace_value))
        name = str(dataset.get("name", "")).strip()
        if not name:
            raise ValueError("Dataset name is missing")
        dataset_payload: OpenLineageDataset = {
            "namespace": namespace,
            "name": name,
        }
        if facets:
            dataset_payload["facets"] = facets
        return dataset_payload

    def _job_namespace(self) -> str:
        namespace = str(self.namespace).strip()
        if not namespace:
            raise ValueError("Job namespace is missing")
        return namespace

    def _job_name(self) -> str:
        if self.job_stage is None:
            raise ValueError("Job name is missing; configure job_stage or pass job_stage to start_run()")
        if isinstance(self.job_stage, JobStageName):
            name = self.job_stage.value
        else:
            name = str(self.job_stage).strip()
        if not name:
            raise ValueError("Job name is missing")
        return name

    def _run_facets(self, run_facets: Mapping[str, Any]) -> dict[str, Any]:
        facets: dict[str, Any] = {}
        for facet_name, facet_payload in run_facets.items():
            if not isinstance(facet_payload, Mapping):
                raise ValueError(f"Run facet '{facet_name}' must be an object")
            if facet_name != "errorMessage":
                if "_producer" not in facet_payload or "_schemaURL" not in facet_payload:
                    raise ValueError(
                        f"Run facet '{facet_name}' must include _producer and _schemaURL"
                    )
            facets[str(facet_name)] = dict(facet_payload)
        return facets

    def _dataset_namespace(self, dataset_namespace: str | None) -> str | None:
        if dataset_namespace is None:
            return None
        return self._canonical_namespace(dataset_namespace)

    def _canonical_namespace(self, namespace: str) -> str:
        normalized = str(namespace).strip()
        if not normalized:
            raise ValueError("Dataset namespace must be a non-empty string")
        if normalized.startswith("s3://"):
            return normalized.rstrip("/")
        return normalized

    def _post(self, payload: dict[str, Any]) -> None:
        """Send one event payload to Marquez."""
        if not self.lineage_url:
            return
        req = request.Request(
            url=self.lineage_url,
            method="POST",
            data=json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        try:
            with request.urlopen(req, timeout=self.timeout_seconds):
                return
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            logger.warning("Lineage emit failed HTTP %s: %s", exc.code, body)
        except (error.URLError, OSError) as exc:
            logger.warning("Lineage emit failed: %s", exc)
