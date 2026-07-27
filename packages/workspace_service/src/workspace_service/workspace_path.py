"""Workspace-confined path capability owned by the workspace application.

User paths are relative to one canonical workspace. Existing symbolic links and
Windows reparse points are rejected instead of followed.
"""

from __future__ import annotations

import os
import re
from pathlib import Path, PureWindowsPath

BACKUP_ID = re.compile(r"^[0-9a-f]{64}$")


class WorkspacePath:
    def __init__(self, root: str | os.PathLike[str], *, create: bool = False):
        raw_root = Path(root).absolute()
        if create:
            raw_root.mkdir(parents=True, exist_ok=True)
        self.root = raw_root.resolve(strict=True)
        if not self.root.is_dir():
            raise ValueError("Workspace root must be a directory")

    @staticmethod
    def _validate_relative(user_path: str) -> tuple[str, ...]:
        if not user_path or "\x00" in user_path:
            raise ValueError("Workspace path must be a non-empty relative path")
        windows = PureWindowsPath(user_path)
        normalized = user_path.replace("\\", "/")
        if (
            Path(user_path).is_absolute()
            or windows.is_absolute()
            or windows.drive
            or normalized.startswith("/")
            or normalized.startswith("//")
            or normalized.startswith("?/")
            or normalized.startswith("./?")
        ):
            raise ValueError(
                "Access denied: absolute, drive, and UNC paths are not allowed"
            )
        parts = tuple(part for part in normalized.split("/") if part not in {"", "."})
        if not parts or any(part == ".." for part in parts):
            raise ValueError("Access denied: path traversal attempt detected")
        if any(":" in part for part in parts):
            raise ValueError(
                "Access denied: alternate data stream paths are not allowed"
            )
        return parts

    def resolve(self, user_path: str, *, must_exist: bool = False) -> Path:
        parts = self._validate_relative(user_path)
        root = os.path.normpath(str(self.root))
        root_identity = os.path.normcase(root)
        root_prefix = root_identity.rstrip("\\/") + os.sep
        lexical = os.path.normpath(os.path.join(root, *parts))
        lexical_identity = os.path.normcase(lexical)
        if not lexical_identity.startswith(root_prefix):
            raise ValueError("Access denied: path escapes workspace")

        # realpath resolves every existing link or Windows reparse point in the
        # chain. Rejecting any difference preserves a link-free capability while
        # the explicit prefix guard gives filesystem operations a normalized,
        # workspace-confined path.
        resolved = os.path.realpath(lexical)
        resolved_identity = os.path.normcase(resolved)
        if not resolved_identity.startswith(root_prefix):
            raise ValueError("Access denied: path escapes workspace")
        if resolved_identity != lexical_identity:
            raise ValueError(
                "Access denied: symbolic links and reparse points are not allowed"
            )

        candidate = Path(resolved)
        if must_exist and not candidate.exists():
            raise FileNotFoundError(user_path)
        return candidate

    def scratch(self, relative_path: str) -> Path:
        return self.resolve(f".wright/tmp/{relative_path}")

    def backup(self, backup_id: str, *, must_exist: bool = False) -> Path:
        if not BACKUP_ID.fullmatch(backup_id):
            raise ValueError("Invalid backup ID")
        return self.resolve(f".git/backups/{backup_id}", must_exist=must_exist)
