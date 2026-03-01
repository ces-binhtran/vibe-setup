# Async Context Manager Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add async context manager protocol to BaseVectorStore for automatic resource cleanup

**Architecture:** Add `__aenter__` and `__aexit__` concrete methods to BaseVectorStore that call existing `initialize()` and `close()` abstract methods. All subclasses (PostgresVectorStore, future implementations) inherit the behavior automatically.

**Tech Stack:** Python 3.10+, pytest, asyncio

---

## Task 1: Add Context Manager Protocol to BaseVectorStore

**Files:**
- Modify: `vibe_rag/storage/base.py:88-95`
- Create: `tests/unit/storage/test_base_vector_store.py`

**Step 1: Write failing test for __aenter__ calling initialize**

Create `tests/unit/storage/test_base_vector_store.py`:

```python
"""Unit tests for BaseVectorStore context manager protocol."""

from unittest.mock import AsyncMock

import pytest

from vibe_rag.models import Document
from vibe_rag.storage.base import BaseVectorStore


class MockVectorStore(BaseVectorStore):
    """Concrete implementation for testing BaseVectorStore."""

    def __init__(self, collection_name: str):
        super().__init__(collection_name)
        self.initialize_called = False
        self.close_called = False

    async def initialize(self) -> None:
        self.initialize_called = True

    async def add_documents(
        self, documents: list[Document], embeddings: list[list[float]]
    ) -> list[str]:
        return [doc.id for doc in documents]

    async def similarity_search(
        self,
        query_embedding: list[float],
        k: int = 5,
        filter_metadata: dict | None = None,
    ) -> list[Document]:
        return []

    async def delete_collection(self) -> None:
        pass

    async def close(self) -> None:
        self.close_called = True


@pytest.mark.asyncio
async def test_context_manager_calls_initialize_on_enter():
    """__aenter__ calls initialize() and returns self."""
    store = MockVectorStore("test")

    result = await store.__aenter__()

    assert store.initialize_called
    assert result is store
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/storage/test_base_vector_store.py::test_context_manager_calls_initialize_on_enter -v`

Expected: FAIL with "AttributeError: 'MockVectorStore' object has no attribute '__aenter__'"

**Step 3: Implement __aenter__ in BaseVectorStore**

Add to `vibe_rag/storage/base.py` after the `close()` abstract method (around line 95):

```python
    async def __aenter__(self):
        """Enter async context manager - initializes the store.

        Returns:
            Self for use in 'async with' statements
        """
        await self.initialize()
        return self
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/storage/test_base_vector_store.py::test_context_manager_calls_initialize_on_enter -v`

Expected: PASS

**Step 5: Commit**

```bash
git add vibe_rag/storage/base.py tests/unit/storage/test_base_vector_store.py
git commit -m "Add __aenter__ to BaseVectorStore for context manager support"
```

---

## Task 2: Add __aexit__ to BaseVectorStore

**Files:**
- Modify: `vibe_rag/storage/base.py:103-104` (after __aenter__)
- Modify: `tests/unit/storage/test_base_vector_store.py`

**Step 1: Write failing test for __aexit__ calling close**

Add to `tests/unit/storage/test_base_vector_store.py`:

```python
@pytest.mark.asyncio
async def test_context_manager_calls_close_on_exit():
    """__aexit__ calls close()."""
    store = MockVectorStore("test")
    await store.__aenter__()

    await store.__aexit__(None, None, None)

    assert store.close_called


@pytest.mark.asyncio
async def test_context_manager_returns_self():
    """Context manager returns the store instance."""
    store = MockVectorStore("test")

    result = await store.__aenter__()

    assert result is store
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/storage/test_base_vector_store.py::test_context_manager_calls_close_on_exit -v`

Expected: FAIL with "AttributeError: 'MockVectorStore' object has no attribute '__aexit__'"

**Step 3: Implement __aexit__ in BaseVectorStore**

Add to `vibe_rag/storage/base.py` after `__aenter__`:

```python
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

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/storage/test_base_vector_store.py -v`

Expected: All 2 tests PASS

**Step 5: Commit**

```bash
git add vibe_rag/storage/base.py tests/unit/storage/test_base_vector_store.py
git commit -m "Add __aexit__ to BaseVectorStore for context manager cleanup"
```

---

## Task 3: Test Exception Propagation

**Files:**
- Modify: `tests/unit/storage/test_base_vector_store.py`

**Step 1: Write failing test for exception propagation**

Add to `tests/unit/storage/test_base_vector_store.py`:

```python
@pytest.mark.asyncio
async def test_context_manager_propagates_exceptions():
    """__aexit__ returns None to propagate exceptions."""
    store = MockVectorStore("test")
    await store.__aenter__()

    result = await store.__aexit__(ValueError, ValueError("test"), None)

    assert result is None
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/unit/storage/test_base_vector_store.py::test_context_manager_propagates_exceptions -v`

Expected: PASS (implementation already returns None)

**Step 3: Write test for cleanup on exception**

Add to `tests/unit/storage/test_base_vector_store.py`:

```python
@pytest.mark.asyncio
async def test_context_manager_closes_even_on_exception():
    """Context manager calls close() even when exception occurs."""
    store = MockVectorStore("test")

    try:
        async with store:
            raise ValueError("Test exception")
    except ValueError:
        pass

    assert store.initialize_called
    assert store.close_called
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/storage/test_base_vector_store.py::test_context_manager_closes_even_on_exception -v`

Expected: PASS

**Step 5: Commit**

```bash
git add tests/unit/storage/test_base_vector_store.py
git commit -m "Add tests for context manager exception handling"
```

---

## Task 4: Integration Test with PostgresVectorStore

**Files:**
- Modify: `tests/unit/storage/test_postgres_vector_store.py`

**Step 1: Write failing integration test**

Add to `tests/unit/storage/test_postgres_vector_store.py`:

```python
@pytest.mark.asyncio
async def test_context_manager_usage():
    """PostgresVectorStore works with async context manager."""
    pool, conn = create_mock_pool()

    with patch("vibe_rag.storage.postgres_vector.asyncpg.create_pool", new_callable=AsyncMock) as mock_create_pool:
        mock_create_pool.return_value = pool

        # Test context manager usage
        async with PostgresVectorStore(
            collection_name="test_collection",
            connection_string="postgresql://localhost/test"
        ) as store:
            # Verify pool was initialized
            assert store._pool is pool

        # Verify pool was closed
        pool.close.assert_called_once()
```

**Step 2: Run test to verify it passes**

Run: `pytest tests/unit/storage/test_postgres_vector_store.py::test_context_manager_usage -v`

Expected: PASS (PostgresVectorStore inherits from BaseVectorStore)

**Step 3: Commit**

```bash
git add tests/unit/storage/test_postgres_vector_store.py
git commit -m "Add integration test for PostgresVectorStore context manager"
```

---

## Task 5: Update BaseVectorStore Documentation

**Files:**
- Modify: `vibe_rag/storage/base.py:8-17`

**Step 1: Update class docstring**

Modify `vibe_rag/storage/base.py` docstring (around line 8):

```python
class BaseVectorStore(ABC):
    """Abstract base class for vector storage implementations.

    All vector storage backends must implement this interface to ensure
    consistent behavior across different storage systems (PostgreSQL + pgvector,
    Pinecone, Weaviate, etc.).

    Supports async context manager protocol for automatic resource cleanup.

    Args:
        collection_name: Name of the collection/table to store vectors

    Example:
        >>> async with PostgresVectorStore(...) as store:
        ...     await store.add_documents(docs, embeddings)
        ...     results = await store.similarity_search(query)
        # Automatic cleanup via close()
    """
```

**Step 2: Verify documentation renders correctly**

Check that the docstring is properly formatted with:
```bash
python -c "from vibe_rag.storage.base import BaseVectorStore; help(BaseVectorStore)"
```

Expected: Docstring displays with context manager example

**Step 3: Commit**

```bash
git add vibe_rag/storage/base.py
git commit -m "Update BaseVectorStore docstring with context manager example"
```

---

## Task 6: Update PostgresVectorStore Documentation

**Files:**
- Modify: `vibe_rag/storage/postgres_vector.py:14-32`

**Step 1: Update class docstring**

Modify `vibe_rag/storage/postgres_vector.py` docstring (around line 15):

```python
class PostgresVectorStore(BaseVectorStore):
    """Vector storage implementation using PostgreSQL + pgvector.

    Uses asyncpg for async database operations and pgvector extension
    for efficient similarity search with cosine distance.

    Args:
        collection_name: Name of the table to store vectors
        connection_string: PostgreSQL connection string
        vector_dimension: Dimension of embedding vectors (default: 768)

    Example:
        >>> async with PostgresVectorStore(
        ...     collection_name="documents",
        ...     connection_string="postgresql://localhost/mydb"
        ... ) as store:
        ...     await store.add_documents(docs, embeddings)
        ...     results = await store.similarity_search(query)
    """
```

**Step 2: Verify documentation renders correctly**

Check that the docstring is properly formatted with:
```bash
python -c "from vibe_rag.storage.postgres_vector import PostgresVectorStore; help(PostgresVectorStore)"
```

Expected: Docstring displays with context manager example

**Step 3: Commit**

```bash
git add vibe_rag/storage/postgres_vector.py
git commit -m "Update PostgresVectorStore docstring with context manager example"
```

---

## Task 7: Run Full Test Suite

**Files:**
- None (verification task)

**Step 1: Run all storage tests**

Run: `pytest tests/unit/storage/ -v`

Expected: All tests PASS

**Step 2: Run full test suite**

Run: `pytest`

Expected: All tests PASS

**Step 3: Check test coverage**

Run: `pytest --cov=vibe_rag.storage --cov-report=term-missing tests/unit/storage/`

Expected:
- BaseVectorStore: 100% coverage (new methods covered)
- PostgresVectorStore: Existing coverage maintained

**Step 4: Run linters**

```bash
black vibe_rag tests
ruff check vibe_rag tests
mypy vibe_rag
```

Expected: No errors

---

## Success Criteria Verification

After completing all tasks, verify:

- [x] `BaseVectorStore` has `__aenter__` and `__aexit__` methods
- [x] Tests verify context manager protocol works correctly
- [x] Tests verify cleanup happens even on exceptions
- [x] PostgresVectorStore inherits behavior without code changes
- [x] Documentation examples use context manager pattern
- [x] All existing tests pass
- [x] Coverage requirements met (BaseVectorStore: 100%, PostgresVectorStore: maintained)
- [x] No linting errors
