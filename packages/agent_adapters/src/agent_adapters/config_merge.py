"""Atomic merge-only writers for provider configuration files."""

from __future__ import annotations

import copy
import os
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

_LOCKS: dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


def _lock_for(path: Path) -> threading.Lock:
    key = str(path.resolve())
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(key, threading.Lock())


def atomic_merge_yaml(
    path: str | Path, update: Callable[[dict[str, Any]], None]
) -> bool:
    """Apply an owned-key update without discarding unrelated YAML entries."""
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    with _lock_for(target):
        if target.exists():
            loaded = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
            if not isinstance(loaded, dict):
                raise ValueError("Provider configuration must be a mapping")
        else:
            loaded = {}
        changed = copy.deepcopy(loaded)
        update(changed)
        if changed == loaded:
            return False

        temporary: Path | None = None
        try:
            descriptor, name = tempfile.mkstemp(
                prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
            )
            temporary = Path(name)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                yaml.safe_dump(
                    changed, handle, default_flow_style=False, sort_keys=False
                )
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
            temporary = None
            return True
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
