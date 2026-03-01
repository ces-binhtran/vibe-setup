"""
Simple RAG example demonstrating core functionality.

This example shows how to:
1. Configure the RAG engine
2. Ingest documents
3. Query the knowledge base
4. View results and metrics

Prerequisites:
- Python 3.10+
- PostgreSQL with pgvector running
- Google Gemini API key

Setup:
    export GOOGLE_API_KEY="your-api-key"
    docker-compose -f docker-compose.test.yml up -d
"""

import asyncio
import os
import tempfile
from pathlib import Path

from vibe_rag import (
    ChunkingConfig,
    LLMConfig,
    PipelineConfig,
    RAGConfig,
    RAGEngine,
    StorageConfig,
)


async def main():
    """Run simple RAG example."""
    # Configuration
    print("🔧 Configuring RAG engine...")
    config = RAGConfig(
        llm=LLMConfig(
            provider="gemini",
            api_key=os.getenv("GOOGLE_API_KEY", "your-api-key-here"),
            model_name="gemini-2.0-flash-exp",
        ),
        storage=StorageConfig(
            backend="postgres",
            collection_name="simple_example",
            connection_string=os.getenv(
                "POSTGRES_CONNECTION",
                "postgresql://vibetest:vibetest123@localhost:5433/vibe_rag_test",
            ),
            vector_dimension=768,
        ),
        pipeline=PipelineConfig(top_k=3),
        chunking=ChunkingConfig(
            strategy="recursive",
            chunk_size=512,
            chunk_overlap=50,
        ),
    )

    # Initialize engine
    print("🚀 Initializing RAG engine...")
    async with RAGEngine(config) as engine:
        # Clean up any existing data
        try:
            await engine.storage.delete_collection()
            await engine.storage._create_table()
            print("✅ Collection cleaned")
        except Exception as e:
            print(f"⚠️  Could not clean collection: {e}")

        # Create sample documents
        print("\n📝 Creating sample documents...")
        docs = {
            "python_intro.txt": """
Python Programming Language

Python is a high-level, interpreted programming language created by Guido van Rossum.
It was first released in 1991 and has since become one of the most popular languages.

Key Features:
- Simple, readable syntax that emphasizes code readability
- Dynamic typing and automatic memory management
- Extensive standard library
- Support for multiple programming paradigms (procedural, object-oriented, functional)
- Large ecosystem of third-party packages via PyPI

Common Use Cases:
- Web development (Django, Flask)
- Data science and machine learning (NumPy, Pandas, Scikit-learn)
- Automation and scripting
- Scientific computing
- Software testing
            """,
            "python_history.txt": """
History of Python

Python was conceived in the late 1980s by Guido van Rossum at Centrum Wiskunde & Informatica (CWI) in the Netherlands.
The first official release was Python 0.9.0 in February 1991.

Major Milestones:
- 1991: Python 0.9.0 released with classes, exceptions, functions
- 2000: Python 2.0 released with list comprehensions and garbage collection
- 2008: Python 3.0 released, not backward compatible with Python 2.x
- 2020: Python 2.7 end of life, Python 3 is the only supported version

The name "Python" was inspired by the British comedy series "Monty Python's Flying Circus",
not by the snake. Guido van Rossum remains Python's principal author and "Benevolent Dictator For Life" (BDFL),
though he stepped down from the role in 2018.
            """,
            "python_ecosystem.txt": """
Python Ecosystem

The Python ecosystem is vast and continues to grow rapidly.

Package Management:
- PyPI (Python Package Index): Official repository with 400,000+ packages
- pip: Standard package installer
- conda: Alternative package manager popular in data science

Popular Frameworks and Libraries:
- Web: Django, Flask, FastAPI
- Data Science: NumPy, Pandas, Matplotlib
- Machine Learning: TensorFlow, PyTorch, Scikit-learn
- Testing: pytest, unittest
- Async: asyncio, aiohttp

Community:
Python has one of the largest and most active programming communities.
The Python Software Foundation (PSF) oversees development and hosts annual conferences like PyCon.
            """,
        }

        # Write documents to disk and ingest
        temp_files = []
        for filename, content in docs.items():
            temp_path = Path(tempfile.gettempdir()) / filename
            temp_path.write_text(content)
            temp_files.append(temp_path)

            print(f"  📄 Ingesting {filename}...")
            await engine.ingest(
                str(temp_path),
                metadata={"filename": filename, "category": "programming"},
            )

        print(f"✅ Ingested {len(docs)} documents")

        # Test queries
        print("\n🔍 Running test queries...\n")
        queries = [
            "Who created Python and when?",
            "What are the main features of Python?",
            "What is Python commonly used for?",
            "What does the name Python refer to?",
        ]

        for i, query in enumerate(queries, 1):
            print(f"{'='*70}")
            print(f"Query {i}: {query}")
            print(f"{'='*70}")

            result = await engine.query(query)

            print(f"\n💡 Answer:\n{result['answer']}\n")

            print(f"📊 Metadata:")
            metadata = result["metadata"]
            print(f"  - Documents retrieved: {metadata['documents_retrieved']}")
            print(f"  - Retrieval time: {metadata['retrieval_time_ms']:.2f}ms")
            print(f"  - Generation time: {metadata['generation_time_ms']:.2f}ms")
            print(f"  - Total time: {metadata['total_time_ms']:.2f}ms")

            print(f"\n📚 Top sources:")
            for j, source in enumerate(result["sources"][:2], 1):
                print(f"  {j}. Score: {source['score']:.4f}")
                print(f"     From: {source['metadata'].get('filename', 'unknown')}")
                snippet = source["content"][:100].replace("\n", " ")
                print(f"     Preview: {snippet}...\n")

        # Show aggregate statistics
        print(f"\n{'='*70}")
        print("📈 Aggregate Statistics")
        print(f"{'='*70}")

        stats = engine.get_stats()
        print(f"Total queries: {stats['total_queries']}")
        print(f"Average total time: {stats['avg_total_time_ms']:.2f}ms")
        print(f"Average retrieval time: {stats['avg_retrieval_time_ms']:.2f}ms")
        print(f"Average generation time: {stats['avg_generation_time_ms']:.2f}ms")
        print(f"Average documents retrieved: {stats['avg_documents_retrieved']:.1f}")

        # Cleanup temp files
        for temp_path in temp_files:
            temp_path.unlink()

        print("\n✅ Example completed successfully!")


if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║              Vibe-RAG Simple Example                          ║
║  Production-grade RAG framework with batteries included       ║
╚═══════════════════════════════════════════════════════════════╝
    """)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL is running: docker-compose -f docker-compose.test.yml up -d")
        print("2. Set GOOGLE_API_KEY environment variable")
        print("3. Check connection string matches your setup")
        raise
