from __future__ import annotations

import asyncio
from pathlib import Path

from wright_engineering.hermes_plugin.commands import handle_wright
from wright_engineering.runtime.models import (
    LifecycleResult,
    LifecycleState,
    utc_now,
)


ROOT = Path(__file__).resolve().parents[2]


class FakeLifecycle:
    def start(self) -> LifecycleResult:
        now = utc_now()
        return LifecycleResult(
            operation_id="op-1",
            command="start",
            ok=True,
            state=LifecycleState.HEALTHY,
            code="ok",
            summary="Wright is healthy.",
            details={"ui_url": "http://127.0.0.1:8000/"},
            started_at=now,
            finished_at=now,
        )


def test_start_command_projects_structured_lifecycle_result() -> None:
    response = asyncio.run(handle_wright("start", lifecycle=FakeLifecycle()))  # type: ignore[arg-type]
    assert "OK [ok]" in response
    assert "http://127.0.0.1:8000/" in response


def test_native_command_layer_contains_no_repo_or_frontend_build_fallback() -> None:
    sources = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in (
            "src/wright_engineering/hermes_plugin/commands.py",
            "src/wright_engineering/runtime/lifecycle.py",
        )
    ).lower()
    for forbidden in (
        "detect_repo_dir",
        "wright_repo_dir",
        "npm run",
        "apps/web",
        "git clone",
        "docker compose",
    ):
        assert forbidden not in sources
