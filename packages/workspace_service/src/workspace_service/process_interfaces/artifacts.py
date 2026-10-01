"""Scoped file access composed from accepted inputs and canonical result owners."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import hashlib
from pathlib import PurePosixPath
import re
from uuid import uuid4

from core.process_interactions import ArtifactRef, FileBinding
from core.tracing import traced

from ..workflow_references import image_media_type
from ..workflow_execution_continuation import restore_result
from ..workflow_run_record import read_workflow_run, WorkflowRunReadError
from .errors import ProcessInterfaceError
from .inputs import _descriptors, _sections, input_file_reference


def _denied():
    return ProcessInterfaceError(
        "SCOPE_DENIED",
        "This file does not belong to the selected process inputs or result.",
        "Open the file from the exact prepared inputs or recorded result.",
    )


def _media_type(path, content):
    suffix = PurePosixPath(path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        return image_media_type(path, content)
    return {
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".json": "application/json",
        ".csv": "text/csv",
        ".stl": "model/stl",
        ".3mf": "model/3mf",
        ".obj": "model/obj",
        ".step": "model/step",
        ".stp": "model/step",
    }.get(suffix, "application/octet-stream")


@dataclass(frozen=True, slots=True)
class ProcessArtifactBytes:
    reference: ArtifactRef
    content: bytes
    media_type: str


class ProcessArtifactAccess:
    def __init__(self, application):
        self.application = application

    @traced("process.interface.input.upload")
    async def upload(self, scope, process, input_id, name, content):
        app = self.application
        resolved = await app.resolve_process(scope, process, operation="process.inputs")
        plan, blocks = _sections(resolved.document.source)
        definitions, _, _ = _descriptors(plan, blocks)
        declaration = next(
            (
                (definition, fields)
                for definition, fields in definitions
                if definition.input_id == input_id
            ),
            None,
        )
        if declaration is None or declaration[0].binding_kind != "file":
            raise _denied()
        if (
            not isinstance(name, str)
            or not name
            or len(name) > 160
            or re.search(r"[/\\:%\x00-\x1f]", name)
            or name.startswith(".")
            or not isinstance(content, bytes)
            or not 0 < len(content) <= app.limits.maximum_upload_bytes
        ):
            raise ProcessInterfaceError(
                "RESPONSE_INVALID",
                "This input file is empty, too large or has an unsupported filename.",
                "Choose a file within the configured upload limit with a simple filename.",
            )
        suffix = PurePosixPath(name).suffix.lower()
        if suffix and not re.fullmatch(r"\.[a-z0-9]{1,12}", suffix):
            raise ProcessInterfaceError(
                "RESPONSE_INVALID",
                "This file extension is unsupported.",
                "Choose a file format supported by the declared input.",
            )
        path = f".wright/process-inputs/{process.source_digest}/{uuid4().hex}{suffix}"
        _, fields = declaration
        try:
            # Validate with the same reference reader used by input preparation.
            # Upload does not create a preparation, edit accepted source or run work.
            input_file_reference(plan, fields, input_id, path, content)
            media_type = _media_type(path, content)
        except (ValueError, UnicodeError) as error:
            raise ProcessInterfaceError(
                "READINESS_UNSUPPORTED",
                "This file cannot supply the declared process input.",
                "Choose a supported image, document or application import for this input.",
            ) from error
        try:
            published = await app.workspace.files.write_generated_bytes(
                resolved.workspace_dir, path, content, "indexed"
            )
            if not isinstance(published, str) or not published.startswith(
                f".wright/process-inputs/{process.source_digest}/"
            ):
                raise ValueError(
                    "The owning writer returned a different publication scope"
                )
            return ArtifactRef(
                artifact_ref=published,
                sha256=hashlib.sha256(content).hexdigest(),
                media_type=media_type,
            )
        except (OSError, ValueError) as error:
            raise ProcessInterfaceError(
                "CAPABILITY_UNAVAILABLE",
                "Wright could not save this input file.",
                "Check the workspace's writable storage and upload the file again.",
            ) from error

    @traced("process.interface.representation.read")
    async def read(
        self, scope, process, reference, *, run_id=None, input_snapshot_id=None
    ):
        app = self.application
        scope.require(process, "process.results")
        if process.source_contract != "canonical-source":
            raise _denied()
        if (run_id is None) == (input_snapshot_id is None):
            raise ProcessInterfaceError(
                "RESPONSE_INVALID",
                "Choose one recorded run or prepared input snapshot for this file.",
                "Open the representation from its exact process view.",
            )
        # The root is derived from the authorized workspace, never a file locator.
        root = app.runs._root(scope, process, "process.results")
        if run_id is not None:
            await self._authorize_result(root, process, run_id, reference)
            maximum = app.limits.maximum_representation_bytes
        else:
            frozen = app._input_snapshot(process, input_snapshot_id)
            if not any(
                isinstance(binding, FileBinding) and binding.reference == reference
                for binding in frozen.bindings
            ):
                raise _denied()
            maximum = app.limits.maximum_upload_bytes
        try:
            content = await app.workspace.files.read_bytes(
                root, reference.artifact_ref, maximum_bytes=maximum
            )
            if hashlib.sha256(content).hexdigest() != reference.sha256:
                raise ProcessInterfaceError(
                    "SUBJECT_STALE",
                    "This file has changed since the inputs or result were recorded.",
                    "Review the changed file and prepare new inputs or rerun its producer.",
                )
            media_type = _media_type(reference.artifact_ref, content)
            return ProcessArtifactBytes(reference, content, media_type)
        except ProcessInterfaceError:
            raise
        except (OSError, ValueError) as error:
            raise ProcessInterfaceError(
                "CAPABILITY_UNAVAILABLE",
                "Wright could not read this recorded representation within its supported bound.",
                "Check the exact file or use the canonical result's supported download/reader.",
            ) from error

    async def _authorize_result(self, root, process, run_id, reference):
        if reference.result_id is None or reference.representation_id is not None:
            raise _denied()
        receipt = await asyncio.to_thread(
            self.application.inputs.receipt_for_run,
            process.workspace_id,
            process.source_path,
            run_id,
        )
        try:
            view = await asyncio.to_thread(
                read_workflow_run,
                root,
                process.source_path,
                run_id,
                **(
                    {"run_log_path": receipt.run_log_path}
                    if receipt and receipt.run_log_path
                    else {}
                ),
            )
            if view["source_digest"] != process.source_digest or (
                receipt and receipt.process != process
            ):
                raise _denied()
            for item in view["results"]:
                result = restore_result(item)
                if (
                    result.id != reference.result_id
                    or result.provenance.run_id != run_id
                ):
                    continue
                if any(
                    rep.kind == "workspace_file"
                    and rep.location == reference.artifact_ref
                    and rep.sha256 == reference.sha256
                    for rep in result.representations
                ):
                    return
            if view.get("execution", {}).get("truncated"):
                raise ProcessInterfaceError(
                    "CAPABILITY_UNAVAILABLE",
                    "This run's bounded result view does not include the requested representation.",
                    "Use the canonical run's supported result reader for this exact artifact.",
                )
        except ProcessInterfaceError:
            raise
        except (WorkflowRunReadError, ValueError, TypeError, KeyError) as error:
            raise ProcessInterfaceError(
                "CAPABILITY_UNAVAILABLE",
                "The exact run's result references could not be verified.",
                "Inspect the canonical process and run record before opening this file.",
            ) from error
        raise _denied()
