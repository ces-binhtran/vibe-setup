"""Tests demonstrating usage of vibe-rag testing utilities.

This module serves as:
1. Verification that testing utilities work correctly
2. Examples for developers writing new tests
3. Documentation through executable code

Tests are organized to demonstrate:
- Fixture usage (sample_documents, sample_embeddings)
- MockLLMProvider capabilities
- MockVectorStore capabilities
"""

from unittest.mock import AsyncMock

import pytest

from vibe_rag.models import Document
from vibe_rag.testing import MockLLMProvider, MockVectorStore


# ------------------------------------------------------------------------------
# Fixture Usage Tests
# ------------------------------------------------------------------------------


@pytest.mark.unit
def test_sample_documents_fixture(sample_documents):
    """Verify sample_documents fixture provides test data."""
    assert len(sample_documents) == 3
    assert all(isinstance(doc, Document) for doc in sample_documents)
    assert sample_documents[0].content == "Python programming guide for beginners"
    assert sample_documents[1].content == "Machine learning tutorial with practical examples"
    assert sample_documents[2].content == "Data science handbook covering statistics and visualization"


@pytest.mark.unit
def test_sample_embeddings_fixture(sample_embeddings):
    """Verify sample_embeddings fixture provides embedding vectors."""
    assert len(sample_embeddings) == 3
    assert all(isinstance(emb, list) for emb in sample_embeddings)
    assert all(len(emb) == 768 for emb in sample_embeddings)
    assert all(isinstance(val, float) for emb in sample_embeddings for val in emb)


# ------------------------------------------------------------------------------
# MockLLMProvider Tests
# ------------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_llm_provider_generate():
    """Test MockLLMProvider.generate() returns mock response."""
    provider = MockLLMProvider()

    response = await provider.generate(
        prompt="What is Python?",
        temperature=0.7,
        max_tokens=100
    )

    assert isinstance(response, str)
    assert response == "Mock response to: What is Python?"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_llm_provider_embed():
    """Test MockLLMProvider.embed() returns mock embeddings."""
    provider = MockLLMProvider()

    texts = ["Python is great", "Databases store data"]
    embeddings = await provider.embed(texts)

    assert len(embeddings) == 2
    assert all(isinstance(emb, list) for emb in embeddings)
    assert all(len(emb) == 768 for emb in embeddings)
    assert all(isinstance(val, float) for emb in embeddings for val in emb)


# ------------------------------------------------------------------------------
# MockVectorStore Tests
# ------------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_vector_store_add_and_search(sample_documents, sample_embeddings):
    """Test MockVectorStore.add_documents() and similarity_search() operations."""
    store = MockVectorStore()

    # Add documents
    await store.add_documents(
        documents=sample_documents,
        collection_name="test_collection",
        embeddings=sample_embeddings
    )

    # Search for similar documents
    query_embedding = sample_embeddings[0]
    results = await store.similarity_search(
        query_embedding=query_embedding,
        collection_name="test_collection",
        top_k=2
    )

    assert len(results) == 2
    assert all(isinstance(doc, Document) for doc in results)
    assert all(doc.score is not None for doc in results)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_vector_store_metadata_filtering(sample_embeddings):
    """Test MockVectorStore metadata filtering."""
    store = MockVectorStore()

    # Add documents with metadata
    docs_with_metadata = [
        Document(
            content="Python is great",
            metadata={"category": "programming", "year": 2023}
        ),
        Document(
            content="Machine learning rocks",
            metadata={"category": "ai", "year": 2023}
        ),
        Document(
            content="Databases are essential",
            metadata={"category": "data", "year": 2022}
        )
    ]

    await store.add_documents(
        documents=docs_with_metadata,
        collection_name="filtered_collection",
        embeddings=sample_embeddings
    )

    # Search with metadata filter
    query_embedding = sample_embeddings[0]
    results = await store.similarity_search(
        query_embedding=query_embedding,
        collection_name="filtered_collection",
        top_k=5,
        filters={"category": "programming"}
    )

    assert len(results) == 1
    assert results[0].metadata["category"] == "programming"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_vector_store_delete():
    """Test MockVectorStore.delete_collection() operation."""
    store = MockVectorStore()

    # Add a document
    doc = Document(id="test_doc_123", content="Test content")
    embedding = [0.1] * 768

    await store.add_documents(
        documents=[doc],
        collection_name="delete_test",
        embeddings=[embedding]
    )

    # Delete the collection
    await store.delete_collection(
        collection_name="delete_test"
    )

    # Search should return no results (collection deleted)
    results = await store.similarity_search(
        query_embedding=embedding,
        collection_name="delete_test",
        top_k=10
    )

    assert len(results) == 0
