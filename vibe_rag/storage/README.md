# Vector Storage Layer

Production-grade vector storage implementations for vibe-rag.

## Overview

The storage layer provides pluggable vector database backends for storing document embeddings and performing similarity search. All implementations follow the `BaseVectorStore` interface, allowing you to swap storage backends without changing your application code.

## Available Backends

### PostgreSQL + pgvector

Production-ready vector storage using PostgreSQL with the pgvector extension.

**Features:**
- Async operations with connection pooling (asyncpg)
- Cosine similarity search with IVFFlat indexing
- JSONB metadata storage and filtering
- Multi-tenant support via collections

**Setup:**

```bash
# Install PostgreSQL and pgvector extension
# See: https://github.com/pgvector/pgvector

# Install Python dependencies
pip install asyncpg pgvector
```

**Usage:**

```python
from vibe_rag.storage import PostgresVectorStore
from vibe_rag.models import Document

# Initialize store
store = PostgresVectorStore(
    collection_name="my_documents",
    connection_string="postgresql://user:pass@localhost/mydb",
    vector_dimension=768  # Match your embedding model
)

# Initialize connection pool and create tables
await store.initialize()

# Add documents with embeddings
docs = [
    Document(content="Machine learning is...", metadata={"source": "docs"}),
    Document(content="Python is a programming...", metadata={"source": "tutorial"})
]
embeddings = [[0.1, 0.2, ...], [0.3, 0.4, ...]]  # From your embedding model

doc_ids = await store.add_documents(docs, embeddings)

# Search for similar documents
query_embedding = [0.15, 0.25, ...]
results = await store.similarity_search(
    query_embedding,
    k=5,
    filter_metadata={"source": "docs"}  # Optional filtering
)

for doc in results:
    print(f"{doc.content} (score: {doc.score})")

# Clean up
await store.close()
```

## Adding Custom Backends

To add a new storage backend, implement the `BaseVectorStore` interface:

```python
from vibe_rag.storage import BaseVectorStore
from vibe_rag.models import Document

class MyVectorStore(BaseVectorStore):
    async def add_documents(
        self, documents: list[Document], embeddings: list[list[float]]
    ) -> list[str]:
        # Add documents to your storage
        pass

    async def similarity_search(
        self,
        query_embedding: list[float],
        k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[Document]:
        # Search for similar documents
        pass

    async def delete_collection(self) -> None:
        # Delete the collection
        pass
```

## Schema

The PostgreSQL schema is automatically created when you call `initialize()`. For reference, see `schema.sql`.

## Testing

Unit tests use mocked database connections:

```bash
pytest tests/unit/storage/
```

Integration tests require a real PostgreSQL database with pgvector:

```bash
# Set up test database
createdb vibe_rag_test
psql vibe_rag_test -c "CREATE EXTENSION vector"

# Run integration tests (when available)
pytest tests/integration/storage/
```

## Performance Tuning

For production deployments:

1. **IVFFlat Index Lists**: Tune based on dataset size (rule of thumb: `sqrt(num_rows)`)
2. **Connection Pool**: Adjust pool size based on concurrent load
3. **Metadata Indexes**: Add indexes on frequently filtered JSONB fields
4. **Vector Dimension**: Use smaller dimensions if accuracy permits (faster search)

See PostgreSQL and pgvector documentation for more optimization strategies.
