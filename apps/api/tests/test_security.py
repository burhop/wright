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
    try:
        assert (await client.get("/api/health")).status_code == 200
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
        session = await client.post(
            "/api/auth/session", json={"token": "test-admin-token"}
        )
        assert session.status_code == 204
        cookie_header = session.headers["set-cookie"]
        assert "test-admin-token" not in cookie_header
        assert app.state.security_settings.browser_session_token() in cookie_header
        assert (await client.get("/api/settings")).status_code == 200
    finally:
        app.state.security_settings = previous
