"""Tests for Step 1: Core Engine, Component Model, and Event Engine."""

import pytest
from orchestrator.core.component import (
    ComponentMetadata,
    ComponentSchema,
    ComponentState,
    ComponentType,
    IComponent,
    PortDefinition,
    PortType,
)
from orchestrator.engines.core import CoreEngine, ServiceContainer
from orchestrator.engines.events import Event, EventEngine


class DummyComponent(IComponent):
    def __init__(self):
        self.schema = ComponentSchema(
            metadata=ComponentMetadata(
                id="dummy-1",
                name="Dummy Component",
                type=ComponentType.CUSTOM,
                category="test",
                description="Test component",
            ),
            inputs=[PortDefinition(name="in_val", type=PortType.STRING)],
            outputs=[PortDefinition(name="out_val", type=PortType.STRING)],
        )
        self.state = ComponentState.UNINITIALIZED
        self.config = {}

    def initialize(self, config):
        self.config = config
        self.state = ComponentState.INITIALIZED

    async def execute(self, inputs, runtime_context=None):
        self.state = ComponentState.EXECUTING
        res = {"out_val": inputs.get("in_val", "") + "_processed"}
        self.state = ComponentState.FINISHED
        return res

    def cleanup(self):
        self.state = ComponentState.UNMOUNTED


@pytest.mark.anyio
async def test_component_lifecycle():
    comp = DummyComponent()
    assert comp.state == ComponentState.UNINITIALIZED
    comp.initialize({"mode": "test"})
    assert comp.state == ComponentState.INITIALIZED

    res = await comp.execute({"in_val": "hello"})
    assert res == {"out_val": "hello_processed"}
    assert comp.state == ComponentState.FINISHED

    comp.cleanup()
    assert comp.state == ComponentState.UNMOUNTED


@pytest.mark.anyio
async def test_core_engine_bootstrap():
    core = CoreEngine()
    container = await core.bootstrap()
    assert container.get_engine(CoreEngine) is core
    await core.start()
    health = await core.healthcheck()
    assert health["status"] == "healthy"
    await core.stop()


@pytest.mark.anyio
async def test_event_engine_pubsub():
    event_engine = EventEngine()
    container = ServiceContainer()
    await event_engine.initialize(container)
    await event_engine.start()

    received = []

    async def handle_agent_event(event: Event):
        received.append(event)

    event_engine.subscribe("agent.*", handle_agent_event)

    await event_engine.publish("agent.started", {"agent": "developer"})
    await event_engine.publish("tool.executed", {"tool": "terminal"})
    await event_engine.publish("agent.finished", {"agent": "developer"})

    assert len(received) == 2
    assert received[0].topic == "agent.started"
    assert received[1].topic == "agent.finished"
    assert len(event_engine.get_history()) == 3

    await event_engine.stop()
