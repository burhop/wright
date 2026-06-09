from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal


class McpServer(BaseModel):
    server_id: str
    name: str
    type: Literal["stdio", "sse", "webmcp"]
    command: Optional[Union[List[str], str]] = None
    is_active: bool
    is_installed: bool = False
    status: Literal["active", "inactive", "error"]
    error_message: Optional[str] = None
    category: str = "utilities"
    created_at: int
    updated_at: int
    image_url: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    installed_version: Optional[str] = None
    env_vars: Optional[dict[str, str]] = None
    instructions: Optional[str] = None


class McpServerCreate(BaseModel):
    name: str
    type: Literal["stdio", "sse", "webmcp"]
    command: Optional[Union[List[str], str]] = None
    category: str = "utilities"
    image_url: Optional[str] = None
    description: Optional[str] = None
    source_url: Optional[str] = None
    installed_version: Optional[str] = None
    env_vars: Optional[dict[str, str]] = None
    instructions: Optional[str] = None


class McpServerUpdate(BaseModel):
    is_active: Optional[bool] = None
    status: Optional[Literal["active", "inactive", "error"]] = None
    error_message: Optional[str] = None
    env_vars: Optional[dict[str, str]] = None
    instructions: Optional[str] = None


class McpTool(BaseModel):
    tool_id: str
    server_id: str
    name: str
    description: Optional[str] = None
    input_schema: dict = Field(default_factory=dict)
    is_enabled: bool
    created_at: int
