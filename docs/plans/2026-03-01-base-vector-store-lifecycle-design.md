# BaseVectorStore Lifecycle Methods Design

**Date:** 2026-03-01
**Status:** Approved
**Priority:** MEDIUM - Design consistency

## Problem

PostgresVectorStore adds `initialize()` and `close()` lifecycle methods that aren't in the BaseVectorStore interface, breaking the adapter pattern.

**Current state:**
- `BaseVectorStore`: `add_documents`, `similarity_search`, `delete_collection`
- `PostgresVectorStore`: adds `initialize()`, `close()` (not in base interface)

**CLAUDE.md states:** "All storage backends implement BaseVectorStore" (Adapter Pattern)

This violates the adapter pattern - implementations should not add public methods not in the interface.

## Goal

Add `initialize()` and `close()` to BaseVectorStore interface to maintain adapter pattern integrity and ensure all vector store implementations have explicit lifecycle management.

## Design Decision

**Approach:** Add both methods as abstract methods (not concrete with default implementations)

**Rationale:**
1. **Adapter pattern integrity** - All implementations must have same interface
2. **Explicit contract** - Forces developers to think about lifecycle, even if it's a no-op
3. **Type safety** - Type checkers will enforce implementation
4. **Production-ready** - Most production vector stores need lifecycle management (connection pools, cleanup)
5. **Already implemented** - PostgresVectorStore already has both methods

**Trade-off accepted:** Simple implementations (e.g., in-memory stores) must write explicit no-op methods instead of inheriting defaults.

## Architecture

### Interface Addition

Add to `BaseVectorStore` (vibe_rag/storage/base.py):

```python
@abstractmethod
async def initialize(self) -> None:
    """Initialize storage backend (create connections, tables, etc.).

    This method must be called before using the vector store.
    For implementations that don't need initialization, this can be a no-op.

    Raises:
        StorageError: If initialization fails
    """
    pass

@abstractmethod
async def close(self) -> None:
    """Close connections and cleanup resources.

    This method should be called when the vector store is no longer needed.
    For implementations that don't need cleanup, this can be a no-op.
    """
    pass
```

### Method Placement

- `initialize()`: After `__init__`, before `add_documents`
- `close()`: At end of class, after `delete_collection`

### Implementation Requirements

All future vector store implementations MUST implement both methods:

**For stores with resources (PostgreSQL, Redis, etc.):**
```python
async def initialize(self) -> None:
    """Create connection pool, initialize schema."""
    self._pool = await create_pool(...)
    await self._create_schema()

async def close(self) -> None:
    """Close connection pool."""
    if self._pool:
        await self._pool.close()
```

**For stores without resources (in-memory, etc.):**
```python
async def initialize(self) -> None:
    """No initialization needed for in-memory store."""
    pass

async def close(self) -> None:
    """No cleanup needed for in-memory store."""
    pass
```

## Impact Analysis

### Files Modified
- `vibe_rag/storage/base.py` - Add abstract methods

### Files NOT Modified
- `vibe_rag/storage/postgres_vector.py` - Already implements both methods correctly

### Future Implementations
All future vector store implementations must implement both methods (can be no-ops).

## Testing Strategy

No new tests needed:
- Existing tests for PostgresVectorStore already call `initialize()` and `close()`
- Abstract method decorator enforces implementation at class definition time
- Type checkers (mypy) will catch missing implementations

## Alternatives Considered

### Alternative 1: Concrete methods with default no-ops
```python
async def initialize(self) -> None:
    """Initialize storage backend. Override if needed."""
    pass
```

**Rejected because:**
- Weakens adapter pattern (implicit vs explicit contract)
- Easy to forget to implement
- Type checkers won't catch missing implementations
- Against "explicit is better than implicit" principle

### Alternative 2: Context manager protocol
```python
async def __aenter__(self):
    await self.initialize()
    return self

async def __aexit__(self, *args):
    await self.close()
```

**Rejected because:**
- Breaking change (requires refactoring existing usage)
- Out of scope for this task
- Can be added later if desired (not mutually exclusive)

## References

- **Adapter Pattern:** CLAUDE.md - "All storage backends implement BaseVectorStore"
- **Existing Implementation:** `vibe_rag/storage/postgres_vector.py:62-72` (initialize), `241-248` (close)
- **Existing Tests:** `tests/unit/storage/test_postgres_vector_store.py:26-40` (initialize), `303-318` (close)
