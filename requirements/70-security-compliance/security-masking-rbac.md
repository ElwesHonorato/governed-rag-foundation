# Security and Compliance Requirements

## SEC-01 Sensitive Data Masking
Mask PII/PHI before vectorization and vector DB writes, including examples such as:
- Supplier bank details
- Driver phone numbers

## SEC-02 Access Control
Implement RBAC so managers retrieve only documents they are authorized to view.

## SEC-03 Secure Retrieval Enforcement
Apply authorization filters at query time using security metadata tags.
