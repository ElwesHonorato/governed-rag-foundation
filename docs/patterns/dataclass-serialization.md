# Dataclass Serialization

## Intent

Keep serialization explicit, predictable, and owned by the contract class by exposing well-defined serialization views for full objects and transport-specific payloads.

## Core Rule

Serialization shape must be defined by the contract class that owns the data, not by the caller.

Callers may choose which serialization view to use, but must never manually reconstruct dictionaries or extract nested fields to build payloads.

## When To Use

- Dataclass-based contracts exchanged between workers.
- Objects persisted to storage (S3, MinIO, filesystem).
- Queue messages or transport payloads.
- Any object whose serialized shape must remain stable across services.

## Serialization Views

Contracts should expose explicit serialization views on the contract class.

### Full Object Serialization

Returns the entire dataclass structure.

Use when:

- persisting full objects
- debugging
- logging
- lineage metadata

### Transport / Payload Serialization

Returns the serialized structure intended for transport or storage.

Use when:

- writing objects to storage
- sending queue messages
- emitting artifact bodies

## Example

Write sites then become simple and predictable:

```python
@dataclass(frozen=True)
class ChunkRecord:
    index: int
    chunk_id: str
    chunk_text: str


@dataclass(frozen=True)
class ChunkArtifact:
    chunk_record: ChunkRecord
    destination_key: str

    @property
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @property
    def to_payload(self) -> dict[str, Any]:
        return asdict(self.chunk_record)

    @classmethod
    def from_dict(cls, payload: dict[str, Any], *, destination_key: str) -> "ChunkArtifact":
        return cls(
            chunk_record=ChunkRecord(**payload),
            destination_key=destination_key,
        )
```

```python
self.object_storage.write_object(
    bucket=self.storage_bucket,
    key=chunk_artifact.destination_key,
    payload=json.dumps(chunk_artifact.to_payload).encode("utf-8"),
    content_type="application/json",
)
```

## Naming Guidelines

Use consistent serialization names across the repository:

| Method | Purpose |
| --- | --- |
| `to_dict` | Full object serialization |
| `to_payload` | Transport or storage body |
| `from_dict()` | Reconstruct object from serialized form |

## Deserialization Rule

In `from_dict`, unpack directly from mapping entries when input fields are already dictionaries.

Preferred:

```python
return cls(
    root_metadata=RootDocumentMetadata(**payload["root_metadata"]),
    content=content_type(**payload["content"]),
    processor_metadata=ProcessorMetadata(**payload["processor_metadata"]),
)
```

Avoid redundant wrappers like `dict(payload["root_metadata"])` unless you explicitly need to force a copy or normalize a non-dict mapping type.

## Anti-Patterns

### Rebuilding dictionaries at write sites

Bad:

```python
payload = {
    "index": chunk_artifact.chunk_record.index,
    "chunk_id": chunk_artifact.chunk_record.chunk_id,
    "chunk_text": chunk_artifact.chunk_record.chunk_text,
}
```

Good:

```python
payload = chunk_artifact.to_payload
```

### Extracting nested structures from serialized objects

Bad:

```python
payload = chunk_artifact.to_dict["chunk_record"]
```

Good:

```python
payload = chunk_artifact.to_payload
```

### Returning partial content from to_dict()

`to_dict` must always return the complete object representation.

Partial serialization belongs in a dedicated view like `to_payload`.

### Inline serialization logic

Avoid:

```python
body = json.dumps(
    {
        "chunk_id": artifact.chunk_record.chunk_id,
        "chunk_text": artifact.chunk_record.chunk_text,
    },
    sort_keys=True,
)
```

Instead:

```python
body = json.dumps(artifact.to_payload, sort_keys=True)
```

## Nested Dataclasses

Nested dataclasses are expected and intentional.
`asdict()` will recursively serialize nested objects.

Example:

```python
@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: str


@dataclass(frozen=True)
class ChunkArtifact:
    chunk_record: ChunkRecord
    destination_key: str
```

Serialized:

```python
asdict(
    ChunkArtifact(
        chunk_record=ChunkRecord(chunk_id="abc123"),
        destination_key="chunks/doc-1/chunk=abc123.json",
    )
)
# {
#   "chunk_record": {"chunk_id": "abc123"},
#   "destination_key": "chunks/doc-1/chunk=abc123.json"
# }
```

## Design Principles

Serialization should be:

- Explicit — shapes defined by contract classes.
- Centralized — serialization logic lives with the data model.
- Reusable — callers reuse serialization views instead of rebuilding structures.
- Stable — schema changes occur in one place and propagate safely.

## Compatibility Rule

Do not add backward-compatibility shims inside serialization logic.

- No dual-read or dual-write payload handling in `to_payload()` / `from_dict()`.
- No fallback parsing for old keys or alternate shapes.
- Validate the current contract shape and fail fast when data does not match.

Bad:

```python
if "metadata" in payload:
    ...
elif "root_metadata" in payload:
    ...
```

Good:

```python
metadata_payload = payload["metadata"]
return cls(
    metadata=StageArtifactMetadata(
        processor=ProcessorMetadata(**metadata_payload["processor"]),
        root=RootDocumentMetadata(**metadata_payload["root"]),
        content=metadata_payload["content"],
        params=metadata_payload["params"],
    ),
    content=content_type(**payload["content"]),
)
```

## Notes

- Contract breaks are acceptable when explicitly requested; update all call sites in the same change.
- Avoid adding new serialization views unless a new transport or persistence shape is required.
