"""End-to-end tests for RAG engine with real components."""

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


@pytest.mark.e2e
class TestRAGEngineE2E:
    """End-to-end tests with real PostgreSQL and Gemini."""

    @pytest.fixture
    async def rag_engine(self, postgres_connection_string, gemini_api_key):
        """Create RAGEngine with real components."""
        config = RAGConfig(
            llm=LLMConfig(
                provider="gemini",
                api_key=gemini_api_key,
                model_name="gemini-2.0-flash-exp",
                embedding_model="models/text-embedding-004",
            ),
            storage=StorageConfig(
                backend="postgres",
                collection_name="e2e_test_docs",
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
            # Clean up any existing data
            try:
                await engine.storage.delete_collection()
                await engine.storage._create_table()
            except Exception:
                pass

            yield engine

            # Cleanup after test
            try:
                await engine.storage.delete_collection()
            except Exception:
                pass

    async def test_complete_rag_workflow(self, rag_engine):
        """Test complete RAG workflow: ingest → query → verify."""
        # 1. Create test documents
        doc1_content = """
Python is a high-level programming language.
It was created by Guido van Rossum and first released in 1991.
Python emphasizes code readability and uses significant indentation.
It supports multiple programming paradigms including procedural, object-oriented, and functional programming.
"""

        doc2_content = """
JavaScript is a programming language that is one of the core technologies of the World Wide Web.
It was created by Brendan Eich in 1995.
JavaScript is primarily used for client-side web development.
It is a multi-paradigm language supporting event-driven, functional, and imperative programming styles.
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f1:
            f1.write(doc1_content)
            doc1_path = f1.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f2:
            f2.write(doc2_content)
            doc2_path = f2.name

        try:
            # 2. Ingest documents
            doc1_ids = await rag_engine.ingest(
                source=doc1_path,
                metadata={"topic": "python", "type": "programming_language"},
            )
            assert len(doc1_ids) > 0

            doc2_ids = await rag_engine.ingest(
                source=doc2_path,
                metadata={"topic": "javascript", "type": "programming_language"},
            )
            assert len(doc2_ids) > 0

            # 3. Query about Python
            result = await rag_engine.query("Who created Python?")

            # Verify response structure
            assert "answer" in result
            assert "sources" in result
            assert "metadata" in result

            # Verify answer mentions Guido van Rossum
            answer = result["answer"].lower()
            assert "guido" in answer or "rossum" in answer, f"Answer did not mention creator: {answer}"

            # Verify sources were retrieved
            assert len(result["sources"]) > 0

            # Verify at least one source is about Python
            sources_text = " ".join(src["content"].lower() for src in result["sources"])
            assert "python" in sources_text

            # Verify metadata
            metadata = result["metadata"]
            assert metadata["documents_retrieved"] > 0
            assert metadata["total_time_ms"] > 0

            print(f"\n✅ Query: Who created Python?")
            print(f"✅ Answer: {result['answer']}")
            print(f"✅ Retrieved {len(result['sources'])} sources")
            print(f"✅ Total time: {metadata['total_time_ms']:.2f}ms")

        finally:
            # Cleanup temp files
            os.unlink(doc1_path)
            os.unlink(doc2_path)

    async def test_semantic_search_accuracy(self, rag_engine):
        """Test that semantic search retrieves relevant documents."""
        # Create documents on different topics
        docs = {
            "machine_learning.txt": """
Machine learning is a subset of artificial intelligence.
It focuses on developing systems that can learn from data.
Common techniques include supervised learning, unsupervised learning, and reinforcement learning.
Neural networks are a popular approach in modern machine learning.
""",
            "cooking.txt": """
Cooking is the art of preparing food.
Common cooking methods include baking, frying, and boiling.
Recipes provide instructions for combining ingredients.
Seasoning is important for flavor in cooking.
""",
            "astronomy.txt": """
Astronomy is the study of celestial objects and phenomena.
It examines stars, planets, galaxies, and the universe.
Telescopes are essential tools for astronomers.
The Big Bang theory explains the origin of the universe.
""",
        }

        temp_files = []
        try:
            # Ingest all documents
            for filename, content in docs.items():
                with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                    f.write(content)
                    temp_files.append(f.name)

                await rag_engine.ingest(
                    source=f.name,
                    metadata={"filename": filename},
                )

            # Query about machine learning
            result = await rag_engine.query("What is machine learning?")

            # Verify ML document was retrieved
            sources_text = " ".join(src["content"].lower() for src in result["sources"])
            assert "machine learning" in sources_text or "neural network" in sources_text

            # Answer should mention machine learning concepts
            answer = result["answer"].lower()
            assert (
                "machine learning" in answer
                or "learn" in answer
                or "data" in answer
                or "ai" in answer
                or "artificial intelligence" in answer
            ), f"Answer doesn't seem relevant to ML: {answer}"

            print(f"\n✅ Semantic search successfully retrieved ML content")
            print(f"✅ Answer: {result['answer'][:200]}...")

        finally:
            for path in temp_files:
                os.unlink(path)

    async def test_chunking_preserves_context(self, rag_engine):
        """Test that chunking preserves context across boundaries."""
        # Create a document with clear sections
        content = """
SECTION 1: Introduction to Quantum Computing

Quantum computing is a type of computation that harnesses quantum mechanical phenomena.
Unlike classical computers that use bits, quantum computers use quantum bits or qubits.
This allows them to process information in fundamentally different ways.

SECTION 2: Quantum Superposition

Superposition is a key principle in quantum mechanics.
A qubit can exist in multiple states simultaneously until measured.
This property allows quantum computers to perform many calculations at once.

SECTION 3: Quantum Entanglement

Entanglement is another quantum phenomenon used in quantum computing.
When qubits are entangled, the state of one qubit affects the state of another.
This enables powerful correlations between quantum bits.
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            await rag_engine.ingest(source=temp_path)

            # Query about superposition
            result = await rag_engine.query("What is quantum superposition?")

            answer = result["answer"].lower()
            # Should mention key concepts
            assert (
                "superposition" in answer or "multiple states" in answer or "qubit" in answer
            ), f"Answer missing superposition concepts: {answer}"

            print(f"\n✅ Chunking preserved context for superposition query")
            print(f"✅ Answer: {result['answer']}")

        finally:
            os.unlink(temp_path)

    async def test_metadata_filtering(self, rag_engine):
        """Test metadata filtering in retrieval."""
        # Create documents with different metadata
        docs = [
            ("Python basics", {"language": "python", "level": "beginner"}),
            ("Python advanced", {"language": "python", "level": "advanced"}),
            ("JavaScript basics", {"language": "javascript", "level": "beginner"}),
        ]

        temp_files = []
        try:
            for content, metadata in docs:
                with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
                    f.write(content * 50)  # Make it longer
                    temp_files.append(f.name)
                await rag_engine.ingest(source=f.name, metadata=metadata)

            # Reconfigure pipeline with metadata filter
            rag_engine.config.pipeline.filter_metadata = {"language": "python"}
            rag_engine.pipeline = rag_engine._build_pipeline()

            # Query should only retrieve Python documents
            result = await rag_engine.query("programming language")

            # Check that sources are Python-related
            for source in result["sources"]:
                assert source["metadata"]["language"] == "python"

            print(f"\n✅ Metadata filtering worked correctly")
            print(f"✅ Retrieved {len(result['sources'])} Python documents only")

        finally:
            for path in temp_files:
                os.unlink(path)

    async def test_metrics_accuracy(self, rag_engine):
        """Test that metrics accurately reflect operations."""
        content = "Test document for metrics. " * 100

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            await rag_engine.ingest(source=temp_path)

            # Perform queries
            results = []
            for i in range(3):
                result = await rag_engine.query(f"Question {i}")
                results.append(result)

            # Verify metrics
            metrics = rag_engine.get_metrics()
            assert len(metrics) == 3

            stats = rag_engine.get_stats()
            assert stats["total_queries"] == 3
            assert stats["avg_total_time_ms"] > 0

            # Each query should have consistent metrics
            for metric in metrics:
                assert metric.total_time_ms > 0
                assert metric.retrieval_time_ms > 0
                assert metric.generation_time_ms > 0
                # Total should be roughly sum of parts (allowing for overhead)
                assert (
                    metric.total_time_ms >= metric.retrieval_time_ms + metric.generation_time_ms
                )

            print(f"\n✅ Metrics tracking is accurate")
            print(f"✅ Average total time: {stats['avg_total_time_ms']:.2f}ms")
            print(f"✅ Average retrieval: {stats['avg_retrieval_time_ms']:.2f}ms")
            print(f"✅ Average generation: {stats['avg_generation_time_ms']:.2f}ms")

        finally:
            os.unlink(temp_path)

    async def test_markdown_document_loading(self, rag_engine):
        """Test loading and querying Markdown documents."""
        markdown_content = """
# Python Programming

## Introduction

Python is a versatile programming language.

## Features

- **Easy to learn**: Simple syntax
- **Powerful**: Rich standard library
- **Versatile**: Multiple use cases

## Use Cases

1. Web development
2. Data science
3. Automation
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(markdown_content)
            temp_path = f.name

        try:
            doc_ids = await rag_engine.ingest(source=temp_path)
            assert len(doc_ids) > 0

            result = await rag_engine.query("What are Python's features?")

            answer = result["answer"].lower()
            # Should mention features
            assert any(
                keyword in answer
                for keyword in ["easy", "learn", "simple", "powerful", "library", "versatile"]
            ), f"Answer missing Python features: {answer}"

            print(f"\n✅ Markdown document loaded and queried successfully")

        finally:
            os.unlink(temp_path)
