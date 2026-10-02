"""Share existing owning services with the isolated presentation API shell."""


def bind_preview_runtime(primary, preview):
    # The preview routes delegate to native handlers. They need the same gateway
    # for qualification/consumption, never a new gateway or provider lifetime.
    names = (
        "surface_http_proxy",
        "surface_sse_proxy",
        "surface_websocket_proxy",
        "surface_route_authority",
        "gateway_service",
    )
    services = {name: getattr(primary.state, name) for name in names}
    for name, service in services.items():
        setattr(preview.state, name, service)
