from __future__ import annotations

import json
import platform
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from model_registry.runtime import (
    AdapterRegistration,
    RuntimeAdapterRegistry,
    RuntimeFailure,
    RuntimeSupervisor,
)


ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "tests" / "fixtures" / "engineering_model_runtime.py"


def _platform() -> tuple[str, str]:
    systems = {"darwin": "macos", "linux": "linux", "windows": "windows"}
    machines = {
        "amd64": "x86_64",
        "x86_64": "x86_64",
        "arm64": "aarch64",
        "aarch64": "aarch64",
    }
    return systems[platform.system().lower()], machines[platform.machine().lower()]


def registration() -> AdapterRegistration:
    system, architecture = _platform()
    return AdapterRegistration(
        adapter_id="wright-deterministic",
        adapter_version="1.0.0",
        contract_version="1.0",
        command=(sys.executable, "-I", str(FIXTURE)),
        formats=frozenset({"wright-affine-json"}),
        tasks=frozenset({"predict"}),
        platforms=frozenset({system}),
        architectures=frozenset({architecture}),
        execution_providers=frozenset({"cpu"}),
    )


def artifacts(tmp_path: Path) -> dict[str, Path]:
    values = {
        "model/coefficients.json": json.dumps(
            {"offset": 1.0, "scale": 2.0}, sort_keys=True, separators=(",", ":")
        ).encode(),
        "LICENSE": b"test license",
    }
    result = {}
    for key, value in values.items():
        path = tmp_path / "source" / Path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
        result[key] = path
    return result


def test_registry_rejects_duplicate_or_invalid_adapter_identity() -> None:
    registry = RuntimeAdapterRegistry()
    registry.register(registration())
    with pytest.raises(RuntimeFailure, match="already registered"):
        registry.register(registration())
    with pytest.raises(RuntimeFailure, match="command"):
        registry.register(replace(registration(), command=()))


@pytest.mark.asyncio
async def test_health_identity_contract_and_supported_dimensions_are_verified(
    tmp_path,
) -> None:
    registry = RuntimeAdapterRegistry((registration(),))
    supervisor = RuntimeSupervisor(registry, scratch_root=tmp_path / "scratch")
    system, architecture = _platform()
    session = await supervisor.start_session(
        adapter_id="wright-deterministic",
        installation_id="installation-affine",
        artifacts=artifacts(tmp_path),
        model_format="wright-affine-json",
        task_id="predict",
        platform=system,
        architecture=architecture,
        execution_provider="cpu",
    )
    try:
        assert session.descriptor.adapter_id == "wright-deterministic"
        assert session.descriptor.adapter_version == "1.0.0"
        assert session.descriptor.contract_version == "1.0"
        assert session.descriptor.health == "healthy"
        progress = []
        result = await session.verify(
            progress_callback=lambda event: progress.append(event)
        )
        assert result["verified"] is True
        assert [event.sequence for event in progress] == [1, 2]
    finally:
        await session.shutdown()
    assert supervisor.active_process_count == 0


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("field", "value", "category"),
    [
        ("model_format", "unsafe-pickle", "unsupported_format"),
        ("task_id", "mesh", "unsupported_task"),
        ("platform", "plan9", "incompatible_provider"),
        ("architecture", "mips", "incompatible_provider"),
        ("execution_provider", "cuda", "incompatible_provider"),
    ],
)
async def test_unsupported_runtime_dimensions_fail_before_load(
    tmp_path, field, value, category
) -> None:
    system, architecture = _platform()
    values = {
        "model_format": "wright-affine-json",
        "task_id": "predict",
        "platform": system,
        "architecture": architecture,
        "execution_provider": "cpu",
    }
    values[field] = value
    supervisor = RuntimeSupervisor(
        RuntimeAdapterRegistry((registration(),)), scratch_root=tmp_path / "scratch"
    )
    with pytest.raises(RuntimeFailure) as caught:
        await supervisor.start_session(
            adapter_id="wright-deterministic",
            installation_id="installation-affine",
            artifacts=artifacts(tmp_path),
            **values,
        )
    assert caught.value.category == category
    assert supervisor.active_process_count == 0


@pytest.mark.asyncio
async def test_child_health_identity_mismatch_fails_closed(tmp_path) -> None:
    supervisor = RuntimeSupervisor(
        RuntimeAdapterRegistry((registration(),)), scratch_root=tmp_path / "scratch"
    )
    system, architecture = _platform()
    with pytest.raises(RuntimeFailure) as caught:
        await supervisor.start_session(
            adapter_id="wright-deterministic",
            installation_id="installation-affine",
            artifacts=artifacts(tmp_path),
            model_format="wright-affine-json",
            task_id="predict",
            platform=system,
            architecture=architecture,
            execution_provider="cpu",
            health_fault_profile="bad_identity",
        )
    assert caught.value.category == "runtime_unhealthy"
    assert supervisor.active_process_count == 0
