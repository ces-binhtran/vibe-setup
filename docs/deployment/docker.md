# Docker Deployment Guide

This guide covers running vibe-rag in Docker — from local development to a
production-ready container setup.

---

## Quick Start (Development)

The repository ships with `docker-compose.test.yml` which starts PostgreSQL with
pgvector pre-installed. This is the fastest path to a running database.

```bash
# Start the test database
docker-compose -f docker-compose.test.yml up -d

# Verify it is healthy
docker ps | grep vibe-rag-test-db

# Connection string for local use
# postgresql://vibetest:vibetest123@localhost:5434/vibe_rag_test
```

Stop and clean up:

```bash
docker-compose -f docker-compose.test.yml down -v
```

---

## Production docker-compose.yml

For production deployments, use a dedicated compose file that co-locates your
application with a managed database service.

```yaml
# docker-compose.yml
version: "3.9"

services:
  postgres:
    image: pgvector/pgvector:pg16
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-vibe}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB:-vibe_rag}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-vibe} -d ${POSTGRES_DB:-vibe_rag}"]
      interval: 10s
      timeout: 5s
      retries: 5
    # Expose on localhost only — do not expose 5432 to the public internet
    ports:
      - "127.0.0.1:5432:5432"

  app:
    build: .
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      GOOGLE_API_KEY: ${GOOGLE_API_KEY}
      DATABASE_URL: postgresql://${POSTGRES_USER:-vibe}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-vibe_rag}
      COLLECTION_NAME: ${COLLECTION_NAME:-documents}
    ports:
      - "8000:8000"

volumes:
  postgres-data:
```

Create a `.env` file (never commit this file):

```bash
GOOGLE_API_KEY=your-gemini-api-key
POSTGRES_PASSWORD=choose-a-strong-password
POSTGRES_USER=vibe
POSTGRES_DB=vibe_rag
COLLECTION_NAME=documents
```

Start the stack:

```bash
docker-compose up -d
docker-compose logs -f app
```

---

## Dockerfile

The following Dockerfile packages a vibe-rag application into a slim, production-ready
image. `asyncpg` requires `libpq-dev` and `gcc` at build time on Debian slim images.

```dockerfile
# ---- Build stage: install dependencies ----
FROM python:3.11-slim AS builder

# Install system dependencies required by asyncpg and psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy and install Python dependencies first (layer caching)
COPY pyproject.toml ./
COPY vibe_rag/ ./vibe_rag/

# Install the package and its dependencies into a prefix
RUN pip install --no-cache-dir --prefix=/install .

# ---- Runtime stage: minimal image ----
FROM python:3.11-slim AS runtime

# Runtime library for asyncpg (libpq, not libpq-dev)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application entry point
COPY app.py ./

# Non-root user for security
RUN useradd --no-create-home --shell /bin/false appuser
USER appuser

EXPOSE 8000

CMD ["python", "app.py"]
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | Yes | — | Gemini API key for LLM and embedding calls |
| `DATABASE_URL` | Yes | — | PostgreSQL connection string, e.g. `postgresql://user:pass@host/db` |
| `COLLECTION_NAME` | No | `documents` | Vector store collection (table) name |

Pass these to the container via `-e` flags or an `--env-file`:

```bash
docker run \
  -e GOOGLE_API_KEY="$GOOGLE_API_KEY" \
  -e DATABASE_URL="postgresql://vibe:pass@db:5432/vibe_rag" \
  -e COLLECTION_NAME="my_docs" \
  my-vibe-rag-app
```

---

## Example App Entry Point

A minimal `app.py` that can be used as the container's entry point:

```python
"""app.py — minimal vibe-rag application entry point."""
import asyncio
import os
from vibe_rag import QuickSetup

API_KEY      = os.environ["GOOGLE_API_KEY"]
DATABASE_URL = os.environ["DATABASE_URL"]
COLLECTION   = os.getenv("COLLECTION_NAME", "documents")


async def main() -> None:
    async with QuickSetup.create(
        provider_api_key=API_KEY,
        database_url=DATABASE_URL,
        collection_name=COLLECTION,
    ) as rag:
        # Example: ingest a document
        doc_ids = await rag.ingest("knowledge_base.txt")
        print(f"Ingested {len(doc_ids)} chunks")

        # Example: answer a question
        result = await rag.query("What is the main topic of the document?")
        print(result["answer"])


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Health Check

Add a simple connection health check to confirm the database is reachable before
accepting traffic:

```python
import asyncpg
import os


async def health_check() -> bool:
    """Return True when the database is reachable."""
    try:
        conn = await asyncpg.connect(os.environ["DATABASE_URL"], timeout=5)
        await conn.fetchval("SELECT 1")
        await conn.close()
        return True
    except Exception:
        return False
```

For HTTP-based health endpoints, combine this with a lightweight ASGI framework such
as FastAPI:

```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/health")
async def health():
    ok = await health_check()
    return {"status": "ok" if ok else "degraded"}
```

In `docker-compose.yml`, reference the endpoint:

```yaml
app:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

---

## Scaling Notes

### Connection Pooling

`asyncpg` maintains a connection pool internally. vibe-rag's `PostgresVectorStore`
creates a pool on `initialize()`. Default pool sizes work for most workloads, but
tune with `DATABASE_URL` parameters when needed:

```
postgresql://user:pass@host/db?min_size=5&max_size=20
```

Rule of thumb: `max_size` ≤ `max_connections` set in PostgreSQL (`SHOW max_connections;`).
Allocate 3–5 connections per application replica.

### Read Replicas

For read-heavy workloads (many queries, few ingestions):

1. Configure a PostgreSQL streaming replica.
2. Point `QuickSetup.create(database_url=REPLICA_URL)` for read-only `query()` calls.
3. Use the primary `DATABASE_URL` only for `ingest()` calls.

The pgvector index is replicated automatically by streaming replication.

### Horizontal Scaling

Multiple application replicas can share the same PostgreSQL database — all writes go
through connection pooling. Ensure your pool `max_size` × replicas does not exceed
PostgreSQL's `max_connections`.
