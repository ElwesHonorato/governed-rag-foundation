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
    run_id: str | None = None
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
    ) -> None:
        """Create run id and emit START event."""
        if job_stage is not None:
            self.job_stage = job_stage
        self.generate_run_id()
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
        self.inputs.clear()
        self.outputs.clear()

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
            run_facets={},
        )

    def emit_complete(self) -> None:
        """Emit COMPLETE run event."""
        self.emit_event(
            event_type=EventType.COMPLETE,
            run_facets={},
        )

    def emit_fail(
        self,
        error_message: str,
    ) -> None:
        """Emit FAIL run event with error facet."""
        self.emit_event(
            event_type=EventType.FAIL,
            run_facets=self.build_error_message_facet(error_message),
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
        return {
            "eventType": event_type.value,
            "eventTime": utc_now_iso(),
            "run": {"runId": self.run_id, "facets": run_facets},
            "job": {"namespace": self.namespace, "name": self.job_stage},
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
        self.namespace = lineage_config.namespace
        self.producer = lineage_config.producer
        self.job_stage = lineage_config.job_stage
        self.timeout_seconds = lineage_config.timeout_seconds

    def _init_run_state(self) -> None:
        self.run_id = None
        self.inputs = []
        self.outputs = []

    def _dataset(self, dataset: OpenLineageDataset) -> OpenLineageDataset:
        facets = dataset.get("facets")
        dataset: OpenLineageDataset = {
            "namespace": dataset.get("namespace","Namespace is missing"),
            "name": dataset.get("name", "Name is missing"),
        }
        if facets:
            dataset["facets"] = facets
        return dataset

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
