from __future__ import annotations

import pytest

from tool_registry.mcp_stdio import StdioGatewayBinding


@pytest.fixture
def stdio_gateway_binding() -> StdioGatewayBinding:
    return StdioGatewayBinding(
        session_id="fixture-session",
        principal_id="stdio:fixture",
        workspace_id="fixture-workspace",
    )
