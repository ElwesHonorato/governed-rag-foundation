from functools import cached_property
from typing import ClassVar

from pipeline_common.stages_contracts.step_00_common import ProcessorMetadata


class BaseProcessor:
    VERSION: ClassVar[str]

    def _build_processor_metadata(self) -> ProcessorMetadata:
        return ProcessorMetadata(
            name=self.__class__.__name__,
            version=self.VERSION,
        )

    @cached_property
    def processor_metadata(self) -> ProcessorMetadata:
        return self._build_processor_metadata()
