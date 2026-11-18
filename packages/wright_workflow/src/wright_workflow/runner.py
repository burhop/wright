"""Run an accepted native definition using only the caller's MCP bindings."""

import asyncio
import base64
import json
from uuid import uuid4

from .arguments import connected_arguments
from .artifacts import snapshot_task_files, verify_task_files
from .bindings import LocalServer, schema_digest
from .checkpoint import own_run
from .contracts import canonical_digest, canonical_json
from .definition import Definition, parse
from .execution import Transition, execute_steps
from .fixed import FixedCall, InputBarrier, compile_steps
from .input_conditions import validate_requirements_resolution
from .interaction_schema import validate_response
from .paths import ConfinedDirectory
from .run_inputs import materialize_inputs, prepare_inputs, verify_record
from .source import WorkflowSourceExecutionError, _invalid
from .transport import Sessions, validate_arguments


def _receipt(state):
    return {k: v for k, v in state.items() if k not in {"definition", "answers"}}


def _bindings(bindings):
    return {
        name: LocalServer.model_validate(server) for name, server in bindings.items()
    }


def run(definition, inputs, bindings, run_dir):
    return asyncio.run(run_async(definition, inputs, bindings, run_dir))


async def run_async(definition, inputs, bindings, run_dir):
    # Re-parse the exact bytes even if a caller has mutated a nested graph object.
    document = parse(
        definition.raw if isinstance(definition, Definition) else definition
    )
    resolved = _bindings(bindings)
    input_ports, files = prepare_inputs(document, inputs)
    with own_run(run_dir) as store:
        state = store.read()
        if state is None:
            run_id = uuid4().hex
            steps = compile_steps(document.graph, run_id)
            state = {
                "version": "wright.run/1",
                "run_id": run_id,
                "source_digest": document.source_digest,
                "definition": base64.b64encode(document.raw).decode("ascii"),
                "definition_digest": canonical_digest(
                    base64.b64encode(document.raw).decode("ascii")
                ),
                "input_digest": canonical_digest(input_ports),
                "bindings_digest": canonical_digest(resolved),
                "status": "ready",
                "cursor": 0,
                "ports": input_ports,
                "attempts": [],
                "answers": {},
                "pending": None,
            }
            materialize_inputs(store.files, files)
            store.save(state)
        else:
            if (
                document.raw != base64.b64decode(state["definition"])
                or state["input_digest"] != canonical_digest(input_ports)
                or state["bindings_digest"] != canonical_digest(resolved)
            ):
                raise _invalid(
                    "This run directory belongs to a different source, input snapshot or provider binding."
                )
            if state["status"] != "ready":
                return _receipt(state)
            steps = compile_steps(document.graph, state["run_id"])
        return await _drive(store, state, resolved, steps)


def resume(run_dir, response, bindings=None):
    return asyncio.run(resume_async(run_dir, response, bindings))


async def resume_async(run_dir, response, bindings=None):
    with own_run(run_dir) as store:
        state = store.read()
        if not state:
            raise _invalid("This directory has no saved run.")
        if not isinstance(response, dict) or set(response) != {"subject", "value"}:
            raise _invalid("Supply the pending subject and its typed input value.")
        subject = response["subject"]
        if not isinstance(subject, str):
            raise _invalid("The input subject is invalid.")
        resolved = _bindings(bindings or {})
        if canonical_digest(resolved) != state["bindings_digest"]:
            raise _invalid(
                "Reopen this run with its original caller-qualified bindings."
            )
        previous = state["answers"].get(subject)
        if previous is not None:
            if previous != canonical_digest(response):
                raise _invalid("This subject already has a different recorded answer.")
            if state["status"] != "ready":
                return _receipt(state)
        elif (
            state["status"] != "waiting_input" or state["pending"]["subject"] != subject
        ):
            raise _invalid("This response does not match the pending subject.")
        raw = base64.b64decode(state["definition"], validate=True)
        document = parse(raw)
        if (
            document.source_digest != state["source_digest"]
            or canonical_digest(state["definition"]) != state["definition_digest"]
        ):
            raise _invalid("The saved definition differs from the accepted source.")
        steps = compile_steps(document.graph, state["run_id"])
        return await _drive(
            store, state, resolved, steps, None if previous else response
        )


def _answer(store, state, step, value):
    validate_response(step.declaration.response_schema, value)
    pending = state["pending"]
    for key, identity in pending["upstream"].items():
        record = state["ports"][key]
        verify_record(store.files, key, record)
        if record["sha256"] != identity:
            raise _invalid("A result bound to the pending input changed.")
    for key, expected in pending.get("resolved", {}).items():
        if key not in value or canonical_json(value[key]) != canonical_json(expected):
            raise _invalid(
                "The response changed a field already resolved by the declared condition."
            )
    port = step.id + "." + step.declaration.output_port
    state["ports"][port] = {
        "kind": "value",
        "value": value,
        "sha256": canonical_digest(value),
    }
    state["answers"][pending["subject"]] = canonical_digest(
        {"subject": pending["subject"], "value": value}
    )
    state.update(status="ready", pending=None, cursor=state["cursor"] + 1)
    store.save(state)


def _wait(store, state, step):
    upstream = {}
    for _, key in step.references:
        record = state["ports"][key]
        verify_record(store.files, key, record)
        upstream[key] = record["sha256"]
    subject = canonical_digest(
        {
            "run": state["run_id"],
            "source": state["source_digest"],
            "inputs": state["input_digest"],
            "bindings": state["bindings_digest"],
            "block": step.id,
            "cursor": state["cursor"],
            "upstream": upstream,
            "declaration": step.declaration,
        }
    )
    pending = {
        "subject": subject,
        "block": step.id,
        "instructions": step.declaration.instructions,
        "schema": step.declaration.response_schema,
        "upstream": upstream,
    }
    if step.declaration.when:
        key = step.declaration.when.source
        value = verify_record(store.files, key, state["ports"][key])
        resolution = validate_requirements_resolution(
            step.declaration.when, step.declaration.response_schema, value
        )
        pending["resolved"] = resolution.resolved_values
        if not resolution.unresolved_fields:
            state["pending"] = pending
            _answer(store, state, step, resolution.resolved_values)
            return Transition.ADVANCE
    state.update(status="waiting_input", pending=pending)
    store.save(state)
    return Transition.HOLD


def _arguments(step, ports, tool, root, *, partial=False):
    addresses = set(step.argument_sources.values()) | set(step.file_dependencies)
    if step.arguments_from:
        addresses.add(step.arguments_from)
    values, evidence = {}, {}
    for address in addresses:
        if partial and address not in ports:
            continue
        record = ports[address]
        value = verify_record(root, address, record)
        if address in step.file_dependencies:
            required = step.file_dependencies[address]
            if record["kind"] != "file" or required not in (
                {"source": "connected_output"},
                record["path"],
            ):
                raise _invalid(
                    f"{step.title}: the input file differs from the connected producer port."
                )
        values[address] = record["path"] if record["kind"] == "file" else value
        evidence[address] = {key: v for key, v in record.items() if key != "value"}
    if partial and step.arguments_from and step.arguments_from not in values:
        return None, evidence
    arguments = connected_arguments(step, values, tool, partial=partial)
    schema = dict(tool.input_schema)
    if partial:
        deferred = {
            name for name, port in step.argument_sources.items() if port not in ports
        }
        if deferred:
            schema["required"] = [
                name for name in schema.get("required", []) if name not in deferred
            ]
    validate_arguments(step, schema, arguments)
    return arguments, evidence


async def _drive(store, state, bindings, steps, response=None):
    async with Sessions(bindings, store.files) as sessions:
        # Check all future required capabilities before executing or consuming an answer.
        for step in steps[state["cursor"] :]:
            if isinstance(step, FixedCall):
                tool = await sessions.resolve(step)
                _arguments(step, state["ports"], tool, store.files, partial=True)
        if response is not None:
            _answer(store, state, steps[state["cursor"]], response["value"])

        async def dispatch(cursor, step):
            if isinstance(step, InputBarrier):
                return _wait(store, state, step)
            tool = await sessions.resolve(step)
            arguments, upstream = _arguments(step, state["ports"], tool, store.files)
            before = snapshot_task_files(store.files, step.expected_files)
            attempt = {
                "id": uuid4().hex,
                "step": step.id,
                "outcome": "in_flight",
                "binding": tool.binding.model_dump(),
                "local_schema_digest": schema_digest(tool),
                "arguments_digest": canonical_digest(arguments),
                "consumed": upstream,
            }
            state["attempts"].append(attempt)
            state["status"] = "in_flight"
            store.save(state)
            try:
                result = await sessions.call(step, tool, arguments)
            except Exception as error:
                attempt["outcome"] = state["status"] = "outcome_unknown"
                attempt["diagnostic"] = (
                    f"The provider response was lost ({type(error).__name__})."
                )
                store.save(state)
                return Transition.HOLD
            except BaseException:
                attempt["outcome"] = state["status"] = "outcome_unknown"
                store.save(state)
                raise
            try:
                value = (
                    result.structuredContent
                    if result.structuredContent is not None
                    else {
                        "content": [
                            part.model_dump(
                                mode="json", by_alias=True, exclude_none=True
                            )
                            for part in result.content
                        ]
                    }
                )
                attempt["result_digest"] = canonical_digest(value)
                if result.isError:
                    raise ValueError(
                        "MCP tool reported failure: " + canonical_json(value)[:2048]
                    )
                _outputs(store, state, step, attempt, value, before)
            except (ValueError, OSError, WorkflowSourceExecutionError) as error:
                attempt.update(outcome="failed", diagnostic=str(error))
                state["status"] = "failed"
                store.save(state)
                return Transition.HOLD
            attempt["outcome"] = "completed"
            state.update(status="ready", cursor=cursor + 1)
            store.save(state)
            return Transition.ADVANCE

        cursor = await execute_steps(steps, state["cursor"], dispatch)
        if cursor == len(steps):
            state["status"] = "completed"
            store.save(state)
    return _receipt(state)


def _outputs(store, state, step, attempt, value, before):
    files = {
        item["output_path"]: item
        for item in verify_task_files(store.files, step.expected_files, before)
    }
    records = {}
    for port in step.output_ports:
        address = step.id + "." + port
        lineage = {
            "run_id": state["run_id"],
            "attempt": attempt["id"],
            "source_port": address,
        }
        if port in step.expected_file_ports:
            item = files[step.expected_file_ports[port]]
            records[address] = dict(
                lineage,
                kind="file",
                path=item["output_path"],
                sha256=item["sha256"],
                size=item["output_bytes"],
            )
        else:
            records[address] = dict(
                lineage, kind="value", value=value, sha256=canonical_digest(value)
            )
    if step.save_response:
        target = ConfinedDirectory(store.files).resolve(step.response_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if step.file_policy in {"indexed", "publish_indexed"} and target.exists():
            target = target.with_name(target.stem + "-" + attempt["id"] + target.suffix)
        content = (
            json.dumps(value, ensure_ascii=False, indent=2)
            if step.output_format == "json" or not isinstance(value, str)
            else value
        )
        target.write_bytes(content.encode("utf-8"))
        attempt["response_path"] = target.relative_to(store.files).as_posix()
    state["ports"].update(records)
