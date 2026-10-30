from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from tests.native_runtime.adapter_support import load_adapter_commands


COMMANDS = load_adapter_commands()


def test_commands_register_real_wright_dispatcher() -> None:
    context = MagicMock()
    COMMANDS.register_commands(context)
    context.register_command.assert_called_once()
    kwargs = context.register_command.call_args.kwargs
    assert kwargs["name"] == "wright"
    assert asyncio.run(kwargs["handler"]("")) == COMMANDS.WRIGHT_HELP_TEXT


def test_commands_contain_no_repository_or_build_fallback() -> None:
    source = open(COMMANDS.__file__, encoding="utf-8").read().lower()
    for forbidden in ("detect_repo_dir", "npm run", "git clone", "docker compose"):
        assert forbidden not in source


def test_start_reports_missing_hermes_sdk_without_changing_lifecycle_or_installing(
    monkeypatch,
):
    monkeypatch.setattr(COMMANDS.importlib.util, "find_spec", lambda _: None)
    monkeypatch.setattr(COMMANDS.importlib.metadata, "version", lambda _: "0.19.0")
    invoker = MagicMock(return_value={"ok": True, "code": "ok", "summary": "Started"})
    result = asyncio.run(COMMANDS.handle_wright("start", invoker=invoker))
    assert result.startswith("OK [ok] Started")
    assert "missing_mcp_client" in result
    assert "hermes-agent[mcp]==0.19.0" in result
    assert "No dependency was installed" in result
    assert "separately running Hermes gateway" in result
    invoker.assert_called_once_with("start", None)


def test_host_mcp_readiness_does_not_claim_ready_from_sdk_presence(monkeypatch):
    monkeypatch.setattr(COMMANDS.importlib.util, "find_spec", lambda _: object())
    assert COMMANDS.host_mcp_readiness() == ""


def test_missing_sdk_and_unknown_hermes_version_explains_manual_recovery(monkeypatch):
    monkeypatch.setattr(COMMANDS.importlib.util, "find_spec", lambda _: None)

    def unavailable(_):
        raise COMMANDS.importlib.metadata.PackageNotFoundError()

    monkeypatch.setattr(COMMANDS.importlib.metadata, "version", unavailable)
    result = COMMANDS.host_mcp_readiness()
    assert "missing_mcp_client" in result
    assert "supported setup" in result
    assert "pip install" not in result
