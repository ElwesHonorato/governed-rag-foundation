# RAG Architecture Blueprint

## A-01 High-Level Flow
1. Ingest from documents, databases, streams, and APIs.
2. Clean, normalize, parse, and chunk by format.
3. Apply masking and governance transforms.
4. Generate embeddings and persist vectors + metadata.
5. Execute hybrid retrieval with authorization filters.
6. Generate grounded responses with source traceability.

## A-02 Processing Design
- Prefer context-aware chunking (recursive/semantic) over fixed-size windows.
- Use parent-child indexing: retrieve child chunks, expand with parent context for generation.
- Maintain versioned indexing for traceable responses.
