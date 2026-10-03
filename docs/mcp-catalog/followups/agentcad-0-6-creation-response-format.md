# AgentCAD 0.6.0 creation response formatting

**Status:** published 0.6.0 defect retained; an existing unreleased pinned upstream
revision is separately qualified. No Wright workaround or catalog promotion.
**Source:** https://github.com/jdilla1277/agentcad, installed version 0.6.0.
**Evidence:** [fresh Linux qualification](../../../artifacts/process-interfaces/083/20261003-agentcad-fresh-clean-partial/README.md).

## Reproduction and environment

From the neutral Wright Linux/amd64 image install selected dependencies with:

```text
uv run --isolated --python 3.12 --with "agentcad[mcp]==0.6.0" --with build123d==0.10.0 --with numpy==2.5.2 --with "mcp[cli]==1.28.1" python -c "import agentcad,build123d,OCP"
```

Initialize a fresh disposable project with agentcad init --build-dir build.
The script imports build123d.Box and calls show_object(Box(2, 3, 4)). Start
the provider's standard python -m agentcad.mcp entry. Call run once with exact
project/script paths, output=clean-probe, build_dir=build, preview=false,
view=false and diff=false. Exact launch/configuration is retained in the evidence.

## Observed boundary

Native STEP/meta commits successfully, while MCP isError=false contains JSON
status=error and combined progress/success JSON. Strict creation qualification
rejects the receipt. Installed _invoke/_format_result consumes Click's combined
output; the same issue occurred on Windows. A separate read-only measure of
the exact STEP succeeds (2/3/4 mm, volume 24 mm3, valid deliverable). No creation
was repeated and no physical operation occurred.

## Next action and ownership

The independent provider should separate structured MCP output from progress
and preserve committed output identity on formatting failure. Qualify a corrected
provider before relying on creation-success receipts. Wright preserves error and
output evidence and reconciles uncertainty without recreation. No bundled
formatter/protocol workaround, public promotion or upstream submission is planned.
This local follow-up authorizes no push, release or physical operation.

## Qualified upstream continuation — 3 October 2026

Existing upstream revision `2a377583d9d250971a584acb7b5ac6e2a75737c0`
separates CLI stdout/stderr and isolates protocol stdout. A fresh selected Linux
install records matching source SHA, official 11-tool discovery, exact gateway
schemas, one successful creation and one successful exact-STEP readback. The
2×3×4 mm/24 mm³ output remains byte-identical through measurement. Both exact
new containers are stopped. No provider source was modified or native failed
creation retried. See [pinned qualification](../../../artifacts/process-interfaces/083/20261003-agentcad-pinned-upstream-qualified/README.md).

The inspected PyPI version is still 0.6.0. Use the recorded Git pin to reproduce
this selected qualification; do not assume the package version string identifies
the corrected source. Prior failed release receipts remain unchanged and must
not be rewritten as passing. Promotion and future-release qualification remain
separate operations.
