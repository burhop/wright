from __future__ import annotations

from types import SimpleNamespace

import pytest

from api import gateway_stdio


@pytest.mark.asyncio
async def test_stdio_gateway_installs_secret_provider_before_runtime(
    monkeypatch,
) -> None:
    events: list[str] = []

    class FakeEngine:
        def __init__(self, *_args, **_kwargs) -> None:
            self.lifecycle = SimpleNamespace(_operation_timeout=30.0)
            self._lifecycle_adapter = SimpleNamespace(operation_timeout=30.0)

    class FakeService:
        notifier = None

        async def shutdown(self) -> None:
            events.append("shutdown")

    def install_secret_provider() -> None:
        events.append("secrets")

    def build_service(*_args, **_kwargs):
        events.append("build")
        return FakeService()

    async def serve(_service, _binding) -> None:
        events.append("serve")

    monkeypatch.delenv("WRIGHT_MCP_COMPATIBILITY_PROBE", raising=False)
    monkeypatch.setattr(
        gateway_stdio, "install_default_secret_provider", install_secret_provider
    )
    monkeypatch.setattr(gateway_stdio, "run_migrations", lambda: None)
    monkeypatch.setattr(gateway_stdio, "reconcile_engineering_catalog", lambda _db: 0)
    monkeypatch.setattr(gateway_stdio, "reconcile_wright_managed_servers", lambda _db: 0)
    monkeypatch.setattr(
        gateway_stdio.McpTransportSettings,
        "from_env",
        lambda: SimpleNamespace(
            operation_timeout_seconds=30.0,
            maximum_timeout_seconds=120.0,
        ),
    )
    monkeypatch.setattr(gateway_stdio, "McpEngine", FakeEngine)
    monkeypatch.setattr(gateway_stdio, "build_api_gateway_service", build_service)
    monkeypatch.setattr(gateway_stdio, "serve_stdio", serve)

    await gateway_stdio._serve(
        SimpleNamespace(
            session_id="session-1",
            principal_id="principal-1",
            workspace_id="workspace-1",
        )
    )

    assert events == ["secrets", "build", "serve", "shutdown"]
