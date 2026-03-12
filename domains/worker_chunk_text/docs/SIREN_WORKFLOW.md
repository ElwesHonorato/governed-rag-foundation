# worker_chunk_text Workflow Variants

This file gives the same current runtime behavior in four different styles so you can choose the one you prefer.

---

## A) Flowchart Style

```mermaid
flowchart TD
    A[pop_message] --> B{Message exists?}
    B -- no --> A
    B -- yes --> C[Parse envelope.source_uri]

    C --> D{Valid payload?}
    D -- no --> D1[push_dlq chunk_text.invalid_message]
    D1 --> D2[ack]
    D2 --> A

    D -- yes --> F[start_run + add_input]

    F --> G[read processed object from storage]
    G --> H[build run_id]
    H --> K[dataframe chunking path]
    K --> L[for each chunk: deterministic chunk_id + chunk object write if missing + registry upsert]

    L --> M[add lineage output for registry prefix]
    M --> N[add lineage outputs for chunk object keys]
    N --> O[complete_run]
    O --> P[enqueue embed_chunks.request for each chunk]
    P --> Q[ack]
    Q --> A

    G -. exception .-> X[fail_run]
    K -. exception .-> X
    L -. exception .-> X
    X --> Y{push_dlq chunk_text.failure succeeds?}
    Y -- yes --> Z[ack]
    Y -- no --> Z2[nack requeue=true]
    Z --> A
    Z2 --> A
```

---

## B) State Diagram Style

```mermaid
stateDiagram-v2
    [*] --> Polling

    Polling --> Polling: no message
    Polling --> Parsing: message received

    Parsing --> InvalidMessage: bad envelope/payload
    InvalidMessage --> DLQInvalid: push invalid_message
    DLQInvalid --> Acked: ack
    Acked --> Polling

    Parsing --> FilteredOut: key not in input scope
    FilteredOut --> Polling

    Parsing --> Running: valid source_key

    Running --> Chunking: chunking requested
    Chunking --> Persisting

    Persisting --> LineageComplete: chunk writes + registry upserts + lineage outputs
    LineageComplete --> EnqueueNext: emit embed_chunks.request per chunk
    EnqueueNext --> Acked: ack

    Running --> Failed: exception
    Chunking --> Failed: exception
    Persisting --> Failed: exception

    Failed --> DLQFailure: push failure
    DLQFailure --> Acked: dlq publish ok
    DLQFailure --> Requeued: dlq publish fails

    Requeued --> Polling
```

---

## C) Swimlane Activity Style

```mermaid
flowchart LR
    subgraph Q[Queue]
        Q1[pop_message]
        Q2[ack]
        Q3[nack requeue=true]
        Q4[push embed_chunks.request]
        Q5[push_dlq invalid_message]
        Q6[push_dlq failure]
    end

    subgraph S[Worker Service]
        S1[parse envelope]
        S2[filter by prefix/suffix]
        S3[start_run + add_input]
        S4[dataframe path]
        S5[complete_run]
        S6[fail_run]
    end

    subgraph O[Object Storage]
        O1[read processed object]
        O2[write chunk object if missing]
    end

    subgraph R[Provenance Registry]
        R1[upsert chunk latest row]
    end

    subgraph L[Lineage]
        L1[add_output chunk registry dataset]
        L2[add_output chunk objects]
    end

    Q1 --> S1
    S1 -->|invalid| Q5 --> Q2
    S1 -->|valid| S2
    S2 -->|out of scope| Q1
    S2 -->|in scope| S3 --> O1 --> S4 --> O2 --> R1 --> L1 --> L2 --> S5 --> Q4 --> Q2

    O1 -.error.-> S6
    S4 -.error.-> S6
    O2 -.error.-> S6
    R1 -.error.-> S6
    S6 --> Q6
    Q6 -->|ok| Q2
    Q6 -->|fail| Q3
```

---

## D) Plain Step-by-Step (No Diagram)

1. Worker loops forever and calls `stage_queue.pop_message()`.
2. If message is missing, loop continues.
3. Worker parses envelope and extracts `payload.source_uri`.
4. If payload is invalid:
   - publishes `chunk_text.invalid_message` to DLQ,
   - `ack()` the original message,
   - continue loop.
5. For valid chunk request:
   - starts lineage run,
   - adds lineage input for source object.
6. Reads processed JSON object from storage.
7. Generates `run_id`.
8. Processing path:
   - Dataframe path.
9. For each chunk produced:
   - computes deterministic `chunk_id` from provenance fields,
   - writes chunk artifact if object key does not already exist,
   - upserts chunk registry latest row at `07_metadata/provenance/chunking/latest/<chunk_id>.json`.
10. Adds lineage output for registry dataset prefix.
11. Adds lineage outputs for each chunk artifact key.
12. Completes lineage run.
13. Enqueues one `embed_chunks.request` per chunk object.
14. `ack()` the consumed message.
15. On any processing exception:
   - marks lineage run as failed,
   - publishes `chunk_text.failure` to DLQ,
   - if DLQ publish succeeds -> `ack()`, otherwise -> `nack(requeue=true)`.

---

## Notes

- This reflects current code behavior in `src/service/worker_chunk_text_service.py` and `src/service/chunk_text_processor.py`.
- The four views above are equivalent descriptions of the same runtime flow.
