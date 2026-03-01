"""LangGraph integration for vibe-rag.

Provides RAGTool, a LangChain BaseTool wrapper around RAGEngine that enables
RAG to be used as a tool in LangGraph AI agent workflows.

Example:
    >>> from langgraph.prebuilt import create_react_agent
    >>> from langchain_google_genai import ChatGoogleGenerativeAI
    >>> from vibe_rag import RAGEngine
    >>> from vibe_rag.integrations.langgraph import RAGTool
    >>>
    >>> rag_tool = RAGTool(rag_engine=rag_engine)
    >>> llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
    >>> agent = create_react_agent(llm, tools=[rag_tool])
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import Any, Type

from langchain_core.tools import BaseTool
from pydantic import BaseModel, ConfigDict, Field

from vibe_rag.engine import RAGEngine


class RAGToolInput(BaseModel):
    """Input schema for RAGTool.

    Attributes:
        question: The question to answer using the knowledge base.
        top_k: Maximum number of source documents to return in the response.
    """

    question: str = Field(description="Question to answer using the knowledge base")
    top_k: int = Field(default=5, description="Number of source documents to include in response")


class RAGTool(BaseTool):
    """LangGraph-compatible tool that wraps RAGEngine.

    Implements both synchronous (_run) and asynchronous (_arun) execution to
    support all LangGraph agent types. The RAGEngine must be initialized before
    the tool is used (e.g., via ``async with RAGEngine(...) as engine``).

    Attributes:
        name: Tool identifier used by LangGraph agents.
        description: Natural language description shown to the LLM agent.
        args_schema: Pydantic schema defining the tool's input parameters.
        rag_engine: The initialized RAGEngine instance to query.

    Example:
        >>> async with RAGEngine(config) as engine:
        ...     tool = RAGTool(rag_engine=engine)
        ...     result = await tool._arun("What is our refund policy?")
        ...     print(result["answer"])
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = "knowledge_base_search"
    description: str = (
        "Search the knowledge base to answer questions using retrieved documents. "
        "Use this when you need domain-specific information from the knowledge base. "
        "Returns an answer with supporting source documents."
    )
    args_schema: Type[BaseModel] = RAGToolInput
    rag_engine: RAGEngine

    def _run(self, question: str, top_k: int = 5) -> dict[str, Any]:
        """Execute RAG query synchronously.

        Runs the async _arun method in a synchronous context. Handles the case
        where an event loop is already running (e.g., in Jupyter notebooks) by
        dispatching to a thread pool executor.

        Args:
            question: Question to answer using the knowledge base.
            top_k: Maximum number of source documents to include in response.

        Returns:
            Dictionary with 'answer' (str) and 'sources' (list of dicts).

        Raises:
            RAGException: If query execution fails.
            ConfigurationError: If the engine is not initialized.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return asyncio.run(self._arun(question, top_k))

        if loop.is_running():
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, self._arun(question, top_k))
                return future.result()

        return loop.run_until_complete(self._arun(question, top_k))

    async def _arun(self, question: str, top_k: int = 5) -> dict[str, Any]:
        """Execute RAG query asynchronously.

        Args:
            question: Question to answer using the knowledge base.
            top_k: Maximum number of source documents to include in response.

        Returns:
            Dictionary containing:
            - answer: Generated answer string.
            - sources: List of source dicts, each with 'content' and 'score'.

        Raises:
            RAGException: If query execution fails.
            ConfigurationError: If the engine is not initialized.
        """
        result = await self.rag_engine.query(question)
        return {
            "answer": result["answer"],
            "sources": [
                {"content": src["content"], "score": src["score"]}
                for src in result["sources"][:top_k]
            ],
        }
