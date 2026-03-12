from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class Envelope:
    """Standard queue envelope for worker message transport."""

    payload: Any
    meta: dict[str, Any] | None = None

    @property
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def to_payload(self) -> dict[str, Any]:
        out = {"payload": self.payload}
        if self.meta:
            out["meta"] = self.meta
        return out

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Envelope":
        return cls(
            payload=raw["payload"],
            meta=dict(raw["meta"]) if "meta" in raw else None,
        )
