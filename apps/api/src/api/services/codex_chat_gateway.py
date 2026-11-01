"""One read-only chat operation over the existing authoritative Wright gateway."""

import json
import uuid

from agent_adapters.codex_policy import permitted_gateway_request
from core.agent_platform import AgentChatGatewayBinding
from core.redaction import redact_mapping
from tool_registry.gateway_service import SUPPORTED_PROTOCOL_VERSION


async def prepare_codex_chat_gateway(request, engine, scope, session_id):
    gateway = getattr(request.app.state, "gateway_service", None)
    # Match Wright's existing native MCP/control-plane actor convention. HTTP
    # authentication is owned by its middleware, never by the model or tool args.
    principal_id = getattr(request.state, "principal_id", "local-admin")
    if gateway is None or not principal_id:
        raise ValueError("The read-only Wright gateway is not ready")
    # Resolve the real gateway binding before a model turn can be submitted.
    # Gateway permission failures are distinct from agent approval decisions.
    gateway_id = f"codex-chat-{uuid.uuid4()}"
    binding = engine.repository.resolve_workspace_binding(session_id)
    if (binding.workspace_id, binding.workspace_path, binding.platform) != (
        scope.workspace_id,
        scope.workspace_dir,
        "codex",
    ):
        raise ValueError("Codex gateway scope does not match the saved session")
    gateway.open_session(
        session_id=gateway_id,
        principal_id=principal_id,
        workspace_id=scope.workspace_id,
        transport="legacy",  # Existing in-process gateway adapter boundary.
        binding_session_id=session_id,
    )
    try:
        gateway.initialize_session(
            gateway_id,
            protocol_version=SUPPORTED_PROTOCOL_VERSION,
            client_name="wright-codex",
            client_version="0.162.1",
            client_capabilities={},
        )
        engine.repository.bind_chat_gateway(
            AgentChatGatewayBinding(
                session_id=session_id,
                workspace_id=scope.workspace_id,
                principal_id=principal_id,
            )
        )
    except Exception:
        await gateway.close_session(gateway_id)
        raise

    async def call(params):
        try:
            if not permitted_gateway_request(params):
                raise ValueError("Unqualified Codex gateway operation")
            result = await gateway.call_tool(
                gateway_id,
                params["callId"],
                "wright__workspace_status",
                {},
                timeout=10,
                client_approval_hint=False,
                workspace_approvals=set(),
            )
            return {
                "success": not result.is_error,
                "contentItems": [
                    {
                        "type": "inputText",
                        "text": json.dumps(
                            redact_mapping(
                                {
                                    "structuredContent": result.structured_content,
                                    "content": list(result.content),
                                    "errorCode": result.error_code,
                                }
                            )
                        ),
                    }
                ],
            }
        except Exception:
            return {
                "success": False,
                "contentItems": [
                    {
                        "type": "inputText",
                        "text": "Wright gateway request denied or failed.",
                    }
                ],
            }

    async def close():
        await gateway.close_session(gateway_id)

    return call, close
