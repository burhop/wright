from __future__ import annotations

import os
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .models import DatabaseBusyError, DatabaseFilesystemError

_LOCAL_LOCKS: dict[str, threading.Lock] = {}
_LOCAL_LOCKS_GUARD = threading.Lock()


def _local_lock(path: Path) -> threading.Lock:
    key = str(path.resolve())
    with _LOCAL_LOCKS_GUARD:
        return _LOCAL_LOCKS.setdefault(key, threading.Lock())


def _try_file_lock(handle) -> bool:
    if os.name == "nt":
        import msvcrt

        try:
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except OSError:
            return False
    import fcntl

    try:
        flock = getattr(fcntl, "flock")
        flock(
            handle.fileno(),
            getattr(fcntl, "LOCK_EX") | getattr(fcntl, "LOCK_NB"),
        )
        return True
    except BlockingIOError:
        return False


def _unlock_file(handle) -> None:
    if os.name == "nt":
        import msvcrt

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    else:
        import fcntl

        getattr(fcntl, "flock")(handle.fileno(), getattr(fcntl, "LOCK_UN"))


@contextmanager
def lifecycle_lock(
    database_path: str | os.PathLike[str], timeout: float = 5.0
) -> Iterator[None]:
    path = Path(f"{database_path}.lifecycle.lock")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        handle = path.open("a+b")
    except OSError as exc:
        raise DatabaseFilesystemError("Unable to open database lifecycle lock") from exc

    local = _local_lock(path)
    if not local.acquire(timeout=max(timeout, 0.0)):
        handle.close()
        raise DatabaseBusyError("Database lifecycle operation is already running")

    deadline = time.monotonic() + max(timeout, 0.0)
    locked = False
    try:
        while not (locked := _try_file_lock(handle)):
            if time.monotonic() >= deadline:
                raise DatabaseBusyError(
                    "Database lifecycle operation is already running"
                )
            time.sleep(0.05)
        yield
    finally:
        if locked:
            _unlock_file(handle)
        handle.close()
        local.release()
