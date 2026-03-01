"""Integration tests for LangGraph RAGTool with mock components."""

import pytest

from vibe_rag import (
    ChunkingConfig,
    LLMConfig,
    PipelineConfig,
    RAGConfig,
    RAGEngine,
    StorageConfig,
)
from vibe_rag.integrations.langgraph import RAGTool, RAGToolInput
from vibe_rag.testing.mocks import MockLLMProvider, MockVectorStore


@pytest.mark.integration
class TestRAGToolInput:
    """Tests for RAGToolInput Pydantic schema."""

    def test_requires_question(self):
        """RAGToolInput raises if question is missing."""
        with pytest.raises(Exception):
            RAGToolInput()  # type: ignore[call-arg]

    def test_default_top_k(self):
        """RAGToolInput defaults top_k to 5."""
        inp = RAGToolInput(question="What is RAG?")
        assert inp.top_k == 5

    def test_custom_top_k(self):
        """RAGToolInput accepts custom top_k."""
        inp = RAGToolInput(question="What is RAG?", top_k=3)
        assert inp.top_k == 3

    def test_question_stored(self):
        """RAGToolInput stores the question correctly."""
        inp = RAGToolInput(question="Test question?")
        assert inp.question == "Test question?"


@pytest.mark.integration
class TestRAGToolMetadata:
    """Tests for RAGTool class-level properties."""

    @pytest.fixture
    def mock_engine(self):
        """Create RAGEngine with mock components (not initialized)."""
        config = RAGConfig(
            llm=LLMConfig(provider="gemini", api_key="test-key"),
            storage=StorageConfig(
                backend="postgres",
                collection_name="test",
                connection_string="postgresql://user:pass@localhost/db",
            ),
        )
        return RAGEngine(
            config=config,
            provider=MockLLMProvider(),
            storage=MockVectorStore("test"),
        )

    def test_tool_name(self, mock_engine):
        """RAGTool has expected name for LangGraph."""
        tool = RAGTool(rag_engine=mock_engine)
        assert tool.name == "knowledge_base_search"

    def test_tool_description_not_empty(self, mock_engine):
        """RAGTool description is non-empty string."""
        tool = RAGTool(rag_engine=mock_engine)
        assert isinstance(tool.description, str)
        assert len(tool.description) > 0

    def test_args_schema_is_rag_tool_input(self, mock_engine):
        """RAGTool uses RAGToolInput as args_schema."""
        tool = RAGTool(rag_engine=mock_engine)
        assert tool.args_schema is RAGToolInput


@pytest.mark.integration
class TestRAGToolExecution:
    """Tests for RAGTool._run() and _arun() methods."""

    @pytest.fixture
    def mock_config(self):
        return RAGConfig(
            llm=LLMConfig(provider="gemini", api_key="test-key"),
            storage=StorageConfig(
                backend="postgres",
                collection_name="test_docs",
                connection_string="postgresql://user:pass@localhost/db",
            ),
            pipeline=PipelineConfig(top_k=3),
            chunking=ChunkingConfig(chunk_size=256, chunk_overlap=20),
        )

    @pytest.fixture
    async def initialized_engine(self, mock_config, populated_mock_store):
        """RAGEngine initialized with populated mock store."""
        engine = RAGEngine(
            config=mock_config,
            provider=MockLLMProvider(),
            storage=populated_mock_store,
        )
        async with engine:
            yield engine

    async def test_arun_returns_answer_and_sources(self, initialized_engine):
        """_arun returns dict with 'answer' and 'sources' keys."""
        tool = RAGTool(rag_engine=initialized_engine)
        result = await tool._arun("What is Python?")

        assert isinstance(result, dict)
        assert "answer" in result
        assert "sources" in result

    async def test_arun_answer_is_string(self, initialized_engine):
        """_arun answer is a non-empty string."""
        tool = RAGTool(rag_engine=initialized_engine)
        result = await tool._arun("What is machine learning?")

        assert isinstance(result["answer"], str)
        assert len(result["answer"]) > 0

    async def test_arun_sources_is_list(self, initialized_engine):
        """_arun sources is a list of dicts with content and score."""
        tool = RAGTool(rag_engine=initialized_engine)
        result = await tool._arun("What is data science?")

        assert isinstance(result["sources"], list)
        for src in result["sources"]:
            assert "content" in src
            assert "score" in src

    async def test_arun_top_k_limits_sources(self, initialized_engine):
        """_arun slices sources to top_k."""
        tool = RAGTool(rag_engine=initialized_engine)

        result_k1 = await tool._arun("What is Python?", top_k=1)
        assert len(result_k1["sources"]) <= 1

        result_k2 = await tool._arun("What is Python?", top_k=2)
        assert len(result_k2["sources"]) <= 2

    def test_run_returns_answer_and_sources(self, initialized_engine):
        """_run synchronously returns dict with 'answer' and 'sources'."""
        tool = RAGTool(rag_engine=initialized_engine)
        result = tool._run("What is Python?")

        assert isinstance(result, dict)
        assert "answer" in result
        assert "sources" in result


@pytest.mark.integration
class TestRAGToolErrorHandling:
    """Tests for error propagation through RAGTool."""

    async def test_arun_raises_on_uninitialized_engine(self):
        """_arun raises when engine is not initialized."""
        config = RAGConfig(
            llm=LLMConfig(provider="gemini", api_key="test-key"),
            storage=StorageConfig(
                backend="postgres",
                collection_name="test",
                connection_string="postgresql://user:pass@localhost/db",
            ),
        )
        engine = RAGEngine(
            config=config,
            provider=MockLLMProvider(),
            storage=MockVectorStore("test"),
        )
        tool = RAGTool(rag_engine=engine)

        with pytest.raises(Exception):
            await tool._arun("Test question?")
