"""Deterministic temporary Git repositories for program-control tests."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


FIXED_GIT_ENV = {
    "GIT_AUTHOR_NAME": "EPP Fixture",
    "GIT_AUTHOR_EMAIL": "epp@example.invalid",
    "GIT_COMMITTER_NAME": "EPP Fixture",
    "GIT_COMMITTER_EMAIL": "epp@example.invalid",
    "GIT_AUTHOR_DATE": "2026-01-02T03:04:05Z",
    "GIT_COMMITTER_DATE": "2026-01-02T03:04:05Z",
}


@dataclass
class GitCommandSpy:
    """Record argument-array Git calls and reject shell-string mutation tricks."""

    calls: list[tuple[str, ...]] = field(default_factory=list)

    def record(self, args: list[str]) -> None:
        assert isinstance(args, list)
        assert all(isinstance(value, str) for value in args)
        self.calls.append(tuple(args))


class GitFixtureBuilder:
    """Build a tiny committed repository under a path containing spaces."""

    def __init__(self, root: Path) -> None:
        self.root = root / "program repo with spaces"
        self.root.mkdir(parents=True)
        self.spy = GitCommandSpy()
        self._git(["init", "-q"])
        self._git(["config", "user.name", FIXED_GIT_ENV["GIT_AUTHOR_NAME"]])
        self._git(["config", "user.email", FIXED_GIT_ENV["GIT_AUTHOR_EMAIL"]])

    def _git(self, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[bytes]:
        self.spy.record(args)
        environment = os.environ.copy()
        environment.update(FIXED_GIT_ENV)
        return subprocess.run(
            ["git", *args],
            cwd=self.root,
            env=environment,
            check=check,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
        )

    def write_bytes(self, relative: str, raw: bytes) -> Path:
        target = self.root / Path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        return target

    def write_json(self, relative: str, value: Any) -> Path:
        raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
        return self.write_bytes(relative, raw)

    def commit(self, message: str = "fixture") -> str:
        self._git(["add", "--all"])
        self._git(["commit", "-q", "-m", message])
        return self._git(["rev-parse", "HEAD"]).stdout.decode().strip()

    def mutate_raw(self, relative: str, old: bytes, new: bytes) -> None:
        target = self.root / Path(relative)
        raw = target.read_bytes()
        if old not in raw:
            raise AssertionError(f"mutation sentinel not found in {relative}")
        target.write_bytes(raw.replace(old, new, 1))

    def git_output(self, *args: str) -> str:
        return self._git(list(args)).stdout.decode("utf-8", errors="strict").strip()
