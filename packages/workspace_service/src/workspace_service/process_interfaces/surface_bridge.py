"""Authorize an already authenticated presentation through existing grant/owners.

No cookie parsing, HTTP routing, command scheduler or process executor lives here.
The preview route authority supplies its presentation and pinned runtime facts.
"""

from dataclasses import dataclass
import re

from pydantic import ValidationError

from ..surfaces.grants import (
    CapabilityGrantError,
    CapabilityRequest,
    ProcessPresentationBinding,
)
from ..surfaces.process_ui_manifest import process_ui_manifest
from ..surfaces.service import ActorRole, SurfaceActor
from .errors import ProcessInterfaceError
from .service import ProcessScope


@dataclass(frozen=True)
class AuthorizedProcessPresentation:
    binding: ProcessPresentationBinding
    scope: ProcessScope
    job_id: str
    session_id: str
    source_version: str
    instance_id: str


def _denied():
    return ProcessInterfaceError(
        "SCOPE_DENIED",
        "This presentation cannot access the requested process operation.",
        "Reopen the exact process interface in Wright or use its common working view.",
    )


def presentation_start_key(presentation_id):
    from core.process_validation import canonical_digest

    return "view-start-" + canonical_digest({"presentation_id": presentation_id})


class ProcessSurfaceBridge:
    def __init__(self, application, grant_service):
        self.application, self.grants = application, grant_service

    @staticmethod
    def retain_start(application, context, request):
        """Retain an exact view/request association before existing start execution.

        This is a locator, not a receipt, permission or independent run status.
        One view cannot submit a second start identity after an uncertain reply.
        """
        from data_vault.process_input_repository import ProcessRecordConflict

        binding = context.binding
        context.scope.require(binding.process, "process.start")
        if binding.read_only or binding.run_id is not None:
            raise _denied()
        payload = {
            "binding": binding.model_dump(mode="json"),
            "principal_id": context.scope.principal_id,
            "session_id": context.session_id,
            "instance_id": context.instance_id,
            "source_version": context.source_version,
            "request_id": request.request_id,
            "input_snapshot_id": request.input_snapshot_id,
            "input_digest": request.expected_input_digest,
            "integration_policy_digest": request.integration_policy_digest,
        }
        try:
            return application.interfaces.retain_authoring_record(
                binding.process.workspace_id,
                context.job_id,
                presentation_start_key(binding.presentation_id),
                payload,
            )
        except ProcessRecordConflict:
            raise ProcessInterfaceError(
                "REQUEST_CONFLICT",
                "This interface view already identifies a different start request.",
                "Reconcile its recorded request or prepare another run in a new view.",
            ) from None

    def revalidate(self, route, context, operation="process.read"):
        """Recheck live stream authority without repeatedly reading a bundle.

        Initial authorization verified immutable artifacts and the run receipt.
        Every streamed chunk still requires the same live presentation, pinned
        generation and exact unexpired, unrevoked read/operation grants.
        """
        binding = context.binding
        if not route.authority_valid() or not route.target_valid():
            raise ProcessInterfaceError(
                "PRESENTATION_EXPIRED",
                "This presentation's authority is no longer current.",
                "Reopen the interface in its Wright workspace.",
            )
        if (
            not route.http_declared
            or context.scope.principal_id != route.principal_id
            or context.scope.workspace_id != route.workspace_id
            or context.session_id != route.session_id
            or context.instance_id != route.instance_id
            or context.source_version != route.source_version
            or binding.presentation_id != route.presentation_id
            or binding.generation != route.generation
            or route.source_id != f"process.{binding.ui_id}.{binding.revision_id}"
        ):
            raise _denied()
        context.scope.require(binding.process, operation)
        actor = SurfaceActor(
            user_id=route.principal_id,
            workspace_id=route.workspace_id,
            session_id=route.session_id,
            role=ActorRole.ENGINEER,
        )
        for capability in {"process.read", operation}:
            try:
                self.grants.authorize(
                    actor=actor,
                    request=CapabilityRequest(
                        source_id=route.source_id,
                        source_version=route.source_version,
                        instance_id=route.instance_id,
                        capability=capability,
                        operation=capability,
                        constraints=binding.model_dump(mode="json"),
                        risk_tier="low"
                        if capability
                        in {"process.read", "process.results", "process.navigate"}
                        else "mutating",
                        persistence="instance",
                        duration_seconds=600,
                        declared=True,
                        decision="allow",
                        reason="Read the exact native-authorized process presentation.",
                    ),
                )
            except CapabilityGrantError:
                raise _denied() from None
        route.activity()

    def authorize(
        self, route, operation="process.read"
    ) -> AuthorizedProcessPresentation:
        if (
            not route.authority_valid()
            or not route.target_valid()
            or not route.http_declared
        ):
            raise ProcessInterfaceError(
                "PRESENTATION_EXPIRED",
                "This presentation's authority is no longer current.",
                "Reopen the interface in its Wright workspace.",
            )
        match = re.fullmatch(
            r"process\.(ui-[0-9a-f]{32})\.(revision-[0-9a-f]{32})", route.source_id
        )
        if not match or not route.source_version:
            raise _denied()
        ui_id, revision_id = match.groups()
        candidates = self.grants.repository.list(
            user_id=route.principal_id,
            workspace_id=route.workspace_id,
            source_id=route.source_id,
            source_version=route.source_version,
        )
        bindings = {}
        for record in candidates:
            if (
                record.capability != "process.read"
                or record.instance_id != route.instance_id
            ):
                continue
            try:
                binding = ProcessPresentationBinding.model_validate(record.constraints)
            except ValidationError:
                continue
            if (
                binding.presentation_id == route.presentation_id
                and binding.generation == route.generation
                and binding.ui_id == ui_id
                and binding.revision_id == revision_id
                and binding.process.workspace_id == route.workspace_id
            ):
                from core.process_validation import canonical_digest

                bindings[canonical_digest(binding)] = binding
        if len(bindings) != 1:
            raise _denied()
        binding = next(iter(bindings.values()))
        actor = SurfaceActor(
            user_id=route.principal_id,
            workspace_id=route.workspace_id,
            session_id=route.session_id,
            role=ActorRole.ENGINEER,
        )
        # The identity of the interface comes from the native owner and exact
        # grants. A vendor/MCP App declaration cannot adopt this reserved bridge.
        try:
            job = self.application.interfaces.job_for_revision(
                route.workspace_id, ui_id, revision_id
            )
            preliminary = ProcessScope(
                route.principal_id,
                route.workspace_id,
                frozenset({"process.read", "process.results", "process.navigate"}),
            )
            _, manifest, _, _, _ = self.application.ui_revisions.preview_bundle(
                preliminary, binding.process, job.job_id
            )
            record = self.application.interfaces.get_authoring_record(
                route.workspace_id, job.job_id, "built"
            )
            root = self.application.runs._root(preliminary, binding.process)
            _, declaration = process_ui_manifest(
                root, manifest, record["inventory_digest"]
            )
            if (
                declaration.canonical_hash != route.source_version
                or operation not in manifest.capabilities
            ):
                raise _denied()
            capabilities = set()
            for capability in manifest.capabilities:
                read = capability in {
                    "process.read",
                    "process.results",
                    "process.navigate",
                }
                request = CapabilityRequest(
                    source_id=route.source_id,
                    source_version=route.source_version,
                    instance_id=route.instance_id,
                    capability=capability,
                    operation=capability,
                    constraints=binding.model_dump(mode="json"),
                    risk_tier="low" if read else "mutating",
                    persistence="instance",
                    duration_seconds=600,
                    declared=True,
                    decision="allow",
                    reason="Use the exact native-authorized process presentation.",
                )
                try:
                    self.grants.authorize(actor=actor, request=request)
                    capabilities.add(capability)
                except CapabilityGrantError:
                    pass
            if "process.read" not in capabilities or operation not in capabilities:
                raise _denied()
            scope = ProcessScope(
                route.principal_id,
                route.workspace_id,
                frozenset(capabilities),
                run_bound=True,
                run_id=binding.run_id,
            )
            if binding.run_id is not None:
                # Existing receipt owner proves the run belongs to this exact
                # accepted source. No generated UI may substitute another run.
                self.application.runs._receipt(scope, binding.process, binding.run_id)
            route.activity()
            return AuthorizedProcessPresentation(
                binding,
                scope,
                job.job_id,
                route.session_id,
                route.source_version,
                route.instance_id,
            )
        except (KeyError, ValueError, CapabilityGrantError):
            raise _denied() from None
