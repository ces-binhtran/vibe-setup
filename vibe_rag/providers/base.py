"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any


class BaseLLMProvider(ABC):
    """Abstract base class that defines the interface for all LLM providers.

    All LLM provider implementations (Gemini, OpenAI, Anthropic, etc.) must
    inherit from this class and implement the required methods.

    This adapter pattern enables:
    - Swapping LLM providers without changing core framework code
    - Easy testing with mock implementations
    - User-defined custom providers

    Example:
        class MyCustomProvider(BaseLLMProvider):
            async def generate(self, prompt: str, **kwargs) -> str:
                # Custom implementation
                pass

            async def embed(self, texts: list[str], **kwargs) -> list[list[float]]:
                # Custom implementation
                pass
    """

    @abstractmethod
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text response from the LLM.

        Args:
            prompt: The input prompt/question to send to the LLM
            **kwargs: Provider-specific parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text response from the LLM

        Raises:
            LLMProviderError: If API call fails or times out

        Example:
            >>> provider = GeminiProvider(api_key="...")
            >>> response = await provider.generate(
            ...     "What is RAG?",
            ...     temperature=0.7,
            ...     max_tokens=500
            ... )
            >>> print(response)
            "RAG (Retrieval-Augmented Generation) is..."
        """
        pass

    @abstractmethod
    async def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        """Generate embeddings (vector representations) for text inputs.

        Args:
            texts: List of text strings to embed
            **kwargs: Provider-specific parameters

        Returns:
            List of embedding vectors, one per input text.
            Each embedding is a list of floats (typically 768 or 1536 dimensions).

        Raises:
            EmbeddingError: If embedding generation fails

        Example:
            >>> provider = GeminiProvider(api_key="...")
            >>> embeddings = await provider.embed([
            ...     "First document",
            ...     "Second document"
            ... ])
            >>> len(embeddings)
            2
            >>> len(embeddings[0])  # Dimension count (e.g., 768 for Gemini)
            768

        Note:
            Implementations should support batch embedding for efficiency.
            Large batches may need to be split based on provider API limits.
        """
        pass
