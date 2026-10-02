"""Typed workflow references; paths never masquerade as document contents."""

from dataclasses import dataclass
from pathlib import PurePosixPath
import base64
import hashlib


def allows_binary_file_reference(steps, addresses: set[str]) -> bool:
    """Opaque bytes need a declared file consumer and no document/argument consumer."""
    file_consumer = False
    for step in steps:
        if step.application_from in addresses:
            file_consumer = True
        for _, source in step.references:
            if source in addresses and source in step.file_dependencies:
                file_consumer = True
        if (
            step.prompt_from in addresses
            or step.arguments_from in addresses
            or addresses.intersection(step.argument_sources.values())
            or any(
                source in addresses
                and (
                    source not in step.file_dependencies
                    or sum(src == source for _, src in step.references) != 1
                )
                for _, source in step.references
            )
        ):
            return False
    return file_consumer


def snapshot_task_files(workspace_dir: str, paths: tuple[str, ...]) -> dict:
    from .workspace_path import WorkspacePath

    result = {}
    for path in paths:
        target = WorkspacePath(workspace_dir).resolve(path)
        if target.is_file():
            result[path] = (target.stat().st_mtime_ns, target.stat().st_size)
    return result


def verify_task_files(
    workspace_dir: str, paths: tuple[str, ...], before: dict | None = None
) -> list[dict]:
    from .workspace_path import WorkspacePath
    from .workflow_source_execution import _invalid

    files = []
    for path in paths:
        try:
            target = WorkspacePath(workspace_dir).resolve(path, must_exist=True)
            size = target.stat().st_size
            if not target.is_file() or not 0 < size <= 100 * 1024 * 1024:
                raise ValueError("Output is empty or exceeds 100 MiB")
            if before and before.get(path) == (target.stat().st_mtime_ns, size):
                raise ValueError("The existing file was not updated by this task")
            with target.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            files.append(
                {
                    "output_path": path,
                    "output_bytes": size,
                    "output_format": target.suffix.lstrip("."),
                    "sha256": digest,
                }
            )
        except (OSError, ValueError) as error:
            raise _invalid(
                f"The task did not produce the expected file: {path}.",
                "Inspect the tool results and correct the task or expected filename.",
            ) from error
    return files


def image_media_type(path: str, data: bytes) -> str:
    suffix = PurePosixPath(path).suffix.lower()
    kinds = {
        ".png": ("image/png", data.startswith(b"\x89PNG\r\n\x1a\n")),
        ".jpg": ("image/jpeg", data.startswith(b"\xff\xd8\xff")),
        ".jpeg": ("image/jpeg", data.startswith(b"\xff\xd8\xff")),
        ".gif": ("image/gif", data[:6] in (b"GIF87a", b"GIF89a")),
        ".webp": ("image/webp", data[:4] == b"RIFF" and data[8:12] == b"WEBP"),
    }
    match = kinds.get(suffix)
    if not match or not match[1]:
        raise ValueError(
            "Choose a PNG, JPEG, GIF or WebP image whose contents match its extension."
        )
    return match[0]


@dataclass(frozen=True)
class WorkflowReference:
    path: str
    sha256: str
    text: str = ""
    image_url: str = ""
    file_only: bool = False
    size_bytes: int | None = None

    @classmethod
    def from_bytes(
        cls, path: str, data: bytes, *, image: bool, allow_binary: bool = False
    ):
        identity = hashlib.sha256(data).hexdigest()
        if image:
            mime = image_media_type(path, data)
            return cls(
                path,
                identity,
                image_url=f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}",
                size_bytes=len(data),
            )
        try:
            text = data.decode("utf-8-sig")
        except UnicodeError as error:
            if allow_binary and data:
                return cls(path, identity, file_only=True, size_bytes=len(data))
            raise ValueError(
                "This document format cannot be read by this task yet. Choose a UTF-8 text, Markdown, HTML or JSON file."
            ) from error
        if "\x00" in text or not text.strip():
            if allow_binary and data:
                return cls(path, identity, file_only=True, size_bytes=len(data))
            raise ValueError("Choose a non-empty text document.")
        return cls(path, identity, text=text, size_bytes=len(data))


def verified_file_dependencies(step, responses, workspace_dir):
    """Pin connected tool files without interpreting binary bytes as model text."""
    from .workflow_results import EngineeringResult
    from .workflow_source_execution import _invalid
    from .workspace_path import WorkspacePath

    records = []
    for source_id, expected_path in step.file_dependencies.items():
        value = responses.get(source_id)
        if isinstance(value, EngineeringResult):
            representations = [
                rep for rep in value.representations if rep.kind == "workspace_file"
            ]
            if len(representations) != 1:
                raise _invalid(
                    f"{step.title}: its connected file differs from the declared input."
                )
            rep = representations[0]
            location, expected_hash, expected_size = (
                rep.location,
                rep.sha256,
                rep.size_bytes,
            )
        elif isinstance(value, WorkflowReference):
            # Supplied/defaulted input files are pinned by preparation, without
            # pretending that an engineering tool produced those input bytes.
            location, expected_hash, expected_size = (
                value.path,
                value.sha256,
                value.size_bytes,
            )
        else:
            raise _invalid(
                f"{step.title}: its connected file was not supplied or produced."
            )
        if location != expected_path or expected_size is None:
            raise _invalid(
                f"{step.title}: its connected file differs from the declared input."
            )
        try:
            target = WorkspacePath(workspace_dir).resolve(
                expected_path, must_exist=True
            )
            with target.open("rb") as stream:
                actual_hash = hashlib.file_digest(stream, "sha256").hexdigest()
            actual_size = target.stat().st_size
        except (OSError, ValueError) as error:
            raise _invalid(
                f"{step.title}: its connected file is unavailable."
            ) from error
        if actual_hash != expected_hash or actual_size != expected_size:
            raise _invalid(
                f"{step.title}: its connected file changed after the previous stage."
            )
        records.append(
            {
                "path": expected_path,
                "sha256": actual_hash,
                "kind": "workspace_file",
                "source_port": source_id,
            }
        )
    return records


async def reference_from_result(result, *, service, workspace_dir, task_title):
    """Read an explicitly connected file representation, preserving its identity."""
    from .workflow_source_execution import _invalid

    if result.kind not in {"file", "image", "text", "structured"}:
        raise _invalid(
            f"{task_title}: {result.name} is an application resource, not document contents.",
            "Connect it as the application resource to work on, or connect a named document/image export.",
        )
    files = [rep for rep in result.representations if rep.kind == "workspace_file"]
    if len(files) != 1:
        raise _invalid(
            f"{task_title}: select one saved workspace file for {result.name}.",
            "Choose a named export saved in this workspace. A cloud link or a group of files cannot supply document contents.",
        )
    rep = files[0]
    image = rep.format.lower() in {
        "png",
        "jpg",
        "jpeg",
        "gif",
        "webp",
        "screenshot_jpeg",
    }
    if not image and rep.format.lower() not in {
        "txt",
        "text",
        "md",
        "markdown",
        "html",
        "htm",
        "json",
        "csv",
        "yaml",
        "yml",
        "xml",
    }:
        raise _invalid(
            f"{task_title}: {rep.format or 'this file format'} cannot be read as document contents.",
            "Connect it to an application that imports this format, or request a text/image export from the producer.",
        )
    if not rep.sha256:
        raise _invalid(
            f"{task_title}: the exported file has no verified content identity.",
            "Run the producing task again to obtain a verified export.",
        )
    try:
        data = await service.files.read_reference(workspace_dir, rep.location)
        if hashlib.sha256(data).hexdigest() != rep.sha256 or (
            rep.size_bytes is not None and len(data) != rep.size_bytes
        ):
            raise _invalid(
                f"{task_title}: {rep.location} changed after it was produced.",
                "Review the file and rerun its producing task before using this export.",
            )
        return WorkflowReference.from_bytes(rep.location, data, image=image)
    except (OSError, ValueError) as error:
        raise _invalid(
            f"{task_title}: the exported workspace file could not be read.",
            str(error)
            if isinstance(error, ValueError)
            else "Restore the file or rerun its producing task.",
        ) from error
