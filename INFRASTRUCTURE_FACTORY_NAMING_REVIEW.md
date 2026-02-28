# InfrastructureFactory Naming Review

## User Concerns
- `InfrastructureFactory` method names are not fully consistent.
- `create` prefix may not always be the right semantic choice.
- Several methods produce objects that feel conceptually similar (e.g., client/gateway-like outputs), so naming should follow a coherent taxonomy.
- Avoid vague, mixed naming styles and clarify whether outputs are `client`, `gateway`, `handler`, or another stable category.
- Prefer design-pattern-strong naming, not ad-hoc naming.

## Current Code Sample
From `libs/pipeline-common/src/pipeline_common/startup.py`:

```python
class InfrastructureFactory:
    """Factory for queue and object storage infrastructure clients."""

    def __init__(self, runtime_context: WorkerRuntimeContext) -> None:
        self.runtime_context = runtime_context
        self.datahub_lineage_client = self._create_datahub_lineage_client()
        self.job_properties = self._parse_job_properties()
        self.object_storage = self._create_object_storage()
        self.stage_queue = self._create_stage_queue()

    def _create_datahub_lineage_client(self) -> DataHubRunTimeLineage:
        """Create DataHub runtime lineage client for this worker."""
        return DataHubRunTimeLineage(
            client_config=DataHubLineageRuntimeConfig(
                connection_settings=DataHubRuntimeConnectionSettings(
                    server=self.runtime_context.datahub_settings.server,
                    env=self.runtime_context.datahub_settings.env,
                    token=self.runtime_context.datahub_settings.token,
                    timeout_sec=self.runtime_context.datahub_settings.timeout_sec,
                    retry_max_times=self.runtime_context.datahub_settings.retry_max_times,
                ),
                data_job_key=self.runtime_context.data_job_key,
            )
        )

    def _parse_job_properties(self) -> dict[str, Any]:
        """Create nested job properties from DataHub custom properties."""
        custom_properties = self.datahub_lineage_client.resolved_job_config.custom_properties
        return JobPropertiesParser(custom_properties).job_properties

    def _create_stage_queue(self) -> StageQueue:
        """Create queue gateway from job queue config."""
        queue_config = self.job_properties["job"]["queue"]
        return StageQueue(
            self.runtime_context.queue_settings.broker_url,
            queue_config=queue_config,
        )

    def _create_object_storage(self) -> ObjectStorageGateway:
        """Create object storage gateway from S3 settings."""
        return ObjectStorageGateway(
            S3Client(
                endpoint_url=self.runtime_context.s3_settings.s3_endpoint,
                access_key=self.runtime_context.s3_settings.s3_access_key,
                secret_key=self.runtime_context.s3_settings.s3_secret_key,
                region_name=self.runtime_context.s3_settings.aws_region,
            )
        )
```

## Open Questions To Resolve
- Should naming align by operation (`create/parse/resolve`) or by output role (`*_client`, `*_gateway`)?
- Is `job_properties` a data product of this factory, or should it move to a dedicated parser/loader object?
- Should `DataHubRunTimeLineage` be treated as a `client`, `gateway`, or domain service in naming?
- Should `StageQueue` and `ObjectStorageGateway` be named with consistent suffixes in public attributes?
