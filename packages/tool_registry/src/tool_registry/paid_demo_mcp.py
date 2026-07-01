import json
import sys
from typing import Any


SERVER_NAME = "premium-ops-intelligence-mcp"
SERVER_VERSION = "0.1.0"


TOOLS = [
    {
        "name": "subscription_status",
        "description": "Return the mocked paid subscription state for the demo MCP server.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "build_ops_plan",
        "description": "Create a mock operating plan for a subscribed business agent.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "description": "Business operation the agent should plan.",
                },
                "budget_usd": {
                    "type": "number",
                    "description": "Optional monthly budget for the operation.",
                },
            },
            "required": ["goal"],
            "additionalProperties": False,
        },
    },
    {
        "name": "quote_mcp_usage",
        "description": "Return mock Stripe metering numbers for an MCP usage scenario.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "calls_per_month": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Expected monthly tool calls.",
                }
            },
            "required": ["calls_per_month"],
            "additionalProperties": False,
        },
    },
]


def _result(req_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _error(req_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": code, "message": message},
    }


def _text_response(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}


def _call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "subscription_status":
        return _text_response(
            "Premium Ops Intelligence MCP is active. Mock Stripe subscription: "
            "status=paid, plan=business-ops-pro, amount=$19/month."
        )

    if name == "build_ops_plan":
        goal = str(arguments.get("goal", "run business operations")).strip()
        budget = arguments.get("budget_usd")
        budget_text = f" with a ${budget:,.2f} monthly budget" if isinstance(budget, (int, float)) else ""
        return _text_response(
            "Mock operating plan unlocked by Stripe subscription:\n"
            f"1. Scope: {goal}{budget_text}.\n"
            "2. Provision: enable required SaaS and MCP tools through Hermes.\n"
            "3. Control: keep purchases behind Stripe Link approval or an MPP budget cap.\n"
            "4. Report: emit spend, tool usage, and outcome metrics back to Wright."
        )

    if name == "quote_mcp_usage":
        calls = int(arguments.get("calls_per_month", 0))
        per_call_cents = 3
        total_cents = calls * per_call_cents
        return _text_response(
            "Mock Stripe metering quote:\n"
            f"- Calls/month: {calls}\n"
            f"- Unit price: ${per_call_cents / 100:.2f} per call\n"
            f"- Estimated monthly total: ${total_cents / 100:.2f}"
        )

    raise ValueError(f"Unknown tool: {name}")


def _handle(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method")
    req_id = request.get("id")

    if method == "initialize":
        return _result(
            req_id,
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            },
        )

    if method == "notifications/initialized":
        return None

    if method == "ping":
        return _result(req_id, {})

    if method == "tools/list":
        return _result(req_id, {"tools": TOOLS})

    if method == "tools/call":
        params = request.get("params") or {}
        try:
            return _result(
                req_id,
                _call_tool(str(params.get("name")), params.get("arguments") or {}),
            )
        except Exception as exc:
            return _result(
                req_id,
                {
                    "isError": True,
                    "content": [{"type": "text", "text": str(exc)}],
                },
            )

    if req_id is None:
        return None

    return _error(req_id, -32601, f"Method not found: {method}")


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = _handle(request)
        except Exception as exc:
            response = _error(None, -32700, f"Invalid request: {exc}")
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
