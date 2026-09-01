"""Workspace-owned storage for human-editable engineering workflow source.

The source is intentionally opaque to this module: syntax and semantic checks
belong to the workflow command layer. This store enforces storage integrity,
workspace confinement, bounded UTF-8 content, and compare-and-swap updates.

Each workflow has one visible definition file at
``workflows/<slug>.workflow.wflow``. Wright-owned revision records live under
``.wright/workflow-sources`` so implementation state never leaks into the
engineer-authored definition. The committed head and hash-chained, write-once
journal make an externally restored historical definition fail closed instead
of silently rewinding its revision identity.
"""

from __future__ import annotations

import hashlib
import errno
import json
import os
import re
import secrets
import stat
import tempfile
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from .errors import WorkspaceTimeoutError
from .executor import BoundedExecutor
from .workspace_path import WorkspacePath

WORKFLOW_SOURCE_MAX_BYTES = 1024 * 1024
WORKFLOW_SOURCE_METADATA_MAX_BYTES = 16 * 1024
WORKFLOW_SOURCE_MAX_REVISIONS = 100_000
WORKFLOW_SOURCE_LOCK_TIMEOUT_SECONDS = 5.0

_SOURCE_FILE = re.compile(
    r"^workflows/(?P<slug>[a-z0-9][a-z0-9-]{0,62})\.workflow\.wflow$"
)
_REVISION_FILE = re.compile(r"^(?P<revision>[0-9]{20})\.json$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_WINDOWS_RESERVED_SLUGS = {
    "aux",
    "con",
    "nul",
    "prn",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
}
_JOURNAL_SCHEMA_VERSION = 1
_HEAD_SCHEMA_VERSION = 1
_RECORD_KEYS = {
    "schema_version",
    "storage_revision",
    "storage_digest",
    "definition_revision",
    "semantic_change_validated",
    "previous_storage_digest",
    "previous_record_digest",
    "size_bytes",
    "updated_at",
}
_HEAD_KEYS = {
    "schema_version",
    "storage_revision",
    "storage_digest",
    "definition_revision",
    "record_digest",
}


class WorkflowSourceStorageError(RuntimeError):
    """A stable, user-safe workflow-source storage failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class WorkflowSourceConflictError(WorkflowSourceStorageError):
    """The supplied compare-and-swap base is no longer current."""

    def __init__(self, storage_revision: int, storage_digest: str) -> None:
        super().__init__(
            "workflow_source_conflict",
            "The workflow source changed after it was read",
        )
        self.storage_revision = storage_revision
        self.storage_digest = storage_digest


@dataclass(frozen=True, slots=True)
class WorkflowSourceDocument:
    path: str
    storage_revision: int
    storage_digest: str
    definition_revision: int
    source: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class _CommittedState:
    document: WorkflowSourceDocument
    record_digest: str


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _source_bytes(source: str) -> bytes:
    try:
        content = source.encode("utf-8")
    except UnicodeEncodeError as error:
        raise WorkflowSourceStorageError(
            "workflow_source_encoding",
            "Workflow source must be valid UTF-8 text",
        ) from error
    if len(content) > WORKFLOW_SOURCE_MAX_BYTES:
        raise WorkflowSourceStorageError(
            "workflow_source_too_large",
            f"Workflow source exceeds the {WORKFLOW_SOURCE_MAX_BYTES}-byte limit",
        )
    return content


def _positive_int(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        return None
    return value


if os.name == "nt":
    import ctypes
    import msvcrt
    from ctypes import wintypes

    _FILE_ATTRIBUTE_DIRECTORY = 0x00000010
    _FILE_ATTRIBUTE_REPARSE_POINT = 0x00000400
    _FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
    _FILE_FLAG_OPEN_REPARSE_POINT = 0x00200000
    _FILE_READ_ATTRIBUTES = 0x00000080
    _FILE_SHARE_READ = 0x00000001
    _FILE_SHARE_WRITE = 0x00000002
    _OPEN_EXISTING = 3
    _INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    class _ByHandleFileInformation(ctypes.Structure):
        _fields_ = [
            ("dwFileAttributes", wintypes.DWORD),
            ("ftCreationTime", wintypes.FILETIME),
            ("ftLastAccessTime", wintypes.FILETIME),
            ("ftLastWriteTime", wintypes.FILETIME),
            ("dwVolumeSerialNumber", wintypes.DWORD),
            ("nFileSizeHigh", wintypes.DWORD),
            ("nFileSizeLow", wintypes.DWORD),
            ("nNumberOfLinks", wintypes.DWORD),
            ("nFileIndexHigh", wintypes.DWORD),
            ("nFileIndexLow", wintypes.DWORD),
        ]

    _kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _create_file = _kernel32.CreateFileW
    _create_file.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    _create_file.restype = wintypes.HANDLE
    _get_file_information = _kernel32.GetFileInformationByHandle
    _get_file_information.argtypes = [
        wintypes.HANDLE,
        ctypes.POINTER(_ByHandleFileInformation),
    ]
    _get_file_information.restype = wintypes.BOOL
    _close_handle = _kernel32.CloseHandle
    _close_handle.argtypes = [wintypes.HANDLE]
    _close_handle.restype = wintypes.BOOL

    def _open_windows_directory(path: Path) -> tuple[int, tuple[int, int]]:
        handle = _create_file(
            str(path),
            _FILE_READ_ATTRIBUTES,
            _FILE_SHARE_READ | _FILE_SHARE_WRITE,
            None,
            _OPEN_EXISTING,
            _FILE_FLAG_BACKUP_SEMANTICS | _FILE_FLAG_OPEN_REPARSE_POINT,
            None,
        )
        if handle == _INVALID_HANDLE_VALUE:
            raise ctypes.WinError(ctypes.get_last_error())
        information = _ByHandleFileInformation()
        if not _get_file_information(handle, ctypes.byref(information)):
            error = ctypes.WinError(ctypes.get_last_error())
            _close_handle(handle)
            raise error
        if (
            not information.dwFileAttributes & _FILE_ATTRIBUTE_DIRECTORY
            or information.dwFileAttributes & _FILE_ATTRIBUTE_REPARSE_POINT
        ):
            _close_handle(handle)
            raise WorkflowSourceStorageError(
                "workflow_source_path_invalid",
                "Workflow source paths may not contain symbolic links or reparse points",
            )
        identity = (
            int(information.dwVolumeSerialNumber),
            (int(information.nFileIndexHigh) << 32)
            | int(information.nFileIndexLow),
        )
        return int(handle), identity

    def _close_windows_directory(handle: int) -> None:
        _close_handle(wintypes.HANDLE(handle))

    def _try_acquire_file_lock(handle: BinaryIO) -> bool:
        handle.seek(0)
        try:
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except OSError as error:
            if error.errno in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                return False
            raise

    def _release_file_lock(handle: BinaryIO) -> None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)

else:
    import fcntl

    def _try_acquire_file_lock(handle: BinaryIO) -> bool:
        try:
            fcntl.flock(  # type: ignore[attr-defined]
                handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB
            )
            return True
        except OSError as error:
            if error.errno in {errno.EACCES, errno.EAGAIN}:
                return False
            raise

    def _release_file_lock(handle: BinaryIO) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)  # type: ignore[attr-defined]


@dataclass(slots=True)
class _DirectoryCapability:
    """Pinned identity for one link-free directory used by mutations."""

    path: Path
    descriptor: int | None = None
    windows_handle: int | None = None
    windows_identity: tuple[int, int] | None = None

    def assert_current(self) -> None:
        try:
            if os.name == "nt":
                assert self.windows_identity is not None
                probe, identity = _open_windows_directory(self.path)
                try:
                    if identity != self.windows_identity:
                        raise WorkflowSourceStorageError(
                            "workflow_source_path_invalid",
                            "Workflow source directory identity changed during a mutation",
                        )
                finally:
                    _close_windows_directory(probe)
                return
            assert self.descriptor is not None
            path_stat = os.stat(self.path, follow_symlinks=False)
            descriptor_stat = os.fstat(self.descriptor)
            if not os.path.samestat(path_stat, descriptor_stat):
                raise WorkflowSourceStorageError(
                    "workflow_source_path_invalid",
                    "Workflow source directory identity changed during a mutation",
                )
        except WorkflowSourceStorageError:
            raise
        except OSError as error:
            raise WorkflowSourceStorageError(
                "workflow_source_path_invalid",
                "Workflow source directory identity could not be verified",
            ) from error

    def lstat(self, name: str) -> os.stat_result:
        if os.name == "nt":
            return os.lstat(self.path / name)
        assert self.descriptor is not None
        return os.stat(name, dir_fd=self.descriptor, follow_symlinks=False)

    def open_file(self, name: str, flags: int, mode: int = 0o600) -> int:
        if os.name == "nt":
            return os.open(self.path / name, flags, mode)
        assert self.descriptor is not None
        return os.open(name, flags, mode, dir_fd=self.descriptor)

    def replace(self, source: str, destination: str) -> None:
        if os.name == "nt":
            os.replace(self.path / source, self.path / destination)
            return
        assert self.descriptor is not None
        os.replace(
            source,
            destination,
            src_dir_fd=self.descriptor,
            dst_dir_fd=self.descriptor,
        )

    def unlink(self, name: str, *, missing_ok: bool = False) -> None:
        try:
            if os.name == "nt":
                (self.path / name).unlink()
            else:
                assert self.descriptor is not None
                os.unlink(name, dir_fd=self.descriptor)
        except FileNotFoundError:
            if not missing_ok:
                raise

    def close(self) -> None:
        if self.windows_handle is not None:
            _close_windows_directory(self.windows_handle)
            self.windows_handle = None
        if self.descriptor is not None:
            os.close(self.descriptor)
            self.descriptor = None


class WorkspaceWorkflowSourceStore:
    """Synchronous file store rooted in one server-authorized workspace."""

    _locks_guard = threading.Lock()
    _locks: dict[str, threading.Lock] = {}

    def __init__(
        self,
        workspace_dir: str,
        *,
        lock_timeout_seconds: float = WORKFLOW_SOURCE_LOCK_TIMEOUT_SECONDS,
    ) -> None:
        if lock_timeout_seconds <= 0:
            raise ValueError("lock_timeout_seconds must be positive")
        self._paths = WorkspacePath(workspace_dir)
        self._lock_timeout_seconds = lock_timeout_seconds
        self._active_directory_capabilities: dict[
            str, _DirectoryCapability
        ] | None = None

    @staticmethod
    def _directory_key(path: Path) -> str:
        return os.path.normcase(os.path.normpath(str(path)))

    def _relative_directory_parts(self, path: Path) -> tuple[str, ...]:
        root = os.path.normpath(str(self._paths.root))
        candidate = os.path.normpath(str(path))
        try:
            common = os.path.commonpath((root, candidate))
        except ValueError as error:
            raise WorkflowSourceStorageError(
                "workflow_source_path_invalid",
                "Workflow source directory is not workspace-confined",
            ) from error
        if os.path.normcase(common) != os.path.normcase(root):
            raise WorkflowSourceStorageError(
                "workflow_source_path_invalid",
                "Workflow source directory is not workspace-confined",
            )
        relative = os.path.relpath(candidate, root)
        if relative == ".":
            return ()
        parts = tuple(Path(relative).parts)
        if any(part in {"", ".", ".."} for part in parts):
            raise WorkflowSourceStorageError(
                "workflow_source_path_invalid",
                "Workflow source directory is not workspace-confined",
            )
        return parts

    @staticmethod
    def _pin_directory(path: Path, *, parent: _DirectoryCapability | None = None) -> _DirectoryCapability:
        try:
            if os.name == "nt":
                handle, identity = _open_windows_directory(path)
                return _DirectoryCapability(
                    path=path,
                    windows_handle=handle,
                    windows_identity=identity,
                )
            flags = (
                os.O_RDONLY
                | getattr(os, "O_DIRECTORY", 0)
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0)
            )
            if parent is None:
                descriptor = os.open(path, flags)
            else:
                assert parent.descriptor is not None
                descriptor = os.open(path.name, flags, dir_fd=parent.descriptor)
            descriptor_stat = os.fstat(descriptor)
            if not stat.S_ISDIR(descriptor_stat.st_mode):
                os.close(descriptor)
                raise WorkflowSourceStorageError(
                    "workflow_source_path_invalid",
                    "Workflow source path component must be a regular directory",
                )
            return _DirectoryCapability(path=path, descriptor=descriptor)
        except WorkflowSourceStorageError:
            raise
        except OSError as error:
            raise WorkflowSourceStorageError(
                "workflow_source_path_invalid",
                "Workflow source directory could not be opened safely",
            ) from error

    def _before_filesystem_mutation(self, _target: Path) -> None:
        """Deterministic race-test seam; production intentionally does nothing."""

    @contextmanager
    def _directory_capability(
        self, directory: Path, *, create: bool
    ) -> Iterator[_DirectoryCapability]:
        parts = self._relative_directory_parts(directory)
        capabilities: list[_DirectoryCapability] = []
        try:
            root = self._pin_directory(self._paths.root)
            capabilities.append(root)
            parent = root
            current = self._paths.root
            for part in parts:
                current = current / part
                try:
                    component_stat = parent.lstat(part)
                except FileNotFoundError:
                    if not create:
                        raise
                    self._before_filesystem_mutation(current)
                    parent.assert_current()
                    try:
                        if os.name == "nt":
                            current.mkdir()
                        else:
                            assert parent.descriptor is not None
                            os.mkdir(part, mode=0o700, dir_fd=parent.descriptor)
                    except FileExistsError:
                        # A concurrent creator is acceptable only if the fresh
                        # component is the same link-free directory pinned below.
                        pass
                    component_stat = parent.lstat(part)
                file_attributes = getattr(component_stat, "st_file_attributes", 0)
                if (
                    not stat.S_ISDIR(component_stat.st_mode)
                    or stat.S_ISLNK(component_stat.st_mode)
                    or file_attributes
                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
                ):
                    raise WorkflowSourceStorageError(
                        "workflow_source_path_invalid",
                        "Workflow source paths may not contain symbolic links or reparse points",
                    )
                child = self._pin_directory(current, parent=parent)
                capabilities.append(child)
                parent = child
            parent.assert_current()
            yield parent
        finally:
            for capability in reversed(capabilities):
                capability.close()

    @contextmanager
    def _directory_for_path(self, path: Path) -> Iterator[_DirectoryCapability]:
        key = self._directory_key(path.parent)
        active = self._active_directory_capabilities or {}
        capability = active.get(key)
        if capability is not None:
            capability.assert_current()
            yield capability
            return
        with self._directory_capability(path.parent, create=True) as opened:
            yield opened

    @classmethod
    def _lock_for(cls, key: str) -> threading.Lock:
        with cls._locks_guard:
            return cls._locks.setdefault(key, threading.Lock())

    def _source_path(self, user_path: str) -> tuple[str, str, Path]:
        normalized = user_path.replace("\\", "/")
        match = _SOURCE_FILE.fullmatch(normalized)
        if match is None:
            raise WorkflowSourceStorageError(
                "workflow_source_path_invalid",
                "Workflow source path must be workflows/<safe-slug>.workflow.wflow",
            )
        slug = match.group("slug")
        if slug in _WINDOWS_RESERVED_SLUGS:
            raise WorkflowSourceStorageError(
                "workflow_source_path_invalid",
                "Workflow source slug is reserved by a supported host platform",
            )
        try:
            resolved = self._paths.resolve(normalized)
        except ValueError as error:
            raise WorkflowSourceStorageError(
                "workflow_source_path_invalid", str(error)
            ) from error
        return normalized, slug, resolved

    def _metadata_directory(self, slug: str) -> Path:
        try:
            return self._paths.resolve(f".wright/workflow-sources/{slug}")
        except ValueError as error:
            raise WorkflowSourceStorageError(
                "workflow_source_path_invalid", str(error)
            ) from error

    def _revision_directory(self, slug: str) -> Path:
        return self._metadata_directory(slug) / "revisions"

    def _head_path(self, slug: str) -> Path:
        return self._metadata_directory(slug) / "head.json"

    def _atomic_write(self, path: Path, content: bytes) -> None:
        with self._directory_for_path(path) as directory:
            self._before_filesystem_mutation(path)
            directory.assert_current()
            if os.name == "nt":
                descriptor, temporary_name = tempfile.mkstemp(
                    prefix=".wright-workflow-source-", dir=directory.path
                )
                temporary_leaf = Path(temporary_name).name
            else:
                descriptor = -1
                temporary_leaf = ""
                for _attempt in range(16):
                    temporary_leaf = (
                        f".wright-workflow-source-{secrets.token_hex(12)}"
                    )
                    try:
                        descriptor = directory.open_file(
                            temporary_leaf,
                            os.O_WRONLY
                            | os.O_CREAT
                            | os.O_EXCL
                            | getattr(os, "O_NOFOLLOW", 0),
                        )
                        break
                    except FileExistsError:
                        continue
                if descriptor < 0:
                    raise WorkflowSourceStorageError(
                        "workflow_source_unavailable",
                        "Workflow source temporary file could not be allocated",
                    )
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(content)
                    stream.flush()
                    os.fsync(stream.fileno())
                self._before_filesystem_mutation(path)
                directory.assert_current()
                directory.replace(temporary_leaf, path.name)
            finally:
                directory.unlink(temporary_leaf, missing_ok=True)

    def _write_once(self, path: Path, content: bytes) -> None:
        """Create one immutable journal entry without an overwrite code path."""

        with self._directory_for_path(path) as directory:
            descriptor: int | None = None
            created = False
            try:
                self._before_filesystem_mutation(path)
                directory.assert_current()
                descriptor = directory.open_file(
                    path.name,
                    os.O_WRONLY
                    | os.O_CREAT
                    | os.O_EXCL
                    | getattr(os, "O_BINARY", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                )
                created = True
                with os.fdopen(descriptor, "wb") as stream:
                    descriptor = None
                    stream.write(content)
                    stream.flush()
                    os.fsync(stream.fileno())
            except FileExistsError as error:
                raise WorkflowSourceStorageError(
                    "workflow_source_integrity",
                    "Workflow source revision journal would overwrite committed history",
                ) from error
            except BaseException:
                if descriptor is not None:
                    os.close(descriptor)
                if created:
                    directory.unlink(path.name, missing_ok=True)
                raise

    def _unlink(self, path: Path, *, missing_ok: bool = False) -> None:
        with self._directory_for_path(path) as directory:
            self._before_filesystem_mutation(path)
            directory.assert_current()
            directory.unlink(path.name, missing_ok=missing_ok)

    def _ensure_metadata_directory(self, slug: str) -> Path:
        directory = self._metadata_directory(slug)
        with self._directory_capability(directory, create=True) as capability:
            capability.assert_current()
        return directory

    @staticmethod
    def _validate_lock_stat(lock_stat: os.stat_result) -> None:
        file_attributes = getattr(lock_stat, "st_file_attributes", 0)
        is_reparse = bool(
            file_attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        )
        if (
            not stat.S_ISREG(lock_stat.st_mode)
            or is_reparse
            or lock_stat.st_nlink != 1
            or lock_stat.st_size not in {0, 1}
        ):
            raise WorkflowSourceStorageError(
                "workflow_source_path_invalid",
                "Workflow source lock must be a private regular file",
            )

    @classmethod
    def _validate_open_lock(
        cls,
        directory: _DirectoryCapability,
        lock_path: Path,
        handle: BinaryIO,
    ) -> None:
        try:
            directory.assert_current()
            path_stat = directory.lstat(lock_path.name)
            handle_stat = os.fstat(handle.fileno())
        except OSError as error:
            raise WorkflowSourceStorageError(
                "workflow_source_path_invalid",
                "Workflow source lock identity could not be verified",
            ) from error
        cls._validate_lock_stat(path_stat)
        cls._validate_lock_stat(handle_stat)
        if not os.path.samestat(path_stat, handle_stat):
            raise WorkflowSourceStorageError(
                "workflow_source_path_invalid",
                "Workflow source lock changed while it was opened",
            )

    @classmethod
    def _open_lock_file(
        cls, directory: _DirectoryCapability, lock_path: Path
    ) -> BinaryIO:
        """Open a private lock file without following or writing through links."""

        for _attempt in range(3):
            try:
                directory.assert_current()
                initial_stat = directory.lstat(lock_path.name)
            except FileNotFoundError:
                initial_stat = None
            except OSError as error:
                raise WorkflowSourceStorageError(
                    "workflow_source_path_invalid",
                    "Workflow source lock could not be inspected",
                ) from error
            if initial_stat is not None:
                cls._validate_lock_stat(initial_stat)

            flags = os.O_RDWR | getattr(os, "O_BINARY", 0)
            created = initial_stat is None
            if created:
                flags |= os.O_CREAT | os.O_EXCL
            flags |= getattr(os, "O_NOFOLLOW", 0)
            try:
                directory.assert_current()
                descriptor = directory.open_file(lock_path.name, flags)
            except (FileExistsError, FileNotFoundError):
                # The path raced between inspection and open. Retry from a
                # fresh lstat; no file has been written by this attempt.
                continue
            except OSError as error:
                raise WorkflowSourceStorageError(
                    "workflow_source_path_invalid",
                    "Workflow source lock could not be opened safely",
                ) from error

            handle = os.fdopen(descriptor, "r+b", buffering=0)
            try:
                cls._validate_open_lock(directory, lock_path, handle)
                if initial_stat is not None and not os.path.samestat(
                    initial_stat, os.fstat(handle.fileno())
                ):
                    raise WorkflowSourceStorageError(
                        "workflow_source_path_invalid",
                        "Workflow source lock changed while it was opened",
                    )
                return handle
            except BaseException:
                opened_stat = os.fstat(handle.fileno())
                handle.close()
                if created:
                    try:
                        current_stat = directory.lstat(lock_path.name)
                        if os.path.samestat(current_stat, opened_stat):
                            directory.unlink(lock_path.name)
                    except OSError:
                        pass
                raise

        raise WorkflowSourceStorageError(
            "workflow_source_path_invalid",
            "Workflow source lock changed repeatedly while it was opened",
        )

    @contextmanager
    def _transaction(self, slug: str, source_path: Path) -> Iterator[None]:
        """Serialize the complete CAS transaction across threads and processes."""

        local_lock = self._lock_for(os.path.normcase(str(source_path)))
        deadline = time.monotonic() + self._lock_timeout_seconds
        if not local_lock.acquire(timeout=self._lock_timeout_seconds):
            raise WorkflowSourceStorageError(
                "workflow_source_unavailable",
                "Workflow source is busy; retry after the active save finishes",
            )
        try:
            directory = self._metadata_directory(slug)
            revisions = self._revision_directory(slug)
            source_directory = source_path.parent
            with ExitStack() as stack:
                metadata_capability = stack.enter_context(
                    self._directory_capability(directory, create=True)
                )
                revision_capability = stack.enter_context(
                    self._directory_capability(revisions, create=True)
                )
                source_capability = stack.enter_context(
                    self._directory_capability(source_directory, create=True)
                )
                previous_capabilities = self._active_directory_capabilities
                self._active_directory_capabilities = {
                    self._directory_key(directory): metadata_capability,
                    self._directory_key(revisions): revision_capability,
                    self._directory_key(source_directory): source_capability,
                }
                lock_path = directory / ".lock"
                handle: BinaryIO | None = None
                locked = False
                try:
                    handle = self._open_lock_file(metadata_capability, lock_path)
                    self._validate_open_lock(
                        metadata_capability, lock_path, handle
                    )
                    if os.fstat(handle.fileno()).st_size == 0:
                        self._before_filesystem_mutation(lock_path)
                        metadata_capability.assert_current()
                        handle.write(b"\0")
                        handle.flush()
                        os.fsync(handle.fileno())
                        self._validate_open_lock(
                            metadata_capability, lock_path, handle
                        )
                    while not _try_acquire_file_lock(handle):
                        if time.monotonic() >= deadline:
                            raise WorkflowSourceStorageError(
                                "workflow_source_unavailable",
                                "Workflow source is busy; retry after the active save finishes",
                            )
                        time.sleep(min(0.02, max(0.0, deadline - time.monotonic())))
                    locked = True
                    self._validate_open_lock(
                        metadata_capability, lock_path, handle
                    )
                    yield
                finally:
                    self._active_directory_capabilities = previous_capabilities
                    if locked and handle is not None:
                        try:
                            _release_file_lock(handle)
                        except OSError:
                            # Closing the descriptor releases a process lock. Do
                            # not turn a completed commit into a reported failure
                            # solely because the explicit unlock call failed.
                            pass
                    if handle is not None:
                        try:
                            handle.close()
                        except OSError:
                            pass
        finally:
            local_lock.release()

    def _read_bounded_file(
        self,
        path: Path,
        *,
        max_bytes: int,
        label: str,
        invalid_code: str,
        too_large_code: str,
        too_large_message: str,
    ) -> bytes:
        """Read a pinned regular file without allocating beyond its limit."""

        descriptor: int | None = None
        try:
            with self._directory_for_path(path) as directory:
                directory.assert_current()
                path_stat = directory.lstat(path.name)
                self._validate_bounded_read_stat(
                    path_stat,
                    label=label,
                    invalid_code=invalid_code,
                )
                if path_stat.st_size > max_bytes:
                    raise WorkflowSourceStorageError(
                        too_large_code, too_large_message
                    )

                descriptor = directory.open_file(
                    path.name,
                    os.O_RDONLY
                    | getattr(os, "O_BINARY", 0)
                    | getattr(os, "O_CLOEXEC", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                )
                opened_stat = os.fstat(descriptor)
                self._validate_bounded_read_stat(
                    opened_stat,
                    label=label,
                    invalid_code=invalid_code,
                )
                directory.assert_current()
                current_stat = directory.lstat(path.name)
                self._validate_bounded_read_stat(
                    current_stat,
                    label=label,
                    invalid_code=invalid_code,
                )
                if not os.path.samestat(path_stat, opened_stat) or not os.path.samestat(
                    current_stat, opened_stat
                ):
                    raise WorkflowSourceStorageError(
                        invalid_code,
                        f"Workflow source {label} changed while it was opened",
                    )
                if opened_stat.st_size > max_bytes:
                    raise WorkflowSourceStorageError(
                        too_large_code, too_large_message
                    )

                with os.fdopen(descriptor, "rb") as stream:
                    descriptor = None
                    content = stream.read(max_bytes + 1)
                    final_stat = os.fstat(stream.fileno())
                if len(content) > max_bytes:
                    raise WorkflowSourceStorageError(
                        too_large_code, too_large_message
                    )
                if final_stat.st_size != len(content):
                    raise WorkflowSourceStorageError(
                        invalid_code,
                        f"Workflow source {label} changed while it was read",
                    )
                return content
        except WorkflowSourceStorageError:
            raise
        except OSError as error:
            raise WorkflowSourceStorageError(
                "workflow_source_integrity",
                f"Workflow source {label} is unreadable",
            ) from error
        finally:
            if descriptor is not None:
                os.close(descriptor)

    @staticmethod
    def _validate_bounded_read_stat(
        file_stat: os.stat_result,
        *,
        label: str,
        invalid_code: str,
    ) -> None:
        file_attributes = getattr(file_stat, "st_file_attributes", 0)
        if (
            not stat.S_ISREG(file_stat.st_mode)
            or stat.S_ISLNK(file_stat.st_mode)
            or file_attributes
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        ):
            raise WorkflowSourceStorageError(
                invalid_code,
                f"Workflow source {label} is invalid",
            )

    def _decode_json(self, path: Path, *, label: str) -> tuple[dict[str, object], bytes]:
        content = self._read_bounded_file(
            path,
            max_bytes=WORKFLOW_SOURCE_METADATA_MAX_BYTES,
            label=label,
            invalid_code="workflow_source_integrity",
            too_large_code="workflow_source_integrity",
            too_large_message=f"Workflow source {label} exceeds its metadata limit",
        )
        try:
            value = json.loads(content.decode("utf-8"))
        except (UnicodeError, ValueError, RecursionError) as error:
            raise WorkflowSourceStorageError(
                "workflow_source_integrity",
                f"Workflow source {label} is unreadable",
            ) from error
        if not isinstance(value, dict):
            raise WorkflowSourceStorageError(
                "workflow_source_integrity",
                f"Workflow source {label} has an invalid format",
            )
        return value, content

    def _journal_paths(self, slug: str) -> dict[int, Path]:
        directory = self._revision_directory(slug)
        if not directory.is_dir() or directory.is_symlink():
            raise WorkflowSourceStorageError(
                "workflow_source_integrity",
                "Workflow source revision journal is missing or invalid",
            )
        paths: dict[int, Path] = {}
        try:
            candidates = directory.iterdir()
            for entry_count, candidate in enumerate(candidates, start=1):
                if entry_count > WORKFLOW_SOURCE_MAX_REVISIONS:
                    raise WorkflowSourceStorageError(
                        "workflow_source_integrity",
                        "Workflow source revision journal exceeds its supported limit",
                    )
                match = _REVISION_FILE.fullmatch(candidate.name)
                if match is None:
                    raise WorkflowSourceStorageError(
                        "workflow_source_integrity",
                        "Workflow source revision journal contains an unexpected entry",
                    )
                revision = int(match.group("revision"))
                if not 1 <= revision <= WORKFLOW_SOURCE_MAX_REVISIONS:
                    raise WorkflowSourceStorageError(
                        "workflow_source_integrity",
                        "Workflow source revision journal contains an unsupported revision",
                    )
                if not candidate.is_file() or candidate.is_symlink():
                    raise WorkflowSourceStorageError(
                        "workflow_source_integrity",
                        "Workflow source revision journal contains an invalid entry",
                    )
                if revision in paths:
                    raise WorkflowSourceStorageError(
                        "workflow_source_integrity",
                        "Workflow source revision journal contains duplicate identity",
                    )
                paths[revision] = candidate
        except OSError as error:
            raise WorkflowSourceStorageError(
                "workflow_source_integrity",
                "Workflow source revision journal is unreadable",
            ) from error
        if not paths:
            raise WorkflowSourceStorageError(
                "workflow_source_integrity",
                "Workflow source revision journal is empty",
            )
        for expected_revision, actual_revision in enumerate(sorted(paths), start=1):
            if actual_revision != expected_revision:
                raise WorkflowSourceStorageError(
                    "workflow_source_integrity",
                    "Workflow source revision journal is incomplete",
                )
        return paths

    @staticmethod
    def _validate_record(
        record: dict[str, object],
        *,
        revision: int,
        previous_record: dict[str, object] | None,
        previous_record_digest: str | None,
    ) -> None:
        storage_revision = _positive_int(record.get("storage_revision"))
        definition_revision = _positive_int(record.get("definition_revision"))
        size_bytes = record.get("size_bytes")
        updated_at = record.get("updated_at")
        semantic_change_validated = record.get("semantic_change_validated")
        if (
            set(record) != _RECORD_KEYS
            or record.get("schema_version") != _JOURNAL_SCHEMA_VERSION
            or storage_revision != revision
            or definition_revision is None
            or isinstance(size_bytes, bool)
            or not isinstance(size_bytes, int)
            or not 0 <= size_bytes <= WORKFLOW_SOURCE_MAX_BYTES
            or isinstance(updated_at, bool)
            or not isinstance(updated_at, int)
            or updated_at < 0
            or not isinstance(semantic_change_validated, bool)
            or not isinstance(record.get("storage_digest"), str)
            or _DIGEST.fullmatch(str(record.get("storage_digest"))) is None
        ):
            raise WorkflowSourceStorageError(
                "workflow_source_integrity",
                "Workflow source revision journal contains invalid metadata",
            )

        if revision == 1:
            if (
                definition_revision != 1
                or semantic_change_validated is not True
                or record.get("previous_storage_digest") is not None
                or record.get("previous_record_digest") is not None
            ):
                raise WorkflowSourceStorageError(
                    "workflow_source_integrity",
                    "Workflow source initial revision metadata is invalid",
                )
            return

        if previous_record is None or previous_record_digest is None:
            raise WorkflowSourceStorageError(
                "workflow_source_integrity",
                "Workflow source revision journal has no predecessor",
            )
        previous_definition_revision = _positive_int(
            previous_record.get("definition_revision")
        )
        expected_definition_revision = (
            previous_definition_revision + int(semantic_change_validated)
            if previous_definition_revision is not None
            else None
        )
        if (
            record.get("previous_storage_digest")
            != previous_record.get("storage_digest")
            or record.get("previous_record_digest") != previous_record_digest
            or definition_revision != expected_definition_revision
            or record.get("storage_digest") == previous_record.get("storage_digest")
        ):
            raise WorkflowSourceStorageError(
                "workflow_source_integrity",
                "Workflow source revision journal chain is invalid",
            )

    def _read_state_unlocked(
        self, normalized: str, slug: str, path: Path
    ) -> _CommittedState:
        if not path.exists():
            if self._history_exists(slug):
                raise WorkflowSourceStorageError(
                    "workflow_source_integrity",
                    "Committed workflow source bytes are missing",
                )
            raise FileNotFoundError(normalized)
        try:
            confined = self._paths.resolve(normalized, must_exist=True)
        except FileNotFoundError as error:
            raise FileNotFoundError(normalized) from error
        except ValueError as error:
            raise WorkflowSourceStorageError(
                "workflow_source_path_invalid", str(error)
            ) from error
        if not confined.is_file() or confined.is_symlink():
            raise WorkflowSourceStorageError(
                "workflow_source_path_invalid",
                "Workflow source must be a regular workspace file",
            )

        head, _head_bytes = self._decode_json(
            self._head_path(slug), label="committed head"
        )
        head_revision = _positive_int(head.get("storage_revision"))
        head_definition_revision = _positive_int(head.get("definition_revision"))
        if (
            set(head) != _HEAD_KEYS
            or head.get("schema_version") != _HEAD_SCHEMA_VERSION
            or head_revision is None
            or head_revision > WORKFLOW_SOURCE_MAX_REVISIONS
            or head_definition_revision is None
            or not isinstance(head.get("storage_digest"), str)
            or _DIGEST.fullmatch(str(head.get("storage_digest"))) is None
            or not isinstance(head.get("record_digest"), str)
            or _DIGEST.fullmatch(str(head.get("record_digest"))) is None
        ):
            raise WorkflowSourceStorageError(
                "workflow_source_integrity",
                "Workflow source committed head has invalid metadata",
            )

        journal_paths = self._journal_paths(slug)
        if head_revision != max(journal_paths):
            raise WorkflowSourceStorageError(
                "workflow_source_integrity",
                "Workflow source committed head does not match the latest journal entry",
            )

        previous_record: dict[str, object] | None = None
        previous_record_digest: str | None = None
        latest_record: dict[str, object] | None = None
        latest_record_digest: str | None = None
        for revision in range(1, head_revision + 1):
            record, record_bytes = self._decode_json(
                journal_paths[revision], label="revision journal entry"
            )
            self._validate_record(
                record,
                revision=revision,
                previous_record=previous_record,
                previous_record_digest=previous_record_digest,
            )
            latest_record = record
            latest_record_digest = _digest(record_bytes)
            previous_record = record
            previous_record_digest = latest_record_digest

        if latest_record is None or latest_record_digest is None:
            raise WorkflowSourceStorageError(
                "workflow_source_integrity",
                "Workflow source revision journal is empty",
            )
        if (
            head.get("record_digest") != latest_record_digest
            or head.get("storage_digest") != latest_record.get("storage_digest")
            or head_definition_revision != latest_record.get("definition_revision")
        ):
            raise WorkflowSourceStorageError(
                "workflow_source_integrity",
                "Workflow source committed head does not authenticate its journal entry",
            )

        content = self._read_bounded_file(
            confined,
            max_bytes=WORKFLOW_SOURCE_MAX_BYTES,
            label="definition bytes",
            invalid_code="workflow_source_path_invalid",
            too_large_code="workflow_source_too_large",
            too_large_message=(
                f"Workflow source exceeds the {WORKFLOW_SOURCE_MAX_BYTES}-byte limit"
            ),
        )
        try:
            source = content.decode("utf-8")
        except UnicodeDecodeError as error:
            raise WorkflowSourceStorageError(
                "workflow_source_encoding",
                "Workflow source must be valid UTF-8 text",
            ) from error
        storage_digest = _digest(content)
        if (
            storage_digest != head.get("storage_digest")
            or len(content) != latest_record.get("size_bytes")
        ):
            raise WorkflowSourceStorageError(
                "workflow_source_integrity",
                "Workflow source bytes do not match the committed head",
            )

        document = WorkflowSourceDocument(
            normalized,
            head_revision,
            storage_digest,
            head_definition_revision,
            source,
            len(content),
        )
        return _CommittedState(document, latest_record_digest)

    def _history_exists(self, slug: str) -> bool:
        directory = self._metadata_directory(slug)
        if (directory / "head.json").exists():
            return True
        revisions = directory / "revisions"
        if not revisions.exists():
            return False
        if not revisions.is_dir() or revisions.is_symlink():
            return True
        try:
            return any(revisions.iterdir())
        except OSError:
            return True

    def read(self, user_path: str) -> WorkflowSourceDocument:
        try:
            normalized, slug, path = self._source_path(user_path)
            if not path.exists() and not self._metadata_directory(slug).exists():
                raise FileNotFoundError(normalized)
            with self._transaction(slug, path):
                return self._read_state_unlocked(normalized, slug, path).document
        except (FileNotFoundError, WorkflowSourceStorageError):
            raise
        except OSError as error:
            raise WorkflowSourceStorageError(
                "workflow_source_unavailable",
                "Workflow source storage is unavailable",
            ) from error

    def _commit(
        self,
        *,
        normalized: str,
        slug: str,
        path: Path,
        previous: _CommittedState | None,
        storage_revision: int,
        definition_revision: int,
        semantic_change_validated: bool,
        source: str,
    ) -> WorkflowSourceDocument:
        if not 1 <= storage_revision <= WORKFLOW_SOURCE_MAX_REVISIONS:
            raise WorkflowSourceStorageError(
                "workflow_source_integrity",
                "Workflow source revision limit has been reached",
            )
        content = _source_bytes(source)
        storage_digest = _digest(content)
        document = WorkflowSourceDocument(
            normalized,
            storage_revision,
            storage_digest,
            definition_revision,
            source,
            len(content),
        )
        revision_record = json.dumps(
            {
                "schema_version": _JOURNAL_SCHEMA_VERSION,
                "storage_revision": storage_revision,
                "storage_digest": storage_digest,
                "definition_revision": definition_revision,
                "semantic_change_validated": semantic_change_validated,
                "previous_storage_digest": (
                    previous.document.storage_digest if previous is not None else None
                ),
                "previous_record_digest": (
                    previous.record_digest if previous is not None else None
                ),
                "size_bytes": len(content),
                "updated_at": int(time.time()),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        record_digest = _digest(revision_record)
        head_record = json.dumps(
            {
                "schema_version": _HEAD_SCHEMA_VERSION,
                "storage_revision": storage_revision,
                "storage_digest": storage_digest,
                "definition_revision": definition_revision,
                "record_digest": record_digest,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        revision_path = (
            self._revision_directory(slug) / f"{storage_revision:020d}.json"
        )
        head_path = self._head_path(slug)
        previous_content = (
            previous.document.source.encode("utf-8") if previous is not None else None
        )

        # The visible replace, immutable journal publication, and committed-head
        # switch occur under one cross-process lock. Any synchronous failure is
        # rolled back to the prior visible bytes and head before the lock opens.
        self._atomic_write(path, content)
        journal_created = False
        try:
            self._write_once(revision_path, revision_record)
            journal_created = True
            self._atomic_write(head_path, head_record)
        except BaseException as error:
            rollback_error: BaseException | None = None
            try:
                if previous_content is None:
                    self._unlink(path, missing_ok=True)
                else:
                    self._atomic_write(path, previous_content)
            except BaseException as caught:
                rollback_error = caught
            if journal_created:
                try:
                    self._unlink(revision_path)
                except BaseException as caught:
                    rollback_error = rollback_error or caught
            if rollback_error is not None:
                raise WorkflowSourceStorageError(
                    "workflow_source_integrity",
                    "Workflow source commit failed and could not restore prior state",
                ) from rollback_error
            raise error
        return document

    def create(self, user_path: str, source: str) -> WorkflowSourceDocument:
        try:
            normalized, slug, path = self._source_path(user_path)
            _source_bytes(source)
            with self._transaction(slug, path):
                if path.exists():
                    raise WorkflowSourceStorageError(
                        "workflow_source_exists", "Workflow source already exists"
                    )
                if self._history_exists(slug):
                    raise WorkflowSourceStorageError(
                        "workflow_source_integrity",
                        "Workflow source history exists without committed definition bytes",
                    )
                return self._commit(
                    normalized=normalized,
                    slug=slug,
                    path=path,
                    previous=None,
                    storage_revision=1,
                    definition_revision=1,
                    semantic_change_validated=True,
                    source=source,
                )
        except WorkflowSourceStorageError:
            raise
        except OSError as error:
            raise WorkflowSourceStorageError(
                "workflow_source_unavailable",
                "Workflow source storage is unavailable",
            ) from error

    def update(
        self,
        user_path: str,
        *,
        expected_storage_revision: int,
        expected_storage_digest: str,
        semantic_change_validated: bool,
        source: str,
    ) -> WorkflowSourceDocument:
        try:
            if not isinstance(semantic_change_validated, bool):
                raise WorkflowSourceStorageError(
                    "workflow_source_semantic_change_invalid",
                    "Semantic-change validation must be explicitly true or false",
                )
            normalized, slug, path = self._source_path(user_path)
            content = _source_bytes(source)
            with self._transaction(slug, path):
                current = self._read_state_unlocked(normalized, slug, path)
                if (
                    current.document.storage_revision != expected_storage_revision
                    or current.document.storage_digest != expected_storage_digest
                ):
                    raise WorkflowSourceConflictError(
                        current.document.storage_revision,
                        current.document.storage_digest,
                    )
                if _digest(content) == current.document.storage_digest:
                    return current.document
                return self._commit(
                    normalized=normalized,
                    slug=slug,
                    path=path,
                    previous=current,
                    storage_revision=current.document.storage_revision + 1,
                    definition_revision=(
                        current.document.definition_revision
                        + int(semantic_change_validated)
                    ),
                    semantic_change_validated=semantic_change_validated,
                    source=source,
                )
        except (FileNotFoundError, WorkflowSourceStorageError):
            raise
        except OSError as error:
            raise WorkflowSourceStorageError(
                "workflow_source_unavailable",
                "Workflow source storage is unavailable",
            ) from error


class WorkspaceWorkflowSourceUseCases:
    """Async application boundary for the synchronous workspace source store."""

    def __init__(
        self,
        executor: BoundedExecutor,
        store_factory: Callable[[str], WorkspaceWorkflowSourceStore] = (
            WorkspaceWorkflowSourceStore
        ),
    ) -> None:
        self._executor = executor
        self._store_factory = store_factory

    async def create(
        self,
        workspace_dir: str,
        path: str,
        source: str,
    ) -> WorkflowSourceDocument:
        try:
            return await self._executor.run_to_completion(
                "workspace.workflow_sources.create",
                lambda: self._store_factory(workspace_dir).create(path, source),
            )
        except WorkflowSourceStorageError:
            raise
        except RuntimeError as error:
            raise WorkflowSourceStorageError(
                "workflow_source_unavailable",
                "Workflow source storage is unavailable",
            ) from error

    async def read(self, workspace_dir: str, path: str) -> WorkflowSourceDocument:
        try:
            return await self._executor.run(
                "workspace.workflow_sources.read",
                lambda: self._store_factory(workspace_dir).read(path),
                timeout_seconds=30.0,
            )
        except WorkspaceTimeoutError as error:
            raise WorkflowSourceStorageError(
                "workflow_source_unavailable",
                "Workflow source read did not finish before its deadline",
            ) from error

    async def update(
        self,
        workspace_dir: str,
        path: str,
        *,
        expected_storage_revision: int,
        expected_storage_digest: str,
        semantic_change_validated: bool,
        source: str,
    ) -> WorkflowSourceDocument:
        try:
            return await self._executor.run_to_completion(
                "workspace.workflow_sources.update",
                lambda: self._store_factory(workspace_dir).update(
                    path,
                    expected_storage_revision=expected_storage_revision,
                    expected_storage_digest=expected_storage_digest,
                    semantic_change_validated=semantic_change_validated,
                    source=source,
                ),
            )
        except WorkflowSourceStorageError:
            raise
        except RuntimeError as error:
            raise WorkflowSourceStorageError(
                "workflow_source_unavailable",
                "Workflow source storage is unavailable",
            ) from error
