# Vibe-RAG Quickstart Guide

Get started with vibe-rag in 5 minutes!

## Prerequisites

1. **Python 3.10+** installed
2. **PostgreSQL with pgvector** extension
3. **Google Gemini API key** ([Get one here](https://ai.google.dev/))

## Installation

```bash
# Install vibe-rag
pip install vibe-rag

# Install PostgreSQL with pgvector (using Docker)
docker run -d \
  --name vibe-rag-postgres \
  -e POSTGRES_PASSWORD=yourpassword \
  -e POSTGRES_DB=vibe_rag \
  -p 5432:5432 \
  pgvector/pgvector:pg16
```

## Quick Start

### 1. Set Up Environment

```bash
export GOOGLE_API_KEY="your-gemini-api-key"
export POSTGRES_CONNECTION="postgresql://postgres:yourpassword@localhost:5432/vibe_rag"
```

### 2. Basic RAG Workflow

```python
import asyncio
from vibe_rag import RAGEngine, RAGConfig, LLMConfig, StorageConfig

async def main():
    # Configure RAG engine
    config = RAGConfig(
        llm=LLMConfig(
            provider="gemini",
            api_key="your-gemini-api-key",
        ),
        storage=StorageConfig(
            backend="postgres",
            collection_name="my_documents",
            connection_string="postgresql://postgres:pass@localhost:5432/vibe_rag",
        ),
    )

    # Create and initialize engine
    async with RAGEngine(config) as engine:
        # Ingest documents
        print("📥 Ingesting documents...")
        await engine.ingest("path/to/your/document.txt")

        # Query the knowledge base
        print("🔍 Querying...")
        result = await engine.query("What is this document about?")

        # Display results
        print(f"\n✨ Answer: {result['answer']}\n")
        print(f"📚 Sources ({len(result['sources'])}):")
        for i, source in enumerate(result['sources'], 1):
            print(f"  {i}. {source['content'][:100]}... (score: {source['score']:.3f})")

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Run Your First Query

Save the above code as `demo.py` and run:

```bash
python demo.py
```

Expected output:
```
📥 Ingesting documents...
🔍 Querying...

✨ Answer: This document discusses...

📚 Sources (3):
  1. First relevant passage... (score: 0.156)
  2. Second relevant passage... (score: 0.234)
  3. Third relevant passage... (score: 0.298)
```

## Common Use Cases

### Ingesting Multiple Documents

```python
# Text files
await engine.ingest("article.txt", metadata={"type": "article"})

# Markdown files
await engine.ingest("README.md", metadata={"type": "documentation"})

# PDF files
await engine.ingest("paper.pdf", metadata={"type": "research"})
```

### Custom Chunking Strategy

```python
from vibe_rag import ChunkingConfig

config = RAGConfig(
    # ... other config ...
    chunking=ChunkingConfig(
        strategy="recursive",      # or "fixed"
        chunk_size=1024,          # characters per chunk
        chunk_overlap=100,        # overlap between chunks
    ),
)
```

### Filtering by Metadata

```python
from vibe_rag import PipelineConfig

config = RAGConfig(
    # ... other config ...
    pipeline=PipelineConfig(
        top_k=5,                          # retrieve 5 documents
        filter_metadata={"type": "research"},  # only research docs
    ),
)
```

### Tracking Performance Metrics

```python
async with RAGEngine(config) as engine:
    # Run queries
    await engine.query("Question 1")
    await engine.query("Question 2")

    # Get metrics
    stats = engine.get_stats()
    print(f"Average query time: {stats['avg_total_time_ms']:.2f}ms")
    print(f"Average retrieval: {stats['avg_retrieval_time_ms']:.2f}ms")
    print(f"Average generation: {stats['avg_generation_time_ms']:.2f}ms")
```

## Testing Your Setup

We provide Docker Compose for easy testing:

### 1. Start Test Database

```bash
# Start PostgreSQL test instance
docker-compose -f docker-compose.test.yml up -d

# Wait for healthcheck
docker-compose -f docker-compose.test.yml ps
```

### 2. Run Tests

```bash
# Set API key
export GOOGLE_API_KEY="your-key"

# Run integration tests (with mocks)
pytest tests/integration -v

# Run E2E tests (with real database and API)
pytest tests/e2e -v --markers=e2e
```

### 3. Cleanup

```bash
# Stop test database
docker-compose -f docker-compose.test.yml down -v
```

## Example: Building a Documentation Q&A System

```python
import asyncio
from pathlib import Path
from vibe_rag import RAGEngine, RAGConfig, LLMConfig, StorageConfig, ChunkingConfig

async def build_docs_qa():
    config = RAGConfig(
        llm=LLMConfig(
            provider="gemini",
            api_key="your-key",
        ),
        storage=StorageConfig(
            backend="postgres",
            collection_name="documentation",
            connection_string="postgresql://localhost/vibe_rag",
        ),
        chunking=ChunkingConfig(
            strategy="recursive",
            chunk_size=512,
            chunk_overlap=50,
        ),
    )

    async with RAGEngine(config) as engine:
        # Ingest all markdown files
        docs_dir = Path("docs")
        for md_file in docs_dir.glob("**/*.md"):
            print(f"📄 Ingesting {md_file.name}...")
            await engine.ingest(
                str(md_file),
                metadata={"filename": md_file.name, "path": str(md_file)}
            )

        print("\n✅ Documentation indexed!\n")

        # Interactive Q&A loop
        while True:
            query = input("❓ Ask a question (or 'quit' to exit): ")
            if query.lower() in ['quit', 'exit', 'q']:
                break

            result = await engine.query(query)
            print(f"\n💡 {result['answer']}\n")
            print(f"📚 Based on {len(result['sources'])} sources")
            print(f"⏱️  Query time: {result['metadata']['total_time_ms']:.2f}ms\n")

if __name__ == "__main__":
    asyncio.run(build_docs_qa())
```

## Next Steps

- **Explore Configuration**: See [Configuration Guide](configuration.md) for all options
- **Custom Components**: Learn about [Custom Loaders](custom-loaders.md) and [Pipeline Components](pipeline.md)
- **Production Deployment**: Check [Deployment Guide](deployment.md) for best practices
- **Advanced Features**: Explore [LangGraph Integration](langgraph.md) for complex workflows

## Troubleshooting

### PostgreSQL Connection Issues

```python
# Test connection
import asyncpg

async def test_connection():
    conn = await asyncpg.connect("postgresql://localhost/vibe_rag")
    version = await conn.fetchval("SELECT version()")
    print(f"Connected! {version}")
    await conn.close()

asyncio.run(test_connection())
```

### API Key Issues

```python
# Test Gemini API
from vibe_rag.providers import GeminiProvider

async def test_api():
    provider = GeminiProvider(api_key="your-key")
    result = await provider.generate("Hello, world!")
    print(f"API works! Response: {result}")

asyncio.run(test_api())
```

### Vector Dimension Mismatch

```python
# Gemini text-embedding-004 uses 768 dimensions
config = RAGConfig(
    llm=LLMConfig(
        embedding_model="models/text-embedding-004",  # 768 dims
    ),
    storage=StorageConfig(
        vector_dimension=768,  # Must match!
    ),
)
```

## Getting Help

- **Documentation**: [https://vibe-rag.readthedocs.io](https://vibe-rag.readthedocs.io)
- **Issues**: [https://github.com/yourusername/vibe-rag/issues](https://github.com/yourusername/vibe-rag/issues)
- **Examples**: See `examples/` directory

Happy building! 🚀
