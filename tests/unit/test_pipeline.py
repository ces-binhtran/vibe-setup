"""Tests for pipeline components."""

import pytest
from abc import ABC
from vibe_rag.pipeline.base import BasePipelineComponent
from vibe_rag.pipeline.context import PipelineContext
from vibe_rag.pipeline.registry import (
    register_component,
    get_component,
    list_components,
    _COMPONENT_REGISTRY
)


def test_base_component_is_abstract():
    """Test that BasePipelineComponent cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BasePipelineComponent()


def test_base_component_interface():
    """Test that BasePipelineComponent defines required interface."""
    assert hasattr(BasePipelineComponent, 'process')
    assert hasattr(BasePipelineComponent, 'component_type')
    assert hasattr(BasePipelineComponent, 'component_name')
    assert hasattr(BasePipelineComponent, 'validate_context')


class MockComponent(BasePipelineComponent):
    """Mock component for testing."""

    @property
    def component_type(self) -> str:
        return "mock"

    async def process(self, context: PipelineContext) -> PipelineContext:
        context.add_component_metadata(self.component_name, {"mock": True})
        return context


@pytest.mark.asyncio
async def test_mock_component_process():
    """Test that subclass can implement process."""
    component = MockComponent()
    context = PipelineContext(query="test")

    result = await component.process(context)

    assert result.query == "test"
    assert "MockComponent" in result.metadata
    assert result.metadata["MockComponent"]["mock"] is True


def test_component_name_defaults_to_class_name():
    """Test that component_name defaults to class name."""
    component = MockComponent()

    assert component.component_name == "MockComponent"


def test_validate_context_default():
    """Test that validate_context is a no-op by default."""
    component = MockComponent()
    context = PipelineContext(query="test")

    # Should not raise
    component.validate_context(context)


def test_register_component_decorator():
    """Test component registration via decorator."""
    @register_component("test_component")
    class TestComponent(BasePipelineComponent):
        @property
        def component_type(self) -> str:
            return "test"

        async def process(self, context: PipelineContext) -> PipelineContext:
            return context

    # Clear registry first to avoid conflicts
    _COMPONENT_REGISTRY.clear()

    @register_component("test_component")
    class TestComponent2(BasePipelineComponent):
        @property
        def component_type(self) -> str:
            return "test"

        async def process(self, context: PipelineContext) -> PipelineContext:
            return context

    assert get_component("test_component") == TestComponent2
    assert "test_component" in list_components()


def test_get_component_returns_none_for_missing():
    """Test that get_component returns None for missing components."""
    result = get_component("nonexistent_component")

    assert result is None


def test_list_components():
    """Test listing all registered components."""
    _COMPONENT_REGISTRY.clear()

    @register_component("comp1")
    class Comp1(BasePipelineComponent):
        @property
        def component_type(self) -> str:
            return "test"

        async def process(self, context: PipelineContext) -> PipelineContext:
            return context

    @register_component("comp2")
    class Comp2(BasePipelineComponent):
        @property
        def component_type(self) -> str:
            return "test"

        async def process(self, context: PipelineContext) -> PipelineContext:
            return context

    components = list_components()

    assert "comp1" in components
    assert "comp2" in components
    assert len(components) == 2
