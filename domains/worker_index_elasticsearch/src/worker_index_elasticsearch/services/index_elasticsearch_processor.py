"""Processor that maps chunk ``StageArtifact`` payloads into Elasticsearch documents."""

from __future__ import annotations

import json

from pipeline_common.gateways.elasticsearch import ElasticsearchIndexGateway
from pipeline_common.provenance import chunk_params_hash
from pipeline_common.stages_contracts import ProcessResult, ProcessorContext, StageArtifact
from pipeline_common.stages_contracts.step_00_common import ProcessorMetadata
from worker_index_elasticsearch.services.configs import MAPPER, MapperConfig


class IndexElasticsearchProcessor:
    """Build Elasticsearch documents from chunk-stage payloads and index them."""

    def __init__(
        self,
        *,
        elasticsearch_gateway: ElasticsearchIndexGateway,
    ) -> None:
        """Store Elasticsearch runtime dependency."""
        self._elasticsearch_gateway = elasticsearch_gateway

    def process(self, *, input_uri: str, raw_payload: bytes) -> ProcessResult:
        """Index one chunk payload into Elasticsearch."""
        artifact = StageArtifact.from_dict(json.loads(raw_payload.decode("utf-8")))
        mapper_config = self._mapper_config_for_uri(input_uri)
        document = mapper_config.index_template.map_document(artifact=artifact, artifact_uri=input_uri)
        self._elasticsearch_gateway.index_document(document)
        return ProcessResult(
            run_id=document.chunk_id or document.doc_id,
            root_doc_metadata=artifact.root_doc_metadata,
            stage_doc_metadata=artifact.stage_doc_metadata,
            input_uri=input_uri,
            processor_context=ProcessorContext(
                params_hash=chunk_params_hash(artifact.params),
                params=artifact.params,
            ),
            processor=ProcessorMetadata(name="IndexElasticsearchProcessor", version="1.0.0"),
            result={
                "indexed_document_id": document.document_id,
                "elasticsearch_index": self._elasticsearch_gateway.index_name,
            },
        )

    def _mapper_config_for_uri(self, input_uri: str) -> MapperConfig:
        """Return the configured mapper contract for one chunk artifact URI."""
        return next(
            config
            for uri_prefix, config in MAPPER.items()
            if uri_prefix in input_uri
        )
