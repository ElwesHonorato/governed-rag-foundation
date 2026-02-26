from .api import MarquezApiClient

__all__ = ["MarquezApiClient"]

# Keep legacy Marquez tooling importable even when DataHub extras are not installed.
try:
    from .contracts import DataHubDataJobKey, DatasetPlatform, ResolvedDataHubFlowConfig
    from .data_hub import DataHubGraphClient, DataHubJobMetadataResolver, DataHubRunTimeLineage
except ModuleNotFoundError:
    pass
else:
    __all__.extend(
        [
            "DataHubGraphClient",
            "DataHubRunTimeLineage",
            "DataHubJobMetadataResolver",
            "DatasetPlatform",
            "DataHubDataJobKey",
            "ResolvedDataHubFlowConfig",
        ]
    )
