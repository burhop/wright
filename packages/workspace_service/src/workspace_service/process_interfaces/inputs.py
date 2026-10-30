"""One conversion layer for accepted source defaults and immutable run values."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
from typing import Literal
from uuid import uuid4

from pydantic import StrictBool, ValidationError, field_validator

from core.process_interactions import (
    ArtifactRef,
    FileBinding,
    InputBinding,
    InputDefinition,
    InputDependency,
    InputSnapshot,
    InlineJSON,
    NavigationTarget,
    ProcessRef,
    Readiness,
    Reason,
    ValueBinding,
    OptionBinding,
    checked_value_schema,
    validate_response,
)
from core.process_validation import Contract, Identifier, canonical_json

from ..workflow_references import WorkflowReference, allows_binary_file_reference
from ..workflow_source_execution import (
    PromptWorkflow,
    WorkflowSourceExecutionError,
    compile_prompt_workflow,
    validate_workspace_authoring_shape,
    _parse,
)
from ..workspace_path import WorkspacePath
from .errors import ProcessInterfaceError
from .limits import ProcessInterfaceLimits
from .options import OptionSource, read_options, verify_option


class InputMetadata(Contract):
    version: Literal[1]
    value_schema: dict
    required: StrictBool = True
    unit: Identifier | None = None
    frame: Identifier | None = None
    default: InlineJSON = None
    option_source: OptionSource | None = None
    default_option_id: Identifier | None = None

    _schema = field_validator("value_schema")(checked_value_schema)


@dataclass(frozen=True)
class PreparedInputs:
    snapshot: InputSnapshot
    definitions: tuple[InputDefinition, ...]
    values: dict
    plan: PromptWorkflow
    dependencies: tuple[InputDependency, ...]
    reasons: tuple[Reason, ...]


def _reason(code, message, correction, *, binding=None, step=None):
    return Reason(
        code=code,
        message=message,
        correction=correction,
        binding_id=binding,
        step_id=step,
        navigation=NavigationTarget(kind="block", block_id=step or binding)
        if step or binding
        else None,
    )


def _unsupported(
    message, correction="Use supported input metadata and connected workflow semantics."
):
    return ProcessInterfaceError("READINESS_UNSUPPORTED", message, correction)


def _sections(source):
    try:
        validate_workspace_authoring_shape(source)
        plan = compile_prompt_workflow(source)
        blocks = _parse(source)
    except WorkflowSourceExecutionError as error:
        raise _unsupported(str(error), error.correction) from error
    return plan, blocks


def _descriptors(plan, blocks):
    task_fields = {
        block["id"]: block["fields"] for block in blocks if block["kind"] == "task"
    }
    edges = [
        block["fields"]
        for block in blocks
        if block["kind"] == "connection" and block["fields"].get("type") == "item"
    ]
    descriptions = []
    for key, fields in plan.inputs.items():
        settings = fields.get("settings", {})
        try:
            metadata = (
                InputMetadata.model_validate(settings["interaction_input"])
                if "interaction_input" in settings
                else None
            )
            output_ports = fields.get("outputs", [])
            if not output_ports:
                raise ValueError("Input requires an output port")
            required = metadata.required if metadata else True
            addresses = {f"{key}.{port['key']}" for port in output_ports}
            for edge in edges:
                if edge["from"] not in addresses:
                    continue
                task_id, port_key = edge["to"].split(".", 1)
                required |= any(
                    port["key"] == port_key and port.get("required") is True
                    for port in task_fields[task_id].get("inputs", [])
                )
            for step in plan.steps:
                required |= bool(
                    addresses.intersection(
                        {
                            step.prompt_from,
                            step.arguments_from,
                            step.cad_from,
                            step.application_from,
                        }
                    )
                )
            file_input = (
                settings.get("input_mode") == "workspace-file"
                or bool(settings.get("workspace_file"))
                or any(port.get("kind") == "reference_images" for port in output_ports)
            )
            schema = (
                metadata.value_schema
                if metadata
                else (
                    {"type": "object"}
                    if file_input
                    else {"type": "string", "minLength": 1}
                )
            )
            default = None
            if metadata and "default" in metadata.model_fields_set:
                if file_input:
                    raise ValueError("File defaults must use an exact workspace file")
                default = ValueBinding(
                    input_id=key, value=metadata.default, provenance="explicit_default"
                )
            elif (
                not file_input
                and settings.get("input_text") is not None
                and settings["input_text"] != ""
            ):
                default = ValueBinding(
                    input_id=key,
                    value=settings["input_text"],
                    provenance="explicit_default",
                )
            option_source = metadata.option_source if metadata else None
            if option_source and file_input:
                raise ValueError("A file input cannot also be a provider choice")
            if metadata and metadata.default_option_id and not option_source:
                raise ValueError("An option default requires its configured source")
            if option_source and default is not None:
                raise ValueError("Use an exact default_option_id for provider choices")
            definition = InputDefinition(
                input_id=key,
                block_id=key,
                port_id=output_ports[0]["key"],
                title=fields["name"],
                binding_kind="option"
                if option_source
                else "file"
                if file_input
                else "value",
                option_source=option_source.capability() if option_source else None,
                required=required,
                value_schema=schema,
                unit=metadata.unit if metadata else None,
                frame=metadata.frame if metadata else None,
                default=default,
            )
        except (ValueError, TypeError, KeyError, ValidationError) as error:
            raise _unsupported(
                f"{fields['name']}: the input declaration is unsupported.",
                "Use version 1 bounded input schemas and explicit compatible defaults.",
            ) from error
        descriptions.append((definition, fields))
    return tuple(descriptions), task_fields, edges


def input_file_reference(plan, fields, input_id, path, data):
    """Use the accepted input's consumers to choose an existing reference reader."""
    addresses = {f"{input_id}.{port['key']}" for port in fields.get("outputs", [])}
    image = any(
        port.get("kind") == "reference_images" for port in fields.get("outputs", [])
    )
    return WorkflowReference.from_bytes(
        path,
        data,
        image=image,
        allow_binary=allows_binary_file_reference(plan.steps, addresses),
    )


def _file_only_consumer(plan, fields, input_id):
    addresses = {f"{input_id}.{port['key']}" for port in fields.get("outputs", [])}
    return not any(
        port.get("kind") == "reference_images" for port in fields.get("outputs", [])
    ) and allows_binary_file_reference(plan.steps, addresses)


async def _large_file_identity(service, workspace_dir, path, limits):
    """Reuse streamed artifact identity without loading native files as content."""
    target = WorkspacePath(workspace_dir).resolve(path, must_exist=True)
    before = target.stat()
    if not target.is_file() or not 0 < before.st_size <= limits.maximum_representation_bytes:
        raise ValueError("The file exceeds the supported artifact reference size.")
    digest = await service.files.hash_reference(workspace_dir, path)
    after = WorkspacePath(workspace_dir).resolve(path, must_exist=True).stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
    ):
        raise ValueError("The input file changed while its identity was prepared.")
    return digest, after.st_size


async def _file_value(
    *, service, workspace_dir, plan, fields, binding, limits, review_snapshots=None
):
    path = binding.reference.artifact_ref
    try:
        target = WorkspacePath(workspace_dir).resolve(path, must_exist=True)
        if (
            review_snapshots is None
            and target.stat().st_size > limits.maximum_upload_bytes
            and _file_only_consumer(plan, fields, binding.input_id)
        ):
            digest, size = await _large_file_identity(
                service, workspace_dir, path, limits
            )
            if digest != binding.reference.sha256:
                raise ProcessInterfaceError(
                    "SUBJECT_STALE",
                    "A prepared input file changed.",
                    "Select the current exact file and prepare its inputs again.",
                )
            return WorkflowReference(path, digest, file_only=True, size_bytes=size)
        data = await service.files.read_bytes(
            workspace_dir, path, maximum_bytes=limits.maximum_upload_bytes
        )
        if not data or len(data) > limits.maximum_upload_bytes:
            raise ValueError("File is empty or exceeds the input bound")
        if hashlib.sha256(data).hexdigest() != binding.reference.sha256:
            raise ProcessInterfaceError(
                "SUBJECT_STALE",
                "A prepared input file changed.",
                "Select the current exact file and prepare its inputs again.",
            )
        value = input_file_reference(plan, fields, binding.input_id, path, data)
        if review_snapshots is not None:
            from ..workflow_artifact_review import snapshot

            review_snapshots.append(snapshot(path, data))
        return value
    except ProcessInterfaceError:
        raise
    except (OSError, ValueError, UnicodeError) as error:
        if isinstance(error.__cause__, UnicodeError):
            raise ProcessInterfaceError(
                "RESPONSE_INVALID",
                f"Input '{fields['name']}' expects text, but the selected file contains binary data.",
                "Configure the connected step to consume this input as a file, "
                "or select a UTF-8 text document. The selected file has not been changed.",
                navigation=NavigationTarget(kind="block", block_id=binding.input_id),
            ) from error
        raise ProcessInterfaceError(
            "RESPONSE_INVALID",
            "The selected file cannot supply this process input.",
            "Select an existing supported file inside this workspace.",
        ) from error


def runtime_value(binding):
    """Detach the frozen JSON value without changing its declared type or units."""
    return json.loads(canonical_json(binding.value))


def _omit_optional(plan, omitted):
    def present(source):
        return source.split(".", 1)[0] not in omitted

    return replace(
        plan,
        inputs={
            key: fields for key, fields in plan.inputs.items() if key not in omitted
        },
        steps=tuple(
            replace(
                step,
                references=tuple(
                    (name, src) for name, src in step.references if present(src)
                ),
                argument_sources={
                    name: src
                    for name, src in step.argument_sources.items()
                    if present(src)
                },
            )
            for step in plan.steps
        ),
    )


async def prepare_inputs(
    *,
    service,
    workspace_dir: str,
    process: ProcessRef,
    source: str,
    bindings: tuple[InputBinding, ...] = (),
    snapshot_id=None,
    now=None,
    created_at=None,
    limits: ProcessInterfaceLimits | None = None,
    review_snapshots=None,
    tool_runtime=None,
    review_snapshot: InputSnapshot | None = None,
) -> PreparedInputs:
    # Only the approval owner's persisted snapshot is eligible for passive
    # review. Normal preparation and continuation still refresh live choices.
    if review_snapshot is not None:
        review_snapshot = InputSnapshot.model_validate_json(
            review_snapshot.model_dump_json()
        )
        if review_snapshot.process != process or review_snapshot.bindings != bindings:
            raise ProcessInterfaceError(
                "SUBJECT_STALE",
                "The review values do not match this run's frozen inputs.",
                "Reopen the exact saved review and its input snapshot.",
            )
    limits = limits or ProcessInterfaceLimits()
    if hashlib.sha256(source.encode("utf-8")).hexdigest() != process.source_digest:
        raise ProcessInterfaceError(
            "SOURCE_CHANGED",
            "The input source no longer matches this process.",
            "Reload the exact accepted source before preparing values.",
        )
    plan, blocks = _sections(source)
    descriptions, task_fields, edges = _descriptors(plan, blocks)
    supplied = {item.input_id: item for item in bindings}
    declared = {item.input_id for item, _ in descriptions}
    if len(supplied) != len(bindings) or not set(supplied) <= declared:
        raise ProcessInterfaceError(
            "RESPONSE_INVALID",
            "An input is duplicated or is not declared by this process.",
            "Supply one value for each declared input ID.",
        )
    values, frozen, definitions, reasons, dependencies, omitted = (
        {},
        [],
        [],
        [],
        [],
        set(),
    )
    total_file_bytes = 0
    for definition, fields in descriptions:
        key = definition.input_id
        default = definition.default
        catalog = None
        metadata = (
            InputMetadata.model_validate(fields["settings"]["interaction_input"])
            if fields.get("settings", {}).get("interaction_input") is not None
            else None
        )
        if definition.binding_kind == "option" and review_snapshot is not None:
            saved = supplied.get(key)
            if saved is not None:
                declared_capability = metadata.option_source.capability()
                if (
                    not isinstance(saved, OptionBinding)
                    or saved.capability.binding_id != declared_capability.binding_id
                    or saved.capability.schema_digest
                    != declared_capability.schema_digest
                    or saved.capability.resource_digest is None
                ):
                    raise ProcessInterfaceError(
                        "SUBJECT_STALE",
                        "The recorded provider choice does not match the accepted input declaration.",
                        "Inspect the exact saved option and capability identity.",
                    )
                definition = InputDefinition.model_validate(
                    {
                        **definition.model_dump(),
                        "option_source": saved.capability,
                    }
                )
                if saved.option_id == metadata.default_option_id:
                    default = saved.model_copy(
                        update={"provenance": "explicit_default"}
                    )
        elif definition.binding_kind == "option":
            try:
                catalog = await read_options(
                    metadata.option_source,
                    tool_runtime,
                    input_id=key,
                    value_schema=definition.value_schema,
                    now=now,
                )
                definition = InputDefinition.model_validate(
                    {
                        **definition.model_dump(),
                        "option_source": catalog.capability,
                        "available_options": catalog.options,
                        "options_observed_at": catalog.observed_at,
                        "options_stale_after": catalog.stale_after,
                    }
                )
                if metadata.default_option_id:
                    selected = next(
                        (
                            item
                            for item in catalog.options
                            if item.option_id == metadata.default_option_id
                        ),
                        None,
                    )
                    if selected:
                        default = OptionBinding(
                            input_id=key,
                            option_id=selected.option_id,
                            capability=catalog.capability,
                            value=selected.value,
                            observed_at=catalog.observed_at,
                            stale_after=catalog.stale_after,
                            provenance="explicit_default",
                        )
            except ProcessInterfaceError as error:
                if error.reason.code == "READINESS_UNSUPPORTED" or key in supplied:
                    raise
                reasons.append(error.reason.model_copy(update={"binding_id": key}))
        if definition.binding_kind == "file" and fields.get("settings", {}).get(
            "workspace_file"
        ):
            default_path = fields["settings"]["workspace_file"]
            try:
                target = WorkspacePath(workspace_dir).resolve(default_path, must_exist=True)
                if (
                    review_snapshots is None
                    and target.stat().st_size > limits.maximum_upload_bytes
                    and _file_only_consumer(plan, fields, key)
                ):
                    identity, _ = await _large_file_identity(
                        service, workspace_dir, default_path, limits
                    )
                else:
                    raw = await service.files.read_bytes(
                        workspace_dir,
                        default_path,
                        maximum_bytes=limits.maximum_upload_bytes,
                    )
                    identity = hashlib.sha256(raw).hexdigest()
                default = FileBinding(
                    input_id=key,
                    reference=ArtifactRef(
                        artifact_ref=default_path,
                        sha256=identity,
                    ),
                    provenance="explicit_default",
                )
            except (OSError, ValueError, TypeError):
                if key not in supplied and definition.required:
                    reasons.append(
                        _reason(
                            "INPUT_REQUIRED",
                            f"{definition.title}: the default file is unavailable.",
                            "Select an existing input file before starting.",
                            binding=key,
                        )
                    )
        binding = supplied.get(key, default)
        if binding is None:
            if definition.required:
                reason = _reason(
                    "INPUT_REQUIRED",
                    f"{definition.title}: an input is required before the process starts.",
                    "Supply this value or file in the preparation view.",
                    binding=key,
                )
                reasons.append(reason)
                dependencies.append(
                    InputDependency(
                        binding_id=key, classification="unresolved", reasons=(reason,)
                    )
                )
            else:
                omitted.add(key)
            definitions.append(
                InputDefinition.model_validate(
                    {**definition.model_dump(), "default": default}
                )
            )
            continue
        if binding.kind != definition.binding_kind:
            raise ProcessInterfaceError(
                "RESPONSE_INVALID",
                "The supplied value has the wrong input kind.",
                "Use the process's declared value, file or provider-choice input.",
            )
        if isinstance(binding, FileBinding):
            value = await _file_value(
                service=service,
                workspace_dir=workspace_dir,
                plan=plan,
                fields=fields,
                binding=binding,
                limits=limits,
                review_snapshots=review_snapshots,
            )
            # Opaque references carry identity/path metadata, not file contents
            # in the preparation request or model context. Their per-artifact
            # bound and exact downstream identity checks still apply.
            if not value.file_only or review_snapshots is not None:
                total_file_bytes += value.size_bytes or 0
            if total_file_bytes > limits.maximum_input_request_bytes:
                raise ProcessInterfaceError(
                    "RESPONSE_INVALID",
                    "The input files exceed this preparation's size bound.",
                    "Use a smaller input pack or authorized artifact references.",
                )
        else:
            if isinstance(binding, OptionBinding) and review_snapshot is None:
                verify_option(binding, catalog)
            try:
                validate_response(definition.value_schema, binding.value)
            except ValueError as error:
                raise ProcessInterfaceError(
                    "RESPONSE_INVALID",
                    f"{definition.title}: this value does not match its declared schema.",
                    "Correct the input type, range or required fields before starting.",
                ) from error
            value = runtime_value(binding)
        if binding.provenance == "explicit_default":
            excluded = {"provenance", "observed_at", "stale_after"}
            if default is None or canonical_json(
                binding.model_dump(exclude=excluded)
            ) != canonical_json(default.model_dump(exclude=excluded)):
                raise ProcessInterfaceError(
                    "RESPONSE_INVALID",
                    "This value is not the process's declared default.",
                    "Supply it as a run value or select the exact declared default.",
                )
        frozen.append(binding)
        values[key] = value
        dependencies.append(
            InputDependency(binding_id=key, classification=binding.provenance)
        )
        definitions.append(
            InputDefinition.model_validate(
                {
                    **definition.model_dump(),
                    "default": default,
                    "current_value": binding,
                }
            )
        )
    for edge in edges:
        producer, output_port = edge["from"].split(".", 1)
        consumer, input_port = edge["to"].split(".", 1)
        if producer not in plan.inputs:
            human_step = next(
                (
                    step
                    for step in plan.steps
                    if step.id == producer and step.human_interaction
                ),
                None,
            )
            dependencies.append(
                InputDependency(
                    binding_id=edge["to"],
                    classification="declared_human_response"
                    if human_step is not None
                    else "upstream_produced",
                    producer_step=producer,
                    producer_port=output_port,
                    interaction_step=producer if human_step is not None else None,
                )
            )
    if len(dependencies) > 256:
        raise _unsupported(
            "This preparation exceeds the bounded dependency assessment size."
        )
    plan = replace(
        _omit_optional(plan, omitted), definition_digest=process.source_digest
    )
    snapshot = InputSnapshot.create(
        snapshot_id=snapshot_id or f"inputs-{uuid4().hex}",
        process=process,
        created_at=created_at or now or datetime.now(timezone.utc).isoformat(),
        bindings=tuple(frozen),
    )
    return PreparedInputs(
        snapshot, tuple(definitions), values, plan, tuple(dependencies), tuple(reasons)
    )


def input_readiness(prepared: PreparedInputs, *, now=None) -> Readiness:
    return Readiness(
        state="blocked" if prepared.reasons else "ready",
        assessment_id=f"readiness-{uuid4().hex}",
        process=prepared.snapshot.process,
        input_digest=prepared.snapshot.digest,
        assessed_at=now or datetime.now(timezone.utc).isoformat(),
        dependencies=prepared.dependencies,
        reasons=prepared.reasons,
    )
