# Heat-spreader proof progress

**Status:** live basis, declared waiting and normal-workspace continuation proved;
complete CAD/solver and tailored-interface proof pending.
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
