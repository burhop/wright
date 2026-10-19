import importlib
from pathlib import Path

import pytest


@pytest.fixture
def inbox(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    return importlib.import_module("desktop_oauth").DesktopOAuthPresentation


@pytest.mark.asyncio
async def test_scope_expiry_cleanup_and_restart_do_not_preserve_urls(inbox):
    now = [1.0]
    state = inbox(clock=lambda: now[0])
    state.bind("cad", "workspace", "session", "plan")
    with pytest.raises(ValueError, match="already pending"):
        state.bind("cad", "other", "other", "plan")
    await state.present(
        "cad",
        "https://issuer.example/auth?state=synthetic",
        "http://127.0.0.1:9505/oauth/callback",
    )
    assert (
        state.read("cad", "workspace", "session", "plan")["presentation"]
        == "awaiting_user"
    )
    with pytest.raises(ValueError, match="another operator scope"):
        state.read("cad", "other", "session", "plan")
    await state.present("cad", None, "http://127.0.0.1:9505/oauth/callback")
    assert (
        state.read("cad", "workspace", "session", "plan")["authorization_url"] is None
    )
    now[0] = 332
    assert (
        state.read("cad", "workspace", "session", "plan")["presentation"] == "expired"
    )
    with pytest.raises(ValueError, match="already pending"):
        state.bind("cad", "workspace", "session", "new-plan")
    state.clear("cad")
    state.bind("cad", "workspace", "session", "new-plan")
    assert (
        inbox().read("cad", "workspace", "session", "plan")["authorization_url"] is None
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "url,redirect",
    [
        ("javascript:alert(1)", "http://127.0.0.1:9505/oauth/callback"),
        (
            "https://user:secret@issuer.example/auth",
            "http://127.0.0.1:9505/oauth/callback",
        ),
        ("https://issuer.example/auth", "http://remote.example:9505/oauth/callback"),
        ("https://issuer.example/auth", "http://127.0.0.1:9505/other"),
    ],
)
async def test_rejects_unsafe_presentation_addresses(inbox, url, redirect):
    state = inbox()
    state.bind("cad", "w", "s", "p")
    with pytest.raises(ValueError):
        await state.present("cad", url, redirect)
    assert state.read("cad", "w", "s", "p")["authorization_url"] is None


@pytest.mark.asyncio
async def test_device_presentation_is_scoped_expires_and_clears_without_a_callback(
    inbox,
):
    now = [1.0]
    state = inbox(clock=lambda: now[0])
    state.bind("cad", "w", "s", "p")
    challenge = {
        "verification_uri": "https://issuer.example/device",
        "verification_uri_complete": None,
        "user_code": "TEST-1234",
        "expires_in": 600,
    }
    await state.present_device("cad", challenge)
    value = state.read("cad", "w", "s", "p")
    assert value["presentation"] == "awaiting_user"
    assert value["device"] == challenge and value["callback_uri"] is None
    with pytest.raises(ValueError, match="another operator scope"):
        state.read("cad", "other", "s", "p")
    now[0] = 602
    assert state.read("cad", "w", "s", "p")["device"] is None
    assert state.read("cad", "w", "s", "p")["presentation"] == "expired"
    state.clear("cad")
    state.bind("cad", "w", "s", "p")
    await state.present_device("cad", challenge)
    await state.present_device("cad", None)
    assert state.read("cad", "w", "s", "p")["device"] is None
    assert inbox().read("cad", "w", "s", "p")["device"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "change",
    [
        {"verification_uri": "http://issuer.example/device"},
        {"verification_uri_complete": "https://other.example/device"},
        {"expires_in": 601},
        {"user_code": ""},
    ],
)
async def test_device_presentation_rejects_unsafe_or_invalid_challenges(inbox, change):
    state = inbox()
    state.bind("cad", "w", "s", "p")
    challenge = {
        "verification_uri": "https://issuer.example/device",
        "verification_uri_complete": None,
        "user_code": "TEST-1234",
        "expires_in": 600,
        **change,
    }
    with pytest.raises(ValueError):
        await state.present_device("cad", challenge)
    assert state.read("cad", "w", "s", "p")["device"] is None
