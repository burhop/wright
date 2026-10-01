"""Durable presentation authoring through the existing agent-engine boundary.

This owner has no process execution, approval or engineering tool authority.
Native authenticated routes supply authoring permission separately from managed
process-client grants. Closing a view only detaches its observer.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from pydantic import TypeAdapter, ValidationError

from agent_adapters.base import (
    AgentChatRequest,
    AgentInvocationContext,
    BaseAgentEngine,
)
from core.process_interfaces import (
    AuthoringJob,
    CodingRole,
    InterfaceManifest,
    ProcessUI,
    RoleResolution,
)
from core.process_interactions import Reason
from core.process_validation import Identifier, canonical_digest, canonical_json
from core.tracing import traced
from data_vault.process_ui_artifacts import ImmutableFileSet

from ..workspace_path import WorkspacePath
from ..workflow_resource_lease import ApplicationLease, lease_is_active
from .build import BuildToolchain, build_interface, validate_manifest_bindings
from .errors import ProcessInterfaceError
from .inputs import _descriptors, _sections
from .resources import AuthoringOutput, load_authoring_resources
from .service import ProcessScope


def _now():
    return datetime.now(timezone.utc).isoformat()


def _reason(message, correction, code="UI_AUTHORING_FAILED"):
    return Reason(code=code, message=message, correction=correction)


@dataclass(frozen=True)
class NativeAuthoringScope:
    """Created by native authentication/RBAC, never accepted as request data."""

    process_scope: ProcessScope
    may_author: bool

    def require(self, process):
        self.process_scope.require(process, "process.read")
        if self.may_author is not True:
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "This view cannot create or change process interfaces.",
                "Use an authorized native Wright workspace authoring view.",
            )


def accepted_binding_catalog(document) -> list[dict]:
    """Stable supported declarations only; no invented runtime observations.

    Provider-qualified extensions and actual run subjects may add reviewed
    selectors later. An unsupported mandatory selector remains unavailable.
    Input defaults, file bytes and engineering results are excluded from prompts.
    """
    plan, blocks = _sections(document.source)
    definitions, _, _ = _descriptors(plan, blocks)
    catalog = [
        {
            "kind": "input",
            "selector": definition.input_id,
            "block_id": definition.block_id,
            "port_id": definition.port_id,
            "expected_schema": definition.value_schema,
        }
        for definition, _ in definitions
    ]
    for block in blocks:
        if block["kind"] != "task":
            continue
        for port in block["fields"].get("outputs", []):
            catalog.append(
                {
                    "kind": "output",
                    "selector": f"{block['id']}.{port['key']}",
                    "block_id": block["id"],
                    "port_id": port["key"],
                    "expected_schema": None,
                }
            )
    return catalog


class ProcessInterfaceAuthoring:
    def __init__(
        self,
        application,
        engine: BaseAgentEngine,
        toolchain: BuildToolchain,
        *,
        maximum_active: int = 4,
    ):
        if type(maximum_active) is not int or not 1 <= maximum_active <= 16:
            raise ValueError("Authoring capacity must be bounded")
        self.application, self.engine, self.toolchain = application, engine, toolchain
        self.repository = application.interfaces
        self.maximum_active = maximum_active
        self._tasks: dict[str, asyncio.Task] = {}
        self._allocation = asyncio.Lock()
        self._closed = False

    async def capabilities(self):
        capability = await self.engine.get_invocation_capabilities()
        try:
            compiler = self.toolchain.describe()
            compiler_reason = None
        except ProcessInterfaceError as error:
            compiler, compiler_reason = None, error.reason.model_dump(mode="json")
        from dataclasses import asdict

        return {
            "role": "process-ui-author/1",
            "model": asdict(capability),
            "compiler": compiler,
            "compiler_reason": compiler_reason,
            "available": capability.available and compiler is not None,
        }

    def _transition(self, job, state, **changes):
        updated = AuthoringJob.model_validate(
            {**job.model_dump(), "state": state, "updated_at": _now(), **changes}
        )
        return self.repository.update_job(
            updated, expected_digest=canonical_digest(job)
        )

    @traced("process.ui.authoring.submit")
    async def submit(
        self,
        scope: NativeAuthoringScope,
        process,
        request_id: str,
        instruction: str,
        *,
        title="Process interface",
        ui_id=None,
        base_revision=None,
        trace_id=None,
    ):
        scope.require(process)
        request_id = TypeAdapter(Identifier).validate_python(request_id)
        trace_id = TypeAdapter(Identifier).validate_python(trace_id or uuid4().hex)
        if (
            not isinstance(instruction, str)
            or not instruction.strip()
            or len(instruction.encode()) > 16_384
        ):
            raise ProcessInterfaceError(
                "RESPONSE_INVALID",
                "Describe the interface within the supported text limit.",
                "Provide a nonempty request of at most 16 KiB.",
            )
        if not isinstance(title, str) or not title.strip() or len(title) > 512:
            raise ProcessInterfaceError(
                "RESPONSE_INVALID",
                "The interface title is invalid.",
                "Use a short nonempty title.",
            )
        if (ui_id is None) != (base_revision is None):
            raise ProcessInterfaceError(
                "RESPONSE_INVALID",
                "An update needs its exact saved interface and revision.",
                "Select the interface revision to update.",
            )
        request = {
            "principal_id": scope.process_scope.principal_id,
            "process": process.model_dump(mode="json"),
            "instruction": instruction,
            "title": title,
            "ui_id": ui_id,
            "base_revision": base_revision,
        }
        digest = canonical_digest(request)
        async with self._allocation:
            # Reconcile before any source/model/compiler reads. A lost HTTP reply
            # must not allocate another session, default-model call or build.
            prior = self.repository.job_for_request(
                process.workspace_id, process.source_path, request_id
            )
            if prior:
                if prior.request_digest != digest or prior.process != process:
                    raise ProcessInterfaceError(
                        "REQUEST_CONFLICT",
                        "This generation request already has different content.",
                        "Open its recorded job or use a new request identity for the change.",
                    )
                return await self.status(scope, process, prior.job_id)
            if (
                self._closed
                or sum(not task.done() for task in self._tasks.values())
                >= self.maximum_active
            ):
                raise ProcessInterfaceError(
                    "CAPABILITY_UNAVAILABLE",
                    "The interface authoring service has no capacity.",
                    "Wait for an active generation or reconnect to the running service.",
                )
            resolved = await self.application.resolve_process(
                scope.process_scope, process
            )
            resources = load_authoring_resources()
            catalog = accepted_binding_catalog(resolved.document)
            previous = None
            if ui_id:
                ui = self.repository.get_ui(process.workspace_id, ui_id)
                revision = self.repository.get_revision(
                    process.workspace_id, ui_id, base_revision
                )
                if ui.archived or ui.process.source_path != process.source_path:
                    raise ProcessInterfaceError(
                        "SCOPE_DENIED",
                        "This interface belongs to a different process.",
                        "Choose a saved revision from the current process.",
                    )
                previous = self.application.ui_revisions.saved_source(
                    scope.process_scope, revision.manifest.process, revision
                )
            capability = await self.engine.get_invocation_capabilities()
            if (
                not capability.available
                or not capability.model_reference
                or not capability.configuration_digest
            ):
                raise ProcessInterfaceError(
                    "CAPABILITY_UNAVAILABLE",
                    "Confined default-model interface authoring is unavailable.",
                    "Configure a qualified adapter; the common working view remains usable.",
                )
            self.toolchain.describe()
            role = CodingRole(
                instructions_version=resources.version,
                instructions_digest=resources.instructions_digest,
                max_repairs=self.application.limits.maximum_repairs,
            )
            resolution = RoleResolution(
                profile=role,
                adapter=capability.adapter,
                model_reference=capability.model_reference,
                configuration_digest=capability.configuration_digest,
                effective_instructions_digest=resources.instructions_digest,
                capability_scope=(),
            )
            manifest = InterfaceManifest(
                ui_id=ui_id or "ui-" + uuid4().hex,
                revision_id="revision-" + uuid4().hex,
                parent_revision=base_revision,
                title=title,
                process=process,
                client_version="1.0.0",
                kit_version="1.0.0",
            )
            now = _now()
            job = AuthoringJob(
                job_id="job-" + uuid4().hex,
                request_id=request_id,
                request_digest=digest,
                process=process,
                base_revision=base_revision,
                role_resolution=resolution,
                state="queued",
                created_at=now,
                updated_at=now,
            )
            job, created = self.repository.create_job(job)
            if not created:
                return await self.status(scope, process, job.job_id)
            self.repository.retain_authoring_record(
                process.workspace_id,
                job.job_id,
                "request",
                {
                    "request": request,
                    "trace_id": trace_id,
                    "workspace_dir": resolved.workspace_dir,
                    "instructions": resources.instructions,
                    "resource_digest": resources.resource_digest,
                    "template": resources.template,
                    "output_schema": resources.output_schema,
                    "catalog": catalog,
                    "available_capabilities": sorted(scope.process_scope.capabilities),
                    "manifest": manifest.model_dump(mode="json"),
                    "previous_source": previous,
                },
            )
            if not ui_id:
                self.repository.create_ui(
                    ProcessUI(
                        ui_id=manifest.ui_id,
                        process=process,
                        title=title,
                        created_at=now,
                        updated_at=now,
                    )
                )
            started = asyncio.Event()
            task = asyncio.create_task(
                self._run(job, started), name=f"process-ui:{job.job_id}"
            )
            self._tasks[job.job_id] = task
            task.add_done_callback(lambda done: self._tasks.pop(job.job_id, None))
            await started.wait()
            return job

    def _authorized(self, scope, process, job_id):
        scope.require(process)
        try:
            job = self.repository.get_job(process.workspace_id, job_id)
        except KeyError:
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "This authoring job is unavailable in this workspace.",
                "Open the job from its originating process.",
            ) from None
        if job.process != process:
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "This job belongs to another accepted process.",
                "Use the job's exact process reference.",
            )
        return job

    async def status(self, scope, process, job_id):
        job = self._authorized(scope, process, job_id)
        if (
            job.state in {"queued", "resolving", "generating", "validating", "building"}
            and job_id not in self._tasks
        ):
            try:
                self.repository.get_authoring_record(
                    process.workspace_id, job_id, "request"
                )
                root = self.application.runs._root(scope.process_scope, process)
                directory = WorkspacePath(root).resolve(
                    ".wright/process-uis/authoring-locks"
                )
                alive = lease_is_active("process-ui:" + job_id, directory=directory)
                # Another owner may have committed the queued identity moments
                # before acquiring its lease. It must never be replayed here.
                if (
                    alive is None
                    and (
                        datetime.now(timezone.utc)
                        - datetime.fromisoformat(job.created_at)
                    ).total_seconds()
                    < 5
                ):
                    alive = True
            except (KeyError, OSError, TypeError, ValueError):
                alive = False
            if not alive:
                job = self._transition(
                    job,
                    "failed",
                    diagnostics=(
                        _reason(
                            "The interface authoring runtime was interrupted. Its generation was not replayed.",
                            "Keep using the common view and explicitly request a fresh generation when ready.",
                            "UI_AUTHORING_INTERRUPTED",
                        ),
                    ),
                )
        return job

    async def wait(self, scope, process, job_id):
        self._authorized(scope, process, job_id)
        task = self._tasks.get(job_id)
        if task:
            await asyncio.shield(task)
        return await self.status(scope, process, job_id)

    async def cancel(self, scope, process, job_id):
        async with self._allocation:
            job = self._authorized(scope, process, job_id)
            if job.state in {"saved", "cancelled", "failed"}:
                return job
            task = self._tasks.get(job_id)
            if task:
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
                return self.repository.get_job(process.workspace_id, job_id)
            if job.state == "preview_ready":
                return self._transition(job, "cancelled")
            recovered = await self.status(scope, process, job_id)
            if recovered.state == "failed":
                return recovered
            raise ProcessInterfaceError(
                "CAPABILITY_UNAVAILABLE",
                "This generation is owned by another active runtime.",
                "Cancel it through the owning Wright runtime; no duplicate model call was issued.",
            )

    async def close(self):
        self._closed = True
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _response(self, job, context, prompt, trace_id):
        text, attestation, ended, count = [], None, False, 0
        async with asyncio.timeout(150):
            async for event in self.engine.stream_chat(
                AgentChatRequest(
                    session_id=job.job_id,
                    message=prompt,
                    invocation_context=context,
                    trace_id=trace_id,
                )
            ):
                count += 1
                if count > 4096:
                    raise ValueError("Authoring stream exceeded its event bound")
                if event.type == "token":
                    value = event.data.get("text")
                    if not isinstance(value, str):
                        raise ValueError("Invalid authoring text event")
                    text.append(value)
                    if sum(len(part.encode()) for part in text) > 1_048_576:
                        raise ValueError("Authoring source exceeded its byte bound")
                elif (
                    event.type == "progress"
                    and "effective_instructions_digest" in event.data
                ):
                    actual = event.data.get("resolution", {})
                    if (
                        event.data["effective_instructions_digest"]
                        != context.instructions_digest
                        or actual.get("model_reference")
                        != job.role_resolution.model_reference
                        or actual.get("configuration_digest")
                        != job.role_resolution.configuration_digest
                    ):
                        raise ValueError(
                            "Authoring provenance did not match the prepared role"
                        )
                    attestation = {
                        "effective_instructions_digest": context.instructions_digest,
                        "model_reference": actual["model_reference"],
                        "configuration_digest": actual["configuration_digest"],
                        "response_model": event.data.get("response_model"),
                    }
                elif event.type == "stream_end":
                    ended = True
                elif event.type not in {"progress"}:
                    raise ValueError(
                        "The confined role returned an error or tool request"
                    )
        if not ended or not attestation:
            raise ValueError(
                "Authoring did not confirm its completed confined invocation"
            )
        return "".join(text), attestation

    async def _run(self, initial, started):
        job = initial
        lease = None
        try:
            record = self.repository.get_authoring_record(
                job.process.workspace_id, job.job_id, "request"
            )
            lease = ApplicationLease(
                "process-ui:" + job.job_id,
                timeout=1,
                directory=WorkspacePath(record["workspace_dir"]).resolve(
                    ".wright/process-uis/authoring-locks"
                ),
            )
            await lease.__aenter__()
            started.set()
            job = self._transition(job, "resolving")
            profile = job.role_resolution.profile
            context = AgentInvocationContext(
                role=profile.role,
                version=profile.version,
                instructions_version=profile.instructions_version,
                instructions=record["instructions"],
                instructions_digest=profile.instructions_digest,
                expected_model_reference=job.role_resolution.model_reference,
                expected_configuration_digest=job.role_resolution.configuration_digest,
            )
            expected = InterfaceManifest.model_validate(record["manifest"])
            prompt_base = {
                "request": record["request"]["instruction"],
                "manifest": record["manifest"],
                "binding_catalog": record["catalog"],
                "available_process_capabilities": record["available_capabilities"],
                "output_schema": record["output_schema"],
                "reference_template": record["template"],
                "previous_source": record["previous_source"],
            }
            correction = None
            job = self._transition(job, "generating")
            while True:
                prompt = canonical_json({**prompt_base, "correction": correction})
                raw, attestation = await self._response(
                    job, context, prompt, record["trace_id"]
                )
                self.repository.retain_authoring_record(
                    job.process.workspace_id,
                    job.job_id,
                    f"attempt-{job.repair_attempt}",
                    {"prompt": prompt, "response": raw, "attestation": attestation},
                )
                job = self._transition(job, "validating")
                try:
                    output = AuthoringOutput.model_validate_json(raw)
                    manifest = output.manifest
                    if any(
                        getattr(manifest, field) != getattr(expected, field)
                        for field in (
                            "ui_id",
                            "revision_id",
                            "parent_revision",
                            "process",
                        )
                    ):
                        raise ProcessInterfaceError(
                            "UI_INCOMPATIBLE",
                            "The generated interface changed its assigned identities.",
                            "Keep Wright's exact UI/revision/parent/process identities.",
                        )
                    validate_manifest_bindings(manifest, job.process, record["catalog"])
                    if not set(manifest.capabilities) <= set(
                        record["available_capabilities"]
                    ):
                        raise ProcessInterfaceError(
                            "UI_INCOMPATIBLE",
                            "The interface requests a process capability unavailable to this authoring view.",
                            "Use only Wright's supplied available_process_capabilities and disclose unavailable operations.",
                        )
                    job = self._transition(job, "building")
                    report, payload = await self._build_candidate(output, job, record)
                    self.repository.retain_authoring_record(
                        job.process.workspace_id,
                        job.job_id,
                        f"build-{job.repair_attempt}",
                        {"report": report.model_dump(mode="json")},
                    )
                    if report.state != "built":
                        diagnostics = report.diagnostics
                    else:
                        destination = WorkspacePath(record["workspace_dir"]).resolve(
                            f".wright/process-uis/{manifest.ui_id}/revisions/{manifest.revision_id}"
                        )
                        inventory_digest = ImmutableFileSet(destination).publish(
                            payload
                        )
                        self.repository.retain_authoring_record(
                            job.process.workspace_id,
                            job.job_id,
                            "built",
                            {
                                "manifest": manifest.model_dump(mode="json"),
                                "build": report.model_dump(mode="json"),
                                "inventory_digest": inventory_digest,
                            },
                        )
                        job = self._transition(
                            job,
                            "preview_ready",
                            revision_id=manifest.revision_id,
                            diagnostics=(),
                        )
                        return
                except ValidationError as error:
                    # Locations and error categories are useful; Pydantic input
                    # values/exception contexts may contain private source data.
                    locations = [
                        ".".join(str(part) for part in e["loc"]) + ": " + e["type"]
                        for e in error.errors(
                            include_input=False, include_context=False
                        )[:16]
                    ]
                    diagnostics = (
                        _reason(
                            "The structured interface source is invalid: "
                            + "; ".join(locations)[:1600],
                            "Return only the exact structured output schema supplied by Wright.",
                        ),
                    )
                except ProcessInterfaceError as error:
                    diagnostics = (error.reason,)
                if job.repair_attempt >= profile.max_repairs:
                    job = self._transition(job, "failed", diagnostics=diagnostics)
                    return
                correction = [reason.model_dump(mode="json") for reason in diagnostics]
                job = self._transition(
                    job,
                    "generating",
                    repair_attempt=job.repair_attempt + 1,
                    diagnostics=diagnostics,
                )
        except asyncio.CancelledError:
            current = self.repository.get_job(job.process.workspace_id, job.job_id)
            if current.state not in {"saved", "failed", "cancelled"}:
                self._transition(current, "cancelled")
            raise
        except Exception:
            # Do not retain raw adapter/build exceptions: SDK errors can contain
            # credentials. Exact structured diagnostics are retained above.
            current = self.repository.get_job(job.process.workspace_id, job.job_id)
            if current.state not in {"saved", "failed", "cancelled"}:
                self._transition(
                    current,
                    "failed",
                    diagnostics=(
                        _reason(
                            "Wright could not finish this confined interface generation.",
                            "Check model/compiler readiness or the retained build diagnostics. The common view remains available.",
                        ),
                    ),
                )
        finally:
            started.set()
            if lease is not None:
                await lease.__aexit__(None, None, None)

    async def _build_candidate(self, output, job, record):
        # Windows process launch rejects very deep working directories even when
        # Python file I/O supports them. The owned fixed compiler gets a short
        # temporary draft; immutable publication remains in the authorized vault.
        with TemporaryDirectory(prefix="wright-ui-") as temporary:
            built = await build_interface(
                source=output.source,
                manifest=output.manifest,
                process=job.process,
                catalog=record["catalog"],
                toolchain=self.toolchain,
                builds_root=Path(temporary),
            )
            if built.report.state != "built":
                return built.report, None
            payload = {
                "source.json": canonical_json(output.source).encode(),
                "binding.json": canonical_json(output.manifest).encode(),
                "build-report.json": canonical_json(built.report).encode(),
            }
            for path in sorted(built.dist.rglob("*")):
                if path.is_symlink():
                    raise ValueError("Compiled files cannot contain links")
                if path.is_file():
                    payload["dist/" + path.relative_to(built.dist).as_posix()] = (
                        path.read_bytes()
                    )
            inventory = {
                name.removeprefix("dist/"): hashlib.sha256(raw).hexdigest()
                for name, raw in payload.items()
                if name.startswith("dist/")
            }
            if (
                canonical_digest(inventory) != built.report.bundle_digest
                or sum(
                    len(raw)
                    for name, raw in payload.items()
                    if name.startswith("dist/")
                )
                != built.report.bundled_bytes
            ):
                raise ValueError("Compiled files changed before immutable publication")
            return built.report, payload
