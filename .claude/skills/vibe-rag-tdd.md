---
name: vibe-rag-tdd
description: TDD workflow specifically for vibe-rag framework development - ensures adapter pattern, async operations, and proper mocking
---

**Note:** This skill is loaded via file read (`.claude/skills/vibe-rag-tdd.md`) because Claude Code does not support project-local skill registration.

# vibe-rag TDD Workflow

Use this skill when implementing any component in the vibe-rag framework.

## Critical Requirements

**ALWAYS:**
1. Write failing tests FIRST
2. Use async/await for all I/O operations
3. Mock external dependencies (no real API calls in unit tests)
4. Follow adapter pattern (implement interface, not concrete class)
5. Use Pydantic for all config and data models
6. Handle errors with custom exceptions

## Testing Strategy for vibe-rag

### Test Coverage Targets

Maintain these minimum coverage levels:

- **Core engine:** 90%+
- **Providers:** 85%+
- **Storage:** 85%+
- **Pipeline:** 80%+
- **Utilities:** 75%+

Check coverage with: `pytest --cov=vibe_rag --cov-report=term-missing`

### Testing Levels

**1. Unit Tests** (fast, isolated):
- Mock external dependencies (APIs, databases)
- Test one component at a time
- Located in `tests/unit/`
- Run with: `pytest tests/unit/`

**2. Integration Tests** (slower, real dependencies):
- Test component interactions
- Use testcontainers for databases
- Located in `tests/integration/`
- Run with: `pytest tests/integration/`

**3. E2E Tests** (slowest, full workflow):
- Test complete user workflows
- Located in `tests/e2e/`
- Run with: `pytest tests/e2e/`

### Mocking Guidelines

**CRITICAL: NEVER call real APIs in unit tests**

- **Mock Gemini:** Don't call actual Gemini API in tests
- **Mock OpenAI:** Don't call actual OpenAI API in tests
- **Mock databases:** Use `unittest.mock` for PostgreSQL connections

**Use these mocking tools:**

- `unittest.mock.AsyncMock` for async functions
- `unittest.mock.patch` for external dependencies
- `pytest.fixtures` for reusable test setup

**Example:**

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
@patch('vibe_rag.providers.gemini.genai')
async def test_gemini_generate(mock_genai):
    # Setup mock
    mock_response = AsyncMock()
    mock_response.text = "Generated text"
    mock_genai.GenerativeModel.return_value.generate_content_async.return_value = mock_response

    # Test
    provider = GeminiProvider(api_key="test-key")
    result = await provider.generate("prompt")

    # Assert
    assert result == "Generated text"
```

## TDD Workflow for vibe-rag

### Step 1: Understand the Interface

Before writing tests, identify:
- What base class/interface must be implemented?
  - `BaseLLMProvider` for LLM providers
  - `BaseVectorStore` for storage backends
  - `BasePipelineComponent` for pipeline components
- What methods are required?
- What exceptions should be raised?

### Step 2: Write Failing Tests

Create test file in `tests/unit/test_<component>.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from vibe_rag.<module>.<component> import ComponentClass
from vibe_rag.utils.errors import SpecificError

# Test 1: Verify interface implementation
def test_component_implements_interface():
    """Test that component implements required interface."""
    component = ComponentClass(...)
    assert hasattr(component, 'required_method')
    assert component.interface_property == "expected_value"

# Test 2: Test async method with mocks
@pytest.mark.asyncio
@patch('vibe_rag.<module>.<component>.external_dependency')
async def test_async_method_success(mock_dependency):
    """Test successful async operation with mocked dependency."""
    # Setup mock
    mock_dependency.async_call.return_value = AsyncMock(return_value="result")

    # Test
    component = ComponentClass(...)
    result = await component.async_method(input_data)

    # Assert
    assert result == expected_output
    mock_dependency.async_call.assert_called_once()

# Test 3: Test error handling
@pytest.mark.asyncio
async def test_method_handles_errors():
    """Test that errors are properly caught and re-raised."""
    component = ComponentClass(...)

    with pytest.raises(SpecificError, match="expected error message"):
        await component.method_that_should_fail(bad_input)
```

### Step 3: Run Tests (Should Fail)

```bash
pytest tests/unit/test_<component>.py -v
```

Expected: FAIL with "ModuleNotFoundError" or "NameError"

### Step 4: Implement Minimal Code

Create implementation file:

```python
from abc import ABC
from typing import Optional
from vibe_rag.<module>.base import BaseInterface
from vibe_rag.utils.errors import SpecificError

class ComponentClass(BaseInterface):
    """Component implementation.

    Args:
        config: Configuration parameters
        **kwargs: Additional parameters
    """

    def __init__(self, config: ConfigClass, **kwargs):
        self.config = config

    @property
    def interface_property(self) -> str:
        """Return property value."""
        return "expected_value"

    async def async_method(self, input_data: InputType) -> OutputType:
        """Async method with proper error handling.

        Args:
            input_data: Input data

        Returns:
            Processed output

        Raises:
            SpecificError: If operation fails
        """
        try:
            # Implementation here
            result = await self._process(input_data)
            return result
        except Exception as e:
            raise SpecificError(f"Operation failed: {e}")

    async def _process(self, data: InputType) -> OutputType:
        """Internal processing logic."""
        pass
```

### Step 5: Run Tests (Should Pass)

```bash
pytest tests/unit/test_<component>.py -v
```

Expected: PASS (all tests green)

### Step 6: Check Coverage

```bash
pytest tests/unit/test_<component>.py --cov=vibe_rag.<module> --cov-report=term-missing
```

Target: 85%+ coverage

### Step 7: Commit

```bash
git add tests/unit/test_<component>.py vibe_rag/<module>/<component>.py
git commit -m "feat: implement ComponentClass with tests

- Add ComponentClass implementing BaseInterface
- Add async method with error handling
- Mock external dependencies in tests
- Achieve 85%+ test coverage"
```

## Component-Specific Patterns

### For LLM Providers:

```python
# Test both generate() and embed() methods
# Mock the actual API client (genai, openai, etc.)
# Test temperature, max_tokens parameters
# Test both text generation and embedding generation
```

### For Storage Backends:

```python
# Test add_documents(), similarity_search(), delete_collection()
# Mock database connections (asyncpg.Pool, etc.)
# Test with different embedding dimensions
# Test metadata filtering with JSONB
```

### For Pipeline Components:

```python
# Test process() method with context passing
# Test component registration
# Test error propagation through pipeline
```

## Common Mistakes to Avoid

❌ Writing implementation before tests
❌ Calling real APIs in unit tests
❌ Forgetting async/await keywords
❌ Not mocking external dependencies
❌ Skipping error handling tests
❌ Not checking test coverage

✅ Tests first, implementation second
✅ Mock everything external
✅ All I/O operations are async
✅ Use custom exceptions
✅ Verify 85%+ coverage

## Verification Checklist

Before marking implementation complete:

- [ ] All tests written before implementation
- [ ] Tests fail first, then pass after implementation
- [ ] All I/O operations use async/await
- [ ] External dependencies are mocked
- [ ] Custom exceptions used for error handling
- [ ] Test coverage >= 85%
- [ ] Docstrings follow Google style
- [ ] Type hints on all parameters and returns
- [ ] Code simplified with `/code-simplifier`

## Reference

- Base interfaces: `vibe_rag/{providers,storage,pipeline}/base.py`
- Custom exceptions: `vibe_rag/utils/errors.py`
- Existing tests: `tests/unit/` for examples
- Design doc: `docs/plans/2026-02-28-rag-framework-design.md`
