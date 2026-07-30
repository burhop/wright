"""Contained filesystem storage for Wright-generated vault artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import uuid


_SAFE_EXTENSION = re.compile(r"\.[A-Za-z0-9]{1,10}\Z")


class VaultPathError(ValueError):
    """Raised when a requested vault name cannot be proven contained."""


@dataclass(frozen=True)
class StoredVaultFile:
    file_id: str
    storage_key: str
    display_name: str
    path: Path
    size_bytes: int


def _display_name(filename: str | None) -> str:
    normalized = (filename or "uploaded_file").replace("\\", "/")
    name = normalized.rsplit("/", 1)[-1]
    name = "".join(char for char in name if ord(char) >= 0x20 and char != "\x7f")
    name = name.strip()[:255]
    return name if name not in {"", ".", ".."} else "uploaded_file"


def _storage_extension(display_name: str) -> str:
    suffix = Path(display_name).suffix
    return suffix.casefold() if _SAFE_EXTENSION.fullmatch(suffix) else ""


class FileVault:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).expanduser().resolve(strict=False)

    def ensure_exists(self) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        return self.root

    def store(self, filename: str | None, content: bytes) -> StoredVaultFile:
        root = self.ensure_exists()
        display_name = _display_name(filename)
        file_id = str(uuid.uuid4())
        storage_key = f"{file_id}{_storage_extension(display_name)}"
        path = (root / storage_key).resolve(strict=False)
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise VaultPathError(
                "Vault file must remain inside the configured root"
            ) from exc
        if path.parent != root:
            raise VaultPathError("Vault files must be direct children of the root")
        path.write_bytes(content)
        return StoredVaultFile(
            file_id=file_id,
            storage_key=storage_key,
            display_name=display_name,
            path=path,
            size_bytes=len(content),
        )

    def resolve(self, name: str) -> Path:
        if (
            not name
            or name in {".", ".."}
            or "\x00" in name
            or "/" in name
            or "\\" in name
            or ":" in name
        ):
            raise VaultPathError("Invalid vault file name")
        root = self.ensure_exists()
        path = (root / name).resolve(strict=False)
        try:
            path.relative_to(root)
        except ValueError as exc:
            raise VaultPathError(
                "Vault file must remain inside the configured root"
            ) from exc
        if path.parent != root:
            raise VaultPathError("Vault files must be direct children of the root")
        if not path.is_file():
            raise FileNotFoundError(name)
        return path
