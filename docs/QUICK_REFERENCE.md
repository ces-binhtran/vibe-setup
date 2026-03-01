# Vibe-RAG Quick Reference

A one-page reference for common vibe-rag operations.

## Installation

```bash
pip install vibe-rag

# With dev dependencies
pip install vibe-rag[dev]

# With all features
pip install vibe-rag[all]
```

## Setup PostgreSQL

```bash
# Using Docker
docker run -d \
  --name vibe-rag-db \
  -e POSTGRES_PASSWORD=yourpass \
  -e POSTGRES_DB=vibe_rag \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

## Basic Usage

```python
import asyncio
from vibe_rag import RAGEngine, RAGConfig, LLMConfig, StorageConfig

async def main():
    config = RAGConfig(
        llm=LLMConfig(
            provider="gemini",
            api_key="your-key",
        ),
        storage=StorageConfig(
            backend="postgres",
            collection_name="docs",
            connection_string="postgresql://localhost/vibe_rag",
        ),
    )

    async with RAGEngine(config) as engine:
        # Ingest
        await engine.ingest("file.txt")

        # Query
        result = await engine.query("Your question?")
        print(result["answer"])

asyncio.run(main())
```

## Configuration Options

### LLM Config

```python
LLMConfig(
    provider="gemini",
    api_key="key",
    model_name="gemini-2.0-flash-exp",
    embedding_model="models/text-embedding-004",
    generation_kwargs={"temperature": 0.7}
)
```

### Storage Config

```python
StorageConfig(
    backend="postgres",
    collection_name="my_docs",
    connection_string="postgresql://user:pass@host/db",
    vector_dimension=768
)
```

### Pipeline Config

```python
PipelineConfig(
    top_k=5,
    filter_metadata={"type": "research"},
    reranking_enabled=False
)
```

### Chunking Config

```python
ChunkingConfig(
    strategy="recursive",  # or "fixed"
    chunk_size=512,
    chunk_overlap=50
)
```

## Document Ingestion

```python
# Text file
await engine.ingest("doc.txt")

# With metadata
await engine.ingest("doc.txt", metadata={"type": "manual"})

# Markdown
await engine.ingest("README.md")

# PDF
await engine.ingest("paper.pdf")

# Custom loader
from vibe_rag.loaders import BaseLoader

class MyLoader(BaseLoader):
    async def load(self, path):
        # Your logic
        return [Document(content="...")]

engine.register_loader(".custom", MyLoader())
await engine.ingest("file.custom")
```

## Querying

```python
# Basic query
result = await engine.query("What is RAG?")

# With custom generation params
result = await engine.query(
    "What is RAG?",
    generation_kwargs={
        "temperature": 0.9,
        "max_tokens": 500
    }
)

# Access results
answer = result["answer"]
sources = result["sources"]
metadata = result["metadata"]

# Source details
for source in sources:
    print(source["content"])
    print(source["score"])
    print(source["metadata"])
```

## Metrics

```python
# Get all metrics
metrics = engine.get_metrics()
for m in metrics:
    print(f"Query: {m.query}")
    print(f"Time: {m.total_time_ms}ms")

# Get stats
stats = engine.get_stats()
print(f"Avg time: {stats['avg_total_time_ms']}ms")
print(f"Total queries: {stats['total_queries']}")
```

## Testing

```bash
# Start test DB
docker-compose -f docker-compose.test.yml up -d

# Set API key
export GOOGLE_API_KEY="your-key"

# Run tests
pytest tests/unit -v              # Fast, no external deps
pytest tests/integration -v       # With mocks
pytest tests/e2e -v               # Full E2E with DB + API

# Cleanup
docker-compose -f docker-compose.test.yml down -v
```

## Common Patterns

### Multiple Collections

```python
# Collection per topic
configs = {
    "tech": RAGConfig(..., storage=StorageConfig(collection_name="tech_docs")),
    "legal": RAGConfig(..., storage=StorageConfig(collection_name="legal_docs")),
}

engines = {name: RAGEngine(cfg) for name, cfg in configs.items()}

async with engines["tech"] as engine:
    result = await engine.query("Tech question?")
```

### Batch Ingestion

```python
from pathlib import Path

async with RAGEngine(config) as engine:
    for file in Path("docs").glob("**/*.md"):
        await engine.ingest(str(file), metadata={"path": str(file)})
```

### Metadata Filtering

```python
# Ingest with tags
await engine.ingest("doc1.txt", metadata={"category": "api", "version": "v2"})
await engine.ingest("doc2.txt", metadata={"category": "tutorial", "version": "v2"})

# Query only API docs
config.pipeline.filter_metadata = {"category": "api"}
engine.pipeline = engine._build_pipeline()  # Rebuild pipeline

result = await engine.query("API question?")  # Only searches API docs
```

## Environment Variables

```bash
# Required
export GOOGLE_API_KEY="your-gemini-api-key"

# Optional
export POSTGRES_CONNECTION="postgresql://user:pass@host/db"
export RAG_LOG_LEVEL="INFO"
```

## Error Handling

```python
from vibe_rag.utils.errors import (
    RAGException,
    EmbeddingError,
    RetrievalError,
    LLMProviderError,
    StorageError,
    ConfigurationError,
    DocumentProcessingError,
)

try:
    result = await engine.query("Question?")
except RetrievalError as e:
    print(f"Retrieval failed: {e}")
except LLMProviderError as e:
    print(f"LLM API failed: {e}")
except RAGException as e:
    print(f"General RAG error: {e}")
```

## Performance Tips

1. **Chunk Size**: Larger chunks (1024) for context, smaller (256) for precision
2. **Top K**: Start with 3-5, increase if answers lack context
3. **Overlap**: 10-20% of chunk size for context preservation
4. **Connection Pooling**: Reuse engine instance, don't recreate per query
5. **Batch Ingestion**: Ingest multiple docs before querying for better indexing

## Troubleshooting

### Connection Refused
```bash
# Check PostgreSQL
docker ps | grep postgres
docker-compose -f docker-compose.test.yml up -d
```

### Dimension Mismatch
```python
# Ensure dimensions match
StorageConfig(
    vector_dimension=768  # Must match Gemini's 768
)
```

### Slow Queries
```python
# Check metrics
stats = engine.get_stats()
print(stats)  # Identify bottleneck (retrieval vs generation)
```

### No Results
```python
# Check if documents were ingested
result = await engine.query("test")
print(f"Retrieved: {len(result['sources'])} docs")

# If 0, check collection name and connection
```

## Resources

- 📖 [Quickstart Guide](quickstart.md)
- 🧪 [Testing Guide](testing-guide.md)
- 💡 [Examples](../examples/)
- 🏗️ [Architecture Docs](plans/)
- 🐛 [Issue Tracker](https://github.com/yourusername/vibe-rag/issues)

---

**Need help?** Check the [full documentation](https://vibe-rag.readthedocs.io) or open an issue!
