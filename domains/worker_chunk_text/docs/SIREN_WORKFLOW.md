# worker_chunk_text Workflow Variants

This file gives the same current runtime behavior in four different styles so you can choose the one you prefer.

---

## A) Flowchart Style

```mermaid
flowchart TD
    A[wait_for_message] --> B[parse envelope payload as input URI]
    B --> C[start_run and add_input]
    C --> D[read input artifact from storage]
    D --> E[build run_id and resolve chunking stages]
    E --> F[split text into chunk documents]
    F --> G[write each chunk artifact and enqueue its URI]
    G --> H[write manifest]
    H --> I[add manifest lineage output]
    I --> J[complete_run]
    J --> K[ack]
    K --> A

    D -. exception .-> X[fail_run]
    E -. exception .-> X
    F -. exception .-> X
    G -. exception .-> X
    H -. exception .-> X
    X --> Y[nack requeue=false]
    Y --> A
```

---

## B) State Diagram Style

```mermaid
stateDiagram-v2
    [*] --> Polling

    Polling --> Parsing: message received
    Parsing --> Running: input URI extracted
    Running --> Chunking: stages resolved
    Chunking --> Persisting: chunk artifacts written
    Persisting --> Manifesting: manifest written
    Manifesting --> Acked: lineage completed and message acked
    Acked --> Polling

    Running --> Failed: exception
    Chunking --> Failed: exception
    Persisting --> Failed: exception
    Manifesting --> Failed: exception

    Failed --> Rejected: fail_run and nack requeue=false
    Rejected --> Polling
```

---

## C) Swimlane Activity Style

```mermaid
flowchart LR
    subgraph Q[Queue]
        Q1[wait_for_message]
        Q2[ack]
        Q3[nack requeue=false]
        Q4[push downstream chunk URI]
    end

    subgraph S[Worker Service]
        S1[parse envelope]
        S2[start_run and add_input]
        S3[start_run + add_input]
        S4[resolve stages and process chunks]
        S5[write manifest and complete_run]
        S6[fail_run]
    end

    subgraph O[Object Storage]
        O1[read processed artifact]
        O2[write chunk object]
        O3[write manifest]
    end

    subgraph L[Lineage]
        L1[add input artifact]
        L2[add manifest output]
    end

    Q1 --> S1
    S1 --> S2 --> L1 --> O1 --> S4 --> O2 --> Q4 --> O3 --> L2 --> S5 --> Q2

    O1 -.error.-> S6
    S4 -.error.-> S6
    O2 -.error.-> S6
    O3 -.error.-> S6
    S6 --> Q3
```

---

## D) Plain Step-by-Step (No Diagram)

1. Worker loops forever and calls `stage_queue.pop_message()`.
2. Worker parses the queue envelope and treats the payload as an input artifact URI.
3. Worker starts a lineage run and adds the input URI as an input dataset.
4. Worker reads the upstream stage artifact from object storage.
5. Worker generates a run ID from the source URI.
6. Worker resolves chunking stages from `root_doc_metadata.source_type`.
7. Worker applies the configured LangChain splitters to the source text.
8. For each chunk produced:
   - computes a deterministic `chunk_id`,
   - writes one chunk artifact object,
   - publishes the chunk URI to the downstream queue.
9. Worker writes a manifest for the process result.
10. Worker adds the manifest URI as a lineage output and completes the run.
11. Worker `ack()`s the consumed message.
12. On any processing exception:
   - marks the lineage run as failed,
   - `nack(requeue=false)`s the original message.

---

## Notes

- This reflects current code behavior in `src/service/worker_chunk_text_service.py` and `src/service/chunk_text_processor.py`.
- This reflects current code behavior in `src/service/worker_chunking_service.py` and `src/processor/chunk_text.py`.
- The four views above are equivalent descriptions of the same runtime flow.
