from __future__ import annotations

from pathlib import Path

from wright_engineering.runtime.layout import NativeLayout
from wright_engineering.runtime.lifecycle import NativeLifecycle
from wright_engineering.runtime.models import LifecycleState


def _lifecycle(tmp_path: Path, **kwargs) -> NativeLifecycle:
    return NativeLifecycle(
        NativeLayout.from_wright_home(tmp_path / "wright-home"),
        manager_id="cli",
        adapter_protocol="wright-lifecycle-v1",
        **kwargs,
    )


def test_status_is_read_only_and_reports_required_surfaces(tmp_path: Path) -> None:
    lifecycle = _lifecycle(
        tmp_path,
        status_probes={
            "manager": lambda: {"ok": True},
            "mcp": lambda: {"ok": True, "transport": "streamable-http"},
            "catalog": lambda: {"ok": True, "entries": 45},
            "configuration": lambda: {"ok": True},
            "workspaces": lambda: {"ok": True, "count": 2},
        },
    )
    assert not lifecycle.store.manifest_path.exists()
    result = lifecycle.status()

    assert result.ok
    assert result.state is LifecycleState.NOT_INSTALLED
    assert not lifecycle.store.manifest_path.exists()
    assert {
        "runtime_distribution_version",
        "manager_id",
        "adapter_protocol",
        "state",
        "compatibility",
        "data_root",
        "api_healthy",
        "ui_healthy",
        "manager",
        "mcp",
        "catalog",
        "configuration",
        "workspaces",
    }.issubset(result.details)


def test_doctor_distinguishes_core_checks_and_external_services(tmp_path: Path) -> None:
    lifecycle = _lifecycle(
        tmp_path,
        status_probes={
            "manager": lambda: {"ok": True},
            "mcp": lambda: {"ok": True},
            "catalog": lambda: {"ok": True},
            "configuration": lambda: {"ok": True},
            "workspaces": lambda: {"ok": True},
        },
        doctor_probes={
            "backup": lambda: {"ok": True},
            "optional_external_mcp": lambda: {
                "ok": False,
                "required_for_core": False,
                "summary": "Solid Edge is not installed",
            },
        },
    )
    result = lifecycle.doctor()
    assert result.command == "doctor"
    assert "checks" in result.details
    assert result.details["checks"]["data_permissions"]["ok"] is True
    assert result.details["optional"]["optional_external_mcp"]["ok"] is False
    assert (
        "Solid Edge" in result.details["optional"]["optional_external_mcp"]["summary"]
    )


def test_status_redacts_probe_secrets(tmp_path: Path) -> None:
    lifecycle = _lifecycle(
        tmp_path,
        status_probes={"configuration": lambda: {"ok": False, "token": "leak"}},
    )
    assert "leak" not in repr(lifecycle.status().to_dict())
