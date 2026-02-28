# infra_portainer domain

This domain is an operational dashboard for the local stack. It is not part of answer generation directly, but it makes running and troubleshooting the RAG environment much easier.

## Deep Dive

### What runs here
- `portainer` (`portainer/portainer-ce@sha256:9012a4256c4632f2c6162da361a4d4db9d6d04800e0db0137de96e31656ab876`)

### How it contributes to RAG
- Lets you inspect container health, logs, and lifecycle.
- Improves operator visibility for app, worker, and infra services.

### Runtime dependencies
- Mounts Docker socket: `/var/run/docker.sock`.
- Persists Portainer data in named volume `portainer-data`.

### Interface
- HTTPS UI on `${PORTAINER_HTTPS_PORT}:9443`.
- HTTP UI on `${PORTAINER_HTTP_PORT}:9000` (mapped from container).
