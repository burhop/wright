# Provider and runtime

`mcp-modelica` is a bounded solver provider. It selects server-owned qualified kits, validates typed
numeric overrides, generates the OMC script, runs OpenModelica, normalizes declared metrics, and
seals exact evidence.

It does not accept a `.mo` file, `.mos` script, shell command, solver path, or caller-selected
runtime.

## Qualified catalogue

| Kit                      | Scenario              | Claim                                                                                                      |
| ------------------------ | --------------------- | ---------------------------------------------------------------------------------------------------------- |
| `coffee-machine-v1`      | `heat-up-nominal`     | Bounded electro-thermal model with water/boiler capacity, ambient loss, heater, and thermostat hysteresis. |
| `linear-thermal-ramp-v1` | `linear-ramp-nominal` | Minimal balanced equation for multi-kit dispatch and real OMC conformance; not a physical thermal oracle.  |

Each kit owns its source, scenario, optional compiler-derived parameter schema, public parameter
mapping, conversions, result normalizer, and produced metric declarations. Registry admission
rejects ambiguous identities, duplicate metrics, invalid units, missing required metrics, and
undeclared observations.

The orchestrator does not know kit-specific CSV columns. A kit-owned versioned normalizer produces
the declared observations. If CoffeeMachine does not reach its target, the optional time metric is
absent rather than invented.

## Runtime and transport

Streamable HTTP is the default transport on port `3016`; native stdio is explicit. `--stdio` cannot
be combined with `--port` or `--hostname`.

The stateless HTTP transport implements MCP protocol `2026-07-28`.

The qualified image contains:

- OpenModelica `1.27.0`
- Modelica Standard Library `4.1.0`
- Deno `2.9.6`

Each currently shipped kit identity (`coffee-machine-v1@0.1.0`, `linear-thermal-ramp-v1@0.1.0`) is
qualified against that exact OpenModelica/MSL pair. The server probes the live runtime before
dispatch and fails closed with machine-readable `runtime_incompatible` when native host state
drifts. An unknown kit or version has no compatibility policy and fails closed as
`compatibility-policy-unavailable`; future identities are not implicitly qualified. Historical run
records are preserved; replay does not require the current image to match the sealed engine.

Its Docker inputs are pinned by digest, the MSL archive is hash-verified, and the build asserts the
actual Deno version. Native AMD64 and ARM64 CI runners build and smoke the final image separately;
the release does not reuse QEMU-produced solver evidence.

The HTTP endpoint should remain on loopback or behind an authenticated boundary. Mount only the
evidence directory at `/runs`; the image needs no Docker socket, CAD export volume, or runtime MSL
download.

## Store and capacity

The default evidence root is `./runs`, configurable with `MODELICA_RUN_DIR`.

- At most 20 persisted runs are retained.
- A result CSV is bounded to 5 MiB.
- Capacity exhaustion refuses a new run; the provider does not evict evidence silently.
- A global kernel lock counts incomplete runs and slot-reserving claims conservatively after a
  crash.
- Claims, ledgers, and artifacts are synced and atomically renamed before directory sync.

The store is strict bi-read: canonical historical v1 ledgers remain readable through frozen
contracts, while canonical v2 ledgers support recorded projections. Reads do not rewrite either
generation. An operator who removes run directories out of band must restart the provider because
there is no authorized archive/removal operation to project during a process lifetime.

## Security boundary

- Callers select only registered model/scenario identities and bounded public parameters.
- Source, scenario, solver scripts, commands, arbitrary paths, and runtime identities remain
  server-owned.
- Malformed or changed ledgers and resources fail closed.
- Raw solver diagnostics are not copied into stable business-error records.
- Resource hashes and solver completion do not authorize engineering conclusions.

Report vulnerabilities privately through the upstream
[SECURITY.md](https://github.com/Casys-AI/mcp-modelica/blob/62e26009a566d15b625493b0c3510bdd14b01c3b/SECURITY.md).

## Digital Thread relationship

This repository is a standalone MCP provider for approved-kit discovery, bounded OpenModelica
execution, persisted evidence, and MCP App rendering.

It is not the current execution authority inside `casys-digital-thread`. There, admitted source is
reopened and executed locally in a microVM by `compile.seal-admission@3` plus
`simulate.run-admitted-modelica@1`; the qualified-kit operation is also a Digital Thread local
microVM path. This repository's container must not be presented as a substitute for those registered
product operations or as evidence of the Workbench's active topology.

The viewer compatibility seam is narrower: Digital Thread may supply an exact registered read-only
session to this provider-owned App. That grants neither MCP authority nor solver credentials to the
whiteboard host.
