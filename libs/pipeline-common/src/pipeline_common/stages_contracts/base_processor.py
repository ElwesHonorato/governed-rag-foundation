from typing import ClassVar

from pipeline_common.stages_contracts.base import ProcessorMetadata


class BaseProcessor:
    VERSION: ClassVar[str]
    STAGE_NAME: ClassVar[str]

    def _build_processor_metadata(self) -> ProcessorMetadata:
        return ProcessorMetadata(
            name=self.__class__.__name__,
            version=self.VERSION,
            stage_name=self.STAGE_NAME,
        )
