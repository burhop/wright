import json

import pytest

from tool_registry.gateway_models import (
    GatewayError,
    GatewayResource,
    GatewaySessionContext,
)
from tool_registry.gateway_resources import GatewayResourceProvider, ResourceContent


def session(workspace_id: str = "w1") -> GatewaySessionContext:
    return GatewaySessionContext(
        "s1", "p1", workspace_id, f"/work/{workspace_id}", "stdio"
    )


def test_catalog_and_workspace_resources_are_bound_and_readable() -> None:
    provider = GatewayResourceProvider()
    resources = provider.list(session())
    assert [resource.uri for resource in resources[:2]] == [
        "wright://catalog/engineering",
        "wright://workspace/w1",
    ]
    assert (
        len(json.loads(provider.read(session(), resources[0].uri).content)["servers"])
        == 42
    )
    assert json.loads(provider.read(session(), resources[1].uri).content) == {
        "session_id": "s1",
        "workspace_id": "w1",
    }


def test_foreign_workspace_resource_fails_closed() -> None:
    with pytest.raises(GatewayError, match="not available"):
        GatewayResourceProvider().read(session(), "wright://workspace/w2")


def test_artifact_reader_receives_bound_session_and_uri() -> None:
    artifact = GatewayResource(
        "wright://artifact/w1/result.step", "result.step", "CAD artifact", "model/step"
    )
    seen = []
    provider = GatewayResourceProvider(
        list_artifacts=lambda bound: [artifact],
        read_artifact=lambda bound, uri: (
            seen.append((bound.workspace_id, uri))
            or ResourceContent(b"STEP", "model/step")
        ),
    )
    assert provider.list(session())[-1] == artifact
    assert provider.read(session(), artifact.uri).content == b"STEP"
    assert seen == [("w1", artifact.uri)]


@pytest.mark.parametrize(
    "uri",
    [
        "wright://artifact/w1/../secret",
        "wright://artifact/w1/%2e%2e/secret",
        "wright://artifact/w1/folder\\secret",
    ],
)
def test_artifact_resource_rejects_escape_locators(uri: str) -> None:
    provider = GatewayResourceProvider(
        read_artifact=lambda bound, value: ResourceContent(b"unsafe", "text/plain")
    )
    with pytest.raises(GatewayError, match="not available"):
        provider.read(session(), uri)
