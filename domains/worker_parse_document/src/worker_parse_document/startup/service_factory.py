"""Service graph assembly for worker_parse_document startup."""

from pipeline_common.startup import WorkerRuntimeContext, WorkerServiceFactory
from worker_parse_document.services.parse_flow_components import DocumentParserProcessor
from worker_parse_document.services.parse_output import ParseOutputWriter
from worker_parse_document.services.worker_parse_document_service import WorkerParseDocumentService
from worker_parse_document.startup.contracts import RuntimeParseJobConfig
from worker_parse_document.startup.parser_registry import build_parser_registry


class ParseServiceFactory(WorkerServiceFactory[RuntimeParseJobConfig, WorkerParseDocumentService]):
    """Build parse service from runtime context and typed parse config."""

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: RuntimeParseJobConfig,
    ) -> WorkerParseDocumentService:
        """Construct worker parse service object graph."""
        parser_processor: DocumentParserProcessor = DocumentParserProcessor(
            parser_registry=build_parser_registry(),
            security_clearance=worker_config.security.clearance,
        )
        output_writer: ParseOutputWriter = ParseOutputWriter(
            object_storage=runtime.object_storage_gateway,
            storage_bucket=worker_config.storage.bucket,
        )
        return WorkerParseDocumentService(
            stage_queue=runtime.stage_queue_gateway,
            object_storage=runtime.object_storage_gateway,
            lineage=runtime.lineage_gateway,
            poll_interval_seconds=worker_config.poll_interval_seconds,
            output_prefix=worker_config.storage.output_prefix,
            parser_processor=parser_processor,
            output_writer=output_writer,
        )
