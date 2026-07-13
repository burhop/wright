import pytest

from tool_registry.gateway_models import GatewayError, GatewayErrorCode
from test_gateway_service import service


@pytest.mark.asyncio
async def test_gateway_rejects_input_that_does_not_match_advertised_schema() -> None:
    instance, _, _ = service()
    tool = instance.catalog.tools("cad")[0]
    object.__setattr__(
        tool,
        "input_schema",
        {
            "type": "object",
            "required": ["shape"],
            "properties": {"shape": {"type": "string"}},
            "additionalProperties": False,
        },
    )
    instance.catalog.tools = lambda _: [tool]

    with pytest.raises(GatewayError) as captured:
        await instance.call_tool("s1", "r1", "cad__run", {"shape": 3})
    assert captured.value.code is GatewayErrorCode.INVALID_INPUT


@pytest.mark.asyncio
async def test_gateway_rejects_output_that_does_not_match_advertised_schema() -> None:
    instance, _, _ = service()
    tool = instance.catalog.tools("cad")[0]
    object.__setattr__(
        tool,
        "output_schema",
        {
            "type": "object",
            "required": ["artifact"],
            "properties": {"artifact": {"type": "string"}},
        },
    )
    instance.catalog.tools = lambda _: [tool]

    with pytest.raises(GatewayError) as captured:
        await instance.call_tool("s1", "r1", "cad__run", {})
    assert captured.value.code is GatewayErrorCode.INVALID_OUTPUT
