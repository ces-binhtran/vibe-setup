"""Tests for BaseVectorStore abstract interface."""

import pytest

from vibe_rag.models import Document
from vibe_rag.storage.base import BaseVectorStore


class ConcreteVectorStore(BaseVectorStore):
    """Concrete implementation for testing abstract interface."""

    async def add_documents(
        self, documents: list[Document], embeddings: list[list[float]]
    ) -> list[str]:
        return [doc.id for doc in documents]

    async def similarity_search(
        self,
        query_embedding: list[float],
        k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[Document]:
        return []

    async def delete_collection(self) -> None:
        pass


def test_base_vector_store_is_abstract():
    """BaseVectorStore cannot be instantiated directly."""
    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        BaseVectorStore(collection_name="test")


def test_base_vector_store_requires_add_documents():
    """Subclass must implement add_documents method."""

    class IncompleteStore(BaseVectorStore):
        async def similarity_search(
            self,
            query_embedding: list[float],
            k: int = 5,
            filter_metadata: dict | None = None,
        ) -> list[Document]:
            return []

        async def delete_collection(self) -> None:
            pass

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompleteStore(collection_name="test")


def test_base_vector_store_requires_similarity_search():
    """Subclass must implement similarity_search method."""

    class IncompleteStore(BaseVectorStore):
        async def add_documents(
            self, documents: list[Document], embeddings: list[list[float]]
        ) -> list[str]:
            return [doc.id for doc in documents]

        async def delete_collection(self) -> None:
            pass

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompleteStore(collection_name="test")


def test_base_vector_store_requires_delete_collection():
    """Subclass must implement delete_collection method."""

    class IncompleteStore(BaseVectorStore):
        async def add_documents(
            self, documents: list[Document], embeddings: list[list[float]]
        ) -> list[str]:
            return [doc.id for doc in documents]

        async def similarity_search(
            self,
            query_embedding: list[float],
            k: int = 5,
            filter_metadata: dict | None = None,
        ) -> list[Document]:
            return []

    with pytest.raises(TypeError, match="Can't instantiate abstract class"):
        IncompleteStore(collection_name="test")


def test_concrete_implementation_can_be_instantiated():
    """Concrete implementation with all methods can be instantiated."""
    store = ConcreteVectorStore(collection_name="test")
    assert store.collection_name == "test"


@pytest.mark.asyncio
async def test_concrete_implementation_add_documents():
    """Concrete implementation can add documents."""
    store = ConcreteVectorStore(collection_name="test")
    docs = [Document(content="test")]
    embeddings = [[1.0, 2.0, 3.0]]

    result = await store.add_documents(docs, embeddings)

    assert len(result) == 1
    assert result[0] == docs[0].id


@pytest.mark.asyncio
async def test_concrete_implementation_similarity_search():
    """Concrete implementation can perform similarity search."""
    store = ConcreteVectorStore(collection_name="test")
    query_embedding = [1.0, 2.0, 3.0]

    result = await store.similarity_search(query_embedding, k=5)

    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_concrete_implementation_delete_collection():
    """Concrete implementation can delete collection."""
    store = ConcreteVectorStore(collection_name="test")

    await store.delete_collection()  # Should not raise
