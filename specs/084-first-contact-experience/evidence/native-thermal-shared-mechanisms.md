# Installed thermal shared-mechanism check

On 23 October 2026, the installed native candidate from `86e76c50` at
`http://wright.localhost:18084/` was checked through its actual workspace UI.
The browser used the ordinary loopback cookie, with no HTTP mocks, injected
authentication, model inference or provider execution. This is bounded shared
mechanism evidence, not a new thermal engineering result or T017 acceptance.

The existing `handle-workspace` was retained. Its handle source and provider
configuration were not edited. The existing empty editor opened **Explore an
example**, where the heat-spreader example showed **Workflow illustration**,
**Reference workflow**, requested thermal inputs, solver effects, and honest
partial/required CAD and conduction-solver qualification. Exploration performed
no writes. **Create editable workflow** returned 201 and opened a separate source.

Exact subject:

- Workspace: `7e720c97-6048-4a50-944f-2376186db36b`.
- Session: `wright-local-3751adae-a1b3-4927-a3fd-b33f56510f20`.
- Source: `workflows/thermal-shared-check.workflow.wflow`.
- Raw workflow ID: `t1e060f4dc9e97480b5172f9b`; API qualified ID:
  `workflow.t1e060f4dc9e97480b5172f9b`.
- Template: `heat-spreader-sizing`, version `1.0.0`; original source digest:
  `b45585c61158350feb5c10bf8d8f841ad1b5e951be8873c0208d1585c1e16f1e`.
- Original template layout digest:
  `793d40e8261e33109e8f4102c4e7b3c77a956b6e72c2ddb804512f5649142011`.
- Initial accepted source digest, definition/storage revision 1:
  `2547bf5bea07a87b21c3d365e864552ba995c87fd2da8e6de335bc4024ff433a`.
- Revised accepted digest, definition/storage revision 2:
  `c6f1f999c4e173409ec59353c42a00d968eb1304064ea4f05020780e104cac73`.

The only user edit was the displayed name, from **Conduction Heat-Spreader
Sizing** to **Conduction Heat-Spreader Sizing — shared view check**, applied with
Enter and Save in the existing editor. The editor normalized source formatting
(header comments, blank lines, JSON key order and identifier quoting), so the
whole source is not byte-identical except for its name. Parsing the two exact
saved sources with the owning source parser proves every section, identifier,
engineering instruction string, setting, port and connection unchanged except
the workflow `name` value. No original catalog or engineering fixture was edited.
The backend changed `reference` to `revised`, retained original provenance, set
qualification/configuration flags to unknown, and required current preflight.

The actual common view exposed a real blocker. Its interaction read returned
HTTP 422 `READINESS_UNSUPPORTED`:

> Define geometry, material, load, and boundaries needs a supported execution type.

The compiler rejects the reference's `review` / `ai_then_engineer` task without
a declared executable interaction. The following configured-tool blocks are
also unbound. The first error occurs before model/tool readiness; therefore this
check does **not** establish a current missing-tool response. Prepare was absent,
and no preparation, run or review was submitted. The common view displayed a
generic recoverable service error because the process client currently reads
`detail.reason`, while the installed API's normal error handler returns the
validated reason in `details.reason`. A bounded client compatibility fix now
accepts that schema-validated reason while retaining `detail.reason` support.
Malformed reasons and raw diagnostics retain the generic safe fallback. The
backend compiler and its rejection are unchanged. The first capture predates
this fix; the installed follow-up is recorded below.

Closing and reopening the actual working-view tab retained the exact revised
source digest and reproduced the same honest failure. Both tabs were closed
after capture. No generated interface/presentation was created. The browser's
only mutations were normal workspace activation, the thermal instance creation,
and a PUT for the thermal source. Background model discovery returned 503 during
this capture; subsequent SDK repair, if established elsewhere, does not change
these retained observations.

Retained local evidence:

- `artifacts/first-contact/084/native-thermal-shared-001/`: browser harness,
  sanitized report, exact before/after sources, source-comparison JSON and seven
  screenshots, including exploration, accepted revision, failure and reopening.
  The harness passed its scoped assertions; this does not mean readiness passed.
- `artifacts/first-contact/084/native-thermal-failure-detail-002/`: one additional
  read-only request captured the exact structured 422 error and trace identity.
- Focused command:
  `.venv/bin/python -m pytest tests/test_process_interface_examples.py::test_heat_source_preserves_original_stages_and_exact_full_validation -q`
  passed **1 test in 2.60s**. It preserves the original seven-stage thermal
  fixture and complete validation requirements; it performs no engineering
  execution. That full scenario fixture is distinct from the catalog's shorter
  reference template, and this evidence does not conflate them.
- Focused process-client command:
  `npm --workspace apps/web run test -- src/services/process-client.spec.ts -t 'validated backend reason|malformed normalized error reason|arbitrary raw HTTP failures|lost start acknowledgement'`
  passed **7 tests in 1.34s** (75 unrelated tests skipped). It covers both error
  envelopes, malformed normalized reasons, non-disclosure of raw diagnostics and
  the existing uncertain-start/no-automatic-retry behavior. Diff whitespace
  validation passed for the two changed implementation/test paths.

After independent review, the two changed client/test files were copied with
verified hashes into the isolated locked frontend build. The owned interactive
`/wright update 0.1.9` installed candidate 2, runtime
`2bec53381fab3113b68afb5d`; wheel SHA-256
`bd2535b153737b29ac6483842d14c236003c953953d533660a5ae2bac0fce739`, UI manifest
SHA-256 `07316ab831ec001f94b9660ad316a8db4951f604946def09e3a1b2fa97ca694c`.
Lifecycle/package evidence remains in
`artifacts/first-contact/084/native-update-002.json` and
`native-candidate-build-002.json`.

`artifacts/first-contact/084/native-thermal-reopen-003/` passed the actual
installed follow-up: the exact thermal revision/digest persisted; open and
close/reopen displayed the backend's actionable `READINESS_UNSUPPORTED` message
and correction. HTTP 422 remains correct. No preparation control was fabricated,
and only ordinary workspace activation was submitted. Both process tabs closed
normally. The reopened screenshot was visually inspected.

Exploration and failure screenshots were visually inspected. Root reviewed the retained report and reopened screenshot and closed T017 for
this bounded shared-mechanism scope: preserved source/requirements, reference-to-revised
setup state, ordinary workspace/common-view fallback, exact error projection and
reopen without dispatch. This reference is explicitly unqualified for execution;
a configured thermal run, new computed fields, physical temperatures and user
acceptance have not been claimed. Later changes to these shared mechanisms
invalidate the relevant checks and require focused follow-up.


## Candidate11 follow-up after the shared file-locator correction

The [installed follow-up004](../../../artifacts/first-contact/084/native-thermal-reopen-004/README.md) passes on runtime `654eb603cac58bba76b6dfcb` with the matching candidate11 client. The exact existing revision2/source digest remains unchanged; first open and reopen both display the expected HTTP422 `READINESS_UNSUPPORTED` reason and actionable correction. Both tabs close normally. Only ordinary workspace activation occurs. This preserves the bounded fallback/reopen scope after the shared contract change; it does not establish thermal execution, a long-artifact thermal run, provider qualification or a new engineering result. Root inspected the reopened screenshot and verified all five manifested file hashes.
