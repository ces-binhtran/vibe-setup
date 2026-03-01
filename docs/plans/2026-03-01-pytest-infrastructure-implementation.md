# Pytest Test Infrastructure Configuration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Configure comprehensive pytest infrastructure with async support, coverage reporting, and reusable test utilities for vibe-rag framework

**Architecture:** Three-component system: enhanced pytest config in pyproject.toml, mock implementations for fast unit testing, and pytest fixtures for common test scenarios

**Tech Stack:** pytest, pytest-asyncio, pytest-cov, Python 3.10+ type hints

---

## Task 1: Enhance Pytest Configuration

**Files:**
- Modify: `pyproject.toml` (lines 42-46, expand pytest.ini_options section)

**Step 1: Read current pytest configuration**

Run: `cat pyproject.toml | grep -A 10 "pytest.ini_options"`
Expected: See current minimal configuration

**Step 2: Update pytest configuration with coverage and markers**

Edit `pyproject.toml` to replace the `[tool.pytest.ini_options]` section:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
asyncio_mode = "auto"
addopts = [
    "-v",                           # Verbose output
    "--strict-markers",             # Enforce marker registration
    "--cov=vibe_rag",              # Coverage for vibe_rag package
    "--cov-report=term-missing",   # Show missing lines in terminal
    "--cov-report=html",           # Generate HTML coverage report
    "--tb=short",                  # Shorter traceback format
]
markers = [
    "unit: Unit tests (fast, isolated)",
    "integration: Integration tests (slower, real dependencies)",
    "e2e: End-to-end tests (slowest, full workflows)",
]
```

**Step 3: Verify configuration syntax is valid**

Run: `python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"`
Expected: No syntax errors

**Step 4: Test pytest loads configuration**

Run: `pytest --markers`
Expected: See custom markers (unit, integration, e2e) listed with descriptions

**Step 5: Commit configuration changes**

```bash
git add pyproject.toml
git commit -m "config: enhance pytest configuration with coverage and markers

Why this change was needed:
- Basic pytest config lacked coverage reporting
- No test organization markers defined
- Need strict marker enforcement to catch typos
- Production testing requires verbose output and HTML reports

What changed:
- Added coverage reporting (terminal + HTML)
- Registered test markers (unit, integration, e2e)
- Enabled strict markers mode
- Set verbose output and short tracebacks

Technical notes:
- asyncio_mode=auto already set for async test support
- HTML reports generated in htmlcov/ directory
- --cov=vibe_rag focuses coverage on framework code only
- Markers enable selective test runs (pytest -m unit)"
```

---

## Task 2: Create Mock LLM Provider

**Files:**
- Create: `vibe_rag/testing/mocks.py`
- Reference: Design document shows BaseLLMProvider interface (will be created in future tasks)

**Step 1: Create placeholder for BaseLLMProvider interface**

Since `BaseLLMProvider` doesn't exist yet (will be created in future tasks), we'll create a mock that follows the expected interface based on the design document.

Create `vibe_rag/testing/mocks.py`:

```python
"""Mock implementations for testing vibe-rag components."""

from typing import Optional


class MockLLMProvider:
    """Mock LLM provider for testing.

    Provides deterministic responses for unit testing without external API calls.
    Implements the expected BaseLLMProvider interface.

    Design decisions:
    - Returns predictable responses based on prompt content
    - No network calls or API dependencies
    - Async methods for compatibility with real providers
    - Deterministic embeddings for reproducible tests
    """

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "mock"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate predictable mock response.

        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            temperature: Sampling temperature (ignored in mock)
            max_tokens: Maximum tokens (ignored in mock)
            **kwargs: Additional parameters (ignored in mock)

        Returns:
            Deterministic response based on prompt
        """
        if system_prompt:
            return f"Mock response to system '{system_prompt}' and prompt '{prompt}'"
        return f"Mock response to: {prompt}"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate deterministic mock embeddings.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors (768-dimensional)

        Note:
            Returns same embedding for same text (deterministic)
            Embedding dimension matches common models (768)
        """
        # Return deterministic embeddings based on text hash
        embeddings = []
        for text in texts:
            # Simple deterministic embedding: use text hash to generate values
            hash_val = hash(text) % 1000 / 1000.0
            embedding = [hash_val + i * 0.01 for i in range(768)]
            embeddings.append(embedding)
        return embeddings
```

**Step 2: Verify the mock can be imported**

Run: `python -c "from vibe_rag.testing.mocks import MockLLMProvider; print('MockLLMProvider imported successfully')"`
Expected: "MockLLMProvider imported successfully"

**Step 3: Test mock provider methods work**

Run: `python -c "import asyncio; from vibe_rag.testing.mocks import MockLLMProvider; provider = MockLLMProvider(); print(asyncio.run(provider.generate('test')))"`
Expected: "Mock response to: test"

**Step 4: Commit mock LLM provider**

```bash
git add vibe_rag/testing/mocks.py
git commit -m "feat: add MockLLMProvider for unit testing

Why this change was needed:
- Unit tests need fast LLM provider without API calls
- Deterministic responses required for reproducible tests
- Real providers have network latency and costs
- TDD workflow needs instant feedback

What changed:
- Created MockLLMProvider implementing expected interface
- Added generate() method with predictable responses
- Added embed() method with deterministic embeddings
- All methods are async for compatibility

Technical notes:
- Embeddings use text hash for determinism (same text = same embedding)
- 768-dimensional embeddings match common models
- Ignores temperature/max_tokens (deterministic by design)
- Will integrate with BaseLLMProvider when created"
```

---

## Task 3: Create Mock Vector Store

**Files:**
- Modify: `vibe_rag/testing/mocks.py` (add MockVectorStore class)
- Reference: Design document shows BaseVectorStore interface (will be created in future tasks)

**Step 1: Add MockVectorStore to mocks.py**

Add to `vibe_rag/testing/mocks.py`:

```python
from vibe_rag.models import Document


class MockVectorStore:
    """Mock vector store for testing.

    In-memory storage for fast, isolated unit testing without database dependencies.
    Implements the expected BaseVectorStore interface.

    Design decisions:
    - Uses dict for in-memory storage (fast, isolated)
    - Simple cosine similarity for search (deterministic)
    - Supports all base operations (add, search, delete)
    - No external dependencies or setup required
    """

    def __init__(self):
        """Initialize in-memory storage."""
        self.documents: dict[str, list[tuple[Document, list[float]]]] = {}

    @property
    def store_name(self) -> str:
        """Return storage backend identifier."""
        return "mock"

    async def add_documents(
        self,
        documents: list[Document],
        collection_name: str,
        embeddings: list[list[float]]
    ) -> list[str]:
        """Add documents with embeddings to collection.

        Args:
            documents: List of documents to add
            collection_name: Name of the collection
            embeddings: List of embedding vectors (one per document)

        Returns:
            List of document IDs

        Raises:
            ValueError: If documents and embeddings counts don't match
        """
        if len(documents) != len(embeddings):
            raise ValueError(
                f"Document count ({len(documents)}) must match "
                f"embedding count ({len(embeddings)})"
            )

        # Initialize collection if needed
        if collection_name not in self.documents:
            self.documents[collection_name] = []

        # Store documents with their embeddings
        doc_ids = []
        for doc, embedding in zip(documents, embeddings):
            self.documents[collection_name].append((doc, embedding))
            doc_ids.append(doc.id)

        return doc_ids

    async def similarity_search(
        self,
        query_embedding: list[float],
        collection_name: str,
        top_k: int = 5,
        filters: Optional[dict] = None
    ) -> list[Document]:
        """Search for similar documents using cosine similarity.

        Args:
            query_embedding: Query embedding vector
            collection_name: Name of the collection to search
            top_k: Number of top results to return
            filters: Optional metadata filters

        Returns:
            List of similar documents with scores

        Note:
            Simple cosine similarity implementation for testing
            Filters match exact metadata key-value pairs
        """
        if collection_name not in self.documents:
            return []

        # Calculate similarities
        results = []
        for doc, embedding in self.documents[collection_name]:
            # Apply metadata filters if provided
            if filters:
                if not all(
                    doc.metadata.get(key) == value
                    for key, value in filters.items()
                ):
                    continue

            # Simple cosine similarity
            similarity = self._cosine_similarity(query_embedding, embedding)
            doc_with_score = Document(
                id=doc.id,
                content=doc.content,
                metadata=doc.metadata,
                score=similarity
            )
            results.append(doc_with_score)

        # Sort by similarity score (descending) and return top_k
        results.sort(key=lambda d: d.score or 0.0, reverse=True)
        return results[:top_k]

    async def delete_collection(self, collection_name: str):
        """Delete an entire collection.

        Args:
            collection_name: Name of the collection to delete
        """
        if collection_name in self.documents:
            del self.documents[collection_name]

    @staticmethod
    def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0.0 to 1.0)
        """
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)
```

**Step 2: Verify mock vector store can be imported**

Run: `python -c "from vibe_rag.testing.mocks import MockVectorStore; print('MockVectorStore imported successfully')"`
Expected: "MockVectorStore imported successfully"

**Step 3: Test mock vector store basic operations**

Run:
```bash
python -c "
import asyncio
from vibe_rag.testing.mocks import MockVectorStore
from vibe_rag.models import Document

async def test():
    store = MockVectorStore()
    docs = [Document(content='test')]
    embeddings = [[0.1] * 768]
    ids = await store.add_documents(docs, 'test_coll', embeddings)
    print(f'Added {len(ids)} documents')

asyncio.run(test())
"
```
Expected: "Added 1 documents"

**Step 4: Commit mock vector store**

```bash
git add vibe_rag/testing/mocks.py
git commit -m "feat: add MockVectorStore for unit testing

Why this change was needed:
- Unit tests need fast storage without database setup
- In-memory storage provides instant feedback for TDD
- Real databases have setup overhead and state management
- Deterministic search results required for reproducible tests

What changed:
- Created MockVectorStore with in-memory dict storage
- Implemented add_documents, similarity_search, delete_collection
- Added cosine similarity calculation for search
- Support metadata filtering in search

Technical notes:
- Uses dict[collection_name -> list[(doc, embedding)]] structure
- Cosine similarity ensures deterministic search results
- Validates document/embedding count matches
- Will integrate with BaseVectorStore when created"
```

---

## Task 4: Create Pytest Fixtures

**Files:**
- Create: `vibe_rag/testing/fixtures.py`

**Step 1: Create fixtures file with common test data**

Create `vibe_rag/testing/fixtures.py`:

```python
"""Pytest fixtures for vibe-rag testing."""

import pytest

from vibe_rag.models import Document
from vibe_rag.testing.mocks import MockLLMProvider, MockVectorStore


@pytest.fixture
def sample_documents() -> list[Document]:
    """Sample documents for testing.

    Returns:
        List of 3 documents with varied content and metadata

    Design notes:
        - Covers different document types (guide, tutorial, handbook)
        - Includes metadata for testing filtering
        - Content varies for similarity testing
    """
    return [
        Document(
            content="Python programming guide for beginners",
            metadata={"type": "guide", "topic": "python", "level": "beginner"}
        ),
        Document(
            content="Machine learning tutorial with practical examples",
            metadata={"type": "tutorial", "topic": "ml", "level": "intermediate"}
        ),
        Document(
            content="Data science handbook covering statistics and visualization",
            metadata={"type": "handbook", "topic": "data-science", "level": "advanced"}
        ),
    ]


@pytest.fixture
def sample_embeddings() -> list[list[float]]:
    """Sample embedding vectors for testing.

    Returns:
        List of 3 embedding vectors (768-dimensional)

    Design notes:
        - 768 dimensions match common embedding models
        - Different patterns for similarity testing
        - Deterministic values for reproducible tests
    """
    return [
        [0.1 + i * 0.001 for i in range(768)],  # Pattern 1
        [0.5 + i * 0.001 for i in range(768)],  # Pattern 2
        [0.9 + i * 0.001 for i in range(768)],  # Pattern 3
    ]


@pytest.fixture
def mock_llm_provider() -> MockLLMProvider:
    """Pre-configured mock LLM provider.

    Returns:
        MockLLMProvider instance ready for testing

    Design notes:
        - Instantiated and ready to use
        - No configuration needed
        - Provides deterministic responses
    """
    return MockLLMProvider()


@pytest.fixture
def mock_vector_store() -> MockVectorStore:
    """Pre-configured mock vector store.

    Returns:
        MockVectorStore instance ready for testing

    Design notes:
        - Empty in-memory storage
        - Fresh instance per test (isolation)
        - No cleanup needed (garbage collected)
    """
    return MockVectorStore()


@pytest.fixture
async def populated_mock_store(
    sample_documents: list[Document],
    sample_embeddings: list[list[float]]
) -> MockVectorStore:
    """Mock vector store pre-populated with sample documents.

    Args:
        sample_documents: Fixture providing sample documents
        sample_embeddings: Fixture providing sample embeddings

    Returns:
        MockVectorStore with documents already added

    Design notes:
        - Ready for immediate search testing
        - Uses 'test_collection' as collection name
        - Combines sample_documents and sample_embeddings fixtures
    """
    store = MockVectorStore()
    await store.add_documents(
        sample_documents,
        "test_collection",
        sample_embeddings
    )
    return store
```

**Step 2: Verify fixtures can be imported**

Run: `python -c "from vibe_rag.testing.fixtures import sample_documents; print('Fixtures imported successfully')"`
Expected: "Fixtures imported successfully"

**Step 3: Test a fixture works in pytest**

Create temporary test file:
```bash
cat > /tmp/test_fixture_verify.py << 'EOF'
import pytest
from vibe_rag.testing.fixtures import sample_documents

def test_sample_documents_fixture(sample_documents):
    assert len(sample_documents) == 3
    assert sample_documents[0].metadata["type"] == "guide"
EOF
```

Run: `pytest /tmp/test_fixture_verify.py -v`
Expected: PASS

**Step 4: Clean up temporary test**

Run: `rm /tmp/test_fixture_verify.py`

**Step 5: Commit pytest fixtures**

```bash
git add vibe_rag/testing/fixtures.py
git commit -m "feat: add pytest fixtures for common test scenarios

Why this change was needed:
- Reduce test boilerplate across test files
- Provide consistent test data for reproducible tests
- Pre-configured mocks save setup time in each test
- Populated store fixture enables immediate search testing

What changed:
- Created sample_documents fixture (3 varied documents)
- Created sample_embeddings fixture (768-dim vectors)
- Created mock_llm_provider fixture (ready-to-use mock)
- Created mock_vector_store fixture (empty store)
- Created populated_mock_store fixture (pre-loaded store)

Technical notes:
- Fixtures use pytest's dependency injection
- populated_mock_store composes other fixtures
- All fixtures provide fresh instances (test isolation)
- Async fixture for populated store (async operations)"
```

---

## Task 5: Export Test Utilities

**Files:**
- Modify: `vibe_rag/testing/__init__.py`

**Step 1: Read current testing package init**

Run: `cat vibe_rag/testing/__init__.py`
Expected: Empty file or minimal content

**Step 2: Update testing package to export utilities**

Edit `vibe_rag/testing/__init__.py`:

```python
"""Testing utilities for vibe-rag.

Provides mock implementations and pytest fixtures for testing vibe-rag components.

Mock Implementations:
    - MockLLMProvider: Fast, deterministic LLM provider for unit tests
    - MockVectorStore: In-memory vector store for isolated testing

Pytest Fixtures:
    - sample_documents: List of varied test documents
    - sample_embeddings: 768-dimensional embedding vectors
    - mock_llm_provider: Pre-configured MockLLMProvider
    - mock_vector_store: Empty MockVectorStore
    - populated_mock_store: MockVectorStore with sample data

Example:
    ```python
    from vibe_rag.testing import MockLLMProvider, sample_documents

    def test_my_feature(sample_documents, mock_llm_provider):
        # Use fixtures in your tests
        result = await mock_llm_provider.generate("test prompt")
        assert "Mock response" in result
    ```
"""

from vibe_rag.testing.mocks import MockLLMProvider, MockVectorStore
from vibe_rag.testing.fixtures import (
    sample_documents,
    sample_embeddings,
    mock_llm_provider,
    mock_vector_store,
    populated_mock_store,
)

__all__ = [
    # Mock implementations
    "MockLLMProvider",
    "MockVectorStore",
    # Fixtures
    "sample_documents",
    "sample_embeddings",
    "mock_llm_provider",
    "mock_vector_store",
    "populated_mock_store",
]
```

**Step 3: Verify utilities can be imported from testing package**

Run: `python -c "from vibe_rag.testing import MockLLMProvider, MockVectorStore, sample_documents; print('All utilities exported successfully')"`
Expected: "All utilities exported successfully"

**Step 4: Commit testing package exports**

```bash
git add vibe_rag/testing/__init__.py
git commit -m "feat: export test utilities from vibe_rag.testing

Why this change was needed:
- Centralized imports simplify test file imports
- Clear documentation of available testing utilities
- Single import location (vibe_rag.testing) is more discoverable
- Matches batteries-included philosophy

What changed:
- Exported MockLLMProvider and MockVectorStore
- Exported all pytest fixtures
- Added comprehensive module docstring with examples
- Defined __all__ for explicit public API

Technical notes:
- Import from vibe_rag.testing instead of submodules
- Fixtures auto-discovered by pytest (no explicit import needed in tests)
- Mocks must be explicitly imported for use
- Documentation includes usage example"
```

---

## Task 6: Verify Pytest Infrastructure

**Files:**
- No files modified (verification only)

**Step 1: Run existing tests with new configuration**

Run: `pytest tests/unit/test_models.py -v`
Expected: All 6 tests PASS with verbose output

**Step 2: Verify coverage reporting works**

Run: `pytest tests/unit/test_models.py --cov=vibe_rag --cov-report=term-missing`
Expected: Coverage report showing vibe_rag/models.py with percentage and missing lines

**Step 3: Check HTML coverage report generated**

Run: `pytest tests/unit/test_models.py --cov=vibe_rag --cov-report=html && ls htmlcov/index.html`
Expected: `htmlcov/index.html` file exists

**Step 4: Verify markers are registered**

Run: `pytest --markers | grep -E "(unit|integration|e2e)"`
Expected: See three markers listed with descriptions

**Step 5: Verify test utilities are importable**

Run: `python -c "from vibe_rag.testing import MockLLMProvider, MockVectorStore; print('Import successful')"`
Expected: "Import successful"

**Step 6: Run all tests with full configuration**

Run: `pytest`
Expected: All tests PASS with coverage report

**Step 7: Verify htmlcov directory in gitignore**

Run: `grep htmlcov .gitignore`
Expected: `htmlcov/` or `htmlcov` found in .gitignore

**Step 8: Add htmlcov to gitignore if missing**

If not found in step 7:
```bash
echo "htmlcov/" >> .gitignore
git add .gitignore
git commit -m "chore: add htmlcov to gitignore

Why this change was needed:
- HTML coverage reports should not be committed
- Generated files clutter git history
- Each developer generates their own reports

What changed:
- Added htmlcov/ to .gitignore

Technical notes:
- Coverage reports are local artifacts
- Regenerated on each pytest --cov run"
```

If found in step 7:
Run: `echo "htmlcov already in .gitignore, skipping"`

---

## Task 7: Create Example Test Using Utilities

**Files:**
- Create: `tests/unit/test_testing_utilities.py`

**Step 1: Create test file demonstrating utilities usage**

Create `tests/unit/test_testing_utilities.py`:

```python
"""Tests demonstrating test utilities usage.

This file serves as both verification and documentation of test utilities.
"""

import pytest

from vibe_rag.models import Document
from vibe_rag.testing import (
    MockLLMProvider,
    MockVectorStore,
    sample_documents,
    sample_embeddings,
)


@pytest.mark.unit
def test_sample_documents_fixture(sample_documents):
    """Verify sample_documents fixture provides expected data."""
    assert len(sample_documents) == 3
    assert all(isinstance(doc, Document) for doc in sample_documents)
    assert sample_documents[0].metadata["type"] == "guide"
    assert sample_documents[1].metadata["type"] == "tutorial"
    assert sample_documents[2].metadata["type"] == "handbook"


@pytest.mark.unit
def test_sample_embeddings_fixture(sample_embeddings):
    """Verify sample_embeddings fixture provides expected data."""
    assert len(sample_embeddings) == 3
    assert all(len(emb) == 768 for emb in sample_embeddings)
    # Verify different patterns
    assert sample_embeddings[0][0] < sample_embeddings[1][0]
    assert sample_embeddings[1][0] < sample_embeddings[2][0]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_llm_provider_generate():
    """Verify MockLLMProvider.generate() returns predictable responses."""
    provider = MockLLMProvider()

    # Test basic generation
    response = await provider.generate("What is Python?")
    assert "Mock response to: What is Python?" == response

    # Test with system prompt
    response_with_system = await provider.generate(
        "What is Python?",
        system_prompt="You are a helpful assistant"
    )
    assert "system" in response_with_system.lower()
    assert "What is Python?" in response_with_system


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_llm_provider_embed():
    """Verify MockLLMProvider.embed() returns deterministic embeddings."""
    provider = MockLLMProvider()

    texts = ["Python programming", "Machine learning"]
    embeddings = await provider.embed(texts)

    # Verify structure
    assert len(embeddings) == 2
    assert all(len(emb) == 768 for emb in embeddings)

    # Verify determinism (same text = same embedding)
    embeddings2 = await provider.embed(texts)
    assert embeddings == embeddings2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_vector_store_add_and_search(sample_documents, sample_embeddings):
    """Verify MockVectorStore add and search operations."""
    store = MockVectorStore()

    # Add documents
    doc_ids = await store.add_documents(
        sample_documents,
        "test_collection",
        sample_embeddings
    )

    assert len(doc_ids) == 3
    assert all(isinstance(doc_id, str) for doc_id in doc_ids)

    # Search
    results = await store.similarity_search(
        query_embedding=sample_embeddings[0],  # Search with first embedding
        collection_name="test_collection",
        top_k=2
    )

    assert len(results) == 2
    assert all(isinstance(doc, Document) for doc in results)
    assert all(doc.score is not None for doc in results)
    # First result should be most similar
    assert results[0].score >= results[1].score


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_vector_store_metadata_filtering(sample_documents, sample_embeddings):
    """Verify MockVectorStore metadata filtering."""
    store = MockVectorStore()

    await store.add_documents(
        sample_documents,
        "test_collection",
        sample_embeddings
    )

    # Filter by metadata
    results = await store.similarity_search(
        query_embedding=sample_embeddings[0],
        collection_name="test_collection",
        top_k=10,
        filters={"type": "guide"}
    )

    assert len(results) == 1
    assert results[0].metadata["type"] == "guide"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mock_vector_store_delete_collection(sample_documents, sample_embeddings):
    """Verify MockVectorStore delete operation."""
    store = MockVectorStore()

    # Add documents
    await store.add_documents(
        sample_documents,
        "test_collection",
        sample_embeddings
    )

    # Delete collection
    await store.delete_collection("test_collection")

    # Verify collection is gone
    results = await store.similarity_search(
        query_embedding=sample_embeddings[0],
        collection_name="test_collection",
        top_k=10
    )

    assert len(results) == 0
```

**Step 2: Run the new tests**

Run: `pytest tests/unit/test_testing_utilities.py -v`
Expected: All tests PASS (8 tests)

**Step 3: Run tests filtered by marker**

Run: `pytest -m unit -v`
Expected: All unit tests PASS (including new utilities tests)

**Step 4: Verify coverage includes testing utilities**

Run: `pytest tests/unit/test_testing_utilities.py --cov=vibe_rag --cov-report=term-missing`
Expected: Coverage report shows vibe_rag/testing/mocks.py and fixtures.py covered

**Step 5: Commit example tests**

```bash
git add tests/unit/test_testing_utilities.py
git commit -m "test: add verification tests for testing utilities

Why this change was needed:
- Verify test utilities work correctly
- Provide usage examples for developers
- Document expected behavior of mocks and fixtures
- Ensure test infrastructure is production-ready

What changed:
- Created test_testing_utilities.py with 8 tests
- Tested sample_documents and sample_embeddings fixtures
- Tested MockLLMProvider generate and embed methods
- Tested MockVectorStore add, search, filter, delete operations
- Marked all tests with @pytest.mark.unit

Technical notes:
- Tests serve as both verification and documentation
- Async tests use @pytest.mark.asyncio decorator
- Metadata filtering test ensures filters work correctly
- Determinism tests ensure reproducible behavior"
```

---

## Task 8: Update .gitignore for Coverage Artifacts

**Files:**
- Modify: `.gitignore`

**Step 1: Check if coverage artifacts already ignored**

Run: `grep -E "(\.coverage|htmlcov)" .gitignore`
Expected: May or may not find entries

**Step 2: Add coverage artifacts to .gitignore if missing**

If not found in step 1, append to `.gitignore`:

```
# Coverage reports
.coverage
htmlcov/
.pytest_cache/
```

**Step 3: Verify .gitignore syntax**

Run: `git check-ignore htmlcov/index.html`
Expected: `htmlcov/index.html` (confirming it's ignored)

**Step 4: Commit .gitignore update (if changed)**

If changes were made:
```bash
git add .gitignore
git commit -m "chore: add coverage artifacts to .gitignore

Why this change was needed:
- Coverage reports should not be committed to git
- Generated files clutter repository and git history
- Each developer generates their own local coverage reports

What changed:
- Added .coverage to .gitignore (coverage data file)
- Added htmlcov/ to .gitignore (HTML coverage reports)
- Added .pytest_cache/ to .gitignore (pytest cache)

Technical notes:
- Coverage artifacts regenerated on each pytest run
- Local-only files not needed in version control"
```

If no changes needed:
Run: `echo "Coverage artifacts already in .gitignore"`

---

## Task 9: Final Verification and Documentation

**Files:**
- Create: `tests/README.md`

**Step 1: Run comprehensive verification**

Run all verification commands:
```bash
# Test execution
pytest tests/unit/test_models.py -v

# Coverage reporting
pytest --cov=vibe_rag --cov-report=term-missing

# Marker verification
pytest --markers | grep -E "(unit|integration|e2e)"

# Utilities import
python -c "from vibe_rag.testing import MockLLMProvider, MockVectorStore; print('✓ Utilities importable')"

# HTML coverage
pytest --cov=vibe_rag --cov-report=html && ls htmlcov/index.html && echo "✓ HTML coverage generated"

# Marker filtering
pytest -m unit -v

# Full test suite
pytest
```

Expected: All commands succeed

**Step 2: Create test directory documentation**

Create `tests/README.md`:

```markdown
# vibe-rag Tests

This directory contains the test suite for the vibe-rag framework.

## Test Organization

Tests are organized by scope and speed:

- **`tests/unit/`** - Fast, isolated unit tests (no external dependencies)
- **`tests/integration/`** - Integration tests (real database, APIs)
- **`tests/e2e/`** - End-to-end workflow tests (slowest)

## Running Tests

### All tests
```bash
pytest
```

### Specific test category
```bash
pytest -m unit              # Fast unit tests only
pytest -m integration       # Integration tests only
pytest -m e2e              # End-to-end tests only
```

### With coverage
```bash
pytest --cov=vibe_rag --cov-report=term-missing
pytest --cov=vibe_rag --cov-report=html  # HTML report in htmlcov/
```

### Specific test file
```bash
pytest tests/unit/test_models.py -v
```

## Test Utilities

The `vibe_rag.testing` package provides utilities for writing tests:

### Mock Implementations

```python
from vibe_rag.testing import MockLLMProvider, MockVectorStore

# Use in tests for fast, deterministic behavior
provider = MockLLMProvider()
store = MockVectorStore()
```

### Pytest Fixtures

```python
def test_my_feature(sample_documents, mock_llm_provider):
    """Fixtures auto-injected by pytest."""
    # Use sample_documents and mock_llm_provider
    pass
```

Available fixtures:
- `sample_documents` - List of 3 varied test documents
- `sample_embeddings` - 768-dimensional embedding vectors
- `mock_llm_provider` - Pre-configured MockLLMProvider
- `mock_vector_store` - Empty MockVectorStore
- `populated_mock_store` - MockVectorStore with sample data

## Writing Tests

Follow TDD workflow:

1. **Write failing test first**
   ```python
   def test_new_feature():
       result = new_feature(input)
       assert result == expected
   ```

2. **Run test to verify it fails**
   ```bash
   pytest tests/unit/test_module.py::test_new_feature -v
   ```

3. **Implement minimal code to pass**

4. **Run test to verify it passes**

5. **Commit**

### Test Markers

Mark tests by category:

```python
import pytest

@pytest.mark.unit
def test_fast_unit():
    pass

@pytest.mark.integration
async def test_with_database():
    pass

@pytest.mark.e2e
async def test_full_workflow():
    pass
```

### Async Tests

Use `@pytest.mark.asyncio` for async tests:

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

## Coverage Goals

Target coverage by component:
- Core engine: 90%+
- Providers: 85%+
- Storage: 85%+
- Pipeline: 80%+
- Utilities: 75%+

View coverage:
```bash
pytest --cov=vibe_rag --cov-report=html
open htmlcov/index.html
```

## CI/CD Integration

Tests run automatically on:
- Pull requests
- Pushes to main/phase-* branches

CI configuration: (TBD - will be added when CI is set up)
```

**Step 3: Verify README syntax**

Run: `cat tests/README.md | head -20`
Expected: Markdown content displayed correctly

**Step 4: Commit test documentation**

```bash
git add tests/README.md
git commit -m "docs: add comprehensive test documentation

Why this change was needed:
- Developers need clear guidance on running tests
- Test utilities usage should be documented
- TDD workflow should be explicit
- Coverage goals provide quality targets

What changed:
- Created tests/README.md with organization overview
- Documented how to run different test categories
- Explained test utilities (mocks and fixtures)
- Provided TDD workflow steps
- Listed coverage goals by component

Technical notes:
- Examples show actual usage patterns
- Markers enable selective test execution
- Async test patterns documented
- CI integration placeholder for future setup"
```

---

## Summary

**What we built:**
1. Enhanced pytest configuration with coverage, markers, and strict settings
2. MockLLMProvider for fast, deterministic LLM testing
3. MockVectorStore for in-memory vector storage testing
4. Pytest fixtures for common test data and scenarios
5. Comprehensive test utilities package
6. Verification tests demonstrating utilities usage
7. Documentation for test organization and usage

**Verification checklist:**
- [x] Pytest runs successfully
- [x] Coverage reporting works (terminal + HTML)
- [x] Test markers registered and functional
- [x] Mock implementations work correctly
- [x] Fixtures provide expected data
- [x] Utilities importable from vibe_rag.testing
- [x] Example tests pass
- [x] Documentation complete

**Next steps:**
- Use test utilities in future component development
- Maintain coverage goals as codebase grows
- Add integration tests when real providers/storage are implemented
- Set up CI/CD to run tests automatically
