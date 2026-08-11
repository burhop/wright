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


@pytest.mark.asyncio
async def test_gateway_preserves_child_error_that_does_not_match_success_schema() -> (
    None
):
    instance, lifecycle, _ = service()
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
    lifecycle.result = {
        "content": [
            {
                "type": "text",
                "text": "Solid Edge flange operation is not supported.",
            }
        ],
        "structuredContent": {"error": "provider_failure"},
        "isError": True,
    }

    result = await instance.call_tool("s1", "r1", "cad__run", {})

    assert result.is_error is True
    assert result.content == (
        {
            "type": "text",
            "text": "Solid Edge flange operation is not supported.",
        },
    )
    assert result.structured_content == {"error": "provider_failure"}


@pytest.mark.asyncio
async def test_gateway_redacts_brep_panel_token_from_model_result() -> None:
    instance, lifecycle, _ = service()
    tool = instance.catalog.tools("cad")[0]
    object.__setattr__(tool, "name", "cad__brep_app_status")
    object.__setattr__(tool, "tool_name", "brep.app.status")
    instance.catalog.tools = lambda _: [tool]
    secret = "this-token-must-stay-inside-wright"
    control_url = f"http://127.0.0.1:5199/?token={secret}"
    lifecycle.result = {
        "content": [
            {
                "type": "text",
                "text": f'{{"connected":true,"controlUrl":"{control_url}"}}',
            }
        ],
        "structuredContent": {
            "connected": True,
            "controlUrl": control_url,
        },
        "_meta": {"controlUrl": control_url},
        "isError": False,
    }

    result = await instance.call_tool("s1", "brep-status", tool.name, {})

    assert secret not in repr(result)
    assert "token=[redacted]" in repr(result)
