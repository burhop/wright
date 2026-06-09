import os
import uuid
import logging
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

router = APIRouter()

VAULT_DIR = Path(os.getenv("WRIGHT_VAULT_DIR", ".vault"))


def ensure_vault_exists():
    VAULT_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    ensure_vault_exists()

    file_id = str(uuid.uuid4())
    safe_filename = file.filename or "uploaded_file"

    # Prepend UUID to avoid collisions
    unique_filename = f"{file_id}_{safe_filename}"
    file_path = VAULT_DIR / unique_filename

    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"Saved uploaded file to {file_path}")

        return {
            "file_id": file_id,
            "filename": safe_filename,
            "mime_type": file.content_type,
            "size_bytes": len(content),
            "url": f"/api/vault/files/{unique_filename}",
        }
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")


@router.get("/files/{filename}")
async def get_file(filename: str):
    file_path = VAULT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=file_path)
