class MetricsCycleProcessor:
    """Compute stage counters from listed storage keys."""

    @staticmethod
    def _count_suffix(keys: list[str], suffix: str) -> int:
        return sum(1 for key in keys if key.endswith(suffix))

    @staticmethod
    def _count_suffixes(keys: list[str], suffixes: tuple[str, ...]) -> int:
        return sum(1 for key in keys if key.endswith(suffixes))

    def build_counts(
        self,
        *,
        processed_keys: list[str],
        chunk_keys: list[str],
        embedding_keys: list[str],
        indexed_keys: list[str],
    ) -> dict[str, int]:
        return {
            "files_processed": self._count_suffix(processed_keys, ".json"),
            "chunks_created": self._count_suffixes(chunk_keys, (".chunk.json", ".chunks.json")),
            "embedding_artifacts": self._count_suffixes(embedding_keys, (".embedding.json", ".embeddings.json")),
            "index_upserts": self._count_suffix(indexed_keys, ".indexed.json"),
        }
