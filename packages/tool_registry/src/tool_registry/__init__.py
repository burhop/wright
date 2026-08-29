from .models import (
    McpServer,
    McpServerCreate,
    McpServerUpdate,
    McpTool,
    EnvVarDefinition,
)
from .db import (
    get_servers,
    get_server,
    get_server_by_name,
    insert_server,
    update_server,
    delete_server,
    get_tools,
    get_tool,
    insert_tools,
    clear_server_tools,
    update_tool_enabled,
)
from .secrets import read_secrets, write_secrets, delete_secrets, has_credentials
from .safety import ApprovalContext, McpSafetyPolicy, PolicyDecision
from .engineering_catalog import ENGINEERING_CATALOG
from .gateway_models import (
    GatewayError,
    GatewayErrorCode,
    GatewayRequest,
    GatewayResource,
    GatewaySessionContext,
    GatewayTool,
    GatewayToolResult,
    RequestState,
    SessionState,
)
from .program_status import (
    ProgramStatusDocument,
    ProgramStatusErrorCode,
    ProgramStatusPublisherState,
    ProgramStatusReadError,
    ProgramStatusReader,
)


def __getattr__(name: str):
    if name == "McpEngine":
        from .manager import McpEngine

        return McpEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "McpServer",
    "McpServerCreate",
    "McpServerUpdate",
    "McpTool",
    "EnvVarDefinition",
    "get_servers",
    "get_server",
    "get_server_by_name",
    "insert_server",
    "update_server",
    "delete_server",
    "get_tools",
    "get_tool",
    "insert_tools",
    "clear_server_tools",
    "update_tool_enabled",
    "read_secrets",
    "write_secrets",
    "delete_secrets",
    "has_credentials",
    "McpEngine",
    "ApprovalContext",
    "McpSafetyPolicy",
    "PolicyDecision",
    "ENGINEERING_CATALOG",
    "GatewayError",
    "GatewayErrorCode",
    "GatewayRequest",
    "GatewayResource",
    "GatewaySessionContext",
    "GatewayTool",
    "GatewayToolResult",
    "RequestState",
    "SessionState",
    "ProgramStatusDocument",
    "ProgramStatusErrorCode",
    "ProgramStatusPublisherState",
    "ProgramStatusReadError",
    "ProgramStatusReader",
]
