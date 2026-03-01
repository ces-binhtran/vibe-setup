"""PostgreSQL + pgvector implementation of vector storage."""

import json
import re
from typing import Any

import asyncpg

from vibe_rag.models import Document
from vibe_rag.storage.base import BaseVectorStore
from vibe_rag.utils.errors import ConfigurationError, RetrievalError, StorageError


class PostgresVectorStore(BaseVectorStore):
    """Vector storage implementation using PostgreSQL + pgvector.

    Uses asyncpg for async database operations and pgvector extension
    for efficient similarity search with cosine distance.

    Args:
        collection_name: Name of the table to store vectors
        connection_string: PostgreSQL connection string
        vector_dimension: Dimension of embedding vectors (default: 768)

    Example:
        >>> store = PostgresVectorStore(
        ...     collection_name="documents",
        ...     connection_string="postgresql://localhost/mydb"
        ... )
        >>> await store.initialize()
        >>> await store.add_documents(docs, embeddings)
    """

    def __init__(
        self,
        collection_name: str,
        connection_string: str,
        vector_dimension: int = 768,
    ):
        """Initialize PostgreSQL vector store.

        Args:
            collection_name: Name of the table to store vectors
            connection_string: PostgreSQL connection string
            vector_dimension: Dimension of embedding vectors (default: 768)

        Raises:
            ConfigurationError: If collection_name is not a valid PostgreSQL identifier
        """
        # Validate collection_name to prevent SQL injection
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", collection_name):
            raise ConfigurationError(
                f"Invalid collection name: {collection_name}. "
                "Must start with a letter or underscore and contain only "
                "letters, numbers, and underscores."
            )
        super().__init__(collection_name)
        self.connection_string = connection_string
        self.vector_dimension = vector_dimension
        self._pool: asyncpg.Pool | None = None

    async def initialize(self) -> None:
        """Initialize connection pool and create table if needed.

        Raises:
            StorageError: If initialization fails
        """
        try:
            self._pool = await asyncpg.create_pool(self.connection_string)
            await self._create_table()
        except Exception as e:
            raise StorageError(f"Failed to initialize vector store: {e}") from e

    async def _create_table(self) -> None:
        """Create table with pgvector extension if it doesn't exist."""
        if not self._pool:
            raise StorageError("Connection pool not initialized")

        async with self._pool.acquire() as conn:
            # Enable pgvector extension
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # Create table
            await conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.collection_name} (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata JSONB DEFAULT '{{}}',
                    embedding vector({self.vector_dimension})
                )
                """
            )

            # Create index for similarity search
            await conn.execute(
                f"""
                CREATE INDEX IF NOT EXISTS {self.collection_name}_embedding_idx
                ON {self.collection_name}
                USING ivfflat (embedding vector_cosine_ops)
                WITH (lists = 100)
                """
            )

    async def add_documents(
        self, documents: list[Document], embeddings: list[list[float]]
    ) -> list[str]:
        """Add documents with their embeddings to the database.

        Args:
            documents: List of documents to add
            embeddings: List of embedding vectors (same length as documents)

        Returns:
            List of document IDs that were added

        Raises:
            StorageError: If adding documents fails or lengths don't match
        """
        if len(documents) != len(embeddings):
            raise StorageError(
                f"Number of documents ({len(documents)}) must match "
                f"number of embeddings ({len(embeddings)})"
            )

        if not self._pool:
            raise StorageError("Connection pool not initialized")

        try:
            async with self._pool.acquire() as conn:
                # Prepare data for batch insert
                values = [
                    (
                        doc.id,
                        doc.content,
                        json.dumps(doc.metadata),
                        embeddings[i],
                    )
                    for i, doc in enumerate(documents)
                ]

                # Insert documents
                await conn.executemany(
                    f"""
                    INSERT INTO {self.collection_name} (id, content, metadata, embedding)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (id) DO UPDATE
                    SET content = EXCLUDED.content,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding
                    """,
                    values,
                )

                return [doc.id for doc in documents]

        except Exception as e:
            raise StorageError(f"Failed to add documents: {e}") from e

    async def similarity_search(
        self,
        query_embedding: list[float],
        k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[Document]:
        """Search for documents similar to the query embedding.

        Uses cosine distance for similarity calculation. Lower distance
        means higher similarity.

        Args:
            query_embedding: Vector representation of the query
            k: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"source": "docs"})

        Returns:
            List of documents ordered by similarity (most similar first)

        Raises:
            RetrievalError: If search fails
        """
        if not self._pool:
            raise StorageError("Connection pool not initialized")

        try:
            async with self._pool.acquire() as conn:
                # Build query with optional metadata filter
                query = f"""
                    SELECT id, content, metadata, embedding <=> $1 AS distance
                    FROM {self.collection_name}
                """

                params: list[Any] = [query_embedding]

                if filter_metadata:
                    # Use JSONB containment operator (@>) for correct type comparison
                    # This avoids the type mismatch issue with ->> text extraction
                    param_idx = len(params) + 1
                    params.append(json.dumps(filter_metadata))
                    query += f" WHERE metadata @> ${param_idx}::jsonb"

                query += f" ORDER BY distance LIMIT {k}"

                # Execute query
                rows = await conn.fetch(query, *params)

                # Convert rows to Documents
                results = []
                for row in rows:
                    doc = Document(
                        id=row["id"],
                        content=row["content"],
                        metadata=json.loads(row["metadata"])
                        if isinstance(row["metadata"], str)
                        else row["metadata"],
                        score=float(row["distance"]),
                    )
                    results.append(doc)

                return results

        except Exception as e:
            raise RetrievalError(f"Failed to search documents: {e}") from e

    async def delete_collection(self) -> None:
        """Delete the entire collection table.

        Raises:
            StorageError: If deletion fails
        """
        if not self._pool:
            raise StorageError("Connection pool not initialized")

        try:
            async with self._pool.acquire() as conn:
                await conn.execute(f"DROP TABLE IF EXISTS {self.collection_name}")

        except Exception as e:
            raise StorageError(f"Failed to delete collection: {e}") from e

    async def close(self) -> None:
        """Close the connection pool.

        Should be called when the vector store is no longer needed
        to release database connections.
        """
        if self._pool:
            await self._pool.close()
