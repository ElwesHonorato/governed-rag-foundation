
from typing import Protocol


class DocumentParser(Protocol):
    def parse(self, content: str) -> dict[str, str]:
        ...
