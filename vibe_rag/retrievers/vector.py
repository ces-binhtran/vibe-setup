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
