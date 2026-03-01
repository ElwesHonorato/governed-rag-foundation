"""DataHub custom property parsing for worker job properties."""

from typing import Any, Mapping


class JobPropertiesParser:
    """Parser for worker DataHub job custom properties."""

    def __init__(self, custom_properties: Mapping[str, str]) -> None:
        self.custom_properties = custom_properties
        self.job_properties = self._build_properties()

    def _set_nested(self, target: dict[str, Any], dotted_key: str, value: str) -> None:
        """Set one dotted key (for example, 'job.storage.bucket') into nested dict."""

        def _insert(node: dict[str, Any], parts: list[str], final_value: str) -> None:
            head = parts[0]
            if len(parts) == 1:
                node[head] = final_value
                return
            child = node.setdefault(head, {})
            _insert(child, parts[1:], final_value)

        _insert(target, dotted_key.split("."), value)

    def _build_properties(self) -> dict[str, Any]:
        """Build nested mapping from dot-notation custom properties."""
        expanded: dict[str, Any] = {}
        for key, value in self.custom_properties.items():
            if "." in key:
                self._set_nested(expanded, key, value)
        return expanded
