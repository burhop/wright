"""Immutable presentation file sets over the existing contained FileVault.

The application supplies an authorized, link-free workspace directory. Logical
names are metadata; generated code never chooses physical vault filenames.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from core.process_validation import canonical_digest, canonical_json, relative_locator

from .file_vault import FileVault


@dataclass(frozen=True)
class ImmutableFileSet:
    root: Path
    maximum_bytes: int = 50_331_648
    maximum_files: int = 96

    def __post_init__(self):
        if (
            type(self.maximum_bytes) is not int
            or not 1 <= self.maximum_bytes <= 50_331_648
        ):
            raise ValueError("Presentation storage requires a bounded byte limit")
        if type(self.maximum_files) is not int or not 1 <= self.maximum_files <= 96:
            raise ValueError("Presentation storage requires a bounded file limit")

    def _directory(self) -> Path:
        path = Path(self.root).absolute()
        # Reject links and Windows reparse points along the trusted path. The
        # owner must separately establish workspace containment/authorization.
        for parent in (path, *path.parents):
            if parent.is_symlink() or (
                parent.exists()
                and getattr(parent.stat(), "st_file_attributes", 0) & 0x400
            ):
                raise ValueError("Presentation storage cannot follow links")
        return path

    def publish(self, content: dict[str, bytes]) -> str:
        """Publish once. Partial drafts are never accepted or overwritten."""
        if not content or len(content) > self.maximum_files:
            raise ValueError("Presentation file count is outside its bound")
        for name, raw in content.items():
            relative_locator(name)
            if not isinstance(raw, bytes):
                raise ValueError("Presentation files require bytes")
        if sum(len(raw) for raw in content.values()) > self.maximum_bytes:
            raise ValueError("Presentation file set exceeds its byte bound")
        root = self._directory()
        root.mkdir(parents=True, exist_ok=False)
        vault = FileVault(root)
        inventory = {}
        for name, raw in sorted(content.items()):
            stored = vault.store(name, raw)
            inventory[name] = {
                "storage_key": stored.storage_key,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "bytes": len(raw),
            }
        with (root / "inventory.json").open("x", encoding="utf-8") as stream:
            stream.write(canonical_json(inventory))
        return canonical_digest(inventory)

    def read(self, expected_inventory_digest: str) -> dict[str, bytes]:
        """Verify every byte before handing a saved bundle to a presenter."""
        root = self._directory()
        index = root / "inventory.json"
        if index.is_symlink() or not index.is_file() or index.stat().st_size > 65_536:
            raise ValueError("The presentation inventory is unavailable")
        inventory = json.loads(index.read_bytes())
        if (
            not isinstance(inventory, dict)
            or not 0 < len(inventory) <= self.maximum_files
            or canonical_digest(inventory) != expected_inventory_digest
        ):
            raise ValueError("The immutable presentation inventory changed")
        vault = FileVault(root)
        content, total = {}, 0
        for name, item in inventory.items():
            relative_locator(name)
            if not isinstance(item, dict) or set(item) != {
                "storage_key",
                "sha256",
                "bytes",
            }:
                raise ValueError("The presentation inventory is malformed")
            size = item["bytes"]
            if type(size) is not int or not 0 <= size <= self.maximum_bytes:
                raise ValueError("The recorded presentation size is invalid")
            lexical = root / item["storage_key"]
            if lexical.is_symlink() or (
                lexical.exists()
                and getattr(lexical.stat(), "st_file_attributes", 0) & 0x400
            ):
                raise ValueError("Presentation storage cannot follow file links")
            path = vault.resolve(item["storage_key"])
            if path.is_symlink() or path.stat().st_size != size:
                raise ValueError("An immutable presentation file changed")
            total += size
            if total > self.maximum_bytes:
                raise ValueError("The saved presentation exceeds its byte bound")
            raw = path.read_bytes()
            if len(raw) != size or hashlib.sha256(raw).hexdigest() != item["sha256"]:
                raise ValueError("An immutable presentation file changed")
            content[name] = raw
        return content
