from datahub.metadata.urns import DataFlowUrn, DataJobUrn, DataProcessInstanceUrn, DatasetUrn


class DataHubUrnFactory:
    """Centralized builders for DataHub URN values."""

    @staticmethod
    def flow_urn(*, flow_platform: str, flow_id: str, flow_instance: str) -> str:
        return DataFlowUrn(
            orchestrator=flow_platform,
            flow_id=f"{flow_instance}.{flow_id}",
            cluster=flow_instance,
        ).urn()

    @staticmethod
    def job_urn(*, flow_platform: str, flow_id: str, flow_instance: str, job_id: str) -> str:
        flow_urn = DataHubUrnFactory.flow_urn(
            flow_platform=flow_platform,
            flow_id=flow_id,
            flow_instance=flow_instance,
        )
        return DataJobUrn(flow=flow_urn, job_id=job_id).urn()

    @staticmethod
    def dataset_urn(*, platform: str, name: str, env: str) -> DatasetUrn:
        return DatasetUrn(platform=platform, name=name, env=env)

    @staticmethod
    def data_process_instance_urn(*, run_id: str) -> str:
        return DataProcessInstanceUrn(run_id).urn()
