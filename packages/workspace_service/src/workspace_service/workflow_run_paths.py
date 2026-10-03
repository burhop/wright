"""Explicit run-path bindings for the canonical compiler/preparer, not an executor."""

from dataclasses import replace
import hashlib
import re

from .workflow_references import WorkflowReference
from .workflow_references import accepts_supplied_artifacts
from .workspace_path import WorkspacePath

VERSION = "wright.run-path/1"
TOKEN = "{{wright.run_id}}"
RESERVED = "{{wright."
FIELDS = (
    "prompt", "task_guidance", "arguments", "output_path", "expected_files",
    "expected_file_ports", "file_dependencies",
)


def _invalid(message):
    from .workflow_source_execution import _invalid as source_invalid

    return source_invalid(message, "Declare wright.run-path/1 and use the supported run-id path token; keep other inputs literal.")


def _map(value, run_id):
    if isinstance(value, str):
        result = value.replace(TOKEN, run_id)
        if RESERVED in result:
            raise _invalid("A run-path template contains an unsupported Wright token.")
        return result
    if isinstance(value, dict):
        if any(RESERVED in str(key) for key in value):
            raise _invalid("Run-path templates cannot change object keys.")
        return {key: _map(item, run_id) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        items = [_map(item, run_id) for item in value]
        return tuple(items) if isinstance(value, tuple) else items
    return value


def _contains(value):
    if isinstance(value, str):
        return RESERVED in value
    if isinstance(value, dict):
        return any(_contains(key) or _contains(item) for key, item in value.items())
    if isinstance(value, (tuple, list)):
        return any(_contains(item) for item in value)
    return False


def _version(value):
    if value not in ("", VERSION):
        raise _invalid("The run-path template version is unsupported.")
    return value == VERSION


def _root(path, run_id):
    from .workflow_source_execution import _safe_path

    parts = path.split("/")
    if parts.count(TOKEN) != 1 or TOKEN not in parts[:-1]:
        raise _invalid("A run-scoped output needs one run-id directory component before its filename.")
    resolved = _safe_path(_map(path, run_id))
    return resolved, "/".join(parts[:parts.index(TOKEN)] + [run_id])


def bind_run_paths(plan, run_id):
    """Resolve only explicitly declared fields, retaining source/step/port identity."""
    enabled = any(step.run_path_template for step in plan.steps) or any(
        fields.get("settings", {}).get("run_path_template") for fields in plan.inputs.values()
    )
    if not enabled:
        if any(_contains(getattr(step, key)) for step in plan.steps for key in FIELDS):
            raise _invalid("A Wright run token needs an explicit run-path declaration.")
        return plan
    if not isinstance(run_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,95}", run_id):
        raise _invalid("Run-path binding requires a safe backend run identity.")
    if plan.run_path_id:
        if plan.run_path_id != run_id:
            raise _invalid("The prepared output paths belong to another run.")
        return plan
    roots = set()
    steps = []
    for step in plan.steps:
        declared = _version(step.run_path_template)
        selected = {key: getattr(step, key) for key in FIELDS}
        if not declared:
            if any(_contains(value) for value in selected.values()):
                raise _invalid("A Wright run token needs an explicit step declaration.")
            steps.append(step)
            continue
        # Approval destinations, validation profiles and native document identities
        # are not template fields. Their existing exact-subject contracts apply.
        for value in (step.external_action, step.validation, step.cad, step.application, step.human_interaction):
            if _contains(value):
                raise _invalid("This run-path version cannot template approval, validation or document configuration.")
        for path in ((step.output_path,) if step.save else ()) + step.expected_files:
            _, root = _root(path, run_id)
            roots.add(root)
        steps.append(replace(step, **{key: _map(value, run_id) for key, value in selected.items()}))
    for fields in plan.inputs.values():
        _version(fields.get("settings", {}).get("run_path_template", ""))
    return replace(plan, steps=tuple(steps), run_path_id=run_id, run_path_roots=tuple(sorted(roots)))


def bind_run_input_values(plan, values):
    """Pin template bytes separately from the exact resolved provider/model text."""
    result = dict(values)
    for key, fields in plan.inputs.items():
        if not _version(fields.get("settings", {}).get("run_path_template", "")) or key not in values:
            continue
        if not plan.run_path_id:
            raise _invalid("A declared run-path input has no backend run identity.")
        addresses = {f"{key}.{port['key']}" for port in fields.get("outputs", [])}
        if any(
            addresses.intersection(step.file_dependencies)
            or step.application_from in addresses
            or (accepts_supplied_artifacts(step) and any(source in addresses for _, source in step.references))
            for step in plan.steps
        ):
            raise _invalid("A run-path template is configuration text, not an opaque artifact handoff.")
        value = values[key]
        if isinstance(value, WorkflowReference):
            if value.file_only or value.image_url:
                raise _invalid("Run-path templates require text, not opaque files or images.")
            if value.run_path_id:
                if value.run_path_id != plan.run_path_id or value.resolved_sha256 != hashlib.sha256(value.text.encode()).hexdigest():
                    raise _invalid("The resolved input belongs to another run or changed.")
                continue
            text = _map(value.text, plan.run_path_id)
            result[key] = replace(value, text=text, run_path_id=plan.run_path_id,
                                  resolved_sha256=hashlib.sha256(text.encode()).hexdigest())
        elif isinstance(value, str):
            result[key] = _map(value, plan.run_path_id)
        else:
            raise _invalid("Run-path templates require a declared text input.")
    return result


def reserve_run_paths(plan, workspace_dir, run_id, *, continuing=False):
    """Reserve fresh output directories only after a durable start is accepted."""
    if not plan.run_path_id:
        if any(step.run_path_template for step in plan.steps) or any(
            fields.get("settings", {}).get("run_path_template") for fields in plan.inputs.values()
        ):
            raise _invalid("The declared run paths were not prepared by the backend.")
        return
    if plan.run_path_id != run_id:
        raise _invalid("The execution identity differs from its prepared output paths.")
    paths = WorkspacePath(workspace_dir)
    for relative in plan.run_path_roots:
        target = paths.resolve(relative)
        if continuing:
            if not target.is_dir():
                raise _invalid("The retained run output directory is unavailable.")
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                target.mkdir(exist_ok=False)
            except FileExistsError as error:
                raise _invalid("This run output directory already exists; reconcile the recorded run instead of overwriting it.") from error
