# Pytest Test Infrastructure Configuration Design

**Date:** 2026-03-01
**Task:** DUB-000d - Configure pytest and test infrastructure
**Status:** Approved
**Target Branch:** phase-1

## Overview

Configure comprehensive pytest infrastructure for production-grade testing with async support, coverage reporting, and reusable test utilities for the vibe-rag framework.

## Context

**Current State:**
- Basic pytest configuration exists in `pyproject.toml` with minimal settings
- Directory structure created (`tests/unit/`, `tests/integration/`, `tests/e2e/`)
- Some tests already exist (`tests/unit/test_models.py`)
- No test utilities or mocks available yet
- No coverage reporting configured

**Target Branch:**
- Branch: `phase-1`
- Already has: pyproject.toml, Document model, custom exceptions
- Needs: Enhanced pytest config, test utilities, coverage setup

**Requirements:**
- `pytest` command runs successfully
- Coverage reporting works
- Test utilities available for TDD workflow
- Aligns with vibe-rag's "batteries included but removable" philosophy

## Architecture

### Components

1. **Enhanced Pytest Configuration** (in `pyproject.toml`)
   - Async support for LLM/storage operations
   - Coverage reporting (terminal + HTML)
   - Test markers for organization (unit, integration, e2e)
   - Strict settings to catch errors early

2. **Test Utilities Package** (`vibe_rag/testing/`)
   - Mock implementations for fast unit testing
   - Pytest fixtures for common test scenarios
   - Reusable across all test types

3. **Verification Workflow**
   - Commands to verify pytest configuration
   - Validation that utilities work correctly

### Philosophy

**"Batteries Included But Removable"**
- Provide comprehensive testing utilities developers can use immediately
- Allow developers to replace with custom implementations
- Make TDD workflow smooth from day one
- Align with vibe-rag's core design philosophy

## Design Details

### 1. Pytest Configuration

**Enhanced `pyproject.toml` settings:**

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

**Key Decisions:**

| Setting | Rationale |
|---------|-----------|
| `asyncio_mode = "auto"` | Automatically detects and runs async tests (critical for async LLM/storage) |
| `--strict-markers` | Catches typos in `@pytest.mark.xyz` decorators early |
| `--cov=vibe_rag` | Focus coverage on framework code, not tests |
| `--cov-report=term-missing` | Show which lines lack coverage in terminal |
| `--cov-report=html` | Visual exploration in `htmlcov/` directory |
| `--tb=short` | Concise tracebacks for faster debugging |
| Test markers | Organize tests by speed/scope, enable selective runs |

**Coverage Approach:**
- No enforced thresholds initially (allows incremental improvement)
- Reports show gaps clearly (motivates filling them)
- HTML reports for visual exploration (easier to understand)

### 2. Test Utilities Structure

**File Organization:**

```
vibe_rag/testing/
├── __init__.py          # Export mocks and fixtures
├── mocks.py             # Mock implementations
└── fixtures.py          # Pytest fixtures
```

**Mock Implementations (`mocks.py`):**

**MockLLMProvider:**
- Implements `BaseLLMProvider` interface
- Returns predictable, deterministic responses
- No network calls or API dependencies
- Fast execution for unit tests

```python
class MockLLMProvider(BaseLLMProvider):
    """Mock LLM provider for testing."""

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate(self, prompt: str, **kwargs) -> str:
        # Returns predictable response based on prompt
        return f"Mock response to: {prompt}"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        # Returns deterministic embeddings
        return [[0.1, 0.2, 0.3] for _ in texts]
```

**MockVectorStore:**
- Implements `BaseVectorStore` interface
- In-memory storage (no database needed)
- Supports all storage operations
- Fast and isolated

```python
class MockVectorStore(BaseVectorStore):
    """Mock vector store for testing."""

    def __init__(self):
        self.documents = {}  # In-memory storage

    @property
    def store_name(self) -> str:
        return "mock"

    async def add_documents(...):
        # Store in memory

    async def similarity_search(...):
        # Simple in-memory search

    async def delete_collection(...):
        # Remove from memory
```

**Pytest Fixtures (`fixtures.py`):**

Common test data and configurations:

```python
@pytest.fixture
def sample_documents() -> list[Document]:
    """Sample documents for testing."""
    return [
        Document(content="Python programming guide", metadata={"type": "guide"}),
        Document(content="Machine learning tutorial", metadata={"type": "tutorial"}),
        Document(content="Data science handbook", metadata={"type": "handbook"}),
    ]

@pytest.fixture
def sample_embeddings() -> list[list[float]]:
    """Sample embedding vectors for testing."""
    return [[0.1] * 768 for _ in range(3)]

@pytest.fixture
def mock_llm_provider() -> MockLLMProvider:
    """Pre-configured mock LLM provider."""
    return MockLLMProvider()

@pytest.fixture
def mock_vector_store() -> MockVectorStore:
    """Pre-configured mock vector store."""
    return MockVectorStore()
```

**Design Principles:**

| Principle | Implementation |
|-----------|----------------|
| Deterministic | Same input always returns same output |
| Fast | No network/database calls |
| Reusable | Available across all test types |
| Async-compatible | All async methods properly implemented |
| Interface-compliant | Follow base class contracts exactly |

### 3. Verification Workflow

**Acceptance Criteria:**

1. ✅ `pytest` command runs successfully
2. ✅ Coverage reporting works
3. ✅ Test utilities are importable
4. ✅ Test markers are registered

**Verification Commands:**

```bash
# 1. Run existing tests (should pass)
pytest tests/unit/test_models.py -v

# 2. Verify coverage reporting
pytest tests/unit/test_models.py --cov=vibe_rag --cov-report=term-missing

# 3. Verify markers are registered
pytest --markers | grep -E "(unit|integration|e2e)"

# 4. Import test utilities
python -c "from vibe_rag.testing import MockLLMProvider, MockVectorStore"

# 5. Run all tests with full config
pytest
```

**Expected Outcomes:**

| Command | Expected Result |
|---------|----------------|
| Test execution | All 6 Document model tests pass |
| Coverage report | Shows vibe_rag/models.py coverage percentage |
| Markers | Lists unit, integration, e2e with descriptions |
| Import utilities | No errors, utilities importable |
| HTML report | `htmlcov/index.html` generated |

## Implementation Approach

### Phase 1: Configuration Enhancement
1. Update `[tool.pytest.ini_options]` in `pyproject.toml`
2. Add coverage settings and markers
3. Verify configuration loads correctly

### Phase 2: Test Utilities
1. Create `vibe_rag/testing/mocks.py` with mock implementations
2. Create `vibe_rag/testing/fixtures.py` with pytest fixtures
3. Update `vibe_rag/testing/__init__.py` to export utilities

### Phase 3: Verification
1. Run verification commands
2. Confirm all acceptance criteria met
3. Generate coverage report

## Testing Strategy

**Verification Tests:**

Since this is test infrastructure, verification is through:
- Running pytest successfully
- Generating coverage reports
- Importing utilities without errors
- Using mocks in example tests

**No separate test file needed** - the infrastructure validates itself through usage.

## Alternative Approaches Considered

### Alternative 1: Standalone pytest.ini

**Rejected because:**
- `pyproject.toml` is the modern Python standard (PEP 518)
- All other tool configs (black, ruff, mypy) already in `pyproject.toml`
- Single configuration file is easier to maintain
- Duplicate config between files causes sync issues

### Alternative 2: Minimal Config Only

**Rejected because:**
- Doesn't align with "batteries included" philosophy
- Requires developers to create utilities later
- Slows down TDD workflow
- Technical debt accumulates

### Alternative 3: Stub Utilities (Placeholders)

**Rejected because:**
- Half-implemented feels incomplete
- May cause confusion ("why are these empty?")
- Full implementation isn't significantly more work
- Provides immediate value for TDD

## Dependencies

**Existing:**
- `pytest>=7.0.0` (already in dev dependencies)
- `pytest-asyncio>=0.21.0` (already in dev dependencies)
- `pytest-cov>=4.0.0` (already in dev dependencies)

**New:**
- None required (all dependencies already specified)

## Success Criteria

- [x] Pytest configuration enhanced in `pyproject.toml`
- [x] Coverage reporting configured (terminal + HTML)
- [x] Test markers registered (unit, integration, e2e)
- [x] Mock implementations created (LLM provider, vector store)
- [x] Pytest fixtures created (sample data, pre-configured mocks)
- [x] Utilities exportable from `vibe_rag.testing`
- [x] `pytest` command runs successfully
- [x] Coverage reports generated correctly
- [x] All verification commands pass

## Future Enhancements

**Out of scope for this task:**

1. **Coverage thresholds** - Add minimum coverage requirements later
2. **Performance benchmarks** - Add pytest-benchmark for performance tests
3. **Parameterized fixtures** - Add configurable test data generators
4. **Integration test helpers** - Add testcontainers for database tests
5. **Snapshot testing** - Add pytest-snapshot for output validation

**These can be added incrementally as needs arise.**

## Notes

- This task establishes the foundation for TDD workflow
- Future tasks will use these utilities extensively
- Following the implementation plan from `docs/plans/2026-02-28-vibe-rag-implementation.md`
- Aligns with CLAUDE.md engineering standards and TDD requirements
