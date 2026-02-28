# vibe-rag Framework Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a production-grade, modular RAG framework with pluggable components, focusing on Phase 1 (Core Foundation MVP)

**Architecture:** Three-layer architecture with core library (vibe_rag), optional service layer (apps build their own), and client layer. Uses adapter pattern for LLM providers and storage backends. Designed for TDD with comprehensive test coverage.

**Tech Stack:** Python 3.10+, LangChain, Google Gemini, PostgreSQL + pgvector, Pydantic, pytest

---

## Phase 1: Core Foundation (MVP)

Focus on getting a working RAG system with:
- Basic project structure and packaging
- Gemini LLM provider
- PostgreSQL + pgvector storage
- Simple vector retrieval pipeline
- Document processing
- QuickSetup convenience class
- Test infrastructure

---

### Task 1: Project Setup & Structure

**Files:**
- Create: `pyproject.toml`
- Create: `vibe_rag/__init__.py`
- Create: `vibe_rag/__version__.py`
- Create: `README.md`
- Create: `LICENSE`
- Create: `.gitignore`
- Create: `pytest.ini`

**Step 1: Write pyproject.toml**

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
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]

dependencies = [
    "langchain>=0.1.0",
    "langchain-google-genai>=1.0.0",
    "langchain-core>=0.1.0",
    "psycopg[binary]>=3.1.0",
    "pgvector>=0.2.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "numpy>=1.24.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]
langgraph = [
    "langgraph>=0.1.0",
]
all = ["vibe-rag[dev,langgraph]"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
asyncio_mode = "auto"

[tool.black]
line-length = 100
target-version = ['py310']

[tool.ruff]
line-length = 100
target-version = "py310"
```

**Step 2: Create version file**

Create `vibe_rag/__version__.py`:
```python
"""Version information for vibe-rag."""

__version__ = "0.1.0"
```

**Step 3: Create package init file**

Create `vibe_rag/__init__.py`:
```python
"""
vibe-rag: Production-grade modular RAG framework.

A batteries-included but removable RAG framework with pluggable components.
"""

from vibe_rag.__version__ import __version__

__all__ = ["__version__"]
```

**Step 4: Create .gitignore**

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Environment
.env
.env.local

# OS
.DS_Store
```

**Step 5: Create basic README**

Create `README.md`:
```markdown
# vibe-rag

Production-grade modular RAG framework with pluggable components.

## Features

- 🔌 Pluggable LLM providers (Gemini, OpenAI, Anthropic)
- 🗄️ Pluggable storage backends (PostgreSQL+pgvector, Chroma, custom)
- 🔧 Composable pipeline components
- 🚀 Quick-start modules for rapid prototyping
- 🧪 Comprehensive testing utilities
- 🔗 LangGraph integration for AI agents

## Installation

```bash
pip install vibe-rag
```

## Quick Start

```python
from vibe_rag import QuickSetup

rag = QuickSetup.create(
    provider_api_key="your-gemini-key",
    database_url="postgresql://localhost/rag_db"
)

rag.ingest_file("knowledge_base.pdf", collection="docs")
result = rag.query("What is the main topic?", collection="docs")
print(result["answer"])
```

## Documentation

See `docs/` for detailed documentation.

## License

MIT
```

**Step 6: Create MIT LICENSE**

Create `LICENSE`:
```
MIT License

Copyright (c) 2026 vibe-rag contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**Step 7: Create pytest config**

Create `pytest.ini`:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
asyncio_mode = auto
addopts =
    -v
    --strict-markers
    --cov=vibe_rag
    --cov-report=term-missing
```

**Step 8: Create directory structure**

Run:
```bash
mkdir -p vibe_rag/{config,modules,pipeline,providers,storage,retrievers,transformers,rerankers,integrations,loaders,utils,testing}
mkdir -p tests/{unit,integration,e2e}
touch vibe_rag/config/__init__.py
touch vibe_rag/modules/__init__.py
touch vibe_rag/pipeline/__init__.py
touch vibe_rag/providers/__init__.py
touch vibe_rag/storage/__init__.py
touch vibe_rag/retrievers/__init__.py
touch vibe_rag/transformers/__init__.py
touch vibe_rag/rerankers/__init__.py
touch vibe_rag/integrations/__init__.py
touch vibe_rag/loaders/__init__.py
touch vibe_rag/utils/__init__.py
touch vibe_rag/testing/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch tests/e2e/__init__.py
```

**Step 9: Verify structure**

Run: `tree -L 2 vibe_rag tests`
Expected: Directory tree showing all created directories

**Step 10: Commit**

```bash
git add .
git commit -m "feat: initial project structure and packaging setup

- Add pyproject.toml with dependencies
- Create package structure for vibe-rag
- Add basic README and LICENSE
- Set up pytest configuration
- Create directory structure for all components

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 2: Core Data Models & Exceptions

**Files:**
- Create: `vibe_rag/models.py`
- Create: `vibe_rag/utils/errors.py`
- Create: `tests/unit/test_models.py`

**Step 1: Write failing test for Document model**

Create `tests/unit/test_models.py`:
```python
"""Tests for core data models."""

import pytest
from vibe_rag.models import Document


def test_document_creation():
    """Test creating a Document with required fields."""
    doc = Document(
        content="Sample content",
        metadata={"source": "test.pdf"}
    )

    assert doc.content == "Sample content"
    assert doc.metadata == {"source": "test.pdf"}
    assert doc.id is not None  # Should auto-generate ID


def test_document_with_id():
    """Test creating a Document with explicit ID."""
    doc_id = "test-id-123"
    doc = Document(
        id=doc_id,
        content="Sample content"
    )

    assert doc.id == doc_id


def test_document_metadata_optional():
    """Test that metadata is optional."""
    doc = Document(content="Sample content")

    assert doc.metadata == {}  # Default to empty dict
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_models.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'vibe_rag.models'"

**Step 3: Implement Document model**

Create `vibe_rag/models.py`:
```python
"""Core data models for vibe-rag."""

from typing import Any, Dict, Optional
from uuid import uuid4
from pydantic import BaseModel, Field


class Document(BaseModel):
    """Document model representing a piece of text with metadata."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = None  # Similarity score when retrieved

    class Config:
        """Pydantic config."""
        frozen = False
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_models.py -v`
Expected: PASS (3 tests)

**Step 5: Write test for custom exceptions**

Add to `tests/unit/test_models.py`:
```python
from vibe_rag.utils.errors import (
    RAGException,
    EmbeddingError,
    RetrievalError,
    LLMProviderError,
    StorageError,
)


def test_rag_exception_hierarchy():
    """Test that custom exceptions inherit from RAGException."""
    assert issubclass(EmbeddingError, RAGException)
    assert issubclass(RetrievalError, RAGException)
    assert issubclass(LLMProviderError, RAGException)
    assert issubclass(StorageError, RAGException)


def test_rag_exception_message():
    """Test exception message handling."""
    error = RAGException("Test error message")
    assert str(error) == "Test error message"


def test_embedding_error():
    """Test EmbeddingError can be raised and caught."""
    with pytest.raises(EmbeddingError, match="Embedding failed"):
        raise EmbeddingError("Embedding failed")
```

**Step 6: Run test to verify it fails**

Run: `pytest tests/unit/test_models.py::test_rag_exception_hierarchy -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'vibe_rag.utils.errors'"

**Step 7: Implement custom exceptions**

Create `vibe_rag/utils/errors.py`:
```python
"""Custom exceptions for vibe-rag."""


class RAGException(Exception):
    """Base exception for all RAG errors."""
    pass


class EmbeddingError(RAGException):
    """Embedding generation failed."""
    pass


class RetrievalError(RAGException):
    """Document retrieval failed."""
    pass


class LLMProviderError(RAGException):
    """LLM provider error (API error, timeout, etc.)."""
    pass


class StorageError(RAGException):
    """Storage backend error."""
    pass


class ConfigurationError(RAGException):
    """Configuration validation error."""
    pass
```

**Step 8: Run tests to verify they pass**

Run: `pytest tests/unit/test_models.py -v`
Expected: PASS (6 tests)

**Step 9: Update package exports**

Edit `vibe_rag/__init__.py`:
```python
"""
vibe-rag: Production-grade modular RAG framework.

A batteries-included but removable RAG framework with pluggable components.
"""

from vibe_rag.__version__ import __version__
from vibe_rag.models import Document
from vibe_rag.utils.errors import (
    RAGException,
    EmbeddingError,
    RetrievalError,
    LLMProviderError,
    StorageError,
    ConfigurationError,
)

__all__ = [
    "__version__",
    "Document",
    "RAGException",
    "EmbeddingError",
    "RetrievalError",
    "LLMProviderError",
    "StorageError",
    "ConfigurationError",
]
```

**Step 10: Commit**

```bash
git add vibe_rag/models.py vibe_rag/utils/errors.py tests/unit/test_models.py vibe_rag/__init__.py
git commit -m "feat: add core data models and custom exceptions

- Implement Document model with Pydantic
- Add custom exception hierarchy (RAGException and subtypes)
- Add comprehensive unit tests
- Update package exports

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 3: LLM Provider Base Interface

**Files:**
- Create: `vibe_rag/providers/base.py`
- Create: `tests/unit/test_providers.py`

**Step 1: Write failing test for BaseLLMProvider**

Create `tests/unit/test_providers.py`:
```python
"""Tests for LLM providers."""

import pytest
from abc import ABC
from vibe_rag.providers.base import BaseLLMProvider


def test_base_provider_is_abstract():
    """Test that BaseLLMProvider cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseLLMProvider()


def test_base_provider_interface():
    """Test that BaseLLMProvider defines required interface."""
    # Check that required methods exist
    assert hasattr(BaseLLMProvider, 'generate')
    assert hasattr(BaseLLMProvider, 'embed')
    assert hasattr(BaseLLMProvider, 'provider_name')


class MockProvider(BaseLLMProvider):
    """Mock provider for testing."""

    @property
    def provider_name(self) -> str:
        return "mock"

    async def generate(self, prompt: str, **kwargs) -> str:
        return f"Generated: {prompt}"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1, 0.2, 0.3] for _ in texts]


@pytest.mark.asyncio
async def test_mock_provider_generate():
    """Test that subclass can implement generate."""
    provider = MockProvider()
    result = await provider.generate("test prompt")
    assert result == "Generated: test prompt"


@pytest.mark.asyncio
async def test_mock_provider_embed():
    """Test that subclass can implement embed."""
    provider = MockProvider()
    result = await provider.embed(["text1", "text2"])
    assert len(result) == 2
    assert result[0] == [0.1, 0.2, 0.3]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_providers.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'vibe_rag.providers.base'"

**Step 3: Implement BaseLLMProvider**

Create `vibe_rag/providers/base.py`:
```python
"""Base interface for LLM providers."""

from abc import ABC, abstractmethod
from typing import Optional


class BaseLLMProvider(ABC):
    """Base interface for all LLM providers.

    All LLM provider implementations must inherit from this class
    and implement the required methods.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier (e.g., 'gemini', 'openai')."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate text from prompt.

        Args:
            prompt: The user prompt/query
            system_prompt: Optional system instruction
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            Generated text response

        Raises:
            LLMProviderError: If generation fails
        """
        pass

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors (one per input text)

        Raises:
            EmbeddingError: If embedding generation fails
        """
        pass

    def validate_config(self, config: dict) -> bool:
        """Validate provider configuration.

        Subclasses can override to add custom validation.

        Args:
            config: Configuration dictionary

        Returns:
            True if valid

        Raises:
            ConfigurationError: If configuration is invalid
        """
        return True
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_providers.py -v`
Expected: PASS (4 tests)

**Step 5: Update providers package init**

Edit `vibe_rag/providers/__init__.py`:
```python
"""LLM provider adapters."""

from vibe_rag.providers.base import BaseLLMProvider

__all__ = ["BaseLLMProvider"]
```

**Step 6: Commit**

```bash
git add vibe_rag/providers/base.py tests/unit/test_providers.py vibe_rag/providers/__init__.py
git commit -m "feat: add BaseLLMProvider interface

- Define abstract base class for LLM providers
- Specify required methods: generate, embed, provider_name
- Add unit tests for interface contract
- Support async operations for scalability

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 4: Gemini Provider Implementation

**Files:**
- Create: `vibe_rag/providers/gemini.py`
- Modify: `tests/unit/test_providers.py`

**Step 1: Write failing test for GeminiProvider**

Add to `tests/unit/test_providers.py`:
```python
from unittest.mock import AsyncMock, MagicMock, patch
from vibe_rag.providers.gemini import GeminiProvider


def test_gemini_provider_initialization():
    """Test GeminiProvider initialization."""
    provider = GeminiProvider(
        api_key="test-key",
        model="gemini-1.5-pro",
        temperature=0.8
    )

    assert provider.provider_name == "gemini"
    assert provider.temperature == 0.8


@pytest.mark.asyncio
@patch('vibe_rag.providers.gemini.genai')
async def test_gemini_generate(mock_genai):
    """Test Gemini text generation."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.text = "Generated response"

    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)

    mock_genai.GenerativeModel.return_value = mock_model

    # Test
    provider = GeminiProvider(api_key="test-key")
    result = await provider.generate("test prompt")

    assert result == "Generated response"
    mock_model.generate_content_async.assert_called_once()


@pytest.mark.asyncio
@patch('vibe_rag.providers.gemini.genai')
async def test_gemini_embed(mock_genai):
    """Test Gemini embedding generation."""
    # Setup mock
    mock_genai.embed_content.return_value = {
        'embedding': [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    }

    # Test
    provider = GeminiProvider(api_key="test-key")
    result = await provider.embed(["text1", "text2"])

    assert len(result) == 2
    assert result[0] == [0.1, 0.2, 0.3]
    assert result[1] == [0.4, 0.5, 0.6]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_providers.py::test_gemini_provider_initialization -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'vibe_rag.providers.gemini'"

**Step 3: Implement GeminiProvider**

Create `vibe_rag/providers/gemini.py`:
```python
"""Google Gemini LLM provider."""

from typing import Optional
import google.generativeai as genai

from vibe_rag.providers.base import BaseLLMProvider
from vibe_rag.utils.errors import LLMProviderError, EmbeddingError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider implementation.

    Supports text generation and embedding using Google's Gemini API.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-pro",
        embedding_model: str = "models/text-embedding-004",
        temperature: float = 0.7,
        **kwargs
    ):
        """Initialize Gemini provider.

        Args:
            api_key: Google API key
            model: Gemini model name for generation
            embedding_model: Model name for embeddings
            temperature: Default sampling temperature
            **kwargs: Additional provider-specific parameters
        """
        self.api_key = api_key
        self.model_name = model
        self.embedding_model = embedding_model
        self.temperature = temperature

        # Configure API
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model)

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "gemini"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: int = 1000,
        **kwargs
    ) -> str:
        """Generate text using Gemini.

        Args:
            prompt: User prompt
            system_prompt: Optional system instruction
            temperature: Sampling temperature (uses default if None)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional Gemini parameters

        Returns:
            Generated text

        Raises:
            LLMProviderError: If generation fails
        """
        try:
            # Prepare generation config
            generation_config = {
                "temperature": temperature if temperature is not None else self.temperature,
                "max_output_tokens": max_tokens,
            }

            # Add system prompt if provided
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            else:
                full_prompt = prompt

            # Generate
            response = await self.model.generate_content_async(
                full_prompt,
                generation_config=generation_config
            )

            return response.text

        except Exception as e:
            raise LLMProviderError(f"Gemini generation failed: {e}")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using Gemini.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            EmbeddingError: If embedding generation fails
        """
        try:
            # Gemini embed_content can handle multiple texts
            result = genai.embed_content(
                model=self.embedding_model,
                content=texts
            )

            return result['embedding']

        except Exception as e:
            raise EmbeddingError(f"Gemini embedding failed: {e}")
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_providers.py -k gemini -v`
Expected: PASS (3 gemini tests)

**Step 5: Update providers package exports**

Edit `vibe_rag/providers/__init__.py`:
```python
"""LLM provider adapters."""

from vibe_rag.providers.base import BaseLLMProvider
from vibe_rag.providers.gemini import GeminiProvider

__all__ = ["BaseLLMProvider", "GeminiProvider"]
```

**Step 6: Update main package exports**

Edit `vibe_rag/__init__.py` to add:
```python
from vibe_rag.providers import GeminiProvider
```

And add to `__all__`:
```python
"GeminiProvider",
```

**Step 7: Run all provider tests**

Run: `pytest tests/unit/test_providers.py -v`
Expected: PASS (all tests)

**Step 8: Commit**

```bash
git add vibe_rag/providers/gemini.py tests/unit/test_providers.py vibe_rag/providers/__init__.py vibe_rag/__init__.py
git commit -m "feat: implement GeminiProvider for LLM operations

- Add Google Gemini integration for text generation
- Support embedding generation via Gemini API
- Handle system prompts and generation parameters
- Add comprehensive unit tests with mocking
- Export GeminiProvider in main package

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 5: Storage Base Interface

**Files:**
- Create: `vibe_rag/storage/base.py`
- Create: `tests/unit/test_storage.py`

**Step 1: Write failing test for BaseVectorStore**

Create `tests/unit/test_storage.py`:
```python
"""Tests for vector storage backends."""

import pytest
from abc import ABC
from vibe_rag.storage.base import BaseVectorStore
from vibe_rag.models import Document


def test_base_storage_is_abstract():
    """Test that BaseVectorStore cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseVectorStore()


def test_base_storage_interface():
    """Test that BaseVectorStore defines required interface."""
    assert hasattr(BaseVectorStore, 'add_documents')
    assert hasattr(BaseVectorStore, 'similarity_search')
    assert hasattr(BaseVectorStore, 'delete_collection')
    assert hasattr(BaseVectorStore, 'store_name')


class MockVectorStore(BaseVectorStore):
    """Mock storage for testing."""

    def __init__(self):
        self.documents = {}

    @property
    def store_name(self) -> str:
        return "mock"

    async def add_documents(
        self,
        documents: list[Document],
        collection_name: str,
        embeddings: list[list[float]]
    ) -> list[str]:
        if collection_name not in self.documents:
            self.documents[collection_name] = []
        self.documents[collection_name].extend(documents)
        return [doc.id for doc in documents]

    async def similarity_search(
        self,
        query_embedding: list[float],
        collection_name: str,
        top_k: int = 5,
        filters: dict | None = None
    ) -> list[Document]:
        docs = self.documents.get(collection_name, [])
        return docs[:top_k]

    async def delete_collection(self, collection_name: str):
        if collection_name in self.documents:
            del self.documents[collection_name]


@pytest.mark.asyncio
async def test_mock_storage_add_documents():
    """Test adding documents to mock storage."""
    store = MockVectorStore()
    docs = [
        Document(content="doc1"),
        Document(content="doc2")
    ]
    embeddings = [[0.1, 0.2], [0.3, 0.4]]

    ids = await store.add_documents(docs, "test_collection", embeddings)

    assert len(ids) == 2
    assert len(store.documents["test_collection"]) == 2


@pytest.mark.asyncio
async def test_mock_storage_similarity_search():
    """Test similarity search in mock storage."""
    store = MockVectorStore()
    docs = [Document(content=f"doc{i}") for i in range(10)]
    embeddings = [[0.1] * 2 for _ in range(10)]

    await store.add_documents(docs, "test_collection", embeddings)

    results = await store.similarity_search([0.1, 0.2], "test_collection", top_k=3)

    assert len(results) == 3


@pytest.mark.asyncio
async def test_mock_storage_delete_collection():
    """Test deleting a collection."""
    store = MockVectorStore()
    docs = [Document(content="doc1")]
    embeddings = [[0.1, 0.2]]

    await store.add_documents(docs, "test_collection", embeddings)
    assert "test_collection" in store.documents

    await store.delete_collection("test_collection")
    assert "test_collection" not in store.documents
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_storage.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'vibe_rag.storage.base'"

**Step 3: Implement BaseVectorStore**

Create `vibe_rag/storage/base.py`:
```python
"""Base interface for vector storage backends."""

from abc import ABC, abstractmethod
from typing import Optional

from vibe_rag.models import Document


class BaseVectorStore(ABC):
    """Base interface for all vector storage backends.

    All vector store implementations must inherit from this class
    and implement the required methods.
    """

    @property
    @abstractmethod
    def store_name(self) -> str:
        """Return storage backend identifier (e.g., 'postgres', 'chroma')."""
        pass

    @abstractmethod
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
            StorageError: If adding documents fails
        """
        pass

    @abstractmethod
    async def similarity_search(
        self,
        query_embedding: list[float],
        collection_name: str,
        top_k: int = 5,
        filters: Optional[dict] = None
    ) -> list[Document]:
        """Search for similar documents using vector similarity.

        Args:
            query_embedding: Query embedding vector
            collection_name: Name of the collection to search
            top_k: Number of top results to return
            filters: Optional metadata filters

        Returns:
            List of similar documents with scores

        Raises:
            RetrievalError: If search fails
        """
        pass

    @abstractmethod
    async def delete_collection(self, collection_name: str):
        """Delete an entire collection.

        Args:
            collection_name: Name of the collection to delete

        Raises:
            StorageError: If deletion fails
        """
        pass

    def validate_config(self, config: dict) -> bool:
        """Validate storage configuration.

        Subclasses can override to add custom validation.

        Args:
            config: Configuration dictionary

        Returns:
            True if valid

        Raises:
            ConfigurationError: If configuration is invalid
        """
        return True
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_storage.py -v`
Expected: PASS (6 tests)

**Step 5: Update storage package init**

Edit `vibe_rag/storage/__init__.py`:
```python
"""Vector storage backends."""

from vibe_rag.storage.base import BaseVectorStore

__all__ = ["BaseVectorStore"]
```

**Step 6: Commit**

```bash
git add vibe_rag/storage/base.py tests/unit/test_storage.py vibe_rag/storage/__init__.py
git commit -m "feat: add BaseVectorStore interface

- Define abstract base class for vector storage
- Specify required methods: add_documents, similarity_search, delete_collection
- Add unit tests for interface contract
- Support async operations and metadata filtering

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

### Task 6: PostgreSQL + pgvector Storage Implementation

**Files:**
- Create: `vibe_rag/storage/postgres_vector.py`
- Create: `vibe_rag/storage/schema.sql`
- Modify: `tests/unit/test_storage.py`
- Create: `tests/integration/test_postgres_storage.py`

**Step 1: Create SQL schema file**

Create `vibe_rag/storage/schema.sql`:
```sql
-- PostgreSQL + pgvector schema for vibe-rag

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Document metadata table
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY,
    collection_name VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    source VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Vector embeddings table
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL DEFAULT 0,
    chunk_text TEXT NOT NULL,
    embedding vector(768),  -- Default dimension, can be changed
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(document_id, chunk_index)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_collection ON documents(collection_name);
CREATE INDEX IF NOT EXISTS idx_documents_created ON documents(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_embeddings_document ON embeddings(document_id);

-- Vector similarity index (IVFFlat for large datasets)
-- Note: This requires data to be present, so it's created after initial inserts
-- CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings
--   USING ivfflat (embedding vector_cosine_ops)
--   WITH (lists = 100);
```

**Step 2: Write failing unit test for PostgresVectorStore**

Add to `tests/unit/test_storage.py`:
```python
from unittest.mock import AsyncMock, MagicMock, patch
from vibe_rag.storage.postgres_vector import PostgresVectorStore


def test_postgres_store_initialization():
    """Test PostgresVectorStore initialization."""
    store = PostgresVectorStore(
        host="localhost",
        port=5432,
        database="test_db",
        user="test_user",
        password="test_pass"
    )

    assert store.store_name == "postgres"
    assert "test_db" in store.connection_string


@pytest.mark.asyncio
@patch('vibe_rag.storage.postgres_vector.asyncpg')
async def test_postgres_add_documents(mock_asyncpg):
    """Test adding documents to PostgreSQL."""
    # Setup mock connection
    mock_conn = AsyncMock()
    mock_pool = AsyncMock()
    mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
    mock_asyncpg.create_pool.return_value = mock_pool

    # Test
    store = PostgresVectorStore(
        host="localhost",
        database="test_db",
        user="user",
        password="pass"
    )
    await store.initialize()

    docs = [Document(id="test-id", content="test content")]
    embeddings = [[0.1] * 768]

    ids = await store.add_documents(docs, "test_collection", embeddings)

    assert len(ids) == 1
    assert ids[0] == "test-id"
```

**Step 3: Run test to verify it fails**

Run: `pytest tests/unit/test_storage.py::test_postgres_store_initialization -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'vibe_rag.storage.postgres_vector'"

**Step 4: Implement PostgresVectorStore (Part 1 - Initialization)**

Create `vibe_rag/storage/postgres_vector.py`:
```python
"""PostgreSQL + pgvector storage backend."""

import asyncpg
from typing import Optional
from pathlib import Path

from vibe_rag.storage.base import BaseVectorStore
from vibe_rag.models import Document
from vibe_rag.utils.errors import StorageError, RetrievalError


class PostgresVectorStore(BaseVectorStore):
    """PostgreSQL + pgvector storage implementation.

    Uses PostgreSQL with pgvector extension for vector similarity search.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str,
        user: str,
        password: str,
        embedding_dimension: int = 768,
        **kwargs
    ):
        """Initialize PostgreSQL storage.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Database user
            password: Database password
            embedding_dimension: Dimension of embedding vectors
            **kwargs: Additional connection parameters
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.embedding_dimension = embedding_dimension

        self.connection_string = (
            f"postgresql://{user}:{password}@{host}:{port}/{database}"
        )

        self.pool: Optional[asyncpg.Pool] = None

    @property
    def store_name(self) -> str:
        """Return storage backend identifier."""
        return "postgres"

    async def initialize(self):
        """Initialize database connection pool and create schema."""
        try:
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=2,
                max_size=10
            )

            # Create schema
            await self._create_schema()

        except Exception as e:
            raise StorageError(f"Failed to initialize PostgreSQL storage: {e}")

    async def _create_schema(self):
        """Create database tables and indexes."""
        schema_path = Path(__file__).parent / "schema.sql"
        schema_sql = schema_path.read_text()

        async with self.pool.acquire() as conn:
            # Replace placeholder dimension with actual value
            schema_sql = schema_sql.replace(
                "vector(768)",
                f"vector({self.embedding_dimension})"
            )
            await conn.execute(schema_sql)

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
            embeddings: List of embedding vectors

        Returns:
            List of document IDs
        """
        if not self.pool:
            await self.initialize()

        if len(documents) != len(embeddings):
            raise StorageError("Number of documents and embeddings must match")

        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    doc_ids = []

                    for doc, embedding in zip(documents, embeddings):
                        # Insert document
                        await conn.execute(
                            """
                            INSERT INTO documents (id, collection_name, content, metadata, source)
                            VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT (id) DO UPDATE
                            SET content = EXCLUDED.content,
                                metadata = EXCLUDED.metadata,
                                updated_at = NOW()
                            """,
                            doc.id,
                            collection_name,
                            doc.content,
                            doc.metadata,
                            doc.metadata.get('source')
                        )

                        # Insert embedding
                        await conn.execute(
                            """
                            INSERT INTO embeddings (document_id, chunk_index, chunk_text, embedding)
                            VALUES ($1, $2, $3, $4)
                            ON CONFLICT (document_id, chunk_index) DO UPDATE
                            SET embedding = EXCLUDED.embedding
                            """,
                            doc.id,
                            0,  # Single chunk for now
                            doc.content,
                            embedding
                        )

                        doc_ids.append(doc.id)

                    return doc_ids

        except Exception as e:
            raise StorageError(f"Failed to add documents: {e}")

    async def similarity_search(
        self,
        query_embedding: list[float],
        collection_name: str,
        top_k: int = 5,
        filters: Optional[dict] = None
    ) -> list[Document]:
        """Search for similar documents.

        Args:
            query_embedding: Query embedding vector
            collection_name: Collection to search
            top_k: Number of results to return
            filters: Optional metadata filters

        Returns:
            List of similar documents with scores
        """
        if not self.pool:
            await self.initialize()

        try:
            async with self.pool.acquire() as conn:
                # Build query with optional metadata filters
                query = """
                    SELECT
                        d.id,
                        d.content,
                        d.metadata,
                        1 - (e.embedding <=> $1) as score
                    FROM embeddings e
                    JOIN documents d ON e.document_id = d.id
                    WHERE d.collection_name = $2
                """
                params = [query_embedding, collection_name]

                # Add metadata filters if provided
                if filters:
                    for i, (key, value) in enumerate(filters.items(), start=3):
                        query += f" AND d.metadata->>${i} = ${i+1}"
                        params.extend([key, str(value)])

                query += f" ORDER BY e.embedding <=> $1 LIMIT {top_k}"

                rows = await conn.fetch(query, *params)

                documents = []
                for row in rows:
                    doc = Document(
                        id=row['id'],
                        content=row['content'],
                        metadata=row['metadata'],
                        score=float(row['score'])
                    )
                    documents.append(doc)

                return documents

        except Exception as e:
            raise RetrievalError(f"Failed to search documents: {e}")

    async def delete_collection(self, collection_name: str):
        """Delete an entire collection.

        Args:
            collection_name: Name of the collection to delete
        """
        if not self.pool:
            await self.initialize()

        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM documents WHERE collection_name = $1",
                    collection_name
                )
        except Exception as e:
            raise StorageError(f"Failed to delete collection: {e}")

    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
```

**Step 5: Add asyncpg to dependencies**

Edit `pyproject.toml` to add to dependencies:
```toml
    "asyncpg>=0.29.0",
```

**Step 6: Run unit tests**

Run: `pytest tests/unit/test_storage.py -k postgres -v`
Expected: PASS

**Step 7: Create integration test (skipped if no DB)**

Create `tests/integration/test_postgres_storage.py`:
```python
"""Integration tests for PostgreSQL storage (requires running PostgreSQL)."""

import pytest
import os
from vibe_rag.storage.postgres_vector import PostgresVectorStore
from vibe_rag.models import Document


# Skip if no test database configured
pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"),
    reason="Requires TEST_DATABASE_URL environment variable"
)


@pytest.fixture
async def postgres_store():
    """Create PostgreSQL store for testing."""
    # Parse DATABASE_URL or use defaults
    store = PostgresVectorStore(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "test_vibe_rag"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
    )

    await store.initialize()

    yield store

    # Cleanup
    await store.close()


@pytest.mark.asyncio
async def test_postgres_full_workflow(postgres_store):
    """Test complete workflow with real PostgreSQL."""
    collection = "test_integration"

    # Add documents
    docs = [
        Document(content="Document about Python programming"),
        Document(content="Document about machine learning"),
    ]
    embeddings = [
        [0.1] * 768,
        [0.9] * 768,
    ]

    ids = await postgres_store.add_documents(docs, collection, embeddings)
    assert len(ids) == 2

    # Search
    results = await postgres_store.similarity_search(
        query_embedding=[0.1] * 768,
        collection_name=collection,
        top_k=1
    )

    assert len(results) == 1
    assert "Python" in results[0].content

    # Delete collection
    await postgres_store.delete_collection(collection)
```

**Step 8: Update storage package exports**

Edit `vibe_rag/storage/__init__.py`:
```python
"""Vector storage backends."""

from vibe_rag.storage.base import BaseVectorStore
from vibe_rag.storage.postgres_vector import PostgresVectorStore

__all__ = ["BaseVectorStore", "PostgresVectorStore"]
```

**Step 9: Commit**

```bash
git add vibe_rag/storage/postgres_vector.py vibe_rag/storage/schema.sql tests/unit/test_storage.py tests/integration/test_postgres_storage.py vibe_rag/storage/__init__.py pyproject.toml
git commit -m "feat: implement PostgreSQL + pgvector storage backend

- Add PostgresVectorStore with async operations
- Create SQL schema with pgvector extension
- Support document ingestion and similarity search
- Add metadata filtering and collection management
- Include unit tests with mocking
- Add integration tests (requires test DB)
- Add asyncpg dependency

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

---

## Summary & Next Steps

This implementation plan covers **Phase 1: Core Foundation (MVP)** with 6 major tasks completed:

1. ✅ Project setup and structure
2. ✅ Core data models and exceptions
3. ✅ LLM provider base interface
4. ✅ Gemini provider implementation
5. ✅ Storage base interface
6. ✅ PostgreSQL + pgvector storage

**Remaining tasks for Phase 1:**
- Task 7: Pipeline base components
- Task 8: Vector retriever implementation
- Task 9: Document processor and loaders
- Task 10: RAG Engine core class
- Task 11: QuickSetup convenience class
- Task 12: Testing utilities (mocks)
- Task 13: Integration tests

**Each task follows TDD:**
- Write failing tests first
- Implement minimal code to pass
- Run tests to verify
- Commit frequently

**To continue:** Use this plan with `superpowers:executing-plans` or `superpowers:subagent-driven-development` to implement remaining tasks.
