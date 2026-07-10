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
    finally:
        app.state.security_settings = previous
