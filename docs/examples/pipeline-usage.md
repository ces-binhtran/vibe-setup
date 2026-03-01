# Pipeline Usage Examples

## Basic Vector Retrieval

```python
from vibe_rag.pipeline import PipelineBuilder, PipelineContext
from vibe_rag.retrievers import VectorRetriever
from vibe_rag.storage import PostgresVectorStore
from vibe_rag.providers import GeminiProvider

async def basic_retrieval():
    # Setup
    storage = PostgresVectorStore(collection_name="knowledge_base")
    await storage.initialize()

    provider = GeminiProvider(api_key="your-api-key")

    # Create retriever
    retriever = VectorRetriever(
        storage=storage,
        provider=provider,
        top_k=5
    )

    # Build pipeline
    pipeline = PipelineBuilder().add_component(retriever).build()

    # Execute
    context = PipelineContext(query="What is machine learning?")
    for component in pipeline:
        context = await component.process(context)

    # Results
    for doc in context.documents:
        print(f"Score: {doc.score:.2f} - {doc.content[:100]}...")

    # Metadata
    print(f"Retrieval took: {context.metadata['VectorRetriever']['duration_ms']:.2f}ms")

    await storage.close()
```

## With Metadata Filtering

```python
# Filter by source
retriever = VectorRetriever(
    storage=storage,
    provider=provider,
    top_k=10,
    filter_metadata={"source": "documentation"}
)
```

## Pipeline Observability

```python
# Access execution trace
context = await execute_pipeline(pipeline, query="test")

for entry in context._trace:
    print(f"{entry['component']}: {entry['duration_ms']:.2f}ms")

# Export for visualization
data = context.to_dict()
# Send to visualization tool or save to file
```

## Creating Custom Components

```python
from vibe_rag.pipeline import BasePipelineComponent, PipelineContext, register_component

@register_component("my_component")
class MyCustomComponent(BasePipelineComponent):
    @property
    def component_type(self) -> str:
        return "transformer"

    async def process(self, context: PipelineContext) -> PipelineContext:
        # Custom processing logic
        context.add_component_metadata(
            self.component_name,
            {"custom_metric": 42}
        )
        return context
```
