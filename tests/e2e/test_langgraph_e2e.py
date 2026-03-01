"""End-to-end tests for LangGraph RAGTool with real components."""

import os
import tempfile

import pytest

from vibe_rag import (
    ChunkingConfig,
    LLMConfig,
    PipelineConfig,
    RAGConfig,
    RAGEngine,
    StorageConfig,
)
from vibe_rag.integrations.langgraph import RAGTool


@pytest.mark.e2e
class TestLangGraphE2E:
    """End-to-end tests with real PostgreSQL and Gemini."""

    @pytest.fixture
    async def rag_engine(self, postgres_connection_string, gemini_api_key):
        """Create RAGEngine with real components for LangGraph e2e tests."""
        config = RAGConfig(
            llm=LLMConfig(
                provider="gemini",
                api_key=gemini_api_key,
                model_name="gemini-2.0-flash",
                embedding_model="models/gemini-embedding-001",
            ),
            storage=StorageConfig(
                backend="postgres",
                collection_name="e2e_langgraph_test",
                connection_string=postgres_connection_string,
                vector_dimension=768,
            ),
            pipeline=PipelineConfig(top_k=3),
            chunking=ChunkingConfig(
                strategy="recursive",
                chunk_size=512,
                chunk_overlap=50,
            ),
        )

        async with RAGEngine(config) as engine:
            # Clean slate for each test run
            try:
                await engine.storage.delete_collection()
                await engine.storage._create_table()
            except Exception:
                pass

            yield engine

            try:
                await engine.storage.delete_collection()
            except Exception:
                pass

    async def test_rag_tool_arun_returns_answer_and_sources(self, rag_engine):
        """RAGTool._arun returns non-empty answer and sources after ingestion."""
        content = (
            "The refund policy allows customers to return items within 30 days "
            "of purchase with a valid receipt."
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            doc_path = f.name

        try:
            await rag_engine.ingest(source=doc_path)

            tool = RAGTool(rag_engine=rag_engine)
            result = await tool._arun("What is the refund policy?")

            assert "answer" in result
            assert "sources" in result
            assert isinstance(result["answer"], str)
            assert len(result["answer"]) > 0
            assert isinstance(result["sources"], list)
            assert len(result["sources"]) > 0

            answer_lower = result["answer"].lower()
            assert (
                "refund" in answer_lower or "return" in answer_lower or "30" in answer_lower
            ), f"Answer not relevant to refund policy: {result['answer']}"

            print(f"\n✅ RAGTool._arun answered: {result['answer']}")
            print(f"✅ Retrieved {len(result['sources'])} source(s)")

        finally:
            os.unlink(doc_path)

    async def test_rag_tool_sources_respect_top_k(self, rag_engine):
        """RAGTool._arun slices sources to the requested top_k."""
        content = (
            "Shipping policy: standard delivery in 5-7 business days. "
            "Express shipping takes 2-3 business days. "
            "International orders take 7-14 business days to arrive."
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            doc_path = f.name

        try:
            await rag_engine.ingest(source=doc_path)

            tool = RAGTool(rag_engine=rag_engine)
            result = await tool._arun("How long does shipping take?", top_k=1)

            assert len(result["sources"]) <= 1

            print(f"\n✅ top_k=1 returned {len(result['sources'])} source(s)")

        finally:
            os.unlink(doc_path)

    async def test_agent_uses_rag_tool(self, rag_engine, gemini_api_key):
        """Full LangGraph agent loop invokes RAGTool and returns relevant answer."""
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langgraph.prebuilt import create_react_agent

        content = (
            "Our premium plan costs $49 per month and includes unlimited storage, "
            "priority support, and access to all advanced features."
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            doc_path = f.name

        try:
            await rag_engine.ingest(source=doc_path)

            rag_tool = RAGTool(rag_engine=rag_engine)
            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=gemini_api_key)
            agent = create_react_agent(llm, tools=[rag_tool])

            result = agent.invoke({"messages": [("user", "How much does the premium plan cost?")]})

            final_message = result["messages"][-1].content
            assert isinstance(final_message, str)
            assert len(final_message) > 0

            answer_lower = final_message.lower()
            assert (
                "49" in answer_lower or "premium" in answer_lower or "month" in answer_lower
            ), f"Agent answer not relevant to pricing: {final_message}"

            print(f"\n✅ Agent answered: {final_message}")

        finally:
            os.unlink(doc_path)
