"""Native authoring use cases; renderer- and Rivet-independent application boundary."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from core.native_process import (
    Finding,
    NativeProcessError,
    language_contract,
    readiness,
    validate_definition,
)
from core.tracing import traced
from data_vault.native_process_repository import NativeProcessRepository

from .errors import WorkspaceNotFoundError, WorkspaceServiceError
from .workspace_path import WorkspacePath


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

    @traced("native.contract.read")
    def contract(self, session_id: str) -> dict[str, Any]:
        self.scope(session_id)
        return language_contract()

    @traced("native.examples.read")
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

    @traced("native.document.list")
    def list_documents(
        self, session_id: str, *, limit: int = 25, cursor: str | None = None
    ) -> dict[str, Any]:
        workspace_id, _ = self.scope(session_id)
        return self.repository.list(workspace_id, limit=limit, cursor=cursor)

    @traced("native.document.read")
    def get_document(self, session_id: str, process_id: str) -> dict[str, Any]:
        workspace_id, _ = self.scope(session_id)
        return self.repository.get(workspace_id, process_id)

    @traced("native.document.save")
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

    @traced("native.document.check")
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
        # Exact gateway binding validation is added with the native MCP adapter.
        # Until then no caller-supplied binding can make a tool step runnable.
        findings = list(readiness(document))
        steps = document.as_dict()["steps"]
        valid_targets = {s["id"] for s in steps if s["operation"] == "mcp.call@1"}
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
