"""Pipeline builder for composing components."""

from vibe_rag.pipeline.base import BasePipelineComponent


class PipelineBuilder:
    """Build pipelines by chaining components.

    Provides a fluent API for composing pipeline components.

    Example:
        pipeline = (
            PipelineBuilder()
            .add_component(query_transformer)
            .add_component(retriever)
            .add_component(reranker)
            .build()
        )

        # Execute pipeline
        context = PipelineContext(query="What is RAG?")
        for component in pipeline:
            context = await component.process(context)
    """

    def __init__(self):
        """Initialize empty pipeline."""
        self.components: list[BasePipelineComponent] = []

    def add_component(
        self,
        component: BasePipelineComponent
    ) -> "PipelineBuilder":
        """Add a component to the pipeline.

        Args:
            component: Component instance to add

        Returns:
            Self for chaining
        """
        self.components.append(component)
        return self

    def build(self) -> list[BasePipelineComponent]:
        """Build and return the component list.

        Returns:
            List of components in execution order
        """
        return self.components
