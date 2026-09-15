"""Bounded file identity reads for exact checkpoint verification, without text."""

import hashlib
import os
import stat

from .workspace_path import WorkspacePath


MAX_IDENTITY_BYTES = 256 * 1024 * 1024


def workspace_file_sha256(workspace_dir: str, path: str) -> str:
    """Hash a confined regular file and reject replacement or concurrent writes.

    This uses the same path capability and stat/fstat identity checks as the
    workspace file inspector. It returns no file content or model context.
    """
    paths = WorkspacePath(workspace_dir)
    target = paths.resolve(path, must_exist=True)
    if not target.is_file():
        raise ValueError("Checkpoint file must be a regular file.")
    digest = hashlib.sha256()
    with target.open("rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_IDENTITY_BYTES:
            raise ValueError("Checkpoint file is not regular or exceeds 256 MiB.")
        count = 0
        while chunk := stream.read(1024 * 1024):
            count += len(chunk)
            if count > MAX_IDENTITY_BYTES:
                raise ValueError("Checkpoint file exceeds 256 MiB.")
            digest.update(chunk)
        after = os.fstat(stream.fileno())
    current = paths.resolve(path, must_exist=True).stat()

    def signature(value):
        # Windows stat/fstat expose different legacy ctime values.
        return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns

    if (
        count != before.st_size
        or signature(before) != signature(after)
        or signature(after) != signature(current)
    ):
        raise ValueError("Checkpoint file changed while its identity was read.")
    return digest.hexdigest()
