# Async Context Manager for PostgresVectorStore

**Date:** 2026-03-01
**Status:** Approved
**Priority:** MEDIUM - Best practice

## Problem

PostgresVectorStore manages async resources (connection pool) but doesn't implement the async context manager protocol (`__aenter__`/`__aexit__`). This makes cleanup error-prone:

```python
# Current approach - easy to forget cleanup
store = PostgresVectorStore(...)
await store.initialize()
# ... use store ...
await store.close()  # Easy to forget!
```

Per CLAUDE.md guidelines: "Use async context managers for resource cleanup"

## Solution

Add async context manager protocol to `BaseVectorStore` so all vector store implementations support it automatically.

**Expected pattern:**
```python
async with PostgresVectorStore(...) as store:
    await store.add_documents(...)
    results = await store.similarity_search(query)
# Automatic cleanup
```

## Design

### Architecture

**Changes to `BaseVectorStore` (`vibe_rag/storage/base.py`):**

Add two concrete methods to the abstract base class:

```python
async def __aenter__(self):
    """Enter async context manager - initializes the store.

    Returns:
        Self for use in 'async with' statements
    """
    await self.initialize()
    return self

async def __aexit__(self, exc_type, exc_val, exc_tb):
    """Exit async context manager - closes the store.

    Args:
        exc_type: Exception type (if any)
        exc_val: Exception value (if any)
        exc_tb: Exception traceback (if any)

    Returns:
        None (don't suppress exceptions)
    """
    await self.close()
    return None
```

**Why in the base class:**
- All vector store implementations need this pattern
- DRY - implement once, works everywhere
- Consistent API across all storage backends (PostgreSQL, Pinecone, Weaviate, etc.)
- Follows Python's standard library pattern (e.g., `contextlib.AbstractAsyncContextManager`)

**Changes to `PostgresVectorStore`:**
- None! It inherits the context manager protocol from base class

### Key Design Decisions

1. **Return `None` from `__aexit__`** - Don't suppress exceptions, let them propagate
2. **Call existing abstract methods** - `initialize()` and `close()` already do the work
3. **Concrete implementation in base class** - No need for each subclass to implement
4. **Backward compatible** - Existing manual `initialize()`/`close()` pattern still works

### Alternatives Considered

**Approach 2: Abstract methods in base class**
- Make `__aenter__`/`__aexit__` abstract methods
- ❌ Rejected: Duplicates code across all implementations

**Approach 3: Mixin pattern**
- Create `AsyncContextManagerMixin` class
- ❌ Rejected: Over-engineering for a 5-line addition

## Testing Strategy

### Test Coverage

1. **Test context manager protocol on BaseVectorStore** (new file: `tests/unit/storage/test_base_vector_store.py`):
   - `test_context_manager_calls_initialize_on_enter` - verify `__aenter__` calls `initialize()`
   - `test_context_manager_calls_close_on_exit` - verify `__aexit__` calls `close()`
   - `test_context_manager_returns_self` - verify `__aenter__` returns the store instance
   - `test_context_manager_propagates_exceptions` - verify exceptions aren't suppressed
   - `test_context_manager_closes_even_on_exception` - verify cleanup happens on error

2. **Integration test with PostgresVectorStore** (add to `tests/unit/storage/test_postgres_vector_store.py`):
   - `test_context_manager_usage` - verify real-world usage pattern works

### Testing Approach
- Use a concrete mock implementation of BaseVectorStore for base class tests
- Mock asyncpg for PostgresVectorStore tests (existing pattern)
- Verify both happy path and error scenarios

## Documentation Updates

1. **Update `BaseVectorStore` docstring** - Add usage example showing context manager pattern
2. **Update `PostgresVectorStore` docstring** - Replace manual initialize/close example with context manager pattern
3. **No changes to external docs** - This is an internal API improvement, not a breaking change

## Backward Compatibility

- ✅ Existing code using `await store.initialize()` and `await store.close()` continues to work
- ✅ No breaking changes - purely additive
- ✅ Users can migrate to context manager at their own pace

## Success Criteria

- [ ] `BaseVectorStore` has `__aenter__` and `__aexit__` methods
- [ ] Tests verify context manager protocol works correctly
- [ ] Tests verify cleanup happens even on exceptions
- [ ] PostgresVectorStore inherits behavior without code changes
- [ ] Documentation examples use context manager pattern
- [ ] All existing tests pass
