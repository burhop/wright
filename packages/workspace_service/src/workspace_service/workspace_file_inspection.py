"""Bounded file observations using private, exact-call integration permits."""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time

from tool_registry.gateway_models import GatewayError, GatewayErrorCode, GatewayTool

from .workspace_path import WorkspacePath

INSPECT_TOOL_NAME = "wright-workspace-files__inspect_file"
MAX_FILE_BYTES = 256 * 1024 * 1024
MAX_TEXT_BYTES = 32768
TEXT_EXTENSIONS = frozenset(
    {
        ".json",
        ".csv",
        ".txt",
        ".md",
        ".markdown",
        ".yaml",
        ".yml",
        ".py",
        ".inp",
        ".log",
    }
)
METADATA_EXTENSIONS = TEXT_EXTENSIONS | frozenset(
    {
        ".step",
        ".stp",
        ".stl",
        ".3mf",
        ".obj",
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
        ".vtu",
        ".vtk",
        ".frd",
        ".dat",
        ".zip",
        ".dxf",
        ".psm",
        ".kicad_pcb",
        ".kicad_pro",
        ".kicad_sch",
    }
)


def argument_digest(arguments):
    return hashlib.sha256(
        json.dumps(
            arguments,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def inspection_tool():
    return GatewayTool(
        name=INSPECT_TOOL_NAME,
        server_id="wright-workspace-files",
        tool_name="inspect_file",
        title="Inspect granted workspace file",
        description="Read actual SHA256 and byte size of an exact enrolled input or current integration attempt output. Optional bounded UTF-8 text excerpt for text files; offsetBytes/nextOffsetBytes support paging. CAD/binary files expose metadata only. Requires private current integration authority; never executes files.",
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["relativePath"],
            "properties": {
                "relativePath": {"type": "string", "minLength": 1, "maxLength": 512},
                "includeText": {"type": "boolean", "default": True},
                "offsetBytes": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": MAX_FILE_BYTES,
                    "default": 0,
                },
                "maxTextBytes": {
                    "type": "integer",
                    "minimum": 4,
                    "maximum": MAX_TEXT_BYTES,
                    "default": 16384,
                },
            },
        },
        output_schema={"type": "object"},
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
            "destructiveHint": False,
            "openWorldHint": False,
        },
        provenance={
            "server_revision": "wright-workspace-inspect-v1",
            "validation_evidence_id": "wright-reviewed:confined-integration-file-inspection-v1",
        },
    )


class WorkspaceFileInspector:
    def __init__(self):
        self._permits = {}
        self._lock = threading.Lock()

    def grant(
        self,
        *,
        request_id,
        session_id,
        workspace_id,
        workspace_path,
        arguments,
        expected_sha256,
        policy_digest,
    ):
        """Private service authority; model/public approval_context cannot mint this."""
        with self._lock:
            now = time.monotonic()
            self._permits = {
                key: value
                for key, value in self._permits.items()
                if value["expires"] > now
            }
            if request_id in self._permits or len(self._permits) >= 1024:
                raise GatewayError(
                    GatewayErrorCode.POLICY_DENIED,
                    "File observation permit unavailable",
                )
            self._permits[request_id] = dict(
                session_id=session_id,
                workspace_id=workspace_id,
                workspace_path=str(WorkspacePath(workspace_path).root),
                arguments_digest=argument_digest(arguments),
                expected_sha256=expected_sha256,
                policy_digest=policy_digest,
                expires=now + 30,
            )

    def inspect(self, session, arguments, request_id):
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
                "Exact integration file observation authority is required",
            )
        try:
            paths = WorkspacePath(session.workspace_path)
            relative = arguments["relativePath"]
            target = paths.resolve(relative, must_exist=True)
            if target.suffix.lower() not in METADATA_EXTENSIONS or not target.is_file():
                raise ValueError(
                    "File extension is outside the reviewed observation formats"
                )
            offset, limit = (
                arguments.get("offsetBytes", 0),
                arguments.get("maxTextBytes", 16384),
            )
            include = arguments.get("includeText", True)
            if (
                type(offset) is not int
                or type(limit) is not int
                or type(include) is not bool
                or not 0 <= offset <= MAX_FILE_BYTES
                or not 4 <= limit <= MAX_TEXT_BYTES
            ):
                raise ValueError("Invalid bounded text observation parameters")
            digest = hashlib.sha256()
            excerpt = bytearray()
            text_allowed = target.suffix.lower() in TEXT_EXTENSIONS and include
            with target.open("rb") as stream:
                before = os.fstat(stream.fileno())
                if before.st_size > MAX_FILE_BYTES or offset > before.st_size:
                    raise ValueError(
                        "File exceeds observation size bound or offset exceeds file"
                    )
                count = 0
                while chunk := stream.read(1024 * 1024):
                    digest.update(chunk)
                    if text_allowed:
                        start, end = (
                            max(0, offset - count),
                            min(len(chunk), offset + limit - count),
                        )
                        if start < end:
                            excerpt.extend(chunk[start:end])
                    count += len(chunk)
                    if count > MAX_FILE_BYTES:
                        raise ValueError("File exceeds observation size bound")
                after = os.fstat(stream.fileno())
            # Reject concurrent writes/replacements and any newly inserted link.
            current = paths.resolve(relative, must_exist=True).stat()

            def signature(value):
                # Windows stat/fstat expose different ctime compatibility values.
                return value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns

            if signature(before) != signature(after) or signature(after) != signature(
                current
            ):
                raise ValueError("File changed while being observed")
            sha256 = digest.hexdigest()
            if permit["expected_sha256"] and permit["expected_sha256"] != sha256:
                raise ValueError("Enrolled input digest changed")
            result = {
                "relativePath": relative,
                "sha256": sha256,
                "bytes": count,
                "integration_policy_digest": permit["policy_digest"],
                "textIncluded": text_allowed,
            }
            if text_allowed:
                # Avoid splitting a multibyte character at the end of a page.
                import codecs

                decoder = codecs.getincrementaldecoder("utf-8")("strict")
                text = decoder.decode(
                    bytes(excerpt), final=offset + len(excerpt) >= count
                )
                consumed = len(excerpt) - len(decoder.getstate()[0])
                result.update(
                    text=text,
                    offsetBytes=offset,
                    nextOffsetBytes=offset + consumed,
                    truncated=offset + consumed < count,
                )
            return result
        except (OSError, ValueError, KeyError) as error:
            raise GatewayError(
                GatewayErrorCode.INVALID_INPUT,
                "File observation unavailable: " + str(error),
            ) from error
