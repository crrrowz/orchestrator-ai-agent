"""Skill package models and manifests."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SkillManifest(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str = ""
    dependencies: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    tools_required: List[str] = Field(default_factory=list)
    system_prompt_snippet: str = ""
    reference_docs: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
