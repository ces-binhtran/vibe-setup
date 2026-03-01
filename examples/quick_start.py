"""
Quick Start example for vibe-rag.

Get up and running in minutes with QuickSetup — minimal configuration required.

Prerequisites:
    - PostgreSQL with pgvector: docker-compose -f docker-compose.test.yml up -d
    - Gemini API key: export GEMINI_API_KEY="your-key"

Run:
    python examples/quick_start.py
"""

import asyncio
import os
import tempfile
from pathlib import Path

from vibe_rag import QuickSetup


async def main() -> None:
    api_key = os.getenv("GEMINI_API_KEY", "your-api-key-here")
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://vibetest:vibetest123@localhost:5434/vibe_rag_test",
    )

    # One-liner setup — sensible defaults: Gemini, recursive chunking, pgvector
    async with QuickSetup.create(
        provider_api_key=api_key,
        database_url=database_url,
        collection_name="quickstart",
    ) as rag:
        # Write a sample document to disk and ingest it
        sample_text = (
            "vibe-rag is a production-grade RAG framework with a "
            "'batteries included but removable' philosophy. "
            "It supports Gemini, PostgreSQL+pgvector, and composable pipelines. "
            "You can get started in under 5 minutes using QuickSetup."
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(sample_text)
            doc_path = f.name

        try:
            print("Ingesting document...")
            doc_ids = await rag.ingest(doc_path)
            print(f"Ingested {len(doc_ids)} chunk(s).")

            print("\nQuerying...")
            result = await rag.query("What is vibe-rag?")
            print(f"Answer: {result['answer']}")
            print(f"Sources retrieved: {result['metadata']['documents_retrieved']}")
        finally:
            Path(doc_path).unlink()


if __name__ == "__main__":
    asyncio.run(main())
