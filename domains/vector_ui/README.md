# vector_ui domain

This domain is a friendly inspection tool for retrieval data. It helps you quickly check what is indexed in Weaviate and how queries resolve.

## Deep Dive

### What runs here
- `vector-ui` app from `apps/vector-ui`

### How it contributes to RAG
- Provides manual query/filter/sort workflows against chunk records.
- Helps validate indexing quality and metadata correctness.
- Speeds up debugging of retrieval relevance issues.

### Runtime dependencies
- Requires `WEAVIATE_URL` to query the vector store.

### Interface
- HTTP UI/API on `${VECTOR_UI_PORT}:8000`.
- Primary app endpoint: `/`
- Query endpoint: `POST /query`
