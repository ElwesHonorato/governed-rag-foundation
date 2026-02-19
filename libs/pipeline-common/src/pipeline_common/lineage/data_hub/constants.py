from enum import Enum


class EventType(str, Enum):
    START = "START"
    COMPLETE = "COMPLETE"
    FAIL = "FAIL"


class DataHubFlowDefaults:
    PLATFORM = "custom"
    INSTANCE = "PROD"
    ACTOR_URN = "urn:li:corpuser:datahub"
