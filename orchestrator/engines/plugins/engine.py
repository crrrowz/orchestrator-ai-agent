"""Dynamic Plugin Engine for loading and isolating 3rd-party capabilities."""

from typing import Any, Dict, List, Optional
from orchestrator.engines.core.container import IContainer, IEngine
from orchestrator.engines.plugins.models import PluginManifest


class PluginEngine(IEngine):
    """Engine responsible for third-party plugin discovery, validation, and lifecycle."""

    engine_name: str = "plugins"

    def __init__(self) -> None:
        self._plugins: Dict[str, PluginManifest] = {}
        self._is_running: bool = False

    async def initialize(self, container: IContainer) -> None:
        container.register_engine(self)

    async def start(self) -> None:
        self._is_running = True

    async def stop(self) -> None:
        self._is_running = False

    def register_plugin(self, manifest: PluginManifest) -> None:
        self._plugins[manifest.name] = manifest

    def get_plugin(self, name: str) -> Optional[PluginManifest]:
        return self._plugins.get(name)

    def list_plugins(self) -> List[PluginManifest]:
        return list(self._plugins.values())

    async def healthcheck(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._is_running else "stopped",
            "loaded_plugins_count": len(self._plugins),
            "plugin_names": list(self._plugins.keys()),
        }
