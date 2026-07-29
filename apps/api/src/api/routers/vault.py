import os
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from data_vault import FileVault, VaultPathError

logger = logging.getLogger(__name__)

router = APIRouter()

VAULT_DIR = Path(os.getenv("WRIGHT_VAULT_DIR", ".vault"))


def _vault() -> FileVault:
    return FileVault(VAULT_DIR)


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
