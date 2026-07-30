from pathlib import Path

import pytest

import api.routers.vault as vault_router


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "filename",
    [
        "../../outside.pdf",
        r"..\..\outside.pdf",
        "/absolute/outside.pdf",
        r"C:\outside.pdf",
    ],
)
async def test_upload_never_uses_client_filename_as_storage_path(
    client, monkeypatch, tmp_path: Path, filename: str
):
    root = tmp_path / "vault"
    monkeypatch.setattr(vault_router, "VAULT_DIR", root)

    response = await client.post(
        "/api/vault/upload",
        files={"file": (filename, b"pdf-data", "application/pdf")},
    )

    assert response.status_code == 200
    payload = response.json()
    storage_key = payload["url"].rsplit("/", 1)[-1]
    assert payload["filename"] == "outside.pdf"
    assert "outside" not in storage_key
    assert (root / storage_key).read_bytes() == b"pdf-data"
    assert not (tmp_path / "outside.pdf").exists()

    download = await client.get(payload["url"])
    assert download.status_code == 200
    assert download.content == b"pdf-data"
    assert download.headers["content-type"].startswith("application/pdf")


@pytest.mark.asyncio
async def test_vault_read_rejects_encoded_windows_traversal(
    client, monkeypatch, tmp_path: Path
):
    monkeypatch.setattr(vault_router, "VAULT_DIR", tmp_path / "vault")

    response = await client.get("/api/vault/files/..%5Coutside.txt")

    assert response.status_code == 404
    assert "outside" not in response.text
