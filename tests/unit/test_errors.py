"""Tests for custom exception hierarchy."""

import pytest
from vibe_rag.utils.errors import (
    RAGException,
    EmbeddingError,
    RetrievalError,
    LLMProviderError,
    StorageError,
    ConfigurationError,
    DocumentProcessingError,
)
from vibe_rag.models import Document


def test_all_exceptions_inherit_from_rag_exception():
    """Test that all custom exceptions inherit from RAGException."""
    assert issubclass(EmbeddingError, RAGException)
    assert issubclass(RetrievalError, RAGException)
    assert issubclass(LLMProviderError, RAGException)
    assert issubclass(StorageError, RAGException)
    assert issubclass(ConfigurationError, RAGException)


def test_rag_exception_inherits_from_exception():
    """Test that RAGException inherits from Python's Exception."""
    assert issubclass(RAGException, Exception)


def test_rag_exception_message():
    """Test RAGException message handling."""
    error = RAGException("Test error message")
    assert str(error) == "Test error message"


def test_embedding_error_raise_and_catch():
    """Test raising and catching EmbeddingError."""
    with pytest.raises(EmbeddingError, match="embedding failed"):
        raise EmbeddingError("embedding failed")


def test_retrieval_error_raise_and_catch():
    """Test raising and catching RetrievalError."""
    with pytest.raises(RetrievalError, match="retrieval failed"):
        raise RetrievalError("retrieval failed")


def test_llm_provider_error_raise_and_catch():
    """Test raising and catching LLMProviderError."""
    with pytest.raises(LLMProviderError, match="llm failed"):
        raise LLMProviderError("llm failed")


def test_storage_error_raise_and_catch():
    """Test raising and catching StorageError."""
    with pytest.raises(StorageError, match="storage failed"):
        raise StorageError("storage failed")


def test_configuration_error_raise_and_catch():
    """Test raising and catching ConfigurationError."""
    with pytest.raises(ConfigurationError, match="config invalid"):
        raise ConfigurationError("config invalid")


def test_catch_all_exceptions_via_base():
    """Test catching all framework errors via RAGException base class."""
    exceptions = [
        EmbeddingError("embedding"),
        RetrievalError("retrieval"),
        LLMProviderError("llm"),
        StorageError("storage"),
        ConfigurationError("config"),
    ]

    for exc in exceptions:
        with pytest.raises(RAGException):
            raise exc


def test_specific_catch_preferred_over_base():
    """Test that specific exception handlers work correctly."""
    # Specific handler should catch before base handler
    try:
        raise EmbeddingError("test")
    except EmbeddingError as e:
        assert str(e) == "test"
        caught_specific = True
    except RAGException:
        caught_specific = False

    assert caught_specific, "Specific handler should catch before base handler"


def test_document_processing_error_basic():
    """Test basic DocumentProcessingError initialization."""
    error = DocumentProcessingError("Test error")
    assert str(error) == "Test error"
    assert error.file_path is None
    assert error.error_type is None
    assert error.original_error is None
    assert error.partial_results is None


def test_document_processing_error_with_context():
    """Test DocumentProcessingError with full context."""
    original = ValueError("Original error")
    partial_docs = [Document(content="test", metadata={"page": 1})]

    error = DocumentProcessingError(
        message="Failed to process document",
        file_path="/path/to/doc.pdf",
        error_type="CorruptPDFError",
        original_error=original,
        partial_results=partial_docs,
    )

    assert str(error) == "Failed to process document"
    assert error.file_path == "/path/to/doc.pdf"
    assert error.error_type == "CorruptPDFError"
    assert error.original_error is original
    assert error.partial_results == partial_docs
    assert len(error.partial_results) == 1


def test_document_processing_error_inheritance():
    """Test that DocumentProcessingError inherits from RAGException."""
    error = DocumentProcessingError("test")
    assert isinstance(error, RAGException)
    assert isinstance(error, Exception)
