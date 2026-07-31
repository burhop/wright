from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from workspace_service.surfaces.process_remote import (
    RemoteLaunchResult,
    RemotePreviewEndpoint,
    RemoteProcessAdapter,
)
from workspace_service.surfaces.process_supervisor import (
    ProcessLaunchRequest,
    ProcessStopResult,
)


pytestmark = pytest.mark.workspace_surfaces


class FakeRemoteHandle:
    def __init__(self, endpoint: RemotePreviewEndpoint) -> None:
        self.launch_result = RemoteLaunchResult(
            runtime_reference="container-123",
            containment_mode="container-runtime",
            endpoint=endpoint,
        )
        self.stop_calls = 0

    async def stdout(self):
        yield b"remote output\n"

    async def stderr(self):
        if False:
            yield b""

    async def wait(self) -> int:
        return 0

    async def stop(self, *, deadline: datetime) -> ProcessStopResult:
        self.stop_calls += 1
        return ProcessStopResult(0, True, False, (), ())


class FakeProvider:
    def __init__(self, endpoint: RemotePreviewEndpoint) -> None:
        self.handle = FakeRemoteHandle(endpoint)
        self.requests = []

    async def launch(self, request):
        self.requests.append(request)
        return self.handle


def _request(tmp_path) -> ProcessLaunchRequest:
    return ProcessLaunchRequest(
        workspace_id="workspace-1",
        instance_id="instance-1",
        generation=2,
        argv=("python", "app.py"),
        cwd=str(tmp_path.resolve()),
        environment={},
        limits={},
        listener_handle=None,
    )


@pytest.mark.asyncio
async def test_internal_container_origin_is_proxy_only_not_browser_assumed(
    tmp_path,
) -> None:
    endpoint = RemotePreviewEndpoint(
        internal_origin="http://app:8000",
        public_origin=None,
        browser_reachable=False,
    )
    provider = FakeProvider(endpoint)
    process = await RemoteProcessAdapter(
        provider=provider, adapter_name="docker"
    ).launch(_request(tmp_path))

    assert process.endpoint.internal_origin == "http://app:8000"
    assert process.endpoint.browser_url is None
    assert process.identity.pid is None
    assert process.identity.containment_id == "container-123"
    assert provider.requests[0].instance_id == "instance-1"


@pytest.mark.asyncio
async def test_remote_adapter_exposes_public_origin_only_when_vouched_reachable(
    tmp_path,
) -> None:
    endpoint = RemotePreviewEndpoint(
        internal_origin="http://10.0.0.7:9000",
        public_origin="https://preview.example.test/app",
        browser_reachable=True,
    )
    provider = FakeProvider(endpoint)
    process = await RemoteProcessAdapter(
        provider=provider, adapter_name="remote"
    ).launch(_request(tmp_path))
    assert process.endpoint.browser_url == "https://preview.example.test/app"
    report = await process.stop(deadline=datetime.now(UTC) + timedelta(seconds=2))
    assert report.complete is True
    assert provider.handle.stop_calls == 1


@pytest.mark.parametrize(
    "values",
    [
        {
            "internal_origin": "file:///tmp/app",
            "public_origin": None,
            "browser_reachable": False,
        },
        {
            "internal_origin": "http://app:8000",
            "public_origin": None,
            "browser_reachable": True,
        },
        {
            "internal_origin": "http://user:pass@app:8000",
            "public_origin": None,
            "browser_reachable": False,
        },
    ],
)
def test_remote_endpoint_contract_rejects_ambiguous_reachability(values) -> None:
    with pytest.raises(ValueError):
        RemotePreviewEndpoint(**values)
