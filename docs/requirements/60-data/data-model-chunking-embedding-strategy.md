# Data Requirements - Model, Chunking, and Embeddings

## D-01 Schema Normalization
Centralize schema normalization to align field names across systems, for example:
- `VendorID`
- `Supplier_No`

## D-02 Format-Aware Parsing
- Tables (Excel/PDF): table-aware extraction preserving row/group context.
- Images: generate text summaries with VLMs or store multimodal embeddings.
- Text (Word/PDF): recursive text splitting that preserves paragraph/sentence boundaries.

## D-03 Chunking Strategy
- Semantic chunking for meaning-aware boundaries.
- Parent-child indexing to preserve broad context during answer generation.

## D-04 Embedding Strategy
- Cross-modal embeddings to support text-to-image and mixed-format retrieval.
- Evaluate late-interaction multi-vector retrieval (for example, ColBERT-style) for domain precision.

## D-05 Metadata Enrichment
Each chunk must include:
- `source_type`
- `timestamp`
- `security_clearance`
