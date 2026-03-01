# Pipeline Component System Design

**Date:** 2026-03-01
**Project:** vibe-rag
**Phase:** 1.4
**Status:** Approved

## Executive Summary

This document outlines the design for the Pipeline Component System in vibe-rag, enabling composable RAG workflows through a context-passing chain pattern. The system allows users to build custom retrieval pipelines by chaining components (retrievers, transformers, rerankers, generators) while maintaining rich observability for debugging and visualization.

**Key Design Principles:**
- **Context-Passing Chain**: Components receive and return enriched context
- **Rich Observability**: Built-in metadata tracking for visualization and debugging
- **Simple First, Future-Ready**: Clean interfaces that support advanced features later
- **Adapter Pattern Consistency**: Follows same pattern as providers and storage
- **Type Safety**: Using `PipelineContext` class instead of plain dictionaries

---

## 1. Architecture Overview

The pipeline system uses a **context-passing chain** pattern where:

1. Each component receives a `PipelineContext` object
2. Components enrich the context with their results and metadata
3. Context flows through the pipeline sequentially
4. Final context contains the complete audit trail

**Core components:**
- `BasePipelineComponent` - Abstract interface all components implement
- `PipelineContext` - Typed context object for pipeline execution
- `PipelineBuilder` - Fluent API for composing components
- Component registry - Decorator-based registration for discoverability

**Example flow:**
```python
context = PipelineContext(query="What is RAG?")
→ [QueryTransformer] → context with transformed_query
→ [VectorRetriever] → context with documents
→ [Reranker] → context with reranked_documents
→ [Generator] → context with answer
```

**Key design decisions:**
- Use typed `PipelineContext` from the start for better DX and type safety
- Structure supports future visualization and fine-tuning tools
- Components are stateless and composable
- Observability built-in via metadata tracking

---

## 2. Core Interfaces

### 2.1 BasePipelineComponent

The abstract base class all components implement:

```python
from abc import ABC, abstractmethod
from vibe_rag.pipeline.context import PipelineContext

class BasePipelineComponent(ABC):
    """Base interface for all pipeline components.

    Components are stateless processors that enrich the context
    as it flows through the pipeline.

    All components must implement:
    - process(): Main processing logic
    - component_type: Component category (retriever, transformer, etc.)
    - component_name: Unique identifier (defaults to class name)
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
        """Return component type (transformer, retriever, reranker, generator)."""
        pass

    @property
    def component_name(self) -> str:
        """Return unique component name (defaults to class name)."""
        return self.__class__.__name__

    def validate_context(self, context: PipelineContext) -> None:
        """Validate context has required data before processing.

        Override in subclasses to check preconditions.

        Raises:
            ConfigurationError: If context is invalid
        """
        pass
```

### 2.2 PipelineContext

Rich context object for pipeline execution:

```python
from typing import Any
from vibe_rag.models import Document

class PipelineContext:
    """Rich context for pipeline execution with built-in observability.

    Tracks:
    - Query and transformations
    - Documents at each stage
    - Component execution metadata
    - Timing and performance data

    Designed for:
    - Debugging: Full execution trace
    - Visualization: Component graph and data flow
    - Fine-tuning: Document provenance and score history
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

        Automatically tracks:
        - Component name
        - Timestamp
        - Custom metadata

        Args:
            component_name: Name of the component
            metadata: Component-specific metadata (timing, scores, etc.)
        """
        import time

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

**Future enhancements to PipelineContext:**
- Add `document_history` for tracking document transformations
- Add `query_transformations` list for multi-query strategies
- Add `component_decisions` for explainability
- Add helper methods for common operations (get_documents_by_stage, etc.)

### 2.3 Component Registry

Simple decorator for component discovery:

```python
# vibe_rag/pipeline/registry.py

from typing import Type
from vibe_rag.pipeline.base import BasePipelineComponent

# Global registry
_COMPONENT_REGISTRY: dict[str, Type[BasePipelineComponent]] = {}

def register_component(name: str):
    """Decorator to register a component for discovery.

    Args:
        name: Unique component identifier

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

**Future enhancements:**
- Add component metadata (description, required inputs, outputs)
- Add validation for duplicate registrations
- Add component discovery from plugins

### 2.4 PipelineBuilder

Fluent API for composing components:

```python
# vibe_rag/pipeline/builder.py

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

**Future enhancements:**
- Add type checking (ensure compatible component order)
- Add validation hooks (component compatibility checks)
- Add named component access (builder.get_component("retriever"))
- Add conditional branching (if/else in pipelines)

---

## 3. VectorRetriever Component

The first concrete component implementation - retrieves documents from vector storage.

```python
# vibe_rag/retrievers/vector.py

import time
from vibe_rag.pipeline.base import BasePipelineComponent
from vibe_rag.pipeline.context import PipelineContext
from vibe_rag.pipeline.registry import register_component
from vibe_rag.storage.base import BaseVectorStore
from vibe_rag.providers.base import BaseLLMProvider
from vibe_rag.utils.errors import RetrievalError

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
    """

    def __init__(
        self,
        storage: BaseVectorStore,
        provider: BaseLLMProvider,
        top_k: int = 5,
        filter_metadata: dict | None = None
    ):
        self.storage = storage
        self.provider = provider
        self.top_k = top_k
        self.filter_metadata = filter_metadata

    @property
    def component_type(self) -> str:
        """Return component type."""
        return "retriever"

    def validate_context(self, context: PipelineContext) -> None:
        """Validate context has required query field.

        Raises:
            ConfigurationError: If query is missing
        """
        if not context.query:
            raise ConfigurationError("VectorRetriever requires context.query")

    async def process(self, context: PipelineContext) -> PipelineContext:
        """Retrieve documents and enrich context.

        Expects: context.query (or context with transformed_query)
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

**Key aspects:**
- Uses existing `BaseVectorStore` and `BaseLLMProvider` (adapter pattern consistency)
- Adds rich metadata for future visualization
- Handles both original and transformed queries (flexible for query transformers)
- Timing built-in for observability
- Proper error handling with custom exceptions

**Future enhancements:**
- Add `document_history` tracking for visualization
- Support multiple retrieval strategies (hybrid search, graph search)
- Add caching layer for repeated queries
- Add score thresholding

---

## 4. Error Handling & Validation

### 4.1 Component Validation

Components can override `validate_context()` to check preconditions:

```python
class MyComponent(BasePipelineComponent):
    def validate_context(self, context: PipelineContext) -> None:
        if not context.documents:
            raise ConfigurationError("MyComponent requires documents")
```

### 4.2 Error Handling Strategy

- Components raise specific exceptions (`RetrievalError`, `EmbeddingError`, etc.)
- Pipeline executor can catch and add to context for debugging
- Failed component metadata still recorded in trace for observability

**Future enhancements:**
- Retry strategies for transient failures
- Fallback components (try retriever A, fall back to B)
- Circuit breaker pattern for external services
- Graceful degradation (continue pipeline with partial results)

---

## 5. Context Structure & Evolution

### 5.1 Phase 1 Structure

```python
context = PipelineContext(query="What is RAG?")

# After VectorRetriever
context.documents = [Document(...), ...]
context.metadata = {
    "VectorRetriever": {
        "top_k": 5,
        "num_results": 5,
        "duration_ms": 123.45,
        "filter_metadata": None,
        "query_used": "What is RAG?"
    }
}
context._trace = [
    {
        "component": "VectorRetriever",
        "timestamp": 1234567890.123,
        "top_k": 5,
        "num_results": 5,
        "duration_ms": 123.45
    }
]
```

### 5.2 Future Enhancements

**Visualization-ready structure:**

```python
# Document provenance tracking
context.document_history = {
    "doc-123": {
        "retrieved_at": "VectorRetriever",
        "score_history": [0.95, 0.92],  # Before/after reranking
        "transformations": ["chunked", "reranked"]
    }
}

# Query evolution tracking
context.query_transformations = [
    {"type": "original", "text": "What is RAG?"},
    {"type": "expanded", "text": "What is Retrieval-Augmented Generation?"}
]

# Component decisions (explainability)
context.component_decisions = {
    "Reranker": {
        "strategy": "cross_encoder",
        "confidence": 0.89,
        "reasoning": "High semantic similarity"
    }
}
```

This structure provides everything needed for:
- **Timeline visualization**: Duration traces, execution order
- **Document journey tracking**: Provenance, score evolution
- **Fine-tuning feedback**: Identify where retrieval fails
- **Explainability**: Understand component decisions

---

## 6. Testing Strategy

### 6.1 Unit Tests

**Test each component in isolation:**
- Mock dependencies (storage, providers)
- Verify context enrichment (input → output)
- Test error handling
- Verify validation logic

**Example:**
```python
async def test_vector_retriever_enriches_context():
    mock_storage = MockVectorStore()
    mock_provider = MockLLMProvider()

    retriever = VectorRetriever(
        storage=mock_storage,
        provider=mock_provider,
        top_k=3
    )

    context = PipelineContext(query="test query")
    result = await retriever.process(context)

    assert len(result.documents) == 3
    assert "VectorRetriever" in result.metadata
    assert result.metadata["VectorRetriever"]["top_k"] == 3
```

### 6.2 Integration Tests

**Test component composition:**
- Verify context flows correctly through pipeline
- Test with real storage/providers (optional, can be skipped)
- Verify metadata accumulation

**Example:**
```python
async def test_pipeline_composition():
    retriever = VectorRetriever(storage, provider)
    reranker = Reranker()

    pipeline = [retriever, reranker]

    context = PipelineContext(query="test")
    for component in pipeline:
        context = await component.process(context)

    assert len(context._trace) == 2
    assert context._trace[0]["component"] == "VectorRetriever"
    assert context._trace[1]["component"] == "Reranker"
```

### 6.3 Test Utilities

Mock component for testing:

```python
# vibe_rag/testing/mocks.py

class MockPipelineComponent(BasePipelineComponent):
    """Mock component for testing pipelines."""

    def __init__(self, component_type: str = "mock"):
        self._type = component_type

    @property
    def component_type(self) -> str:
        return self._type

    async def process(self, context: PipelineContext) -> PipelineContext:
        context.add_component_metadata(
            self.component_name,
            {"mock": True, "duration_ms": 0}
        )
        return context
```

---

## 7. Phase 1 Deliverables

### 7.1 Files to Implement

1. `vibe_rag/pipeline/base.py` - `BasePipelineComponent` interface
2. `vibe_rag/pipeline/context.py` - `PipelineContext` class
3. `vibe_rag/pipeline/registry.py` - Component registry and decorator
4. `vibe_rag/pipeline/builder.py` - `PipelineBuilder` for composition
5. `vibe_rag/retrievers/vector.py` - `VectorRetriever` implementation
6. `tests/unit/test_pipeline.py` - Component and context tests
7. `tests/unit/test_retrievers.py` - VectorRetriever tests

### 7.2 What We're NOT Building in Phase 1

- Other component types (transformers, rerankers, generators) - later phases
- Advanced PipelineBuilder features (type checking, validation hooks)
- Visualization tools - foundation only
- Event hooks - can add later without breaking changes
- Document provenance tracking - structure ready, implementation later
- Query transformation tracking - structure ready, implementation later

### 7.3 Success Criteria

- ✅ `BasePipelineComponent` defines clear interface with `process()` method
- ✅ `PipelineContext` tracks execution with metadata and trace
- ✅ Components self-register via `@register_component` decorator
- ✅ `PipelineBuilder` composes components with fluent API
- ✅ `VectorRetriever` integrates with storage backend and LLM provider
- ✅ Tests verify component composition and context flow
- ✅ Context structure supports future visualization tools

---

## 8. Future Enhancements

### 8.1 Advanced Pipeline Features

- **Type checking**: Ensure compatible component order (retriever before reranker)
- **Validation hooks**: Component compatibility checks before execution
- **Conditional branching**: If/else logic in pipelines
- **Parallel execution**: Run independent components concurrently
- **Pipeline templates**: Pre-built pipeline configurations

### 8.2 Observability & Debugging

- **Pipeline visualization UI**: Visual graph of component execution
- **Document journey tracking**: See how documents transform through pipeline
- **Performance profiling**: Identify bottlenecks
- **A/B testing**: Compare different pipeline configurations

### 8.3 Fine-Tuning & Feedback

- **Feedback loops**: Mark correct/incorrect retrievals
- **Fine-tune embeddings**: Use feedback to improve retrieval
- **Dynamic pipeline adjustment**: Adjust component parameters based on performance

---

## 9. Design Decisions & Rationale

### 9.1 Why PipelineContext Class Instead of Dict?

**Decision:** Use typed `PipelineContext` from the start

**Rationale:**
- Better developer experience (IDE autocomplete, type checking)
- Clear API (explicit methods vs dict key access)
- Future-proof (no migration needed later)
- Same implementation effort as plain dict
- Supports visualization tools from day one

### 9.2 Why Context-Passing Chain vs Event-Driven?

**Decision:** Context-passing chain pattern

**Rationale:**
- Simpler mental model (data flows through)
- Easy to debug (inspect context at any stage)
- Components are stateless and composable
- Perfect for visualization (context is the audit trail)
- Natural fit for async operations
- Can add event hooks later without breaking changes

### 9.3 Why Component Registry?

**Decision:** Decorator-based registration

**Rationale:**
- Simple discoverability (list all available components)
- Enables dynamic pipeline construction
- Foundation for plugin system later
- No runtime overhead

### 9.4 Why Rich Metadata from Start?

**Decision:** Track timing, scores, and component decisions in Phase 1

**Rationale:**
- User explicitly wants visualization and debugging tools
- Structure now prevents breaking changes later
- Minimal overhead (metadata tracking is cheap)
- Critical for fine-tuning and feedback loops

---

## 10. Open Questions & Risks

### 10.1 Resolved Questions

**Q: Should we use plain dict or PipelineContext class?**
A: PipelineContext class - same effort, better DX and future-proof

**Q: How much metadata should we track?**
A: Rich metadata from start - user needs visualization/debugging

**Q: Should we build PipelineBuilder in Phase 1?**
A: Yes - simple fluent API, minimal effort, better usability

### 10.2 Remaining Considerations

- **Performance**: Will metadata tracking impact performance at scale?
  - Mitigation: Track only essential data, make metadata optional later

- **Context size**: Could context grow too large with many components?
  - Mitigation: Add context pruning strategies in future phases

- **Component compatibility**: How to ensure components work together?
  - Mitigation: Add validation in PipelineBuilder later

---

## Appendix A: Example Usage

### A.1 Basic Retrieval Pipeline

```python
from vibe_rag.pipeline import PipelineBuilder, PipelineContext
from vibe_rag.retrievers import VectorRetriever
from vibe_rag.storage import PostgresVectorStore
from vibe_rag.providers import GeminiProvider

# Setup
storage = PostgresVectorStore(collection_name="docs")
provider = GeminiProvider(api_key="...")

# Build pipeline
retriever = VectorRetriever(
    storage=storage,
    provider=provider,
    top_k=5
)

pipeline = PipelineBuilder().add_component(retriever).build()

# Execute
context = PipelineContext(query="What is RAG?")
for component in pipeline:
    context = await component.process(context)

# Results
print(f"Found {len(context.documents)} documents")
print(f"Retrieval took {context.metadata['VectorRetriever']['duration_ms']}ms")
```

### A.2 Future: Multi-Stage Pipeline

```python
# Future phases will support:
pipeline = (
    PipelineBuilder()
    .add_component(query_transformer)
    .add_component(retriever)
    .add_component(reranker)
    .add_component(generator)
    .build()
)
```

---

**End of Design Document**
