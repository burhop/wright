from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from workspace_service.surfaces.process_supervisor import (
    PlatformProcessIdentity,
    ProcessStopResult,
    ProcessSupervisor,
    ProcessSupervisorError,
)


pytestmark = [pytest.mark.workspace_surfaces, pytest.mark.asyncio]


class FakeProcess:
    def __init__(self) -> None:
        self.identity = PlatformProcessIdentity(
            adapter="fake",
            pid=321,
            creation_time=55.0,
            containment_id="group-321",
            containment_mode="hard",
        )
        self._exit = asyncio.Event()
        self.stop_calls = 0

    async def stdout(self):
        yield b"started token=test-secret-value\n"

    async def stderr(self):
        yield b"warning\n"

    async def wait(self) -> int:
        await self._exit.wait()
        return 0

    async def stop(self, *, deadline: datetime) -> ProcessStopResult:
        self.stop_calls += 1
        self._exit.set()
        return ProcessStopResult(
            exit_code=0,
            graceful=True,
            forced=False,
            descendants_remaining=(),
            listeners_remaining=(),
        )


class FakeAdapter:
    def __init__(self) -> None:
        self.launches = []
        self.process = FakeProcess()

    async def launch(self, request):
        self.launches.append(request)
        return self.process


async def test_async_start_is_argv_only_idempotent_and_captures_redacted_logs(
    tmp_path,
) -> None:
    adapter = FakeAdapter()
    supervisor = ProcessSupervisor(adapter=adapter, id_factory=lambda: "runtime-1")
    arguments = dict(
        workspace_id="workspace-1",
        instance_id="instance-1",
        generation=1,
        argv=("python", "app.py"),
        cwd=str(tmp_path),
        environment={"API_TOKEN": "test-secret-value"},
        secret_environment_names=frozenset({"API_TOKEN"}),
        redaction_query_names=frozenset({"token"}),
        limits={
            "captured_log_bytes": 4096,
            "captured_log_bytes_per_second": 4096,
            "captured_log_burst_bytes": 4096,
        },
        idempotency_key="start-1",
    )

    first = await supervisor.start(**arguments)
    second = await supervisor.start(**arguments)
    await asyncio.sleep(0)

    assert first == second
    assert first.runtime_id == "runtime-1"
    assert first.identity.pid == 321
    assert len(adapter.launches) == 1
    assert adapter.launches[0].argv == ("python", "app.py")
    assert adapter.launches[0].shell is False
    assert adapter.launches[0].environment["API_TOKEN"] == "secret-value"
    assert "secret-value" not in str(first)
    preview = supervisor.diagnostics("runtime-1")["logs"]["preview"]
    assert "secret-value" not in preview
    assert "[REDACTED]" in preview


async def test_stop_is_generation_checked_idempotent_and_awaits_tree_cleanup(
    tmp_path,
) -> None:
    adapter = FakeAdapter()
    supervisor = ProcessSupervisor(adapter=adapter, id_factory=lambda: "runtime-2")
    snapshot = await supervisor.start(
        workspace_id="workspace-1",
        instance_id="instance-2",
        generation=4,
        argv=("python", "app.py"),
        cwd=str(tmp_path),
        environment={},
        secret_environment_names=frozenset(),
        redaction_query_names=frozenset(),
        limits={
            "captured_log_bytes": 4096,
            "captured_log_bytes_per_second": 4096,
            "captured_log_burst_bytes": 4096,
        },
        idempotency_key="start-2",
    )
    deadline = datetime.now(UTC) + timedelta(seconds=5)

    with pytest.raises(ProcessSupervisorError, match="generation"):
        await supervisor.stop(
            runtime_id=snapshot.runtime_id, generation=3, deadline=deadline
        )
    stopped = await supervisor.stop(
        runtime_id=snapshot.runtime_id, generation=4, deadline=deadline
    )
    repeated = await supervisor.stop(
        runtime_id=snapshot.runtime_id, generation=4, deadline=deadline
    )

    assert stopped.status == "stopped"
    assert repeated == stopped
    assert adapter.process.stop_calls == 1


async def test_shutdown_stops_every_owned_runtime(tmp_path) -> None:
    adapters = [FakeAdapter(), FakeAdapter()]
    current = iter(adapters)

    class MultiplexAdapter:
        async def launch(self, request):
            return await next(current).launch(request)

    ids = iter(("runtime-a", "runtime-b"))
    supervisor = ProcessSupervisor(
        adapter=MultiplexAdapter(), id_factory=lambda: next(ids)
    )
    for index in range(2):
        await supervisor.start(
            workspace_id="workspace-1",
            instance_id=f"instance-{index}",
            generation=1,
            argv=("python", "app.py"),
            cwd=str(tmp_path),
            environment={},
            secret_environment_names=frozenset(),
            redaction_query_names=frozenset(),
            limits={
                "captured_log_bytes": 4096,
                "captured_log_bytes_per_second": 4096,
                "captured_log_burst_bytes": 4096,
            },
            idempotency_key=f"start-{index}",
        )

    reports = await supervisor.shutdown(
        deadline=datetime.now(UTC) + timedelta(seconds=5)
    )
    assert {item.runtime_id for item in reports} == {"runtime-a", "runtime-b"}
    assert all(adapter.process.stop_calls == 1 for adapter in adapters)
