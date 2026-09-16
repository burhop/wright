# Approved Modelica kit prerequisite, 2026-09-12

**Current status:** a separately identified selected kit has been implemented,
qualified, installed and bound to all three actual template instances. See the
[selected kit report](modelica-selected-kit.md). Its canonical cases are enrolled
and were not dispatched by this prerequisite task.

**Historical inspection outcome for the unmodified upstream kit:** all three
heater datasets were blocked before dispatch. The findings below describe that
initial source-only inspection, before the separately authorized extension.

The public source fetched directly from GitHub is version **0.6.5**, commit
`62e26009a566d15b625493b0c3510bdd14b01c3b`. The cached web search README describing
0.2.0 is stale. Exact source snapshots, original MIT license, SHA-256 and source
URLs are in [contract-inspection.json](../../../../docs/mcp-catalog/evidence/modelica-2026-09-12/contract-inspection.json).

## Exact contract gaps

The approved `coffee-machine-v1@0.1.0` kit exposes these public bounds:

| Parameter | Unit | Inclusive bounds |
|---|---|---|
| initial_water_temperature | degC | 0–45 |
| ambient_temperature | degC | -10–50 |
| heater_power | W | 500–3000 |
| water_mass | kg | 0.1–3 |
| boiler_heat_capacity | J/K | 100–5000 |
| heat_loss_conductance | W/K | 0.1–50 |
| setpoint_temperature | degC | 70–110 |
| hysteresis | K | 0.1–20 |

Case01 requests 350 W and a 90 J/K vessel, outside reviewed bounds. Case02
requests a 400 W candidate, also outside bounds. Case03's listed power and
capacity values fit. All cases request independent electrical-to-thermal
efficiency (0.92/0.93/0.94); the model sends `heaterPowerRated` directly to an
ideal thermal source. A reviewed conversion could map electrical input to
thermal power and back to electrical energy, but that conversion is not an
independent exposed kit parameter and would not repair the other gaps.

`heat-up-nominal` fixes start=0 s, stop=900 s, 900 output intervals, DASSL,
target=90 degC. The simulate and resumable submit schemas are closed and expose
no stop-time, solver-timestep or tolerance override. The datasets request
300/600/700 s stops, and every original workflow requires a tighter-timestep
rerun. Decimating a CSV or changing the output sampling density would not prove
solver timestep convergence. This is the decisive all-case blocker.

Source: [kit definitions](https://github.com/Casys-AI/mcp-modelica/blob/62e26009a566d15b625493b0c3510bdd14b01c3b/src/kits/coffee-machine.ts),
[closed input schemas](https://github.com/Casys-AI/mcp-modelica/blob/62e26009a566d15b625493b0c3510bdd14b01c3b/src/tools/kit-input-schemas.ts),
[scenario](https://github.com/Casys-AI/mcp-modelica/blob/62e26009a566d15b625493b0c3510bdd14b01c3b/scenarios/heat-up-nominal.json).

## Runtime and evidence findings

`docker buildx imagetools inspect ghcr.io/casys-ai/mcp-modelica:0.6.5` succeeded
on Docker28.5.1. Public OCI index is
`sha256:326784ce8ac6608ac7ec9047b4c5e13643bf94a6cdb417917a4131e465db0d4e`;
linux/amd64 manifest is
`sha256:4e896acb15761c71f52758a983021e1b9f575a39c2257f6bde22ae9e68f8c256`.
No image was pulled or started after the semantic blocker was established.

The selected sidecar contains OpenModelica1.27.0, MSL4.1.0 and Deno2.9.6,
supports HTTP at `/mcp` and explicit native `--stdio`, and needs only its own
`/runs` evidence mount. No Wright base-image change is needed. Current local MCP
SDK1.28.1 accepts protocol versions through2025-11-25; upstream docs advertise
2026-07-28. Actual negotiation was not exercised, so transport/gateway
compatibility remains **unqualified**, not failed or passed.

Version0.6.5 does provide exact CSV retrieval: use `resources/read` on the URI
declared in the sealed ledger (`casys://modelica/runs/<run-id>/<artifact>`), which
rechecks bytes/SHA-256. The resumable2.1 manifest→template→submit→request-get
flow supports caller request identity and crash-safe readback. Its
`modelica_simulation_series_get` returns at most128 samples and cannot replace
the complete CSV for independent energy integration. Capacity remains20 runs,
5 MiB per CSV, with no silent eviction. These are inspected contracts, not
live retrieval evidence. See [upstream contract](https://github.com/Casys-AI/mcp-modelica/blob/62e26009a566d15b625493b0c3510bdd14b01c3b/docs/contracts-and-evidence.md).

## Reproduction and next action

```powershell
git clone --depth 1 https://github.com/Casys-AI/mcp-modelica.git .local-run/feature-081-live/modelica-prerequisite/source
.venv/Scripts/python.exe scripts/inspect_modelica_dataset_compatibility.py --source .local-run/feature-081-live/modelica-prerequisite/source --datasets tests/datasets/engineering-workflows/scenarios/water-heater-sizing --output docs/mcp-catalog/evidence/modelica-2026-09-12
docker buildx imagetools inspect ghcr.io/casys-ai/mcp-modelica:0.6.5
```

A separately reviewed selected-kit extension must qualify the lower power and
capacity ranges, explicit efficiency mapping, and independent bounded solver
step/tolerance variants. Give that extension a new immutable kit/scenario
identity. Then run the clean Intel Linux Wright→selected sidecar protocol,
backend simulation, exact CSV retrieval and gateway probes before enrollment.
Do not rewrite this kit's source under its existing identity, substitute a
free-form ODE, drop candidate settings or bypass the third stage.
