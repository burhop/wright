"""Safe read-only Git-object access and exact subject resolution."""

from __future__ import annotations

import os
import posixpath
import re
import subprocess
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath
from typing import Any, Final

from .json_contracts import (
    ContractError,
    canonical_digest,
    sha256_bytes,
    strict_loads,
)


HEX40: Final[re.Pattern[str]] = re.compile(r"^[a-f0-9]{40}$")
SAFE_GIT_COMMANDS: Final[frozenset[str]] = frozenset(
    {
        "cat-file",
        "config",
        "diff",
        "log",
        "ls-tree",
        "merge-base",
        "rev-parse",
        "rev-list",
        "show",
        "status",
    }
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


@dataclass(frozen=True)
class GitBlobFact:
    """Exact immutable identity for one path at one commit."""

    commit: str
    path: str
    git_blob: str
    sha256: str


class GitReader:
    """Read Git objects using argument arrays and an explicit command allowlist."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root.resolve(strict=True)
        self._blob_cache: dict[tuple[str, str], bytes] = {}
        self._tree_cache: dict[tuple[str, str], tuple[dict[str, str], ...]] = {}
        self._commit_cache: dict[str, str] = {}
        self._identity_cache: dict[tuple[str, str], GitIdentity] = {}
        self._summary_cache: dict[str, dict[str, object]] = {}
        self._object_id_cache: dict[tuple[str, str], str] = {}
        self._added_path_cache: dict[tuple[str, str], dict[str, str]] = {}
        self._introduction_cache: dict[tuple[str, str], str] = {}
        self._branch_cache: str | None = None
        self._ancestor_cache: dict[str, frozenset[str]] = {}
        self._parent_cache: dict[str, tuple[str, ...]] = {}
        self._cat_file_processes: dict[str, subprocess.Popen[bytes]] = {}

    @classmethod
    def discover(cls, start: Path | None = None) -> "GitReader":
        try:
            cwd = (start or Path.cwd()).resolve(strict=True)
        except OSError as exc:
            raise GitSubjectError(
                "repository start path could not be resolved"
            ) from exc
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

    def _run(self, args: list[str], *, input_data: bytes | None = None) -> bytes:
        if not args or args[0] not in SAFE_GIT_COMMANDS:
            raise GitSubjectError("Git command is not read-only allowlisted")
        if (
            args[0] == "cat-file"
            and len(args) == 2
            and args[1].startswith("--batch")
            and input_data is not None
        ):
            return self._run_cat_file_batch(args[1], input_data)
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_root,
            check=False,
            input=input_data,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            shell=False,
        )
        if result.returncode != 0:
            raise GitSubjectError("Git object operation failed")
        return result.stdout

    @staticmethod
    def _read_exact(stream: Any, size: int) -> bytes:
        chunks: list[bytes] = []
        remaining = size
        while remaining:
            chunk = stream.read(remaining)
            if not chunk:
                raise GitSubjectError("Git batch response is truncated")
            chunks.append(chunk)
            remaining -= len(chunk)
        return b"".join(chunks)

    def _run_cat_file_batch(self, mode: str, input_data: bytes) -> bytes:
        """Reuse bounded cat-file workers to avoid per-object process startup."""

        queries = [line for line in input_data.splitlines() if line]
        if not queries:
            return b""
        process = self._cat_file_processes.get(mode)
        if process is None or process.poll() is not None:
            process = subprocess.Popen(
                ["git", "cat-file", mode],
                cwd=self.repo_root,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                shell=False,
            )
            self._cat_file_processes[mode] = process
        if process.stdin is None or process.stdout is None:
            raise GitSubjectError("Git batch worker is unavailable")
        try:
            output: list[bytes] = []
            for query in queries:
                process.stdin.write(query + b"\n")
                process.stdin.flush()
                header = process.stdout.readline()
                if not header:
                    raise GitSubjectError("Git batch response is truncated")
                output.append(header)
                if mode == "--batch":
                    fields = header.rstrip(b"\n").split()
                    if len(fields) == 3 and fields[2].isdigit():
                        output.append(
                            self._read_exact(process.stdout, int(fields[2]) + 1)
                        )
            return b"".join(output)
        except (BrokenPipeError, OSError) as exc:
            self._cat_file_processes.pop(mode, None)
            raise GitSubjectError("Git batch worker failed") from exc

    def resolve_commit(self, revision: str) -> str:
        if (
            not revision
            or revision.startswith("-")
            or any(ch.isspace() for ch in revision)
        ):
            raise GitSubjectError("unsafe revision")
        cached = self._commit_cache.get(revision)
        if cached is not None:
            return cached
        value = (
            self._run(["rev-parse", "--verify", f"{revision}^{{commit}}"])
            .decode()
            .strip()
        )
        if not HEX40.fullmatch(value):
            raise GitSubjectError("revision did not resolve to a commit")
        self._commit_cache[revision] = value
        self._commit_cache[value] = value
        return value

    def resolve_identity(self, revision: str, program_root: str) -> GitIdentity:
        root = normalize_repo_path(program_root)
        commit = self.resolve_commit(revision)
        cached = self._identity_cache.get((commit, root))
        if cached is not None:
            return cached
        values = (
            self._run(["rev-parse", f"{commit}^{{tree}}", f"{commit}:{root}"])
            .decode()
            .splitlines()
        )
        if len(values) != 2:
            raise GitSubjectError("subject tree identity is incomplete")
        tree, program_tree = values
        if not HEX40.fullmatch(tree) or not HEX40.fullmatch(program_tree):
            raise GitSubjectError("subject tree identity is invalid")
        identity = GitIdentity(commit, tree, program_tree)
        self._identity_cache[(commit, root)] = identity
        return identity

    def blob(self, commit: str, path: str) -> bytes:
        normalized = normalize_repo_path(path)
        if not HEX40.fullmatch(commit):
            raise GitSubjectError("commit identity is invalid")
        cached = self._blob_cache.get((commit, normalized))
        if cached is not None:
            return cached
        return self.read_blobs(commit, [normalized])[normalized]

    def read_blobs(self, commit: str, paths: Iterable[str]) -> dict[str, bytes]:
        """Read many committed blobs through one bounded cat-file batch."""

        if not HEX40.fullmatch(commit):
            raise GitSubjectError("commit identity is invalid")
        normalized = sorted({normalize_repo_path(path) for path in paths})
        self.read_blob_requests((commit, path) for path in normalized)
        return {path: self._blob_cache[(commit, path)] for path in normalized}

    def read_blob_requests(
        self, requests: Iterable[tuple[str, str]]
    ) -> dict[tuple[str, str], bytes]:
        """Read blobs across multiple commits in one bounded batch."""

        normalized: list[tuple[str, str]] = []
        for commit, path in requests:
            if not HEX40.fullmatch(commit):
                raise GitSubjectError("commit identity is invalid")
            normalized.append((commit, normalize_repo_path(path)))
        normalized = sorted(set(normalized))
        missing = [request for request in normalized if request not in self._blob_cache]
        if missing:
            query = b"".join(
                f"{commit}:{path}\n".encode("utf-8") for commit, path in missing
            )
            output = self._run(["cat-file", "--batch"], input_data=query)
            cursor = 0
            for commit, path in missing:
                newline = output.find(b"\n", cursor)
                if newline < 0:
                    raise GitSubjectError("Git batch response is truncated")
                header = output[cursor:newline]
                cursor = newline + 1
                fields = header.split()
                if len(fields) != 3 or fields[1] != b"blob" or not fields[2].isdigit():
                    raise GitSubjectError(
                        "Git blob is missing or is not a regular blob"
                    )
                size = int(fields[2])
                end = cursor + size
                if end >= len(output) or output[end : end + 1] != b"\n":
                    raise GitSubjectError("Git batch blob length is invalid")
                self._blob_cache[(commit, path)] = output[cursor:end]
                cursor = end + 1
            if cursor != len(output):
                raise GitSubjectError("Git batch response has trailing bytes")
        return {request: self._blob_cache[request] for request in normalized}

    def blob_facts(
        self, requests: Iterable[tuple[str, str]]
    ) -> dict[tuple[str, str], GitBlobFact]:
        """Batch exact Git-blob IDs and SHA-256 values for closed claims."""

        normalized = sorted(
            {(commit, normalize_repo_path(path)) for commit, path in requests}
        )
        blobs = self.read_blob_requests(normalized)
        object_ids = self.object_ids(normalized)
        return {
            request: GitBlobFact(
                commit=request[0],
                path=request[1],
                git_blob=object_ids[request],
                sha256=sha256_bytes(blobs[request]),
            )
            for request in normalized
        }

    @staticmethod
    def _parse_commit_sections(raw: bytes) -> list[dict[str, object]]:
        sections: list[dict[str, object]] = []
        for section in raw.split(b"COMMIT\x00")[1:]:
            fields = section.split(b"\x00")
            if len(fields) < 3:
                raise GitSubjectError("Git history section is malformed")
            try:
                commit = fields[0].decode("ascii")
                parents = fields[1].decode("ascii").split()
                tree = fields[2].decode("ascii")
                paths = sorted(
                    normalize_repo_path(raw_path.removeprefix(b"\n").decode("utf-8"))
                    for raw_path in fields[3:]
                    if raw_path.removeprefix(b"\n")
                )
            except (UnicodeDecodeError, GitSubjectError) as exc:
                raise GitSubjectError("Git history encoding is invalid") from exc
            if (
                not HEX40.fullmatch(commit)
                or not HEX40.fullmatch(tree)
                or any(not HEX40.fullmatch(parent) for parent in parents)
            ):
                raise GitSubjectError("Git history identity is invalid")
            sections.append(
                {"commit": commit, "parents": parents, "tree": tree, "paths": paths}
            )
        return sections

    def added_path_commits(self, source: str, root: str) -> dict[str, str]:
        """Map append-only paths to their unique introducing commit."""

        commit = self.resolve_commit(source)
        normalized = normalize_repo_path(root)
        cached = self._added_path_cache.get((commit, normalized))
        if cached is not None:
            return dict(cached)
        raw = self._run(
            [
                "log",
                "--diff-filter=A",
                "--no-renames",
                "--format=COMMIT%x00%H%x00%P%x00%T%x00",
                "--name-only",
                "-z",
                commit,
                "--",
                normalized,
            ]
        )
        result: dict[str, str] = {}
        for section in self._parse_commit_sections(raw):
            containing = str(section["commit"])
            self._commit_cache[containing] = containing
            for parent in section["parents"]:
                self._commit_cache[str(parent)] = str(parent)
            for path in section["paths"]:
                path = str(path)
                if path in result:
                    raise GitSubjectError("append-only path has multiple introductions")
                result[path] = containing
                self._introduction_cache[(commit, path)] = containing
        self._added_path_cache[(commit, normalized)] = dict(result)
        return dict(result)

    def commit_summaries(self, commits: Iterable[str]) -> dict[str, dict[str, object]]:
        """Read parents, tree, and complete changed paths for exact commits."""

        values = sorted(set(commits))
        if not values or any(not HEX40.fullmatch(commit) for commit in values):
            raise GitSubjectError("commit summary request is invalid")
        missing = [commit for commit in values if commit not in self._summary_cache]
        if missing:
            raw = self._run(
                [
                    "show",
                    "--no-renames",
                    "--format=COMMIT%x00%H%x00%P%x00%T%x00",
                    "--name-only",
                    "-z",
                    *missing,
                    "--",
                ]
            )
            for section in self._parse_commit_sections(raw):
                commit = str(section["commit"])
                self._summary_cache[commit] = section
                self._commit_cache[commit] = commit
                for parent in section["parents"]:
                    self._commit_cache[str(parent)] = str(parent)
        if any(commit not in self._summary_cache for commit in values):
            raise GitSubjectError("commit summary is incomplete")
        return {commit: self._summary_cache[commit] for commit in values}

    def object_ids(
        self, requests: Iterable[tuple[str, str]]
    ) -> dict[tuple[str, str], str]:
        """Resolve exact tree/blob IDs for safe commit:path requests in one batch."""

        normalized: list[tuple[str, str]] = []
        for commit, path in requests:
            if not HEX40.fullmatch(commit):
                raise GitSubjectError("commit identity is invalid")
            normalized.append((commit, normalize_repo_path(path)))
        normalized = sorted(set(normalized))
        missing = [
            request for request in normalized if request not in self._object_id_cache
        ]
        if missing:
            query = b"".join(
                f"{commit}:{path}\n".encode("utf-8") for commit, path in missing
            )
            raw = self._run(
                ["cat-file", "--batch-check=%(objectname)"], input_data=query
            )
            values = raw.decode("ascii", errors="strict").splitlines()
            if len(values) != len(missing) or any(
                not HEX40.fullmatch(value) for value in values
            ):
                raise GitSubjectError("Git object identity batch is invalid")
            self._object_id_cache.update(dict(zip(missing, values, strict=True)))
        return {request: self._object_id_cache[request] for request in normalized}

    def optional_object_ids(
        self, requests: Iterable[tuple[str, str]]
    ) -> dict[tuple[str, str], str | None]:
        """Resolve exact objects while distinguishing a missing path from Git failure."""

        normalized: list[tuple[str, str]] = []
        for commit, path in requests:
            if not HEX40.fullmatch(commit):
                raise GitSubjectError("commit identity is invalid")
            normalized.append((commit, normalize_repo_path(path)))
        normalized = sorted(set(normalized))
        query = b"".join(
            f"{commit}:{path}\n".encode("utf-8") for commit, path in normalized
        )
        raw = self._run(
            ["cat-file", "--batch-check=%(objectname) %(objecttype)"],
            input_data=query,
        )
        lines = raw.decode("ascii", errors="strict").splitlines()
        if len(lines) != len(normalized):
            raise GitSubjectError("Git optional object batch is incomplete")
        result: dict[tuple[str, str], str | None] = {}
        for request, line in zip(normalized, lines, strict=True):
            fields = line.split()
            if (
                len(fields) == 2
                and HEX40.fullmatch(fields[0])
                and fields[1]
                in {
                    "blob",
                    "tree",
                }
            ):
                result[request] = fields[0]
                self._object_id_cache[request] = fields[0]
            elif line.endswith(" missing"):
                result[request] = None
            else:
                raise GitSubjectError("Git optional object identity is invalid")
        return result

    def tree_entries(self, commit: str, root: str) -> list[dict[str, str]]:
        """Return sorted recursive tree entries with exact modes and IDs."""

        if not HEX40.fullmatch(commit):
            raise GitSubjectError("commit identity is invalid")
        normalized = normalize_repo_path(root, allow_empty=True)
        key = (commit, normalized)
        cached = self._tree_cache.get(key)
        if cached is not None:
            return [dict(row) for row in cached]
        args = ["ls-tree", "-r", "-z", commit]
        if normalized:
            args.extend(["--", normalized])
        raw = self._run(args)
        entries: list[dict[str, str]] = []
        for record in raw.split(b"\x00"):
            if not record:
                continue
            try:
                metadata, raw_path = record.split(b"\t", 1)
                mode, object_type, object_id = metadata.decode("ascii").split()
                path = normalize_repo_path(raw_path.decode("utf-8", errors="strict"))
            except (UnicodeDecodeError, ValueError) as exc:
                raise GitSubjectError("Git tree entry is malformed") from exc
            if not HEX40.fullmatch(object_id):
                raise GitSubjectError("Git tree object identity is invalid")
            entries.append(
                {
                    "path": path,
                    "mode": mode,
                    "type": object_type,
                    "git_blob": object_id,
                }
            )
        entries.sort(key=lambda row: row["path"])
        self._tree_cache[key] = tuple(dict(row) for row in entries)
        return entries

    def blob_id(self, commit: str, path: str) -> str:
        normalized = normalize_repo_path(path)
        matches = [
            row
            for row in self.tree_entries(commit, normalized)
            if row["path"] == normalized
        ]
        if len(matches) != 1:
            raise GitSubjectError("Git blob identity is unavailable")
        return matches[0]["git_blob"]

    def list_files(self, commit: str, root: str) -> list[str]:
        normalized = normalize_repo_path(root)
        return [row["path"] for row in self.tree_entries(commit, normalized)]

    def current_head(self) -> str:
        return self.resolve_commit("HEAD")

    def current_branch(self) -> str:
        if self._branch_cache is not None:
            return self._branch_cache
        value = self._run(["rev-parse", "--abbrev-ref", "HEAD"]).decode().strip()
        if not value or value == "HEAD":
            raise GitSubjectError("checkout is detached")
        self._branch_cache = value
        return value

    def first_parent(self, commit: str) -> str:
        return self.resolve_commit(f"{commit}^1")

    def diff_paths(self, base: str, target: str) -> list[str]:
        base_commit = self.resolve_commit(base)
        target_commit = self.resolve_commit(target)
        raw = self._run(["diff", "--name-only", "-z", base_commit, target_commit, "--"])
        try:
            return sorted(
                normalize_repo_path(path)
                for path in raw.decode("utf-8", errors="strict").split("\x00")
                if path
            )
        except UnicodeDecodeError as exc:
            raise GitSubjectError("Git diff paths are not UTF-8") from exc

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        left = self.resolve_commit(ancestor)
        right = self.resolve_commit(descendant)
        reachable = self._ancestor_cache.get(right)
        if reachable is None:
            if right not in self._parent_cache:
                raw = self._run(["rev-list", "--parents", right])
                try:
                    lines = raw.decode("ascii", errors="strict").splitlines()
                except UnicodeDecodeError as exc:
                    raise GitSubjectError("Git ancestry encoding is invalid") from exc
                for line in lines:
                    values = line.split()
                    if not values or any(
                        not HEX40.fullmatch(value) for value in values
                    ):
                        raise GitSubjectError("Git ancestry could not be resolved")
                    commit, *parents = values
                    self._parent_cache[commit] = tuple(parents)
                    self._commit_cache[commit] = commit
                    for parent in parents:
                        self._commit_cache[parent] = parent
            pending = [right]
            visited: set[str] = set()
            while pending:
                commit = pending.pop()
                if commit in visited:
                    continue
                visited.add(commit)
                parents = self._parent_cache.get(commit)
                if parents is None:
                    raise GitSubjectError("Git ancestry could not be resolved")
                pending.extend(parents)
            reachable = frozenset(visited)
            self._ancestor_cache[right] = reachable
        return left in reachable

    def containing_commit(self, source: str, path: str) -> str:
        commit = self.resolve_commit(source)
        normalized = normalize_repo_path(path)
        cached = self._introduction_cache.get((commit, normalized))
        if cached is not None:
            return cached
        raw = self._run(
            [
                "log",
                "--diff-filter=A",
                "--format=%H",
                "--reverse",
                commit,
                "--",
                normalized,
            ]
        )
        commits = [line for line in raw.decode("ascii").splitlines() if line]
        if len(commits) != 1 or not HEX40.fullmatch(commits[0]):
            raise GitSubjectError("append-only containing commit is ambiguous")
        containing = commits[0]
        self._commit_cache[containing] = containing
        self._introduction_cache[(commit, normalized)] = containing
        return containing

    def status_for_paths(self, paths: Iterable[str]) -> list[bytes]:
        normalized = sorted({normalize_repo_path(path) for path in paths})
        raw = self._run(
            [
                "status",
                "--porcelain=v1",
                "-z",
                "--untracked-files=all",
                "--ignored=matching",
                "--",
                *normalized,
            ]
        )
        return [record for record in raw.split(b"\x00") if record]

    def source_bundle(self, commit: str) -> tuple[list[dict[str, object]], str]:
        """Resolve the closed validator source bundle at one commit."""

        source = self.resolve_commit(commit)
        entrypoint = "scripts/validate-engineering-process-program.py"
        all_entries = self.tree_entries(source, "")
        entries = [
            row
            for row in all_entries
            if row["path"].startswith("scripts/program_control/")
            and row["path"].endswith(".py")
        ]
        entry_rows = [row for row in all_entries if row["path"] == entrypoint]
        entries.extend(entry_rows)
        entries.sort(key=lambda row: row["path"])
        if not entries or len(entries) > 100:
            raise GitSubjectError("validator source bundle file count is invalid")
        if len({row["path"] for row in entries}) != len(entries) or any(
            row["type"] != "blob" or row["mode"] not in {"100644", "100755"}
            for row in entries
        ):
            raise GitSubjectError("validator source bundle contains an invalid entry")
        blobs = self.read_blobs(source, [row["path"] for row in entries])
        manifest: list[dict[str, object]] = []
        total_bytes = 0
        for row in entries:
            path = row["path"]
            raw = blobs[path]
            total_bytes += len(raw)
            manifest.append(
                {
                    "path": path,
                    "sha256": sha256_bytes(raw),
                    "git_blob": row["git_blob"],
                    "byte_length": len(raw),
                }
            )
        if total_bytes > 2 * 1024 * 1024:
            raise GitSubjectError("validator source bundle byte limit is exceeded")
        return manifest, canonical_digest(manifest)

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
        rows = self.tree_entries(commit, root)
        regular = [
            row
            for row in rows
            if row["type"] == "blob" and row["mode"] in {"100644", "100755"}
        ]
        if len(regular) != len(rows):
            raise GitSubjectError(
                "program input contains a symlink or non-regular entry"
            )
        blobs = self.read_blobs(commit, [row["path"] for row in regular])
        for row in regular:
            path = row["path"]
            if (
                path in excluded
                or "/evidence/verification/EPP-F01-dashboard-delivery.json" in path
            ):
                continue
            raw = blobs[path]
            entries.append(
                {
                    "path": path,
                    "git_blob": row["git_blob"],
                    "sha256": sha256_bytes(raw),
                }
            )
        return entries, canonical_digest(entries)

    def authoritative_manifest(
        self,
        commit: str,
        program_root: str,
        policy: Mapping[str, Any],
    ) -> tuple[list[dict[str, Any]], str]:
        """Resolve the complete typed authoritative input manifest at one commit."""

        source = self.resolve_commit(commit)
        root = normalize_repo_path(program_root)
        role_rows = [
            row for row in policy.get("path_roles", []) if isinstance(row, Mapping)
        ]
        excluded = {
            f"{root}/dashboard.json",
            f"{root}/evidence/verification/EPP-F01-dashboard-delivery.json",
        }
        selected: list[tuple[dict[str, str], Mapping[str, Any]]] = []
        for tree_row in self.tree_entries(source, ""):
            path = tree_row["path"]
            role = next(
                (
                    row
                    for row in role_rows
                    if fnmatchcase(path, str(row.get("pattern", "")))
                ),
                None,
            )
            if (
                role is None
                or path in excluded
                or role.get("role") == "generated_projection"
            ):
                continue
            if tree_row["type"] != "blob" or tree_row["mode"] not in {
                "100644",
                "100755",
            }:
                raise GitSubjectError("authoritative input is not a regular blob")
            selected.append((tree_row, role))
        by_path = {row["path"]: row for row, _ in selected}
        role_by_path = {row["path"]: role for row, role in selected}
        blobs = self.read_blobs(source, by_path)
        parsed: dict[str, Any] = {}
        for path, raw in blobs.items():
            if path.endswith(".json"):
                try:
                    parsed[path] = strict_loads(raw)
                except ContractError:
                    parsed[path] = None

        def schema_path(document_path: str, schema_ref: str) -> str | None:
            if schema_ref.startswith("https://wright.local/programs/epp/"):
                return f"{root}/schemas/{schema_ref.rsplit('/', 1)[-1]}"
            if "://" in schema_ref:
                return None
            return normalize_repo_path(
                posixpath.normpath(
                    posixpath.join(posixpath.dirname(document_path), schema_ref)
                )
            )

        manifest: list[dict[str, Any]] = []
        for path in sorted(by_path):
            value = parsed.get(path)
            schema_id: str | None = None
            schema_version: str | None = None
            if isinstance(value, Mapping):
                version = value.get("schema_version")
                schema_version = str(version) if isinstance(version, str) else None
                if "/schemas/" in path and isinstance(value.get("$id"), str):
                    schema_id = str(value["$id"])
                elif isinstance(value.get("$schema"), str):
                    schema_ref = str(value["$schema"])
                    resolved = schema_path(path, schema_ref)
                    schema_value = parsed.get(resolved or "")
                    schema_id = (
                        str(schema_value.get("$id"))
                        if isinstance(schema_value, Mapping)
                        and isinstance(schema_value.get("$id"), str)
                        else schema_ref
                    )
            source_row = by_path[path]
            manifest.append(
                {
                    "path": path,
                    "role": str(role_by_path[path].get("role")),
                    "sha256": sha256_bytes(blobs[path]),
                    "git_blob": source_row["git_blob"],
                    "schema_id": schema_id,
                    "schema_version": schema_version,
                }
            )
        return manifest, canonical_digest(manifest)
