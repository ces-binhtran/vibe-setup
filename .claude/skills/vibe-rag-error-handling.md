---
name: vibe-rag-error-handling
description: Guide exception design and error handling patterns - uses custom exceptions with specific error types, no silent failures
---

# vibe-rag Error Handling

Use this skill when implementing error handling or creating exceptions.

## Custom Exception Hierarchy

**All vibe-rag errors inherit from `RAGException`:**

- `RAGException` - Base for all framework errors
- `EmbeddingError` - Embedding generation failures
- `RetrievalError` - Document retrieval failures
- `LLMProviderError` - LLM API failures
- `StorageError` - Database/storage failures
- `ConfigurationError` - Invalid configuration

**Location:** `vibe_rag/utils/errors.py`

## Error Handling Pattern

**Always wrap external errors with vibe-rag exceptions:**

```python
try:
    result = await external_api_call()
except ExternalAPIError as e:
    raise LLMProviderError(f"Failed to generate: {e}")
```

**Why?**
- Isolates external library errors from internal code
- Provides consistent error interface to users
- Enables specific exception handling at higher levels

## NO Silent Failures

**NEVER do these:**

❌ **Don't catch exceptions and ignore them:**

```python
try:
    result = risky_operation()
except Exception:
    pass  # ❌ WRONG: Silent failure
```

❌ **Don't return `None` on errors:**

```python
def process_data(data):
    try:
        return transform(data)
    except Exception:
        return None  # ❌ WRONG: Caller doesn't know it failed
```

✅ **DO raise specific, informative exceptions:**

```python
def process_data(data):
    try:
        return transform(data)
    except TransformError as e:
        raise ProcessingError(f"Failed to process {data}: {e}")
```

**Principle:** Errors should be explicit and propagated, not hidden.
