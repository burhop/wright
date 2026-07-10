"""Crash-safe, cross-process JSON storage for local Wright secrets."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from collections.abc import Callable, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any

_LOCAL_LOCKS: dict[str, threading.Lock] = {}
_LOCAL_LOCKS_GUARD = threading.Lock()


def _local_lock(path: Path) -> threading.Lock:
    key = str(path.resolve())
    with _LOCAL_LOCKS_GUARD:
        return _LOCAL_LOCKS.setdefault(key, threading.Lock())


class SecretStoreError(RuntimeError):
    """The fallback secret store is unavailable, corrupt, or insecure."""


if os.name == "nt":
    import msvcrt

    def _lock(handle: Any) -> None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)

    def _unlock(handle: Any) -> None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)

else:
    import fcntl

    def _lock(handle: Any) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)

    def _unlock(handle: Any) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class AtomicSecretStore:
    """Serialize read-modify-write transactions through a stable lock file."""

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()
        self.lock_path = self.path.with_name(f"{self.path.name}.lock")

    def _ensure_directory(self) -> None:
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            os.chmod(self.path.parent, 0o700)
        except OSError as exc:
            if os.name != "nt":
                raise SecretStoreError("Cannot restrict secret directory") from exc

    @contextmanager
    def _transaction_lock(self):
        self._ensure_directory()
        with _local_lock(self.lock_path):
            with self.lock_path.open("a+b") as handle:
                if handle.tell() == 0:
                    handle.write(b"\0")
                    handle.flush()
                try:
                    os.chmod(self.lock_path, 0o600)
                except OSError as exc:
                    if os.name != "nt":
                        raise SecretStoreError(
                            "Cannot restrict secret lock file"
                        ) from exc
                _lock(handle)
                try:
                    yield
                finally:
                    _unlock(handle)

    def _read_unlocked(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SecretStoreError("Secret store is unreadable or corrupt") from exc
        if not isinstance(payload, dict) or not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in payload.items()
        ):
            raise SecretStoreError("Secret store has an invalid format")
        return payload

    def read(self) -> dict[str, str]:
        with self._transaction_lock():
            return self._read_unlocked()

    def _write_unlocked(self, data: Mapping[str, str]) -> None:
        temporary: Path | None = None
        try:
            descriptor, name = tempfile.mkstemp(
                prefix=f".{self.path.name}.", suffix=".tmp", dir=self.path.parent
            )
            temporary = Path(name)
            try:
                os.chmod(temporary, 0o600)
            except OSError as exc:
                if os.name != "nt":
                    raise SecretStoreError(
                        "Cannot restrict temporary secret file"
                    ) from exc
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(dict(sorted(data.items())), handle, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
            temporary = None
            try:
                os.chmod(self.path, 0o600)
            except OSError as exc:
                if os.name != "nt":
                    raise SecretStoreError("Cannot restrict secret store") from exc
            if os.name != "nt":
                directory_fd = os.open(self.path.parent, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
        except OSError as exc:
            raise SecretStoreError("Atomic secret-store update failed") from exc
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def update(self, transform: Callable[[dict[str, str]], None]) -> dict[str, str]:
        with self._transaction_lock():
            data = self._read_unlocked()
            transform(data)
            self._write_unlocked(data)
            return dict(data)

    def set_many(
        self, updates: Mapping[str, str], deletes: set[str] | None = None
    ) -> dict[str, str]:
        def transform(data: dict[str, str]) -> None:
            for key in deletes or set():
                data.pop(key, None)
            data.update(updates)

        return self.update(transform)
