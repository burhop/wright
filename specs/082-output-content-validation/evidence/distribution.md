# Process validator distribution evidence

**Date:** 2026-09-16  
**Feature:** 082 output content validation  
**Scope:** T031 installed native/offline/CLI/gateway/Docker boundary

## Installed wheel

The repository wheel was built with the standard no-isolation package path:

```powershell
.venv\Scripts\python.exe -m build --wheel --no-isolation `
  --outdir .local-run/process-validation-082/docker-wheel-20260916/dist
```

Result: `wright_engineering-0.1.9-py3-none-any.whl`, 806 members, SHA-256
`7b47c4f61ac576dbd4b9ee33ab3febf39063554485fd51874929fa1470e846c2`.

`tests/packaging/test_process_validation_distribution.py` builds and extracts a
fresh wheel, starts Python with `-I`, inserts only the extracted wheel root for
Wright modules, and runs from a separate runtime directory. It proves:

- the core contract, repository, service, structured/geometry/thermal readers,
  CLI, BaseTool/gateway adapter and all packaged profiles are present;
- the `wright-process-validate` console entry maps to
  `workspace_service.process_validation_cli:main`;
- `structured-demo`, `parametric-drill-jig-01`,
  `heat-spreader-sizing-01` and coverage map version 2 load through
  `importlib.resources`;
- the CLI evaluates a passing structured output into a real SQLite ledger;
- the installed gateway provider exposes evaluate/read/get/export and retrieves
  that same assessment;
- all Wright module paths resolve below the extracted wheel, while network and
  child-process entry points are blocked during evaluation;
- the wheel does not contain test, script or retained-evidence trees.

Command and result:

```powershell
.venv\Scripts\python.exe -m pytest `
  tests/packaging/test_process_validation_distribution.py -q `
  -p no:cacheprovider `
  --basetemp=.local-run/process-validation-082/pytest-distribution-final
```

Result: **2 passed in 9.79s**.

No package metadata change was necessary. The existing Hatch wheel target
recursively includes the package resources, and the console entry already
exists in the root project metadata.

## Docker boundary

Docker Server 28.5.1 was available. The current wheel was extracted into an
ordinary feature-owned directory and mounted read-only into the existing Wright
Linux runtime image. The repository was not mounted. The container ran with no
network and wrote only to `/tmp`:

```powershell
docker run --rm --network none --entrypoint python `
  -v "D:\repos\wright\.local-run\process-validation-082\docker-wheel-20260916\installed:/opt/validator:ro" `
  -v "D:\repos\wright\.local-run\process-validation-082\docker-distribution-smoke.py:/tmp/docker-distribution-smoke.py:ro" `
  wright-dev-gate:e2f018eb -I /tmp/docker-distribution-smoke.py
```

Image identity:
`sha256:fc11b351d5f6ac259a8f64b6f9669f8b73d26d806cd39f3fc3241e9d7f1db3f8`
(`linux/amd64`, Python 3.13.15).

Result:

```json
{"installed_root":"/opt/validator","network":"none","profile":"structured-demo","python":"3.13.15","release_eligible":true}
```

The smoke loaded the structured, jig and heat profiles from `/opt/validator`,
verified core and workspace-service modules came from that mount, performed an
offline structured evaluation with the packaged service/readers and received a
release-eligible immutable assessment. This establishes installed-resource and
provider-neutral Docker compatibility; it is not a production image release or
a claim that optional CAD/CAE hosts exist in the base image.

## Native and optional-reader boundary

The supported local readers are Python-only bounded readers:

- `structured@1`: inline/JSON/CSV/text inspection;
- `step-seat-geometry@1`: read-only ISO-10303-21 seat circle placement
  inspection for the qualified jig scope;
- `thermal-field@1`: read-only CSV/JSON field, balance, refinement and
  selection inspection for the qualified heat scope.

They operate offline from installed package resources. T030 security tests
confirm that AgentCAD, build123d, CadQuery and OCP are absent from Wright runtime
dependencies, active base/dev Docker instructions and packaged reader imports.
The T028 producer demonstration owns `agentcad[mcp]==0.6.0` and
`build123d==0.10.0` in an explicit `uv run --no-project --isolated` selected-MCP
command. The base image remains free of those provider-specific dependencies,
as required by `docs/mcp-catalog/mcp-server-testing-process.md`.

Native file inputs still require formats covered by the packaged readers.
Unsupported family/native readers return a named blocked capability result, as
recorded in coverage map version 2. The Docker smoke does not promote those
states or imply physical qualification.
