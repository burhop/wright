"""Confirmation-bound deletion of Wright-owned user data."""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path

from .layout import LayoutError, NativeLayout


@dataclass(frozen=True, slots=True)
class PurgePlan:
    installation_id: str
    targets: tuple[Path, ...]
    confirmation_code: str


class PurgeManager:
    def __init__(self, layout: NativeLayout) -> None:
        self.layout = layout

    def validate_target(self, candidate: Path) -> Path:
        lexical = candidate.absolute()
        expected = self.layout.data.absolute()
        resolved = lexical.resolve(strict=False)
        if resolved != self.layout.data.resolve(strict=False) or lexical != expected:
            raise LayoutError("purge_scope_must_equal_data_root")
        self.layout.require_owned(resolved)
        if lexical.is_symlink():
            raise LayoutError("purge_data_root_symlink_refused")
        if lexical.exists():
            for child in lexical.rglob("*"):
                if child.is_symlink():
                    raise LayoutError("purge_symlink_refused")
        return lexical

    def plan(self, installation_id: str) -> PurgePlan:
        target = self.validate_target(self.layout.data)
        canonical = f"{installation_id}|data|{target}".encode("utf-8")
        code = hashlib.sha256(canonical).hexdigest()[:16]
        return PurgePlan(installation_id, (target,), code)

    def execute(self, plan: PurgePlan, confirmation: str) -> tuple[str, ...]:
        current = self.plan(plan.installation_id)
        if current.targets != plan.targets or confirmation != current.confirmation_code:
            raise ValueError("invalid_confirmation")
        removed: list[str] = []
        for target in current.targets:
            self.validate_target(target)
            if target.exists():
                shutil.rmtree(target)
                removed.append("data")
        return tuple(removed)
