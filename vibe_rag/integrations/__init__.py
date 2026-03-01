"""Integrations for vibe-rag with external frameworks.

Provides tool wrappers and adapters for popular AI frameworks.

Note:
    LangGraph integration requires the optional ``langgraph`` dependency:
    ``pip install vibe-rag[langgraph]``
"""

from vibe_rag.integrations.langgraph import RAGTool, RAGToolInput

__all__ = ["RAGTool", "RAGToolInput"]
