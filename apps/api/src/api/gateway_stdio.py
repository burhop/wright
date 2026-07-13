from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from api.composition import build_api_gateway_service
from api.config import DATABASE_PATH, McpTransportSettings
from api.database.migrate import run_migrations
from tool_registry import McpEngine
from tool_registry.catalog_reconcile import reconcile_engineering_catalog
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.mcp_stdio import StdioGatewayBinding, serve_stdio


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Wright MCP 2025-11-25 STDIO server")
    parser.add_argument(
        "--session-id", default=os.getenv("WRIGHT_MCP_SESSION_ID"), required=False
    )
    parser.add_argument(
        "--workspace-id", default=os.getenv("WRIGHT_MCP_WORKSPACE_ID"), required=False
    )
    parser.add_argument(
        "--principal-id",
        default=os.getenv("WRIGHT_MCP_PRINCIPAL_ID") or f"stdio:{os.getpid()}",
    )
    values = parser.parse_args()
    if not values.session_id or not values.workspace_id:
        parser.error("--session-id and --workspace-id are required")
    return values


async def _serve(values: argparse.Namespace) -> None:
    run_migrations()
    reconcile_engineering_catalog(DATABASE_PATH)
    engine = McpEngine(DATABASE_PATH)
    await engine.sync_active_servers()
    settings = McpTransportSettings.from_env()
    service = build_api_gateway_service(DATABASE_PATH, engine, settings)
    service.notifier = GatewayNotificationHub()
    probe_task = None
    probe_path = os.getenv("WRIGHT_MCP_COMPATIBILITY_PROBE")
    if probe_path:

        async def publish_probe() -> None:
            while service.notifier.subscriber_count(values.workspace_id) == 0:
                await asyncio.sleep(0.01)
            service.notifier.publish(
                workspace_id=values.workspace_id, event="tools/list_changed"
            )
            Path(probe_path).write_text("tools/list_changed\n", encoding="utf-8")

        probe_task = asyncio.create_task(publish_probe())
    try:
        await serve_stdio(
            service,
            StdioGatewayBinding(
                values.session_id,
                values.principal_id,
                values.workspace_id,
            ),
        )
    finally:
        if probe_task is not None:
            probe_task.cancel()
            await asyncio.gather(probe_task, return_exceptions=True)
        await service.shutdown()


def main() -> None:
    asyncio.run(_serve(_arguments()))


if __name__ == "__main__":
    main()
