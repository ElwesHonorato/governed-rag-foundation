# Local Stack Scripts

These scripts centralize local infrastructure lifecycle for development and testing so services can be started consistently as one stack or by domain.

## Usage

```bash
./stack.sh up
./stack.sh down
./stack.sh wipe
./stack.sh up storage
./stack.sh up vector
./stack.sh logs lineage
./stack.sh ps
./stack.sh ps apps
```

## Domain-by-domain start

```bash
./stack.sh up storage
./stack.sh up vector
./stack.sh up lineage
./stack.sh up cache
./stack.sh up apps
```

All domains join the shared external Docker network `rag-local`, so services resolve each other by container service name when started independently.

## Local endpoints

- MinIO console: http://localhost:9001
- Weaviate: http://localhost:8080
- Marquez API: http://localhost:5000
- Marquez UI: http://localhost:3000
- rag-api: http://localhost:8000
