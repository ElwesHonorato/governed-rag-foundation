# Open Questions - Global Logistics Intelligence Hub

## Platform Decisions
- Which vector database is primary (Pinecone, Milvus, Weaviate)?
- Which embedding models will be standardized for text and images?
- Is late-interaction retrieval (for example, ColBERT-style) required in V1?

## Operating Constraints
- What are target p95 latency and uptime SLOs?
- What are monthly cost budgets for embeddings, storage, and inference?

## Governance and Security
- Which compliance regimes are in scope (for example, SOC 2, ISO 27001, HIPAA)?
- What exact RBAC role matrix is required per business unit/region?

## Data and Integrations
- What is the source-of-truth priority when systems conflict?
- What refresh/streaming SLAs are required per data source?
- How to store links contained in Word documents in the vector database, and how to extract and retrieve those links reliably at query time?
