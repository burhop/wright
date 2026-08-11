import os
import logging
import base64
import mimetypes
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from data_vault import FileVault, VaultPathError

logger = logging.getLogger(__name__)

router = APIRouter()

VAULT_DIR = Path(os.getenv("WRIGHT_VAULT_DIR", ".vault"))


def _vault() -> FileVault:
    return FileVault(VAULT_DIR)


def attachment_data_urls(file_ids: list[str] | None) -> list[str] | None:
    """Resolve uploaded image IDs into Hermes-compatible multimodal data URLs."""
    if not file_ids:
        return None

    urls: list[str] = []
    vault = _vault()
    for file_id in file_ids:
        try:
            path = vault.resolve_file_id(file_id)
        except (VaultPathError, FileNotFoundError):
            raise HTTPException(
                status_code=400, detail="Attachment was not found"
            ) from None
        mime_type = mimetypes.guess_type(path.name)[0]
        if not mime_type or not mime_type.startswith("image/"):
            raise HTTPException(
                status_code=400, detail="Only image attachments are supported"
            )
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        urls.append(f"data:{mime_type};base64,{encoded}")
    return urls


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        stored = _vault().store(file.filename, content)
        logger.info("Saved uploaded vault file %s", stored.storage_key)

        return {
            "file_id": stored.file_id,
            "filename": stored.display_name,
            "mime_type": file.content_type,
            "size_bytes": stored.size_bytes,
            "url": f"/api/vault/files/{stored.storage_key}",
        }
    except Exception:
        logger.exception("Failed to save uploaded vault file")
        raise HTTPException(status_code=500, detail="Failed to save file") from None


@router.get("/files/{filename}")
async def get_file(filename: str):
    try:
        file_path = _vault().resolve(filename)
    except (VaultPathError, FileNotFoundError):
        raise HTTPException(status_code=404, detail="File not found") from None

    return FileResponse(path=file_path)
