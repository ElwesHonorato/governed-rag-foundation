# Acceptance Criteria - Global Logistics Intelligence Hub

## AC-01 Ingestion Coverage
- System ingests from all defined source classes (unstructured, structured, streams, APIs, DB).

## AC-02 Data Normalization
- Canonical schema successfully maps equivalent fields from distinct systems.

## AC-03 Retrieval Quality
- Hybrid retrieval returns relevant, source-cited results for shipment, contract, and IoT queries.

## AC-04 Governance and Lineage
- Every response can be traced back to source document/version and processing path.

## AC-05 Security
- Masking prevents sensitive fields from entering vector storage in raw form.
- RBAC prevents unauthorized document retrieval.

## AC-06 Scale
- Platform demonstrates stable behavior for 1,000+ active users with acceptable latency.
