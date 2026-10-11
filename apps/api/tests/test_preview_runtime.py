from types import SimpleNamespace

import pytest

from api.preview_runtime import bind_preview_runtime


def test_preview_uses_identical_native_gateway_and_surface_owners():
    services = {
        name: object()
        for name in (
            "surface_http_proxy",
            "surface_sse_proxy",
            "surface_websocket_proxy",
            "surface_route_authority",
            "gateway_service",
        )
    }
    primary = SimpleNamespace(state=SimpleNamespace(**services, credential="private"))
    preview = SimpleNamespace(state=SimpleNamespace())
    bind_preview_runtime(primary, preview)
    assert vars(preview.state) == services
    assert all(
        getattr(preview.state, name) is value for name, value in services.items()
    )
    assert not hasattr(preview.state, "credential")


def test_missing_owner_does_not_partially_configure_preview():
    primary = SimpleNamespace(state=SimpleNamespace(surface_http_proxy=object()))
    preview = SimpleNamespace(state=SimpleNamespace())
    with pytest.raises(AttributeError):
        bind_preview_runtime(primary, preview)
    assert not vars(preview.state)
