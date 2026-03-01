"""Component registry for pipeline component discovery."""

from typing import Type

from vibe_rag.pipeline.base import BasePipelineComponent

# Global registry
_COMPONENT_REGISTRY: dict[str, Type[BasePipelineComponent]] = {}


def register_component(name: str):
    """Decorator to register a component for discovery.

    Args:
        name: Unique component identifier

    Returns:
        Decorator function

    Example:
        @register_component("vector_retriever")
        class VectorRetriever(BasePipelineComponent):
            ...
    """
    def decorator(cls: Type[BasePipelineComponent]):
        _COMPONENT_REGISTRY[name] = cls
        return cls
    return decorator


def get_component(name: str) -> Type[BasePipelineComponent] | None:
    """Get a registered component by name.

    Args:
        name: Component identifier

    Returns:
        Component class or None if not found
    """
    return _COMPONENT_REGISTRY.get(name)


def list_components() -> list[str]:
    """List all registered component names.

    Returns:
        List of component identifiers
    """
    return list(_COMPONENT_REGISTRY.keys())
