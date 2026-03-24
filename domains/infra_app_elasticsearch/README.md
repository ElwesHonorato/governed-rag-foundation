# infra_app_elasticsearch domain

This domain packages the `app_elasticsearch` Python CLI into a containerized runtime.

## Deep Dive

### What runs here
- `app-elasticsearch` built from `domains/infra_app_elasticsearch/Dockerfile`

### What this is
- Infra packaging for the standalone Elasticsearch CLI prototype.
- A compose entrypoint for running the Python commands in the shared stack network.

### What this is not
- Not the Elasticsearch database itself.
- Not the Python source package for the CLI commands.

### Runtime dependencies
- `STACK_NETWORK` for the shared Docker network.
- `ELASTICSEARCH_POC_URL` for the target Elasticsearch endpoint.
- `ELASTICSEARCH_POC_INDEX` for the target index name.
- `ELASTICSEARCH_POC_S3_ENDPOINT`, `ELASTICSEARCH_POC_S3_BUCKET`, `ELASTICSEARCH_POC_S3_PREFIX` for MinIO chunk import.
- `ELASTICSEARCH_POC_S3_ACCESS_KEY`, `ELASTICSEARCH_POC_S3_SECRET_KEY` for MinIO credentials.

### Interface
- Containerized CLI entrypoint for `poetry run elasticsearch-poc*` commands.
