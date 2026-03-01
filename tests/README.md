# vibe-rag Testing Guide

This guide explains how to write and run tests for the vibe-rag framework.

## Test Organization

Tests are organized into three levels based on scope and speed:

```
tests/
├── unit/              # Fast, isolated tests with mocked dependencies
├── integration/       # Tests with real dependencies (databases, APIs)
├── e2e/              # Full workflow tests
└── conftest.py       # Shared fixtures and configuration
```

### Test Levels

**Unit Tests** (`tests/unit/`)
- Fast (< 100ms per test)
- No external dependencies (mock APIs, databases)
- Test individual components in isolation
- Use pytest markers: `@pytest.mark.unit`

**Integration Tests** (`tests/integration/`)
- Slower (seconds per test)
- Use real dependencies (PostgreSQL, vector stores)
- Test component interactions
- Use pytest markers: `@pytest.mark.integration`

**End-to-End Tests** (`tests/e2e/`)
- Slowest (minutes per test)
- Test complete user workflows
- Use production-like configurations
- Use pytest markers: `@pytest.mark.e2e`

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Tests by Level
```bash
pytest -m unit              # Fast unit tests only
pytest -m integration       # Integration tests only
pytest -m e2e              # End-to-end tests only
```

### Run Specific Test Files
```bash
pytest tests/unit/test_models.py
pytest tests/integration/test_postgres_store.py
```

### Run with Verbose Output
```bash
pytest -v                  # Verbose mode
pytest -vv                 # Extra verbose (shows diffs)
```

### Run with Coverage
```bash
# Terminal report
pytest --cov=vibe_rag --cov-report=term-missing

# HTML report (opens in browser)
pytest --cov=vibe_rag --cov-report=html
open htmlcov/index.html
```

### Run Tests in Parallel
```bash
pytest -n auto             # Auto-detect CPU count
pytest -n 4                # Use 4 workers
```

## Testing Utilities

### Available Fixtures

All fixtures are automatically available in tests (defined in `conftest.py`).

**Document Fixtures:**
```python
def test_something(sample_documents):
    """sample_documents: List of 3 test Document objects"""
    assert len(sample_documents) == 3
```

**Embedding Fixtures:**
```python
def test_embeddings(sample_embeddings):
    """sample_embeddings: List of 3 embedding vectors (768-dim)"""
    assert len(sample_embeddings) == 3
    assert len(sample_embeddings[0]) == 768
```

**Mock Provider Fixtures:**
```python
@pytest.mark.asyncio
async def test_llm(mock_llm_provider):
    """mock_llm_provider: MockLLMProvider instance"""
    response = await mock_llm_provider.generate("What is Python?")
    assert isinstance(response, str)
```

**Mock Store Fixtures:**
```python
@pytest.mark.asyncio
async def test_store(mock_vector_store):
    """mock_vector_store: Empty MockVectorStore instance"""
    await mock_vector_store.add_documents(...)
```

```python
@pytest.mark.asyncio
async def test_search(populated_mock_store):
    """populated_mock_store: Pre-populated with sample_documents"""
    results = await populated_mock_store.similarity_search(...)
```

### Mock Implementations

**MockLLMProvider**
```python
from vibe_rag.testing import MockLLMProvider

provider = MockLLMProvider()

# Generate text (no API calls)
response = await provider.generate(
    prompt="What is RAG?",
    temperature=0.7,
    max_tokens=100
)

# Generate embeddings (deterministic)
embeddings = await provider.embed(["text1", "text2"])
```

**MockVectorStore**
```python
from vibe_rag.testing import MockVectorStore

store = MockVectorStore()

# Add documents
await store.add_documents(
    documents=[doc1, doc2],
    collection_name="test_collection",
    embeddings=[emb1, emb2]
)

# Search with cosine similarity
results = await store.similarity_search(
    query_embedding=query_emb,
    collection_name="test_collection",
    top_k=5,
    filters={"category": "python"}
)

# Delete collection
await store.delete_collection("test_collection")
```

## Writing Tests

### Test-Driven Development (TDD)

vibe-rag follows TDD for all new features:

1. **Write failing test first**
   ```python
   @pytest.mark.unit
   def test_new_feature():
       """Test description."""
       result = new_feature()
       assert result == expected
   ```

2. **Run test (should fail)**
   ```bash
   pytest tests/unit/test_new_feature.py -v
   ```

3. **Implement feature**
   ```python
   def new_feature():
       return expected
   ```

4. **Run test (should pass)**
   ```bash
   pytest tests/unit/test_new_feature.py -v
   ```

5. **Refactor if needed**

6. **Commit with descriptive message**

### Async Tests

Use `@pytest.mark.asyncio` for async tests:

```python
@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_function():
    """Test async operations."""
    result = await some_async_function()
    assert result is not None
```

### Parameterized Tests

Test multiple inputs efficiently:

```python
@pytest.mark.unit
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
    ("", ""),
])
def test_uppercase(input, expected):
    """Test string uppercasing."""
    assert input.upper() == expected
```

### Mocking External Dependencies

Always mock external APIs in unit tests:

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.unit
@pytest.mark.asyncio
async def test_with_mock():
    """Test with mocked external service."""
    with patch('vibe_rag.providers.gemini.GeminiAPI') as mock_api:
        mock_api.return_value.generate = AsyncMock(return_value="response")
        result = await some_function_using_gemini()
        assert result == "response"
```

## Coverage Goals

Maintain high test coverage for production readiness:

- **Core engine**: 90%+
- **Providers**: 85%+
- **Storage**: 85%+
- **Pipeline**: 80%+
- **Utilities**: 75%+

Check coverage:
```bash
pytest --cov=vibe_rag --cov-report=term-missing
```

## Examples

See `tests/unit/test_testing_utilities.py` for comprehensive examples of:
- Using fixtures
- Testing mocks
- Async test patterns
- Metadata filtering
- Collection operations

## Continuous Integration

Tests run automatically on:
- Every commit (unit tests)
- Pull requests (all tests)
- Main branch merges (all tests + coverage report)

Local pre-commit hook runs unit tests before commit.

## Troubleshooting

**Tests not found:**
```bash
# Ensure you're in project root
cd /path/to/vibe-setup

# Check pytest configuration
pytest --collect-only
```

**Fixtures not found:**
```bash
# Check conftest.py exists
ls tests/conftest.py

# Verify fixture imports
pytest --fixtures
```

**Async tests failing:**
```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Check pyproject.toml has asyncio_mode configured
```

**Coverage not working:**
```bash
# Install pytest-cov
pip install pytest-cov

# Check .coveragerc or pyproject.toml configuration
```

## Best Practices

1. **Write tests first** (TDD)
2. **Keep tests fast** (mock external dependencies)
3. **One assertion per test** (easier debugging)
4. **Use descriptive names** (`test_document_with_metadata_filters_by_category`)
5. **Test edge cases** (empty inputs, None values, errors)
6. **Clean up resources** (use fixtures for setup/teardown)
7. **Avoid test interdependencies** (each test should run independently)
8. **Use appropriate markers** (`@pytest.mark.unit`, etc.)

## Resources

- pytest documentation: https://docs.pytest.org/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- pytest-cov: https://pytest-cov.readthedocs.io/
- vibe-rag testing utilities: `vibe_rag/testing/`
