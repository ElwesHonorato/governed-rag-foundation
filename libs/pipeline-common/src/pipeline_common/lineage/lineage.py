import json
import logging
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any
from urllib import error, request

from pipeline_common.config import JobStageName
from pipeline_common.contracts import utc_now_iso
from pipeline_common.settings import LineageRuntimeSettings
from .constants import OPENLINEAGE_SCHEMA_URLS

logger = logging.getLogger(__name__)

LineageConfig = dict[str, str | JobStageName]


@dataclass(init=False)
class LineageEmitter:
    """Best-effort OpenLineage emitter for Marquez."""

    enabled: bool
    lineage_url: str
    namespace: str
    producer: str
    timeout_seconds: float
    job_stage: JobStageName | None = None
    run_id: str | None = None
    inputs: list[dict[str, str]] = field(default_factory=list)
    outputs: list[dict[str, str]] = field(default_factory=list)

    def __init__(
        self,
        *,
        lineage_settings: LineageRuntimeSettings,
        lineage_config: LineageConfig,
    ) -> None:
        """Build lineage emitter from runtime settings and lineage config."""
        normalized_url = lineage_settings.lineage_url.strip()
        self.enabled = bool(normalized_url)
        self.lineage_url = normalized_url
        self.namespace = lineage_settings.namespace
        self.producer = str(lineage_config["producer"])
        self.timeout_seconds = lineage_settings.timeout_seconds
        self.job_stage = self._parse_job_stage(lineage_config.get("job_stage"))
        self.run_id = None
        self.inputs = []
        self.outputs = []

    def generate_run_id(self) -> None:
        """Create a new lineage run id, store it, and reset input/output state."""
        self.reset_io()
        self.run_id = str(uuid.uuid4())

    def start_run(
        self,
        *,
        inputs: Sequence[str],
        outputs: Sequence[str] = (),
        job_stage: str | JobStageName | None = None,
    ) -> None:
        """Create run id, register in/out datasets, and emit START event."""
        self.generate_run_id()
        for path in inputs:
            self.add_input(path)
        for path in outputs:
            self.add_output(path)
        self.emit_start(job_stage=job_stage, run_id=self._resolve_run_id(None))

    def complete_run(
        self,
        *,
        run_id: str | None = None,
        inputs: Sequence[str] | None = None,
        outputs: Sequence[str] | None = None,
    ) -> None:
        """Emit COMPLETE event, optionally overriding in/out datasets first."""
        if inputs is not None or outputs is not None:
            self.reset_io()
            for path in inputs or ():
                self.add_input(path)
            for path in outputs or ():
                self.add_output(path)
        self.emit_complete(run_id=self._resolve_run_id(run_id))

    def fail_run(
        self,
        *,
        run_id: str | None = None,
        error_message: str,
    ) -> None:
        """Emit FAIL event for one run id."""
        self.emit_fail(
            run_id=self._resolve_run_id(run_id),
            error_message=error_message,
        )

    def set_job_stage(self, job_stage: JobStageName) -> "LineageEmitter":
        """Set default job stage and return emitter for fluent setup."""
        self.job_stage = job_stage
        return self

    def reset_io(self) -> None:
        """Clear current input/output lineage datasets for one run."""
        self.inputs.clear()
        self.outputs.clear()

    def add_input(self, path: str) -> None:
        """Add one OpenLineage input dataset descriptor from a path."""
        self.inputs.append(self._dataset_from_path(path))

    def add_output(self, path: str) -> None:
        """Add one OpenLineage output dataset descriptor from a path."""
        self.outputs.append(self._dataset_from_path(path))

    @staticmethod
    def _dataset_from_path(path: str) -> dict[str, str]:
        """Build an OpenLineage dataset descriptor from one path string."""
        normalized_path = path.strip()
        if "://" in normalized_path:
            scheme, remainder = normalized_path.split("://", 1)
            if "/" in remainder:
                root, name = remainder.split("/", 1)
                return {"namespace": f"{scheme}://{root}", "name": name}
            return {"namespace": f"{scheme}://{remainder}", "name": ""}
        return {"namespace": "path://", "name": normalized_path}

    def emit_start(
        self,
        *,
        job_stage: str | JobStageName | None = None,
        run_id: str,
    ) -> None:
        """Emit START run event."""
        self._emit(
            event_type="START",
            job_stage=self._resolve_job_stage(job_stage),
            run_id=run_id,
            inputs=self.inputs,
            outputs=self.outputs,
            run_facets={},
        )

    def emit_complete(
        self,
        *,
        job_stage: str | JobStageName | None = None,
        run_id: str,
    ) -> None:
        """Emit COMPLETE run event."""
        try:
            self._emit(
                event_type="COMPLETE",
                job_stage=self._resolve_job_stage(job_stage),
                run_id=run_id,
                inputs=self.inputs,
                outputs=self.outputs,
                run_facets={},
            )
        finally:
            self.reset_io()

    def emit_fail(
        self,
        *,
        job_stage: str | JobStageName | None = None,
        run_id: str,
        error_message: str,
    ) -> None:
        """Emit FAIL run event with error facet."""
        try:
            self._emit(
                event_type="FAIL",
                job_stage=self._resolve_job_stage(job_stage),
                run_id=run_id,
                inputs=self.inputs,
                outputs=self.outputs,
                run_facets={
                    "errorMessage": {
                        "_producer": self.producer,
                        "_schemaURL": OPENLINEAGE_SCHEMA_URLS["error_message_run_facet"],
                        "message": error_message,
                        "programmingLanguage": "python",
                    }
                },
            )
        finally:
            self.reset_io()

    def _emit(
        self,
        *,
        event_type: str,
        job_stage: str,
        run_id: str,
        inputs: list[dict[str, str]],
        outputs: list[dict[str, str]],
        run_facets: dict[str, Any],
    ) -> None:
        """Best-effort event sender."""
        if not self.enabled:
            return

        payload = {
            "eventType": event_type,
            "eventTime": utc_now_iso(),
            "run": {"runId": run_id, "facets": run_facets},
            "job": {"namespace": self.namespace, "name": job_stage},
            "producer": self.producer,
            "schemaURL": OPENLINEAGE_SCHEMA_URLS["run_event"],
            "inputs": list(inputs),
            "outputs": list(outputs),
        }
        self._post(payload)

    def _post(self, payload: dict[str, Any]) -> None:
        """Send one event payload to Marquez."""
        if not self.enabled:
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
        except (error.URLError, OSError, ValueError) as exc:
            logger.warning("Lineage emit failed: %s", exc)

    def _resolve_job_stage(self, explicit_job_stage: str | JobStageName | None) -> str:
        """Resolve job stage from explicit value or configured emitter stage."""
        resolved = explicit_job_stage if explicit_job_stage is not None else self.job_stage
        if resolved is None:
            raise ValueError("lineage job_stage is not configured")
        if isinstance(resolved, JobStageName):
            return resolved.value
        return resolved

    @staticmethod
    def _parse_job_stage(raw_job_stage: str | JobStageName | None) -> JobStageName | None:
        """Normalize job_stage into enum when possible."""
        if raw_job_stage is None:
            return None
        if isinstance(raw_job_stage, JobStageName):
            return raw_job_stage
        return JobStageName(str(raw_job_stage))

    def _resolve_run_id(self, explicit_run_id: str | None) -> str:
        """Resolve run id from explicit value or the emitter current run state."""
        resolved = explicit_run_id if explicit_run_id is not None else self.run_id
        if resolved is None:
            raise ValueError("lineage run_id is not configured")
        return resolved
