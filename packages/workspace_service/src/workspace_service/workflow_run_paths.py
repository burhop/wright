"""Explicit run-path bindings for the canonical compiler/preparer, not an executor."""

from dataclasses import replace
import hashlib
import re

from .workflow_references import WorkflowReference
from .workflow_references import accepts_supplied_artifacts
from .workspace_path import WorkspacePath

VERSION = "wright.run-path/1"
ATTEMPT_VERSION = "wright.run-path/2"
TOKEN = "{{wright.run_id}}"
ATTEMPT_TOKEN = "{{wright.producer_attempt}}"
RESERVED = "{{wright."
FIELDS = (
    "prompt",
    "task_guidance",
    "arguments",
    "output_path",
    "expected_files",
    "expected_file_ports",
    "file_dependencies",
)


def _invalid(message):
    from .workflow_source_execution import _invalid as source_invalid

    return source_invalid(
        message,
        "For wright.run-path/1, give every saved response and expected file a complete {{wright.run_id}} directory, for example deliverables/{{wright.run_id}}/model.step. Map provider file ports with expected_file_ports. Use version 2 only for explicitly configured automatic create-new file correction; do not switch versions to repair a missing run directory. Keep other inputs literal.",
    )


def _map(value, run_id, *, allow_attempt=False):
    if isinstance(value, str):
        result = value.replace(TOKEN, run_id)
        inspected = result.replace(ATTEMPT_TOKEN, "") if allow_attempt else result
        if RESERVED in inspected:
            raise _invalid("A run-path template contains an unsupported Wright token.")
        return result
    if isinstance(value, dict):
        if any(RESERVED in str(key) for key in value):
            raise _invalid("Run-path templates cannot change object keys.")
        return {
            key: _map(item, run_id, allow_attempt=allow_attempt)
            for key, item in value.items()
        }
    if isinstance(value, (tuple, list)):
        items = [_map(item, run_id, allow_attempt=allow_attempt) for item in value]
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
    if value not in ("", VERSION, ATTEMPT_VERSION):
        raise _invalid("The run-path template version is unsupported.")
    return bool(value)


def _root(path, run_id, *, allow_attempt=False):
    from .workflow_source_execution import _safe_path

    parts = path.split("/")
    if parts.count(TOKEN) != 1 or TOKEN not in parts[:-1]:
        raise _invalid(
            "A run-scoped output needs one run-id directory component before its filename."
        )
    resolved = _safe_path(_map(path, run_id, allow_attempt=allow_attempt))
    return resolved, "/".join(parts[: parts.index(TOKEN)] + [run_id])


def validate_attempt_paths(step):
    """A declared file correction must allocate each attempt before dispatch."""
    if step.run_path_template != ATTEMPT_VERSION:
        raise _invalid(
            "Automatic MCP file correction requires wright.run-path/2 attempt paths."
        )
    if not (
        step.agent_task
        and step.revision_policy == "create_new_files"
        and step.file_policy == "indexed"
        and step.expected_files
        and not any(
            (
                step.cad,
                step.application,
                step.tool_name,
                step.external_action,
                step.human_review,
                step.human_interaction,
                step.design_check,
            )
        )
    ):
        raise _invalid(
            "Attempt paths require an isolated create-new workspace-file MCP task."
        )
    # A dependency belongs to its upstream producer, not to this task's attempt.
    if _contains_attempt(step.file_dependencies):
        raise _invalid(
            "File dependencies cannot use the consuming task's attempt token."
        )
    for path in ((step.output_path,) if step.save else ()) + step.expected_files:
        parts = path.split("/")
        if parts.count(ATTEMPT_TOKEN) != 1 or ATTEMPT_TOKEN not in parts[:-1]:
            raise _invalid(
                "Each corrected output needs one producer-attempt directory before its filename."
            )
        if TOKEN in parts and parts.index(TOKEN) >= parts.index(ATTEMPT_TOKEN):
            raise _invalid(
                "The producer-attempt directory must be inside its run directory."
            )


def _contains_attempt(value):
    if isinstance(value, str):
        return ATTEMPT_TOKEN in value
    if isinstance(value, dict):
        return any(
            _contains_attempt(key) or _contains_attempt(item)
            for key, item in value.items()
        )
    if isinstance(value, (tuple, list)):
        return any(_contains_attempt(item) for item in value)
    return False


def bind_attempt_paths(step, attempt, workspace_dir):
    """Bind and exclusively reserve an attempt of an already run-bound task.

    The accepted plan remains a template. Continuation derives the attempt from
    its retained canonical records; an existing directory is never replayed.
    """
    if step.run_path_template != ATTEMPT_VERSION:
        return step
    validate_attempt_paths(step)
    if type(attempt) is not int or not 1 <= attempt <= 4:
        raise _invalid("The producer attempt exceeds the supported correction bound.")
    if any(TOKEN in path for path in step.expected_files):
        raise _invalid("Attempt paths require a backend-bound run identity first.")

    def resolve(value):
        if isinstance(value, str):
            return value.replace(ATTEMPT_TOKEN, str(attempt))
        if isinstance(value, dict):
            return {key: resolve(item) for key, item in value.items()}
        if isinstance(value, (tuple, list)):
            items = [resolve(item) for item in value]
            return tuple(items) if isinstance(value, tuple) else items
        return value

    roots = set()
    for path in ((step.output_path,) if step.save else ()) + step.expected_files:
        parts = path.split("/")
        roots.add("/".join(parts[: parts.index(ATTEMPT_TOKEN)] + [str(attempt)]))
    paths = WorkspacePath(workspace_dir)
    for relative in sorted(roots):
        target = paths.resolve(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            target.mkdir(exist_ok=False)
        except FileExistsError as error:
            raise _invalid(
                "This producer attempt already has an output directory; reconcile its outcome instead of replaying it."
            ) from error
    return replace(step, **{key: resolve(getattr(step, key)) for key in FIELDS})


def verify_prior_attempt_files(step, attempts, workspace_dir):
    """Stop the correction if a provider changed evidence from a prior attempt."""
    if step.run_path_template != ATTEMPT_VERSION:
        return
    paths = WorkspacePath(workspace_dir)
    for record in attempts:
        if record["task_id"] != step.id:
            continue
        for receipt in record.get("produced_files", []):
            try:
                target = paths.resolve(receipt["output_path"], must_exist=True)
                with target.open("rb") as stream:
                    digest = hashlib.file_digest(stream, "sha256").hexdigest()
                if digest != receipt["sha256"]:
                    raise ValueError("changed bytes")
            except (OSError, ValueError, KeyError) as error:
                raise _invalid(
                    "A previous producer attempt's file changed or is unavailable; correction cannot release downstream work."
                ) from error


def bind_run_paths(plan, run_id):
    """Resolve only explicitly declared fields, retaining source/step/port identity."""
    # These fields never participate in this template version, including on
    # undeclared steps in a templated process. Leaving a token literal here
    # would defer predictable missing action/document configuration until run.
    for step in plan.steps:
        for value in (
            step.external_action,
            step.validation,
            step.cad,
            step.application,
            step.human_interaction,
        ):
            if _contains(value):
                raise _invalid(
                    "This run-path version cannot template approval, validation or document configuration."
                )
    enabled = any(step.run_path_template for step in plan.steps) or any(
        fields.get("settings", {}).get("run_path_template")
        for fields in plan.inputs.values()
    )
    if not enabled:
        if any(_contains(getattr(step, key)) for step in plan.steps for key in FIELDS):
            raise _invalid("A Wright run token needs an explicit run-path declaration.")
        return plan
    if not isinstance(run_id, str) or not re.fullmatch(
        r"[A-Za-z0-9][A-Za-z0-9_-]{0,95}", run_id
    ):
        raise _invalid("Run-path binding requires a safe backend run identity.")
    if plan.run_path_id:
        if plan.run_path_id != run_id:
            raise _invalid("The prepared output paths belong to another run.")
        return plan
    roots = set()
    steps = []
    for step in plan.steps:
        declared = _version(step.run_path_template)
        attempt_paths = step.run_path_template == ATTEMPT_VERSION
        if attempt_paths:
            validate_attempt_paths(step)
        selected = {key: getattr(step, key) for key in FIELDS}
        if not declared:
            if any(_contains(value) for value in selected.values()):
                raise _invalid("A Wright run token needs an explicit step declaration.")
            steps.append(step)
            continue
        for path in ((step.output_path,) if step.save else ()) + step.expected_files:
            _, root = _root(path, run_id, allow_attempt=attempt_paths)
            roots.add(root)
        mapped = {
            key: _map(value, run_id, allow_attempt=attempt_paths)
            for key, value in selected.items()
        }
        if step.external_action and step.output_path:
            # The compiler declares a receipt as an output. Bind that output
            # into existing checkpoint/dispatch settings only after its path
            # is concrete; authority dictionaries never become templates.
            settings = step.external_action.get("settings", {})
            if "receipt_path" in settings:
                raise _invalid(
                    "A declared receipt output conflicts with an approval receipt path."
                )
            mapped["external_action"] = {
                **step.external_action,
                "settings": {**settings, "receipt_path": mapped["output_path"]},
            }
        steps.append(replace(step, **mapped))
    for fields in plan.inputs.values():
        if fields.get("settings", {}).get("run_path_template") == ATTEMPT_VERSION:
            raise _invalid(
                "Producer-attempt templates belong to task outputs, not process inputs."
            )
        _version(fields.get("settings", {}).get("run_path_template", ""))
    return replace(
        plan,
        steps=tuple(steps),
        run_path_id=run_id,
        run_path_roots=tuple(sorted(roots)),
    )


def bind_run_input_values(plan, values):
    """Pin template bytes separately from the exact resolved provider/model text."""
    result = dict(values)
    for key, fields in plan.inputs.items():
        if (
            not _version(fields.get("settings", {}).get("run_path_template", ""))
            or key not in values
        ):
            continue
        if not plan.run_path_id:
            raise _invalid("A declared run-path input has no backend run identity.")
        addresses = {f"{key}.{port['key']}" for port in fields.get("outputs", [])}
        if any(
            addresses.intersection(step.file_dependencies)
            or step.application_from in addresses
            or (
                accepts_supplied_artifacts(step)
                and any(source in addresses for _, source in step.references)
            )
            for step in plan.steps
        ):
            raise _invalid(
                "A run-path template is configuration text, not an opaque artifact handoff."
            )
        value = values[key]
        if isinstance(value, WorkflowReference):
            if value.file_only or value.image_url:
                raise _invalid(
                    "Run-path templates require text, not opaque files or images."
                )
            if value.run_path_id:
                if (
                    value.run_path_id != plan.run_path_id
                    or value.resolved_sha256
                    != hashlib.sha256(value.text.encode()).hexdigest()
                ):
                    raise _invalid(
                        "The resolved input belongs to another run or changed."
                    )
                continue
            text = _map(value.text, plan.run_path_id)
            result[key] = replace(
                value,
                text=text,
                run_path_id=plan.run_path_id,
                resolved_sha256=hashlib.sha256(text.encode()).hexdigest(),
            )
        elif isinstance(value, str):
            result[key] = _map(value, plan.run_path_id)
        else:
            raise _invalid("Run-path templates require a declared text input.")
    return result


def reserve_run_paths(plan, workspace_dir, run_id, *, continuing=False):
    """Reserve fresh output directories only after a durable start is accepted."""
    if not plan.run_path_id:
        if any(step.run_path_template for step in plan.steps) or any(
            fields.get("settings", {}).get("run_path_template")
            for fields in plan.inputs.values()
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
                raise _invalid(
                    "This run output directory already exists; reconcile the recorded run instead of overwriting it."
                ) from error
