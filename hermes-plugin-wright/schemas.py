from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal


class EnvVarDefinition(BaseModel):
    """Metadata about an environment variable an MCP server needs.
    Matches tool_registry.models.EnvVarDefinition exactly.
    """
    name: str
    label: str
    description: str = ""
    required: bool = True
    secret: bool = False


class DependencySpec(BaseModel):
    """Dependencies required to run the MCP server."""
    system: List[str] = Field(default_factory=list)
    python: List[str] = Field(default_factory=list)
    node: List[str] = Field(default_factory=list)


class CatalogEntry(BaseModel):
    """A registered engineering MCP server in the catalog."""
    id: str
    name: str
    vendor: str
    description: str
    domains: List[str]
    tags: List[str] = Field(default_factory=list)
    transport: Literal["stdio", "sse", "webmcp"]
    command: Union[List[str], str]
    source_url: Optional[str] = None
    image_url: Optional[str] = None
    locality: Literal["local", "remote"]
    weight: Literal["light", "medium", "heavy"]
    env_vars: List[EnvVarDefinition] = Field(default_factory=list)
    dependencies: DependencySpec = Field(default_factory=DependencySpec)
