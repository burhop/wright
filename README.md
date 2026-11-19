# Wright

Wright reads native `.workflow.wflow` definitions and executes their fixed MCP calls. A developer supplies the workflow, local server bindings and any declared inputs. The executor records the exact output each downstream step consumed and checkpoints each run in its own directory.

## Run the example

From a checkout, activate a Python 3.11 or newer virtual environment and run:

```shell
python -m pip install .
python examples/handoff/configure.py bindings.json
wright-workflow parse examples/handoff/length.workflow.wflow
wright-workflow run examples/handoff/length.workflow.wflow --bindings bindings.json --run-dir runs/length
```

The example starts two local MCP processes. The writer saves two points to a file. The reader consumes that file and reports a distance of **5 mm**. Its receipt includes the file's digest and the producer port. Running the same command again returns the saved result.

See the [executable profile](FORMAT.md) for source and bundle rules, tool qualification, human input and interrupted calls. The command is `wright-workflow` and the import is `wright_workflow`. Both can coexist with the historical `wright-engineering` application. Existing installations can continue using their selected releases and workspace data.

The [MIT license](LICENSE) covers this implementation and its Wright-derived profile. The profile links to the separate October interchange draft.
