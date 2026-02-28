# RAG Framework Design Document

**Date:** 2026-02-28
**Project:** vibe-rag
**Version:** 1.0
**Status:** Approved

## Executive Summary

This document outlines the design for `vibe-rag`, a production-grade, modular RAG (Retrieval-Augmented Generation) framework built with Python and LangChain. The framework follows a "batteries included, but removable" philosophy - providing quick-start modules for immediate use while maintaining full flexibility for customization.

**Key Design Principles:**
- **Modular & Pluggable**: Swap LLM providers, storage backends, and pipeline components via configuration
- **Production-Ready**: Built with PostgreSQL + pgvector, comprehensive error handling, and observability
- **Developer-Friendly**: Quick-start modules for prototyping, full customization for production
- **LangGraph Compatible**: Designed to integrate as a tool in LangGraph AI agent workflows
- **Domain-Agnostic**: Reusable across multiple projects and knowledge domains

---

## 1. Architecture Overview

### 1.1 Three-Layer Architecture

```
┌─────────────────────────────────────┐
│      Client Layer (Any System)      │
│   (REST API, Direct Import, gRPC)   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Service Layer (Optional)       │
│   - FastAPI wrapper (app-specific)  │
│   - REST endpoints                  │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│    Core Layer (vibe_rag library)    │
│   - RAG Engine                      │
│   - LLM Adapters                    │
│   - Vector Store Adapters           │
│   - Pipeline Components             │
│   - Document Processors             │
└─────────────────────────────────────┘
```

**Layer Responsibilities:**

1. **Core Layer** (Framework - Library):
   - Pure Python package for RAG logic
   - Pluggable components (providers, storage, retrievers)
   - Configuration schemas and validation
   - Can be pip-installed and imported directly

2. **Service Layer** (Application-Specific):
   - Optional HTTP wrapper (FastAPI, Flask, etc.)
   - Apps build their own service layer
   - Request/response handling
   - Authentication and authorization

3. **Client Layer** (Application):
   - Can import framework directly (`from vibe_rag import RAGEngine`)
   - Or consume via REST API
   - Or use as LangGraph tool

### 1.2 Design Philosophy: Batteries Included, But Removable

The framework supports multiple usage modes:

**Mode 1: Quick Start (Easy Mode)**
```python
from vibe_rag import QuickSetup

rag = QuickSetup.create(
    provider_api_key=os.getenv("GEMINI_API_KEY"),
    database_url=os.getenv("DATABASE_URL")
)
response = rag.query("question", collection="kb")
```

**Mode 2: Pre-built Modules**
```python
from vibe_rag.modules import BasicRAGModule

rag = BasicRAGModule(
    api_key=os.getenv("GEMINI_API_KEY"),
    db_url=os.getenv("DATABASE_URL")
)
```

**Mode 3: Configuration-Driven**
```python
from vibe_rag import RAGEngine, RAGConfig

config = RAGConfig.from_yaml("config.yaml")
rag = RAGEngine(config)
```

**Mode 4: Fully Custom**
```python
from vibe_rag import RAGEngine
from vibe_rag.pipeline import PipelineBuilder
from vibe_rag.providers import GeminiProvider
from vibe_rag.storage import PostgresVectorStore

storage = PostgresVectorStore(host="...", database="...")
provider = GeminiProvider(api_key="...", model="...")
pipeline = PipelineBuilder().add_retriever(...).build()

rag = RAGEngine(storage=storage, provider=provider, pipeline=pipeline)
```

---

## 2. Core Module Structure

### 2.1 Directory Layout

```
vibe_rag/
├── __init__.py                 # Public API exports
├── __version__.py              # Version string
├── quick.py                    # QuickSetup convenience class
├── engine.py                   # RAGEngine main class
│
├── config/
│   ├── models.py               # Pydantic configuration schemas
│   └── defaults.py             # Default values
│
├── modules/                    # Pre-built RAG modules
│   ├── __init__.py
│   ├── basic.py                # BasicRAGModule
│   ├── advanced.py             # AdvancedRAGModule
│   ├── graph.py                # GraphRAGModule (future)
│   └── agentic.py              # AgenticRAGModule (LangGraph-based)
│
├── pipeline/
│   ├── base.py                 # BasePipelineComponent abstract class
│   ├── builder.py              # PipelineBuilder for composition
│   └── registry.py             # Component registry
│
├── retrievers/
│   ├── vector.py               # VectorRetriever (pgvector)
│   ├── keyword.py              # BM25/keyword search
│   ├── hybrid.py               # HybridRetriever
│   └── graph.py                # GraphRetriever (future)
│
├── transformers/
│   ├── query.py                # Query transformation (HyDE, multi-query)
│   └── document.py             # Document chunking/processing
│
├── rerankers/
│   ├── cross_encoder.py        # Cross-encoder reranking
│   └── llm.py                  # LLM-based reranking
│
├── providers/
│   ├── base.py                 # BaseLLMProvider interface
│   ├── gemini.py               # Google Gemini adapter (initial focus)
│   ├── openai.py               # OpenAI adapter (future)
│   └── anthropic.py            # Anthropic adapter (future)
│
├── storage/
│   ├── base.py                 # BaseVectorStore interface
│   ├── postgres_vector.py      # PostgreSQL + pgvector (default)
│   ├── chroma.py               # Chroma adapter (optional)
│   └── custom/                 # User custom storage adapters
│
├── integrations/
│   ├── langgraph.py            # LangGraph tool wrapper
│   ├── langchain.py            # LangChain retriever interface
│   └── llamaindex.py           # LlamaIndex (future)
│
├── loaders/
│   ├── text.py                 # Text file loader
│   ├── pdf.py                  # PDF loader
│   └── markdown.py             # Markdown loader
│
├── utils/
│   ├── embeddings.py           # Embedding utilities
│   ├── chunking.py             # Text splitting strategies
│   ├── errors.py               # Custom exceptions
│   └── observability.py        # Metrics and logging
│
└── testing/                    # Testing utilities for apps
    ├── mocks.py                # Mock providers and storage
    ├── fixtures.py             # Common test data
    └── helpers.py              # Test utilities
```

### 2.2 Public API Surface

The framework exports a clean, minimal API:

```python
# Main classes
from vibe_rag import (
    RAGEngine,          # Core engine
    QuickSetup,         # One-liner setup
)

# Configuration
from vibe_rag import (
    RAGConfig,
    LLMProviderConfig,
    StorageConfig,
)

# Pre-built modules
from vibe_rag.modules import (
    BasicRAGModule,
    AdvancedRAGModule,
    AgenticRAGModule,
)

# Components for custom pipelines
from vibe_rag.pipeline import PipelineBuilder
from vibe_rag.providers import GeminiProvider, OpenAIProvider
from vibe_rag.storage import PostgresVectorStore
from vibe_rag.retrievers import VectorRetriever, HybridRetriever
from vibe_rag.rerankers import CrossEncoderReranker

# LangGraph integration
from vibe_rag.integrations.langgraph import RAGTool

# Testing utilities
from vibe_rag.testing import MockLLMProvider, MockVectorStore
```

---

## 3. Pipeline Component System

### 3.1 Component Architecture

All pipeline components implement a common interface:

```python
# pipeline/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict

class BasePipelineComponent(ABC):
    """Base class for all pipeline components"""

    @abstractmethod
    async def process(self, input_data: Any, context: Dict) -> Any:
        """Process input and return output"""
        pass

    @property
    @abstractmethod
    def component_type(self) -> str:
        """Return component type (retriever, transformer, reranker, generator)"""
        pass

    def validate_config(self, config: Dict) -> bool:
        """Validate component configuration"""
        return True
```

### 3.2 Component Types

1. **Transformers**: Modify queries or documents
   - Query expansion (HyDE, multi-query, step-back)
   - Document chunking and preprocessing

2. **Retrievers**: Fetch relevant documents
   - Vector search (pgvector)
   - Keyword search (BM25)
   - Hybrid retrieval
   - Graph-based retrieval

3. **Rerankers**: Reorder retrieved documents
   - Cross-encoder models
   - LLM-based reranking

4. **Generators**: Produce final responses
   - LLM-based generation
   - Template-based responses

### 3.3 Pipeline Execution Flow

```
Query → [Transformers] → [Retrievers] → [Rerankers] → [Generator] → Response
                            ↓
                    Context passed through all stages
```

### 3.4 Component Registry

Components self-register for discoverability:

```python
from vibe_rag.pipeline import register_component

@register_component("vector_retriever")
class VectorRetriever(BasePipelineComponent):
    component_type = "retriever"

    def __init__(self, top_k: int = 5, **kwargs):
        self.top_k = top_k

    async def process(self, query: str, context: Dict) -> List[Document]:
        # Retrieve from vector store
        pass
```

### 3.5 Pipeline Strategies

The framework provides preset pipeline strategies:

**Basic Strategy:**
```yaml
name: basic
description: Simple vector search + generation
components:
  - type: retriever
    class: VectorRetriever
    params:
      top_k: 5
  - type: generator
    class: LLMGenerator
```

**Advanced Strategy:**
```yaml
name: advanced
description: Query enhancement + retrieval + reranking
components:
  - type: transformer
    class: HyDETransformer
    params:
      num_hypothetical_docs: 3
  - type: retriever
    class: VectorRetriever
    params:
      top_k: 20
  - type: reranker
    class: CrossEncoderReranker
    params:
      model: cross-encoder/ms-marco-MiniLM-L-6-v2
      top_k: 5
  - type: generator
    class: LLMGenerator
```

**Custom Pipeline:**
```python
from vibe_rag.pipeline import PipelineBuilder

pipeline = PipelineBuilder() \
    .add_transformer("query_expansion", num_queries=5) \
    .add_retriever("hybrid", semantic_weight=0.7, keyword_weight=0.3) \
    .add_reranker("cross_encoder", top_k=5) \
    .build()

rag = RAGEngine(pipeline=pipeline)
```

---

## 4. LLM Provider System

### 4.1 Provider Interface

All LLM providers implement a common interface:

```python
# providers/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class BaseLLMProvider(ABC):
    """Base interface for all LLM providers"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate text from prompt"""
        pass

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier"""
        pass
```

### 4.2 Gemini Provider (Initial Focus)

```python
# providers/gemini.py
import google.generativeai as genai

class GeminiProvider(BaseLLMProvider):
    provider_name = "gemini"

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-pro",
        temperature: float = 0.7,
        **kwargs
    ):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)
        self.embedding_model = "models/text-embedding-004"
        self.temperature = temperature

    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.model.generate_content_async(
            prompt,
            generation_config={"temperature": kwargs.get("temperature", self.temperature)}
        )
        return response.text

    async def embed(self, texts: List[str]) -> List[List[float]]:
        result = genai.embed_content(
            model=self.embedding_model,
            content=texts
        )
        return result['embedding']
```

### 4.3 Provider Configuration

Apps configure providers via config objects:

```python
from vibe_rag import LLMProviderConfig

config = LLMProviderConfig(
    provider="gemini",
    model="gemini-1.5-pro",
    api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.7,
    max_tokens=1000
)
```

Framework provides defaults, apps override as needed.

---

## 5. Storage Layer

### 5.1 Storage Interface

All storage backends implement a common interface:

```python
# storage/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class BaseVectorStore(ABC):
    """Base interface for all vector storage backends"""

    @abstractmethod
    async def add_documents(
        self,
        documents: List[Document],
        collection_name: str,
        embeddings: List[List[float]]
    ) -> List[str]:
        """Add documents with embeddings to collection"""
        pass

    @abstractmethod
    async def similarity_search(
        self,
        query_embedding: List[float],
        collection_name: str,
        top_k: int = 5,
        filters: Optional[Dict] = None
    ) -> List[Document]:
        """Vector similarity search with optional metadata filters"""
        pass

    @abstractmethod
    async def delete_collection(self, collection_name: str):
        """Delete entire collection"""
        pass

    @property
    @abstractmethod
    def store_name(self) -> str:
        """Return storage backend identifier"""
        pass
```

### 5.2 PostgreSQL + pgvector (Default)

**Database schema:**

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Document metadata table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_name VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB,
    source VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Vector embeddings table
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(768),  -- Dimension depends on embedding model
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_documents_collection ON documents(collection_name);
CREATE INDEX idx_embeddings_document ON embeddings(document_id);
CREATE INDEX idx_embeddings_vector ON embeddings
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

**Implementation:**

```python
# storage/postgres_vector.py
from vibe_rag.storage.base import BaseVectorStore

class PostgresVectorStore(BaseVectorStore):
    store_name = "postgres"

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str,
        user: str,
        password: str,
        **kwargs
    ):
        self.connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        # Initialize connection pool

    async def add_documents(self, documents, collection_name, embeddings):
        # Insert documents and embeddings
        pass

    async def similarity_search(self, query_embedding, collection_name, top_k, filters):
        # Vector similarity search with metadata filtering
        pass
```

### 5.3 Custom Storage Backends

Apps can provide custom storage implementations:

```python
from vibe_rag.storage.base import BaseVectorStore
from vibe_rag import register_storage

@register_storage("my_custom_db")
class MyCustomVectorStore(BaseVectorStore):
    store_name = "my_custom_db"

    async def add_documents(self, documents, collection_name, embeddings):
        # Custom implementation
        pass

    async def similarity_search(self, query_embedding, collection_name, top_k, filters):
        # Custom implementation
        pass
```

---

## 6. Configuration Management

### 6.1 Configuration Philosophy

**Framework provides:**
- Configuration schemas (Pydantic models)
- Validation logic
- Default values

**Apps provide:**
- Actual configuration files
- Environment-specific values
- Secrets management

### 6.2 Configuration Schemas

```python
# config/models.py
from pydantic import BaseModel
from typing import Literal, Optional

class LLMProviderConfig(BaseModel):
    """LLM provider configuration"""
    provider: Literal["gemini", "openai", "anthropic"]
    model: str
    api_key: str
    temperature: float = 0.7
    max_tokens: int = 1000

class StorageConfig(BaseModel):
    """Storage backend configuration"""
    backend: Literal["postgres", "chroma", "custom"]
    connection_params: dict

class RAGConfig(BaseModel):
    """Main RAG configuration"""
    llm: LLMProviderConfig
    storage: StorageConfig
    default_strategy: str = "basic"
    chunk_size: int = 512
    chunk_overlap: int = 50
    top_k: int = 5

    @classmethod
    def from_yaml(cls, path: str) -> "RAGConfig":
        """Load config from YAML file"""
        pass
```

### 6.3 App Configuration Example

```yaml
# app's config.yaml
llm:
  provider: gemini
  model: gemini-1.5-pro
  api_key: ${GEMINI_API_KEY}
  temperature: 0.7

storage:
  backend: postgres
  connection_params:
    host: ${DB_HOST}
    port: 5432
    database: my_kb
    user: ${DB_USER}
    password: ${DB_PASSWORD}

default_strategy: advanced
chunk_size: 1000
top_k: 10
```

```python
# app's main.py
from vibe_rag import RAGEngine, RAGConfig

config = RAGConfig.from_yaml("config.yaml")
rag = RAGEngine(config)
```

---

## 7. LangGraph Integration

### 7.1 Integration Architecture

The framework is designed to work as a **tool within LangGraph AI agents**:

```
┌─────────────────────────────────────────────┐
│          LangGraph AI Agent (App)           │
│  ┌─────────────────────────────────────┐   │
│  │  Agent State & Orchestration        │   │
│  └─────────────────────────────────────┘   │
│                    │                        │
│  ┌─────────────────┼────────────────────┐  │
│  │      Agent Tools                     │  │
│  │  ├─ Web Search Tool                  │  │
│  │  ├─ Calculator Tool                  │  │
│  │  ├─ RAG Tool (vibe_rag) ←────────────┼──┼─ Integration point
│  │  └─ Custom Tools...                  │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│       vibe_rag Framework (Library)          │
│  ┌─────────────────────────────────────┐   │
│  │  RAGEngine                          │   │
│  └─────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### 7.2 RAG as a LangGraph Tool

The framework provides a LangGraph-compatible tool wrapper:

```python
# integrations/langgraph.py
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

class RAGToolInput(BaseModel):
    """Input schema for RAG tool"""
    question: str = Field(description="Question to answer using knowledge base")
    collection: str = Field(default="default", description="Knowledge base collection")
    top_k: int = Field(default=5, description="Number of documents to retrieve")

class RAGTool(BaseTool):
    """LangGraph-compatible RAG tool"""

    name: str = "knowledge_base_search"
    description: str = """
    Search the knowledge base to answer questions using retrieved documents.
    Use this when you need domain-specific information from the company's knowledge base.
    Returns: answer with supporting source documents.
    """
    args_schema: type[BaseModel] = RAGToolInput
    rag_engine: RAGEngine

    def _run(self, question: str, collection: str = "default", top_k: int = 5) -> dict:
        """Synchronous execution"""
        result = self.rag_engine.query_sync(
            question=question,
            collection=collection,
            top_k=top_k
        )
        return {
            "answer": result["answer"],
            "sources": [{"content": doc.content, "score": doc.score} for doc in result["sources"]]
        }

    async def _arun(self, question: str, collection: str = "default", top_k: int = 5) -> dict:
        """Async execution"""
        result = await self.rag_engine.query(
            question=question,
            collection=collection,
            top_k=top_k
        )
        return {
            "answer": result["answer"],
            "sources": [{"content": doc.content, "score": doc.score} for doc in result["sources"]]
        }
```

### 7.3 App Usage Example

```python
# app/agent.py
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from vibe_rag import RAGEngine
from vibe_rag.integrations.langgraph import RAGTool

# Initialize RAG
rag_engine = RAGEngine.from_config("config.yaml")
rag_tool = RAGTool(rag_engine=rag_engine)

# Create LangGraph agent with RAG as a tool
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
agent = create_react_agent(llm, tools=[rag_tool, ...])

# Agent decides when to use RAG
result = agent.invoke({
    "messages": [("user", "What is our refund policy?")]
})
```

### 7.4 Two Levels of LangGraph Integration

1. **App Level** (Primary use case): LangGraph agent uses RAG as a tool
2. **Framework Level** (Optional): Agentic RAG strategy uses LangGraph internally for multi-step retrieval

```python
# Optional: Agentic RAG strategy using LangGraph internally
from vibe_rag.modules import AgenticRAGModule

rag = AgenticRAGModule(
    api_key=os.getenv("GEMINI_API_KEY"),
    db_url=os.getenv("DATABASE_URL"),
    agent_config={
        "tools": ["query_rewriter", "multi_hop_search"],
        "max_iterations": 5
    }
)
```

---

## 8. Document Processing

### 8.1 Document Processor

```python
# transformers/document.py
from typing import List, Literal

class DocumentProcessor:
    """Handles document loading and chunking"""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
        chunking_strategy: Literal["fixed", "semantic", "recursive"] = "recursive"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = chunking_strategy

    async def process_document(
        self,
        content: str,
        metadata: dict = None
    ) -> List[Document]:
        """Split document into chunks"""
        pass
```

### 8.2 Document Loaders

Pre-built loaders for common formats:

```python
from vibe_rag.loaders import (
    TextLoader,
    PDFLoader,
    MarkdownLoader,
)

# Simple usage
from vibe_rag.modules import BasicRAGModule

rag = BasicRAGModule(...)
rag.ingest_file("docs/policy.pdf", collection="kb")

# Custom processing
from vibe_rag.transformers import DocumentProcessor

processor = DocumentProcessor(
    chunk_size=1000,
    chunk_overlap=100,
    chunking_strategy="semantic"
)

rag = RAGEngine(document_processor=processor)
```

---

## 9. Error Handling & Observability

### 9.1 Custom Exceptions

```python
# utils/errors.py
class RAGException(Exception):
    """Base exception for all RAG errors"""
    pass

class EmbeddingError(RAGException):
    """Embedding generation failed"""
    pass

class RetrievalError(RAGException):
    """Document retrieval failed"""
    pass

class LLMProviderError(RAGException):
    """LLM provider error (API error, timeout, etc.)"""
    pass

class StorageError(RAGException):
    """Storage backend error"""
    pass
```

### 9.2 Metrics & Observability

```python
# utils/observability.py
class RAGMetrics:
    """Track RAG operation metrics"""

    def record_query(
        self,
        retrieval_time_ms: float,
        generation_time_ms: float,
        tokens_used: int,
        documents_retrieved: int,
        query_id: str
    ):
        pass

    def get_metrics_summary(self) -> dict:
        """Get aggregated metrics"""
        pass
```

### 9.3 Response Format with Metadata

```python
response = {
    "answer": "The refund policy allows...",
    "sources": [
        {
            "document_id": "uuid",
            "content": "excerpt",
            "score": 0.95,
            "metadata": {"source": "policy.pdf", "page": 3}
        }
    ],
    "metadata": {
        "query_id": "uuid",
        "retrieval_time_ms": 120,
        "generation_time_ms": 800,
        "total_time_ms": 920,
        "tokens_used": 450,
        "documents_retrieved": 5,
        "strategy_used": "advanced"
    }
}
```

---

## 10. Testing Strategy

### 10.1 Testing Structure

```
tests/
├── unit/                       # Unit tests for components
│   ├── test_providers.py
│   ├── test_retrievers.py
│   ├── test_pipeline.py
│   └── test_storage.py
├── integration/                # Integration tests
│   ├── test_rag_engine.py
│   └── test_langgraph_integration.py
└── e2e/                        # End-to-end tests
    └── test_full_workflow.py
```

### 10.2 Testing Utilities

```python
# testing/mocks.py
class MockLLMProvider(BaseLLMProvider):
    """Mock LLM for testing without API calls"""
    provider_name = "mock"

    def __init__(self, responses: List[str] = None):
        self.responses = responses or ["Mock response"]
        self.call_count = 0

    async def generate(self, prompt: str, **kwargs) -> str:
        return self.responses[self.call_count % len(self.responses)]

    async def embed(self, texts: List[str]) -> List[List[float]]:
        return [[0.1] * 768] * len(texts)

class MockVectorStore(BaseVectorStore):
    """In-memory vector store for testing"""
    store_name = "mock"

    def __init__(self):
        self.documents = {}

    async def add_documents(self, documents, collection_name, embeddings):
        if collection_name not in self.documents:
            self.documents[collection_name] = []
        self.documents[collection_name].extend(documents)
        return [str(i) for i in range(len(documents))]
```

### 10.3 Coverage Targets

| Component | Target Coverage |
|-----------|----------------|
| Core engine | 90%+ |
| Providers | 85%+ |
| Storage | 85%+ |
| Pipeline | 80%+ |
| Utilities | 75%+ |

### 10.4 Testing Example

```python
# App tests using framework mocks
from vibe_rag import RAGEngine
from vibe_rag.testing import MockLLMProvider, MockVectorStore

def test_rag_query():
    rag = RAGEngine(
        provider=MockLLMProvider(responses=["Test answer"]),
        storage=MockVectorStore()
    )

    result = rag.query_sync("test question", collection="test")

    assert result["answer"] == "Test answer"
    assert "metadata" in result
```

---

## 11. Package Distribution

### 11.1 Package Structure

```
vibe-rag/
├── pyproject.toml              # Modern Python packaging
├── setup.py                    # Legacy compatibility
├── README.md
├── LICENSE
├── CHANGELOG.md
├── vibe_rag/
├── tests/
├── docs/
└── examples/
```

### 11.2 pyproject.toml

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "vibe-rag"
version = "0.1.0"
description = "Production-grade modular RAG framework"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}

dependencies = [
    "langchain>=0.1.0",
    "langchain-google-genai>=1.0.0",
    "psycopg[binary]>=3.1.0",
    "pgvector>=0.2.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "numpy>=1.24.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
langgraph = [
    "langgraph>=0.1.0",
]
all = ["vibe-rag[dev,langgraph]"]
```

### 11.3 Installation

```bash
# Basic installation
pip install vibe-rag

# With LangGraph support
pip install vibe-rag[langgraph]

# Development installation
pip install -e ".[dev]"
```

### 11.4 Versioning

- **Semantic Versioning (SemVer)**: MAJOR.MINOR.PATCH
- **0.x.x**: Initial development
- **1.0.0**: Stable API
- **Breaking changes**: Increment MAJOR
- **New features**: Increment MINOR
- **Bug fixes**: Increment PATCH

---

## 12. Documentation Structure

```
docs/
├── README.md                   # Quick start
├── getting-started/
│   ├── installation.md
│   ├── quick-start.md
│   └── configuration.md
├── guides/
│   ├── basic-usage.md
│   ├── custom-pipelines.md
│   ├── langgraph-integration.md
│   ├── extending-framework.md
│   └── production-deployment.md
├── api-reference/
│   ├── rag-engine.md
│   ├── providers.md
│   ├── storage.md
│   └── pipeline.md
└── examples/
    ├── basic-rag/
    ├── custom-pipeline/
    ├── langgraph-agent/
    └── multi-domain/
```

---

## 13. Implementation Phases

### Phase 1: Core Foundation (MVP)
- RAGEngine core class
- Gemini provider implementation
- PostgreSQL + pgvector storage
- Basic retrieval pipeline
- Simple document processing
- QuickSetup convenience class

### Phase 2: Modularity & Flexibility
- Pipeline builder system
- Component registry
- Pre-built modules (Basic, Advanced)
- Configuration system
- Custom component support

### Phase 3: LangGraph Integration
- RAGTool implementation
- Integration documentation
- Example LangGraph agent

### Phase 4: Advanced Features
- Advanced pipeline strategies
- Additional providers (OpenAI, Anthropic)
- Additional storage backends (Chroma)
- GraphRAG support

### Phase 5: Production Hardening
- Comprehensive testing (80%+ coverage)
- Error handling & observability
- Performance optimization
- Production deployment guide

---

## 14. Success Criteria

The framework is considered successful when:

1. **✅ Easy to Start**: 5-minute setup with QuickSetup
2. **✅ Flexible**: Swap any component via configuration
3. **✅ Production-Ready**: PostgreSQL + pgvector, error handling, metrics
4. **✅ LangGraph Compatible**: Works as agent tool out-of-box
5. **✅ Domain-Agnostic**: Reusable across multiple projects
6. **✅ Well-Tested**: 80%+ test coverage
7. **✅ Well-Documented**: Examples and guides for all use cases
8. **✅ Extensible**: Easy to add custom components

---

## 15. Open Questions & Future Considerations

### 15.1 Future Enhancements
- Support for more embedding models
- Built-in evaluation metrics (RAGAS, etc.)
- Caching layer for repeated queries
- Multi-modal document support (images, audio)
- Distributed deployment patterns

### 15.2 Performance Optimization
- Connection pooling strategies
- Batch processing for large ingestion
- Query result caching
- Index optimization recommendations

### 15.3 Security Considerations
- API key management best practices
- Role-based access control (RBAC)
- Data privacy and PII handling
- Audit logging

---

## Appendix A: Example Use Cases

### A.1 Simple Knowledge Base

```python
from vibe_rag import QuickSetup

rag = QuickSetup.create(
    provider_api_key=os.getenv("GEMINI_API_KEY"),
    database_url=os.getenv("DATABASE_URL")
)

rag.ingest_file("company_handbook.pdf", collection="hr")
response = rag.query("What is the vacation policy?", collection="hr")
```

### A.2 Multi-Domain Application

```python
from vibe_rag import RAGEngine, RAGConfig

config = RAGConfig.from_yaml("config.yaml")
rag = RAGEngine(config)

# Separate collections for different domains
rag.ingest_file("legal_docs.pdf", collection="legal")
rag.ingest_file("technical_docs.pdf", collection="engineering")

legal_answer = rag.query("Contract terms?", collection="legal")
tech_answer = rag.query("API usage?", collection="engineering")
```

### A.3 LangGraph AI Agent

```python
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from vibe_rag import RAGEngine
from vibe_rag.integrations.langgraph import RAGTool

rag_engine = RAGEngine.from_config("config.yaml")
rag_tool = RAGTool(rag_engine=rag_engine)

agent = create_react_agent(
    ChatGoogleGenerativeAI(model="gemini-1.5-pro"),
    tools=[rag_tool, web_search_tool, calculator_tool]
)

result = agent.invoke({
    "messages": [("user", "What's our Q4 revenue and how does it compare to industry average?")]
})
# Agent uses RAG for internal data, web search for industry data
```

---

## Appendix B: Key Design Decisions

### B.1 Why Layered Architecture?
- **Separation of concerns**: Core logic separate from HTTP layer
- **Flexibility**: Use as library OR service
- **Testability**: Each layer independently testable

### B.2 Why PostgreSQL + pgvector?
- **Production-ready**: Battle-tested database
- **Operational simplicity**: Leverage existing PostgreSQL infrastructure
- **Feature-rich**: JSONB for metadata, full SQL capabilities
- **Cost-effective**: No managed vector DB fees

### B.3 Why Gemini First?
- **Modern API**: Clean, well-documented
- **Cost-effective**: Competitive pricing
- **Performance**: Fast inference
- **Flexibility**: Easy to add other providers later

### B.4 Why Adapter Pattern for Everything?
- **Swappable**: Change providers/storage without code changes
- **Extensible**: Apps can add custom implementations
- **Testable**: Mock components for testing

### B.5 Why "Batteries Included, But Removable"?
- **Quick start**: Pre-built modules for prototyping
- **Production-ready**: Full customization when needed
- **Developer-friendly**: Choose complexity level

---

**End of Design Document**
