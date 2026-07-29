from __future__ import annotations

import asyncio

import pytest

from .adapter_support import load_adapter_commands


COMMANDS = load_adapter_commands()


def _invoke(command: str, argument: str | None) -> dict[str, object]:
    return {
        "ok": True,
        "code": "ok",
        "summary": f"{command} complete",
        "details": {},
        "remediation": [],
    }


class FakeApi:
    def list_catalog(self):
        return [{"server_id": "cad.demo", "name": "Demo CAD", "description": "test"}]

    def install(self, server_id: str):
        return {"server_id": server_id, "installed": True}


@pytest.mark.parametrize("command", ["start", "status", "doctor", "stop"])
def test_lifecycle_commands_project_results(command: str) -> None:
    response = asyncio.run(COMMANDS.handle_wright(command, invoker=_invoke))
    assert f"{command} complete" in response


def test_open_catalog_info_and_install_use_packaged_api_projection() -> None:
    api = FakeApi()
    opened = asyncio.run(COMMANDS.handle_wright("open", api_client=api))
    catalog = asyncio.run(COMMANDS.handle_wright("catalog", api_client=api))
    info = asyncio.run(COMMANDS.handle_wright("info cad.demo", api_client=api))
    install = asyncio.run(COMMANDS.handle_wright("install cad.demo", api_client=api))
    assert "http://127.0.0.1:8000/" in opened
    assert "cad.demo" in catalog
    assert "Demo CAD" in info
    assert "installed" in install.lower()


def test_catalog_failure_returns_explicit_start_instruction() -> None:
    class OfflineApi(FakeApi):
        def list_catalog(self):
            raise OSError("offline")

    response = asyncio.run(COMMANDS.handle_wright("catalog", api_client=OfflineApi()))
    assert "/wright start" in response
