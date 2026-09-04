"""Native authoring use cases; renderer- and Rivet-independent application boundary."""

from __future__ import annotations

import asyncio
import os
import threading
from collections.abc import Callable, Mapping
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any

from core.native_process import (
    Finding,
    NativeProcessError,
    language_contract,
    readiness,
    validate_definition,
)
from core.native_tracing import traced_native
from core.logging import get_logger
from data_vault.native_process_artifacts import NativeArtifactStore
from data_vault.native_process_repository import NativeProcessRepository

from .errors import WorkspaceNotFoundError, WorkspaceServiceError
from .workspace_path import WorkspacePath

if TYPE_CHECKING:
    from .native_process_mcp import NativeMcpAdapter
    from .native_process_runtime import NativeRuntime

logger = get_logger(__name__)


class NativeServiceError(ValueError):
    def __init__(
        self,
        code: str,
        message: str,
        recovery: str,
        *,
        findings: tuple[Finding, ...] = (),
    ):
        super().__init__(message)
        self.code = code
        self.recovery = recovery
        self.findings = findings


class NativeProcessService:
    def __init__(
        self,
        repository: NativeProcessRepository,
        workspace_resolver: Callable[[str], Mapping[str, Any]],
        examples_root: Path,
    ):
        self.repository = repository
        self.workspace_resolver = workspace_resolver
        self.examples_root = examples_root
        self.runtime: NativeRuntime | None = None
        self.mcp: NativeMcpAdapter | None = None
        self._startup_guard = threading.Lock()
        self._started = False
        self._closing = False
        self.reconciliation: dict[str, Any] = {"removed": 0, "residue": []}

    def configure_execution(
        self, runtime: NativeRuntime, mcp: NativeMcpAdapter
    ) -> None:
        self.runtime, self.mcp = runtime, mcp

    def _execution(self) -> NativeRuntime:
        if self.runtime is None or self._closing:
            raise NativeServiceError(
                "NATIVE_RUNTIME_BUSY",
                "Native execution is unavailable.",
                "Reconnect to the running local Wright service.",
            )
        return self.runtime

    def _startup(self) -> None:
        # No run can enqueue until this owner-only sweep completes. Unavailable
        # workspace capabilities are retained and reported, never guessed.
        with self._startup_guard:
            runtime = self._execution()
            runtime.ensure_owner()
            if self._started:
                return
            removed, residue, visited = 0, [], set()
            for recorded in self.repository.artifact_scopes():
                identity = recorded["workspace_id"]
                if identity in visited:
                    continue
                try:
                    current, paths = self.scope(recorded["session_id"])
                    if current != identity:
                        raise ValueError("Workspace binding changed")
                    result = NativeArtifactStore(paths).reconcile(
                        self.repository.indexed_artifact_keys(identity)
                    )
                    removed += len(result["removed"])
                    residue.extend(
                        {"workspace_id": identity, "storage_key": key}
                        for key in result["residue"][: 100 - len(residue)]
                    )
                    visited.add(identity)
                except (NativeServiceError, OSError, ValueError):
                    if len(residue) < 100:
                        residue.append(
                            {
                                "workspace_id": identity,
                                "code": "ARTIFACT_SCOPE_UNAVAILABLE",
                            }
                        )
            self.reconciliation = {"removed": removed, "residue": residue}
            self._started = True
            logger.info(
                "native_artifact_reconciliation",
                removed=removed,
                residue_count=len(residue),
            )

    async def startup(self) -> dict[str, Any]:
        await asyncio.to_thread(self._startup)
        return self.reconciliation

    async def close(self) -> None:
        self._closing = True
        try:
            if self.runtime is not None:
                await self.runtime.close()
        finally:
            if self.mcp is not None:
                await self.mcp.close()

    def scope(self, session_id: str) -> tuple[str, WorkspacePath]:
        if not isinstance(session_id, str) or not 1 <= len(session_id) <= 200:
            raise NativeServiceError(
                "NATIVE_INVALID",
                "Session identity is invalid.",
                "Select an existing workspace.",
            )
        try:
            workspace = self.workspace_resolver(session_id)
            registered = Path(str(workspace["local_path"]))
            resolved = registered.resolve(strict=True)
            if (
                not registered.is_absolute()
                or not resolved.is_dir()
                or os.path.normcase(str(registered.absolute()))
                != os.path.normcase(str(resolved))
            ):
                raise ValueError("Workspace is not a canonical registered directory")
            return str(workspace["workspace_id"]), WorkspacePath(resolved)
        except WorkspaceNotFoundError as exc:
            raise NativeServiceError(
                "NATIVE_NOT_FOUND",
                "Workspace was not found.",
                "Select an existing workspace.",
            ) from exc
        except (WorkspaceServiceError, OSError, ValueError, KeyError) as exc:
            raise NativeServiceError(
                "NATIVE_DENIED",
                "Workspace access is unavailable.",
                "Select an available managed workspace.",
            ) from exc

    @traced_native("native.contract.read")
    def contract(self, session_id: str) -> dict[str, Any]:
        self.scope(session_id)
        return language_contract()

    @traced_native("native.examples.read")
    def examples(self) -> dict[str, Any]:
        examples = []
        for name in ("concept-brief", "mass-check", "package-review"):
            path = self.examples_root / f"{name}.json"
            with path.open("rb") as source:
                document = validate_definition(source.read(1024 * 1024 + 1))
            definition = document.as_dict()
            examples.append(
                {
                    "id": document.process_id,
                    "title": definition["title"],
                    "definition": definition,
                    "presentation": {},
                }
            )
        return {"examples": examples}

    @traced_native("native.document.list")
    def list_documents(
        self, session_id: str, *, limit: int = 25, cursor: str | None = None
    ) -> dict[str, Any]:
        workspace_id, _ = self.scope(session_id)
        return self.repository.list(workspace_id, limit=limit, cursor=cursor)

    @traced_native("native.document.read")
    def get_document(self, session_id: str, process_id: str) -> dict[str, Any]:
        workspace_id, _ = self.scope(session_id)
        return self.repository.get(workspace_id, process_id)

    @traced_native("native.document.save")
    def save_document(
        self,
        session_id: str,
        definition: Mapping[str, Any],
        presentation: object,
        *,
        request_id: str,
        expected_token: str | None,
        trace_id: str,
        process_id: str | None = None,
    ) -> dict[str, Any]:
        workspace_id, _ = self.scope(session_id)
        document = validate_definition(definition)
        if process_id is not None and document.process_id != process_id:
            raise NativeServiceError(
                "NATIVE_INVALID",
                "Process identity does not match the requested document.",
                "Save using the matching process identity.",
            )
        return self.repository.save(
            workspace_id,
            document,
            presentation,
            request_id=request_id,
            expected_token=expected_token,
            trace_id=trace_id,
        )

    @traced_native("native.document.check")
    def check(
        self,
        session_id: str,
        definition: Mapping[str, Any],
        bindings: Mapping[str, Any],
    ) -> dict[str, Any]:
        _, paths = self.scope(session_id)
        try:
            document = validate_definition(definition)
        except NativeProcessError as exc:
            return {
                "structurally_valid": False,
                "ready": False,
                "findings": [f.as_dict() for f in exc.findings],
            }
        findings = []
        bound = set()
        steps = document.as_dict()["steps"]
        valid_targets = {s["id"] for s in steps if s["operation"] == "mcp.call@1"}
        for identity in sorted(set(bindings) & valid_targets):
            if self.mcp is None:
                continue
            try:
                self.mcp.preflight(session_id, bindings[identity])
                bound.add(identity)
            except NativeServiceError as error:
                findings.extend(
                    replace(finding, step_id=identity)
                    for finding in (
                        error.findings
                        or (Finding(error.code, str(error), error.recovery),)
                    )
                )
        findings.extend(readiness(document, bound_step_ids=frozenset(bound)))
        if set(bindings) - valid_targets:
            findings.append(
                Finding(
                    "BINDING_TARGET",
                    "Binding refers to a step that is not an MCP operation.",
                    "Remove the unmatched binding.",
                )
            )
        for step in steps:
            if step["operation"] != "artifact.input@1" or "path" not in step["config"]:
                continue
            try:
                path = paths.resolve(step["config"]["path"], must_exist=True)
                if not path.is_file() or path.stat().st_size > 10 * 1024 * 1024:
                    raise ValueError("Artifact is not a bounded regular file")
            except (OSError, ValueError):
                findings.append(
                    Finding(
                        "ARTIFACT_UNAVAILABLE",
                        "Artifact input is not available within this workspace.",
                        "Select an existing workspace file of at most 10 MiB.",
                        step["id"],
                    )
                )
        return {
            "structurally_valid": True,
            "ready": not findings,
            "findings": [f.as_dict() for f in findings],
        }

    @traced_native("native.bindings.read")
    def bindings(self, session_id: str) -> dict[str, Any]:
        self.scope(session_id)
        if self.mcp is None:
            raise NativeServiceError(
                "NATIVE_NOT_READY",
                "Tool discovery is unavailable.",
                "Reconnect to the local runtime service.",
            )
        return self.mcp.discover(session_id)

    def _prepare_run(self, session_id: str, process_id: str, arguments: dict[str, Any]):
        workspace_id, _ = self.scope(session_id)
        self._startup()
        replay = self.repository.replay_run(
            workspace_id, process_id, session_id=session_id, **arguments
        )
        if replay is not None:
            return workspace_id, replay
        saved = self.repository.get(workspace_id, process_id)
        if saved["token"] != arguments["expected_token"]:
            raise NativeServiceError(
                "NATIVE_CONFLICT",
                "The saved process changed before run submission.",
                "Reopen the current process before submitting a new run.",
            )
        checked = self.check(session_id, saved["definition"], arguments["bindings"])
        if not checked["ready"]:
            findings = tuple(Finding(**item) for item in checked["findings"])
            codes = {finding.code for finding in findings}
            code = (
                "NATIVE_BINDING_CHANGED"
                if "MCP_BINDING_CHANGED" in codes
                else "NATIVE_DENIED"
                if "MCP_DENIED" in codes
                else "NATIVE_NOT_READY"
            )
            raise NativeServiceError(
                code,
                "The saved process is not ready for execution.",
                "Resolve the readiness findings and submit a new run.",
                findings=findings,
            )
        return workspace_id, None

    @traced_native("native.run.submit")
    async def start_run(
        self,
        session_id: str,
        process_id: str,
        *,
        expected_token: str,
        request_id: str,
        bindings: dict[str, Any],
        timeout_seconds: int,
        derived_from_run_id: str | None,
        actor: str,
        trace_id: str,
    ) -> dict[str, Any]:
        arguments = dict(
            expected_token=expected_token,
            request_id=request_id,
            bindings=bindings,
            timeout_seconds=timeout_seconds,
            derived_from_run_id=derived_from_run_id,
            actor=actor,
            trace_id=trace_id,
        )
        workspace_id, replay = await asyncio.to_thread(
            self._prepare_run, session_id, process_id, arguments
        )
        current_workspace, _ = self.scope(session_id)
        if current_workspace != workspace_id:
            raise NativeServiceError(
                "NATIVE_DENIED",
                "Workspace binding changed before run submission.",
                "Select the original workspace and submit a new run.",
            )
        runtime = self._execution()
        # Commit and enqueue occur without an await between them. Disconnecting
        # the HTTP request cannot strand a newly committed queued run.
        result = replay or self.repository.create_run(
            workspace_id, process_id, session_id=session_id, **arguments
        )
        runtime.enqueue(workspace_id, session_id, result["run_id"])
        return result

    @traced_native("native.run.history")
    def run_history(
        self,
        session_id: str,
        process_id: str,
        *,
        limit: int = 25,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        workspace_id, _ = self.scope(session_id)
        return self.repository.history(
            workspace_id, process_id, limit=limit, cursor=cursor
        )

    @traced_native("native.run.inspect")
    def inspect_run(self, session_id: str, run_id: str) -> dict[str, Any]:
        workspace_id, _ = self.scope(session_id)
        return self.repository.inspect(workspace_id, run_id)

    @traced_native("native.run.events")
    def run_events(
        self, session_id: str, run_id: str, *, after_sequence: int = 0, limit: int = 200
    ) -> dict[str, Any]:
        workspace_id, _ = self.scope(session_id)
        return self.repository.events(
            workspace_id, run_id, after_sequence=after_sequence, limit=limit
        )

    @traced_native("native.run.cancel")
    async def cancel_run(self, session_id: str, run_id: str) -> dict[str, Any]:
        workspace_id, _ = self.scope(session_id)
        await asyncio.to_thread(self._startup)
        return await self._execution().cancel(workspace_id, run_id)

    @traced_native("native.run.artifact")
    def run_artifact(
        self, session_id: str, run_id: str, artifact_id: str
    ) -> tuple[dict[str, Any], bytes]:
        workspace_id, paths = self.scope(session_id)
        record = self.repository.artifact(workspace_id, run_id, artifact_id)
        try:
            return record, NativeArtifactStore(paths).read(record)
        except (OSError, ValueError) as error:
            from data_vault.native_process_repository import NativeRepositoryError

            if isinstance(error, NativeRepositoryError):
                raise
            raise NativeServiceError(
                "NATIVE_ARTIFACT_INVALID",
                "Recorded artifact bytes are unavailable.",
                "Inspect the retained run and regenerate the artifact in a linked run.",
            ) from error
