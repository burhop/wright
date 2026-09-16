# Sensor/fan harness: selected WireViz execution

The selected implementation uses real WireViz 0.4.1 / Graphviz 2.42.4 and three
fixed engineering MCP operations. This explicitly recorded Splice alternative
needs no Splice account and makes no claim to have produced Splice output.
All three original task IDs, both original order connections, and the engineer
review remain in the actual API-created instances. Research precedes that review;
the original generation and verification steps follow it; final collection is last.

The declarative binding is
`tests/datasets/engineering-workflows/bindings/sensor-fan-harness.json`; the preparer
is `scripts/prepare-harness-dataset-campaign.py`. Original profiles, human prompts,
images, company context, and all CSVs are staged byte-for-byte. Authored operation,
MCP and source-selection files are also immutable enrolled inputs. None of the
input packs contains a precomputed harness, diagram, BOM or electrical result.

## Selected setup and qualification

Following `docs/mcp-catalog/mcp-server-testing-process.md`, a clean Intel Linux
Wright container used image
`sha256:512b001cbffd0551969630eaf618d9d4fb72987bdfb6422d9d444d8ad2e8ee73`.
Only this selected container received Graphviz, Poppler and its isolated Python
environment. The base image and native Hermes environment were unchanged.

```sh
apt-get update
apt-get install -y --no-install-recommends graphviz poppler-utils
uv python install 3.12
uv venv --python 3.12 /tmp/harness-env
uv pip install --python /tmp/harness-env/bin/python wireviz==0.4.1 mcp==1.28.1 pypdf==6.9.1
```

The persistent selected container `wright-081-harness-runtime` mounts only the
disposable demo workspace at `/workspace` read/write and repository `scripts`
at `/operations` read-only. It exposes no ports or physical devices. The normal
API registered, installed, demo-enabled and activated server
`e73f0c6c-01a5-4ded-93d2-b7c3e65408ce`, with default enabling false:

```text
docker exec -i -e PYTHONPATH= -e WRIGHT_HARNESS_WORKSPACE=/workspace
  wright-081-harness-runtime /tmp/harness-env/bin/python
  /operations/harness_engineering_mcp.py
```

The three exact tools are `retrieve_harness_component_records`,
`generate_harness_package`, and `verify_harness_package`. Paths are confined to
one declared attempt, the executed operation source must match its staged hash,
and output directories must be fresh. There is no arbitrary shell, network URL,
procurement, energizing, controller or physical-device operation.

Actual direct MCP initialize/list/call qualification ran all three original packs:
14 primary records retrieved per case, real WireViz YAML/SVG/PNG/native BOM
generated, expanded BOM/pin/cut/assembly files written, and independent observations
produced. Probe 006 contains the final source; earlier attempts retain diagnostics.
Native Wright `GatewayService` initialization/discovery/call also successfully
re-ran the case 03 verifier against actual native files. This is selected backend
and native gateway evidence, not a claim of complete public catalog qualification
or a Hermes-facing gateway facade test.

Local evidence: `.local-run/feature-081-live/harness-campaign/probe-006/evidence.json`
and `gateway-evidence.json` in its parent. Four opt-in fault-injection tests passed
against those actual artifacts, covering unchanged outcomes, altered native pins,
incorrect shared current and changed primary records. Three fast preparer tests
passed. The actual native case 01 PNG was visually inspected.

## Engineering basis and limits

Exact sources are listed in `scripts/harness_component_sources.json`. Each actual
run retrieves and hashes their bytes again; engineering facts are indexed to
those records, with unresolved application facts left unknown. The selected parts
include [Amphenol AT housings](https://www.amphenol-sine.com/pdf/datasheet/AT06-6S.pdf),
[machined size 16 contacts](https://www.amphenol-sine.com/pdf/catalog/A-Series-Contacts.pdf),
the [AUTK-16 tool](https://www.amphenol-sine.com/pdf/datasheet/AUTK-16.pdf),
[Alpha 3057 wire](https://www.alphawire.com/en/products/wire/hook-up-wire/premium/3057),
[Belden 8719 shielded pair](https://catalog.belden.com/techdata/EN/8719_techdata.pdf)
and [WAGO 221-413 branch terminals](https://www.wago.com/gb/installation-terminal-blocks-and-connectors/splicing-connector-with-levers/p/221-413).

All topology and installed lengths come from the uploaded schedule. Separate
50 mm power pigtails prevent multiple wires sharing one crimp; their lengths are
deducted from downstream routes so original root-to-load distances are preserved.
Cut lengths include explicit service length and sourced termination allowances;
twisted-pair cable is cut once. Unmodified manufacturer drawing images provide
the mating-face reference alongside the logical pin diagram. Actual shield
cables appear in native WireViz output; detailed shield-end handling is retained
in the generated shield schedule and assembly instructions.

The independent checker inspects actual emitted YAML connections, detects added
loops and changed pins, checks customer nets/reserves, conserves route lengths,
solves shared continuous/startup currents, and calculates copper voltage drop
using sourced conductor resistance. It separately retains the uploaded initial
assumed-wire calculation. Nominal ratings are compared to supplied requirements;
contact and splice resistance is never assumed zero. The three actual probe
maximum copper drops were approximately 0.0222, 0.3432 and 0.2779 V against the
0.72 V copper budget. These observations are not certified electrical validation.

All three reports retain `hold_for_missing_application_evidence`: loaded-contact
derating, installed bundle conditions, contact/splice resistance, exact fan and
transmitter interfaces, final chassis/shield termination hardware, retained splice
enclosures and service reach remain unresolved. The BOM identifies base wire part
numbers and required colors; procurement put-up suffixes are not invented.
No physical continuity test or energizing took place, and dashboard content-validity
credit remains zero.

## Campaign handoff and corrected export declarations

Harness attempt 001 was saved/enrolled but never dispatched. Before execution,
the campaign exporter correctly exposed that copied operation source is provenance,
not newly generated engineering output. The binding now excludes those source
copies from required deliverables; the backend may retain them as ancillary
provenance and the original pinned input remains intact.

Use only `.local-run/feature-081-live/campaign-execution/harness-attempt-002.json`
for the corrected three cases. It preserves attempt 001 source/grants and creates
fresh sources and confined output roots. No direct qualification probe counts as
a canonical dataset run; the parent campaign runner dispatches these instances.

Observed setup problems were resolved in the selected operation: Belden's HTTP
gzip body is decoded before PDF extraction, native WireViz cavity numbers use
integers, customer CSV aliases are normalized, and per-step required artifacts
stay within the canonical limit of 16. These fixes did not modify shared runtime
code or relax the engineering release holds.
