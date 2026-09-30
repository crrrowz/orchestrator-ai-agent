"""Plugin Engine models and manifests."""

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class PluginManifest(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = "ORAGAI Community"
    entrypoints: Dict[str, str] = Field(default_factory=dict)
    components: List[Dict[str, Any]] = Field(default_factory=list)
    dependencies: Dict[str, str] = Field(default_factory=dict)
    permissions: List[str] = Field(default_factory=list)
