# Third-Party License Notes

This project depends on third-party software with different license types.
Use this file as a practical portfolio publishing checklist, not legal advice.

Primary evidence and source links:
- `docs/compliance/OSS_LICENSE_EVIDENCE.md`

## Quick Risk View

Higher-risk licenses for public redistribution/commercial reuse:
- AGPL-3.0: MinIO
- GPL-2.0: MySQL
- GPL-3.0: Neo4j Community
- ELv2 (source-available): Elasticsearch default distribution
- Confluent Community License (source-available): Schema Registry image line

Moderate or conditional review licenses:
- MPL-2.0: RabbitMQ
- Confluent image bundles: review image notices and included components

Generally permissive licenses in current inventory:
- Apache-2.0
- MIT
- BSD-3-Clause
- zlib
- PSF

## Portfolio Publishing Recommendations

To reduce exposure when publishing this repository:
1. Publish source and instructions; do not publish prebuilt container images that include restricted components.
2. Keep restricted services scoped as local DEV/demo usage in docs.
3. Record exact third-party components and versions used by your demo.
4. Replace high-risk components with permissive alternatives where practical.
5. Re-run license checks before major dependency/image updates.

## Intended Scope

Current project intent is local development and educational demonstration.
Any production or commercial usage should be preceded by a formal legal/license review.
