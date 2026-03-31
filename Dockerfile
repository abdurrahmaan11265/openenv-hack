FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl git && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    "openenv-core[core]>=0.2.1" \
    "openai>=1.0.0" \
    "anthropic>=0.40.0" \
    "httpx>=0.27.0" \
    "uvicorn>=0.24.0" \
    "fastapi>=0.115.0" \
    "sentence-transformers>=3.0.0" \
    "numpy>=1.24.0"

# Pre-download the embedding model so it's baked into the image
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . .

ENV PYTHONPATH="/app:$PYTHONPATH"

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]