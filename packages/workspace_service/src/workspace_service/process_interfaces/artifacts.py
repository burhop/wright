"""Scoped file access composed from accepted inputs and canonical result owners."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import hashlib
import json
from pathlib import PurePosixPath
import re
from uuid import uuid4

from core.process_interactions import ArtifactRef, FileBinding
from core.process_validation import canonical_digest
from core.tracing import traced

from ..errors import WorkspaceTimeoutError
from ..workflow_references import image_media_type
from ..workflow_execution_continuation import restore_result
from ..workflow_run_record import read_workflow_run, WorkflowRunReadError
from ..workflow_external_actions import WorkflowExternalActionError
from .errors import ProcessInterfaceError
from .inputs import _descriptors, _sections, input_file_reference


def _denied():
    return ProcessInterfaceError(
        "SCOPE_DENIED",
        "This file does not belong to the selected process inputs, checkpoint or result.",
        "Open the file from the exact prepared inputs, retained checkpoint or recorded result.",
    )


def _media_type(path, content):
    suffix = PurePosixPath(path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
        return image_media_type(path, content)
    return {
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".pdf": "application/pdf",
        ".json": "application/json",
        ".csv": "text/csv",
        ".stl": "model/stl",
        ".gcode": "text/x-gcode",
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


def assessment_content_matches(content, assessment):
    """Compare complete immutable JSON content, independently of its formatting."""

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate assessment field")
            result[key] = value
        return result

    try:
        if len(content) > 16 * 1024 * 1024:
            return False
        payload = json.loads(content, object_pairs_hook=unique_object)
        # Comparing the complete parsed payload retains every explicit field:
        # model coercion or filling missing defaults must not create a match.
        return canonical_digest(payload) == canonical_digest(assessment)
    except (ValueError, TypeError, UnicodeError, RecursionError):
        return False


class ProcessArtifactAccess:
    def __init__(self, application):
        self.application = application

    @traced("process.interface.representation.preview")
    async def preview(
        self,
        scope,
        process,
        reference,
        *,
        run_id=None,
        input_snapshot_id=None,
        archive_entry=None,
        preview="toolpaths",
        page=None,
    ):
        """Derive a passive view only after exact membership and byte authorization."""
        from .representations import (
            RepresentationUnavailable,
            read_3mf_toolpaths,
            read_gcode_toolpaths,
        )

        artifact = await self.read(
            scope,
            process,
            reference,
            run_id=run_id,
            input_snapshot_id=input_snapshot_id,
        )

        def derive():
            suffix = PurePosixPath(reference.artifact_ref).suffix.lower()
            if preview == "validation-report":
                from .owners import reports_for_run
                from ..process_validation.reporting import render_readable_markdown

                if (
                    run_id is None
                    or reference.result_id is None
                    or archive_entry is not None
                    or page is not None
                    or suffix != ".json"
                    or len(artifact.content) > 16 * 1024 * 1024
                ):
                    raise RepresentationUnavailable(
                        "Choose an assessment recorded by this run."
                    )
                root = self.application.runs._root(scope, process, "process.results")
                # Membership and raw SHA above pin the original file. Its complete
                # immutable content must match the owning assessment; ledger reloads
                # may legitimately change dictionary ordering or JSON whitespace.
                reports = [
                    report
                    for report in reports_for_run(
                        self.application, process, root, run_id
                    )
                    if assessment_content_matches(artifact.content, report.assessment)
                ]
                if len(reports) != 1:
                    raise RepresentationUnavailable(
                        "No exact assessment report belongs to this run."
                    )
                content = render_readable_markdown(reports[0]).encode("utf-8")
                if len(content) > min(
                    self.application.limits.maximum_representation_bytes,
                    2 * 1024 * 1024,
                ):
                    raise RepresentationUnavailable(
                        "The assessment exceeds the report preview bound."
                    )
                return ProcessArtifactBytes(reference, content, "text/markdown")
            media_type = "application/vnd.wright.toolpaths+json"
            if preview == "pdf-page" and suffix == ".pdf" and archive_entry is None:
                from .pdf_preview import read_pdf_page

                document = read_pdf_page(
                    artifact.content,
                    reference.sha256,
                    page=page if page is not None else 1,
                )
                media_type = "application/vnd.wright.pdf-page+json"
            elif preview != "toolpaths" or page is not None:
                raise RepresentationUnavailable(
                    "Unsupported passive preview selection."
                )
            elif suffix == ".3mf":
                document = read_3mf_toolpaths(
                    artifact.content,
                    reference.sha256,
                    entry=archive_entry,
                )
            elif suffix in {".gcode", ".txt"} and archive_entry is None:
                document = read_gcode_toolpaths(artifact.content, reference.sha256)
            else:
                raise RepresentationUnavailable(
                    "The exact artifact has no supported toolpath reader."
                )
            content = json.dumps(
                document, separators=(",", ":"), allow_nan=False
            ).encode("utf-8")
            if len(content) > min(
                self.application.limits.maximum_representation_bytes, 64 * 1024 * 1024
            ):
                raise RepresentationUnavailable(
                    "The derived view exceeds its passive presentation bound."
                )
            return ProcessArtifactBytes(reference, content, media_type)

        try:
            # Both parsing and serialization use the workspace's existing worker
            # owner. A passive timeout never changes or replays process work.
            return await self.application.workspace.executor.run(
                "process.representation.preview",
                derive,
                timeout_seconds=self.application.limits.representation_timeout_seconds,
            )
        except (RepresentationUnavailable, WorkspaceTimeoutError, ValueError) as error:
            raise ProcessInterfaceError(
                "CAPABILITY_UNAVAILABLE",
                "A readable assessment is unavailable for this recorded file."
                if preview == "validation-report"
                else "A PDF page preview is unavailable for this recorded file."
                if preview == "pdf-page"
                else "A complete toolpath preview is unavailable for this recorded file.",
                "Download the exact artifact and inspect it with a compatible engineering tool.",
                details={"reader_diagnostic": str(error)},
            ) from error

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
        self,
        scope,
        process,
        reference,
        *,
        run_id=None,
        input_snapshot_id=None,
        _maximum_bytes=None,
    ):
        app = self.application
        scope.require_run(run_id)
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
        if _maximum_bytes is not None:
            if type(_maximum_bytes) is not int or _maximum_bytes <= 0:
                raise ValueError("Internal representation read bound must be positive")
            maximum = min(maximum, _maximum_bytes)
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
        if reference.representation_id is not None:
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
                complete_results=True,
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
            if reference.result_id is None:
                self._authorize_checkpoint(process, run_id, view, reference)
                return
            for item in view["results"] + [
                row["result"] for row in view.get("previous_results", [])
            ]:
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
        except ProcessInterfaceError:
            raise
        except (WorkflowRunReadError, ValueError, TypeError, KeyError) as error:
            raise ProcessInterfaceError(
                "CAPABILITY_UNAVAILABLE",
                "The exact run's result references could not be verified.",
                "Inspect the canonical process and run record before opening this file.",
            ) from error
        raise _denied()

    def _authorize_checkpoint(self, process, run_id, view, reference):
        """Read existing checkpoint evidence without inspection/decision/dispatch."""
        from .owners import _approval_evidence

        for field, owner in (
            ("approval", self.application.workspace.workflow_external_actions),
            ("input_checkpoint", self.application.human_inputs),
        ):
            retained = view.get(field)
            if not retained or not retained.get("checkpoint_id"):
                continue
            try:
                checkpoint = owner.get(
                    retained["checkpoint_id"],
                    workspace_id=process.workspace_id,
                    run_id=run_id,
                )
            except WorkflowExternalActionError as error:
                raise _denied() from error
            if (
                checkpoint.workflow_id != process.source_path
                or checkpoint.subject.get("definition_digest") != process.source_digest
                or checkpoint.subject_digest != retained.get("subject_digest")
            ):
                raise _denied()
            if reference in _approval_evidence(checkpoint):
                return
        raise _denied()


@dataclass(frozen=True)
class ProcessUIPreviewObservation:
    """Server-derived observation from a validated presentation handshake.

    This is not a public request model. The managed surface owner supplies it
    only after the exact preview bundle loaded in its current presentation.
    """

    presentation_id: str
    ui_id: str
    revision_id: str
    bundle_digest: str


class ProcessInterfaceRevisions:
    """Immutable presentation artifacts and metadata; no run/input mutations."""

    def __init__(self, application):
        self.application = application
        self.repository = application.interfaces

    def _load_built(self, scope, process, job_id):
        import json
        from core.process_interfaces import (
            BuildReport,
            InterfaceManifest,
            SourceEnvelope,
        )
        from core.process_validation import canonical_digest
        from data_vault.process_ui_artifacts import ImmutableFileSet
        from ..workspace_path import WorkspacePath

        scope.require(process, "process.read")
        job = self.repository.get_job(process.workspace_id, job_id)
        if job.process != process or job.state not in {"preview_ready", "saved"}:
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "This job has no available built preview for this process.",
                "Open its current authoring job or use the common view.",
            )
        record = self.repository.get_authoring_record(
            process.workspace_id, job_id, "built"
        )
        manifest = InterfaceManifest.model_validate(record["manifest"])
        report = BuildReport.model_validate(record["build"])
        if manifest.process != job.process or manifest.revision_id != job.revision_id:
            raise ProcessInterfaceError(
                "SUBJECT_STALE",
                "The built revision and its job disagree.",
                "Inspect the immutable authoring records before presenting it.",
            )
        # IDs must be opaque identifiers allocated by the authoring owner. Never
        # interpolate arbitrary core.Identifier strings into filesystem paths.
        if not re.fullmatch(r"ui-[0-9a-f]{32}", manifest.ui_id) or not re.fullmatch(
            r"revision-[0-9a-f]{32}", manifest.revision_id
        ):
            raise ProcessInterfaceError(
                "UI_INCOMPATIBLE",
                "This revision uses an unsupported artifact identity.",
                "Create a current managed interface; retain older metadata for inspection.",
            )
        root = self.application.runs._root(scope, process)
        location = WorkspacePath(root).resolve(
            f".wright/process-uis/{manifest.ui_id}/revisions/{manifest.revision_id}"
        )
        try:
            content = ImmutableFileSet(location).read(record["inventory_digest"])
            source = SourceEnvelope.model_validate_json(content["source.json"])
            if (
                json.loads(content["binding.json"]) != manifest.model_dump(mode="json")
                or json.loads(content["build-report.json"])
                != report.model_dump(mode="json")
                or canonical_digest(source) != report.source_digest
                or canonical_digest(manifest) != report.manifest_digest
                or report.state != "built"
            ):
                raise ValueError("Immutable metadata changed")
            bundle = {
                name.removeprefix("dist/"): raw
                for name, raw in content.items()
                if name.startswith("dist/")
            }
            hashes = {
                name: hashlib.sha256(raw).hexdigest() for name, raw in bundle.items()
            }
            if (
                canonical_digest(hashes) != report.bundle_digest
                or sum(len(raw) for raw in bundle.values()) != report.bundled_bytes
            ):
                raise ValueError("Immutable bundle changed")
        except (OSError, ValueError, KeyError) as error:
            raise ProcessInterfaceError(
                "UI_INCOMPATIBLE",
                "The saved interface files could not be verified.",
                "Use the common view and restore or regenerate the exact interface revision.",
            ) from error
        return job, manifest, report, source, bundle

    def preview_bundle(self, scope, process, job_id):
        return self._load_built(scope, process, job_id)

    def presentation_bundle(self, scope, process, job_id):
        """Load an immutable origin build for a saved UI in the same source family.

        This permits presentation reuse only. The caller checks current bindings;
        backend operations and grants still name the exact current ProcessRef.
        Unsaved drafts, generation and save remain pinned to their origin revision.
        """
        scope.require(process, "process.read")
        job = self.repository.get_job(process.workspace_id, job_id)
        if job.process == process:
            return self._load_built(scope, process, job_id)
        if (
            job.state != "saved"
            or job.process.workspace_id != process.workspace_id
            or job.process.source_path != process.source_path
        ):
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "This build is not a saved interface from the current process.",
                "Choose a saved revision from this process or update the interface.",
            )
        built = self._load_built(scope, job.process, job_id)
        revision = self.repository.get_revision(
            process.workspace_id, built[1].ui_id, built[1].revision_id
        )
        self.saved_source(scope, job.process, revision)
        return built

    def observe_preview(
        self, scope, process, job_id, observation: ProcessUIPreviewObservation
    ):
        from pydantic import TypeAdapter
        from core.process_validation import Identifier
        from datetime import datetime, timezone

        job, manifest, report, _, _ = self._load_built(scope, process, job_id)
        if (
            not isinstance(observation, ProcessUIPreviewObservation)
            or observation.ui_id != manifest.ui_id
            or observation.revision_id != manifest.revision_id
            or observation.bundle_digest != report.bundle_digest
        ):
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "The preview observation belongs to another presentation bundle.",
                "Open the exact validated preview in Wright.",
            )
        presentation = TypeAdapter(Identifier).validate_python(
            observation.presentation_id
        )
        try:
            return self.repository.get_authoring_record(
                process.workspace_id, job.job_id, "preview"
            )
        except KeyError:
            return self.repository.retain_authoring_record(
                process.workspace_id,
                job.job_id,
                "preview",
                {
                    "presentation_id": presentation,
                    "previewed_at": datetime.now(timezone.utc).isoformat(),
                    "bundle_digest": report.bundle_digest,
                    "revision_id": manifest.revision_id,
                },
            )

    async def save(
        self,
        author_scope,
        process,
        job_id,
        *,
        expected_source_digest,
        expected_manifest_digest,
        expected_bundle_digest,
        expected_active_revision,
    ):
        from core.process_interfaces import InterfaceRevision
        from core.process_validation import canonical_digest
        from datetime import datetime, timezone
        from .compatibility import check_interface_compatibility

        author_scope.require(process)
        scope = author_scope.process_scope
        job, manifest, report, _, _ = self._load_built(scope, process, job_id)
        if (
            expected_source_digest,
            expected_manifest_digest,
            expected_bundle_digest,
        ) != (report.source_digest, report.manifest_digest, report.bundle_digest):
            raise ProcessInterfaceError(
                "SUBJECT_STALE",
                "This save request identifies different source or build bytes.",
                "Reload the exact validated preview before saving.",
            )
        try:
            preview = self.repository.get_authoring_record(
                process.workspace_id, job_id, "preview"
            )
        except KeyError:
            raise ProcessInterfaceError(
                "ACTION_NOT_PERMITTED",
                "This interface has not been opened in its managed preview.",
                "Open and inspect the built preview before saving it.",
            ) from None
        if (
            preview["bundle_digest"] != report.bundle_digest
            or preview["revision_id"] != manifest.revision_id
        ):
            raise ProcessInterfaceError(
                "SUBJECT_STALE",
                "The recorded preview does not identify this built revision.",
                "Open its exact preview again.",
            )
        revision = InterfaceRevision(
            manifest=manifest,
            source_digest=report.source_digest,
            build=report,
            role_resolution=job.role_resolution,
            generation_request_digest=job.request_digest,
            created_at=report.created_at,
            previewed_at=preview["previewed_at"],
        )
        compatibility = await check_interface_compatibility(
            self.application, scope, process, revision
        )
        if compatibility.state != "compatible":
            raise ProcessInterfaceError(
                "UI_INCOMPATIBLE",
                "This preview is incompatible with the current process view.",
                "Update its required bindings/capabilities or use the common working view.",
                details={
                    "reasons": [
                        reason.model_dump(mode="json")
                        for reason in compatibility.reasons
                    ]
                },
            )
        self.repository.save_revision(process.workspace_id, revision)
        ui = self.repository.get_ui(process.workspace_id, manifest.ui_id)
        if ui.active_revision != manifest.revision_id:
            self.repository.activate(
                process.workspace_id,
                manifest.ui_id,
                manifest.revision_id,
                expected_revision=expected_active_revision,
                updated_at=datetime.now(timezone.utc).isoformat(),
            )
        if job.state == "preview_ready":
            updated = type(job).model_validate(
                {
                    **job.model_dump(),
                    "state": "saved",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            self.repository.update_job(updated, expected_digest=canonical_digest(job))
        return revision

    async def activate(
        self, author_scope, process, ui_id, revision_id, *, expected_active_revision
    ):
        from datetime import datetime, timezone
        from .compatibility import check_interface_compatibility

        author_scope.require(process)
        revision = self.repository.get_revision(
            process.workspace_id, ui_id, revision_id
        )
        job = self.repository.job_for_revision(process.workspace_id, ui_id, revision_id)
        self.presentation_bundle(author_scope.process_scope, process, job.job_id)
        compatibility = await check_interface_compatibility(
            self.application, author_scope.process_scope, process, revision
        )
        if compatibility.state != "compatible":
            raise ProcessInterfaceError(
                "UI_INCOMPATIBLE",
                "This saved revision cannot be activated for the current process.",
                "Use the common view or update the changed bindings.",
            )
        return self.repository.activate(
            process.workspace_id,
            ui_id,
            revision_id,
            expected_revision=expected_active_revision,
            updated_at=datetime.now(timezone.utc).isoformat(),
        )

    def saved_source(self, scope, process, revision):
        from core.process_validation import canonical_digest

        manifest = revision.manifest
        job = self.repository.job_for_revision(
            process.workspace_id, manifest.ui_id, manifest.revision_id
        )
        _, actual_manifest, report, source, _ = self._load_built(
            scope, process, job.job_id
        )
        if (
            canonical_digest(actual_manifest) != canonical_digest(manifest)
            or report != revision.build
            or canonical_digest(source) != revision.source_digest
        ):
            raise ProcessInterfaceError(
                "UI_INCOMPATIBLE",
                "The saved revision and its artifact provenance disagree.",
                "Restore the immutable revision before updating it.",
            )
        return source.model_dump(mode="json")
