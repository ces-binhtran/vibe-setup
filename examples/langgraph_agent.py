"""
LangGraph Agent example for vibe-rag.

Shows how to wrap RAGEngine as a LangGraph tool and use it inside a
ReAct agent that can combine RAG with other tools for complex workflows.

Prerequisites:
    - PostgreSQL with pgvector: docker-compose -f docker-compose.test.yml up -d
    - Gemini API key: export GEMINI_API_KEY="your-key"
    - LangGraph support: pip install vibe-rag[langgraph]

Run:
    python examples/langgraph_agent.py
"""

import asyncio
import os
import tempfile
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from vibe_rag import QuickSetup
from vibe_rag.integrations.langgraph import RAGTool


async def main() -> None:
    api_key = os.getenv("GEMINI_API_KEY", "your-api-key-here")
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://vibetest:vibetest123@localhost:5434/vibe_rag_test",
    )

    # Initialize RAG engine and ingest sample knowledge base
    async with QuickSetup.create(
        provider_api_key=api_key,
        database_url=database_url,
        collection_name="agent_demo",
    ) as rag:
        # Ingest sample policy documents into the knowledge base
        policies = {
            "refund_policy.txt": (
                "Our refund policy allows customers to return items within 30 days "
                "of purchase with a valid receipt. Refunds are processed within 5-7 "
                "business days to the original payment method."
            ),
            "shipping_policy.txt": (
                "We offer free standard shipping on orders over $50. "
                "Express shipping (2-3 days) is available for $9.99. "
                "International shipping takes 7-14 business days."
            ),
        }

        print("Ingesting knowledge base documents...")
        for filename, content in policies.items():
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False, prefix=filename
            ) as f:
                f.write(content)
                doc_path = f.name

            try:
                doc_ids = await rag.ingest(doc_path)
                print(f"  {filename}: {len(doc_ids)} chunk(s) ingested")
            finally:
                Path(doc_path).unlink()

        # Create RAGTool to expose the knowledge base to the agent
        rag_tool = RAGTool(rag_engine=rag)

        # Build a LangGraph ReAct agent with RAG as a tool
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=api_key)
        agent = create_react_agent(llm, tools=[rag_tool])

        # Run example queries through the agent
        queries = [
            "What is the refund policy?",
            "How long does international shipping take?",
        ]

        print("\nRunning agent queries...")
        for query in queries:
            print(f"\nQ: {query}")
            result = agent.invoke({"messages": [("user", query)]})
            answer = result["messages"][-1].content
            print(f"A: {answer}")


if __name__ == "__main__":
    asyncio.run(main())
