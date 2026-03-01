"""Tests for PipelineContext."""

import pytest
from vibe_rag.pipeline.context import PipelineContext
from vibe_rag.models import Document


def test_pipeline_context_creation():
    """Test creating PipelineContext with query."""
    context = PipelineContext(query="What is RAG?")

    assert context.query == "What is RAG?"
    assert context.documents == []
    assert context.answer is None
    assert context.metadata == {}
    assert context._trace == []


def test_pipeline_context_add_component_metadata():
    """Test adding component metadata."""
    context = PipelineContext(query="test")

    context.add_component_metadata(
        "VectorRetriever",
        {"top_k": 5, "duration_ms": 123.45}
    )

    assert "VectorRetriever" in context.metadata
    assert context.metadata["VectorRetriever"]["top_k"] == 5
    assert len(context._trace) == 1
    assert context._trace[0]["component"] == "VectorRetriever"
    assert "timestamp" in context._trace[0]


def test_pipeline_context_to_dict():
    """Test exporting context to dictionary."""
    context = PipelineContext(query="test")
    context.documents = [Document(content="doc1")]
    context.answer = "answer text"

    result = context.to_dict()

    assert result["query"] == "test"
    assert len(result["documents"]) == 1
    assert result["answer"] == "answer text"
    assert "metadata" in result
    assert "trace" in result


def test_pipeline_context_empty_documents():
    """Test that documents defaults to empty list."""
    context = PipelineContext(query="test")

    assert isinstance(context.documents, list)
    assert len(context.documents) == 0
