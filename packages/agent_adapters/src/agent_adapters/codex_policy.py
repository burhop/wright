"""Fixed transport controls. Capability qualification is separate from config."""

SDK_VERSION = "0.162.1"
RUNTIME_VERSION = "0.162.1"

GATEWAY_READ_TOOL = {
    "type": "function",
    "name": "wright__workspace_status",
    "description": "Read this chat session's Wright workspace binding through the Wright gateway.",
    "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
}


def permitted_gateway_request(params):
    return (
        isinstance(params, dict)
        and params.get("tool") == GATEWAY_READ_TOOL["name"]
        and params.get("namespace") in {None, "functions"}
        and params.get("arguments") == {}
        and all(
            isinstance(params.get(key), str) and 0 < len(params[key]) <= 160
            for key in ("threadId", "turnId", "callId")
        )
    )


# Host controls, not behavioral instructions or model-selectable overrides.
CONFIG_OVERRIDES = (
    'sandbox_mode="read-only"',
    'approval_policy="never"',
    'approvals_reviewer="user"',
    'cli_auth_credentials_store="file"',
    'web_search="disabled"',
    "project_doc_max_bytes=0",
    "features.shell_tool=false",
    "features.unified_exec=false",
    "features.code_mode_host=false",
    "features.apps=false",
    "features.plugins=false",
    "features.remote_plugin=false",
    "features.hooks=false",
    "features.goals=false",
    "features.memories=false",
    "features.multi_agent=false",
    "features.multi_agent_v2=false",
    "features.browser_use=false",
    "features.computer_use=false",
    "features.image_generation=false",
    "features.view_image=false",
    "features.sleep_tool=false",
    "features.workspace_dependencies=false",
    "features.shell_snapshot=false",
    "features.skill_mcp_dependency_install=false",
    "features.skill_search=false",
    "features.tool_suggest=false",
    "analytics.enabled=false",
)

# Restrict the client itself: never expose shellCommand, process/*, configuration
# writes, platform goals, login/logout, dynamic tools or a remote Code Mode host.
RPC_METHODS = frozenset(
    {
        "initialize",
        "account/read",
        "model/list",
        "config/read",
        "thread/start",
        "thread/resume",
        "thread/read",
        "thread/list",
        "thread/archive",
        "turn/start",
        "turn/interrupt",
    }
)

NO_TOOLS_QUALIFIED = False
NO_TOOLS_REASON = (
    "Codex 0.162.1 still executes direct collaboration tools with the tested "
    "feature overrides and empty environments. Confined authoring and workflow "
    "decisions are unavailable pending an enforceable startup tool ceiling."
)


def deny_permission_request(method: str, params: dict | None) -> dict:
    """Agent approvals cannot grant Wright process or external-action authority."""
    if method in {
        "item/commandExecution/requestApproval",
        "item/fileChange/requestApproval",
    }:
        return {"decision": "decline"}
    if method == "item/permissions/requestApproval":
        return {"permissions": {}, "scope": "turn"}
    if method == "item/tool/requestUserInput":
        return {"answers": {}}
    if method == "item/tool/call":
        return {"success": False, "contentItems": []}
    # Unknown server requests must terminate the transport, never receive an
    # invented acknowledgement that could grant new upstream authority.
    raise ValueError("Unsupported Codex permission request")


def confined_rpc_params(method: str, params: dict) -> dict:
    """A model/user cannot relax transport controls through request fields."""
    allowed = {
        "initialize": set(),
        "account/read": set(),
        "model/list": set(),
        "config/read": set(),
        "thread/list": {"limit", "cursor"},
        "thread/read": {"threadId"},
        "thread/archive": {"threadId"},
        "turn/interrupt": {"threadId", "turnId"},
        "thread/start": {
            "model",
            "baseInstructions",
            "developerInstructions",
            "ephemeral",
        },
        "thread/resume": {
            "threadId",
            "model",
            "baseInstructions",
            "developerInstructions",
        },
        "turn/start": {"threadId", "input", "model", "effort", "outputSchema"},
    }
    if (
        method not in allowed
        or not isinstance(params, dict)
        or set(params) - allowed[method]
    ):
        raise ValueError("Unsupported Codex request fields")
    result = dict(params)
    if method in {"thread/start", "thread/resume", "turn/start"}:
        model = params.get("model")
        if not isinstance(model, str) or not model.strip() or len(model) > 160:
            raise ValueError("An explicit bounded Codex model is required")
        result.update(approvalPolicy="never", approvalsReviewer="user")
    required_ids = []
    if method in {
        "thread/resume",
        "thread/read",
        "thread/archive",
        "turn/start",
        "turn/interrupt",
    }:
        required_ids.append("threadId")
    if method == "turn/interrupt":
        required_ids.append("turnId")
    for field in required_ids:
        value = params.get(field)
        if not isinstance(value, str) or not value.strip() or len(value) > 160:
            raise ValueError("A bounded Codex thread/turn identity is required")
    for field in ("baseInstructions", "developerInstructions"):
        if field in params:
            value = params[field]
            if (
                not isinstance(value, str)
                or not value.strip()
                or len(value.encode("utf-8")) > 131072
            ):
                raise ValueError("Codex instructions must contain 1–131072 bytes")
    if method in {"thread/start", "thread/resume"}:
        result["sandbox"] = "read-only"
    if method == "thread/start":
        result.update(environments=[], allowProviderModelFallback=False)
    if method == "turn/start":
        inputs = params.get("input")
        if not isinstance(inputs, list) or not 1 <= len(inputs) <= 32:
            raise ValueError("Codex input must be a bounded text list")
        for item in inputs:
            if (
                not isinstance(item, dict)
                or set(item) != {"type", "text"}
                or item["type"] != "text"
                or not isinstance(item["text"], str)
            ):
                raise ValueError("This Codex transport has only qualified text input")
        result["environments"] = []
    return result
