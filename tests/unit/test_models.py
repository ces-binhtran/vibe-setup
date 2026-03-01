"""Tests for core data models."""

import pytest
from vibe_rag.models import Document


def test_document_creation():
    """Test creating a Document with required fields."""
    doc = Document(
        content="Sample content",
        metadata={"source": "test.pdf"}
    )

    assert doc.content == "Sample content"
    assert doc.metadata == {"source": "test.pdf"}
    assert doc.id is not None  # Should auto-generate ID


def test_document_with_id():
    """Test creating a Document with explicit ID."""
    doc_id = "test-id-123"
    doc = Document(
        id=doc_id,
        content="Sample content"
    )

    assert doc.id == doc_id


def test_document_metadata_optional():
    """Test that metadata is optional."""
    doc = Document(content="Sample content")

    assert doc.metadata == {}  # Default to empty dict


def test_document_score_optional():
    """Test that score is optional and defaults to None."""
    doc = Document(content="Sample content")

    assert doc.score is None


def test_document_with_score():
    """Test creating a Document with similarity score."""
    doc = Document(
        content="Sample content",
        score=0.95
    )

    assert doc.score == 0.95


def test_document_id_auto_generation():
    """Test that IDs are auto-generated and unique."""
    doc1 = Document(content="Content 1")
    doc2 = Document(content="Content 2")

    assert doc1.id != doc2.id
    assert len(doc1.id) > 0
    assert len(doc2.id) > 0
