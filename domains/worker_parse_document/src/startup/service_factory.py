"""Service graph assembly for worker_parse_document startup."""

from contracts.contracts import ParseProcessingConfigContract, ParseSecurityConfigContract, ParseWorkerConfigContract
from parsing.registry import ParserRegistry
from pipeline_common.startup import WorkerRuntimeContext, WorkerServiceFactory
from services.worker_parse_document_service import WorkerParseDocumentService


class ParseServiceFactory(WorkerServiceFactory[ParseWorkerConfigContract, WorkerParseDocumentService]):
    """Build parse service from runtime context and typed parse config."""

    def __init__(self, *, parser_registry: ParserRegistry) -> None:
        self._parser_registry = parser_registry

    def build(
        self,
        runtime: WorkerRuntimeContext,
        worker_config: ParseWorkerConfigContract,
    ) -> WorkerParseDocumentService:
        """Construct worker parse service object graph."""
        security_config: ParseSecurityConfigContract = ParseSecurityConfigContract(
            clearance=worker_config.security_clearance
        )
        processing_config: ParseProcessingConfigContract = ParseProcessingConfigContract(
            poll_interval_seconds=worker_config.poll_interval_seconds,
            queue=worker_config.queue_config,
            storage=worker_config.storage,
            security=security_config,
        )
        return WorkerParseDocumentService(
            stage_queue=runtime.stage_queue_gateway,
            object_storage=runtime.object_storage_gateway,
            lineage=runtime.lineage_gateway,
            processing_config=processing_config,
            parser_registry=self._parser_registry,
        )
