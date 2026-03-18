# infra_elasticsearch domain

This domain provides local Elasticsearch infrastructure for a standalone proof of concept.

## Deep Dive

### What runs here
- `elasticsearch` (`docker.elastic.co/elasticsearch/elasticsearch:8.17.2`)

### What this is
- A local-only Elasticsearch sandbox for indexing and querying chunk-like documents.
- An isolated spike environment for interview prep and hands-on exploration.

### What this is not
- Not part of the governed RAG production flow.
- Not wired into current workers, gateways, retrieval, or startup paths.

### Runtime dependencies
- `ELASTICSEARCH_HTTP_PORT` for the host-mapped HTTP port.
- No shared stack network is required for this isolated spike.

### Interface
- Elasticsearch HTTP API on `${ELASTICSEARCH_HTTP_PORT:-9201}:9200`.

### Start locally

```bash
docker compose -f domains/infra_elasticsearch/docker-compose.yml up -d
docker compose -f domains/infra_elasticsearch/docker-compose.yml logs -f
docker compose -f domains/infra_elasticsearch/docker-compose.yml down
```
