from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from api.composition import build_api_gateway_service
from api.config import DATABASE_PATH, McpTransportSettings
from api.database.migrate import run_migrations
from api.logging_config import configure_logging
from core.logging import get_logger
from data_vault import install_default_secret_provider
from tool_registry import McpEngine
from tool_registry.catalog_reconcile import (
    reconcile_engineering_catalog,
    reconcile_wright_managed_servers,
)
from tool_registry.gateway_notifications import GatewayNotificationHub
from tool_registry.mcp_stdio import StdioGatewayBinding, serve_stdio

logger = get_logger(__name__)


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
    # The API process installs this composition dependency at import time, but
    # Hermes launches the stdio gateway as its own process. OAuth-backed remote
    # MCP servers need the same provider here to load and refresh their tokens.
    install_default_secret_provider()
    run_migrations()
    reconcile_engineering_catalog(DATABASE_PATH)
    reconcile_wright_managed_servers(DATABASE_PATH)
    settings = McpTransportSettings.from_env()
    engine = McpEngine(
        DATABASE_PATH,
        operation_timeout=settings.operation_timeout_seconds,
    )
    logger.info(
        "mcp_gateway_runtime_configured",
        operation_timeout_seconds=settings.operation_timeout_seconds,
        maximum_timeout_seconds=settings.maximum_timeout_seconds,
        lifecycle_operation_timeout_seconds=engine.lifecycle._operation_timeout,
        adapter_operation_timeout_seconds=(engine._lifecycle_adapter.operation_timeout),
    )
    # The explicit gateway binding is the source of the child workspace. Do not
    # eagerly start persisted "active" servers without it; GatewayService starts
    # the selected child lazily on the first authorized call with workspace_path.
    service = build_api_gateway_service(
        DATABASE_PATH,
        engine,
        settings,
        proxy_brep_via_api=True,
    )
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
    # stdout belongs exclusively to MCP JSON-RPC framing.
    configure_logging(stream=sys.stderr)
    asyncio.run(_serve(_arguments()))


if __name__ == "__main__":
    main()
