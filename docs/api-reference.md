# vibe-rag API Reference

Complete reference for all public classes and functions exported by `vibe_rag`.

---

## Quick Navigation

- [RAGEngine](#ragengine) — main orchestrator
- [QuickSetup](#quicksetup) — one-liner initialization
- [BasicRAGModule](#basicragmodule) — pre-configured module wrapper
- [Configuration](#configuration) — RAGConfig, LLMConfig, StorageConfig, PipelineConfig, ChunkingConfig
- [Document](#document) — core data model
- [Loaders](#loaders) — TextLoader, MarkdownLoader, PDFLoader, custom loaders
- [Errors](#errors) — exception hierarchy
- [Observability](#observability) — RAGMetrics, MetricsTracker

---

## RAGEngine

```python
from vibe_rag import RAGEngine
```

The central interface for all RAG operations. Orchestrates document ingestion,
retrieval, and generation. Supports use as an async context manager.

### Constructor

```python
RAGEngine(
    config: RAGConfig,
    provider: Optional[BaseLLMProvider] = None,
    storage: Optional[BaseVectorStore] = None,
    enable_metrics: bool = True,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `config` | `RAGConfig` | required | Complete RAG configuration |
| `provider` | `BaseLLMProvider` or `None` | `None` | Custom LLM provider — overrides `config.llm` when provided |
| `storage` | `BaseVectorStore` or `None` | `None` | Custom storage backend — overrides `config.storage` when provided |
| `enable_metrics` | `bool` | `True` | Enable metrics tracking via `MetricsTracker` |

Raises `ConfigurationError` if configuration is invalid (e.g. dimension mismatch).

### Usage pattern

```python
config = RAGConfig(
    llm=LLMConfig(api_key="your-key"),
    storage=StorageConfig(connection_string="postgresql://..."),
)

async with RAGEngine(config) as engine:
    await engine.ingest("document.txt")
    result = await engine.query("What is this about?")
    print(result["answer"])
```

### Methods

#### `initialize() -> None`

Initialize all components. Must be called before using the engine when **not** using
the async context manager.

```python
engine = RAGEngine(config)
await engine.initialize()
# ... use engine ...
await engine.close()
```

Raises `StorageError` if the storage backend fails to initialize.

#### `close() -> None`

Close all components and release resources (database connections, etc.).

#### `ingest(source, metadata=None, loader=None) -> list[str]`

Ingest a document through the full pipeline: load → chunk → embed → store.

```python
doc_ids = await engine.ingest(
    "report.pdf",
    metadata={"department": "engineering", "year": 2026},
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `source` | `str` | required | File path to document |
| `metadata` | `dict[str, Any]` or `None` | `None` | Metadata attached to all chunks |
| `loader` | `BaseLoader` or `None` | `None` | Custom loader; auto-detected from extension if `None` |

Auto-detected extensions: `.txt` (TextLoader), `.md` (MarkdownLoader), `.pdf` (PDFLoader).

Returns a `list[str]` of document IDs for all stored chunks.

Raises:
- `DocumentProcessingError` — file loading or chunking failed
- `EmbeddingError` — embedding generation failed
- `StorageError` — database storage failed
- `ConfigurationError` — engine not yet initialized

#### `query(query, generation_kwargs=None) -> dict[str, Any]`

Execute a RAG query: retrieve relevant documents then generate an answer.

```python
result = await engine.query(
    "What is the refund policy?",
    generation_kwargs={"temperature": 0.3, "max_tokens": 500},
)

print(result["answer"])
for source in result["sources"]:
    print(source["score"], source["metadata"])
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | required | User question |
| `generation_kwargs` | `dict[str, Any]` or `None` | `None` | LLM generation parameters, merged with `config.llm.generation_kwargs` |

Returns a `dict` with:

| Key | Type | Description |
|-----|------|-------------|
| `answer` | `str` | Generated answer |
| `sources` | `list[dict]` | Retrieved documents, each with `content`, `score`, and `metadata` |
| `metadata` | `dict` | Query metadata: `query_id`, `retrieval_time_ms`, `generation_time_ms`, `total_time_ms`, `documents_retrieved`, `pipeline_metadata` |

Raises:
- `RetrievalError` — document retrieval failed
- `LLMProviderError` — LLM generation failed
- `ConfigurationError` — engine not yet initialized

#### `register_loader(extension, loader) -> None`

Register a custom loader for a file extension.

```python
from vibe_rag.loaders.base import BaseLoader

engine.register_loader(".docx", MyDocxLoader())
await engine.ingest("report.docx")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `extension` | `str` | File extension including dot, e.g. `".docx"` |
| `loader` | `BaseLoader` | Loader instance |

#### `get_metrics() -> list[RAGMetrics]`

Return all recorded `RAGMetrics` objects, one per `query()` call.

Raises `ConfigurationError` if metrics tracking is disabled (`enable_metrics=False`).

#### `get_stats() -> dict[str, Any]`

Return aggregate statistics across all queries.

```python
stats = engine.get_stats()
# {
#   "total_queries": 42,
#   "avg_total_time_ms": 1243.5,
#   "avg_retrieval_time_ms": 150.2,
#   "avg_generation_time_ms": 1093.3,
#   "avg_documents_retrieved": 4.8,
#   "total_input_tokens": 18500,
#   "total_output_tokens": 4200,
# }
```

Raises `ConfigurationError` if metrics tracking is disabled.

---

## QuickSetup

```python
from vibe_rag import QuickSetup
```

One-liner setup for `RAGEngine` with sensible defaults. Uses Gemini as the LLM
provider and PostgreSQL+pgvector for storage.

### `QuickSetup.create()`

```python
@staticmethod
def create(
    provider_api_key: str,
    database_url: str,
    collection_name: str = "documents",
    top_k: int = 5,
) -> RAGEngine
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provider_api_key` | `str` | required | Gemini API key |
| `database_url` | `str` | required | PostgreSQL connection string |
| `collection_name` | `str` | `"documents"` | Vector store collection name |
| `top_k` | `int` | `5` | Documents to retrieve per query |

Returns a configured `RAGEngine` (not yet initialized — use as async context manager).

Default configuration applied:
- Model: `gemini-2.0-flash`
- Embedding model: `models/gemini-embedding-001` (768 dimensions)
- Chunking: `recursive` strategy, chunk_size=512, chunk_overlap=50
- Storage: PostgreSQL+pgvector, vector_dimension=768

```python
async with QuickSetup.create(
    provider_api_key=os.environ["GOOGLE_API_KEY"],
    database_url="postgresql://user:pass@localhost/mydb",
) as rag:
    await rag.ingest("knowledge_base.txt")
    result = await rag.query("What does the document say about X?")
    print(result["answer"])
```

---

## BasicRAGModule

```python
from vibe_rag import BasicRAGModule
```

A thin, named wrapper around `QuickSetup.create()`. Provides explicit, readable
parameter names and supports the async context manager protocol.

### Constructor

```python
BasicRAGModule(
    api_key: str,
    db_url: str,
    collection_name: str = "documents",
    top_k: int = 5,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str` | required | Gemini API key |
| `db_url` | `str` | required | PostgreSQL connection string |
| `collection_name` | `str` | `"documents"` | Vector store collection name |
| `top_k` | `int` | `5` | Documents to retrieve per query |

### Methods

`BasicRAGModule` delegates directly to `RAGEngine`. All methods have identical
signatures and return types to `RAGEngine`.

| Method | Description |
|--------|-------------|
| `ingest(source, metadata=None, loader=None) -> list[str]` | Ingest a document |
| `query(query, generation_kwargs=None) -> dict[str, Any]` | Execute a RAG query |

### Usage

```python
async with BasicRAGModule(
    api_key=os.environ["GOOGLE_API_KEY"],
    db_url="postgresql://user:pass@localhost/mydb",
    collection_name="hr_policies",
) as rag:
    await rag.ingest("hr_handbook.pdf")
    result = await rag.query("What is the vacation policy?")
    print(result["answer"])
```

---

## Configuration

```python
from vibe_rag import RAGConfig, LLMConfig, StorageConfig, PipelineConfig, ChunkingConfig
```

All configuration models are Pydantic `BaseModel` subclasses with `frozen=False`.

### RAGConfig

Top-level configuration object passed to `RAGEngine`.

```python
class RAGConfig(BaseModel):
    llm: LLMConfig
    storage: StorageConfig
    pipeline: PipelineConfig = PipelineConfig()   # default: top_k=5
    chunking: ChunkingConfig = ChunkingConfig()   # default: recursive, 512, 50
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `llm` | `LLMConfig` | required | LLM provider configuration |
| `storage` | `StorageConfig` | required | Storage backend configuration |
| `pipeline` | `PipelineConfig` | `PipelineConfig()` | Retrieval pipeline configuration |
| `chunking` | `ChunkingConfig` | `ChunkingConfig()` | Document chunking configuration |

`RAGConfig.validate_dimensions()` is called automatically by `RAGEngine.__init__()`.
It raises `ValueError` (wrapped as `ConfigurationError`) when `storage.vector_dimension`
does not match the embedding model's output dimension.

### LLMConfig

```python
class LLMConfig(BaseModel):
    provider: Literal["gemini"] = "gemini"
    api_key: Optional[str] = None
    model_name: str = "gemini-2.0-flash"
    embedding_model: str = "models/gemini-embedding-001"
    generation_kwargs: dict[str, Any] = {}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `provider` | `"gemini"` | `"gemini"` | LLM provider type (only `"gemini"` currently supported) |
| `api_key` | `str` or `None` | `None` | API key for the provider |
| `model_name` | `str` | `"gemini-2.0-flash"` | Generation model name |
| `embedding_model` | `str` | `"models/gemini-embedding-001"` | Embedding model name |
| `generation_kwargs` | `dict[str, Any]` | `{}` | Default kwargs passed to every `generate()` call |

### StorageConfig

```python
class StorageConfig(BaseModel):
    backend: Literal["postgres"] = "postgres"
    collection_name: str = "documents"
    connection_string: str                         # required
    vector_dimension: int = 768
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `backend` | `"postgres"` | `"postgres"` | Storage backend (only `"postgres"` currently supported) |
| `collection_name` | `str` | `"documents"` | PostgreSQL table name; must match `^[a-zA-Z_][a-zA-Z0-9_]*$` |
| `connection_string` | `str` | required | PostgreSQL connection string, e.g. `"postgresql://user:pass@host/db"` |
| `vector_dimension` | `int` | `768` | Dimension of stored embedding vectors |

Raises `ValueError` if `collection_name` is not a valid PostgreSQL identifier.

### PipelineConfig

```python
class PipelineConfig(BaseModel):
    top_k: int = 5                           # range: 1–100
    filter_metadata: Optional[dict[str, Any]] = None
    reranking_enabled: bool = False
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `top_k` | `int` | `5` | Number of documents to retrieve per query (1–100) |
| `filter_metadata` | `dict[str, Any]` or `None` | `None` | Exact key-value metadata filters applied at retrieval |
| `reranking_enabled` | `bool` | `False` | Enable reranking (reserved for future use) |

#### Metadata filtering example

```python
PipelineConfig(
    top_k=5,
    filter_metadata={"department": "engineering", "year": 2026},
)
```

Only documents whose metadata contains all specified key-value pairs are returned.

### ChunkingConfig

```python
class ChunkingConfig(BaseModel):
    strategy: Literal["fixed", "recursive"] = "recursive"
    chunk_size: int = 512                    # range: 100–4096
    chunk_overlap: int = 50                  # must be < chunk_size
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `strategy` | `"fixed"` or `"recursive"` | `"recursive"` | Chunking strategy |
| `chunk_size` | `int` | `512` | Target chunk size in characters (100–4096) |
| `chunk_overlap` | `int` | `50` | Overlap between consecutive chunks (0 ≤ overlap < chunk_size) |

**Strategies:**
- `"recursive"` — LangChain `RecursiveCharacterTextSplitter`; respects paragraph and sentence boundaries. Preferred for prose.
- `"fixed"` — LangChain `CharacterTextSplitter`; splits at exact character count. Faster but may split mid-sentence.

---

## Document

```python
from vibe_rag import Document
```

Core data model used throughout the pipeline.

```python
class Document(BaseModel):
    id: str           # auto-generated UUID
    content: str      # text content of this document/chunk
    metadata: dict[str, Any] = {}
    score: float | None = None   # similarity score set during retrieval
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | `str` | auto UUID | Unique identifier for this document/chunk |
| `content` | `str` | required | Text content |
| `metadata` | `dict[str, Any]` | `{}` | Arbitrary key-value metadata |
| `score` | `float` or `None` | `None` | Cosine similarity score (set during retrieval; not set on ingestion) |

Chunks produced by `DocumentProcessor.process()` include these metadata fields automatically:

| Key | Description |
|-----|-------------|
| `chunk_index` | 0-based position of this chunk in the sequence |
| `chunk_total` | Total number of chunks from this document |
| `chunk_size` | Actual character count of this chunk |
| `chunking_strategy` | Strategy used: `"fixed"`, `"recursive"`, or `"custom"` |
| `parent_doc_id` | UUID linking all chunks from the same source document |
| `chunk_overlap` | Configured overlap size in characters |

---

## Loaders

```python
from vibe_rag import TextLoader, MarkdownLoader, PDFLoader
from vibe_rag.loaders.base import BaseLoader
```

All loaders are async and return `list[Document]`.

### TextLoader

Loads plain text files (`.txt`) with automatic encoding detection.

Tries encodings in order: `utf-8`, `latin-1`, `cp1252`.

```python
loader = TextLoader()
documents = await loader.load("readme.txt")
# returns [Document(content="...", metadata={"source_file": "readme.txt",
#                                             "file_type": "text",
#                                             "encoding": "utf-8"})]
```

Raises `DocumentProcessingError` if the file is not found, is not a file, or cannot
be decoded with any of the attempted encodings.

### MarkdownLoader

Loads Markdown files (`.md`) and extracts header structure.

```python
loader = MarkdownLoader()
documents = await loader.load("guide.md")
# metadata includes: {"source_file": ..., "file_type": "markdown",
#                     "headers": ["# Title", "## Section 1", ...]}
```

Returns a single `Document` with the full markdown content.
Raises `DocumentProcessingError` if the file is not found.

### PDFLoader

Loads PDF files (`.pdf`) page-by-page using PyPDF2.

```python
loader = PDFLoader()
documents = await loader.load("report.pdf")
# returns one Document per page
# metadata: {"source_file": ..., "file_type": "pdf",
#            "page_number": 1, "total_pages": 42}
```

Returns one `Document` per page with `page_number` and `total_pages` in metadata.
Raises `DocumentProcessingError` if the file is not found or PDF parsing fails.
Partial results are available via `DocumentProcessingError.partial_results` when a
later page fails after earlier pages succeeded.

### Writing a Custom Loader

Subclass `BaseLoader` and implement the `load()` coroutine:

```python
from vibe_rag.loaders.base import BaseLoader
from vibe_rag.models import Document
from vibe_rag.utils.errors import DocumentProcessingError


class HtmlLoader(BaseLoader):
    async def load(self, file_path: str) -> list[Document]:
        try:
            with open(file_path, encoding="utf-8") as f:
                raw = f.read()
            # Strip HTML tags
            import re
            text = re.sub(r"<[^>]+>", " ", raw)
            return [Document(
                content=text,
                metadata={"source_file": file_path, "file_type": "html"},
            )]
        except Exception as e:
            raise DocumentProcessingError(
                f"Failed to load HTML: {e}",
                file_path=file_path,
                error_type=type(e).__name__,
                original_error=e,
            )
```

Register with the engine:

```python
engine.register_loader(".html", HtmlLoader())
```

---

## Errors

```python
from vibe_rag import (
    RAGException,
    EmbeddingError,
    RetrievalError,
    LLMProviderError,
    StorageError,
    ConfigurationError,
    DocumentProcessingError,
)
```

### Exception hierarchy

```
Exception
└── RAGException                    — base for all vibe-rag errors
    ├── EmbeddingError              — embedding generation failed
    ├── RetrievalError              — document retrieval failed
    ├── LLMProviderError            — LLM API error (timeout, rate limit, etc.)
    ├── StorageError                — database/storage operation failed
    ├── ConfigurationError          — invalid configuration or uninitialized state
    └── DocumentProcessingError     — file loading or chunking failed
```

### RAGException

Base exception. All vibe-rag errors inherit from this. Catch this to handle any
framework error in a single `except` clause.

### EmbeddingError

Raised when an embedding API call fails. Emitted by `RAGEngine.ingest()`.

### RetrievalError

Raised when similarity search fails. Emitted by `RAGEngine.query()`.

### LLMProviderError

Raised when the LLM generation API call fails (network error, quota exceeded, etc.).
Emitted by `RAGEngine.query()`.

### StorageError

Raised when a database operation fails (connection error, query error, etc.).
Emitted by `RAGEngine.initialize()` and `RAGEngine.ingest()`.

### ConfigurationError

Raised for invalid configuration or calling methods before initialization.

Common causes:
- `engine.query()` or `engine.ingest()` called before `engine.initialize()`
- `engine.get_metrics()` called when `enable_metrics=False`
- Unsupported `llm.provider` or `storage.backend` value
- `vector_dimension` does not match the embedding model's output size

### DocumentProcessingError

Raised when file loading or text chunking fails. Carries rich context:

```python
class DocumentProcessingError(RAGException):
    file_path: str | None       # path to the file that failed
    error_type: str | None      # e.g. "FileNotFoundError", "EncodingError"
    original_error: Exception | None
    partial_results: list | None  # successfully processed chunks before failure
```

---

## Observability

```python
from vibe_rag import RAGMetrics, MetricsTracker
```

### RAGMetrics

Dataclass holding metrics for a single `query()` call. Automatically populated and
recorded by `RAGEngine` when `enable_metrics=True`.

```python
@dataclass
class RAGMetrics:
    query_id: str           # auto UUID
    query: str              # original query text
    answer: str             # generated answer
    retrieval_time_ms: float
    generation_time_ms: float
    total_time_ms: float
    documents_retrieved: int
    documents_used: int
    input_tokens: Optional[int]   # None if not tracked by provider
    output_tokens: Optional[int]  # None if not tracked by provider
    metadata: dict[str, Any]      # pipeline_metadata, generation_kwargs, timestamps
```

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `to_dict()` | `dict[str, Any]` | Serialize to dictionary |
| `summarize()` | `str` | Human-readable one-line summary |

### MetricsTracker

Aggregates `RAGMetrics` objects across multiple queries.

```python
tracker = MetricsTracker()
```

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `create_metrics(query: str)` | `RAGMetrics` | Create a new metrics object for a query |
| `record(metrics: RAGMetrics)` | `None` | Record a completed metrics object |
| `get_all()` | `list[RAGMetrics]` | Return a copy of all recorded metrics |
| `get_stats()` | `dict[str, Any]` | Return aggregate statistics (see below) |
| `clear()` | `None` | Clear all recorded metrics |

`get_stats()` returns:

```python
{
    "total_queries": int,
    "avg_total_time_ms": float,
    "avg_retrieval_time_ms": float,
    "avg_generation_time_ms": float,
    "avg_documents_retrieved": float,
    "total_input_tokens": int,    # 0 if no provider tracks tokens
    "total_output_tokens": int,   # 0 if no provider tracks tokens
}
```

`get_stats()` returns all zeros when no metrics have been recorded yet.

### Accessing metrics via RAGEngine

```python
async with RAGEngine(config) as engine:
    await engine.query("Question 1")
    await engine.query("Question 2")

    # Individual metrics
    for m in engine.get_metrics():
        print(m.summarize())

    # Aggregate stats
    stats = engine.get_stats()
    print(f"Avg latency: {stats['avg_total_time_ms']:.0f}ms")
```
