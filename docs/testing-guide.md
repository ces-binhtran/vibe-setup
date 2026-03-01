# Testing Guide for Vibe-RAG

This guide helps you test the complete vibe-rag system with real components.

## Prerequisites

Before testing, ensure you have:

1. ✅ **Python 3.10+** installed
2. ✅ **Docker** installed (for PostgreSQL)
3. ✅ **Google Gemini API key** from [Google AI Studio](https://ai.google.dev/)

## Setup Test Environment

### 1. Install Dependencies

```bash
# Install vibe-rag with dev dependencies
pip install -e ".[dev]"

# Verify installation
python -c "import vibe_rag; print(vibe_rag.__version__)"
```

### 2. Start PostgreSQL Test Database

We provide a Docker Compose file for testing:

```bash
# Start PostgreSQL with pgvector
docker-compose -f docker-compose.test.yml up -d

# Verify it's running
docker-compose -f docker-compose.test.yml ps

# Check logs
docker-compose -f docker-compose.test.yml logs -f
```

**Test Database Details:**
- Host: `localhost:5433`
- User: `vibetest`
- Password: `vibetest123`
- Database: `vibe_rag_test`
- Connection String: `postgresql://vibetest:vibetest123@localhost:5433/vibe_rag_test`

### 3. Set Environment Variables

```bash
# Required for E2E tests
export GOOGLE_API_KEY="your-gemini-api-key-here"

# Optional: Override test database connection
export TEST_POSTGRES_CONNECTION="postgresql://vibetest:vibetest123@localhost:5433/vibe_rag_test"
```

## Running Tests

### Quick Test (Unit Tests Only)

Fast tests with mocks, no external dependencies:

```bash
pytest tests/unit -v
```

### Integration Tests

Tests with mock components but real logic:

```bash
pytest tests/integration -v -m integration
```

### End-to-End Tests

**⚠️ Requires PostgreSQL and Gemini API key!**

Full system tests with real database and API calls:

```bash
# Run all E2E tests
pytest tests/e2e -v -m e2e

# Run specific E2E test
pytest tests/e2e/test_rag_engine_e2e.py::TestRAGEngineE2E::test_complete_rag_workflow -v
```

### Run All Tests

```bash
# Run everything
pytest -v

# With coverage report
pytest --cov=vibe_rag --cov-report=html
```

## Manual Testing Workflow

### Example 1: Simple Q&A System

Create `test_simple.py`:

```python
import asyncio
from vibe_rag import RAGEngine, RAGConfig, LLMConfig, StorageConfig

async def test_simple():
    config = RAGConfig(
        llm=LLMConfig(
            provider="gemini",
            api_key="your-api-key",
        ),
        storage=StorageConfig(
            backend="postgres",
            collection_name="test_simple",
            connection_string="postgresql://vibetest:vibetest123@localhost:5433/vibe_rag_test",
        ),
    )

    async with RAGEngine(config) as engine:
        # Clean up first
        try:
            await engine.storage.delete_collection()
            await engine.storage._create_table()
        except:
            pass

        # Create test document
        with open("test_doc.txt", "w") as f:
            f.write("""
            Python was created by Guido van Rossum in 1991.
            It is known for its simple, readable syntax.
            Python is used for web development, data science, and automation.
            """)

        # Ingest
        print("📥 Ingesting document...")
        await engine.ingest("test_doc.txt")

        # Query
        print("🔍 Querying...")
        result = await engine.query("Who created Python?")

        # Results
        print(f"\n✨ Answer: {result['answer']}")
        print(f"\n📊 Metadata:")
        print(f"  - Documents retrieved: {result['metadata']['documents_retrieved']}")
        print(f"  - Retrieval time: {result['metadata']['retrieval_time_ms']:.2f}ms")
        print(f"  - Generation time: {result['metadata']['generation_time_ms']:.2f}ms")
        print(f"  - Total time: {result['metadata']['total_time_ms']:.2f}ms")

        print(f"\n📚 Sources:")
        for i, source in enumerate(result['sources'], 1):
            print(f"  {i}. Score: {source['score']:.4f}")
            print(f"     Content: {source['content'][:100]}...")

if __name__ == "__main__":
    asyncio.run(test_simple())
```

Run it:

```bash
python test_simple.py
```

Expected output:
```
📥 Ingesting document...
🔍 Querying...

✨ Answer: Python was created by Guido van Rossum in 1991.

📊 Metadata:
  - Documents retrieved: 1
  - Retrieval time: 145.23ms
  - Generation time: 892.45ms
  - Total time: 1037.68ms

📚 Sources:
  1. Score: 0.1234
     Content: Python was created by Guido van Rossum in 1991.
            It is known for its simple, readable...
```

### Example 2: Multiple Document RAG

Create `test_multi_doc.py`:

```python
import asyncio
from pathlib import Path
from vibe_rag import RAGEngine, RAGConfig, LLMConfig, StorageConfig, ChunkingConfig

async def test_multi_doc():
    # Create test documents
    docs = {
        "python.txt": "Python is a high-level programming language created by Guido van Rossum.",
        "javascript.txt": "JavaScript is a programming language created by Brendan Eich in 1995.",
        "rust.txt": "Rust is a systems programming language focused on safety and performance.",
    }

    for filename, content in docs.items():
        with open(filename, "w") as f:
            f.write(content)

    config = RAGConfig(
        llm=LLMConfig(provider="gemini", api_key="your-key"),
        storage=StorageConfig(
            backend="postgres",
            collection_name="test_multi",
            connection_string="postgresql://vibetest:vibetest123@localhost:5433/vibe_rag_test",
        ),
        chunking=ChunkingConfig(chunk_size=256, chunk_overlap=20),
    )

    async with RAGEngine(config) as engine:
        # Clean up
        try:
            await engine.storage.delete_collection()
            await engine.storage._create_table()
        except:
            pass

        # Ingest all documents
        for filename in docs.keys():
            print(f"📄 Ingesting {filename}...")
            await engine.ingest(filename, metadata={"source": filename})

        # Test queries
        queries = [
            "Who created Python?",
            "What is Rust known for?",
            "When was JavaScript created?",
        ]

        for query in queries:
            print(f"\n❓ Query: {query}")
            result = await engine.query(query)
            print(f"💡 Answer: {result['answer']}")
            print(f"📚 Sources: {len(result['sources'])} documents")

        # Show metrics
        stats = engine.get_stats()
        print(f"\n📊 Overall Stats:")
        print(f"  - Total queries: {stats['total_queries']}")
        print(f"  - Avg time: {stats['avg_total_time_ms']:.2f}ms")
        print(f"  - Avg docs retrieved: {stats['avg_documents_retrieved']:.1f}")

        # Cleanup files
        for filename in docs.keys():
            Path(filename).unlink()

if __name__ == "__main__":
    asyncio.run(test_multi_doc())
```

### Example 3: Testing Chunking Strategies

```python
import asyncio
from vibe_rag import RAGEngine, RAGConfig, LLMConfig, StorageConfig, ChunkingConfig

async def test_chunking():
    # Create large document
    long_content = "This is a test sentence. " * 500  # ~12500 characters

    with open("long_doc.txt", "w") as f:
        f.write(long_content)

    strategies = ["fixed", "recursive"]

    for strategy in strategies:
        print(f"\n{'='*60}")
        print(f"Testing {strategy.upper()} chunking strategy")
        print(f"{'='*60}")

        config = RAGConfig(
            llm=LLMConfig(provider="gemini", api_key="your-key"),
            storage=StorageConfig(
                backend="postgres",
                collection_name=f"test_{strategy}",
                connection_string="postgresql://vibetest:vibetest123@localhost:5433/vibe_rag_test",
            ),
            chunking=ChunkingConfig(
                strategy=strategy,
                chunk_size=512,
                chunk_overlap=50,
            ),
        )

        async with RAGEngine(config) as engine:
            # Clean up
            try:
                await engine.storage.delete_collection()
                await engine.storage._create_table()
            except:
                pass

            # Ingest
            doc_ids = await engine.ingest("long_doc.txt")
            print(f"✅ Created {len(doc_ids)} chunks")

            # Query
            result = await engine.query("What is this about?")
            print(f"✅ Retrieved {len(result['sources'])} chunks")
            print(f"✅ Chunk sizes: {[len(s['content']) for s in result['sources']]}")

    # Cleanup
    Path("long_doc.txt").unlink()

if __name__ == "__main__":
    asyncio.run(test_chunking())
```

## Verification Checklist

Use this checklist to verify your setup:

### ✅ Unit Tests
```bash
pytest tests/unit -v
# All tests should pass
```

### ✅ Database Connection
```python
import asyncio
import asyncpg

async def test_db():
    conn = await asyncpg.connect(
        "postgresql://vibetest:vibetest123@localhost:5433/vibe_rag_test"
    )
    print(await conn.fetchval("SELECT version()"))
    await conn.close()

asyncio.run(test_db())
```

### ✅ Gemini API
```python
import asyncio
from vibe_rag.providers import GeminiProvider

async def test_gemini():
    provider = GeminiProvider(api_key="your-key")
    result = await provider.generate("Say hello")
    print(f"✅ Gemini API works! Response: {result}")

asyncio.run(test_gemini())
```

### ✅ End-to-End RAG
```bash
# Run the complete E2E test
pytest tests/e2e/test_rag_engine_e2e.py::TestRAGEngineE2E::test_complete_rag_workflow -v -s
```

## Common Issues & Solutions

### Issue: "Connection refused" to PostgreSQL

**Solution:**
```bash
# Check if container is running
docker ps | grep vibe-rag-test-db

# If not running, start it
docker-compose -f docker-compose.test.yml up -d

# Check logs
docker-compose -f docker-compose.test.yml logs
```

### Issue: "pgvector extension not found"

**Solution:**
```bash
# Ensure you're using pgvector/pgvector image
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml up -d

# Manually verify
docker exec -it vibe-rag-test-db psql -U vibetest -d vibe_rag_test -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Issue: "GOOGLE_API_KEY not set"

**Solution:**
```bash
# Set the environment variable
export GOOGLE_API_KEY="your-actual-api-key"

# Verify it's set
echo $GOOGLE_API_KEY

# Or pass it directly in Python
config = RAGConfig(
    llm=LLMConfig(api_key="your-key-here"),
    ...
)
```

### Issue: "Dimension mismatch" error

**Solution:**
```python
# Gemini text-embedding-004 uses 768 dimensions
config = RAGConfig(
    llm=LLMConfig(
        embedding_model="models/text-embedding-004",  # 768 dims
    ),
    storage=StorageConfig(
        vector_dimension=768,  # MUST match!
    ),
)
```

### Issue: Tests are slow

**Tip:** Skip E2E tests during development:

```bash
# Run only fast tests
pytest tests/unit tests/integration -v

# Or mark E2E tests to skip
pytest -v -m "not e2e"
```

## Cleanup

After testing:

```bash
# Stop and remove test database
docker-compose -f docker-compose.test.yml down -v

# Remove test data
rm -rf htmlcov/  # coverage reports
rm .coverage
rm test_*.txt    # test files
```

## Performance Benchmarks

Expected performance on modest hardware (M1 Mac, local PostgreSQL):

| Operation | Time |
|-----------|------|
| Document ingestion (1KB text) | ~200-400ms |
| Embedding generation (1 doc) | ~100-300ms |
| Vector search (top 5) | ~20-50ms |
| LLM generation (short answer) | ~500-1500ms |
| Complete RAG query | ~700-2000ms |

**Note:** First query may be slower due to cold start.

## Next Steps

- 📖 Read [Architecture Guide](architecture.md) to understand internals
- 🔧 See [Configuration Guide](configuration.md) for tuning
- 🚀 Check [Deployment Guide](deployment.md) for production
- 💡 Explore [Examples](../examples/) directory

Happy testing! 🧪
