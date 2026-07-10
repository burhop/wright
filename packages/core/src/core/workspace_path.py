"""Workspace-confined path capability.

User paths are relative to one canonical workspace. Existing symbolic links and
Windows reparse points are rejected instead of followed.
"""

from __future__ import annotations

import os
import re
import stat
from pathlib import Path, PureWindowsPath

BACKUP_ID = re.compile(r"^[0-9a-f]{64}$")


class WorkspacePath:
    def __init__(self, root: str | os.PathLike[str]):
        raw_root = Path(root).absolute()
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

    @staticmethod
    def _is_link_or_reparse(path: Path) -> bool:
        info = path.lstat()
        return stat.S_ISLNK(info.st_mode) or bool(
            getattr(info, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
        )

    def resolve(self, user_path: str, *, must_exist: bool = False) -> Path:
        parts = self._validate_relative(user_path)
        candidate = self.root.joinpath(*parts)
        current = self.root
        for part in parts:
            current = current / part
            if os.path.lexists(current) and self._is_link_or_reparse(current):
                raise ValueError(
                    "Access denied: symbolic links and reparse points are not allowed"
                )
        try:
            if os.path.commonpath(
                (os.path.normcase(str(self.root)), os.path.normcase(str(candidate)))
            ) != os.path.normcase(str(self.root)):
                raise ValueError("Access denied: path escapes workspace")
        except ValueError as error:
            raise ValueError("Access denied: path escapes workspace") from error
        if must_exist and not candidate.exists():
            raise FileNotFoundError(user_path)
        return candidate

    def scratch(self, relative_path: str) -> Path:
        return self.resolve(f".wright/tmp/{relative_path}")

    def backup(self, backup_id: str, *, must_exist: bool = False) -> Path:
        if not BACKUP_ID.fullmatch(backup_id):
            raise ValueError("Invalid backup ID")
        return self.resolve(f".git/backups/{backup_id}", must_exist=must_exist)
