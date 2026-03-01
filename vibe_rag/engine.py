"""RAG Engine - The main orchestrator for RAG operations."""

import time
from typing import Any, Optional

from vibe_rag.config.models import RAGConfig
from vibe_rag.loaders.base import BaseLoader
from vibe_rag.loaders.text import TextLoader
from vibe_rag.loaders.markdown import MarkdownLoader
from vibe_rag.loaders.pdf import PDFLoader
from vibe_rag.models import Document
from vibe_rag.pipeline.base import BasePipelineComponent
from vibe_rag.pipeline.builder import PipelineBuilder
from vibe_rag.pipeline.context import PipelineContext
from vibe_rag.providers.base import BaseLLMProvider
from vibe_rag.providers.gemini import GeminiProvider
from vibe_rag.retrievers.vector import VectorRetriever
from vibe_rag.storage.base import BaseVectorStore
from vibe_rag.storage.postgres_vector import PostgresVectorStore
from vibe_rag.transformers.document import DocumentProcessor
from vibe_rag.utils.errors import (
    ConfigurationError,
    DocumentProcessingError,
    LLMProviderError,
    RAGException,
    RetrievalError,
    StorageError,
)
from vibe_rag.utils.observability import MetricsTracker, RAGMetrics


class RAGEngine:
    """Main RAG engine orchestrating all components.

    The RAGEngine is the central interface for RAG operations. It:
    - Initializes and manages all components (LLM, storage, pipeline)
    - Handles document ingestion (loading, chunking, embedding, storing)
    - Executes RAG queries (retrieval + generation)
    - Tracks metrics and observability

    Example:
        >>> config = RAGConfig(
        ...     llm=LLMConfig(api_key="your-key"),
        ...     storage=StorageConfig(connection_string="postgresql://...")
        ... )
        >>> async with RAGEngine(config) as engine:
        ...     # Ingest documents
        ...     await engine.ingest("path/to/docs.txt")
        ...
        ...     # Query
        ...     result = await engine.query("What is RAG?")
        ...     print(result["answer"])
    """

    def __init__(
        self,
        config: RAGConfig,
        provider: Optional[BaseLLMProvider] = None,
        storage: Optional[BaseVectorStore] = None,
        enable_metrics: bool = True,
    ):
        """Initialize RAG engine.

        Args:
            config: Complete RAG configuration
            provider: Optional custom LLM provider (overrides config)
            storage: Optional custom storage backend (overrides config)
            enable_metrics: Whether to track metrics (default: True)

        Raises:
            ConfigurationError: If configuration is invalid
        """
        self.config = config

        # Validate configuration
        try:
            self.config.validate_dimensions()
        except ValueError as e:
            raise ConfigurationError(str(e)) from e

        # Initialize components
        self.provider = provider or self._create_provider()
        self.storage = storage or self._create_storage()
        self.document_processor = DocumentProcessor(
            strategy=config.chunking.strategy,
            chunk_size=config.chunking.chunk_size,
            chunk_overlap=config.chunking.chunk_overlap,
        )

        # Build pipeline
        self.pipeline = self._build_pipeline()

        # Metrics tracking
        self.enable_metrics = enable_metrics
        self.metrics_tracker = MetricsTracker() if enable_metrics else None

        # Loaders registry
        self._loaders: dict[str, BaseLoader] = {
            ".txt": TextLoader(),
            ".md": MarkdownLoader(),
            ".pdf": PDFLoader(),
        }

        self._initialized = False

    def _create_provider(self) -> BaseLLMProvider:
        """Create LLM provider from config.

        Returns:
            Initialized LLM provider

        Raises:
            ConfigurationError: If provider type is unsupported
        """
        if self.config.llm.provider == "gemini":
            return GeminiProvider(
                api_key=self.config.llm.api_key,
                model_name=self.config.llm.model_name,
                embedding_model=self.config.llm.embedding_model,
            )
        else:
            raise ConfigurationError(
                f"Unsupported LLM provider: {self.config.llm.provider}"
            )

    def _create_storage(self) -> BaseVectorStore:
        """Create storage backend from config.

        Returns:
            Initialized storage backend

        Raises:
            ConfigurationError: If storage backend is unsupported
        """
        if self.config.storage.backend == "postgres":
            return PostgresVectorStore(
                collection_name=self.config.storage.collection_name,
                connection_string=self.config.storage.connection_string,
                vector_dimension=self.config.storage.vector_dimension,
            )
        else:
            raise ConfigurationError(
                f"Unsupported storage backend: {self.config.storage.backend}"
            )

    def _build_pipeline(self) -> list[BasePipelineComponent]:
        """Build retrieval pipeline from config.

        Returns:
            List of pipeline components in execution order
        """
        builder = PipelineBuilder()

        # Add retriever
        retriever = VectorRetriever(
            storage=self.storage,
            provider=self.provider,
            top_k=self.config.pipeline.top_k,
            filter_metadata=self.config.pipeline.filter_metadata,
        )
        builder.add_component(retriever)

        # Future: Add reranker if enabled
        # if self.config.pipeline.reranking_enabled:
        #     builder.add_component(reranker)

        return builder.build()

    async def initialize(self) -> None:
        """Initialize all components.

        Must be called before using the engine.

        Raises:
            StorageError: If storage initialization fails
        """
        if self._initialized:
            return

        await self.storage.initialize()
        self._initialized = True

    async def close(self) -> None:
        """Close all components and cleanup resources."""
        if self._initialized:
            await self.storage.close()
            self._initialized = False

    async def __aenter__(self) -> "RAGEngine":
        """Enter async context manager.

        Returns:
            Self for use in 'async with' statements
        """
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context manager."""
        await self.close()

    async def ingest(
        self,
        source: str,
        metadata: Optional[dict[str, Any]] = None,
        loader: Optional[BaseLoader] = None,
    ) -> list[str]:
        """Ingest documents into the RAG system.

        Handles the complete ingestion pipeline:
        1. Load document from source (using file extension or custom loader)
        2. Chunk into smaller pieces
        3. Generate embeddings
        4. Store in vector database

        Args:
            source: File path to document
            metadata: Optional metadata to attach to all chunks
            loader: Optional custom loader (overrides default file extension logic)

        Returns:
            List of document IDs that were added

        Raises:
            DocumentProcessingError: If loading or chunking fails
            EmbeddingError: If embedding generation fails
            StorageError: If storage operation fails
        """
        if not self._initialized:
            raise ConfigurationError("Engine not initialized. Call initialize() first.")

        try:
            # 1. Load document
            if loader is None:
                # Auto-detect loader from file extension
                import os

                ext = os.path.splitext(source)[1].lower()
                if ext not in self._loaders:
                    raise DocumentProcessingError(
                        f"No loader registered for file type: {ext}. "
                        f"Supported types: {list(self._loaders.keys())}"
                    )
                loader = self._loaders[ext]

            documents = await loader.load(source)

            # 2. Chunk documents
            all_chunks = []
            for doc in documents:
                # Merge source metadata with document metadata
                doc_metadata = {**(metadata or {}), **doc.metadata}
                chunks = self.document_processor.process(doc.content, doc_metadata)
                all_chunks.extend(chunks)

            # 3. Generate embeddings
            texts = [chunk.content for chunk in all_chunks]
            embeddings = await self.provider.embed(texts)

            # 4. Store in vector database
            doc_ids = await self.storage.add_documents(all_chunks, embeddings)

            return doc_ids

        except (DocumentProcessingError, StorageError) as e:
            # Re-raise known errors
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise DocumentProcessingError(
                f"Failed to ingest document from {source}: {e}",
                error_type=type(e).__name__,
                original_error=e,
            ) from e

    async def query(
        self,
        query: str,
        generation_kwargs: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Execute RAG query.

        Handles the complete RAG pipeline:
        1. Retrieve relevant documents
        2. Generate answer using LLM + context
        3. Track metrics

        Args:
            query: User question
            generation_kwargs: Optional parameters for LLM generation
                              (overrides config defaults)

        Returns:
            Dictionary containing:
            - answer: Generated answer
            - sources: Retrieved documents with scores
            - metadata: Query metadata (ID, timings, tokens, etc.)

        Raises:
            RetrievalError: If document retrieval fails
            LLMProviderError: If LLM generation fails
        """
        if not self._initialized:
            raise ConfigurationError("Engine not initialized. Call initialize() first.")

        # Create metrics
        metrics = self.metrics_tracker.create_metrics(query) if self.enable_metrics else None
        total_start = time.time()

        try:
            # 1. Retrieval phase
            retrieval_start = time.time()
            context = PipelineContext(query=query)

            # Execute pipeline
            for component in self.pipeline:
                context = await component.process(context)

            retrieval_time = (time.time() - retrieval_start) * 1000

            # Get retrieved documents
            documents = context.documents or []

            # 2. Generation phase
            generation_start = time.time()

            # Build prompt with context
            context_text = "\n\n".join(
                f"[Source {i+1}] {doc.content}" for i, doc in enumerate(documents)
            )

            prompt = f"""Based on the following context, answer the question.

Context:
{context_text}

Question: {query}

Answer:"""

            # Merge generation kwargs
            gen_kwargs = {**self.config.llm.generation_kwargs}
            if generation_kwargs:
                gen_kwargs.update(generation_kwargs)

            # Generate answer
            answer = await self.provider.generate(prompt, **gen_kwargs)
            generation_time = (time.time() - generation_start) * 1000

            # 3. Build response
            total_time = (time.time() - total_start) * 1000

            # Prepare sources
            sources = [
                {
                    "content": doc.content,
                    "score": doc.score,
                    "metadata": doc.metadata,
                }
                for doc in documents
            ]

            # Update metrics
            if metrics:
                metrics.answer = answer
                metrics.retrieval_time_ms = retrieval_time
                metrics.generation_time_ms = generation_time
                metrics.total_time_ms = total_time
                metrics.documents_retrieved = len(documents)
                metrics.documents_used = len(documents)
                metrics.metadata.update(
                    {
                        "pipeline_metadata": context.metadata,
                        "generation_kwargs": gen_kwargs,
                    }
                )
                self.metrics_tracker.record(metrics)

            response = {
                "answer": answer,
                "sources": sources,
                "metadata": {
                    "query_id": metrics.query_id if metrics else None,
                    "retrieval_time_ms": retrieval_time,
                    "generation_time_ms": generation_time,
                    "total_time_ms": total_time,
                    "documents_retrieved": len(documents),
                    "pipeline_metadata": context.metadata,
                },
            }

            return response

        except (RetrievalError, LLMProviderError) as e:
            # Re-raise known errors
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise RAGException(f"Query execution failed: {e}") from e

    def register_loader(self, extension: str, loader: BaseLoader) -> None:
        """Register custom document loader for file extension.

        Args:
            extension: File extension (e.g., ".docx")
            loader: Loader instance
        """
        self._loaders[extension] = loader

    def get_metrics(self) -> list[RAGMetrics]:
        """Get all recorded metrics.

        Returns:
            List of metrics for all queries

        Raises:
            ConfigurationError: If metrics tracking is disabled
        """
        if not self.enable_metrics or not self.metrics_tracker:
            raise ConfigurationError("Metrics tracking is disabled")
        return self.metrics_tracker.get_all()

    def get_stats(self) -> dict[str, Any]:
        """Get aggregate statistics across all queries.

        Returns:
            Dictionary with aggregate stats

        Raises:
            ConfigurationError: If metrics tracking is disabled
        """
        if not self.enable_metrics or not self.metrics_tracker:
            raise ConfigurationError("Metrics tracking is disabled")
        return self.metrics_tracker.get_stats()
