# llm domain

This domain is the model-serving layer. It provides the language model endpoint that turns grounded context into natural-language answers.

## Deep Dive

### What runs here
- `ollama` built from `domains/llm/Dockerfile`

### How it contributes to RAG
- Receives chat/generation requests from `rag-api`.
- Produces final responses from retrieval-grounded prompts.

### Runtime dependencies
- Build arg `LLM_MODEL` determines which model is preloaded.

### Interface
- Exposes Ollama API on `${LLM_PORT}:11434`.
- No persistent volume is configured in this domain compose.
