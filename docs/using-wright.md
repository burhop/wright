# Using Wright

Use the first-workflow example to install Wright and generate working bindings for two MCP servers. [Run the example](../README.md#run-the-example)

## What you supply

| Item | Contents |
| --- | --- |
| Workflow | A UTF-8 `.workflow.wflow` source or a JSON `wright.workflow-bundle/1` document. Each fixed tool step names its provider, operation and connections. |
| Local bindings | A JSON object keyed by the source’s server aliases. Each entry identifies a local stdio MCP command, its arguments, pinned build files, provider/build identity and allowed tool contracts. Generate the example file on the machine where you will run it. |
| Inputs | An optional JSON object keyed by the declared input block ID or its qualified output port, such as `part.source`. Supply one key per input. For a file input, use an object such as `{"path":"drawing.step"}`. Relative source paths are read from your current directory. |
| Run directory | A writable directory for one run. Pick a path whose components are ordinary directories. For example, use the physical directory path if your system exposes temporary storage through a symbolic link. |

## Inspect and run

```shell
wright-workflow parse process.workflow.wflow
wright-workflow run process.workflow.wflow --inputs inputs.json --bindings bindings.json --run-dir runs/trial-01
```

Replace the paths with your files. Omit `--inputs` when the definition needs no supplied values. Parsing reads the definition without contacting a tool. To execute a fixed call, Wright checks the local program hashes, the configured server and the advertised tool contract. A missing or incompatible provider needs a corrected local binding. Choosing a different provider changes the workflow definition. [Binding generator](../examples/handoff/configure.py) · [Executable profile](../FORMAT.md)

The example connects the writer’s `coordinates` port to the reader’s `source_file` input. The workflow declares the connection, the bindings tell Wright how to launch each server, and the receipt identifies the bytes that actually travelled between them. New providers need their own reviewed executable paths, hashes and contracts. [Complete definition](../examples/handoff/length.workflow.wflow)

## Read a receipt or continue a wait

Use `status` to decide what to do next. Keep the run directory to retain the checkpoint and its files.

| Status | Meaning and next action |
| --- | --- |
| `completed` | Inspect the named results in `ports` and their input records in `attempts`. Tool completion records the execution outcome. Engineering acceptance depends on the checks your process requires. |
| `waiting_input` | Read `pending`, copy its exact `subject`, and provide a `value` that satisfies the block’s declared response schema. Resume in the same directory with the same bindings. |
| `failed` | Inspect the failed attempt and the upstream results already recorded. |
| `outcome_unknown` | A call may have taken effect before its reply was recorded. Inspect the provider’s evidence for that attempt before taking further action. Reopening the run preserves the hold. |

For a waiting block that asks for an integer quantity, an answer file has the shape `{"subject":"<copy pending.subject>","value":{"quantity":2}}`. Use the subject and value schema from your own run.

```shell
wright-workflow resume --run-dir runs/trial-01 --bindings bindings.json --response answer.json
```

The CLI prints receipts to standard output. Exit code 0 includes a declared wait, so automation should also inspect `status`. A failed or uncertain run returns 1. Invalid source, arguments or configuration can return 2 with a diagnostic on standard error.

## Use the Python API

From the checkout, after generating `bindings.json` as in the quickstart, the same example can be run in Python.

```python
import json
from pathlib import Path

from wright_workflow import parse, run

definition = parse(Path("examples/handoff/length.workflow.wflow"))
bindings = json.loads(Path("bindings.json").read_text(encoding="utf-8"))
receipt = run(definition, {}, bindings, Path("runs/python-length"))
print(receipt["ports"]["reader.measurement"]["value"]["length_mm"])
```

Pass a `Path` to `parse` to read a file. A `str` argument is interpreted as source text. For an existing event loop, use `await run_async(...)` or `await resume_async(...)`. [Python entry points](../src/wright_workflow/__init__.py)
