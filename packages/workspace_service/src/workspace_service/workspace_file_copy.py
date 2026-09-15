"""Private, single-use, bounded working copies; never an artifact publisher."""

from __future__ import annotations

from contextlib import contextmanager, ExitStack
import hashlib
import os
import stat
import time
import uuid

from tool_registry.gateway_models import GatewayError, GatewayErrorCode, GatewayTool

from .workspace_file_inspection import WorkspaceFileInspector, argument_digest
from .workspace_path import WorkspacePath

COPY_TOOL_NAME = "wright-workspace-files__copy_file"
MAX_COPY_BYTES = 256 * 1024 * 1024


def copy_tool():
    return GatewayTool(
        name=COPY_TOOL_NAME,
        server_id="wright-workspace-files",
        tool_name="copy_file",
        title="Create granted engineering working copy",
        description="Copy one exact enrolled input or current-run verified file to a new fixed canonical working path. Private integration authority only. Binary streaming, no overwrite, no execution. Returns copy-time hash lineage; the mutable working copy is not a published final artifact.",
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["sourcePath", "destinationPath"],
            "properties": {
                key: {"type": "string", "minLength": 1, "maxLength": 512}
                for key in ("sourcePath", "destinationPath")
            },
        },
        output_schema={"type": "object"},
        annotations={
            "readOnlyHint": False,
            "idempotentHint": False,
            "destructiveHint": False,
            "openWorldHint": False,
        },
        provenance={
            "server_revision": "wright-workspace-copy-v1",
            "validation_evidence_id": "wright-reviewed:exact-integration-working-copy-v1",
        },
    )


def _signature(value):
    return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns


def _new_copy_file(temporary, temp_name, kwargs):
    if os.name != "nt":
        return os.open(
            temp_name,
            os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            **kwargs,
        )
    import ctypes
    from ctypes import wintypes
    import msvcrt

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.LPVOID,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    create.restype = wintypes.HANDLE
    # CREATE_NEW, read/write owner, other handles may read only. This protects
    # the temporary inode through both the output hash and atomic publication.
    handle = create(str(temporary), 0xC0000000, 1, None, 1, 0x80, None)
    if handle == wintypes.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return msvcrt.open_osfhandle(handle, os.O_RDWR | os.O_BINARY)
    except Exception:
        close = kernel.CloseHandle
        close.argtypes = [wintypes.HANDLE]
        close(handle)
        raise


@contextmanager
def _pin_windows_paths(paths):
    """Deny rename/delete of every ancestor and source during publication."""
    with ExitStack() as stack:
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes

            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            create = kernel.CreateFileW
            create.argtypes = [
                wintypes.LPCWSTR,
                wintypes.DWORD,
                wintypes.DWORD,
                wintypes.LPVOID,
                wintypes.DWORD,
                wintypes.DWORD,
                wintypes.HANDLE,
            ]
            create.restype = wintypes.HANDLE
            close = kernel.CloseHandle
            close.argtypes = [wintypes.HANDLE]
            close.restype = wintypes.BOOL
            for path in sorted(set(paths), key=lambda p: len(p.parts)):
                # OPEN_REPARSE_POINT + BACKUP_SEMANTICS; no FILE_SHARE_DELETE.
                directory = path.is_dir()
                handle = create(
                    str(path),
                    0 if directory else 0x80000000,
                    3 if directory else 1,
                    None,
                    3,
                    0x02200000,
                    None,
                )
                if handle == wintypes.HANDLE(-1).value:
                    raise ctypes.WinError(ctypes.get_last_error())
                stack.callback(close, handle)
                value = path.lstat()
                if getattr(value, "st_file_attributes", 0) & 0x400:
                    raise ValueError("Reparse points are forbidden")
        yield


class WorkspaceFileCopier(WorkspaceFileInspector):
    def grant(self, *, expected_bytes, source_provenance, **kwargs):
        super().grant(**kwargs)
        with self._lock:
            self._permits[kwargs["request_id"]].update(
                expected_bytes=expected_bytes, source_provenance=dict(source_provenance)
            )

    def copy(self, session, arguments, request_id):
        with self._lock:
            permit = self._permits.pop(request_id, None)
        if (
            not permit
            or permit["expires"] <= time.monotonic()
            or permit["session_id"] != session.session_id
            or session.principal_id != "wright-native-workflow"
            or permit["workspace_id"] != session.workspace_id
            or permit["workspace_path"]
            != str(WorkspacePath(session.workspace_path).root)
            or permit["arguments_digest"] != argument_digest(arguments)
        ):
            raise GatewayError(
                GatewayErrorCode.POLICY_DENIED,
                "Exact integration working-copy authority is required",
            )
        try:
            return self._copy(session, arguments, permit, request_id)
        except (OSError, ValueError, KeyError) as error:
            raise GatewayError(
                GatewayErrorCode.INVALID_INPUT,
                "Working copy unavailable: " + str(error),
            ) from error

    def _copy(self, session, arguments, permit, request_id):
        paths = WorkspacePath(session.workspace_path)
        source_name, destination_name = (
            arguments["sourcePath"],
            arguments["destinationPath"],
        )
        source = paths.resolve(source_name, must_exist=True)
        target = paths.resolve(destination_name)
        if not stat.S_ISREG(source.lstat().st_mode):
            raise ValueError("Source must be a regular file")
        if source == target or target.exists() or not target.parent.is_dir():
            raise ValueError("Working copy needs a new path in an existing directory")
        ancestors = {paths.root, source}
        for item in (source.parent, target.parent):
            ancestors.add(item)
            ancestors.update(
                p
                for p in item.parents
                if p == paths.root or p.is_relative_to(paths.root)
            )
        with _pin_windows_paths(ancestors), ExitStack() as stack:
            # Revalidate after pinning: a raced junction/link cannot gain authority.
            paths.resolve(source_name, must_exist=True)
            paths.resolve(destination_name)
            parent_signatures = {
                p: (p.stat().st_dev, p.stat().st_ino) for p in ancestors if p != source
            }
            destination_fd = None
            if os.name != "nt":
                destination_fd = os.open(
                    target.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
                )
                stack.callback(os.close, destination_fd)
            temp_name = f".{target.name}.wright-copy-{uuid.uuid4().hex}.tmp"
            temporary = target.parent / temp_name
            kwargs = {"dir_fd": destination_fd} if destination_fd is not None else {}
            descriptor = _new_copy_file(temporary, temp_name, kwargs)
            published = False
            temp_identity = None
            try:
                with os.fdopen(descriptor, "w+b") as output:
                    source_fd = os.open(
                        source,
                        os.O_RDONLY
                        | getattr(os, "O_BINARY", 0)
                        | getattr(os, "O_NOFOLLOW", 0)
                        | getattr(os, "O_NONBLOCK", 0),
                    )
                    with os.fdopen(source_fd, "rb") as input_stream:
                        before = os.fstat(input_stream.fileno())
                        if (
                            not stat.S_ISREG(before.st_mode)
                            or before.st_size > MAX_COPY_BYTES
                        ):
                            raise ValueError("Source is not a bounded regular file")
                        digest, count = hashlib.sha256(), 0
                        while chunk := input_stream.read(1024 * 1024):
                            count += len(chunk)
                            if count > MAX_COPY_BYTES:
                                raise ValueError(
                                    "Source exceeds working-copy size bound"
                                )
                            digest.update(chunk)
                            output.write(chunk)
                        after = os.fstat(input_stream.fileno())
                    if _signature(before) != _signature(after) or _signature(
                        after
                    ) != _signature(paths.resolve(source_name, must_exist=True).stat()):
                        raise ValueError("Source changed during copy")
                    if (
                        digest.hexdigest() != permit["expected_sha256"]
                        or permit["expected_bytes"] is not None
                        and count != permit["expected_bytes"]
                    ):
                        raise ValueError("Source differs from authorized file evidence")
                    output.flush()
                    os.fsync(output.fileno())
                    temp_identity = os.fstat(output.fileno())
                    paths.resolve(destination_name)
                    if _signature(
                        paths.resolve(source_name, must_exist=True).stat()
                    ) != _signature(after):
                        raise ValueError("Source changed before publication")
                    for parent, identity in parent_signatures.items():
                        current = parent.stat()
                        if (current.st_dev, current.st_ino) != identity:
                            raise ValueError("Workspace parent changed during copy")
                    # Hash the actual copied inode, not just the input stream.
                    output.seek(0)
                    copied_hash, copied_count = hashlib.sha256(), 0
                    while chunk := output.read(1024 * 1024):
                        copied_count += len(chunk)
                        if copied_count > MAX_COPY_BYTES:
                            raise ValueError("Copied file exceeds size bound")
                        copied_hash.update(chunk)
                    if (
                        copied_count != count
                        or copied_hash.hexdigest() != digest.hexdigest()
                        or _signature(os.fstat(output.fileno()))
                        != _signature(temp_identity)
                        or _signature(
                            os.stat(
                                temp_name if kwargs else temporary,
                                follow_symlinks=False,
                                **kwargs,
                            )
                        )
                        != _signature(temp_identity)
                    ):
                        raise ValueError(
                            "Copied bytes differ from the authorized source"
                        )
                    if destination_fd is not None:
                        os.link(
                            temp_name,
                            target.name,
                            src_dir_fd=destination_fd,
                            dst_dir_fd=destination_fd,
                            follow_symlinks=False,
                        )
                    else:
                        os.link(temporary, target)
                    published = True
                    if _signature(
                        paths.resolve(destination_name, must_exist=True).stat()
                    ) != _signature(temp_identity):
                        raise ValueError("Published working copy changed")
                    if _signature(
                        paths.resolve(source_name, must_exist=True).stat()
                    ) != _signature(after):
                        raise ValueError("Source changed at publication")
                    return {
                        "operation": "copy_file",
                        "mutable_working_copy": True,
                        "published_artifact": False,
                        "request_id": request_id,
                        "integration_policy_digest": permit["policy_digest"],
                        "source": {
                            "relativePath": source_name,
                            "sha256": digest.hexdigest(),
                            "bytes": count,
                            "provenance": permit["source_provenance"],
                        },
                        "destination": {
                            "relativePath": destination_name,
                            "sha256": digest.hexdigest(),
                            "bytes": count,
                        },
                    }
            except Exception:
                if published:
                    # Compensate only our exact inode; never delete another writer's file.
                    current = os.stat(
                        target.name if kwargs else target,
                        follow_symlinks=False,
                        **kwargs,
                    )
                    if (current.st_dev, current.st_ino) == (
                        temp_identity.st_dev,
                        temp_identity.st_ino,
                    ):
                        os.unlink(target.name if kwargs else target, **kwargs)
                raise
            finally:
                os.unlink(temp_name if kwargs else temporary, **kwargs)
