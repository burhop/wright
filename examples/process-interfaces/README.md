# Process working-interface examples

These examples use Wright's accepted source, durable runtime and native UI
authoring services. They do not implement an executor or install providers.
See the [operator/developer guide](../../docs/workflows/process-working-interfaces.md)
and the [checked feature scope](../../specs/083-process-working-interfaces/tasks.md).

## Compose through Wright

Open an accepted workflow in the workspace and choose **Use saved process**.
In its working tab choose **Create or choose interface**. Use the supplied
[reference instruction](reference-instruction.txt) in **How should this interface
help the user?**, adapting the layout to the job. Wright supplies the actual
process bindings, versioned instructions, public client/kit and fixed build.
Inspect **Open preview**, wait for it to load, then **Save interface**. Preview
does not execute the process. Select **Open saved interface** to reuse the build.

The packaged reference implementation is
`workspace_service.process_interfaces.resources/reference.tsx`. Inspect it in an
installed Wright Python environment without relying on a source checkout:

```powershell
python -c "from importlib.resources import files; print(files('workspace_service.process_interfaces.resources').joinpath('reference.tsx').read_text(encoding='utf-8'))"
```

This command reads a resource. It neither generates nor compiles an interface.
The actual configured-model authoring proof and saved reuse are documented in
[live UI evidence](../../specs/083-process-working-interfaces/evidence/live-ui-authoring.md).

## Read native authoring state

The authenticated operator environment supplies `WRIGHT_API_TOKEN`. Keep it out
of command arguments, source, interfaces and evidence. Replace the placeholders
below with the API origin, workspace/session and exact accepted source digest
from your own Wright installation:

```powershell
python examples/process-interfaces/inspect_interface.py --api API_ORIGIN --workspace-id WORKSPACE_ID --session SESSION_ID --source workflows/accepted.workflow.wflow --digest ACCEPTED_SOURCE_SHA256
```

Add `--job JOB_ID` to read a known job instead of authoring availability. Find
that ID in **Creation details**. The utility makes one bounded authenticated GET,
checks the returned process/job identity, refuses redirects, and prints only
selected status/provenance fields. It does not submit, poll, build, save, start,
approve or cancel anything. Authoring unavailable does not mean a saved interface
or common working view is unavailable.

Seventeen controlled tests and two earlier real scoped API reads are recorded in
[operator example evidence](../../specs/083-process-working-interfaces/evidence/operator-examples.md).

## Different engineering jobs

- [Heat-spreader sizing](heat-spreader-sizing/README.md): explicit geometry and
  thermal-analysis dependencies with unchanged engineering review requirements.
- [Printed replacement-part preparation](printed-replacement-part/README.md):
  existing independent geometry/slicing providers and exact preparation evidence.

Their `prepare.py` commands stage proposals in fresh isolated roots. Source
acceptance, readiness, execution and reviewer authority remain Wright operations.
Provider installation and vendor protocols remain outside these examples.
Neither example authorizes a machine, supplier action or engineering acceptance.

The original dataset preparers additionally use explicit
[external slicing bindings](../../docs/workflows/external-slicing-bindings.md)
and, for printed replacement parts,
[independent geometry bindings](../../docs/workflows/external-mesh-bindings.md).
These are proposed source/configuration and exact-artifact verification, not
bundled vendor implementation or private campaign execution. Saved historical
campaigns keep their original source and evidence.
