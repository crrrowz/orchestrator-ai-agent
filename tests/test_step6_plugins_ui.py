"""Tests for Step 6: Plugin Engine and Visual UI API Server."""

import pytest
from orchestrator.engines.core import ServiceContainer
from orchestrator.engines.plugins import PluginEngine, PluginManifest


@pytest.mark.anyio
async def test_plugin_engine_lifecycle():
    container = ServiceContainer()
    plugin_engine = PluginEngine()
    await plugin_engine.initialize(container)
    await plugin_engine.start()

    manifest = PluginManifest(
        name="docker-devops-tools",
        version="1.0.0",
        description="Docker integration",
        permissions=["terminal.execute"],
    )

    plugin_engine.register_plugin(manifest)
    assert len(plugin_engine.list_plugins()) == 1
    assert plugin_engine.get_plugin("docker-devops-tools") is not None

    health = await plugin_engine.healthcheck()
    assert health["loaded_plugins_count"] == 1
