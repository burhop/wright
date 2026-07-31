import pytest

from api.security import SecuritySettings


def test_security_settings_fail_closed_without_token():
    with pytest.raises(RuntimeError, match="WRIGHT_API_TOKEN"):
        SecuritySettings(
            "enforced", None, ("http://localhost:5173",), "127.0.0.1"
        ).validate()


def test_security_settings_reject_wildcard_and_insecure_remote_bind():
    with pytest.raises(RuntimeError, match="wildcard"):
        SecuritySettings("enforced", "secret", ("*",), "127.0.0.1").validate()
    with pytest.raises(RuntimeError, match="Remote bind"):
        SecuritySettings(
            "compat", None, ("http://localhost:5173",), "0.0.0.0"
        ).validate()


def test_browser_session_token_is_derived_and_separately_validated():
    settings = SecuritySettings(
        "enforced", "test-admin-token", ("http://localhost:5173",), "127.0.0.1"
    )

    browser_token = settings.browser_session_token()

    assert browser_token
    assert browser_token != settings.api_token
    assert settings.browser_session_valid(browser_token)
    assert not settings.browser_session_valid(settings.api_token)


@pytest.mark.asyncio
async def test_protected_api_requires_valid_bearer(client, monkeypatch):
    from api.main import app

    previous = app.state.security_settings
    app.state.security_settings = SecuritySettings(
        "enforced", "test-admin-token", ("http://localhost:5173",), "127.0.0.1"
    )
    monkeypatch.setenv("WRIGHT_RUNTIME_CHALLENGE", "health-challenge")
    monkeypatch.setenv("WRIGHT_RUNTIME_ID", "runtime-1")
    monkeypatch.setenv("WRIGHT_RUNTIME_INSTANCE_ID", "instance-1")
    monkeypatch.setenv("WRIGHT_RUNTIME_OPERATION_ID", "operation-1")
    try:
        assert (await client.get("/api/health")).status_code == 200
        identity = await client.get("/api/runtime/identity")
        assert identity.status_code == 200
        assert identity.json()["runtime_id"] == "runtime-1"
        assert (await client.get("/api/settings")).status_code == 401
        wrong = await client.get(
            "/api/settings", headers={"Authorization": "Bearer wrong"}
        )
        assert wrong.status_code == 401
        allowed = await client.get(
            "/api/settings", headers={"Authorization": "Bearer test-admin-token"}
        )
        assert allowed.status_code == 200
        denied_origin = await client.get(
            "/api/settings",
            headers={
                "Authorization": "Bearer test-admin-token",
                "Origin": "https://evil.example",
            },
        )
        assert denied_origin.status_code == 403
        invalid_session = await client.post(
            "/api/auth/session", json={"token": "wrong"}
        )
        assert invalid_session.status_code == 401
        session_status = await client.get("/api/auth/session/status")
        assert session_status.status_code == 200
        assert session_status.json() == {
            "auth_required": True,
            "authenticated": False,
        }
        session = await client.post(
            "/api/auth/session", json={"token": "test-admin-token"}
        )
        assert session.status_code == 204
        cookie_header = session.headers["set-cookie"]
        assert "test-admin-token" not in cookie_header
        assert app.state.security_settings.browser_session_token() in cookie_header
        session_status = await client.get("/api/auth/session/status")
        assert session_status.status_code == 200
        assert session_status.json() == {
            "auth_required": True,
            "authenticated": True,
        }
        assert (await client.get("/api/settings")).status_code == 200
    finally:
        app.state.security_settings = previous


@pytest.mark.asyncio
async def test_native_loopback_navigation_establishes_browser_session(client):
    from api.main import app

    previous = app.state.security_settings
    app.state.security_settings = SecuritySettings(
        "enforced",
        "native-admin-token",
        ("http://127.0.0.1:8000",),
        "127.0.0.1",
        native_runtime=True,
    )
    try:
        response = await client.get(
            "/", headers={"Host": "127.0.0.1:8000", "Sec-Fetch-Mode": "navigate"}
        )
        assert response.status_code == 200
        assert "wright_session=" in response.headers["set-cookie"]
        assert "native-admin-token" not in response.headers["set-cookie"]
        assert (await client.get("/api/settings")).status_code == 200

        rejected = await client.get(
            "/", headers={"Host": "rebind.example", "Sec-Fetch-Mode": "navigate"}
        )
        assert "set-cookie" not in rejected.headers
    finally:
        app.state.security_settings = previous
