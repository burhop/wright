from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

from core.tools import BaseTool, ToolContext


class EchoTool(BaseTool):
    name = "echo"
    description = "Return one bounded value."
    input_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["value"],
        "properties": {"value": {"type": "number"}},
    }
    output_schema = {
        "type": "object",
        "additionalProperties": False,
        "required": ["value"],
        "properties": {"value": {"type": "number"}},
    }

    async def execute(
        self, arguments: Mapping[str, Any], *, context: ToolContext
    ) -> Mapping[str, Any]:
        assert context.trace_id == "trace-1"
        return {"value": arguments["value"]}


def test_base_tool_requires_typed_metadata_and_exposes_safe_projection() -> None:
    tool = EchoTool()
    assert tool.contract()["name"] == "echo"
    assert tool.contract()["input_schema"]["additionalProperties"] is False


@pytest.mark.asyncio
async def test_base_tool_executes_with_bounded_context() -> None:
    tool = EchoTool()
    result = await tool.execute(
        {"value": 3},
        context=ToolContext(
            principal_id="engineer-1",
            workspace_id="workspace-1",
            trace_id="trace-1",
            request_id="request-1",
        ),
    )
    assert result == {"value": 3}


def test_base_tool_rejects_incomplete_subclasses() -> None:
    class IncompleteTool(BaseTool):
        pass

    with pytest.raises(TypeError):
        IncompleteTool()
