# OSS License Evidence

Purpose:
- Keep external audit/source links separate from architecture narrative.
- Preserve traceability for legal/procurement review of license assertions.

Scope and discovery method (reviewed 2026-03-02):
- Runtime and app dependencies from `pyproject.toml` files.
- Container software from `domains/*/docker-compose.yml`.
- Base images from `domains/*/Dockerfile`.

Repo evidence locations:
- `pyproject.toml`
- `libs/pipeline-common/pyproject.toml`
- `domains/*/pyproject.toml`
- `domains/*/docker-compose.yml`
- `domains/*/Dockerfile`

## Python/runtime libraries used in this repo

### Python (runtime base image)
- Used in: multiple Dockerfiles (`FROM python:3.11-slim`)
- Upstream: <https://github.com/python/cpython>
- License evidence: <https://github.com/python/cpython/blob/main/LICENSE>
- Observed license: PSF License (Python Software Foundation License)

### Flask
- Used in: `domains/app_rag_api/pyproject.toml`, `domains/app_vector_ui/pyproject.toml`
- Upstream: <https://github.com/pallets/flask>
- License evidence: <https://github.com/pallets/flask/blob/main/LICENSE.txt>
- Observed license: BSD-3-Clause

### Requests
- Used in: `pyproject.toml`
- Upstream: <https://github.com/psf/requests>
- License evidence: <https://github.com/psf/requests/blob/main/LICENSE>
- Observed license: Apache-2.0

### Boto3
- Used in: root and worker/library `pyproject.toml` files
- Upstream: <https://github.com/boto/boto3>
- License evidence: <https://github.com/boto/boto3/blob/develop/LICENSE>
- Observed license: Apache-2.0

### Pika
- Used in: worker/library `pyproject.toml` files
- Upstream: <https://github.com/pika/pika>
- License evidence: <https://github.com/pika/pika/blob/main/LICENSE>
- Observed license: BSD-3-Clause

### PyYAML
- Used in: `pyproject.toml`, `libs/pipeline-common/pyproject.toml`
- Upstream: <https://github.com/yaml/pyyaml>
- License evidence: <https://github.com/yaml/pyyaml/blob/main/LICENSE>
- Observed license: MIT

### Trafilatura
- Used in: `domains/worker_parse_document/pyproject.toml`
- Upstream: <https://github.com/adbar/trafilatura>
- License evidence: <https://github.com/adbar/trafilatura/blob/master/LICENSE>
- Observed license: Apache-2.0

### Acryl DataHub Python SDK (`acryl-datahub`)
- Used in: root and worker `pyproject.toml` files
- Upstream: <https://github.com/datahub-project/datahub>
- License evidence: <https://github.com/datahub-project/datahub/blob/master/LICENSE>
- Observed license: Apache-2.0

## Containerized software used in this repo

### DataHub (GMS/Frontend/Actions/Setup images)
- Used in: `domains/infra_lineage/docker-compose.yml` (`acryldata/datahub-*`)
- Upstream: <https://github.com/datahub-project/datahub>
- License evidence: <https://github.com/datahub-project/datahub/blob/master/LICENSE>
- Observed license: Apache-2.0

### Weaviate
- Used in: `domains/infra_vector/docker-compose.yml`
- Upstream: <https://github.com/weaviate/weaviate>
- License evidence: <https://github.com/weaviate/weaviate/blob/main/LICENSE>
- Observed license: BSD-3-Clause

### RabbitMQ
- Used in: `domains/infra_queue/docker-compose.yml`
- Upstream: <https://github.com/rabbitmq/rabbitmq-server>
- License evidence: <https://github.com/rabbitmq/rabbitmq-server>
- Observed license: MPL-2.0

### MinIO
- Used in: `domains/infra_storage/docker-compose.yml`
- Upstream: <https://github.com/minio/minio>
- License evidence: <https://github.com/minio/minio/blob/master/LICENSE>
- Observed license: AGPL-3.0
- Compliance note: non-permissive copyleft; explicit legal review recommended.

### Ollama
- Used in: `domains/infra_llm/Dockerfile`
- Upstream: <https://github.com/ollama/ollama>
- License evidence: <https://github.com/ollama/ollama/blob/main/LICENSE>
- Observed license: MIT

### Portainer CE
- Used in: `domains/infra_portainer/docker-compose.yml`
- Upstream: <https://github.com/portainer/portainer>
- License evidence: <https://github.com/portainer/portainer/blob/develop/LICENSE>
- Observed license: zlib

### Apache Kafka (via `confluentinc/cp-kafka` image)
- Used in: `domains/infra_lineage/docker-compose.yml`
- Upstream core: <https://github.com/apache/kafka>
- License evidence: <https://github.com/apache/kafka/blob/trunk/LICENSE>
- Observed license: Apache-2.0 (Kafka core)
- Compliance note: Confluent images may include mixed licensing; review image notices before production.

### Confluent Schema Registry (via `confluentinc/cp-schema-registry` image)
- Used in: `domains/infra_lineage/docker-compose.yml`
- Upstream docs: <https://docs.confluent.io/platform/current/installation/license.html>
- License evidence: <https://docs.confluent.io/platform/current/installation/license.html>
- Observed license: Confluent Community License
- Compliance note: source-available license; legal review recommended.

### Apache ZooKeeper (via `confluentinc/cp-zookeeper` image)
- Used in: `domains/infra_lineage/docker-compose.yml`
- Upstream core: <https://github.com/apache/zookeeper>
- License evidence: <https://github.com/apache/zookeeper/blob/master/LICENSE.txt>
- Observed license: Apache-2.0 (ZooKeeper core)
- Compliance note: Confluent image packaging may include additional notices.

### Elasticsearch
- Used in: `domains/infra_lineage/docker-compose.yml`
- Upstream: <https://github.com/elastic/elasticsearch>
- License evidence: <https://www.elastic.co/pricing/faq/licensing/>
- Observed license: default distribution under Elastic License 2.0 (ELv2)
- Compliance note: ELv2 is source-available and not an OSI permissive license; legal review required.

### MySQL
- Used in: `domains/infra_lineage/docker-compose.yml`
- Upstream: <https://github.com/mysql/mysql-server>
- License evidence: <https://github.com/mysql/mysql-server/blob/trunk/LICENSE>
- Observed license: GPL-2.0
- Compliance note: copyleft obligations should be reviewed for distribution scenarios.

### Neo4j
- Used in: `domains/infra_lineage/docker-compose.yml`
- Upstream: <https://github.com/neo4j/neo4j>
- License evidence: <https://github.com/neo4j/neo4j>
- Observed license: GPL-3.0 (community codebase)
- Compliance note: copyleft obligations should be reviewed.
