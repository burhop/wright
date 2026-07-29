from __future__ import annotations

import asyncio
from pathlib import Path

from .adapter_support import load_adapter_commands


ROOT = Path(__file__).resolve().parents[2]
COMMANDS = load_adapter_commands()


def _invoke(command: str, argument: str | None) -> dict[str, object]:
    assert command == "start"
    assert argument is None
    return {
        "ok": True,
        "code": "ok",
        "summary": "Wright is healthy.",
        "details": {"ui_url": "http://127.0.0.1:8000/"},
        "remediation": [],
    }


def test_start_command_projects_structured_lifecycle_result() -> None:
    response = asyncio.run(COMMANDS.handle_wright("start", invoker=_invoke))
    assert "OK [ok]" in response
    assert "http://127.0.0.1:8000/" in response


def test_native_command_layer_contains_no_repo_or_frontend_build_fallback() -> None:
    sources = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in (
            "hermes-plugin-wright/bootstrap.py",
            "hermes-plugin-wright/commands.py",
            "src/wright_engineering/runtime/lifecycle.py",
        )
    ).lower()
    for forbidden in (
        "detect_repo_dir",
        "npm run",
        "apps/web",
        "git clone",
        "docker compose",
    ):
        assert forbidden not in sources
