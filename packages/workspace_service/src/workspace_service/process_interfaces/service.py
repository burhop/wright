"""Owning process UI boundary; execution/review/gateway remain existing services."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cached_property
from typing import TYPE_CHECKING, get_args

from pydantic import TypeAdapter

from core.process_interactions import NavigationTarget, ProcessCapability, ProcessRef
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
        run_id: str,
        page: str | None = None,
        gateway=None,
        session_id: str = "",
    ):
        from .owners import recorded_run_facts
        from .projection import project_interactions

        resolved = await self.resolve_process(scope, process)
        facts = await recorded_run_facts(
            self, resolved, run_id, gateway=gateway, session_id=session_id
        )
        return project_interactions(facts, scope, page=page)

    @cached_property
    def inputs(self) -> ProcessInputRepository:
        return ProcessInputRepository(self.db_path)

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
