"""Base interface for pipeline components."""

from abc import ABC, abstractmethod

from vibe_rag.pipeline.context import PipelineContext


class BasePipelineComponent(ABC):
    """Base interface for all pipeline components.

    Components are stateless processors that enrich the context
    as it flows through the pipeline.

    All components must implement:
    - process(): Main processing logic
    - component_type: Component category (retriever, transformer, etc.)

    Optional:
    - component_name: Unique identifier (defaults to class name)
    - validate_context(): Validate context before processing

    Example:
        @register_component("my_component")
        class MyComponent(BasePipelineComponent):
            @property
            def component_type(self) -> str:
                return "transformer"

            async def process(self, context: PipelineContext) -> PipelineContext:
                # Process and enrich context
                return context
    """

    @abstractmethod
    async def process(self, context: PipelineContext) -> PipelineContext:
        """Process the context and return enriched context.

        Args:
            context: Current pipeline context

        Returns:
            Enriched context with component's results and metadata

        Raises:
            RAGException: If processing fails
        """
        pass

    @property
    @abstractmethod
    def component_type(self) -> str:
        """Return component type.

        Returns:
            Component category: "transformer", "retriever", "reranker", "generator"
        """
        pass

    @property
    def component_name(self) -> str:
        """Return unique component name.

        Defaults to class name. Override for custom names.

        Returns:
            Component identifier
        """
        return self.__class__.__name__

    def validate_context(self, context: PipelineContext) -> None:
        """Validate context has required data before processing.

        Override in subclasses to check preconditions.

        Args:
            context: Pipeline context to validate

        Raises:
            ConfigurationError: If context is invalid
        """
        pass
