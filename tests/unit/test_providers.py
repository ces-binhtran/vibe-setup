"""Unit tests for LLM provider system.

Tests the BaseLLMProvider interface and GeminiProvider implementation
using mocked API calls (no real Gemini API requests).
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from vibe_rag.providers.base import BaseLLMProvider
from vibe_rag.providers.gemini import GeminiProvider
from vibe_rag.utils.errors import EmbeddingError, LLMProviderError


class TestBaseLLMProvider:
    """Test the BaseLLMProvider abstract interface."""

    def test_cannot_instantiate_directly(self) -> None:
        """BaseLLMProvider is abstract and cannot be instantiated."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseLLMProvider()  # type: ignore

    def test_subclass_must_implement_generate(self) -> None:
        """Subclasses must implement the generate() method."""

        class IncompleteProvider(BaseLLMProvider):
            async def embed(self, texts: list[str], **kwargs) -> list[list[float]]:  # type: ignore[empty-body]
                pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteProvider()  # type: ignore

    def test_subclass_must_implement_embed(self) -> None:
        """Subclasses must implement the embed() method."""

        class IncompleteProvider(BaseLLMProvider):
            async def generate(self, prompt: str, **kwargs) -> str:  # type: ignore[empty-body]
                pass

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteProvider()  # type: ignore

    def test_complete_implementation_works(self) -> None:
        """A complete implementation of BaseLLMProvider can be instantiated."""

        class CompleteProvider(BaseLLMProvider):
            async def generate(self, prompt: str, **kwargs) -> str:
                return "response"

            async def embed(self, texts: list[str], **kwargs) -> list[list[float]]:
                return [[0.1, 0.2, 0.3]]

        provider = CompleteProvider()
        assert isinstance(provider, BaseLLMProvider)


class TestGeminiProviderInitialization:
    """Test GeminiProvider initialization and configuration."""

    def test_init_with_api_key(self) -> None:
        """GeminiProvider can be initialized with API key parameter."""
        with patch("vibe_rag.providers.gemini.ChatGoogleGenerativeAI"), patch(
            "vibe_rag.providers.gemini.GoogleGenerativeAIEmbeddings"
        ):
            provider = GeminiProvider(api_key="test-key-123")
            assert provider.api_key == "test-key-123"
            assert provider.model_name == "gemini-2.0-flash"
            assert provider.embedding_model_name == "models/gemini-embedding-001"

    def test_init_from_environment(self) -> None:
        """GeminiProvider reads API key from GOOGLE_API_KEY environment variable."""
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "env-key-456"}), patch(
            "vibe_rag.providers.gemini.ChatGoogleGenerativeAI"
        ), patch("vibe_rag.providers.gemini.GoogleGenerativeAIEmbeddings"):
            provider = GeminiProvider()
            assert provider.api_key == "env-key-456"

    def test_init_without_api_key_raises_error(self) -> None:
        """GeminiProvider raises error if no API key is provided."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                LLMProviderError, match="Google API key not provided"
            ):
                GeminiProvider()

    def test_custom_model_names(self) -> None:
        """GeminiProvider accepts custom model names."""
        with patch("vibe_rag.providers.gemini.ChatGoogleGenerativeAI"), patch(
            "vibe_rag.providers.gemini.GoogleGenerativeAIEmbeddings"
        ):
            provider = GeminiProvider(
                api_key="test-key",
                model_name="gemini-custom",
                embedding_model="models/custom-embedding",
            )
            assert provider.model_name == "gemini-custom"
            assert provider.embedding_model_name == "models/custom-embedding"

    def test_initialization_failure_raises_error(self) -> None:
        """GeminiProvider raises LLMProviderError if LangChain models fail to initialize."""
        with patch(
            "vibe_rag.providers.gemini.ChatGoogleGenerativeAI",
            side_effect=Exception("API error"),
        ):
            with pytest.raises(
                LLMProviderError, match="Failed to initialize Gemini models"
            ):
                GeminiProvider(api_key="test-key")


class TestGeminiProviderGenerate:
    """Test GeminiProvider text generation."""

    @pytest.mark.asyncio
    async def test_generate_success(self) -> None:
        """generate() returns text response from Gemini API."""
        # Mock the LangChain response
        mock_response = MagicMock()
        mock_response.content = "RAG stands for Retrieval-Augmented Generation."

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)

        with patch("vibe_rag.providers.gemini.ChatGoogleGenerativeAI"), patch(
            "vibe_rag.providers.gemini.GoogleGenerativeAIEmbeddings"
        ):
            provider = GeminiProvider(api_key="test-key")
            provider._llm = mock_llm

            result = await provider.generate("What is RAG?")

            assert result == "RAG stands for Retrieval-Augmented Generation."
            mock_llm.ainvoke.assert_called_once_with("What is RAG?")

    @pytest.mark.asyncio
    async def test_generate_with_parameters(self) -> None:
        """generate() accepts and uses custom generation parameters."""
        mock_response = MagicMock()
        mock_response.content = "Test response"

        mock_custom_llm = MagicMock()
        mock_custom_llm.ainvoke = AsyncMock(return_value=mock_response)

        with patch("vibe_rag.providers.gemini.ChatGoogleGenerativeAI") as mock_chat, patch(
            "vibe_rag.providers.gemini.GoogleGenerativeAIEmbeddings"
        ):
            # Mock the custom LLM instance created with kwargs
            mock_chat.return_value = mock_custom_llm

            provider = GeminiProvider(api_key="test-key")

            result = await provider.generate(
                "Test prompt", temperature=0.7, max_tokens=500
            )

            assert result == "Test response"
            # Verify that a new ChatGoogleGenerativeAI was created with custom params
            mock_chat.assert_called()
            call_kwargs = mock_chat.call_args.kwargs
            assert call_kwargs.get("temperature") == 0.7
            assert call_kwargs.get("max_tokens") == 500

    @pytest.mark.asyncio
    async def test_generate_handles_string_response(self) -> None:
        """generate() handles responses that are plain strings."""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value="Plain string response")

        with patch("vibe_rag.providers.gemini.ChatGoogleGenerativeAI"), patch(
            "vibe_rag.providers.gemini.GoogleGenerativeAIEmbeddings"
        ):
            provider = GeminiProvider(api_key="test-key")
            provider._llm = mock_llm

            result = await provider.generate("Test")
            assert result == "Plain string response"

    @pytest.mark.asyncio
    async def test_generate_api_failure(self) -> None:
        """generate() raises LLMProviderError on API failures."""
        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(side_effect=Exception("Network timeout"))

        with patch("vibe_rag.providers.gemini.ChatGoogleGenerativeAI"), patch(
            "vibe_rag.providers.gemini.GoogleGenerativeAIEmbeddings"
        ):
            provider = GeminiProvider(api_key="test-key")
            provider._llm = mock_llm

            with pytest.raises(LLMProviderError, match="Gemini API call failed"):
                await provider.generate("Test prompt")


class TestGeminiProviderEmbed:
    """Test GeminiProvider embedding generation."""

    @pytest.mark.asyncio
    async def test_embed_success(self) -> None:
        """embed() returns embedding vectors from Gemini API."""
        mock_embeddings_obj = MagicMock()
        mock_embeddings_obj.aembed_documents = AsyncMock(
            return_value=[
                [0.1] * 768,  # 768-dimensional embedding for first text
                [0.2] * 768,  # 768-dimensional embedding for second text
            ]
        )

        with patch("vibe_rag.providers.gemini.ChatGoogleGenerativeAI"), patch(
            "vibe_rag.providers.gemini.GoogleGenerativeAIEmbeddings"
        ):
            provider = GeminiProvider(api_key="test-key")
            provider._embeddings = mock_embeddings_obj

            result = await provider.embed(["First document", "Second document"])

            assert len(result) == 2
            assert len(result[0]) == 768
            assert len(result[1]) == 768
            assert result[0] == [0.1] * 768
            assert result[1] == [0.2] * 768
            mock_embeddings_obj.aembed_documents.assert_called_once_with(
                ["First document", "Second document"]
            )

    @pytest.mark.asyncio
    async def test_embed_single_text(self) -> None:
        """embed() works with a single text input."""
        mock_embeddings_obj = MagicMock()
        mock_embeddings_obj.aembed_documents = AsyncMock(return_value=[[0.5] * 768])

        with patch("vibe_rag.providers.gemini.ChatGoogleGenerativeAI"), patch(
            "vibe_rag.providers.gemini.GoogleGenerativeAIEmbeddings"
        ):
            provider = GeminiProvider(api_key="test-key")
            provider._embeddings = mock_embeddings_obj

            result = await provider.embed(["Single document"])

            assert len(result) == 1
            assert len(result[0]) == 768

    @pytest.mark.asyncio
    async def test_embed_empty_list_raises_error(self) -> None:
        """embed() raises EmbeddingError for empty text list."""
        with patch("vibe_rag.providers.gemini.ChatGoogleGenerativeAI"), patch(
            "vibe_rag.providers.gemini.GoogleGenerativeAIEmbeddings"
        ):
            provider = GeminiProvider(api_key="test-key")

            with pytest.raises(
                EmbeddingError, match="Cannot generate embeddings for empty text list"
            ):
                await provider.embed([])

    @pytest.mark.asyncio
    async def test_embed_api_failure(self) -> None:
        """embed() raises EmbeddingError on API failures."""
        mock_embeddings_obj = MagicMock()
        mock_embeddings_obj.aembed_documents = AsyncMock(
            side_effect=Exception("API quota exceeded")
        )

        with patch("vibe_rag.providers.gemini.ChatGoogleGenerativeAI"), patch(
            "vibe_rag.providers.gemini.GoogleGenerativeAIEmbeddings"
        ):
            provider = GeminiProvider(api_key="test-key")
            provider._embeddings = mock_embeddings_obj

            with pytest.raises(
                EmbeddingError, match="Gemini embedding generation failed"
            ):
                await provider.embed(["Test document"])


class TestGeminiProviderIntegration:
    """Integration tests for GeminiProvider (still using mocks, no real API)."""

    @pytest.mark.asyncio
    async def test_complete_workflow(self) -> None:
        """Test a complete workflow: generate text and create embeddings."""
        # Mock generate
        mock_generate_response = MagicMock()
        mock_generate_response.content = "This is a generated response"

        mock_llm = MagicMock()
        mock_llm.ainvoke = AsyncMock(return_value=mock_generate_response)

        # Mock embed
        mock_embeddings_obj = MagicMock()
        mock_embeddings_obj.aembed_documents = AsyncMock(
            return_value=[[0.3] * 768, [0.4] * 768]
        )

        with patch("vibe_rag.providers.gemini.ChatGoogleGenerativeAI"), patch(
            "vibe_rag.providers.gemini.GoogleGenerativeAIEmbeddings"
        ):
            provider = GeminiProvider(api_key="test-key")
            provider._llm = mock_llm
            provider._embeddings = mock_embeddings_obj

            # Generate text
            text_response = await provider.generate("Tell me about RAG")
            assert text_response == "This is a generated response"

            # Generate embeddings
            embeddings = await provider.embed(["doc1", "doc2"])
            assert len(embeddings) == 2
            assert len(embeddings[0]) == 768

    @pytest.mark.asyncio
    async def test_provider_is_instance_of_base(self) -> None:
        """GeminiProvider is a proper implementation of BaseLLMProvider."""
        with patch("vibe_rag.providers.gemini.ChatGoogleGenerativeAI"), patch(
            "vibe_rag.providers.gemini.GoogleGenerativeAIEmbeddings"
        ):
            provider = GeminiProvider(api_key="test-key")
            assert isinstance(provider, BaseLLMProvider)
            assert isinstance(provider, GeminiProvider)
