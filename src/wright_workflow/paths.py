"""Resolve relative paths beneath a caller-owned root without following links."""

import os
import stat
from pathlib import Path, PureWindowsPath


class ConfinedDirectory:
    def __init__(self, root: str | os.PathLike[str]):
        self.root = Path(os.path.realpath(os.path.abspath(root)))

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
    def _windows_spelling_identity(path: str) -> str:
        """Remove only an extended DOS/UNC prefix from a normalized identity."""
        if path.startswith("\\\\?\\unc\\"):
            return "\\\\" + path[8:]
        if (
            path.startswith("\\\\?\\")
            and len(path) >= 7
            and path[4] in "abcdefghijklmnopqrstuvwxyz"
            and path[5:7] == ":\\"
        ):
            return path[4:]
        return path

    @staticmethod
    def _reject_existing_links(candidate: Path) -> None:
        for component in (*reversed(candidate.parents), candidate):
            try:
                metadata = component.lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISLNK(metadata.st_mode) or (
                getattr(metadata, "st_file_attributes", 0)
                & stat.FILE_ATTRIBUTE_REPARSE_POINT
            ):
                raise ValueError(
                    "Access denied: symbolic links and reparse points are not allowed"
                )

    def resolve(self, user_path: str, *, must_exist: bool = False) -> Path:
        parts = self._validate_relative(user_path)
        root = os.path.normpath(str(self.root))
        root_identity = os.path.normcase(root)
        root_prefix = root_identity.rstrip("\\/") + os.sep
        lexical = os.path.normpath(os.path.join(root, *parts))
        lexical_identity = os.path.normcase(lexical)
        if not lexical_identity.startswith(root_prefix):
            raise ValueError("Access denied: path escapes workspace")

        # realpath resolves existing links. On Windows a concurrent mkdir can
        # leave the equivalent extended DOS/UNC prefix on a missing target.
        # Accept only that spelling change, after checking existing components;
        # other identity changes remain forbidden.
        resolved = os.path.realpath(lexical)
        resolved_identity = os.path.normcase(resolved)
        if resolved_identity != lexical_identity:
            if os.name != "nt" or self._windows_spelling_identity(
                resolved_identity
            ) != self._windows_spelling_identity(lexical_identity):
                raise ValueError(
                    "Access denied: symbolic links and reparse points are not allowed"
                )
            self._reject_existing_links(Path(lexical))
            resolved = lexical
            resolved_identity = lexical_identity
        if not resolved_identity.startswith(root_prefix):
            raise ValueError("Access denied: path escapes workspace")

        candidate = Path(resolved)
        if must_exist and not candidate.exists():
            raise FileNotFoundError(user_path)
        return candidate
