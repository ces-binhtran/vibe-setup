"""Unit tests for PostgresVectorStore with mocked database."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vibe_rag.models import Document
from vibe_rag.storage.postgres_vector import PostgresVectorStore
from vibe_rag.utils.errors import StorageError


def create_mock_pool():
    """Helper to create properly configured mock pool."""
    pool = AsyncMock()
    conn = AsyncMock()
    # Mock acquire() to return an async context manager (not awaitable)
    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=conn)
    acquire_cm.__aexit__ = AsyncMock(return_value=None)
    pool.acquire = MagicMock(return_value=acquire_cm)
    pool.close = AsyncMock()
    return pool, conn


@pytest.mark.asyncio
async def test_init_creates_connection_pool():
    """PostgresVectorStore initializes with connection pool."""
    pool, conn = create_mock_pool()

    with patch("vibe_rag.storage.postgres_vector.asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
        mock_create_pool.return_value = pool

        store = PostgresVectorStore(
            collection_name="test_collection",
            connection_string="postgresql://localhost/test",
        )
        await store.initialize()

        mock_create_pool.assert_called_once_with("postgresql://localhost/test")
        assert store._pool is pool


@pytest.mark.asyncio
async def test_add_documents_inserts_into_database():
    """add_documents inserts documents with embeddings."""
    pool, conn = create_mock_pool()

    with patch("vibe_rag.storage.postgres_vector.asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
        mock_create_pool.return_value = pool

        store = PostgresVectorStore(
            collection_name="test_collection",
            connection_string="postgresql://localhost/test",
        )
        await store.initialize()

        docs = [
            Document(id="doc1", content="test content 1", metadata={"source": "test"}),
            Document(id="doc2", content="test content 2", metadata={"page": 1}),
        ]
        embeddings = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]

        result = await store.add_documents(docs, embeddings)

        assert result == ["doc1", "doc2"]
        assert conn.executemany.called
        call_args = conn.executemany.call_args[0]
        assert "INSERT INTO" in call_args[0]
        assert "test_collection" in call_args[0]


@pytest.mark.asyncio
async def test_add_documents_raises_error_on_database_failure():
    """add_documents raises StorageError when database fails."""
    pool, conn = create_mock_pool()
    conn.executemany.side_effect = Exception("Database error")

    with patch("vibe_rag.storage.postgres_vector.asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
        mock_create_pool.return_value = pool

        store = PostgresVectorStore(
            collection_name="test_collection",
            connection_string="postgresql://localhost/test",
        )
        await store.initialize()

        docs = [Document(content="test")]
        embeddings = [[1.0, 2.0, 3.0]]

        with pytest.raises(StorageError, match="Failed to add documents"):
            await store.add_documents(docs, embeddings)


@pytest.mark.asyncio
async def test_add_documents_validates_matching_lengths():
    """add_documents raises error if documents and embeddings don't match."""
    pool, conn = create_mock_pool()

    with patch("vibe_rag.storage.postgres_vector.asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
        mock_create_pool.return_value = pool

        store = PostgresVectorStore(
            collection_name="test_collection",
            connection_string="postgresql://localhost/test",
        )
        await store.initialize()

        docs = [Document(content="test1"), Document(content="test2")]
        embeddings = [[1.0, 2.0, 3.0]]  # Only one embedding

        with pytest.raises(StorageError, match="must match"):
            await store.add_documents(docs, embeddings)


@pytest.mark.asyncio
async def test_similarity_search_queries_database():
    """similarity_search queries database with cosine distance."""
    pool, conn = create_mock_pool()

    # Mock database response
    mock_rows = [
        {
            "id": "doc1",
            "content": "test content 1",
            "metadata": {"source": "test"},
            "distance": 0.1,
        },
        {
            "id": "doc2",
            "content": "test content 2",
            "metadata": {"page": 1},
            "distance": 0.2,
        },
    ]
    conn.fetch.return_value = mock_rows

    with patch("vibe_rag.storage.postgres_vector.asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
        mock_create_pool.return_value = pool

        store = PostgresVectorStore(
            collection_name="test_collection",
            connection_string="postgresql://localhost/test",
        )
        await store.initialize()

        query_embedding = [1.0, 2.0, 3.0]
        results = await store.similarity_search(query_embedding, k=5)

        assert len(results) == 2
        assert results[0].id == "doc1"
        assert results[0].content == "test content 1"
        assert results[0].score == 0.1
        assert results[1].id == "doc2"
        assert results[1].content == "test content 2"
        assert results[1].score == 0.2

        # Verify query was called with correct SQL
        assert conn.fetch.called
        call_args = conn.fetch.call_args[0]
        assert "SELECT" in call_args[0]
        assert "test_collection" in call_args[0]
        assert "ORDER BY" in call_args[0]


@pytest.mark.asyncio
async def test_similarity_search_with_metadata_filter():
    """similarity_search applies metadata filters."""
    pool, conn = create_mock_pool()
    conn.fetch.return_value = []

    with patch("vibe_rag.storage.postgres_vector.asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
        mock_create_pool.return_value = pool

        store = PostgresVectorStore(
            collection_name="test_collection",
            connection_string="postgresql://localhost/test",
        )
        await store.initialize()

        query_embedding = [1.0, 2.0, 3.0]
        await store.similarity_search(
            query_embedding, k=5, filter_metadata={"source": "docs"}
        )

        # Verify filter was applied in query
        call_args = conn.fetch.call_args[0]
        assert "metadata" in call_args[0]


@pytest.mark.asyncio
async def test_similarity_search_raises_error_on_failure():
    """similarity_search raises RetrievalError on database failure."""
    pool, conn = create_mock_pool()
    conn.fetch.side_effect = Exception("Database error")

    with patch("vibe_rag.storage.postgres_vector.asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
        mock_create_pool.return_value = pool

        store = PostgresVectorStore(
            collection_name="test_collection",
            connection_string="postgresql://localhost/test",
        )
        await store.initialize()

        query_embedding = [1.0, 2.0, 3.0]

        with pytest.raises(Exception):  # Will be RetrievalError in implementation
            await store.similarity_search(query_embedding, k=5)


@pytest.mark.asyncio
async def test_delete_collection_drops_table():
    """delete_collection drops the collection table."""
    pool, conn = create_mock_pool()

    with patch("vibe_rag.storage.postgres_vector.asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
        mock_create_pool.return_value = pool

        store = PostgresVectorStore(
            collection_name="test_collection",
            connection_string="postgresql://localhost/test",
        )
        await store.initialize()

        await store.delete_collection()

        assert conn.execute.called
        call_args = conn.execute.call_args[0]
        assert "DROP TABLE" in call_args[0]
        assert "test_collection" in call_args[0]


@pytest.mark.asyncio
async def test_delete_collection_raises_error_on_failure():
    """delete_collection raises StorageError on database failure."""
    pool, conn = create_mock_pool()

    with patch("vibe_rag.storage.postgres_vector.asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
        mock_create_pool.return_value = pool

        store = PostgresVectorStore(
            collection_name="test_collection",
            connection_string="postgresql://localhost/test",
        )
        await store.initialize()

        # Set error after initialization
        conn.execute.side_effect = Exception("Database error")

        with pytest.raises(StorageError, match="Failed to delete collection"):
            await store.delete_collection()


@pytest.mark.asyncio
async def test_close_closes_pool():
    """close() closes the connection pool."""
    pool, conn = create_mock_pool()

    with patch("vibe_rag.storage.postgres_vector.asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
        mock_create_pool.return_value = pool

        store = PostgresVectorStore(
            collection_name="test_collection",
            connection_string="postgresql://localhost/test",
        )
        await store.initialize()
        await store.close()

        pool.close.assert_called_once()
