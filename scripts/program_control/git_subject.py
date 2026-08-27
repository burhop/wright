"""Safe read-only Git-object access and exact subject resolution."""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final

from .json_contracts import canonical_digest, sha256_bytes


HEX40: Final[re.Pattern[str]] = re.compile(r"^[a-f0-9]{40}$")
SAFE_GIT_COMMANDS: Final[frozenset[str]] = frozenset(
    {"cat-file", "config", "diff", "ls-tree", "rev-parse", "status"}
)


class GitSubjectError(ValueError):
    """A bounded Git resolution or path failure."""


def normalize_repo_path(value: str, *, allow_empty: bool = False) -> str:
    """Normalize a repository-relative path without touching the filesystem."""

    if not isinstance(value, str) or "\x00" in value:
        raise GitSubjectError("unsafe repository path")
    normalized = value.replace("\\", "/")
    if not normalized and allow_empty:
        return ""
    if (
        not normalized
        or normalized.startswith(("/", "//"))
        or re.match(r"^[A-Za-z]:", normalized)
    ):
        raise GitSubjectError("path must be repository-relative")
    path = PurePosixPath(normalized)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise GitSubjectError("path traversal is not permitted")
    return path.as_posix()


def ensure_safe_checkout_target(repo_root: Path, relative: str) -> Path:
    """Resolve an output path and reject repository escape or symlink traversal."""

    normalized = normalize_repo_path(relative)
    root = repo_root.resolve(strict=True)
    candidate = root.joinpath(*PurePosixPath(normalized).parts)
    cursor = root
    for part in PurePosixPath(normalized).parts[:-1]:
        cursor = cursor / part
        if cursor.exists() and cursor.is_symlink():
            raise GitSubjectError("symlink traversal is not permitted")
    resolved_parent = candidate.parent.resolve(strict=False)
    try:
        resolved_parent.relative_to(root)
    except ValueError as exc:
        raise GitSubjectError("path escapes repository") from exc
    return candidate


@dataclass(frozen=True)
class GitIdentity:
    source_commit: str
    source_tree: str
    program_tree: str


class GitReader:
    """Read Git objects using argument arrays and an explicit command allowlist."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve(strict=True)

    @classmethod
    def discover(cls, start: Path | None = None) -> "GitReader":
        cwd = (start or Path.cwd()).resolve(strict=True)
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
        if result.returncode != 0:
            raise GitSubjectError("repository root could not be resolved")
        try:
            root = Path(result.stdout.decode("utf-8", errors="strict").strip())
        except UnicodeDecodeError as exc:
            raise GitSubjectError("repository root encoding is unsupported") from exc
        return cls(root)

    def _run(self, args: list[str]) -> bytes:
        if not args or args[0] not in SAFE_GIT_COMMANDS:
            raise GitSubjectError("Git command is not read-only allowlisted")
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
        if result.returncode != 0:
            raise GitSubjectError("Git object operation failed")
        return result.stdout

    def resolve_commit(self, revision: str) -> str:
        if (
            not revision
            or revision.startswith("-")
            or any(ch.isspace() for ch in revision)
        ):
            raise GitSubjectError("unsafe revision")
        value = (
            self._run(["rev-parse", "--verify", f"{revision}^{{commit}}"])
            .decode()
            .strip()
        )
        if not HEX40.fullmatch(value):
            raise GitSubjectError("revision did not resolve to a commit")
        return value

    def resolve_identity(self, revision: str, program_root: str) -> GitIdentity:
        root = normalize_repo_path(program_root)
        commit = self.resolve_commit(revision)
        tree = self._run(["rev-parse", f"{commit}^{{tree}}"]).decode().strip()
        program_tree = self._run(["rev-parse", f"{commit}:{root}"]).decode().strip()
        if not HEX40.fullmatch(tree) or not HEX40.fullmatch(program_tree):
            raise GitSubjectError("subject tree identity is invalid")
        return GitIdentity(commit, tree, program_tree)

    def blob(self, commit: str, path: str) -> bytes:
        normalized = normalize_repo_path(path)
        if not HEX40.fullmatch(commit):
            raise GitSubjectError("commit identity is invalid")
        return self._run(["cat-file", "blob", f"{commit}:{normalized}"])

    def blob_id(self, commit: str, path: str) -> str:
        normalized = normalize_repo_path(path)
        output = self._run(["ls-tree", commit, "--", normalized]).decode(
            "utf-8", errors="strict"
        )
        fields = output.strip().split()
        if len(fields) < 3 or not HEX40.fullmatch(fields[2]):
            raise GitSubjectError("Git blob identity is unavailable")
        return fields[2]

    def list_files(self, commit: str, root: str) -> list[str]:
        normalized = normalize_repo_path(root)
        raw = self._run(
            ["ls-tree", "-r", "-z", "--name-only", commit, "--", normalized]
        )
        try:
            paths = raw.decode("utf-8", errors="strict").split("\x00")
        except UnicodeDecodeError as exc:
            raise GitSubjectError("repository paths are not UTF-8") from exc
        return sorted(normalize_repo_path(path) for path in paths if path)

    def worktree_observation(self) -> dict[str, object]:
        status = self._run(["status", "--porcelain=v1", "-z"])
        autocrlf_raw = (
            self._run(["config", "--get", "core.autocrlf"]).decode().strip().lower()
        )
        autocrlf = (
            autocrlf_raw if autocrlf_raw in {"true", "false", "input"} else "unset"
        )
        return {
            "platform": "windows" if os.name == "nt" else "posix",
            "autocrlf": autocrlf,
            "dirty_path_count": len([part for part in status.split(b"\x00") if part]),
        }

    def manifest(
        self, commit: str, program_root: str
    ) -> tuple[list[dict[str, str]], str]:
        """Build the complete non-generated program input manifest."""

        root = normalize_repo_path(program_root)
        excluded = {
            f"{root}/dashboard.json",
        }
        entries: list[dict[str, str]] = []
        for path in self.list_files(commit, root):
            if (
                path in excluded
                or "/evidence/verification/EPP-F01-dashboard-delivery.json" in path
            ):
                continue
            raw = self.blob(commit, path)
            entries.append(
                {
                    "path": path,
                    "git_blob": self.blob_id(commit, path),
                    "sha256": sha256_bytes(raw),
                }
            )
        return entries, canonical_digest(entries)
