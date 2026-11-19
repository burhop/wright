"""Verified files and their exact producing run, step and port."""

from __future__ import annotations

import base64
import hashlib
import struct
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
from typing import Literal

from .paths import ConfinedDirectory
from .source import _error, _invalid

ResultKind = Literal["text", "image", "file", "structured", "cad_model", "analysis"]
ArtifactRole = Literal[
    "source",
    "intermediate",
    "deliverable",
    "verification",
    "diagnostic",
    "external_action_receipt",
]


@dataclass(frozen=True)
class Representation:
    kind: Literal["value", "workspace_file", "application_document", "cloud_resource"]
    location: str
    format: str = ""
    provider_id: str = ""
    resource_id: str = ""
    revision: str | None = None
    durability: Literal["persistent", "session", "run"] = "run"
    sha256: str | None = None
    size_bytes: int | None = None

    def __post_init__(self):
        if self.kind not in {
            "value",
            "workspace_file",
            "application_document",
            "cloud_resource",
        } or self.durability not in {"persistent", "session", "run"}:
            raise ValueError("Unknown result representation or durability.")
        if not isinstance(self.location, str) or not self.location.strip():
            raise ValueError("A result representation needs a location.")
        if self.revision is not None and not isinstance(self.revision, str):
            raise ValueError("Resource revisions must be strings.")
        if self.kind in {"application_document", "cloud_resource"} and not (
            self.provider_id and self.resource_id
        ):
            raise ValueError(
                "Application resources need explicit provider and resource identity."
            )
        if self.kind == "workspace_file":
            from pathlib import PurePosixPath

            path = PurePosixPath(self.location.replace("\\", "/"))
            if path.is_absolute() or ".." in path.parts or ":" in self.location:
                raise ValueError("Result files must be relative to their workspace.")
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ValueError("A file size cannot be negative.")


@dataclass(frozen=True)
class Provenance:
    run_id: str
    task_id: str
    output_port: str
    input_revisions: tuple[tuple[str, str | None], ...] = ()
    definition_digest: str | None = None
    binding_digest: str | None = None


@dataclass(frozen=True)
class EngineeringResult:
    id: str
    kind: ResultKind
    name: str
    representations: tuple[Representation, ...]
    provenance: Provenance
    # Named export results retain their own IDs, formats and connection targets.
    exports: tuple["EngineeringResult", ...] = ()
    artifact_role: ArtifactRole = "deliverable"

    def __post_init__(self):
        if self.kind not in {
            "text",
            "image",
            "file",
            "structured",
            "cad_model",
            "analysis",
        }:
            raise ValueError("Unknown engineering result kind.")
        if not self.id or not self.name or not self.representations:
            raise ValueError(
                "A result needs an identity and at least one verified representation."
            )
        if self.artifact_role not in {
            "source",
            "intermediate",
            "deliverable",
            "verification",
            "diagnostic",
            "external_action_receipt",
        }:
            raise ValueError("Unknown engineering artifact role.")

    @property
    def persistent(self):
        return any(r.durability == "persistent" for r in self.representations)

    def to_dict(self):
        return {"schema_version": 1, **asdict(self)}


def file_representation(output: dict) -> Representation:
    return Representation(
        "workspace_file",
        output["output_path"],
        output.get("output_format", ""),
        durability="persistent",
        sha256=output.get("sha256"),
        size_bytes=output["output_bytes"],
    )


def file_result(output: dict, provenance: Provenance) -> EngineeringResult:
    return EngineeringResult(
        f"{provenance.run_id}:{provenance.task_id}:{provenance.output_port}",
        "image" if str(output.get("media_type", "")).startswith("image/") else "file",
        output["output_path"],
        (file_representation(output),),
        provenance,
        artifact_role=output.get("artifact_role", "deliverable"),
    )


def _dimensions(raw, mime):
    if mime == "image/png":
        if len(raw) < 33 or raw[:8] != b"\x89PNG\r\n\x1a\n" or raw[12:16] != b"IHDR":
            raise ValueError("invalid_image_header")
        return struct.unpack(">II", raw[16:24])
    if mime != "image/jpeg" or not raw.startswith(b"\xff\xd8\xff"):
        raise ValueError("invalid_image_header")
    offset = 2
    while offset + 3 < len(raw):
        if raw[offset] != 0xFF:
            raise ValueError("invalid_image_header")
        while offset < len(raw) and raw[offset] == 0xFF:
            offset += 1
        if offset >= len(raw):
            break
        marker = raw[offset]
        offset += 1
        if marker in {0xD8, 0x01, *range(0xD0, 0xD8)}:
            continue
        if marker in {0xD9, 0xDA} or offset + 2 > len(raw):
            break
        length = int.from_bytes(raw[offset : offset + 2], "big")
        if length < 2 or offset + length > len(raw):
            break
        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }:
            if length < 8:
                break
            height, width = struct.unpack(">HH", raw[offset + 3 : offset + 7])
            return width, height
        offset += length
    raise ValueError("invalid_image_header")


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
    run_path_id: str = ""
    resolved_sha256: str = ""

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


def snapshot_task_files(workspace_dir: str, paths: tuple[str, ...]) -> dict:

    result = {}
    for path in paths:
        target = ConfinedDirectory(workspace_dir).resolve(path)
        if target.is_file():
            result[path] = (target.stat().st_mtime_ns, target.stat().st_size)
    return result


def verify_task_files(
    workspace_dir: str, paths: tuple[str, ...], before: dict | None = None
) -> list[dict]:

    files = []
    for path in paths:
        try:
            target = ConfinedDirectory(workspace_dir).resolve(path, must_exist=True)
            size = target.stat().st_size
            if not target.is_file() or not 0 < size <= 100 * 1024 * 1024:
                raise ValueError("Output is empty or exceeds 100 MiB")
            if before and before.get(path) == (target.stat().st_mtime_ns, size):
                raise ValueError("The existing file was not updated by this task")
            with target.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            media_type = None
            if target.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
                with target.open("rb") as stream:
                    media_type = image_media_type(path, stream.read(16))
                    if media_type in {"image/png", "image/jpeg"}:
                        stream.seek(0)
                        width, height = _dimensions(stream.read(), media_type)
                        if width <= 0 or height <= 0:
                            raise ValueError("Image dimensions must be positive")
            files.append(
                {
                    "output_path": path,
                    "output_bytes": size,
                    "output_format": target.suffix.lstrip("."),
                    "sha256": digest,
                    **({"media_type": media_type} if media_type else {}),
                }
            )
        except (OSError, ValueError) as error:
            raise _error(
                "WORKFLOW_OUTPUT_INVALID",
                f"The task did not produce the expected file: {path}.",
                "Inspect the tool results and correct the task or expected filename.",
            ) from error
    return files


def verified_file_dependencies(step, responses, workspace_dir):
    """Pin connected tool files without interpreting binary bytes as model text."""

    records = []
    for source_id, expected_path in step.file_dependencies.items():
        value = responses.get(source_id)
        connected_output = expected_path == {"source": "connected_output"}
        if isinstance(value, EngineeringResult):
            if (
                connected_output
                and source_id
                != f"{value.provenance.task_id}.{value.provenance.output_port}"
            ):
                raise _invalid(
                    f"{step.title}: its file receipt belongs to another connected output."
                )
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
        if connected_output:
            expected_path = location
        if location != expected_path or expected_size is None:
            raise _invalid(
                f"{step.title}: its connected file differs from the declared input."
            )
        try:
            target = ConfinedDirectory(workspace_dir).resolve(
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
