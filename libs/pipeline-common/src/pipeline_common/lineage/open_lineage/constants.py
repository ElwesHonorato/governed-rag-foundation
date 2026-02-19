from enum import Enum


class EventType(str, Enum):
    START = "START"
    COMPLETE = "COMPLETE"
    FAIL = "FAIL"


class LineageNamespace(str, Enum):
    GOVERNED_RAG = "governed-rag"


class OpenLineageSchemaUrl(str, Enum):
    RUN_EVENT = "https://openlineage.io/spec/1-0-5/OpenLineage.json#/definitions/RunEvent"
    ERROR_MESSAGE_RUN_FACET = "https://openlineage.io/spec/facets/1-0-0/ErrorMessageRunFacet.json"
