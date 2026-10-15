# Casys CalculiX MCP usage guide

Updated 14 October 2026. GB10 ARM64 qualification is in progress; installation
and solver success are not yet established on this host.

## Identity and setup

Independent provider: [Casys-AI/mcp-calculix](https://github.com/Casys-AI/mcp-calculix).
Use the immutable 0.8.6 image
`ghcr.io/casys-ai/mcp-calculix@sha256:82ce8628279e03c8f492f156bb928e5703ea1fcb2d7c465826faf38f7389a778`.
The inspected registry index includes Linux ARM64 and x64. The documented image
supports `stdio` and `http`; HTTP uses `/mcp` on port 3015 and protocol 2026-07-28.
Mount STEP inputs read-only and a fresh writable recorded-run directory; configure
`CALCULIX_RUNS_DIRECTORY`. One active writer owns each recorded-run directory.
Use container-visible paths. Native solver dependencies belong to this selected
image, never Wright's base image. Credentials are not required for local solves.

## Existing evidence and engineering use

The [September qualification](../evidence/campaign-2026-09-12/calculix-recorded.json)
records a bounded static solve directly and through GatewayService, with exact
STEP/request/deck/mesh/native-log/result resources. It is historical evidence,
not current GB10 or complete Robot workflow acceptance. The existing probe is
`scripts/qualification/qualify-calculix-recorded.py`; its HTTP adapter is explicitly
qualification-only. Production stdio compatibility requires its own actual check.

Specify reviewed loads, supports, material and units (mm/N/MPa). Use mesh preflight
before the recorded solve. Preserve request identity, returned run identity,
STEP SHA-256 and every evidence resource hash. The existing field companion may
perform an output-only second solve; it must retain separate provenance and the
unchanged original evidence. No field expansion has been qualified on GB10 yet.

## Recovery and limits

After a timeout, inspect the same recorded run/request before deciding whether
anything can be repeated. Never infer an absent effect from a missing response.
Solver completion does not prove correct requirements, physics or engineering
acceptance. No physical action, review grant or generated geometry is supplied
by installation. Full Robot corrective CAD, coarse/fine sensitivity, force
balance and genuine review remain separate obligations.

## Follow-ups

No provider bug has been established or reported by this workstream. Keep exact
inputs and current schemas before attributing a failure. Update this guide with
actual GB10 startup/tool/solve results and retained evidence after each probe.

## GB10 ARM64 observed results, 14 October 2026

The pinned image started nonroot with dropped capabilities, read-only root and
input mounts, private tmpfs, a dedicated run directory and loopback-only port3049.
Actual versions: Deno2.9.6, Gmsh4.12.1, CalculiX2.21. Startup downloaded runtime
packages into private DENO_DIR; the shipped deno.lock is retained. This was not an
offline startup qualification.

A newly generated 20×10×4mm coupon completed a 1N static test directly and through
current-worktree GatewayService. Both returned1062 nodes/507 elements,67 nodes
per end selection,0.0007224248147886028mm maximum displacement and
0.6283308400200671MPa maximum von Mises stress. All nine evidence resources per
run passed byte-length/SHA-256 checks; DAT contained displacement and stress.
These are provider observations, not an independently validated design verdict.

See [ARM64 receipt](https://github.com/burhop/wright/blob/37746c7b20ee1146c55e67dc965aa2b0a9e9992b/prototypes/desktop-harness/calculix-arm64-evidence.json).
The existing probe initially hard-coded an older clean-client image identity.
Original evidence is retained; the receipt explicitly corrects that attribution.
The script now records observed client OS/architecture/Python instead of inventing
a container identity. This invocation used the feature worktree client, not a
clean Wright container or a canonical desktop workflow. Stdio, field expansion,
restart/reconciliation and engineering validation remain unqualified here.

## Native stdio recovery failure, 14 October 2026

Fresh sessions initialized protocol2025-11-25 with official Python MCP1.28.1 and
listed all tools. `calculix_run_get` then failed client output validation:
`'result' is a required property`. Native tools/list advertises an object with a
required `result` containing the union schema, while the observed response is
the unwrapped record. HTTP advertises the union directly. Do not infer stdio
compatibility from the successful HTTP test or disable output validation.

Two read-only attempts submitted zero solves. The second explicitly compared all
non-lock durable files before/after and found no changes. Stdio containers exited0.
The prior HTTP container was deliberately stopped after its solves completed;
Docker reports exit133, so graceful HTTP shutdown is not qualified. All selected
containers are stopped and preserved. See the
[reproduction receipt](https://github.com/burhop/wright/blob/37746c7b20ee1146c55e67dc965aa2b0a9e9992b/prototypes/desktop-harness/calculix-stdio-recovery-evidence.json)
and `prototypes/desktop-harness/calculix_recovery_probe.py`. No upstream report
was submitted, provider patch applied or runtime compatibility shim introduced.
