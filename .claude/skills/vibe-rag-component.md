---
name: vibe-rag-component
description: Guide for implementing new pluggable components in vibe-rag framework - ensures adapter pattern and proper integration
---

# Implementing vibe-rag Components

Use this skill when adding a new provider, storage backend, or pipeline component.

## Component Types

### 1. LLM Provider (e.g., OpenAI, Anthropic)
### 2. Storage Backend (e.g., Chroma, Pinecone)
### 3. Pipeline Component (e.g., Reranker, Transformer)

## Universal Component Checklist

Before starting ANY component implementation:

1. **Read the base interface** - Understand what must be implemented
2. **Check existing implementations** - See how others did it
3. **Identify external dependencies** - What libraries/APIs needed?
4. **Plan mocking strategy** - How to test without real dependencies?

## Step-by-Step Implementation Guide

### Phase 1: Create the Interface Test

```python
# tests/unit/test_<component>.py
import pytest
from vibe_rag.<module>.base import Base<Component>

def test_base_<component>_is_abstract():
    """Test that Base<Component> cannot be instantiated."""
    with pytest.raises(TypeError):
        Base<Component>()

def test_base_<component>_interface():
    """Test that Base<Component> defines required methods."""
    assert hasattr(Base<Component>, 'method1')
    assert hasattr(Base<Component>, 'method2')
    assert hasattr(Base<Component>, 'component_name_property')
```

### Phase 2: Implement the Base Interface

```python
# vibe_rag/<module>/base.py
from abc import ABC, abstractmethod
from typing import Optional, List

class Base<Component>(ABC):
    """Base interface for all <component> implementations.

    All <component> implementations must inherit from this class
    and implement the required methods.
    """

    @property
    @abstractmethod
    def component_name(self) -> str:
        """Return component identifier."""
        pass

    @abstractmethod
    async def main_method(self, input_data: InputType, **kwargs) -> OutputType:
        """Main component method.

        Args:
            input_data: Input data
            **kwargs: Additional parameters

        Returns:
            Processed output

        Raises:
            ComponentError: If operation fails
        """
        pass

    def validate_config(self, config: dict) -> bool:
        """Validate component configuration.

        Args:
            config: Configuration dictionary

        Returns:
            True if valid

        Raises:
            ConfigurationError: If configuration is invalid
        """
        return True
```

### Phase 3: Create Concrete Implementation Test

```python
# tests/unit/test_<concrete_component>.py
import pytest
from unittest.mock import AsyncMock, patch
from vibe_rag.<module>.<concrete> import Concrete<Component>

def test_<concrete>_initialization():
    """Test Concrete<Component> initialization."""
    component = Concrete<Component>(
        api_key="test-key",
        param="value"
    )

    assert component.component_name == "concrete_name"
    assert component.param == "value"

@pytest.mark.asyncio
@patch('vibe_rag.<module>.<concrete>.external_lib')
async def test_<concrete>_main_method(mock_lib):
    """Test main method with mocked external dependency."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.result = "expected_output"
    mock_lib.async_call.return_value = AsyncMock(return_value=mock_response)

    # Test
    component = Concrete<Component>(api_key="test-key")
    result = await component.main_method(input_data)

    # Assert
    assert result == "expected_output"
    mock_lib.async_call.assert_called_once()

@pytest.mark.asyncio
async def test_<concrete>_error_handling():
    """Test error handling."""
    component = Concrete<Component>(api_key="test-key")

    with pytest.raises(ComponentError, match="Operation failed"):
        await component.main_method(invalid_input)
```

### Phase 4: Implement Concrete Component

```python
# vibe_rag/<module>/<concrete>.py
from typing import Optional
import external_lib

from vibe_rag.<module>.base import Base<Component>
from vibe_rag.utils.errors import ComponentError

class Concrete<Component>(Base<Component>):
    """<Provider/Storage/Component> implementation using <ExternalLib>.

    Supports <key features>.
    """

    def __init__(
        self,
        api_key: str,
        param: str = "default_value",
        **kwargs
    ):
        """Initialize <Concrete> component.

        Args:
            api_key: API key for authentication
            param: Configuration parameter
            **kwargs: Additional parameters
        """
        self.api_key = api_key
        self.param = param

        # Initialize external library
        external_lib.configure(api_key=api_key)
        self.client = external_lib.Client(param)

    @property
    def component_name(self) -> str:
        """Return component identifier."""
        return "concrete_name"

    async def main_method(
        self,
        input_data: InputType,
        optional_param: Optional[str] = None,
        **kwargs
    ) -> OutputType:
        """Main component method.

        Args:
            input_data: Input data
            optional_param: Optional parameter
            **kwargs: Provider-specific parameters

        Returns:
            Processed output

        Raises:
            ComponentError: If operation fails
        """
        try:
            # Call external API/library
            response = await self.client.async_call(
                input_data,
                param=optional_param or self.param
            )

            return response.result

        except Exception as e:
            raise ComponentError(f"<Concrete> operation failed: {e}")
```

### Phase 5: Register and Export

```python
# vibe_rag/<module>/__init__.py
from vibe_rag.<module>.base import Base<Component>
from vibe_rag.<module>.<concrete> import Concrete<Component>

__all__ = ["Base<Component>", "Concrete<Component>"]
```

### Phase 6: Update Main Package Exports

```python
# vibe_rag/__init__.py
from vibe_rag.<module> import Concrete<Component>

__all__ = [
    # ... existing exports
    "Concrete<Component>",
]
```

## Adapter Pattern Compliance

**Critical:** Ensure your component follows the adapter pattern:

```python
# ✅ GOOD: Code uses the interface
def use_component(component: Base<Component>):
    result = await component.main_method(data)

# ❌ BAD: Code depends on concrete implementation
def use_component(component: Concrete<Component>):
    result = await component.main_method(data)
```

## Integration with RAGEngine

For components used by RAGEngine:

1. **Add to RAGConfig:**
```python
# vibe_rag/config/models.py
class ComponentConfig(BaseModel):
    component_type: Literal["concrete_name", "other_name"]
    api_key: str
    param: str = "default"
```

2. **Add initialization in RAGEngine:**
```python
# vibe_rag/engine.py
def _initialize_component(self, config: ComponentConfig):
    if config.component_type == "concrete_name":
        return Concrete<Component>(
            api_key=config.api_key,
            param=config.param
        )
```

## Testing Checklist

Component implementation is complete when:

- [ ] Base interface defined with abstract methods
- [ ] Base interface tested for abstractness
- [ ] Concrete implementation inherits from base
- [ ] All abstract methods implemented
- [ ] All methods use async/await for I/O
- [ ] External dependencies mocked in tests
- [ ] Error handling with custom exceptions
- [ ] Test coverage >= 85%
- [ ] Component exported in package __init__
- [ ] Component registered in main package exports
- [ ] RAGConfig updated if component is configurable
- [ ] Code simplified with `/code-simplifier`

## Common Patterns

### For Async Initialization:

```python
async def initialize(self):
    """Initialize async resources."""
    self.connection_pool = await create_pool(...)

async def close(self):
    """Close async resources."""
    if self.connection_pool:
        await self.connection_pool.close()
```

### For Configuration Validation:

```python
def validate_config(self, config: dict) -> bool:
    """Validate configuration."""
    required = ["api_key", "endpoint"]
    if not all(key in config for key in required):
        raise ConfigurationError(f"Missing required config: {required}")
    return True
```

### For Registry Pattern:

```python
# Component self-registration
from vibe_rag.pipeline.registry import register_component

@register_component("component_name")
class MyComponent(BasePipelineComponent):
    pass
```

## Reference Files

- Base interfaces: `vibe_rag/{providers,storage,pipeline}/base.py`
- Existing components: `vibe_rag/{providers,storage,pipeline}/*.py`
- Configuration: `vibe_rag/config/models.py`
- Exceptions: `vibe_rag/utils/errors.py`
- Design doc: `docs/plans/2026-02-28-rag-framework-design.md`

## Questions to Ask

Before implementing:

1. What external library/API will be used?
2. What credentials/configuration is needed?
3. How will it be mocked in tests?
4. What errors can occur and how to handle them?
5. Does it need async initialization?
6. What cleanup is needed (connection closing, etc.)?
7. How does it integrate with RAGEngine?
