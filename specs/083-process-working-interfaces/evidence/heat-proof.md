# Heat-spreader proof progress

**Status:** actual CAD/solver chain, original validation and common-workspace
result inspection proved; complete tailored-interface proof pending.
**Checkpoint:** 2 October 2026 UTC.

The new example at `examples/process-interfaces/heat-spreader-sizing/` prepares a
connected source using the original three substantive stages and unchanged
`heat-spreader-sizing-01` assignment. It copies original input bytes with their
frozen digests and pins the original full 082 profile. Exact selected provider
IDs, fresh Wright tool/schema identities, native project path and solver mount
are supplied explicitly. No new provider executor or vendor wrapper is introduced.

The prepared definition connects authored CAD source to its native operation and
each actual exported STEP/measurement file to the recorded solver call. The
existing numerical operation checks reopened CAD measurements and STEP hashes
before rectangular meshing. It preserves both candidates, actual coarse/fine
fields, original analytical/refinement/balance thresholds, 45 °C decision limit,
`critic_approved=false`, current assessment and declared reviews.

`tests/test_process_interface_examples.py`: **7 passed**, 2.35 seconds, no skips.
Command:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_process_interface_examples.py --basetemp=.local-run/process-interfaces-083/t046-preparation-tests-006 -o cache_dir=.local-run/process-interfaces-083/pytest-cache-t046 --tb=short --junitxml=.local-run/process-interfaces-083/t046-preparation-tests-006.xml -q
```

The fixture project manifest and tool hashes establish **declarative checks only**.
No model, CAD host, solver, accepted live run, rendered browser, synthetic reviewer,
human engineering acceptance or physical operation was exercised by this suite.
It checks compilation and exact full-profile subjects, original-byte preservation,
missing-tool preflight, mount constraints, exact/fresh project identity, and
preservation of existing attempts. Ruff checks pass on the three added Python files.

Failed test roots remain private. Compiler requirements were retained: source IDs
were normalized, every staged input connected, direct tool references bound as
actual file dependencies, and original source-copy bytes preserved without newline
normalization. These fixes do not relax engineering checks.

Provider qualification is separately described in
[provider-qualification.md](provider-qualification.md). AgentCAD read-back is
qualified; its creation-response formatter warning remains explicit. The prepared
workflow retains the raw creation response and performs separate actual read-back,
without relabeling the response or blindly replaying creation.

Pending T046/T047: run the accepted prepared definition through Wright's normal
owner/API with fresh native providers and an exact isolated test policy; retain
real waiting/resume and current 082 assessments; compose/generate/update/save/reuse
both common and tailored views from actual outputs. These preparation checks do
not complete the engineering proof.

## Normal workspace and first live continuation

The normal production API, actual configured default model, fresh CAD project and
network-disabled selected solver container ran in an isolated workspace. Accepted
source creation, tool export, immutable inputs and process start used their normal
routes. The first run (`258ba276bbf34d3e970dbcd6be1061a8`) produced the original
thermal basis and persisted its declared review. A separately authorized synthetic
decision retained `actor=integration_test:083-private-digital-heat-004` and
`integration_test=true`; it is not human engineering acceptance.

The normal workspace entry exposed an editor defect: documented MCP file-dependency
objects were rejected as scalar settings. The editor now preserves and checks that
documented shape; runtime connection/file/tool checks remain intact. The actual heat
file then opened through Workflows and its named file chooser, with the common
working view in a workspace tab.

Its continuation initially returned an acknowledgement timeout while the backend
continued. Authorization was durable before a slower run-log publication, but the
acknowledgement callback came after publication. The callback now follows durable
consume immediately; dispatch still follows publication. Slow/failing-publication
tests retain exact-subject replay refusal and distinguish authorization from tool
acceptance/completion.

The first run subsequently failed before CAD source creation because its manual
test policy did not permit automatic document writes. No CAD version or solver
output was produced. Its consumed continuation was not replayed and its policy was
not changed. Owned providers and container were stopped gracefully. The failure is
retained in [failed-manual-attempt.json](../../../../artifacts/process-interfaces/083/20261002-heat-continuation/failed-manual-attempt.json).

A fresh exact automatic digital-test policy and workspace produced run
`86533be67a404058bc21a633146bd598` with accepted source digest
`4208d4194fcf8273e32262bf5c263ea51cc47fa67f2176f751005f869ed4466c`.
It again persisted a real basis-review wait. The synthetic decision was labelled
in the actual browser, the explicit confirmation was checked, and Continue process
returned **202** with the same run identity and visible Running state. Ten normal
workspace walkthrough checks passed, without mocked routes. This proves continuation
and progress, not completed CAD/solver work. The private browser trace retains
authentication headers and is not published.

This run subsequently wrote and fully reread its actual CAD source, then returned
`TASK_BLOCKED`: the authoring prompt also described exports belonging to the next
native CAD step. The source-writing step correctly declined to claim nonexistent
CAD outputs. No native CAD creation was executed. The example now explicitly assigns
source creation/checking to authoring and geometry/export/measurement to the next
declared tool step. A fresh isolated output/source attempt retains that correction;
the failed run and authored source remain unchanged.

Checks: 28 action/example tests, 89 affected approval/continuation tests, 47
frontend tests across three files, TypeScript and Ruff passed for the initial fixes.
Final checks retain 28 action/example tests and add 57 frontend tests across four
files; TypeScript and Ruff pass. Authoring-availability coverage adds visible
capability progress and lets
creation readiness resolve independently of saved-interface reads. The original
failed test/report roots remain retained. See [checked scope](../../../../artifacts/process-interfaces/083/20261002-heat-continuation/checked-scope.json).

Prepared definitions now remain proposals outside `workflows/`. The example
documents normal source-service acceptance and exact digest read-back; writing a
proposal alone does not establish accepted revision history. The original
assignment, full validation profile, engineering thresholds and protected campaign
records remain unchanged.

## Actual CAD, numerical analysis and current assessment

Fresh run `67abaa021ee44972a94e3c9cbaa3dbbe` used accepted source
`workflows/heat-spreader-sizing-live-default-model-002.workflow.wflow`, digest
`e1ddaf65a1890060ad546ccc9604ea6f2a3ebfcdb9f0de7d1183bdeaadf20bf9`.
Normal source/input/start services recorded immutable inputs. A real declared
basis wait and labelled synthetic decision preceded its one-shot continuation.
The policy actor was `integration_test:083-private-digital-heat-005-rerun-002`;
this is not human engineering acceptance. An initial extra request field was
rejected before action claim; the corrected request returned 202. No consumed
action or uncertain native operation was replayed.

The actual configured model authored the plate source. Independent AgentCAD
created native STEP exports, reopened them and measured the two rectangles:
100 × 40 × 2 mm and 100 × 60 × 2 mm. Separate read-back retained the provider's
creation-response limitation instead of relabelling its receipt. Independent
OASiS/scikit-fem consumed exact STEP hashes and measured dimensions and generated
actual coarse/fine tetrahedral conduction fields, CSV/VTU, balances and selection
evidence. Coarse meshes used 135 nodes/384 elements; fine meshes used
765 nodes/3,072 elements. This is the declared rectangular idealization, not
arbitrary STEP-topology import or physical qualification.

The actual fine-grid hot-end results were approximately **50 °C** for the 40 mm
candidate and **41.67 °C** for the 60 mm candidate. The first exceeds the original
45 °C limit. Analytical agreement, refinement and balance thresholds were
preserved; `critic_approved=false` remains explicit. The unchanged full 082
profile recorded **25 passing checks and one blocked review**, assessment
`assessment-c1cc56ecf12341938996ff0fa1c07b4e`. Its terminal diagnostic was
`PROCESS_VALIDATION_NEEDS_INPUT`; the synthetic basis decision does not satisfy
the profile's authenticated human review. Release eligibility remains false.

Actual outputs, exact assessment and checked scope are retained in
[the digital analysis artifacts](../../../../artifacts/process-interfaces/083/20261002-live-heat-analysis/checked-scope.json).
Assessment semantic digest and serialized-file SHA-256 are separate identities.

## Common working view and remaining model limitation

The recorder read-side previously replaced current continuation results with the
earlier wait's final result. It now reads current partial results for noncompleted
runs, including an explicitly empty map after invalidation, while preserving
completed final-result authority. No execution record or history is rewritten.
The normal isolated API was restarted on the same database without replaying
engineering work; its interaction now exposes all **18** recorded results.

A fresh real-workspace walkthrough passed **12 checks**: normal Workflows and
named accepted-file entry, common tab, same-run attachment, all outputs, exact
fine-grid CSV table, all 765 projected samples, full assessment evidence and
exact-result focus. One assessment checking several outputs now focuses the
requested result as well as its assessment. JSON evidence has a 1 MiB inert,
scrollable preview bound; prose retains 64 KiB, with download fallback above the
limits. Earlier incorrect harness selectors and the assessment-size stopping
report remain retained. See the
[workspace report](../../../../artifacts/process-interfaces/083/20261002-live-heat-analysis/workspace-walkthrough/report.html).
Raw authenticated traces remain private.

Three actual heat-interface generation attempts failed before a preview/build.
The latest bounded request through Wright identifies **UI_MODEL_TIMEOUT** for
the unchanged configured `gpt-5.6-sol`/Hermes model-only role. No broad tools,
global model change or automatic replay was used. Fixed timeout/auth/rate-limit
categories provide actionable messages without forwarding SDK exception text.
The failed job and
[safe timeout evidence](../../../../artifacts/process-interfaces/083/20261002-live-heat-analysis/ui-authoring-timeout.json)
are retained. The common results view remains usable; successful earlier generic
authoring smoke does not establish this tailored heat interface.

Checks after resume: **124** result/continuation/082 tests, **131** role/authoring/
API/contract tests, **35** focused adapter tests and **96** frontend tests passed.
The focused adapter suite overlaps the 131-test group. TypeScript and Ruff passed;
app ESLint passed with explicit config, while the external kit file is outside
that config's base path and was not lint-qualified by it. The new shared-assessment
focus regression first reproduced the wrong earlier-result focus, then passed.
Browser console/page/network error lists are empty in the successful report.

T046/T047 remain incomplete until tailored generation/preview/save/update/reuse
and the second engineering workflow are proved. Provider clean-container checks,
migration and final installed distribution also remain open. No protected
campaign subject, physical action, human acceptance, push or release was changed.
