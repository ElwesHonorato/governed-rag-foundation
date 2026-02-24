from datahub.metadata.urns import DataFlowUrn, DataJobUrn, DataProcessInstanceUrn, DatasetUrn


class DataHubUrnFactory:
    """Centralized builders for DataHub URN values."""

    @staticmethod
    def flow_urn(*, flow_platform: str, flow_name: str, flow_instance: str) -> str:
        return DataFlowUrn(
            orchestrator=flow_platform,
            flow_id=f"{flow_instance}.{flow_name}",
            cluster=flow_instance,
        ).urn()

    @staticmethod
    def job_urn(*, flow_platform: str, flow_name: str, flow_instance: str, job_name: str) -> str:
        flow_urn = DataHubUrnFactory.flow_urn(
            flow_platform=flow_platform,
            flow_name=flow_name,
            flow_instance=flow_instance,
        )
        return DataJobUrn(flow=flow_urn, job_id=job_name).urn()

    @staticmethod
    def dataset_urn(*, platform: str, name: str, env: str) -> DatasetUrn:
        return DatasetUrn(platform=platform, name=name, env=env)

    @staticmethod
    def data_process_instance_urn(*, run_id: str) -> str:
        return DataProcessInstanceUrn(run_id).urn()
