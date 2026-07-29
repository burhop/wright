"""Canonical manager-neutral Wright-owned paths."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


class LayoutError(ValueError):
    """Raised when a path is outside Wright's safely managed scope."""


_RUNTIME_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


@dataclass(frozen=True, slots=True)
class NativeLayout:
    wright_home: Path
    root: Path
    runtimes: Path
    cache: Path
    state: Path
    logs: Path
    data: Path
    workspaces: Path

    @classmethod
    def from_wright_home(cls, wright_home: str | os.PathLike[str]) -> NativeLayout:
        home = Path(wright_home).expanduser().resolve(strict=False)
        if not home.is_absolute() or home == Path(home.anchor):
            raise LayoutError("wright_home_unsafe")
        root = home
        return cls(
            wright_home=home,
            root=root,
            runtimes=root / "runtimes",
            cache=root / "cache",
            state=root / "state",
            logs=root / "logs",
            data=root / "data",
            workspaces=root / "data" / "workspaces",
        )

    @classmethod
    def from_hermes_home(cls, hermes_home: str | os.PathLike[str]) -> NativeLayout:
        """Migrate callers that supplied a Hermes profile to its former Wright root."""
        return cls.from_wright_home(Path(hermes_home) / "wright")

    @classmethod
    def discover(
        cls, wright_home: str | os.PathLike[str] | None = None
    ) -> NativeLayout:
        if wright_home is None:
            configured = os.environ.get("WRIGHT_HOME", "").strip()
            wright_home = configured or Path.home() / ".wright"
        return cls.from_wright_home(wright_home)

    @property
    def manifest(self) -> Path:
        return self.state / "installation.json"

    @property
    def lock_file(self) -> Path:
        return self.state / "lifecycle.lock"

    @property
    def control_plane_token(self) -> Path:
        return self.data / "control-plane.token"

    def ensure(self) -> None:
        for directory in (
            self.runtimes,
            self.cache,
            self.state,
            self.logs,
            self.data,
            self.workspaces,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def runtime_path(self, runtime_id: str) -> Path:
        if not _RUNTIME_ID.fullmatch(runtime_id):
            raise LayoutError("runtime_id_unsafe")
        return self.require_contained(self.runtimes / runtime_id, self.runtimes)

    def require_contained(self, candidate: Path, parent: Path) -> Path:
        parent_resolved = parent.resolve(strict=False)
        candidate_resolved = candidate.resolve(strict=False)
        if (
            candidate_resolved == parent_resolved
            or not candidate_resolved.is_relative_to(parent_resolved)
        ):
            raise LayoutError("path_outside_managed_root")
        return candidate_resolved

    def require_owned(self, candidate: Path) -> Path:
        candidate_resolved = candidate.resolve(strict=False)
        if candidate_resolved in {
            Path(candidate_resolved.anchor),
            self.root,
        }:
            raise LayoutError("broad_root_refused")
        if not candidate_resolved.is_relative_to(self.root):
            raise LayoutError("path_outside_wright_root")
        return candidate_resolved

    def require_deletion_target(self, candidate: Path, *, allowed_root: Path) -> Path:
        root = allowed_root.resolve(strict=False)
        lexical = candidate.absolute()
        try:
            relative = lexical.relative_to(allowed_root.absolute())
        except ValueError as exc:
            raise LayoutError("delete_target_outside_category") from exc
        if not relative.parts:
            raise LayoutError("delete_category_root_refused")

        current = allowed_root.absolute()
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                raise LayoutError("delete_symlink_refused")

        resolved = lexical.resolve(strict=False)
        if not resolved.is_relative_to(root):
            raise LayoutError("delete_target_outside_category")
        return self.require_owned(resolved)
