FROM ollama/ollama:latest

ARG LLM_MODEL=llama3.2:1b

# Bake the selected model into the image at build time.
RUN set -eu; \
    OLLAMA_HOST=http://127.0.0.1:11434 ollama serve >/tmp/ollama-build.log 2>&1 & \
    OLLAMA_PID="$!"; \
    i=0; \
    until OLLAMA_HOST=http://127.0.0.1:11434 ollama list >/dev/null 2>&1; do \
      i=$((i + 1)); \
      if [ "$i" -ge 120 ]; then \
        echo "Ollama did not become ready during image build"; \
        kill "$OLLAMA_PID" || true; \
        exit 1; \
      fi; \
      sleep 1; \
    done; \
    OLLAMA_HOST=http://127.0.0.1:11434 ollama pull "$LLM_MODEL"; \
    kill "$OLLAMA_PID"; \
    wait "$OLLAMA_PID" || true
