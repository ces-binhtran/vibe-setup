"""Google Gemini LLM provider implementation."""

import os
from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from vibe_rag.providers.base import BaseLLMProvider
from vibe_rag.utils.errors import EmbeddingError, LLMProviderError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider implementation.

    Implements the BaseLLMProvider interface using Google's Gemini API
    via LangChain integration.

    Features:
    - Text generation using Gemini Pro models
    - Embedding generation using Gemini embedding models (768 dimensions)
    - Async operations for production scalability
    - Configurable via environment variables or constructor args

    Environment Variables:
        GOOGLE_API_KEY: Google AI API key (required if not passed to constructor)

    Example:
        >>> provider = GeminiProvider(api_key="your-api-key")
        >>> response = await provider.generate("What is RAG?")
        >>> embeddings = await provider.embed(["doc1", "doc2"])

    Args:
        api_key: Google AI API key. If not provided, reads from GOOGLE_API_KEY env var
        model_name: Model name for text generation (default: "gemini-2.0-flash-exp")
        embedding_model: Model name for embeddings (default: "models/text-embedding-004")
        **kwargs: Additional parameters passed to the LangChain models
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gemini-2.0-flash",
        embedding_model: str = "models/gemini-embedding-001",
        **kwargs: Any,
    ) -> None:
        """Initialize Gemini provider.

        Args:
            api_key: Google AI API key. If not provided, reads from GOOGLE_API_KEY env var
            model_name: Model name for text generation
            embedding_model: Model name for embeddings
            **kwargs: Additional parameters for LangChain models

        Raises:
            LLMProviderError: If API key is not provided and not found in environment
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise LLMProviderError(
                "Google API key not provided. Set GOOGLE_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.model_name = model_name
        self.embedding_model_name = embedding_model

        # Initialize LangChain models
        try:
            self._llm = ChatGoogleGenerativeAI(
                model=model_name, google_api_key=self.api_key, **kwargs
            )
            self._embeddings = GoogleGenerativeAIEmbeddings(
                model=embedding_model, google_api_key=self.api_key, output_dimensionality=768
            )
        except Exception as e:
            raise LLMProviderError(f"Failed to initialize Gemini models: {e}") from e

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text response using Gemini.

        Args:
            prompt: Input text prompt
            **kwargs: Additional generation parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text response

        Raises:
            LLMProviderError: If API call fails or times out

        Example:
            >>> provider = GeminiProvider(api_key="...")
            >>> response = await provider.generate(
            ...     "Explain RAG in one sentence",
            ...     temperature=0.7
            ... )
        """
        try:
            # Update model parameters if provided
            if kwargs:
                # Create a new instance with updated parameters
                llm = ChatGoogleGenerativeAI(
                    model=self.model_name, google_api_key=self.api_key, **kwargs
                )
            else:
                llm = self._llm

            # LangChain's ainvoke is async
            response = await llm.ainvoke(prompt)

            # Extract text content from the response
            if hasattr(response, "content"):
                return str(response.content)
            else:
                return str(response)

        except Exception as e:
            raise LLMProviderError(f"Gemini API call failed: {e}") from e

    async def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        """Generate embeddings using Gemini embedding model.

        Args:
            texts: List of text strings to embed
            **kwargs: Additional embedding parameters

        Returns:
            List of embedding vectors (768 dimensions each)

        Raises:
            EmbeddingError: If embedding generation fails

        Example:
            >>> provider = GeminiProvider(api_key="...")
            >>> embeddings = await provider.embed(["text1", "text2"])
            >>> len(embeddings)
            2
            >>> len(embeddings[0])
            768

        Note:
            Gemini's text-embedding-004 model produces 768-dimensional embeddings.
            The model supports batch embedding for efficiency.
        """
        if not texts:
            raise EmbeddingError("Cannot generate embeddings for empty text list")

        try:
            # LangChain's aembed_documents is async and handles batch processing
            embeddings = await self._embeddings.aembed_documents(texts)
            return embeddings

        except Exception as e:
            raise EmbeddingError(f"Gemini embedding generation failed: {e}") from e
