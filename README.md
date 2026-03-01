# vibe-rag

Production-grade modular RAG framework with pluggable components.

## Features

- 🔌 **Pluggable LLM providers** - Gemini, OpenAI, Anthropic support
- 🗄️ **Flexible storage** - PostgreSQL+pgvector, Chroma, or custom backends
- 🔧 **Composable pipelines** - Build custom retrieval strategies
- 🚀 **Quick-start modules** - Get running in 5 minutes
- 🧪 **Testing utilities** - Mock providers and storage for testing
- 🔗 **LangGraph ready** - Integrate as an AI agent tool

## Installation

```bash
pip install vibe-rag
```

With LangGraph support:
```bash
pip install vibe-rag[langgraph]
```

Development installation:
```bash
pip install -e ".[dev]"
```

## Quick Start

### Option 1: QuickSetup (Easiest)

Get started in seconds with sensible defaults:

```python
from vibe_rag import QuickSetup
import os

# One-line setup
rag = QuickSetup.create(
    provider_api_key=os.getenv("GEMINI_API_KEY"),
    database_url=os.getenv("DATABASE_URL")
)

# Ingest documents
rag.ingest_file("knowledge_base.pdf", collection="docs")

# Query
result = rag.query("What is the main topic?", collection="docs")
print(result["answer"])
```

### Option 2: Custom Configuration

Full control over components:

```python
from vibe_rag import RAGEngine
from vibe_rag.providers import GeminiProvider
from vibe_rag.storage import PostgresVectorStore
from vibe_rag.pipeline import PipelineBuilder

# Configure components
provider = GeminiProvider(
    api_key=os.getenv("GEMINI_API_KEY"),
    model="gemini-1.5-pro"
)

storage = PostgresVectorStore(
    host="localhost",
    database="rag_db",
    user="postgres",
    password=os.getenv("DB_PASSWORD")
)

# Build custom pipeline
pipeline = PipelineBuilder() \
    .add_retriever("vector", top_k=10) \
    .add_reranker("cross_encoder", top_k=5) \
    .build()

# Create RAG engine
rag = RAGEngine(
    provider=provider,
    storage=storage,
    pipeline=pipeline
)
```

## Architecture

vibe-rag uses a three-layer architecture:

- **Core Library** - Pluggable components and RAG logic
- **Service Layer** - Optional HTTP wrapper (build your own)
- **Client Layer** - Direct import or REST API consumption

All components implement abstract base classes, making them swappable via configuration.

## Documentation

See `docs/` for detailed documentation:

- [Getting Started](docs/getting-started/)
- [Configuration Guide](docs/guides/configuration.md)
- [Custom Pipelines](docs/guides/custom-pipelines.md)
- [LangGraph Integration](docs/guides/langgraph-integration.md)
- [API Reference](docs/api-reference/)

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=vibe_rag --cov-report=html

# Format code
black vibe_rag tests

# Lint
ruff check vibe_rag tests

# Type check
mypy vibe_rag
```

## License

MIT - see [LICENSE](LICENSE) for details.

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
