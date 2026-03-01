"""Integration tests demonstrating exception usage patterns."""

from collections.abc import Callable

import pytest

from vibe_rag.utils.errors import (
    ConfigurationError,
    EmbeddingError,
    RAGException,
    RetrievalError,
    StorageError,
)


def mock_embedding_operation(should_fail: bool = False) -> list[list[float]]:
    """Mock function simulating embedding operation."""
    if should_fail:
        raise EmbeddingError("Failed to generate embeddings for batch")
    return [[0.1, 0.2, 0.3]]


def mock_retrieval_operation(should_fail: bool = False) -> list[dict[str, float | str]]:
    """Mock function simulating retrieval operation."""
    if should_fail:
        raise RetrievalError("Vector search failed: connection timeout")
    return [{"content": "doc1", "score": 0.95}]


def test_catch_specific_exception_with_recovery() -> None:
    """Test catching specific exception and recovering."""
    # Simulate retry logic
    attempts = 0
    max_attempts = 2
    result = None

    while attempts < max_attempts:
        try:
            result = mock_embedding_operation(should_fail=(attempts == 0))
            break
        except EmbeddingError:
            attempts += 1
            if attempts >= max_attempts:
                raise

    assert result is not None
    assert attempts == 1  # Failed once, succeeded on retry


def test_catch_all_framework_errors() -> None:
    """Test catching all framework errors with single handler."""
    errors_caught: list[str] = []

    operations: list[Callable[[], object]] = [
        lambda: mock_embedding_operation(should_fail=True),
        lambda: mock_retrieval_operation(should_fail=True),
    ]

    for operation in operations:
        try:
            operation()
        except RAGException as e:
            errors_caught.append(type(e).__name__)

    assert len(errors_caught) == 2
    assert "EmbeddingError" in errors_caught
    assert "RetrievalError" in errors_caught


def test_exception_chaining() -> None:
    """Test re-raising with exception chaining for context."""
    def high_level_operation() -> None:
        try:
            mock_retrieval_operation(should_fail=True)
        except RetrievalError as e:
            raise StorageError("Database connection lost") from e

    with pytest.raises(StorageError) as exc_info:
        high_level_operation()

    # Verify exception chain
    assert exc_info.value.__cause__ is not None
    assert isinstance(exc_info.value.__cause__, RetrievalError)


def test_multiple_exception_handlers() -> None:
    """Test multiple exception handlers in order."""
    def operation_with_multiple_failures(error_type: str) -> None:
        if error_type == "embedding":
            raise EmbeddingError("Embedding failed")
        elif error_type == "storage":
            raise StorageError("Storage failed")
        elif error_type == "config":
            raise ConfigurationError("Invalid config")

    # Test specific handlers
    with pytest.raises(EmbeddingError):
        operation_with_multiple_failures("embedding")

    with pytest.raises(StorageError):
        operation_with_multiple_failures("storage")

    with pytest.raises(ConfigurationError):
        operation_with_multiple_failures("config")

    # Test catch-all handler
    for error_type in ["embedding", "storage", "config"]:
        with pytest.raises(RAGException):
            operation_with_multiple_failures(error_type)
