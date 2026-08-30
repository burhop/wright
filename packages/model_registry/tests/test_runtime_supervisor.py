from __future__ import annotations

import asyncio
import os
import stat

import pytest

from model_registry.models import canonical_digest
from model_registry.runtime import (
    RuntimeAdapterRegistry,
    RuntimeFailure,
    RuntimeSession,
    RuntimeSupervisor,
)

from test_runtime_adapter import _platform, artifacts, registration


async def opened(tmp_path, *, values=None):
    supervisor = RuntimeSupervisor(
        RuntimeAdapterRegistry((registration(),)), scratch_root=tmp_path / "scratch"
    )
    system, architecture = _platform()
    session = await supervisor.start_session(
        adapter_id="wright-deterministic",
        installation_id="installation-affine",
        artifacts=values or artifacts(tmp_path),
        model_format="wright-affine-json",
        task_id="predict",
        platform=system,
        architecture=architecture,
        execution_provider="cpu",
    )
    return supervisor, session


@pytest.mark.asyncio
async def test_supervisor_applies_one_bounded_startup_deadline(
    tmp_path, monkeypatch
) -> None:
    observed: list[float] = []
    exchange = RuntimeSession._exchange

    async def record_startup_timeout(self, operation, payload, **kwargs):
        if operation == "health":
            observed.append(kwargs["timeout"])
        return await exchange(self, operation, payload, **kwargs)

    monkeypatch.setattr(RuntimeSession, "_exchange", record_startup_timeout)
    supervisor = RuntimeSupervisor(
        RuntimeAdapterRegistry((registration(),)), scratch_root=tmp_path / "scratch"
    )
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
        startup_timeout=5.0,
    )
    await session.shutdown()

    assert observed == [5.0]


@pytest.mark.asyncio
@pytest.mark.parametrize("startup_timeout", [0.0, -1.0, 30.1, float("inf")])
async def test_supervisor_rejects_unbounded_startup_deadlines(
    tmp_path, startup_timeout
) -> None:
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
            startup_timeout=startup_timeout,
        )

    assert caught.value.category == "resource_rejected"
    assert supervisor.active_process_count == 0


@pytest.mark.asyncio
async def test_supervisor_uses_clean_environment_and_confined_read_only_artifacts(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("WRIGHT_TEST_SECRET", "test-secret-value")
    supervisor, session = await opened(tmp_path)
    artifact_root = session.scratch / "artifacts"
    try:
        assert "WRIGHT_TEST_SECRET" not in supervisor.last_environment_keys
        assert set(supervisor.last_environment_keys) <= {
            "SYSTEMROOT",
            "WINDIR",
            "COMSPEC",
            "TEMP",
            "TMP",
            "PYTHONIOENCODING",
            "PYTHONUNBUFFERED",
        }
        assert (artifact_root / "model" / "coefficients.json").is_file()
        assert os.access(artifact_root / "model" / "coefficients.json", os.R_OK)
        assert await session.verify()
    finally:
        assert await session.shutdown() == "clean"
    assert not session.scratch.exists()


@pytest.mark.asyncio
async def test_verify_load_infer_unload_and_shutdown_are_bounded_and_idempotent(
    tmp_path,
) -> None:
    supervisor, session = await opened(tmp_path)
    progress = []
    try:
        verified = await session.verify(progress_callback=progress.append)
        handle = await session.load(progress_callback=progress.append)
        result = await session.infer(
            handle,
            {"x": 2.0},
            schema_digest="f" * 64,
            timeout=1,
            maximum_output_bytes=4096,
            progress_callback=progress.append,
        )
        assert verified["artifact_set_digest"] == session.artifact_set_digest
        assert result["output"] == {"y": 5.0}
        assert result["output_digest"] == canonical_digest({"y": 5.0})
        assert all(len(item.message) <= 512 for item in progress)
        await session.unload(handle)
        await session.unload(handle)
    finally:
        assert await session.shutdown() == "clean"
        assert await session.shutdown() == "clean"
    assert supervisor.active_process_count == 0


@pytest.mark.asyncio
async def test_missing_corrupt_and_unsafe_artifacts_fail_closed(tmp_path) -> None:
    _, missing_session = await opened(tmp_path)
    missing = missing_session.scratch / "artifacts" / "model" / "coefficients.json"
    missing.parent.chmod(stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
    missing.chmod(0o600)
    missing.unlink()
    with pytest.raises(RuntimeFailure) as caught:
        await missing_session.verify()
    assert caught.value.category == "artifact_missing"
    await missing_session.shutdown()

    _, corrupt_session = await opened(tmp_path / "corrupt")
    corrupt = corrupt_session.scratch / "artifacts" / "model" / "coefficients.json"
    corrupt.parent.chmod(stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)
    corrupt.chmod(0o600)
    corrupt.write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeFailure) as caught:
        await corrupt_session.verify()
    assert caught.value.category == "artifact_invalid"
    await corrupt_session.shutdown()

    supervisor = RuntimeSupervisor(
        RuntimeAdapterRegistry((registration(),)), scratch_root=tmp_path / "unsafe"
    )
    system, architecture = _platform()
    with pytest.raises(RuntimeFailure) as caught:
        await supervisor.start_session(
            adapter_id="wright-deterministic",
            installation_id="installation-affine",
            artifacts={
                "../outside": next(iter(artifacts(tmp_path / "outside").values()))
            },
            model_format="wright-affine-json",
            task_id="predict",
            platform=system,
            architecture=architecture,
            execution_provider="cpu",
        )
    assert caught.value.category == "artifact_invalid"


@pytest.mark.asyncio
async def test_declared_artifact_resource_ceiling_is_enforced_before_launch(
    tmp_path,
) -> None:
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
            maximum_artifact_bytes=1,
        )
    assert caught.value.category == "resource_rejected"
    assert supervisor.active_process_count == 0


@pytest.mark.asyncio
async def test_resource_reservations_are_atomic_and_release_after_shutdown(
    tmp_path,
) -> None:
    supervisor = RuntimeSupervisor(
        RuntimeAdapterRegistry((registration(),)),
        scratch_root=tmp_path / "scratch",
        maximum_reserved_ram_bytes=3,
        maximum_reserved_disk_bytes=3,
    )
    system, architecture = _platform()

    async def start(installation_id: str):
        return await supervisor.start_session(
            adapter_id="wright-deterministic",
            installation_id=installation_id,
            artifacts=artifacts(tmp_path / installation_id),
            model_format="wright-affine-json",
            task_id="predict",
            platform=system,
            architecture=architecture,
            execution_provider="cpu",
            required_ram_bytes=2,
            required_disk_bytes=2,
        )

    first = await start("installation-first")
    assert supervisor.active_resource_reservations == (2, 2)
    with pytest.raises(RuntimeFailure) as caught:
        await start("installation-conflict")
    assert caught.value.category == "resource_rejected"
    assert supervisor.active_resource_reservations == (2, 2)

    await first.shutdown()
    assert supervisor.active_resource_reservations == (0, 0)
    replacement = await start("installation-replacement")
    await replacement.shutdown()
    assert supervisor.active_resource_reservations == (0, 0)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("fault", "maximum", "category"),
    [
        ("nonfinite", 4096, "output_invalid"),
        ("oversized", 128, "output_invalid"),
        ("bad_progress", 4096, "output_invalid"),
    ],
)
async def test_invalid_output_and_progress_never_cross_the_boundary(
    tmp_path, fault, maximum, category
) -> None:
    _, session = await opened(tmp_path)
    try:
        await session.verify()
        handle = await session.load()
        with pytest.raises(RuntimeFailure) as caught:
            await session.infer(
                handle,
                {"x": 2},
                schema_digest="f" * 64,
                timeout=1,
                maximum_output_bytes=maximum,
                fault_profile=fault,
            )
        assert caught.value.category == category
    finally:
        await session.shutdown()


@pytest.mark.asyncio
async def test_deadline_crash_and_oversized_request_terminate_without_late_output(
    tmp_path,
) -> None:
    supervisor, session = await opened(tmp_path / "timeout")
    handle = await session.load()
    with pytest.raises(RuntimeFailure) as caught:
        await session.infer(
            handle,
            {"x": 2},
            schema_digest="f" * 64,
            timeout=0.02,
            maximum_output_bytes=4096,
            fault_profile="late",
        )
    assert caught.value.category == "runtime_timeout"
    assert supervisor.active_process_count == 0
    await session.shutdown()

    _, crash_session = await opened(tmp_path / "crash")
    with pytest.raises(RuntimeFailure) as caught:
        await crash_session.verify(fault_profile="crash")
    assert caught.value.category == "runtime_unhealthy"
    await crash_session.shutdown()

    _, large_session = await opened(tmp_path / "large")
    handle = await large_session.load()
    with pytest.raises(RuntimeFailure) as caught:
        await large_session.infer(
            handle,
            {"x": "x" * (1024 * 1024)},
            schema_digest="f" * 64,
            timeout=1,
            maximum_output_bytes=4096,
        )
    assert caught.value.category == "input_invalid"
    await large_session.shutdown()


@pytest.mark.asyncio
async def test_absolute_deadline_is_not_extended_by_continuous_progress(
    tmp_path,
) -> None:
    supervisor, session = await opened(tmp_path)
    handle = await session.load()
    with pytest.raises(RuntimeFailure) as caught:
        await session.infer(
            handle,
            {"x": 2},
            schema_digest="f" * 64,
            timeout=0.05,
            maximum_output_bytes=4096,
            fault_profile="progress_forever",
        )
    assert caught.value.category == "runtime_timeout"
    assert supervisor.active_process_count == 0
    await session.shutdown()


@pytest.mark.asyncio
async def test_cooperative_cancellation_wins_and_cleanup_has_no_residue(
    tmp_path,
) -> None:
    supervisor, session = await opened(tmp_path)
    handle = await session.load()
    inference = asyncio.create_task(
        session.infer(
            handle,
            {"x": 2},
            schema_digest="f" * 64,
            timeout=5,
            maximum_output_bytes=4096,
            fault_profile="slow",
        )
    )
    for _ in range(100):
        if session._current_request_id:
            break
        await asyncio.sleep(0)
    await session.cancel_current(grace_seconds=0.1)
    with pytest.raises(RuntimeFailure) as caught:
        await inference
    assert caught.value.category == "cancelled"
    assert await session.shutdown() == "clean"
    assert supervisor.active_process_count == 0
    assert not tuple((tmp_path / "scratch").glob("runtime-*"))


@pytest.mark.asyncio
async def test_cancellation_wins_over_a_child_success_emitted_during_grace(
    tmp_path,
) -> None:
    _, session = await opened(tmp_path)
    handle = await session.load()
    inference = asyncio.create_task(
        session.infer(
            handle,
            {"x": 2},
            schema_digest="f" * 64,
            timeout=1,
            maximum_output_bytes=4096,
            fault_profile="late_short",
        )
    )
    for _ in range(100):
        if session._current_request_id:
            break
        await asyncio.sleep(0)
    await session.cancel_current(grace_seconds=0.1)
    with pytest.raises(RuntimeFailure) as caught:
        await inference
    assert caught.value.category == "cancelled"
    assert await session.shutdown() == "clean"
