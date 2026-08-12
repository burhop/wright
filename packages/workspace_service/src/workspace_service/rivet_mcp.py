"""Workspace-confined Rivet workflow MCP shipped and launched by Wright."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
from dataclasses import replace
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable, Mapping

import mcp.types as types
import structlog
from data_vault import WorkflowReviewRepository, WorkflowRunRepository
from mcp.server.lowlevel import NotificationOptions, Server
from mcp.server.stdio import stdio_server

from core.workflows import WorkflowPersistenceError
from core.workflow_runs import WorkflowRunnerError, WorkflowRunState

from .rivet_validation import (
    WorkflowIdentityMismatch,
    WorkflowValidationResult,
    validate_rivet_project,
)
from .workflow_catalog import WorkflowTemplateCatalog, WorkflowTemplateError
from .workflow_runner import RunnerSettings, WorkspaceWorkflowRunner
from .workflows import WorkspaceWorkflowStore


_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_SAFE_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")
_MAX_PROJECT_BYTES = 4 * 1024 * 1024
_MAX_INPUT_BYTES = 1024 * 1024
logger = structlog.get_logger(__name__)


class RivetMcpError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class RivetMcpBinding:
    workspace_path: str
    database_path: str
    workspace_id: str
    session_id: str

    def __post_init__(self) -> None:
        workspace = Path(self.workspace_path)
        database = Path(self.database_path)
        if not workspace.is_absolute() or not database.is_absolute():
            raise ValueError("Rivet MCP paths must be absolute")
        canonical = workspace.resolve(strict=True)
        if not canonical.is_dir() or workspace.is_symlink():
            raise ValueError("Rivet MCP workspace must be a canonical directory")
        if not _SAFE_ID.fullmatch(self.workspace_id) or not _SAFE_ID.fullmatch(
            self.session_id
        ):
            raise ValueError("Rivet MCP trusted identity is invalid")
        object.__setattr__(self, "workspace_path", str(canonical))
        object.__setattr__(self, "database_path", str(database.resolve()))

    @classmethod
    def from_environment(
        cls, env: Mapping[str, str] | None = None
    ) -> "RivetMcpBinding":
        source = os.environ if env is None else env
        values = tuple(
            (source.get(name) or "").strip()
            for name in (
                "WRIGHT_RIVET_MCP_WORKSPACE",
                "WRIGHT_RIVET_MCP_DATABASE",
                "WRIGHT_RIVET_MCP_WORKSPACE_ID",
                "WRIGHT_RIVET_MCP_SESSION_ID",
            )
        )
        if not all(values):
            raise ValueError("Rivet MCP trusted launch binding is incomplete")
        return cls(*values)


def _identity(document) -> dict[str, Any]:
    return {
        "slug": document.slug,
        "workflowId": document.workflow_id,
        "revision": document.revision,
        "digest": document.digest,
    }


def _port(port) -> dict[str, Any]:
    return {"id": port.id, "dataType": port.data_type, "required": port.required}


def _graph(graph) -> dict[str, Any]:
    return {
        "id": graph.id,
        "name": graph.name,
        "inputs": [_port(value) for value in graph.inputs],
        "outputs": [_port(value) for value in graph.outputs],
    }


def _validation(result: WorkflowValidationResult) -> dict[str, Any]:
    def issue(value) -> dict[str, Any]:
        return {
            "code": value.code,
            "message": value.message,
            **({"graphId": value.graph_id} if value.graph_id else {}),
            **({"nodeId": value.node_id} if value.node_id else {}),
        }

    return {
        "workflowId": result.workflow_id,
        "revision": result.revision,
        "digest": result.digest,
        "valid": result.valid,
        "mainGraph": _graph(result.main_graph) if result.main_graph else None,
        "graphs": [_graph(value) for value in result.graphs],
        "requirements": list(result.requirements),
        "errors": [issue(value) for value in result.errors],
        "warnings": [issue(value) for value in result.warnings],
    }


ProgressHandler = Callable[[dict[str, Any]], Awaitable[None] | None]
RunHandler = Callable[
    [dict[str, Any], Any, WorkflowValidationResult, ProgressHandler | None],
    Awaitable[dict[str, Any]],
]


class RivetWorkflowMcpService:
    def __init__(
        self,
        binding: RivetMcpBinding,
        *,
        catalog: WorkflowTemplateCatalog | None = None,
        run_handler: RunHandler | None = None,
    ) -> None:
        self.binding = binding
        self.store = WorkspaceWorkflowStore(binding.workspace_path)
        self.catalog = catalog or WorkflowTemplateCatalog()
        self.reviews = WorkflowReviewRepository(binding.database_path)
        self.run_handler = run_handler

    @staticmethod
    def _slug(arguments: Mapping[str, Any]) -> str:
        slug = arguments.get("slug")
        if not isinstance(slug, str) or not _SAFE_SLUG.fullmatch(slug):
            raise RivetMcpError(
                "RIVET_WORKFLOW_INVALID",
                "Workflow slug must use 1-63 lowercase letters, digits, or hyphens.",
            )
        return slug

    def _read(self, slug: str):
        try:
            return self.store.read(slug)
        except FileNotFoundError as error:
            raise RivetMcpError(
                "RIVET_WORKFLOW_NOT_FOUND", "Workflow was not found."
            ) from error
        except (
            WorkflowPersistenceError,
            OSError,
            ValueError,
            json.JSONDecodeError,
        ) as error:
            raise RivetMcpError(
                "RIVET_WORKFLOW_INVALID", "Workflow storage is invalid or unsafe."
            ) from error

    def _validate(
        self, document, arguments: Mapping[str, Any]
    ) -> WorkflowValidationResult:
        expected_revision = arguments.get("expectedRevision")
        expected_digest = arguments.get("expectedDigest")
        if expected_revision is not None and (
            not isinstance(expected_revision, int) or expected_revision < 1
        ):
            raise RivetMcpError(
                "RIVET_WORKFLOW_INVALID", "Expected revision is invalid."
            )
        if expected_digest is not None and (
            not isinstance(expected_digest, str)
            or not re.fullmatch(r"[a-f0-9]{64}", expected_digest)
        ):
            raise RivetMcpError("RIVET_WORKFLOW_INVALID", "Expected digest is invalid.")
        selected_graph = arguments.get("graph")
        if selected_graph is not None and (
            not isinstance(selected_graph, str) or len(selected_graph) > 256
        ):
            raise RivetMcpError("RIVET_WORKFLOW_INVALID", "Selected graph is invalid.")
        try:
            return validate_rivet_project(
                document.project,
                workflow_id=document.workflow_id,
                revision=document.revision,
                digest=document.digest,
                selected_graph=selected_graph,
                expected_revision=expected_revision,
                expected_digest=expected_digest,
            )
        except WorkflowIdentityMismatch as error:
            raise RivetMcpError(
                "RIVET_WORKFLOW_REVISION_CONFLICT",
                "Workflow revision or digest changed; inspect the current identity.",
            ) from error

    async def list_templates(self, _arguments: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "templates": [
                {
                    "id": template.template_id,
                    "title": template.title,
                    "description": template.description,
                    "kind": template.kind,
                    "requirements": list(template.requirements),
                }
                for template in self.catalog.list()
            ]
        }

    async def list_workflows(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        limit = arguments.get("limit", 50)
        if not isinstance(limit, int) or not 1 <= limit <= 100:
            raise RivetMcpError(
                "RIVET_WORKFLOW_INVALID", "Workflow list limit must be 1-100."
            )
        workflows = []
        for slug in sorted(self.store.list_slugs())[:limit]:
            document = self._read(slug)
            review = self.reviews.get(self.binding.workspace_id, document.workflow_id)
            workflows.append(
                {
                    **_identity(document),
                    "reviewState": (
                        review.state
                        if review and review.revision == document.revision
                        else None
                    ),
                    "lastRunState": None,
                }
            )
        return {"workflows": workflows}

    async def inspect_workflow(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        document = self._read(self._slug(arguments))
        return {
            "workflow": _identity(document),
            "validation": _validation(self._validate(document, arguments)),
        }

    async def create_workflow(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        slug = self._slug(arguments)
        template_id = arguments.get("templateId")
        project = arguments.get("project")
        if (template_id is None) == (project is None):
            raise RivetMcpError(
                "RIVET_WORKFLOW_INVALID",
                "Exactly one of templateId or project is required.",
            )
        if template_id is not None:
            if not isinstance(template_id, str):
                raise RivetMcpError("RIVET_WORKFLOW_INVALID", "Template ID is invalid.")
            try:
                project = self.catalog.instantiate(template_id)
            except WorkflowTemplateError as error:
                raise RivetMcpError(
                    "RIVET_WORKFLOW_INVALID",
                    "Workflow template was not found or is invalid.",
                ) from error
        if (
            not isinstance(project, str)
            or len(project.encode("utf-8")) > _MAX_PROJECT_BYTES
        ):
            raise RivetMcpError(
                "RIVET_WORKFLOW_INVALID", "Workflow project is invalid or too large."
            )
        provisional_digest = hashlib.sha256(project.encode("utf-8")).hexdigest()
        provisional = validate_rivet_project(
            project,
            workflow_id="pending",
            revision=1,
            digest=provisional_digest,
        )
        if not provisional.valid:
            raise RivetMcpError(
                "RIVET_WORKFLOW_INVALID",
                "Workflow project did not pass Rivet validation.",
            )
        try:
            document = self.store.create(slug, project)
        except WorkflowPersistenceError as error:
            code = (
                "RIVET_WORKFLOW_EXISTS"
                if "already exists" in str(error)
                else "RIVET_WORKFLOW_INVALID"
            )
            raise RivetMcpError(
                code, "Workflow could not be created in the bound workspace."
            ) from error
        validation = self._validate(document, {})
        return {"workflow": _identity(document), "validation": _validation(validation)}

    async def validate_workflow(self, arguments: Mapping[str, Any]) -> dict[str, Any]:
        document = self._read(self._slug(arguments))
        return _validation(self._validate(document, arguments))

    async def run_workflow(
        self,
        arguments: Mapping[str, Any],
        progress_callback: ProgressHandler | None = None,
    ) -> dict[str, Any]:
        document = self._read(self._slug(arguments))
        if "expectedRevision" not in arguments or "expectedDigest" not in arguments:
            raise RivetMcpError(
                "RIVET_WORKFLOW_REVISION_CONFLICT",
                "Exact workflow revision and digest are required for execution.",
            )
        validation = self._validate(document, arguments)
        if not validation.valid:
            raise RivetMcpError("RIVET_WORKFLOW_INVALID", "Workflow is not executable.")
        encoded_inputs = json.dumps(
            {
                "inputs": arguments.get("inputs", {}),
                "context": arguments.get("context", {}),
            },
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
        if len(encoded_inputs) > _MAX_INPUT_BYTES:
            raise RivetMcpError(
                "RIVET_WORKFLOW_INVALID", "Workflow inputs exceed the limit."
            )
        if not self.reviews.approved(
            self.binding.workspace_id, document.workflow_id, document.revision
        ):
            raise RivetMcpError(
                "RIVET_WORKFLOW_REVIEW_REQUIRED",
                "The current workflow revision requires durable Wright approval before execution.",
            )
        if self.run_handler is None:
            raise RivetMcpError(
                "RIVET_RUNNER_UNAVAILABLE", "The Rivet runtime is unavailable."
            )
        return await self.run_handler(
            dict(arguments), document, validation, progress_callback
        )

    async def dispatch(
        self,
        name: str,
        arguments: Mapping[str, Any],
        progress_callback: ProgressHandler | None = None,
    ) -> dict[str, Any]:
        if name == "run_workflow":
            return await self.run_workflow(arguments, progress_callback)
        handler = {
            "list_templates": self.list_templates,
            "list_workflows": self.list_workflows,
            "inspect_workflow": self.inspect_workflow,
            "create_workflow": self.create_workflow,
            "validate_workflow": self.validate_workflow,
        }.get(name)
        if handler is None:
            raise RivetMcpError(
                "RIVET_TOOL_NOT_FOUND", "Rivet workflow tool was not found."
            )
        return await handler(arguments)


def _tool(
    name: str,
    description: str,
    properties: dict[str, Any],
    *,
    required: tuple[str, ...] = (),
    read_only: bool,
    destructive: bool,
    idempotent: bool,
) -> types.Tool:
    return types.Tool(
        name=name,
        description=description,
        inputSchema={
            "type": "object",
            "properties": properties,
            "required": list(required),
            "additionalProperties": False,
        },
        annotations=types.ToolAnnotations(
            readOnlyHint=read_only,
            destructiveHint=destructive,
            idempotentHint=idempotent,
            openWorldHint=False,
        ),
    )


_SLUG_SCHEMA = {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{0,62}$"}
_DIGEST_SCHEMA = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
_TOOLS = (
    _tool(
        "list_templates",
        "List reviewed Rivet workflow templates.",
        {},
        read_only=True,
        destructive=False,
        idempotent=True,
    ),
    _tool(
        "list_workflows",
        "List workflow identities in the bound workspace without project content.",
        {"limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50}},
        read_only=True,
        destructive=False,
        idempotent=True,
    ),
    _tool(
        "inspect_workflow",
        "Inspect one workflow identity, graphs, ports, and requirements.",
        {"slug": _SLUG_SCHEMA},
        required=("slug",),
        read_only=True,
        destructive=False,
        idempotent=True,
    ),
    _tool(
        "create_workflow",
        "Create one new workflow from a reviewed template or bounded Rivet project.",
        {
            "slug": _SLUG_SCHEMA,
            "templateId": {"type": "string", "maxLength": 63},
            "project": {"type": "string", "maxLength": _MAX_PROJECT_BYTES},
        },
        required=("slug",),
        read_only=False,
        destructive=True,
        idempotent=False,
    ),
    _tool(
        "validate_workflow",
        "Validate a workflow and optionally verify its exact revision and digest.",
        {
            "slug": _SLUG_SCHEMA,
            "expectedRevision": {"type": "integer", "minimum": 1},
            "expectedDigest": _DIGEST_SCHEMA,
            "graph": {"type": "string", "maxLength": 256},
        },
        required=("slug",),
        read_only=True,
        destructive=False,
        idempotent=True,
    ),
    _tool(
        "run_workflow",
        "Run an exact, durably reviewed workflow revision through Wright's Rivet runtime.",
        {
            "slug": _SLUG_SCHEMA,
            "expectedRevision": {"type": "integer", "minimum": 1},
            "expectedDigest": _DIGEST_SCHEMA,
            "graph": {"type": "string", "maxLength": 256},
            "inputs": {"type": "object"},
            "context": {"type": "object"},
            "timeoutSeconds": {"type": "number", "minimum": 1, "maximum": 300},
        },
        required=("slug", "expectedRevision", "expectedDigest"),
        read_only=False,
        destructive=True,
        idempotent=False,
    ),
)


def create_rivet_mcp_server(service: RivetWorkflowMcpService) -> Server:
    server = Server(
        "rivet-workflows",
        version="0.1.0",
        instructions=(
            "Manage Rivet workflows only in the bound Wright workspace. Creation and execution "
            "remain subject to Wright validation, durable review, and gateway approval."
        ),
    )

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return list(_TOOLS)

    @server.call_tool(validate_input=True)
    async def call_tool(name: str, arguments: dict[str, Any]) -> types.CallToolResult:
        request_context = server.request_context
        progress_token = (
            request_context.meta.progressToken
            if request_context.meta is not None
            else None
        )

        async def relay_progress(update: dict[str, Any]) -> None:
            if progress_token is None:
                return
            await request_context.session.send_progress_notification(
                progress_token,
                float(update.get("sequence", 0)),
                None,
                str(
                    update.get("phase")
                    or update.get("state")
                    or "Running Rivet workflow"
                ),
                related_request_id=str(request_context.request_id),
            )

        try:
            result = await service.dispatch(
                name,
                arguments,
                relay_progress if progress_token is not None else None,
            )
        except RivetMcpError as error:
            structured = {"error": {"code": error.code, "message": str(error)}}
            return types.CallToolResult(
                content=[types.TextContent(type="text", text=str(error))],
                structuredContent=structured,
                isError=True,
            )
        return types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=json.dumps(result, separators=(",", ":"), ensure_ascii=False),
                )
            ],
            structuredContent=result,
            isError=False,
        )

    return server


def initialization_options(server: Server):
    return server.create_initialization_options(
        notification_options=NotificationOptions(),
        experimental_capabilities={},
    )


async def serve_stdio(service: RivetWorkflowMcpService) -> None:
    server = create_rivet_mcp_server(service)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, initialization_options(server))


def create_bound_rivet_service(binding: RivetMcpBinding) -> RivetWorkflowMcpService:
    if os.name == "nt":
        from .surfaces.process_windows import WindowsProcessAdapter

        adapter = WindowsProcessAdapter()
    else:
        from .surfaces.process_posix import PosixProcessAdapter

        adapter = PosixProcessAdapter()
    from .rivet_runtime_host import RivetRuntimeHost
    from .surfaces.process_supervisor import ProcessSupervisor

    settings = replace(
        RunnerSettings.from_env(), enabled=True, real_execution_enabled=True
    )
    supervisor = ProcessSupervisor(adapter=adapter)
    repository = WorkflowRunRepository(
        binding.database_path,
        maximum_output_bytes=settings.captured_output_bytes,
        maximum_event_bytes=settings.maximum_event_bytes,
    )
    runner = WorkspaceWorkflowRunner(
        supervisor=supervisor,
        settings=settings,
        runtime_host=RivetRuntimeHost(supervisor=supervisor, settings=settings),
        run_repository=repository,
    )

    async def run_handler(
        arguments: dict[str, Any],
        document,
        validation: WorkflowValidationResult,
        progress_callback: ProgressHandler | None,
    ) -> dict[str, Any]:
        del validation
        try:
            run = await runner.start(
                workspace_id=binding.workspace_id,
                session_id=binding.session_id,
                workspace_dir=binding.workspace_path,
                slug=document.slug,
                expected_revision=int(arguments["expectedRevision"]),
                expected_digest=str(arguments["expectedDigest"]),
                graph=arguments.get("graph"),
                inputs=arguments.get("inputs") or {},
                context=arguments.get("context") or {},
                timeout_seconds=float(
                    arguments.get("timeoutSeconds", settings.run_timeout_seconds)
                ),
                progress_callback=progress_callback,
            )
            timeout = min(
                float(arguments.get("timeoutSeconds", settings.run_timeout_seconds)),
                settings.run_timeout_seconds,
            )
            deadline = asyncio.get_running_loop().time() + timeout + 1
            while run.state in {
                WorkflowRunState.QUEUED,
                WorkflowRunState.RUNNING,
                WorkflowRunState.CANCELLING,
            }:
                if asyncio.get_running_loop().time() >= deadline:
                    run = await runner.cancel(run.run_id, generation=run.generation)
                    break
                await asyncio.sleep(0.02)
                run = runner.get(run.run_id)
        except asyncio.CancelledError:
            if "run" in locals():
                await runner.cancel(run.run_id, generation=run.generation)
            raise
        except WorkflowRunnerError as error:
            raise RivetMcpError(error.code, str(error)) from error
        record = runner.result(run.run_id)
        result = {
            "runId": run.run_id,
            "state": run.state.value,
            "workflow": _identity(document),
            "graph": record.graph if record is not None else arguments.get("graph"),
            "outputs": (
                record.output_summary.get("outputs", {})
                if record is not None and record.output_summary
                else {}
            ),
            "durationMs": (
                record.output_summary.get("durationMs")
                if record is not None and record.output_summary
                else None
            ),
            "reason": run.reason,
        }
        logger.info(
            "rivet_mcp_run_completed",
            run_id=run.run_id,
            workflow_id=document.workflow_id,
            revision=document.revision,
            graph=result["graph"],
            state=run.state.value,
            duration_ms=result["durationMs"],
        )
        return result

    return RivetWorkflowMcpService(binding, run_handler=run_handler)


def main() -> None:
    binding = RivetMcpBinding.from_environment()
    asyncio.run(serve_stdio(create_bound_rivet_service(binding)))


if __name__ == "__main__":
    main()
