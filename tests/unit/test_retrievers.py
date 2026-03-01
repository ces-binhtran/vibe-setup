"""Tests for retriever components."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from vibe_rag.retrievers.vector import VectorRetriever
from vibe_rag.pipeline.context import PipelineContext
from vibe_rag.models import Document
from vibe_rag.testing.mocks import MockVectorStore, MockLLMProvider
from vibe_rag.utils.errors import RetrievalError, ConfigurationError


def test_vector_retriever_initialization():
    """Test VectorRetriever initialization."""
    storage = MockVectorStore(collection_name="test")
    provider = MockLLMProvider()

    retriever = VectorRetriever(
        storage=storage,
        provider=provider,
        top_k=3
    )

    assert retriever.storage == storage
    assert retriever.provider == provider
    assert retriever.top_k == 3
    assert retriever.component_type == "retriever"
    assert retriever.component_name == "VectorRetriever"


@pytest.mark.asyncio
async def test_vector_retriever_process():
    """Test VectorRetriever processes context and retrieves documents."""
    # Setup mocks
    storage = MockVectorStore(collection_name="test")
    provider = MockLLMProvider()

    # Add mock documents to storage with embeddings
    docs = [
        Document(content="Document 1"),
        Document(content="Document 2"),
        Document(content="Document 3"),
    ]
    embeddings = [[0.1] * 768, [0.2] * 768, [0.3] * 768]
    # Store as tuples (doc, embedding)
    storage.documents["test"] = [(doc, emb) for doc, emb in zip(docs, embeddings)]

    # Create retriever
    retriever = VectorRetriever(
        storage=storage,
        provider=provider,
        top_k=3
    )

    # Process
    context = PipelineContext(query="test query")
    result = await retriever.process(context)

    # Verify
    assert len(result.documents) == 3
    assert result.documents[0].content == "Document 1"
    assert "VectorRetriever" in result.metadata
    assert result.metadata["VectorRetriever"]["top_k"] == 3
    assert result.metadata["VectorRetriever"]["num_results"] == 3
    assert "duration_ms" in result.metadata["VectorRetriever"]


@pytest.mark.asyncio
async def test_vector_retriever_validates_context():
    """Test that VectorRetriever validates context has query."""
    storage = MockVectorStore(collection_name="test")
    provider = MockLLMProvider()
    retriever = VectorRetriever(storage, provider)

    context = PipelineContext(query="")

    with pytest.raises(ConfigurationError, match="requires context.query"):
        retriever.validate_context(context)


@pytest.mark.asyncio
async def test_vector_retriever_handles_errors():
    """Test that VectorRetriever handles errors properly."""
    storage = MockVectorStore(collection_name="test")
    provider = MockLLMProvider()

    # Make storage raise error
    storage.similarity_search = AsyncMock(side_effect=Exception("DB error"))

    retriever = VectorRetriever(storage, provider)
    context = PipelineContext(query="test")

    with pytest.raises(RetrievalError, match="VectorRetriever failed"):
        await retriever.process(context)


@pytest.mark.asyncio
async def test_vector_retriever_with_metadata_filters():
    """Test VectorRetriever with metadata filters."""
    storage = MockVectorStore(collection_name="test")
    provider = MockLLMProvider()

    retriever = VectorRetriever(
        storage=storage,
        provider=provider,
        filter_metadata={"source": "docs"}
    )

    context = PipelineContext(query="test")
    result = await retriever.process(context)

    assert result.metadata["VectorRetriever"]["filter_metadata"] == {"source": "docs"}
