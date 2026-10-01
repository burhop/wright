"""Owning process UI boundary; execution/review/gateway remain existing services."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, get_args

from pydantic import TypeAdapter

from core.process_interactions import (
    Action,
    NavigationTarget,
    ProcessCapability,
    ProcessRef,
    Reason,
)
from core.process_validation import Identifier
from core.tracing import traced
from data_vault.process_input_repository import ProcessInputRepository
from data_vault.process_interface_repository import ProcessInterfaceRepository

from ..workflow_sources import WorkflowSourceDocument, WorkflowSourceStorageError
from .errors import ProcessInterfaceError
from .limits import ProcessInterfaceLimits

if TYPE_CHECKING:
    from ..service import WorkspaceService


@dataclass(frozen=True, slots=True)
class ProcessScope:
    """Server-derived invocation context; never a public request schema.

    Native auth/RBAC and managed presentation grants construct this scope. It is
    not a permission check by itself; each operation still checks live authority.
    """

    principal_id: str
    workspace_id: str
    capabilities: frozenset[ProcessCapability]

    def __post_init__(self):
        identifier = TypeAdapter(Identifier)
        object.__setattr__(
            self, "principal_id", identifier.validate_python(self.principal_id)
        )
        object.__setattr__(
            self, "workspace_id", identifier.validate_python(self.workspace_id)
        )
        if not isinstance(self.capabilities, frozenset) or not self.capabilities <= set(
            get_args(ProcessCapability)
        ):
            raise ValueError(
                "Process invocation requires closed configured capabilities"
            )

    def require(self, process: ProcessRef, operation: ProcessCapability) -> None:
        if (
            self.workspace_id != process.workspace_id
            or operation not in self.capabilities
        ):
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "This interface cannot perform that operation on this process.",
                "Open the process in its authorized Wright workspace.",
            )


@dataclass(frozen=True, slots=True)
class ResolvedProcess:
    process: ProcessRef
    workspace_dir: str
    document: WorkflowSourceDocument


class ProcessInterfaceService:
    def __init__(
        self,
        workspace: WorkspaceService,
        *,
        limits: ProcessInterfaceLimits | None = None,
    ):
        self.workspace = workspace
        self.db_path = workspace.db_path
        self.limits = limits or ProcessInterfaceLimits()

    @traced("process.interface.run.snapshot")
    async def get_snapshot(
        self,
        scope: ProcessScope,
        process: ProcessRef,
        *,
        run_id: str | None = None,
        input_snapshot_id: str | None = None,
        page: str | None = None,
        gateway=None,
        session_id: str = "",
    ):
        from .owners import recorded_run_facts
        from .projection import project_interactions

        resolved = await self.resolve_process(scope, process)
        if run_id is not None:
            if input_snapshot_id is not None:
                raise ProcessInterfaceError(
                    "RESPONSE_INVALID",
                    "A recorded run owns its original inputs.",
                    "Attach the run without overriding its frozen input identity.",
                )
            facts = await recorded_run_facts(
                self, resolved, run_id, gateway=gateway, session_id=session_id
            )
        else:
            from datetime import datetime, timezone
            from .readiness import prepare_values, qualify_inputs
            from .projection import ProjectionFacts

            frozen = (
                self._input_snapshot(process, input_snapshot_id)
                if input_snapshot_id
                else None
            )
            prepared = await prepare_values(
                self, resolved, snapshot=frozen, gateway=gateway, session_id=session_id
            )
            readiness = await qualify_inputs(
                self, resolved, prepared, gateway=gateway, session_id=session_id
            )
            # Reading defaults does not create persistent preparation. The client
            # calls setInputs, including for unchanged defaults, before start.
            if frozen is None:
                readiness = type(readiness).model_validate(
                    {**readiness.model_dump(), "input_digest": None}
                )
            facts = ProjectionFacts(
                process=process,
                generated_at=datetime.now(timezone.utc).isoformat(),
                input_snapshot=frozen,
                inputs=prepared.definitions,
                readiness=readiness,
                actions=(
                    Action(
                        action_id="start",
                        operation="start",
                        title="Start process",
                        enabled=frozen is not None and readiness.state == "ready",
                        subject_digest=frozen.digest if frozen is not None else None,
                        reasons=readiness.reasons
                        if readiness.state != "ready"
                        else ()
                        if frozen is not None
                        else (
                            Reason(
                                code="INPUT_REQUIRED",
                                message="Prepare the inputs before starting.",
                                correction="Save these values as this run's input preparation.",
                            ),
                        ),
                    ),
                ),
            )
        return project_interactions(facts, scope, page=page)

    def _input_snapshot(self, process, snapshot_id):
        try:
            snapshot = self.inputs.get_snapshot(process.workspace_id, snapshot_id)
        except KeyError as error:
            raise ProcessInterfaceError(
                "SUBJECT_STALE",
                "The input preparation is unavailable in this workspace.",
                "Prepare this process's inputs again.",
            ) from error
        if snapshot.process != process:
            raise ProcessInterfaceError(
                "SUBJECT_STALE",
                "These inputs belong to a different accepted process.",
                "Prepare inputs for this exact source revision.",
            )
        return snapshot

    @traced("process.interface.inputs.set")
    async def set_inputs(
        self, scope, process, *, bindings=(), gateway=None, session_id=""
    ):
        from .readiness import prepare_values

        resolved = await self.resolve_process(
            scope, process, operation="process.inputs"
        )
        prepared = await prepare_values(
            self, resolved, bindings=bindings, gateway=gateway, session_id=session_id
        )
        self.inputs.put_snapshot(prepared.snapshot)
        return prepared

    @traced("process.interface.readiness.check")
    async def check_readiness(
        self, scope, process, input_snapshot_id, *, gateway=None, session_id=""
    ):
        from .readiness import prepare_values, qualify_inputs

        resolved = await self.resolve_process(scope, process)
        frozen = self._input_snapshot(process, input_snapshot_id)
        prepared = await prepare_values(
            self, resolved, snapshot=frozen, gateway=gateway, session_id=session_id
        )
        if prepared.snapshot != frozen:
            raise ProcessInterfaceError(
                "SUBJECT_STALE",
                "The prepared inputs no longer match the frozen values.",
                "Prepare the current values before starting.",
            )
        return await qualify_inputs(
            self, resolved, prepared, gateway=gateway, session_id=session_id
        )

    @cached_property
    def runs(self):
        from .runs import ProcessRunSupervisor

        return ProcessRunSupervisor(self)

    @cached_property
    def inputs(self) -> ProcessInputRepository:
        return ProcessInputRepository(self.db_path)

    @cached_property
    def human_inputs(self):
        from data_vault.workflow_continuation_repository import (
            WorkflowContinuationRepository,
        )
        from .interactions import HumanInputCheckpointService

        return HumanInputCheckpointService(
            WorkflowContinuationRepository(self.db_path), self.inputs
        )

    @cached_property
    def reviews(self):
        from .decisions import ProcessReviewDecisions

        return ProcessReviewDecisions(self)

    async def close(self):
        # Do not create a supervisor solely to shut an unused service down.
        supervisor = self.__dict__.get("runs")
        if supervisor is not None:
            await supervisor.close()
        authoring = self.__dict__.get("_authoring")
        if authoring is not None:
            await authoring.close()

    def configure_authoring(self, engine, toolchain):
        """Native composition supplies existing engine and trusted compiler config."""
        from .authoring import ProcessInterfaceAuthoring

        prior = self.__dict__.get("_authoring")
        if prior is None:
            prior = ProcessInterfaceAuthoring(self, engine, toolchain)
            self.__dict__["_authoring"] = prior
        elif prior.engine is not engine or prior.toolchain != toolchain:
            raise ValueError(
                "An active authoring owner cannot silently change its model/compiler configuration"
            )
        return prior

    @cached_property
    def ui_revisions(self):
        from .artifacts import ProcessInterfaceRevisions

        return ProcessInterfaceRevisions(self)

    @cached_property
    def artifacts(self):
        from .artifacts import ProcessArtifactAccess

        return ProcessArtifactAccess(self)

    @cached_property
    def navigation(self):
        from .navigation import ProcessNavigation

        return ProcessNavigation(self)

    @cached_property
    def interfaces(self) -> ProcessInterfaceRepository:
        return ProcessInterfaceRepository(self.db_path)

    @traced("process.interface.source.resolve")
    async def resolve_process(
        self,
        scope: ProcessScope,
        process: ProcessRef,
        *,
        operation: ProcessCapability = "process.read",
    ) -> ResolvedProcess:
        scope.require(process, operation)
        if process.source_contract != "canonical-source":
            raise ProcessInterfaceError(
                "READINESS_UNSUPPORTED",
                "This process source format is not supported by the working interface.",
                "Use a supported accepted Wright workflow source.",
            )
        record = self.workspace.repository.get_by_id(scope.workspace_id)
        if record is None:
            raise ProcessInterfaceError(
                "SCOPE_DENIED",
                "The process workspace is unavailable.",
                "Open a registered Wright workspace.",
            )
        root = str(record["local_path"])
        self.workspace.ensure_workspace_path_safe(root)
        try:
            document = await self.workspace.workflow_sources.read(
                root, process.source_path
            )
        except WorkflowSourceStorageError as exc:
            raise ProcessInterfaceError(
                "CAPABILITY_UNAVAILABLE",
                "Wright could not read the accepted process.",
                "Open its workflow file and check that it is available.",
                navigation=NavigationTarget(kind="process"),
                details={"storage_error": exc.code},
            ) from exc
        if document.storage_digest != process.source_digest:
            raise ProcessInterfaceError(
                "SOURCE_CHANGED",
                "This process has changed since the interface was prepared.",
                "Reload the accepted workflow and prepare its inputs again.",
                navigation=NavigationTarget(kind="process"),
            )
        if process.semantic_digest is not None and process.semantic_digest != getattr(
            document, "semantic_digest", None
        ):
            raise ProcessInterfaceError(
                "SOURCE_CHANGED",
                "The accepted process identity could not be confirmed.",
                "Reload the workflow's current supported source reference.",
                navigation=NavigationTarget(kind="process"),
            )
        return ResolvedProcess(process=process, workspace_dir=root, document=document)
