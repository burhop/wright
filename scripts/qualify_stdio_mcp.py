#!/usr/bin/env python3
"""Run a small, evidence-producing stdio MCP qualification through Wright.

This helper is intended to run inside a disposable Wright container. It starts
one pinned MCP command through McpEngine, calls one safe tool directly, repeats
that call through GatewayService, and writes a redacted evidence summary.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import time
from typing import Any

from tool_registry import McpServer
from tool_registry.gateway_models import GatewayTool
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.gateway_service import GatewayService, SUPPORTED_PROTOCOL_VERSION
from tool_registry.runners.stdio import StdioRunner


class _Workspaces:
    def __init__(self, path: Path, server_id: str) -> None:
        self.path = path
        self.server_id = server_id

    def resolve_binding(self, *, session_id: str, principal_id: str, workspace_id: str):
        return {
            "session_id": session_id,
            "principal_id": principal_id,
            "workspace_id": workspace_id,
            "workspace_path": str(self.path),
        }

    def enabled_server_ids(self, _session):
        return {self.server_id}


class _Audit:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def record(self, event) -> None:
        self.events.append(dict(event))


class _Catalog:
    def __init__(self, server: McpServer, tools: list[dict[str, Any]]) -> None:
        self.server = server
        self._tools = tuple(
            GatewayTool(
                name=f"{server.server_id}__{tool['name']}",
                server_id=server.server_id,
                tool_name=tool["name"],
                description=tool.get("description") or "",
                input_schema=tool.get("inputSchema") or {},
                title=tool.get("title"),
                output_schema=tool.get("outputSchema"),
                annotations=tool.get("annotations") or {},
                upstream_meta=tool.get("_meta") or {},
                provenance={"source_url": server.source_url},
            )
            for tool in tools
        )

    def servers(self):
        return (self.server,)

    def tools(self, server_id: str):
        return self._tools if server_id == self.server.server_id else ()

    def resources(self, _session):
        return ()


class _Lifecycle:
    def __init__(self, runner: StdioRunner) -> None:
        self.runner = runner

    def lifecycle_projection(self, _server_id: str):
        return {
            "kind": "ordinary",
            "visible_application": False,
            "cancellation_supported": True,
            "recovery_action": None,
        }

    async def ensure_started(self, *_args, **_kwargs) -> None:
        if not self.runner.is_running():
            await self.runner.start()

    async def call_tool(
        self,
        _server_id: str,
        tool_name: str,
        arguments,
        *,
        approval_context,
        progress_callback=None,
    ):
        return await self.runner.call_tool(
            tool_name, dict(arguments), progress_callback=progress_callback
        )

    async def shutdown(self) -> None:
        await self.runner.stop()


def _digest(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--command-json", required=True)
    parser.add_argument("--env-json", default="{}")
    parser.add_argument("--safe-tool", required=True)
    parser.add_argument("--safe-arguments-json", default="{}")
    parser.add_argument("--expected-tool-count", type=int)
    parser.add_argument("--container-image", required=True)
    parser.add_argument("--environment", default="clean-wright-container")
    parser.add_argument("--platform", default="linux_x64")
    parser.add_argument("--workspace", default="/tmp/wright-mcp-qualification")
    parser.add_argument("--package-integrity")
    parser.add_argument("--browser-url")
    parser.add_argument("--browser-wait-seconds", type=float, default=8.0)
    parser.add_argument("--evidence", required=True)
    return parser.parse_args()


async def _run(args: argparse.Namespace) -> dict[str, Any]:
    command = json.loads(args.command_json)
    launch_env = json.loads(args.env_json)
    safe_arguments = json.loads(args.safe_arguments_json)
    if not isinstance(command, list) or not all(
        isinstance(item, str) for item in command
    ):
        raise ValueError("--command-json must be a JSON string array")
    if not isinstance(safe_arguments, dict):
        raise ValueError("--safe-arguments-json must be a JSON object")
    if not isinstance(launch_env, dict) or not all(
        isinstance(key, str) and isinstance(value, str)
        for key, value in launch_env.items()
    ):
        raise ValueError("--env-json must be a JSON string map")

    started = time.time()
    workspace = Path(args.workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    server = McpServer(
        server_id=args.server_id,
        name=args.name,
        type="stdio",
        command=command,
        is_active=True,
        is_installed=True,
        status="active",
        created_at=now,
        updated_at=now,
        source_url=args.source_url,
        installed_version=args.source_revision,
        verification_state="verified_docs_mcp",
        installability_tier="might_work",
        risk_level="read-only",
        default_enabled=False,
    )
    runner = StdioRunner(
        command, env=launch_env, cwd=str(workspace), operation_timeout=60
    )
    audit = _Audit()
    playwright = None
    browser = None
    browser_observation = None
    try:
        await runner.start()
        if args.browser_url:
            from playwright.async_api import async_playwright

            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            page.on(
                "console", lambda message: print(f"browser-console: {message.text}")
            )
            page.on(
                "pageerror",
                lambda error: print(f"browser-pageerror: {type(error).__name__}"),
            )
            await page.goto(args.browser_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(args.browser_wait_seconds * 1000)
            browser_observation = await page.evaluate(
                """async () => {
                  const context = navigator.modelContext;
                  if (!context) return { hasModelContext: false, toolCount: 0 };
                  const result = await context.listTools();
                  const tools = Array.isArray(result) ? result : (result.tools || []);
                  return {
                    hasModelContext: true,
                    toolCount: tools.length,
                    toolNames: tools.map((tool) => tool.name).sort(),
                    title: document.title,
                  };
                }"""
            )
            print(
                "browser-observation: "
                + json.dumps(browser_observation, sort_keys=True)
            )
        tools = await runner.list_tools()
        names = sorted(tool["name"] for tool in tools)
        if args.safe_tool not in names:
            raise RuntimeError(f"safe tool {args.safe_tool!r} was not listed")
        if (
            args.expected_tool_count is not None
            and len(names) != args.expected_tool_count
        ):
            raise RuntimeError(
                f"expected {args.expected_tool_count} tools, observed {len(names)}"
            )

        direct = await runner.call_tool(args.safe_tool, safe_arguments)
        direct_payload = direct.get("structuredContent") or direct.get("content")
        direct_digest = _digest(direct_payload)

        gateway = GatewayService(
            workspaces=_Workspaces(workspace, args.server_id),
            catalog=_Catalog(server, tools),
            lifecycle=_Lifecycle(runner),
            audit=audit,
            notifier=GatewayNotificationHub(),
            operation_timeout=60,
        )
        gateway.open_session(
            session_id="qualification",
            principal_id="wright-validator",
            workspace_id="qualification-workspace",
            transport="stdio",
        )
        gateway.initialize_session(
            "qualification",
            protocol_version=SUPPORTED_PROTOCOL_VERSION,
            client_name="wright-qualification",
            client_version="1",
            client_capabilities={},
        )
        gateway_tools = sorted(
            tool.name for tool in gateway.list_tools("qualification")
        )
        qualified_name = f"{args.server_id}__{args.safe_tool}"
        if qualified_name not in gateway_tools:
            raise RuntimeError(f"gateway did not list {qualified_name!r}")
        gateway_result = await gateway.call_tool(
            "qualification", "safe-call", qualified_name, safe_arguments
        )
        gateway_payload = gateway_result.structured_content or list(
            gateway_result.content
        )
        gateway_digest = _digest(gateway_payload)
        if gateway_digest != direct_digest:
            raise RuntimeError("direct and gateway safe-tool results differed")

        return {
            "server_id": args.server_id,
            "observed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started)),
            "finished_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "duration_seconds": round(time.time() - started, 3),
            "environment": args.environment,
            "platform": args.platform,
            "source_url": args.source_url,
            "source_revision": args.source_revision,
            "container_image": args.container_image,
            "package_integrity": args.package_integrity,
            "status": "passed",
            "steps": [
                {"stage": "direct_protocol_and_discovery", "status": "passed"},
                {"stage": "direct_safe_backend_call", "status": "passed"},
                {"stage": "wright_gateway_discovery", "status": "passed"},
                {"stage": "wright_gateway_safe_backend_call", "status": "passed"},
            ],
            "tool_count": len(names),
            "tool_schema_sha256": _digest(
                [
                    {
                        "name": tool["name"],
                        "input_schema": tool.get("inputSchema") or {},
                    }
                    for tool in tools
                ]
            ),
            "safe_tool": args.safe_tool,
            "safe_result_sha256": direct_digest,
            "gateway_tool_count": len(gateway_tools),
            "gateway_result_sha256": gateway_digest,
            "audit_event_count": len(audit.events),
            "browser_observation": browser_observation,
            "cleanup": "pending",
            "limitations": [
                "This run proves the selected read-only scope; it does not establish repeat user adoption."
            ],
        }
    finally:
        if browser is not None:
            await browser.close()
        if playwright is not None:
            await playwright.stop()
        await runner.stop()


def main() -> int:
    args = _parse_args()
    evidence_path = Path(args.evidence)
    try:
        result = asyncio.run(_run(args))
        result["cleanup"] = "passed"
    except Exception as exc:
        result = {
            "server_id": args.server_id,
            "status": "failed",
            "diagnostic": f"{type(exc).__name__}: {exc}",
            "cleanup": "attempted",
        }
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
