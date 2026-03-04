# infra_spark domain

This domain provides a local Spark standalone cluster (master + worker) for worker job submission.

## Deep Dive

### What runs here
- `spark-master` (`apache/spark:3.5.1`)
- `spark-worker` (`apache/spark:3.5.1`)

### Why `apache/spark`
- `apache/spark:3.5.1` is currently resolvable from Docker Hub in this environment.
- Previous `bitnami/spark:3.5.1` reference fails with image-not-found.
- Uses explicit master/worker startup commands, so behavior is deterministic and does not depend on image-specific mode env vars.

### How it contributes to RAG
- Hosts the Spark driver/worker runtime used by workers that enable Spark in their composition roots.
- Exposes a stable master endpoint that workers can target via:
  - `SPARK_MASTER_URL=spark://spark-master:7077` (from containers on `STACK_NETWORK`)
  - `SPARK_MASTER_URL=spark://localhost:${SPARK_MASTER_PORT}` (from local host processes)

### Runtime dependencies
- Shared Docker network `${STACK_NETWORK}`.
- Optional tuning via:
  - `SPARK_WORKER_CORES` (default `2`)
  - `SPARK_WORKER_MEMORY` (default `2G`)

### Interface
- Spark master RPC on `${SPARK_MASTER_PORT:-7077}`.
- Spark master UI on `${SPARK_MASTER_UI_PORT:-8088}`.
- Spark worker UI on `${SPARK_WORKER_UI_PORT:-8089}`.

## Usage

Start Spark infra:
- `./stack.sh up infra_spark`

Check status:
- `./stack.sh ps infra_spark`

View logs:
- `./stack.sh logs infra_spark`

Recommended worker env:
- `SPARK_MASTER_URL=spark://spark-master:7077`

Spark enablement is controlled in worker composition roots through `SettingsRequest(..., spark=True|False)`.
