# Pipeline Component System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the pipeline component system for composable RAG workflows with rich observability.

**Architecture:** Context-passing chain pattern where components receive and enrich a typed `PipelineContext` object. Components self-register for discoverability and are composed using a fluent `PipelineBuilder` API.

**Tech Stack:** Python 3.10+, Pydantic, pytest, asyncio

---

## Phase 1.4 Implementation Tasks

### Task 1: PipelineContext Class

**Files:**
- Create: `vibe_rag/pipeline/context.py`
- Create: `tests/unit/test_pipeline_context.py`

**Step 1: Write failing test for PipelineContext creation**

Create `tests/unit/test_pipeline_context.py`:

```python
"""Tests for PipelineContext."""

import pytest
from vibe_rag.pipeline.context import PipelineContext
from vibe_rag.models import Document


def test_pipeline_context_creation():
    """Test creating PipelineContext with query."""
    context = PipelineContext(query="What is RAG?")

    assert context.query == "What is RAG?"
    assert context.documents == []
    assert context.answer is None
    assert context.metadata == {}
    assert context._trace == []


def test_pipeline_context_add_component_metadata():
    """Test adding component metadata."""
    context = PipelineContext(query="test")

    context.add_component_metadata(
        "VectorRetriever",
        {"top_k": 5, "duration_ms": 123.45}
    )

    assert "VectorRetriever" in context.metadata
    assert context.metadata["VectorRetriever"]["top_k"] == 5
    assert len(context._trace) == 1
    assert context._trace[0]["component"] == "VectorRetriever"
    assert "timestamp" in context._trace[0]


def test_pipeline_context_to_dict():
    """Test exporting context to dictionary."""
    context = PipelineContext(query="test")
    context.documents = [Document(content="doc1")]
    context.answer = "answer text"

    result = context.to_dict()

    assert result["query"] == "test"
    assert len(result["documents"]) == 1
    assert result["answer"] == "answer text"
    assert "metadata" in result
    assert "trace" in result


def test_pipeline_context_empty_documents():
    """Test that documents defaults to empty list."""
    context = PipelineContext(query="test")

    assert isinstance(context.documents, list)
    assert len(context.documents) == 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_pipeline_context.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'vibe_rag.pipeline.context'"

**Step 3: Implement PipelineContext**

Create `vibe_rag/pipeline/context.py`:

```python
"""Pipeline context for tracking execution state."""

import time
from typing import Any

from vibe_rag.models import Document


class PipelineContext:
    """Rich context for pipeline execution with built-in observability.

    Tracks query, documents, answer, and metadata throughout pipeline execution.
    Provides audit trail for debugging and visualization.

    Attributes:
        query: The user's question or search query
        documents: Retrieved documents (populated by retriever components)
        answer: Generated answer (populated by generator components)
        metadata: Component execution metadata
        _trace: Execution trace with timestamps

    Example:
        >>> context = PipelineContext(query="What is RAG?")
        >>> context.add_component_metadata("VectorRetriever", {"top_k": 5})
        >>> print(context.to_dict())
    """

    def __init__(self, query: str):
        """Initialize context with user query.

        Args:
            query: The user's question or search query
        """
        self.query = query
        self.documents: list[Document] = []
        self.answer: str | None = None
        self.metadata: dict[str, Any] = {}
        self._trace: list[dict] = []

    def add_component_metadata(
        self,
        component_name: str,
        metadata: dict
    ) -> None:
        """Add metadata for a component execution.

        Automatically tracks component name, timestamp, and custom metadata.

        Args:
            component_name: Name of the component
            metadata: Component-specific metadata (timing, scores, etc.)
        """
        self.metadata[component_name] = metadata
        self._trace.append({
            "component": component_name,
            "timestamp": time.time(),
            **metadata
        })

    def to_dict(self) -> dict:
        """Export as dictionary for serialization.

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        return {
            "query": self.query,
            "documents": [d.model_dump() for d in self.documents],
            "answer": self.answer,
            "metadata": self.metadata,
            "trace": self._trace
        }
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_pipeline_context.py -v`
Expected: PASS (5 tests)

**Step 5: Update pipeline package init**

Edit `vibe_rag/pipeline/__init__.py`:

```python
"""Pipeline components for composable RAG workflows."""

from vibe_rag.pipeline.context import PipelineContext

__all__ = ["PipelineContext"]
```

**Step 6: Commit**

```bash
git add vibe_rag/pipeline/context.py tests/unit/test_pipeline_context.py vibe_rag/pipeline/__init__.py
git commit -m "feat: add PipelineContext for pipeline execution tracking

- Implement PipelineContext with query, documents, answer fields
- Add metadata tracking with timestamps
- Support serialization via to_dict()
- Add comprehensive unit tests"
```

---

### Task 2: BasePipelineComponent Interface

**Files:**
- Create: `vibe_rag/pipeline/base.py`
- Modify: `tests/unit/test_pipeline_context.py` → `tests/unit/test_pipeline.py`

**Step 1: Write failing test for BasePipelineComponent**

Create `tests/unit/test_pipeline.py`:

```python
"""Tests for pipeline components."""

import pytest
from abc import ABC
from vibe_rag.pipeline.base import BasePipelineComponent
from vibe_rag.pipeline.context import PipelineContext


def test_base_component_is_abstract():
    """Test that BasePipelineComponent cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BasePipelineComponent()


def test_base_component_interface():
    """Test that BasePipelineComponent defines required interface."""
    assert hasattr(BasePipelineComponent, 'process')
    assert hasattr(BasePipelineComponent, 'component_type')
    assert hasattr(BasePipelineComponent, 'component_name')
    assert hasattr(BasePipelineComponent, 'validate_context')


class MockComponent(BasePipelineComponent):
    """Mock component for testing."""

    @property
    def component_type(self) -> str:
        return "mock"

    async def process(self, context: PipelineContext) -> PipelineContext:
        context.add_component_metadata(self.component_name, {"mock": True})
        return context


@pytest.mark.asyncio
async def test_mock_component_process():
    """Test that subclass can implement process."""
    component = MockComponent()
    context = PipelineContext(query="test")

    result = await component.process(context)

    assert result.query == "test"
    assert "MockComponent" in result.metadata
    assert result.metadata["MockComponent"]["mock"] is True


def test_component_name_defaults_to_class_name():
    """Test that component_name defaults to class name."""
    component = MockComponent()

    assert component.component_name == "MockComponent"


def test_validate_context_default():
    """Test that validate_context is a no-op by default."""
    component = MockComponent()
    context = PipelineContext(query="test")

    # Should not raise
    component.validate_context(context)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_pipeline.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'vibe_rag.pipeline.base'"

**Step 3: Implement BasePipelineComponent**

Create `vibe_rag/pipeline/base.py`:

```python
"""Base interface for pipeline components."""

from abc import ABC, abstractmethod

from vibe_rag.pipeline.context import PipelineContext


class BasePipelineComponent(ABC):
    """Base interface for all pipeline components.

    Components are stateless processors that enrich the context
    as it flows through the pipeline.

    All components must implement:
    - process(): Main processing logic
    - component_type: Component category (retriever, transformer, etc.)

    Optional:
    - component_name: Unique identifier (defaults to class name)
    - validate_context(): Validate context before processing

    Example:
        @register_component("my_component")
        class MyComponent(BasePipelineComponent):
            @property
            def component_type(self) -> str:
                return "transformer"

            async def process(self, context: PipelineContext) -> PipelineContext:
                # Process and enrich context
                return context
    """

    @abstractmethod
    async def process(self, context: PipelineContext) -> PipelineContext:
        """Process the context and return enriched context.

        Args:
            context: Current pipeline context

        Returns:
            Enriched context with component's results and metadata

        Raises:
            RAGException: If processing fails
        """
        pass

    @property
    @abstractmethod
    def component_type(self) -> str:
        """Return component type.

        Returns:
            Component category: "transformer", "retriever", "reranker", "generator"
        """
        pass

    @property
    def component_name(self) -> str:
        """Return unique component name.

        Defaults to class name. Override for custom names.

        Returns:
            Component identifier
        """
        return self.__class__.__name__

    def validate_context(self, context: PipelineContext) -> None:
        """Validate context has required data before processing.

        Override in subclasses to check preconditions.

        Args:
            context: Pipeline context to validate

        Raises:
            ConfigurationError: If context is invalid
        """
        pass
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_pipeline.py -v`
Expected: PASS (6 tests)

**Step 5: Update pipeline package init**

Edit `vibe_rag/pipeline/__init__.py`:

```python
"""Pipeline components for composable RAG workflows."""

from vibe_rag.pipeline.base import BasePipelineComponent
from vibe_rag.pipeline.context import PipelineContext

__all__ = ["BasePipelineComponent", "PipelineContext"]
```

**Step 6: Commit**

```bash
git add vibe_rag/pipeline/base.py tests/unit/test_pipeline.py vibe_rag/pipeline/__init__.py
git commit -m "feat: add BasePipelineComponent interface

- Define abstract base class for pipeline components
- Specify required methods: process, component_type
- Add optional validate_context for preconditions
- Add unit tests for interface contract"
```

---

### Task 3: Component Registry

**Files:**
- Create: `vibe_rag/pipeline/registry.py`
- Modify: `tests/unit/test_pipeline.py`

**Step 1: Write failing test for component registry**

Add to `tests/unit/test_pipeline.py`:

```python
from vibe_rag.pipeline.registry import (
    register_component,
    get_component,
    list_components,
    _COMPONENT_REGISTRY
)


def test_register_component_decorator():
    """Test component registration via decorator."""
    @register_component("test_component")
    class TestComponent(BasePipelineComponent):
        @property
        def component_type(self) -> str:
            return "test"

        async def process(self, context: PipelineContext) -> PipelineContext:
            return context

    # Clear registry first to avoid conflicts
    _COMPONENT_REGISTRY.clear()

    @register_component("test_component")
    class TestComponent2(BasePipelineComponent):
        @property
        def component_type(self) -> str:
            return "test"

        async def process(self, context: PipelineContext) -> PipelineContext:
            return context

    assert get_component("test_component") == TestComponent2
    assert "test_component" in list_components()


def test_get_component_returns_none_for_missing():
    """Test that get_component returns None for missing components."""
    result = get_component("nonexistent_component")

    assert result is None


def test_list_components():
    """Test listing all registered components."""
    _COMPONENT_REGISTRY.clear()

    @register_component("comp1")
    class Comp1(BasePipelineComponent):
        @property
        def component_type(self) -> str:
            return "test"

        async def process(self, context: PipelineContext) -> PipelineContext:
            return context

    @register_component("comp2")
    class Comp2(BasePipelineComponent):
        @property
        def component_type(self) -> str:
            return "test"

        async def process(self, context: PipelineContext) -> PipelineContext:
            return context

    components = list_components()

    assert "comp1" in components
    assert "comp2" in components
    assert len(components) == 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_pipeline.py::test_register_component_decorator -v`
Expected: FAIL with "ImportError: cannot import name 'register_component'"

**Step 3: Implement component registry**

Create `vibe_rag/pipeline/registry.py`:

```python
"""Component registry for pipeline component discovery."""

from typing import Type

from vibe_rag.pipeline.base import BasePipelineComponent

# Global registry
_COMPONENT_REGISTRY: dict[str, Type[BasePipelineComponent]] = {}


def register_component(name: str):
    """Decorator to register a component for discovery.

    Args:
        name: Unique component identifier

    Returns:
        Decorator function

    Example:
        @register_component("vector_retriever")
        class VectorRetriever(BasePipelineComponent):
            ...
    """
    def decorator(cls: Type[BasePipelineComponent]):
        _COMPONENT_REGISTRY[name] = cls
        return cls
    return decorator


def get_component(name: str) -> Type[BasePipelineComponent] | None:
    """Get a registered component by name.

    Args:
        name: Component identifier

    Returns:
        Component class or None if not found
    """
    return _COMPONENT_REGISTRY.get(name)


def list_components() -> list[str]:
    """List all registered component names.

    Returns:
        List of component identifiers
    """
    return list(_COMPONENT_REGISTRY.keys())
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_pipeline.py -k registry -v`
Expected: PASS (3 new tests)

**Step 5: Update pipeline package init**

Edit `vibe_rag/pipeline/__init__.py`:

```python
"""Pipeline components for composable RAG workflows."""

from vibe_rag.pipeline.base import BasePipelineComponent
from vibe_rag.pipeline.context import PipelineContext
from vibe_rag.pipeline.registry import (
    register_component,
    get_component,
    list_components,
)

__all__ = [
    "BasePipelineComponent",
    "PipelineContext",
    "register_component",
    "get_component",
    "list_components",
]
```

**Step 6: Commit**

```bash
git add vibe_rag/pipeline/registry.py tests/unit/test_pipeline.py vibe_rag/pipeline/__init__.py
git commit -m "feat: add component registry for discoverability

- Implement register_component decorator
- Add get_component and list_components functions
- Support component discovery and registration
- Add unit tests for registry operations"
```

---

### Task 4: PipelineBuilder

**Files:**
- Create: `vibe_rag/pipeline/builder.py`
- Modify: `tests/unit/test_pipeline.py`

**Step 1: Write failing test for PipelineBuilder**

Add to `tests/unit/test_pipeline.py`:

```python
from vibe_rag.pipeline.builder import PipelineBuilder


@pytest.mark.asyncio
async def test_pipeline_builder_add_component():
    """Test adding components to pipeline builder."""
    comp1 = MockComponent()
    comp2 = MockComponent()

    builder = PipelineBuilder()
    builder.add_component(comp1)
    builder.add_component(comp2)

    components = builder.build()

    assert len(components) == 2
    assert components[0] == comp1
    assert components[1] == comp2


@pytest.mark.asyncio
async def test_pipeline_builder_fluent_api():
    """Test fluent API chaining."""
    comp1 = MockComponent()
    comp2 = MockComponent()

    components = (
        PipelineBuilder()
        .add_component(comp1)
        .add_component(comp2)
        .build()
    )

    assert len(components) == 2


@pytest.mark.asyncio
async def test_pipeline_builder_empty():
    """Test building empty pipeline."""
    builder = PipelineBuilder()
    components = builder.build()

    assert components == []
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_pipeline.py::test_pipeline_builder_add_component -v`
Expected: FAIL with "ImportError: cannot import name 'PipelineBuilder'"

**Step 3: Implement PipelineBuilder**

Create `vibe_rag/pipeline/builder.py`:

```python
"""Pipeline builder for composing components."""

from vibe_rag.pipeline.base import BasePipelineComponent


class PipelineBuilder:
    """Build pipelines by chaining components.

    Provides a fluent API for composing pipeline components.

    Example:
        pipeline = (
            PipelineBuilder()
            .add_component(query_transformer)
            .add_component(retriever)
            .add_component(reranker)
            .build()
        )

        # Execute pipeline
        context = PipelineContext(query="What is RAG?")
        for component in pipeline:
            context = await component.process(context)
    """

    def __init__(self):
        """Initialize empty pipeline."""
        self.components: list[BasePipelineComponent] = []

    def add_component(
        self,
        component: BasePipelineComponent
    ) -> "PipelineBuilder":
        """Add a component to the pipeline.

        Args:
            component: Component instance to add

        Returns:
            Self for chaining
        """
        self.components.append(component)
        return self

    def build(self) -> list[BasePipelineComponent]:
        """Build and return the component list.

        Returns:
            List of components in execution order
        """
        return self.components
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_pipeline.py -k builder -v`
Expected: PASS (3 new tests)

**Step 5: Update pipeline package init**

Edit `vibe_rag/pipeline/__init__.py`:

```python
"""Pipeline components for composable RAG workflows."""

from vibe_rag.pipeline.base import BasePipelineComponent
from vibe_rag.pipeline.builder import PipelineBuilder
from vibe_rag.pipeline.context import PipelineContext
from vibe_rag.pipeline.registry import (
    register_component,
    get_component,
    list_components,
)

__all__ = [
    "BasePipelineComponent",
    "PipelineBuilder",
    "PipelineContext",
    "register_component",
    "get_component",
    "list_components",
]
```

**Step 6: Commit**

```bash
git add vibe_rag/pipeline/builder.py tests/unit/test_pipeline.py vibe_rag/pipeline/__init__.py
git commit -m "feat: add PipelineBuilder for component composition

- Implement fluent API for chaining components
- Support building component list
- Add unit tests for builder operations"
```

---

### Task 5: VectorRetriever Component

**Files:**
- Create: `vibe_rag/retrievers/vector.py`
- Create: `tests/unit/test_retrievers.py`

**Step 1: Write failing test for VectorRetriever**

Create `tests/unit/test_retrievers.py`:

```python
"""Tests for retriever components."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from vibe_rag.retrievers.vector import VectorRetriever
from vibe_rag.pipeline.context import PipelineContext
from vibe_rag.models import Document
from vibe_rag.testing.mocks import MockVectorStore, MockLLMProvider
from vibe_rag.utils.errors import RetrievalError, ConfigurationError


def test_vector_retriever_initialization():
    """Test VectorRetriever initialization."""
    storage = MockVectorStore(collection_name="test")
    provider = MockLLMProvider()

    retriever = VectorRetriever(
        storage=storage,
        provider=provider,
        top_k=3
    )

    assert retriever.storage == storage
    assert retriever.provider == provider
    assert retriever.top_k == 3
    assert retriever.component_type == "retriever"
    assert retriever.component_name == "VectorRetriever"


@pytest.mark.asyncio
async def test_vector_retriever_process():
    """Test VectorRetriever processes context and retrieves documents."""
    # Setup mocks
    storage = MockVectorStore(collection_name="test")
    provider = MockLLMProvider()

    # Add mock documents to storage
    docs = [
        Document(content="Document 1", score=0.95),
        Document(content="Document 2", score=0.85),
        Document(content="Document 3", score=0.75),
    ]
    storage.documents["test"] = docs

    # Create retriever
    retriever = VectorRetriever(
        storage=storage,
        provider=provider,
        top_k=3
    )

    # Process
    context = PipelineContext(query="test query")
    result = await retriever.process(context)

    # Verify
    assert len(result.documents) == 3
    assert result.documents[0].content == "Document 1"
    assert "VectorRetriever" in result.metadata
    assert result.metadata["VectorRetriever"]["top_k"] == 3
    assert result.metadata["VectorRetriever"]["num_results"] == 3
    assert "duration_ms" in result.metadata["VectorRetriever"]


@pytest.mark.asyncio
async def test_vector_retriever_validates_context():
    """Test that VectorRetriever validates context has query."""
    storage = MockVectorStore(collection_name="test")
    provider = MockLLMProvider()
    retriever = VectorRetriever(storage, provider)

    context = PipelineContext(query="")

    with pytest.raises(ConfigurationError, match="requires context.query"):
        retriever.validate_context(context)


@pytest.mark.asyncio
async def test_vector_retriever_handles_errors():
    """Test that VectorRetriever handles errors properly."""
    storage = MockVectorStore(collection_name="test")
    provider = MockLLMProvider()

    # Make storage raise error
    storage.similarity_search = AsyncMock(side_effect=Exception("DB error"))

    retriever = VectorRetriever(storage, provider)
    context = PipelineContext(query="test")

    with pytest.raises(RetrievalError, match="VectorRetriever failed"):
        await retriever.process(context)


@pytest.mark.asyncio
async def test_vector_retriever_with_metadata_filters():
    """Test VectorRetriever with metadata filters."""
    storage = MockVectorStore(collection_name="test")
    provider = MockLLMProvider()

    retriever = VectorRetriever(
        storage=storage,
        provider=provider,
        filter_metadata={"source": "docs"}
    )

    context = PipelineContext(query="test")
    result = await retriever.process(context)

    assert result.metadata["VectorRetriever"]["filter_metadata"] == {"source": "docs"}
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_retrievers.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'vibe_rag.retrievers.vector'"

**Step 3: Implement VectorRetriever**

Create `vibe_rag/retrievers/vector.py`:

```python
"""Vector retriever component for semantic search."""

import time

from vibe_rag.pipeline.base import BasePipelineComponent
from vibe_rag.pipeline.context import PipelineContext
from vibe_rag.pipeline.registry import register_component
from vibe_rag.storage.base import BaseVectorStore
from vibe_rag.providers.base import BaseLLMProvider
from vibe_rag.utils.errors import RetrievalError, ConfigurationError


@register_component("vector_retriever")
class VectorRetriever(BasePipelineComponent):
    """Retrieves documents using vector similarity search.

    Integrates with BaseVectorStore implementations to perform
    semantic search based on query embeddings.

    Args:
        storage: Vector storage backend
        provider: LLM provider for embedding generation
        top_k: Number of documents to retrieve
        filter_metadata: Optional metadata filters

    Example:
        storage = PostgresVectorStore(collection_name="docs")
        provider = GeminiProvider(api_key="...")
        retriever = VectorRetriever(storage, provider, top_k=5)

        context = PipelineContext(query="What is RAG?")
        result = await retriever.process(context)
        print(f"Retrieved {len(result.documents)} documents")
    """

    def __init__(
        self,
        storage: BaseVectorStore,
        provider: BaseLLMProvider,
        top_k: int = 5,
        filter_metadata: dict | None = None
    ):
        """Initialize VectorRetriever.

        Args:
            storage: Vector storage backend
            provider: LLM provider for embedding generation
            top_k: Number of documents to retrieve
            filter_metadata: Optional metadata filters
        """
        self.storage = storage
        self.provider = provider
        self.top_k = top_k
        self.filter_metadata = filter_metadata

    @property
    def component_type(self) -> str:
        """Return component type.

        Returns:
            Component category
        """
        return "retriever"

    def validate_context(self, context: PipelineContext) -> None:
        """Validate context has required query field.

        Args:
            context: Pipeline context to validate

        Raises:
            ConfigurationError: If query is missing or empty
        """
        if not context.query:
            raise ConfigurationError("VectorRetriever requires context.query")

    async def process(self, context: PipelineContext) -> PipelineContext:
        """Retrieve documents and enrich context.

        Expects: context.query (or context with transformed_query attribute)
        Adds: context.documents, context metadata

        Args:
            context: Current pipeline context

        Returns:
            Context enriched with retrieved documents

        Raises:
            RetrievalError: If retrieval fails
        """
        self.validate_context(context)
        start = time.time()

        try:
            # Get query (prefer transformed if available)
            query = getattr(context, 'transformed_query', None) or context.query

            # Generate embedding
            embeddings = await self.provider.embed([query])
            query_embedding = embeddings[0]

            # Search
            documents = await self.storage.similarity_search(
                query_embedding=query_embedding,
                k=self.top_k,
                filter_metadata=self.filter_metadata
            )

            # Enrich context
            context.documents = documents
            context.add_component_metadata(
                self.component_name,
                {
                    "top_k": self.top_k,
                    "num_results": len(documents),
                    "duration_ms": (time.time() - start) * 1000,
                    "filter_metadata": self.filter_metadata,
                    "query_used": query
                }
            )

            return context

        except Exception as e:
            raise RetrievalError(f"VectorRetriever failed: {e}")
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_retrievers.py -v`
Expected: PASS (5 tests)

**Step 5: Update retrievers package init**

Edit `vibe_rag/retrievers/__init__.py`:

```python
"""Retriever components for document retrieval."""

from vibe_rag.retrievers.vector import VectorRetriever

__all__ = ["VectorRetriever"]
```

**Step 6: Update main package exports**

Edit `vibe_rag/__init__.py` to add:

```python
from vibe_rag.retrievers import VectorRetriever
```

And add to `__all__`:

```python
"VectorRetriever",
```

**Step 7: Commit**

```bash
git add vibe_rag/retrievers/vector.py tests/unit/test_retrievers.py vibe_rag/retrievers/__init__.py vibe_rag/__init__.py
git commit -m "feat: implement VectorRetriever component

- Add VectorRetriever for semantic search
- Integrate with storage and provider interfaces
- Track retrieval metadata for observability
- Handle transformed queries from transformers
- Add comprehensive unit tests with mocks"
```

---

### Task 6: Integration Tests

**Files:**
- Create: `tests/integration/test_pipeline_integration.py`

**Step 1: Write integration test for pipeline composition**

Create `tests/integration/test_pipeline_integration.py`:

```python
"""Integration tests for pipeline composition."""

import pytest
from vibe_rag.pipeline import PipelineBuilder, PipelineContext
from vibe_rag.retrievers import VectorRetriever
from vibe_rag.testing.mocks import MockVectorStore, MockLLMProvider
from vibe_rag.models import Document


@pytest.mark.asyncio
async def test_pipeline_with_vector_retriever():
    """Test complete pipeline with VectorRetriever."""
    # Setup
    storage = MockVectorStore(collection_name="test")
    provider = MockLLMProvider()

    # Add test documents
    docs = [
        Document(content="Python is a programming language", score=0.95),
        Document(content="Machine learning with Python", score=0.85),
    ]
    storage.documents["test"] = docs

    # Build pipeline
    retriever = VectorRetriever(storage, provider, top_k=2)
    pipeline = PipelineBuilder().add_component(retriever).build()

    # Execute
    context = PipelineContext(query="What is Python?")
    for component in pipeline:
        context = await component.process(context)

    # Verify
    assert len(context.documents) == 2
    assert context.documents[0].content == "Python is a programming language"
    assert "VectorRetriever" in context.metadata
    assert len(context._trace) == 1
    assert context._trace[0]["component"] == "VectorRetriever"


@pytest.mark.asyncio
async def test_pipeline_context_flow():
    """Test that context flows through multiple components."""
    storage = MockVectorStore(collection_name="test")
    provider = MockLLMProvider()

    # Add test documents
    storage.documents["test"] = [Document(content="doc1")]

    # Build pipeline with multiple retrievers (simulate multi-stage)
    retriever1 = VectorRetriever(storage, provider, top_k=1)
    retriever2 = VectorRetriever(storage, provider, top_k=1)

    pipeline = (
        PipelineBuilder()
        .add_component(retriever1)
        .add_component(retriever2)
        .build()
    )

    # Execute
    context = PipelineContext(query="test")
    for component in pipeline:
        context = await component.process(context)

    # Verify metadata accumulated
    assert len(context._trace) == 2
    assert context._trace[0]["component"] == "VectorRetriever"
    assert context._trace[1]["component"] == "VectorRetriever"
    assert len(context.metadata) == 2


@pytest.mark.asyncio
async def test_pipeline_serialization():
    """Test that pipeline context can be serialized."""
    storage = MockVectorStore(collection_name="test")
    provider = MockLLMProvider()
    storage.documents["test"] = [Document(content="test doc")]

    retriever = VectorRetriever(storage, provider)
    pipeline = PipelineBuilder().add_component(retriever).build()

    context = PipelineContext(query="test")
    for component in pipeline:
        context = await component.process(context)

    # Serialize
    result = context.to_dict()

    assert result["query"] == "test"
    assert len(result["documents"]) == 1
    assert "metadata" in result
    assert "trace" in result
    assert len(result["trace"]) == 1
```

**Step 2: Run integration tests**

Run: `pytest tests/integration/test_pipeline_integration.py -v`
Expected: PASS (3 tests)

**Step 3: Commit**

```bash
git add tests/integration/test_pipeline_integration.py
git commit -m "test: add integration tests for pipeline composition

- Test pipeline with VectorRetriever
- Verify context flows through multiple components
- Test context serialization
- Validate metadata accumulation"
```

---

### Task 7: Documentation Updates

**Files:**
- Modify: `README.md`
- Create: `docs/examples/pipeline-usage.md`

**Step 1: Update README with pipeline example**

Add to `README.md` after the Quick Start section:

```markdown
## Pipeline Components

Build custom RAG pipelines by composing components:

```python
from vibe_rag.pipeline import PipelineBuilder, PipelineContext
from vibe_rag.retrievers import VectorRetriever
from vibe_rag.storage import PostgresVectorStore
from vibe_rag.providers import GeminiProvider

# Setup components
storage = PostgresVectorStore(collection_name="docs")
provider = GeminiProvider(api_key="...")
retriever = VectorRetriever(storage, provider, top_k=5)

# Build pipeline
pipeline = PipelineBuilder().add_component(retriever).build()

# Execute
context = PipelineContext(query="What is RAG?")
for component in pipeline:
    context = await component.process(context)

# Access results
print(f"Retrieved {len(context.documents)} documents")
print(f"Metadata: {context.metadata}")
```

## Component Types

- **Retrievers**: Fetch relevant documents (VectorRetriever)
- **Transformers**: Modify queries or documents (coming soon)
- **Rerankers**: Reorder retrieved documents (coming soon)
- **Generators**: Produce final responses (coming soon)
```

**Step 2: Create pipeline usage examples**

Create `docs/examples/pipeline-usage.md`:

```markdown
# Pipeline Usage Examples

## Basic Vector Retrieval

```python
from vibe_rag.pipeline import PipelineBuilder, PipelineContext
from vibe_rag.retrievers import VectorRetriever
from vibe_rag.storage import PostgresVectorStore
from vibe_rag.providers import GeminiProvider

async def basic_retrieval():
    # Setup
    storage = PostgresVectorStore(collection_name="knowledge_base")
    await storage.initialize()

    provider = GeminiProvider(api_key="your-api-key")

    # Create retriever
    retriever = VectorRetriever(
        storage=storage,
        provider=provider,
        top_k=5
    )

    # Build pipeline
    pipeline = PipelineBuilder().add_component(retriever).build()

    # Execute
    context = PipelineContext(query="What is machine learning?")
    for component in pipeline:
        context = await component.process(context)

    # Results
    for doc in context.documents:
        print(f"Score: {doc.score:.2f} - {doc.content[:100]}...")

    # Metadata
    print(f"Retrieval took: {context.metadata['VectorRetriever']['duration_ms']:.2f}ms")

    await storage.close()
```

## With Metadata Filtering

```python
# Filter by source
retriever = VectorRetriever(
    storage=storage,
    provider=provider,
    top_k=10,
    filter_metadata={"source": "documentation"}
)
```

## Pipeline Observability

```python
# Access execution trace
context = await execute_pipeline(pipeline, query="test")

for entry in context._trace:
    print(f"{entry['component']}: {entry['duration_ms']:.2f}ms")

# Export for visualization
data = context.to_dict()
# Send to visualization tool or save to file
```

## Creating Custom Components

```python
from vibe_rag.pipeline import BasePipelineComponent, PipelineContext, register_component

@register_component("my_component")
class MyCustomComponent(BasePipelineComponent):
    @property
    def component_type(self) -> str:
        return "transformer"

    async def process(self, context: PipelineContext) -> PipelineContext:
        # Custom processing logic
        context.add_component_metadata(
            self.component_name,
            {"custom_metric": 42}
        )
        return context
```
```

**Step 3: Commit documentation**

```bash
git add README.md docs/examples/pipeline-usage.md
git commit -m "docs: add pipeline component usage examples

- Update README with pipeline example
- Add detailed usage examples document
- Include metadata filtering and observability
- Document custom component creation"
```

---

### Task 8: Verification

**Files:**
- All implemented files

**Step 1: Run full test suite**

Run: `pytest -v`
Expected: All tests pass

**Step 2: Check test coverage**

Run: `pytest --cov=vibe_rag.pipeline --cov=vibe_rag.retrievers --cov-report=term-missing`
Expected: Coverage >= 85% for both modules

**Step 3: Run linters**

Run: `ruff check vibe_rag/pipeline vibe_rag/retrievers tests/unit/test_pipeline.py tests/unit/test_retrievers.py`
Expected: No errors

**Step 4: Run type checker**

Run: `mypy vibe_rag/pipeline vibe_rag/retrievers`
Expected: No type errors

**Step 5: Final verification commit**

```bash
git add .
git commit -m "chore: verify Phase 1.4 implementation complete

- All tests passing
- Coverage >= 85%
- No linter errors
- Type checking passes"
```

---

## Summary

**Implemented:**
- ✅ `PipelineContext` - Rich context with metadata tracking
- ✅ `BasePipelineComponent` - Interface for all components
- ✅ Component registry - Decorator-based registration
- ✅ `PipelineBuilder` - Fluent API for composition
- ✅ `VectorRetriever` - Semantic search component
- ✅ Unit tests with 85%+ coverage
- ✅ Integration tests for pipeline composition
- ✅ Documentation and examples

**Ready for:**
- Phase 1.5: Transformers and rerankers
- Phase 1.6: RAG engine integration
- Future: Visualization and fine-tuning tools

**Total Tasks:** 8
**Estimated Time:** 2-3 hours
**Testing:** TDD throughout, mocked dependencies
**Coverage Target:** 85%+

---

**Skills Referenced:**
- TDD workflow: `.claude/skills/vibe-rag-tdd.md`
- Code quality: `.claude/skills/vibe-rag-code-quality.md`
- Error handling: `.claude/skills/vibe-rag-error-handling.md`
- Commit guidelines: `.claude/skills/vibe-rag-commit-guidelines.md`
