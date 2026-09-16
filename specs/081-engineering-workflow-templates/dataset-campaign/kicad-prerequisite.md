# KiCad selected campaign prerequisite, 2026-09-12

**Installed and backend tested; campaign drafts prepared, no dataset dispatched.**
Selected normal API server is `c488c91b-8310-4cf1-9198-6e5f0342202f`, with18
discovered tools. Container `wright-081-kicad-runtime` uses image
`sha256:eaaf00be76c3750bf5d0525f3637d8cf630232f13a249709a4adbdb2e12beda7`.
It has no network and mounts only the three PCB attempt001 inputs read-only and
artifact directories writable. The Wright base image is unchanged.

## Selected dependencies and actual checks

Source is [blwfish0.13.0](https://github.com/blwfish/kicad-mcp/tree/bcc6f11de92e5f47cb7dde1d24565f7779b2fbed),
commit `bcc6f11de92e5f47cb7dde1d24565f7779b2fbed`, MIT. Fresh Intel Linux Wright
base `sha256:512b001cbffd0551969630eaf618d9d4fb72987bdfb6422d9d444d8ad2e8ee73`
had no KiCad. The selected image adds KiCad `9.0.2+dfsg-1`, standard symbol and
footprint libraries `9.0.2-1`, and the upstream frozen Python dependency graph.
System `/usr/bin/python3` provides actual pcbnew, separate from MCP Python3.13.

Five DRC-history `print` diagnostics corrupted stdio in the old qualification.
The selected patch sends those exact diagnostics to stderr, leaving DRC
execution, reports, severities and history persistence unchanged. The patch
requires the reviewed source SHA-256 and fails on drift. An early local attempt
exposed CRLF handling in the patch; normalizing line endings before the import
insertion corrected it. Failed prerequisite attempts remain in the local log.

[Probe evidence](../../../../docs/mcp-catalog/evidence/kicad-2026-09-12/qualification.json)
records real initialize/initialized/list calls, library search, a40×30mm native
board with two resistor footprints and nets, native schematic authoring,
repeated MCP DRC/history followed by tools/list, and Gerber/drill export.
Intentional defects produced two unconnected DRC items and two native ERC
errors. FreeRouter then routed the actual board; a subsequent native DRC
reported zero violations and zero unconnected items.38files were produced;
native files, complete rule reports, schemas and fabrication ZIP are retained
with hashes. This tiny prerequisite is **not any of the thirty dataset runs**.

FreeRouter [2.2.4 release JAR](https://github.com/freerouting/freerouting/releases/tag/v2.2.4)
SHA-256 is `f5ed374182900ccc78e473518bbb9f6b869f4a07159495f663a76f52bb10523b`,
matching the public GitHub release asset digest. Its classfile major69 requires
Java25, despite older upstream guidance mentioning Java17. Selected Temurin
JRE25.0.4+7 comes from official OCI index
`sha256:15090d159279e5c158473eccb48cd87f57b3e3a47511a797eb5a7a7ea6f86b0f`.
Routing ran headless with upstream analytics-disabled arguments and Docker
network disabled.

## Native rule-report extension

Upstream `schematic(operation='validate')` uses kicad-sch-api; it is not proof
that native KiCad ERC executed. Selected `native_rule_check(kind,source_path,
report_path)` explicitly runs only `kicad-cli sch erc` or `kicad-cli pcb drc`.
It confines native input/new JSON output to `/work`, rejects overwrite and
wrong file types, checks source hash before/after execution, preserves exact
native JSON bytes and all issues, and returns file hash/size/source identity.
Eight focused tests pass, including path escape, stale output, CLI failure,
missing report and source mutation. The live probe exercised both operations.
Report creation never implies zero errors.

## Reusable setup

Files are [Dockerfile](../../../../scripts/kicad_campaign/Dockerfile),
[hash-guarded stderr repair](../../../../scripts/kicad_campaign/repair_drc_stdout.py),
[native check](../../../../scripts/kicad_campaign/native_rule_check.py), and
[probe](../../../../scripts/kicad_campaign/probe.py). Build context must contain
the pinned source checkout, verified JAR and these selected helper files.

```powershell
git clone https://github.com/blwfish/kicad-mcp.git .local-run/feature-081-live/kicad-prerequisite/source
git -C .local-run/feature-081-live/kicad-prerequisite/source checkout --detach bcc6f11de92e5f47cb7dde1d24565f7779b2fbed
# Obtain the2.2.4 JAR from the release above and verify its stated SHA-256.
Copy-Item scripts/kicad_campaign/Dockerfile,scripts/kicad_campaign/repair_drc_stdout.py,scripts/kicad_campaign/native_rule_check.py,scripts/kicad_campaign/server.py .local-run/feature-081-live/kicad-prerequisite/
docker build --platform linux/amd64 -t wright:kicad-campaign-selected-20260912 .local-run/feature-081-live/kicad-prerequisite
```

Register/start explicitly with `scripts/install-kicad-campaign-mcp.py --execute
--workspace-root <actual-workspace> --output <receipt.json>`. It uses normal
register/install/workspace-enable/activate APIs and refuses to replace an
unrecorded container. Inspect a changed build before updating its pinned image
constant. The persistent container runs only `sleep infinity`; each gateway
MCP session starts the selected provider via `docker exec`, preserving
schematic state within that session.

## Canonical binding handoff

`scripts/prepare-pcb-dataset-campaign.py --workspace-root <workspace>
--draft-root <drafts> --server-id c488c91b-8310-4cf1-9198-6e5f0342202f` stages
human files and compiles all three cases. Current actual-workspace staging and
drafts are under `.local-run/feature-081-live/pcb-ready-drafts-utf8`.

The five-step graph preserves all original semantic stages:

1. Original `capture_electrical_basis`: supplied net table, profile, sketch,
   constraints and unresolved datasheet assumptions.
2. Exact local-review approval, using current scoped manual/test-auto policy.
3. Original `author_pcb`: real library search, native schematic/connectivity,
   board outline/placement and net assignment.
4. Actual FreeRouter routing and native DRC/audit. The board is registered as a
   final file only after routing; its earlier mutable authoring state is not
   misrepresented as an immutable final artifact.
5. Original `verify_and_export`: independently compare nets/dimensions,
   native ERC/DRC, reject unreviewed errors, then actual BOM/Gerber/drill exports.

Before canonical dispatch, use the normal template-instance API, then rerun
preparation with `--scenario <id> --instance-source <returned-source>` and a
fresh draft directory to retain exact instance IDs/provenance. Save through
normal source edit APIs and enroll current source/input/tool schema digests.
Use the selected tool names in the declarative binding JSON; no template-ID
runtime executor exists. All file outputs are declared workspace-relative;
tool paths use `/work/` plus that same relative path through confined mounts.

Expected BOM is `design_bom.csv`. Native Gerber Protel outline is
`design-Edge_Cuts.gm1`; the three manifests now accept this exact alternative
while retaining prior valid extensions. [Fingerprint change record](../../../../docs/mcp-catalog/evidence/kicad-2026-09-12/dataset-format-amendment.json)
records the reason and actual probe. Enroll the updated fingerprints only.

No public catalog readiness promotion, full renewed gateway qualification,
dataset completion or correctness-validation claim has been made. The next
bounded step is a real canonical run through the current gateway, followed by
same-run evidence export. Current registration/discovery does not by itself
prove all18tools through the canonical gateway or complete the engineering
datasets. No fabrication order or physical device operation is authorized.
