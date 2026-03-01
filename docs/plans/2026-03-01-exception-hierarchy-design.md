# Custom Exception Hierarchy Design

**Date:** 2026-03-01
**Project:** vibe-rag
**Version:** 1.0
**Status:** Approved

## Executive Summary

This document outlines the design for vibe-rag's custom exception hierarchy. We implement a simple, flat hierarchy where all framework-specific exceptions inherit directly from `RAGException`, enabling both broad and fine-grained error handling.

**Key Design Principles:**
- **Simple and flat** - All exceptions inherit directly from RAGException
- **Clear semantics** - Each exception has a specific, well-documented purpose
- **Easy to catch** - Single base class catches all framework errors
- **Extensible** - Can add more exceptions or intermediate classes later

---

## 1. Exception Hierarchy Structure

### 1.1 Visual Hierarchy

```
Exception (Python built-in)
    └── RAGException (base for all vibe-rag errors)
        ├── EmbeddingError
        ├── RetrievalError
        ├── LLMProviderError
        ├── StorageError
        └── ConfigurationError
```

### 1.2 Design Rationale

**Why a flat hierarchy?**
- **MVP Phase (Phase 1)** - Keep it simple for Core Foundation
- **YAGNI principle** - Don't add intermediate classes until we need them
- **Easy to understand** - Clear parent-child relationships
- **Easy to test** - Simple inheritance checks
- **Matches implementation plan** - Directly implements Task 2 specification

**Why not a multi-level hierarchy?**
- We don't yet have patterns showing we need grouping (e.g., "all provider errors")
- Can always add intermediate classes in Phase 5 (Production Hardening) if needed
- Premature categorization adds complexity without proven benefit

---

## 2. Exception Definitions

### 2.1 RAGException (Base)

```python
class RAGException(Exception):
    """Base exception for all RAG errors."""
    pass
```

**Purpose:** Top-level exception for the entire framework. Allows catching any vibe-rag error with a single `except` clause.

**Usage:**
```python
try:
    result = await rag.query("question")
except RAGException as e:
    logger.error(f"RAG operation failed: {e}")
    return error_response()
```

### 2.2 EmbeddingError

```python
class EmbeddingError(RAGException):
    """Embedding generation failed."""
    pass
```

**Purpose:** Raised when embedding generation fails (API errors, invalid inputs, etc.)

**Raised by:**
- `BaseLLMProvider.embed()`
- `GeminiProvider.embed()`
- Document processing when generating embeddings

**Usage:**
```python
try:
    embeddings = await provider.embed(texts)
except EmbeddingError as e:
    logger.warning(f"Embedding failed: {e}")
    fallback_to_cached_embeddings()
```

### 2.3 RetrievalError

```python
class RetrievalError(RAGException):
    """Document retrieval failed."""
    pass
```

**Purpose:** Raised when vector similarity search or document retrieval fails

**Raised by:**
- `BaseVectorStore.similarity_search()`
- `PostgresVectorStore.similarity_search()`
- Retriever components in pipeline

**Usage:**
```python
try:
    docs = await store.similarity_search(query_embedding, collection)
except RetrievalError as e:
    logger.error(f"Retrieval failed: {e}")
    return []  # Return empty results
```

### 2.4 LLMProviderError

```python
class LLMProviderError(RAGException):
    """LLM provider error (API error, timeout, etc.)."""
    pass
```

**Purpose:** Raised when LLM text generation fails

**Raised by:**
- `BaseLLMProvider.generate()`
- `GeminiProvider.generate()`
- Any LLM provider implementation

**Usage:**
```python
try:
    response = await provider.generate(prompt)
except LLMProviderError as e:
    logger.error(f"LLM generation failed: {e}")
    retry_with_backoff()
```

### 2.5 StorageError

```python
class StorageError(RAGException):
    """Storage backend error."""
    pass
```

**Purpose:** Raised when database/storage operations fail

**Raised by:**
- `BaseVectorStore.add_documents()`
- `BaseVectorStore.delete_collection()`
- `PostgresVectorStore` connection/transaction errors

**Usage:**
```python
try:
    ids = await store.add_documents(docs, collection, embeddings)
except StorageError as e:
    logger.error(f"Storage operation failed: {e}")
    rollback_transaction()
```

### 2.6 ConfigurationError

```python
class ConfigurationError(RAGException):
    """Configuration validation error."""
    pass
```

**Purpose:** Raised when configuration is invalid or missing required parameters

**Raised by:**
- Pydantic model validation in `RAGConfig`
- Provider/storage configuration validation
- Pipeline component configuration

**Usage:**
```python
try:
    config = RAGConfig.from_yaml("config.yaml")
except ConfigurationError as e:
    logger.error(f"Invalid configuration: {e}")
    print_config_help()
```

---

## 3. Implementation Details

### 3.1 File Location

**File:** `vibe_rag/utils/errors.py`

**Why `utils/errors.py`?**
- Matches implementation plan structure
- Centralized location for all exceptions
- Easy to import from anywhere in the framework

### 3.2 Complete Implementation

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

### 3.3 Package Exports

Update `vibe_rag/__init__.py`:
```python
from vibe_rag.utils.errors import (
    RAGException,
    EmbeddingError,
    RetrievalError,
    LLMProviderError,
    StorageError,
    ConfigurationError,
)

__all__ = [
    # ... other exports
    "RAGException",
    "EmbeddingError",
    "RetrievalError",
    "LLMProviderError",
    "StorageError",
    "ConfigurationError",
]
```

---

## 4. Testing Strategy

### 4.1 Test Coverage

**File:** `tests/unit/test_errors.py`

**Tests to implement:**
1. Verify all exceptions inherit from `RAGException`
2. Verify `RAGException` inherits from `Exception`
3. Test exception message handling
4. Test raising and catching each exception type
5. Test catching all exceptions via `RAGException`

### 4.2 Test Examples

```python
def test_exception_hierarchy():
    """Test that all exceptions inherit from RAGException."""
    assert issubclass(EmbeddingError, RAGException)
    assert issubclass(RetrievalError, RAGException)
    assert issubclass(LLMProviderError, RAGException)
    assert issubclass(StorageError, RAGException)
    assert issubclass(ConfigurationError, RAGException)
    assert issubclass(RAGException, Exception)


def test_embedding_error_raise_and_catch():
    """Test raising and catching EmbeddingError."""
    with pytest.raises(EmbeddingError, match="test message"):
        raise EmbeddingError("test message")


def test_catch_all_via_base():
    """Test catching all framework errors via RAGException."""
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
```

---

## 5. Usage Patterns

### 5.1 Catching Specific Errors

```python
async def generate_with_fallback(provider, prompt):
    """Generate with fallback on error."""
    try:
        return await provider.generate(prompt)
    except LLMProviderError as e:
        logger.warning(f"Primary provider failed: {e}")
        return await backup_provider.generate(prompt)
```

### 5.2 Catching All Framework Errors

```python
async def safe_query(rag_engine, question):
    """Query with broad error handling."""
    try:
        return await rag_engine.query(question)
    except RAGException as e:
        logger.error(f"RAG query failed: {e}")
        return {"error": str(e), "answer": None}
```

### 5.3 Re-raising with Context

```python
async def embed_documents(provider, texts):
    """Embed documents with error context."""
    try:
        return await provider.embed(texts)
    except Exception as e:
        raise EmbeddingError(f"Failed to embed {len(texts)} documents: {e}")
```

---

## 6. Future Considerations

### 6.1 Potential Extensions (Phase 5)

If we find we're catching groups of exceptions frequently, we could add intermediate classes:

```python
class ProviderException(RAGException):
    """Base for all provider errors."""
    pass

class LLMProviderError(ProviderException):
    """LLM provider error."""
    pass

class EmbeddingError(ProviderException):
    """Embedding generation failed."""
    pass
```

**When to add this:**
- After Phase 3-4 when we have multiple providers
- If we see patterns like "catch all provider errors"
- If error handling becomes repetitive

### 6.2 Rich Exception Context (Optional)

Could add optional context dictionaries for debugging:

```python
class RAGException(Exception):
    """Base exception for all RAG errors."""

    def __init__(self, message: str, context: dict = None):
        super().__init__(message)
        self.context = context or {}
```

**When to add this:**
- Phase 5 (Production Hardening)
- After we understand what context is most useful
- If debugging becomes difficult without it

---

## 7. Acceptance Criteria

This design is complete when:

1. ✅ All 6 exceptions defined in `vibe_rag/utils/errors.py`
2. ✅ All exceptions inherit from `RAGException`
3. ✅ Comprehensive unit tests with 100% coverage
4. ✅ Exceptions exported in main package `__init__.py`
5. ✅ Clear docstrings explaining when each exception is raised
6. ✅ Examples demonstrating usage patterns

---

## 8. Implementation Checklist

- [ ] Create `vibe_rag/utils/errors.py`
- [ ] Define `RAGException` base class
- [ ] Define 5 specific exception classes
- [ ] Add docstrings to all exceptions
- [ ] Create `tests/unit/test_errors.py`
- [ ] Write tests for exception hierarchy
- [ ] Write tests for raising/catching each exception
- [ ] Update `vibe_rag/__init__.py` exports
- [ ] Update `vibe_rag/utils/__init__.py` exports
- [ ] Run tests and verify 100% coverage
- [ ] Commit with meaningful message

---

**End of Design Document**
