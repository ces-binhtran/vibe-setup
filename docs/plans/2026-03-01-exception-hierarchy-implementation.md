# Exception Hierarchy Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement custom exception hierarchy for vibe-rag error handling

**Architecture:** Flat exception hierarchy with RAGException as base class, all specific exceptions inherit directly from it, enabling both broad and fine-grained error handling

**Tech Stack:** Python 3.10+, pytest

---

## Task 1: Create Exception Classes

**Files:**
- Create: `vibe_rag/utils/errors.py`
- Create: `tests/unit/test_errors.py`

**Step 1: Write failing test for exception hierarchy**

Create `tests/unit/test_errors.py`:
```python
"""Tests for custom exception hierarchy."""

import pytest
from vibe_rag.utils.errors import (
    RAGException,
    EmbeddingError,
    RetrievalError,
    LLMProviderError,
    StorageError,
    ConfigurationError,
)


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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_errors.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'vibe_rag.utils.errors'"

**Step 3: Implement exception classes**

Create `vibe_rag/utils/errors.py`:
```python
"""Custom exceptions for vibe-rag."""


class RAGException(Exception):
    """Base exception for all RAG errors."""
    pass


class EmbeddingError(RAGException):
    """Embedding generation failed."""
    pass


class RetrievalError(RAGException):
    """Document retrieval failed."""
    pass


class LLMProviderError(RAGException):
    """LLM provider error (API error, timeout, etc.)."""
    pass


class StorageError(RAGException):
    """Storage backend error."""
    pass


class ConfigurationError(RAGException):
    """Configuration validation error."""
    pass
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_errors.py -v`
Expected: PASS (3 tests)

**Step 5: Commit**

```bash
git add vibe_rag/utils/errors.py tests/unit/test_errors.py
git commit -m "feat: implement custom exception hierarchy

Why this change was needed:
- Framework needs standardized error handling across all components
- Users need to catch all framework errors or specific error types
- Provides clear error semantics for different failure modes

What changed:
- Created RAGException base class for all framework errors
- Implemented 5 specific exception types (Embedding, Retrieval, LLMProvider, Storage, Configuration)
- Added comprehensive unit tests for exception hierarchy

Technical notes:
- Flat hierarchy chosen for simplicity (YAGNI principle)
- All exceptions inherit directly from RAGException
- Can extend to multi-level hierarchy in future if needed"
```

---

## Task 2: Add Tests for Raising and Catching Exceptions

**Files:**
- Modify: `tests/unit/test_errors.py`

**Step 1: Write tests for raising each exception type**

Add to `tests/unit/test_errors.py`:
```python
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
```

**Step 2: Run tests to verify they pass**

Run: `pytest tests/unit/test_errors.py -v`
Expected: PASS (8 tests total)

**Step 3: Commit**

```bash
git add tests/unit/test_errors.py
git commit -m "test: add tests for raising and catching each exception type

Why this change was needed:
- Verify each exception can be raised and caught correctly
- Ensure error messages are preserved through raise/catch cycle
- Document expected usage patterns for each exception type

What changed:
- Added test for each of the 5 specific exception types
- Tests verify both raising and catching with message matching

Technical notes:
- Using pytest.raises with match parameter for message verification
- Each test follows same pattern for consistency"
```

---

## Task 3: Add Test for Catching All Exceptions via Base Class

**Files:**
- Modify: `tests/unit/test_errors.py`

**Step 1: Write test for catching all exceptions via RAGException**

Add to `tests/unit/test_errors.py`:
```python
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
```

**Step 2: Run tests to verify they pass**

Run: `pytest tests/unit/test_errors.py -v`
Expected: PASS (10 tests total)

**Step 3: Commit**

```bash
git add tests/unit/test_errors.py
git commit -m "test: verify catching all exceptions via base class

Why this change was needed:
- Users need to catch all framework errors with single except clause
- Verify exception hierarchy allows both broad and fine-grained catching
- Document expected catch patterns for framework users

What changed:
- Added test verifying all exceptions caught via RAGException
- Added test verifying specific handlers take precedence

Technical notes:
- Tests demonstrate exception handler resolution order
- Validates flat hierarchy design enables flexible error handling"
```

---

## Task 4: Update Package Exports

**Files:**
- Modify: `vibe_rag/utils/__init__.py`
- Modify: `vibe_rag/__init__.py`

**Step 1: Update utils package exports**

Edit `vibe_rag/utils/__init__.py`:
```python
"""Utility modules for vibe-rag."""

from vibe_rag.utils.errors import (
    RAGException,
    EmbeddingError,
    RetrievalError,
    LLMProviderError,
    StorageError,
    ConfigurationError,
)

__all__ = [
    "RAGException",
    "EmbeddingError",
    "RetrievalError",
    "LLMProviderError",
    "StorageError",
    "ConfigurationError",
]
```

**Step 2: Update main package exports**

Edit `vibe_rag/__init__.py` to add exception imports:
```python
"""
vibe-rag: Production-grade modular RAG framework.

A batteries-included but removable RAG framework with pluggable components.
"""

from vibe_rag.__version__ import __version__
from vibe_rag.utils.errors import (
    RAGException,
    EmbeddingError,
    RetrievalError,
    LLMProviderError,
    StorageError,
    ConfigurationError,
)

__all__ = [
    "__version__",
    "RAGException",
    "EmbeddingError",
    "RetrievalError",
    "LLMProviderError",
    "StorageError",
    "ConfigurationError",
]
```

**Step 3: Verify imports work**

Run: `python -c "from vibe_rag import RAGException, EmbeddingError; print('Imports successful')"`
Expected: "Imports successful"

**Step 4: Run all tests to ensure nothing broke**

Run: `pytest tests/unit/test_errors.py -v`
Expected: PASS (10 tests)

**Step 5: Commit**

```bash
git add vibe_rag/utils/__init__.py vibe_rag/__init__.py
git commit -m "feat: export exceptions in main package API

Why this change was needed:
- Users need to import exceptions from top-level package
- Enables clean imports like 'from vibe_rag import RAGException'
- Follows framework's public API design pattern

What changed:
- Added exception exports to vibe_rag/utils/__init__.py
- Added exception exports to vibe_rag/__init__.py
- All 6 exceptions now available from main package

Technical notes:
- Maintains flat import structure for user convenience
- Follows established pattern from existing framework components"
```

---

## Task 5: Add Integration Test for Exception Usage

**Files:**
- Create: `tests/unit/test_errors_integration.py`

**Step 1: Write integration test demonstrating real-world usage**

Create `tests/unit/test_errors_integration.py`:
```python
"""Integration tests demonstrating exception usage patterns."""

import pytest
from vibe_rag.utils.errors import (
    RAGException,
    EmbeddingError,
    RetrievalError,
    LLMProviderError,
    StorageError,
    ConfigurationError,
)


def mock_embedding_operation(should_fail: bool = False):
    """Mock function simulating embedding operation."""
    if should_fail:
        raise EmbeddingError("Failed to generate embeddings for batch")
    return [[0.1, 0.2, 0.3]]


def mock_retrieval_operation(should_fail: bool = False):
    """Mock function simulating retrieval operation."""
    if should_fail:
        raise RetrievalError("Vector search failed: connection timeout")
    return [{"content": "doc1", "score": 0.95}]


def test_catch_specific_exception_with_recovery():
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


def test_catch_all_framework_errors():
    """Test catching all framework errors with single handler."""
    errors_caught = []

    operations = [
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


def test_exception_chaining():
    """Test re-raising with exception chaining for context."""
    def high_level_operation():
        try:
            mock_retrieval_operation(should_fail=True)
        except RetrievalError as e:
            raise StorageError("Database connection lost") from e

    with pytest.raises(StorageError) as exc_info:
        high_level_operation()

    # Verify exception chain
    assert exc_info.value.__cause__ is not None
    assert isinstance(exc_info.value.__cause__, RetrievalError)


def test_multiple_exception_handlers():
    """Test multiple exception handlers in order."""
    def operation_with_multiple_failures(error_type: str):
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
```

**Step 2: Run tests to verify they pass**

Run: `pytest tests/unit/test_errors_integration.py -v`
Expected: PASS (5 tests)

**Step 3: Run full test suite**

Run: `pytest tests/unit/test_errors*.py -v`
Expected: PASS (15 tests total)

**Step 4: Commit**

```bash
git add tests/unit/test_errors_integration.py
git commit -m "test: add integration tests for exception usage patterns

Why this change was needed:
- Demonstrate real-world exception usage patterns
- Verify exceptions work correctly in retry logic and error recovery
- Document best practices for exception handling in framework

What changed:
- Added integration tests for exception recovery patterns
- Added tests for exception chaining and context preservation
- Added tests for multiple exception handlers

Technical notes:
- Tests use mock operations to simulate real framework behavior
- Demonstrates both specific and catch-all exception handling
- Validates exception hierarchy supports complex error handling scenarios"
```

---

## Task 6: Verify Test Coverage

**Files:**
- None (verification only)

**Step 1: Run tests with coverage report**

Run: `pytest tests/unit/test_errors*.py --cov=vibe_rag.utils.errors --cov-report=term-missing -v`
Expected: 100% coverage for `vibe_rag/utils/errors.py`

**Step 2: Review coverage output**

Expected output should show:
```
vibe_rag/utils/errors.py    100%
```

**Step 3: If coverage < 100%, add missing tests**

If any lines are not covered, add tests to cover them.

Run: `pytest tests/unit/test_errors*.py --cov=vibe_rag.utils.errors --cov-report=term-missing -v`
Expected: 100% coverage

**Step 4: Run full test suite one final time**

Run: `pytest tests/unit/test_errors*.py -v`
Expected: PASS (all 15 tests)

---

## Summary

**Tasks completed:**
1. ✅ Created exception classes in `vibe_rag/utils/errors.py`
2. ✅ Added tests for raising/catching each exception type
3. ✅ Added tests for catching all exceptions via base class
4. ✅ Updated package exports for public API
5. ✅ Added integration tests for real-world usage patterns
6. ✅ Verified 100% test coverage

**Acceptance criteria met:**
- ✅ All 6 exceptions inherit from RAGException
- ✅ Tests pass with 100% coverage
- ✅ Exceptions exported in main package API
- ✅ Clear docstrings on all exception classes
- ✅ Integration tests demonstrate usage patterns

**Files created:**
- `vibe_rag/utils/errors.py` (exception classes)
- `tests/unit/test_errors.py` (unit tests)
- `tests/unit/test_errors_integration.py` (integration tests)

**Files modified:**
- `vibe_rag/utils/__init__.py` (exports)
- `vibe_rag/__init__.py` (exports)

**Commits made:** 6 commits following conventional commit format with detailed reasoning

---

**Next steps:**
After this implementation is complete, the exception hierarchy will be ready to use throughout the framework. The next task in the implementation plan is to implement the LLM provider base interface and Gemini provider, which will use these exceptions for error handling.
