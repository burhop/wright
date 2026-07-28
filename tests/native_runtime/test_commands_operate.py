from __future__ import annotations

import asyncio

import pytest

from wright_engineering.hermes_plugin.commands import handle_wright
from wright_engineering.runtime.models import LifecycleResult, LifecycleState, utc_now


def _result(command: str, code: str = "ok") -> LifecycleResult:
    now = utc_now()
    return LifecycleResult(
        operation_id=f"{command}-op",
        command=command,
        ok=True,
        state=LifecycleState.STOPPED,
        code=code,
        summary=f"{command} complete",
        started_at=now,
        finished_at=now,
    )


class FakeLifecycle:
    def start(self):
        return _result("start")

    def status(self):
        return _result("status")

    def doctor(self):
        return _result("doctor")

    def stop(self):
        return _result("stop")


class FakeApi:
    def list_catalog(self):
        return [{"server_id": "cad.demo", "name": "Demo CAD", "description": "test"}]

    def install(self, server_id: str):
        return {"server_id": server_id, "installed": True}


@pytest.mark.parametrize("command", ["start", "status", "doctor", "stop"])
def test_lifecycle_commands_project_results(command: str) -> None:
    response = asyncio.run(
        handle_wright(command, lifecycle=FakeLifecycle(), api_client=FakeApi())  # type: ignore[arg-type]
    )
    assert f"{command} complete" in response


def test_open_catalog_info_and_install_use_packaged_api_projection() -> None:
    lifecycle = FakeLifecycle()
    api = FakeApi()
    opened = asyncio.run(handle_wright("open", lifecycle=lifecycle, api_client=api))  # type: ignore[arg-type]
    catalog = asyncio.run(handle_wright("catalog", lifecycle=lifecycle, api_client=api))  # type: ignore[arg-type]
    info = asyncio.run(
        handle_wright("info cad.demo", lifecycle=lifecycle, api_client=api)
    )  # type: ignore[arg-type]
    install = asyncio.run(
        handle_wright("install cad.demo", lifecycle=lifecycle, api_client=api)
    )  # type: ignore[arg-type]
    assert "http://127.0.0.1:8000/" in opened
    assert "cad.demo" in catalog
    assert "Demo CAD" in info
    assert "installed" in install.lower()


def test_catalog_failure_returns_explicit_start_instruction() -> None:
    class OfflineApi(FakeApi):
        def list_catalog(self):
            raise OSError("offline")

    response = asyncio.run(
        handle_wright("catalog", lifecycle=FakeLifecycle(), api_client=OfflineApi())  # type: ignore[arg-type]
    )
    assert "/wright start" in response
