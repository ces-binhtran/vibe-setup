"""Integration tests for pipeline composition."""

import pytest
from vibe_rag.pipeline import PipelineBuilder, PipelineContext
from vibe_rag.retrievers import VectorRetriever
from vibe_rag.testing.mocks import MockVectorStore, MockLLMProvider
from vibe_rag.models import Document


@pytest.mark.asyncio
async def test_pipeline_with_vector_retriever():
    """Test complete pipeline with VectorRetriever."""
    # Setup
    storage = MockVectorStore(collection_name="test")
    provider = MockLLMProvider()

    # Add test documents with embeddings
    docs = [
        Document(content="Python is a programming language", score=0.95),
        Document(content="Machine learning with Python", score=0.85),
    ]
    # Generate embeddings for the documents
    embeddings = await provider.embed([doc.content for doc in docs])
    # Store as tuples (Document, embedding) as expected by MockVectorStore
    storage.documents["test"] = [(doc, emb) for doc, emb in zip(docs, embeddings)]

    # Build pipeline
    retriever = VectorRetriever(storage, provider, top_k=2)
    pipeline = PipelineBuilder().add_component(retriever).build()

    # Execute
    context = PipelineContext(query="What is Python?")
    for component in pipeline:
        context = await component.process(context)

    # Verify
    assert len(context.documents) == 2
    assert context.documents[0].content == "Python is a programming language"
    assert "VectorRetriever" in context.metadata
    assert len(context._trace) == 1
    assert context._trace[0]["component"] == "VectorRetriever"


@pytest.mark.asyncio
async def test_pipeline_context_flow():
    """Test that context flows through multiple components."""
    storage = MockVectorStore(collection_name="test")
    provider = MockLLMProvider()

    # Add test documents with embeddings
    doc = Document(content="doc1")
    embeddings = await provider.embed([doc.content])
    storage.documents["test"] = [(doc, embeddings[0])]

    # Build pipeline with multiple retrievers (simulate multi-stage)
    retriever1 = VectorRetriever(storage, provider, top_k=1)
    retriever2 = VectorRetriever(storage, provider, top_k=1)

    pipeline = (
        PipelineBuilder()
        .add_component(retriever1)
        .add_component(retriever2)
        .build()
    )

    # Execute
    context = PipelineContext(query="test")
    for component in pipeline:
        context = await component.process(context)

    # Verify metadata accumulated
    assert len(context._trace) == 2
    assert context._trace[0]["component"] == "VectorRetriever"
    assert context._trace[1]["component"] == "VectorRetriever"
    # metadata dict has 1 entry (both components share same name, last one wins)
    assert len(context.metadata) == 1
    # But trace has both executions
    assert "VectorRetriever" in context.metadata


@pytest.mark.asyncio
async def test_pipeline_serialization():
    """Test that pipeline context can be serialized."""
    storage = MockVectorStore(collection_name="test")
    provider = MockLLMProvider()

    # Add test document with embedding
    doc = Document(content="test doc")
    embeddings = await provider.embed([doc.content])
    storage.documents["test"] = [(doc, embeddings[0])]

    retriever = VectorRetriever(storage, provider)
    pipeline = PipelineBuilder().add_component(retriever).build()

    context = PipelineContext(query="test")
    for component in pipeline:
        context = await component.process(context)

    # Serialize
    result = context.to_dict()

    assert result["query"] == "test"
    assert len(result["documents"]) == 1
    assert "metadata" in result
    assert "trace" in result
    assert len(result["trace"]) == 1
