"""Synthetic keys only: confined encryption, exact subjects, one-use recovery."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from jwcrypto import jwe, jwk


def form_class(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1]))
    from desktop_credential_form import DesktopCredentialForms

    return DesktopCredentialForms


def seal(form, values, **headers):
    envelope = jwe.JWE(
        json.dumps({"form_id": form["form_id"], "values": values}).encode(),
        protected={"alg": "RSA-OAEP-256", "enc": "A256GCM", **headers},
        recipient=jwk.JWK(**form["public_key"]),
    )
    return envelope.serialize(compact=True)


def test_one_use_exact_subject_expiry_and_restart(monkeypatch):
    cls = form_class(monkeypatch)
    now = [0]
    owner = cls(clock=lambda: now[0])
    form = owner.issue(("w", "s", "plan", "config"), ["KEY"])
    sealed = seal(form, {"KEY": "synthetic-private"})
    assert "synthetic-private" not in sealed and "d" not in form["public_key"]
    with pytest.raises(ValueError):
        owner.consume(form["form_id"], ("other",), sealed)
    assert owner.consume(form["form_id"], ("w", "s", "plan", "config"), sealed) == {
        "KEY": "synthetic-private"
    }
    with pytest.raises(ValueError):
        owner.consume(form["form_id"], ("w", "s", "plan", "config"), sealed)
    form = owner.issue(("w",), ["KEY"])
    with pytest.raises(ValueError):
        cls().consume(form["form_id"], ("w",), seal(form, {"KEY": "value"}))
    now[0] = 301
    with pytest.raises(ValueError):
        owner.consume(form["form_id"], ("w",), seal(form, {"KEY": "value"}))


@pytest.mark.parametrize(
    "values", [{"other": "value"}, {"KEY": ""}, {"KEY": 42}, {"KEY": "x" * 4097}]
)
def test_invalid_values_consumed_without_reflection(monkeypatch, values):
    owner = form_class(monkeypatch)()
    form = owner.issue(("w",), ["KEY"])
    with pytest.raises(ValueError, match="could not be saved") as error:
        owner.consume(form["form_id"], ("w",), seal(form, values))
    assert str(values) not in str(error.value)
    with pytest.raises(ValueError, match="expired"):
        owner.consume(form["form_id"], ("w",), seal(form, {"KEY": "good"}))


def test_rejects_compression_and_replacement_invalidates_old_form(monkeypatch):
    owner = form_class(monkeypatch)()
    form = owner.issue(("w",), ["KEY"])
    with pytest.raises(ValueError):
        owner.consume(
            form["form_id"], ("w",), seal(form, {"KEY": "synthetic-private"}, zip="DEF")
        )
    old = owner.issue(("w",), ["KEY"])
    owner.issue(("w",), ["KEY"])
    with pytest.raises(ValueError):
        owner.consume(old["form_id"], ("w",), seal(old, {"KEY": "value"}))


@pytest.mark.asyncio
async def test_bridge_returns_public_key_only_in_meta_and_accepts_ciphertext(
    monkeypatch,
):
    form_class(monkeypatch)
    from mcp_bridge import server
    from unittest.mock import AsyncMock

    response = {
        "workspace_id": "w",
        "session_id": "s",
        "plan_id": "p",
        "form": {"public_key": "synthetic-public", "form_id": "f"},
    }
    client = SimpleNamespace(
        scope=AsyncMock(), call=AsyncMock(return_value=response.copy())
    )
    bridge = server(client)
    result = await bridge.call_tool(
        "wright_connection_credentials_form",
        {
            "workspace_id": "w",
            "session_id": "s",
            "plan_id": "p",
            "plan_digest": "a" * 64,
        },
    )
    assert "synthetic-public" not in str(result.content) + str(result.structuredContent)
    assert result.meta["wright/credential-form"]["form_id"] == "f"
    tools = {tool.name: tool for tool in await bridge.list_tools()}
    for name in (
        "wright_connection_credentials",
        "wright_connection_credentials_form",
        "wright_connection_credentials_save",
    ):
        assert tools[name].meta["ui"]["visibility"] == ["app"]
    assert (
        "values"
        not in tools["wright_connection_credentials_save"].inputSchema["properties"]
    )
