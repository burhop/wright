"""Host-wide cooperative application locks for workflow tasks.

OS locks release on process exit. Lock files are persistent addresses, never
deleted while another process may be waiting on the same inode/file handle.
"""

import asyncio
import hashlib
import tempfile
from pathlib import Path
from .workflow_sources import _try_acquire_file_lock, _release_file_lock
from .workflow_source_execution import _error


class ApplicationLease:
    def __init__(self, identity, *, timeout=30, on_wait=None, directory=None):
        self.identity = identity
        self.timeout = timeout
        self.on_wait = on_wait
        self.directory = (
            Path(directory)
            if directory
            else Path(tempfile.gettempdir()) / "wright-workflow-application-locks"
        )
        self.handle = None

    async def __aenter__(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / (
            hashlib.sha256(self.identity.encode()).hexdigest() + ".lock"
        )
        handle = path.open("a+b")
        self.handle = handle
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b"\0")
            handle.flush()
        try:
            async with asyncio.timeout(self.timeout):
                announced = False
                while not _try_acquire_file_lock(handle):
                    if not announced and self.on_wait:
                        await self.on_wait()
                        announced = True
                    await asyncio.sleep(0.1)
            return self
        except TimeoutError as error:
            handle.close()
            self.handle = None
            raise _error(
                "APPLICATION_BUSY",
                "Another workflow is using this application.",
                "Wait for its task to finish before running this task again.",
            ) from error
        except BaseException:
            handle.close()
            self.handle = None
            raise

    async def __aexit__(self, *args):
        if self.handle:
            try:
                _release_file_lock(self.handle)
            finally:
                self.handle.close()
                self.handle = None


def lease_is_active(identity, *, directory=None):
    """Read cooperative ownership without creating an absent historical lease."""
    root = (
        Path(directory)
        if directory
        else Path(tempfile.gettempdir()) / "wright-workflow-application-locks"
    )
    path = root / (hashlib.sha256(identity.encode()).hexdigest() + ".lock")
    try:
        handle = path.open("r+b")
    except FileNotFoundError:
        return None
    with handle:
        if not _try_acquire_file_lock(handle):
            return True
        _release_file_lock(handle)
        return False
