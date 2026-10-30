"""Gateway adapter over canonical source/template authoring; never executes work."""

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
from urllib.parse import quote, urlencode

from core.engineering_workflow_templates import EngineeringWorkflowTemplateError
from core.redaction import redact_text
from core.workflow_instructions import WorkflowInstructionSet
from tool_registry.gateway_management import GatewayManagementToolSpec
from tool_registry.gateway_models import GatewayError, GatewayErrorCode

from .workflow_instruction_settings import materialize_new_workflow_instructions
from .workflow_source_execution import (
    WorkflowSourceExecutionError,
    _parse,
    compile_prompt_workflow,
    validate_workspace_authoring_shape,
)
from .workflow_sources import (
    WORKFLOW_SOURCE_MAX_BYTES,
    WorkflowSourceConflictError,
    WorkflowSourceStorageError,
)


_PATH = {
    "type": "string",
    "pattern": r"^workflows/[a-z0-9][a-z0-9-]{0,62}\.workflow\.wflow$",
    "maxLength": 256,
}
_DIGEST = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
_SOURCE = {"type": "string", "minLength": 1, "maxLength": WORKFLOW_SOURCE_MAX_BYTES}
_SOURCE_VIEW = {
    "type": "string",
    "enum": ["process", "complete"],
    "default": "process",
    "description": "process returns editable_source without saved instruction bodies; complete returns the exact stored source including them. Host revision/digest always identify the complete stored file.",
}


def instruction_summary(instructions):
    """Inspection metadata; the complete collection remains in its owning source."""
    return {
        "profile_id": instructions.profile_id,
        "profile_version": instructions.profile_version,
        "digest": instructions.digest,
        "policy": instructions.policy.model_dump(mode="json"),
        "assets": [
            {key: getattr(asset, key) for key in ("id", "role", "version", "body_digest")}
            for asset in instructions.assets
        ],
        "bodies_included": False,
    }


def authoring_source_view(source, view="process"):
    """Project editable process text without changing stored bytes or authority."""
    if view == "complete":
        return {"source_view": "complete", "source": source}
    try:
        header = next((item for item in _parse(source) if item["kind"] == "workflow"), None)
    except WorkflowSourceExecutionError:
        return {"source_view": "complete", "source": source,
                "projection_unavailable": "Source could not be parsed; exact text returned."}
    saved = header["fields"].get("instructions") if header else None
    if saved is None:
        return {"source_view": "process", "editable_source": source,
                "saved_instructions": None}
    instructions = WorkflowInstructionSet.model_validate(saved)
    lines = source.splitlines(keepends=True)
    in_header = False
    projected = []
    for line in lines:
        if line.strip() == f"workflow {header['id']}":
            in_header = True
        elif in_header and line.strip() == "end":
            in_header = False
        if in_header and line.lstrip().startswith("instructions:"):
            continue
        projected.append(line)
    return {
        "source_view": "process",
        "editable_source": "".join(projected),
        "saved_instructions": instruction_summary(instructions),
    }


def workflow_source_authoring_tools(service_factory, gateway_factory):
    """Use the native API's authoring authority within the trusted MCP binding.

    These are local definition edits, like the existing authenticated editor
    APIs. They carry no run, tool-installation, review or dispatch grant. The
    gateway validates/audits calls; source storage still owns confinement/CAS.
    """

    def bound(session):
        service = service_factory()
        workspace = service.lifecycle.get_by_session(
            session.binding_session_id or session.session_id
        )
        if not workspace or str(workspace.get("workspace_id")) != session.workspace_id:
            raise GatewayError(
                GatewayErrorCode.INVALID_BINDING, "Workspace binding changed"
            )
        root = service.ensure_workspace_path_safe(str(workspace["local_path"]))
        if Path(root).resolve() != Path(session.workspace_path).resolve():
            raise GatewayError(
                GatewayErrorCode.INVALID_BINDING, "Workspace path binding changed"
            )
        return service, root

    def document(session, value, source_view="process"):
        fields = asdict(value)
        source = fields.pop("source")
        if source_view == "process":
            fields.pop("layout", None)
        return {
            **fields,
            **authoring_source_view(source, source_view),
            "authoring_view_contract": "wright.workflow-authoring-view/1",
            "layout_included": source_view == "complete",
            "workspace_id": session.workspace_id,
            "metadata_authority": "wright_host",
            "run_started_by_this_call": False,
            "editor_path": "/workspace/"
            + quote(session.workspace_id, safe="")
            + "?"
            + urlencode({"workflow": "canonical", "workflowPath": value.path}),
        }

    async def context(session, arguments):
        from agent_adapters.workflow_instructions import (
            load_default_workflow_instructions,
        )

        service, root = bound(session)
        guide = next(
            item
            for item in load_default_workflow_instructions().assets
            if item.id == "context.workflow-source-authoring"
        )
        defaults = await service.executor.run(
            "workspace.workflow_sources.instruction_defaults",
            lambda: service.workflow_instruction_defaults(root),
            timeout_seconds=30.0,
        )
        include_bodies = arguments.get("include_instruction_bodies", False)
        if not include_bodies:
            defaults = {
                **{key: value for key, value in defaults.items() if key != "instructions"},
                "instruction_summary": instruction_summary(
                    WorkflowInstructionSet.model_validate(defaults["instructions"])
                ),
            }
        return {
            "workspace_id": session.workspace_id,
            "authoring_guide": guide.model_dump(mode="json"),
            "instruction_defaults": defaults,
            "instruction_bodies_included": include_bodies,
        }

    async def templates(session, arguments):
        service, _root = bound(session)
        catalog = service.engineering_workflow_templates
        if arguments.get("version") and not arguments.get("template_id"):
            raise ValueError("A template version requires its exact template_id")
        if arguments.get("template_id"):
            return {
                "template": catalog.detail(
                    arguments["template_id"], arguments.get("version")
                )
            }
        return {
            "catalog_version": catalog.catalog_version,
            "templates": list(catalog.list()),
        }

    async def tool_contracts(session, arguments):
        from .workflow_mcp_execution import WorkflowMcpRuntime

        bound(session)
        gateway = gateway_factory()
        if gateway is None:
            raise GatewayError(
                GatewayErrorCode.CHILD_UNAVAILABLE, "Workflow gateway is unavailable"
            )
        runtime = WorkflowMcpRuntime(
            gateway,
            workspace_id=session.workspace_id,
            session_id=session.binding_session_id or session.session_id,
        )
        try:
            available = runtime.available()
            if arguments.get("server_id"):
                available = [
                    item
                    for item in available
                    if item["server_id"] == arguments["server_id"]
                ]
            include_schemas = arguments.get("include_schemas", bool(arguments.get("server_id")))
            if not include_schemas:
                available = [
                    {key: value for key, value in item.items()
                     if key not in {"input_schema", "output_schema"}}
                    for item in available
                ]
            return {
                "workspace_id": session.workspace_id,
                "tools": available[:64],
                "total": len(available),
                "truncated": len(available) > 64,
                "schemas_included": include_schemas,
            }
        finally:
            await runtime.close()

    async def instantiate(session, arguments):
        service, root = bound(session)
        result = await service.engineering_workflow_templates.instantiate(
            workspace_id=session.workspace_id,
            workspace_dir=root,
            template_id=arguments["template_id"],
            template_version=arguments["version"],
            expected_source_digest=arguments["expected_source_digest"],
            workflow_path=arguments["path"],
            request_id=arguments["request_id"],
            created_by=session.principal_id,
        )
        return {
            **document(session, result.document, arguments.get("source_view", "process")),
            "workflow_id": result.workflow_id,
            "template_origin": {
                "template_id": result.template_id,
                "version": result.template_version,
                "source_digest": result.template_source_digest,
            },
            "readiness": service.engineering_workflow_templates.detail(
                arguments["template_id"], arguments["version"]
            )["readiness"],
        }

    async def read(session, arguments):
        service, root = bound(session)
        return document(
            session, await service.workflow_sources.read(root, arguments["path"]),
            arguments.get("source_view", "process"),
        )

    async def save(session, arguments, *, creating):
        service, root = bound(session)
        source = arguments["source"]
        instruction_preservation = None
        if len(source.encode("utf-8")) > WORKFLOW_SOURCE_MAX_BYTES:
            raise ValueError("Workflow source exceeds its UTF-8 byte limit")
        if creating:
            # Materialize with the same resolver used by the existing create
            # use case, then validate the exact instruction-complete candidate.
            defaults = service.workflow_instruction_defaults(root)
            source = materialize_new_workflow_instructions(
                source, WorkflowInstructionSet.model_validate(defaults["instructions"])
            )
        else:
            previous = await service.workflow_sources.read(root, arguments["path"])
            if (
                previous.storage_revision != arguments["expected_storage_revision"]
                or previous.storage_digest != arguments["expected_storage_digest"]
            ):
                raise WorkflowSourceConflictError(
                    previous.storage_revision, previous.storage_digest
                )
            old_header = next(
                (
                    item
                    for item in _parse(previous.source)
                    if item["kind"] == "workflow"
                ),
                None,
            )
            new_header = next(
                (item for item in _parse(source) if item["kind"] == "workflow"), None
            )
            if old_header is None or new_header is None:
                raise ValueError(
                    "Both saved and proposed source require a workflow header"
                )
            if arguments.get("preserve_saved_instructions") is True:
                if "instructions" in new_header["fields"]:
                    raise ValueError(
                        "preserve_saved_instructions requires source without an "
                        "instructions field. To edit instructions, supply the full "
                        "collection and omit this option. No source was written."
                    )
                if "instructions" not in old_header["fields"]:
                    raise ValueError(
                        "This saved workflow has no instruction collection to "
                        "preserve. Omit preserve_saved_instructions to retain its "
                        "legacy behavior, or explicitly supply instructions in a "
                        "new revision. No source was written."
                    )
                instructions = WorkflowInstructionSet.model_validate(
                    old_header["fields"]["instructions"]
                )
                # Reuse the existing source materializer, with the exact saved
                # collection instead of consulting any current defaults. Storage
                # repeats CAS under its transaction after authoring validation.
                source = materialize_new_workflow_instructions(source, instructions)
                instruction_preservation = {
                    "from_storage_revision": previous.storage_revision,
                    "from_storage_digest": previous.storage_digest,
                    "instructions_digest": instructions.digest,
                }
            elif (
                "instructions" in old_header["fields"]
                and "instructions" not in new_header["fields"]
            ):
                raise ValueError(
                    "Retain the saved instruction collection when updating this "
                    "workflow, or set preserve_saved_instructions=true and omit "
                    "the instructions field to copy it from the exact read "
                    "revision. No source was written."
                )

        if len(source.encode("utf-8")) > WORKFLOW_SOURCE_MAX_BYTES:
            raise ValueError("Workflow source exceeds its UTF-8 byte limit")

        def validate():
            validate_workspace_authoring_shape(source)
            headers = [item for item in _parse(source) if item["kind"] == "workflow"]
            if len(headers) != 1:
                raise ValueError("Source requires exactly one workflow declaration. No source was written.")
            if "instructions" in headers[0]["fields"]:
                WorkflowInstructionSet.model_validate(headers[0]["fields"]["instructions"])
            try:
                compile_prompt_workflow(source)
            except WorkflowSourceExecutionError as error:
                if (
                    creating
                    or arguments.get("save_as_draft") is not True
                    or error.code not in {"WORKFLOW_NOT_READY", "WORKFLOW_DISCONNECTED_PROCESS"}
                ):
                    raise
                # The existing storage owner can retain an unaccepted source
                # edit without advancing its accepted definition revision.
                # Execution still compiles the exact saved source separately.
                return {
                    "code": error.code,
                    "message": redact_text(str(error)),
                    "correction": redact_text(error.correction),
                }
            return None

        execution_diagnostic = await service.executor.run(
            "workspace.workflow_sources.validate_authoring",
            validate,
            timeout_seconds=30.0,
        )
        if creating:
            result = await service.workflow_sources.create(
                root, arguments["path"], source
            )
        else:
            result = await service.workflow_sources.update(
                root,
                arguments["path"],
                expected_storage_revision=arguments["expected_storage_revision"],
                expected_storage_digest=arguments["expected_storage_digest"],
                semantic_change_validated=execution_diagnostic is None,
                source=source,
            )
        return {
            **document(session, result, arguments.get("source_view", "process")),
            "validation_scope": (
                "authoring_shape_only" if execution_diagnostic else "supported_source_shape"
            ),
            "source_status": "saved_draft" if execution_diagnostic else "checked_definition",
            **(
                {"execution_diagnostic": execution_diagnostic}
                if execution_diagnostic is not None else {}
            ),
            **(
                {"instruction_preservation": instruction_preservation}
                if instruction_preservation is not None
                else {}
            ),
        }

    async def task_prompt(session, arguments):
        service, root = bound(session)
        previous = await service.workflow_sources.read(root, arguments["path"])
        task = next((item for item in _parse(previous.source)
                     if item["kind"] == "task" and item["id"] == arguments["task_id"]), None)
        if task is None or not isinstance(task["fields"].get("prompt"), str):
            raise ValueError("The selected task has no editable prompt. No source was written.")
        prompt = task["fields"]["prompt"]
        return {
            "path": previous.path,
            "task_id": arguments["task_id"],
            "prompt": prompt,
            "prompt_digest": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "storage_revision": previous.storage_revision,
            "storage_digest": previous.storage_digest,
            "definition_revision": previous.definition_revision,
            "run_started_by_this_call": False,
        }

    async def update_task_prompt(session, arguments):
        service, root = bound(session)
        previous = await service.workflow_sources.read(root, arguments["path"])
        if (previous.storage_revision != arguments["expected_storage_revision"]
                or previous.storage_digest != arguments["expected_storage_digest"]):
            raise WorkflowSourceConflictError(previous.storage_revision, previous.storage_digest)
        task = next((item for item in _parse(previous.source)
                     if item["kind"] == "task" and item["id"] == arguments["task_id"]), None)
        if task is None or not isinstance(task["fields"].get("prompt"), str):
            raise ValueError("The selected task has no editable prompt. No source was written.")
        old_prompt = task["fields"]["prompt"]
        if hashlib.sha256(old_prompt.encode("utf-8")).hexdigest() != arguments["expected_prompt_digest"]:
            raise ValueError("The task prompt changed. Read it again before editing. No source was written.")
        lines = previous.source.splitlines(keepends=True)
        in_task = False
        replaced = False
        for index, line in enumerate(lines):
            if line.strip() == "task " + arguments["task_id"]:
                in_task = True
            elif in_task and line.strip() == "end":
                break
            elif in_task and line.lstrip().startswith("prompt:"):
                indentation = line[:len(line) - len(line.lstrip())]
                ending = "\r\n" if line.endswith("\r\n") else "\n" if line.endswith("\n") else ""
                lines[index] = indentation + "prompt: " + json.dumps(arguments["prompt"], ensure_ascii=False) + ending
                replaced = True
                break
        if not replaced:
            raise ValueError("Task prompt source field was not found. No source was written.")
        # The existing save path repeats CAS, validates the whole definition and
        # preserves its instruction collection. No run or review is transferred.
        result = await save(session, {
            "path": arguments["path"], "source": "".join(lines),
            "expected_storage_revision": arguments["expected_storage_revision"],
            "expected_storage_digest": arguments["expected_storage_digest"],
            "save_as_draft": arguments.get("save_as_draft", False),
        }, creating=False)
        result.pop("editable_source", None)
        result.pop("source", None)
        result.update(task_id=arguments["task_id"], prompt=arguments["prompt"],
                      prompt_digest=hashlib.sha256(arguments["prompt"].encode("utf-8")).hexdigest(),
                      source_included=False)
        return result

    def guarded(handler):
        async def call(session, arguments):
            try:
                return await handler(session, arguments)
            except WorkflowSourceExecutionError as error:
                raise GatewayError(
                    GatewayErrorCode.INVALID_INPUT,
                    f"{error.code}: {redact_text(str(error))} {redact_text(error.correction)} No source was written.",
                ) from error
            except WorkflowSourceStorageError as error:
                # A storage failure can be uncertain. Re-read its exact source
                # before another mutation; never label it a safe blind replay.
                raise GatewayError(
                    GatewayErrorCode.INVALID_INPUT,
                    f"{error.code}: {redact_text(str(error))} Re-read the saved source before retrying.",
                ) from error
            except (EngineeringWorkflowTemplateError, ValueError) as error:
                raise GatewayError(
                    GatewayErrorCode.INVALID_INPUT, redact_text(str(error))
                ) from error
            except FileNotFoundError as error:
                raise GatewayError(
                    GatewayErrorCode.NOT_FOUND,
                    "Workflow source not found; no file was created",
                ) from error
            except OSError as error:
                raise GatewayError(
                    GatewayErrorCode.CHILD_UNAVAILABLE,
                    "Workflow storage is unavailable; inspect the saved source before retrying",
                ) from error

        return call

    def tool(
        name,
        description,
        properties,
        required,
        handler,
        *,
        read_only=True,
        idempotent=True,
    ):
        return (
            GatewayManagementToolSpec(
                name="wright__workflow_" + name,
                description=description,
                input_schema={
                    "type": "object",
                    "properties": properties,
                    "required": required,
                    "additionalProperties": False,
                },
                output_schema={"type": "object"},
                read_only=read_only,
                idempotent=idempotent,
            ),
            guarded(handler),
        )

    async def create(session, arguments):
        return await save(session, arguments, creating=True)

    async def update(session, arguments):
        return await save(session, arguments, creating=False)

    return [
        tool(
            "tool_contracts",
            "List actual workspace-enabled workflow MCP tool identities and descriptions. Filter one exact server_id to include its schemas, or explicitly set include_schemas. Unfiltered listing omits large schemas by default. No provider startup or tool call; at most64 contracts with an explicit truncation flag.",
            {"server_id": {"type": "string", "minLength": 1, "maxLength": 256},
             "include_schemas": {"type": "boolean", "description": "Default true when filtering server_id, otherwise false. Read actual schemas before binding arguments."}},
            [],
            tool_contracts,
        ),
        tool(
            "authoring_context",
            "Read the canonical authoring guide and instruction-default identities/policy. Set include_instruction_bodies=true to inspect the complete instruction collection. New sources still snapshot the complete defaults. No execution or modification.",
            {"include_instruction_bodies": {"type": "boolean", "default": False}},
            [],
            context,
        ),
        tool(
            "templates",
            "List existing engineering workflow templates, or read one exact template version including source and readiness. A reference template may not be runnable.",
            {
                "template_id": {"type": "string", "minLength": 1, "maxLength": 100},
                "version": {"type": "string", "maxLength": 40},
            },
            [],
            templates,
        ),
        tool(
            "instantiate_template",
            "Create an exact selected template as a canonical workspace workflow, preserving its requirements, lineage and readiness barriers. Does not run or approve it.",
            {
                "template_id": {"type": "string", "minLength": 1, "maxLength": 100},
                "version": {"type": "string", "minLength": 1, "maxLength": 40},
                "expected_source_digest": _DIGEST,
                "path": _PATH,
                "source_view": _SOURCE_VIEW,
                "request_id": {
                    "type": "string",
                    "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$",
                },
            },
            ["template_id", "version", "expected_source_digest", "path", "request_id"],
            instantiate,
            read_only=False,
        ),
        tool(
            "read_source",
            "Read an existing workflow's editable_source, saved-instruction identity and host-owned revision/digest. Default source_view=process omits saved instruction bodies; update that text with preserve_saved_instructions=true. source_view=complete returns exact stored source for full instruction inspection/editing. Read never creates a file.",
            {"path": _PATH, "source_view": _SOURCE_VIEW},
            ["path"],
            read,
        ),
        tool(
            "create_source",
            "Exclusively create a new canonical workflow after backend authoring/compiler checks and instruction snapshotting. Does not run, qualify or approve it. Read authoring_context first.",
            {"path": _PATH, "source": _SOURCE, "source_view": _SOURCE_VIEW},
            ["path", "source"],
            create,
            read_only=False,
            idempotent=False,
        ),
        tool(
            "read_task_prompt",
            "Read one task prompt with exact source revision/digest and prompt digest, without returning the whole workflow. Use before a bounded prompt edit.",
            {"path": _PATH, "task_id": {"type": "string", "minLength": 1, "maxLength": 256}},
            ["path", "task_id"], task_prompt,
        ),
        tool(
            "update_task_prompt",
            "Replace only one task prompt using the exact source and prompt digests from read_task_prompt. Reuses checked source save, preserves all other fields and saved instructions, and returns a compact saved receipt. Does not run work or transfer approval. Inspect after an uncertain save before retrying.",
            {"path": _PATH, "task_id": {"type": "string", "minLength": 1, "maxLength": 256},
             "prompt": {"type": "string", "minLength": 1, "maxLength": 262144},
             "expected_storage_revision": {"type": "integer", "minimum": 1},
             "expected_storage_digest": _DIGEST, "expected_prompt_digest": _DIGEST,
             "save_as_draft": {"type": "boolean", "default": False}},
            ["path", "task_id", "prompt", "expected_storage_revision", "expected_storage_digest", "expected_prompt_digest"],
            update_task_prompt, read_only=False, idempotent=False,
        ),
        tool(
            "update_source",
            "Save a checked canonical workflow revision against the exact previously read revision/digest. Set preserve_saved_instructions=true and omit source instructions to retain the exact saved collection. Explicit instruction edits require the complete collection and preservation omitted/false. Set save_as_draft=true to retain an existing unready draft with its execution diagnostic; that draft advances storage only, not the accepted definition revision. Shape, instructions and CAS are still checked. No execution or review authority.",
            {
                "path": _PATH,
                "source": _SOURCE,
                "source_view": _SOURCE_VIEW,
                "expected_storage_revision": {"type": "integer", "minimum": 1},
                "expected_storage_digest": _DIGEST,
                "preserve_saved_instructions": {
                    "type": "boolean",
                    "default": False,
                    "description": "Copy the instruction collection and typed policy from the exact saved revision when source omits instructions. Never uses current defaults; rejects a supplied instructions field or a saved source without instructions.",
                },
                "save_as_draft": {
                    "type": "boolean",
                    "default": False,
                    "description": "Explicitly allow an existing source edit to remain an unaccepted draft when execution compilation is not ready. Returns saved_draft and the exact execution diagnostic; accepted definition revision does not advance. Source syntax/shape and instruction collections are still checked; run/readiness/review gates are unchanged. A compilable source still uses the normal checked save.",
                },
            },
            ["path", "source", "expected_storage_revision", "expected_storage_digest"],
            update,
            read_only=False,
            idempotent=False,
        ),
    ]
