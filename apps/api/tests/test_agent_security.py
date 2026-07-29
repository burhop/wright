from pathlib import Path

import pytest

from api.routers.agent import title_from_slash_command


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("/title mark", "mark"),
        ("  /TITLE\tQuoted Title  ", "Quoted Title"),
        ('/title "quoted"', "quoted"),
        ("/title", None),
        ("/titlex wrong", None),
        ("/title    ", None),
    ],
)
def test_title_parser_is_unambiguous(message: str, expected: str | None):
    assert title_from_slash_command(message) == expected


def test_title_parser_bounds_repeated_input():
    parsed = title_from_slash_command("/title " + "a" * 100_000)

    assert parsed == "a" * 200


@pytest.mark.asyncio
async def test_new_session_rejects_unregistered_path_without_creating(
    client, tmp_path: Path
):
    requested = tmp_path / "unregistered" / "caller-selected"

    response = await client.post(
        "/api/agent/sessions/new", json={"workspace": str(requested)}
    )

    assert response.status_code == 400
    assert not requested.exists()


@pytest.mark.asyncio
async def test_new_session_without_path_creates_generated_managed_workspace(
    client, mock_agent_engine, monkeypatch, tmp_path: Path
):
    managed_root = tmp_path / "managed"
    monkeypatch.setenv("WRIGHT_WORKSPACES_DIR", str(managed_root))

    response = await client.post("/api/agent/sessions/new", json={})

    assert response.status_code == 200
    session = mock_agent_engine._sessions[response.json()["session_id"]]
    workspace = Path(session.workspace).resolve()
    assert workspace.is_dir()
    assert workspace.parent == managed_root.resolve()
    assert workspace.name.startswith("session-")
