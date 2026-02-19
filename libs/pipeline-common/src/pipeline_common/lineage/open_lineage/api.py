import json
from urllib import parse, request


class MarquezApiClient:
    """Minimal HTTP client for Marquez lineage API."""

    def __init__(self, base_url: str, timeout_seconds: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _get_json(self, url: str) -> dict:
        req = request.Request(url=url, method="GET")
        with request.urlopen(req, timeout=self.timeout_seconds) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def namespaces(self) -> dict:
        return self._get_json(f"{self.base_url}/namespaces")

    def jobs(self, namespace: str, limit: int = 200) -> dict:
        ns = parse.quote(namespace, safe="")
        return self._get_json(f"{self.base_url}/namespaces/{ns}/jobs?limit={limit}")

    def datasets(self, namespace: str, limit: int = 2000) -> dict:
        ns = parse.quote(namespace, safe="")
        return self._get_json(f"{self.base_url}/namespaces/{ns}/datasets?limit={limit}")

    def search(self, query: str) -> dict:
        encoded_query = parse.urlencode({"q": query})
        return self._get_json(f"{self.base_url}/search?{encoded_query}")
