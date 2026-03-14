import hashlib
from datetime import UTC, datetime


def utc_now_iso() -> str:
    """Execute utc now iso."""
    return datetime.now(tz=UTC).isoformat()


def doc_id_from_source_uri(source_uri: str) -> str:
    """Execute doc id from source uri."""
    digest = hashlib.sha256(source_uri.encode("utf-8")).hexdigest()
    return digest[:24]
