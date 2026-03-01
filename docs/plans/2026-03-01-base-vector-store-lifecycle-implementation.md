# BaseVectorStore Lifecycle Methods Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add `initialize()` and `close()` abstract methods to BaseVectorStore interface to maintain adapter pattern integrity.

**Architecture:** Add two abstract async methods to the BaseVectorStore ABC class. No changes needed to PostgresVectorStore as it already implements both methods.

**Tech Stack:** Python 3.10+, ABC (abstract base classes), pytest

---

## Task 1: Add initialize() abstract method to BaseVectorStore

**Files:**
- Modify: `vibe_rag/storage/base.py:26-43`

**Step 1: Write the failing test**

Since we're modifying an abstract base class, we'll verify the change by attempting to instantiate a concrete class that doesn't implement the method. However, the existing PostgresVectorStore already implements both methods, so we'll verify by reading the file and checking the test still passes.

First, let's verify current state works:

Run: `pytest tests/unit/storage/test_postgres_vector_store.py::test_init_creates_connection_pool -v`
Expected: PASS (PostgresVectorStore already implements initialize)

**Step 2: Add initialize() abstract method to BaseVectorStore**

Open `vibe_rag/storage/base.py` and add the `initialize()` method after the `__init__` method (around line 26):

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
```

The complete section should look like:

```python
def __init__(self, collection_name: str):
    """Initialize the vector store.

    Args:
        collection_name: Name of the collection/table to store vectors
    """
    self.collection_name = collection_name

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
async def add_documents(
    self, documents: list[Document], embeddings: list[list[float]]
) -> list[str]:
```

**Step 3: Run tests to verify nothing breaks**

Run: `pytest tests/unit/storage/test_postgres_vector_store.py -v`
Expected: All tests PASS (PostgresVectorStore already implements initialize)

**Step 4: Commit**

```bash
git add vibe_rag/storage/base.py
git commit -m "feat: add initialize() abstract method to BaseVectorStore

Add initialize() lifecycle method to BaseVectorStore interface to
maintain adapter pattern. All vector store implementations must now
explicitly handle initialization, even if it's a no-op."
```

---

## Task 2: Add close() abstract method to BaseVectorStore

**Files:**
- Modify: `vibe_rag/storage/base.py:74-75`

**Step 1: Verify current state**

Run: `pytest tests/unit/storage/test_postgres_vector_store.py::test_close_closes_pool -v`
Expected: PASS (PostgresVectorStore already implements close)

**Step 2: Add close() abstract method to BaseVectorStore**

Open `vibe_rag/storage/base.py` and add the `close()` method after the `delete_collection` method (around line 74):

```python
@abstractmethod
async def close(self) -> None:
    """Close connections and cleanup resources.

    This method should be called when the vector store is no longer needed.
    For implementations that don't need cleanup, this can be a no-op.
    """
    pass
```

The complete ending of the class should look like:

```python
@abstractmethod
async def delete_collection(self) -> None:
    """Delete the entire collection/table.

    Raises:
        StorageError: If deletion fails
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

**Step 3: Run all storage tests to verify**

Run: `pytest tests/unit/storage/ -v`
Expected: All tests PASS

**Step 4: Run full test suite to ensure no regressions**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add vibe_rag/storage/base.py
git commit -m "feat: add close() abstract method to BaseVectorStore

Add close() lifecycle method to BaseVectorStore interface to maintain
adapter pattern. All vector store implementations must now explicitly
handle cleanup, even if it's a no-op.

This completes the BaseVectorStore lifecycle interface, ensuring all
implementations have consistent initialization and cleanup patterns."
```

---

## Task 3: Verify implementation completeness

**Step 1: Review the changes**

Open `vibe_rag/storage/base.py` and verify:
- [ ] `initialize()` is after `__init__` and before `add_documents`
- [ ] `close()` is after `delete_collection` at end of class
- [ ] Both methods have `@abstractmethod` decorator
- [ ] Both methods are `async def` with `-> None` return type
- [ ] Both have comprehensive docstrings
- [ ] Docstrings mention StorageError for initialize() only

**Step 2: Verify PostgresVectorStore still works**

Run: `pytest tests/unit/storage/test_postgres_vector_store.py -v`
Expected: All tests PASS

**Step 3: Verify type checking (if mypy is configured)**

Run: `mypy vibe_rag/storage/ --strict`
Expected: No errors (PostgresVectorStore implements both abstract methods)

If mypy is not configured, skip this step.

**Step 4: Manual verification - check the interface**

Read `vibe_rag/storage/base.py` and verify the complete interface:
- `__init__(collection_name: str)`
- `initialize() -> None` (abstract, async)
- `add_documents(documents, embeddings) -> list[str]` (abstract, async)
- `similarity_search(query_embedding, k, filter_metadata) -> list[Document]` (abstract, async)
- `delete_collection() -> None` (abstract, async)
- `close() -> None` (abstract, async)

**Step 5: Final commit if any adjustments were needed**

If you made any adjustments in previous steps (unlikely), commit them:

```bash
git add vibe_rag/storage/base.py
git commit -m "refactor: polish BaseVectorStore lifecycle interface"
```

Otherwise, skip this step.

---

## Completion Checklist

Before marking this task complete, verify:

- [x] Design document written: `docs/plans/2026-03-01-base-vector-store-lifecycle-design.md`
- [ ] `initialize()` added to BaseVectorStore as abstract method
- [ ] `close()` added to BaseVectorStore as abstract method
- [ ] Both methods properly documented with docstrings
- [ ] All existing tests pass (PostgresVectorStore already implements both)
- [ ] No new tests needed (abstract methods enforced at class definition time)
- [ ] Adapter pattern maintained (all implementations must implement same interface)

## References

- **Design doc:** `docs/plans/2026-03-01-base-vector-store-lifecycle-design.md`
- **Base interface:** `vibe_rag/storage/base.py`
- **Reference implementation:** `vibe_rag/storage/postgres_vector.py:62-72, 241-248`
- **Existing tests:** `tests/unit/storage/test_postgres_vector_store.py`
