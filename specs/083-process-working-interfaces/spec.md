# Feature Specification: Process working interfaces

**Feature:** `083-process-working-interfaces`  
**Prepared on:** `codex/prompt-to-3d-printed-part-demo`  
**Implementation branch:** `codex/083-process-working-interfaces`  
**Created:** 2026-09-30  
**Status:** Approved by goal submission on 2026-09-30; implementation active.

## Purpose and agreed scope

People build and inspect a process with Wright's existing flowchart, blocks,
source and inspectors. They carry out the job in a common working view or a
reusable interface tailored to that process. Both views refer to the same
accepted process, exact inputs, durable run, outputs, assessments and decisions.

Users ask Wright to create, preview, save and update a tailored interface using
its coding-agent role, initially the configured default LLM. Wright supplies
consistent components, styling, hosting and a scoped process client. The
interface presents the job; the existing backend executes it.

This feature delivers the complete experience, including actual AI generation
through Wright and two different engineering processes. It is not a UI-kit-only
milestone. Apply V1–V7 in the [platform vision](../../docs/design/workflow-platform-vision.md)
and the [process UI design](../../docs/design/process-apps.md). Manufacturing is
one reference process, not the platform's required lifecycle.

## User Scenarios & Testing

### User Story 1 — Prepare and carry out a process (Priority: P1)

An engineer opens a saved process in a workspace, switches to its common working
view, supplies the required choices, checks readiness, starts it and inspects
actual outputs. Progress remains visible, and closing/reopening the view retains
the same run. The engineer can inspect the exact contributing tool and block.

**Independent test:** A supported saved process completes its digital stages
through the common view without any generated interface.

**Acceptance scenarios:**

1. A required choice for a later step is missing: start is unavailable, with a
   reason and a link to the input. No tool work starts and no late popup repairs
   the omission.
2. An intermediate result will be produced upstream: readiness accepts that
   declared producer rather than demanding the result before execution.
3. The user starts a prepared process: a run identity is returned, activity and
   tool contributions update, and uploaded images have thumbnails.
4. The user closes the tab or loses the connection: execution remains backend
   owned; reopening attaches to the same run without starting it again.
5. A result or assessment is absent, stale or unsupported: the UI discloses the
   condition and provides a supported inspection/download or corrective action.
6. Cancellation is supported: an explicit request reports its actual outcome;
   closing the tab does not request cancellation.

### User Story 2 — Follow deliberate human interaction (Priority: P1)

A process runs without questions between declared interaction points. At a
declared review or structured-input step, it durably waits. The engineer sees
the subject/evidence, responds, and the same run continues when permitted.

**Independent test:** An isolated process reaches two declared checkpoints,
survives service reopening, and consumes each valid response at most once.

**Acceptance scenarios:**

1. A declared questionnaire is known before start; its later response is an
   allowed dependency. At that step the run waits with the declared fields.
2. An AI requests an undeclared clarification during unattended work: the run
   reports a diagnostic/failure according to policy, without inventing a form
   or silently defaulting engineering requirements.
3. A review refers to an exact output revision: a changed subject invalidates
   the response/action. The UI explains which evidence must be refreshed.
4. Two views submit the same response or lose its acknowledgement: reconciliation
   returns the recorded outcome; no duplicate continuation or external effect.
5. External availability changes: the configured bounded wait/recovery/failure
   policy applies, distinct from waiting for a human.

### User Story 3 — Have Wright create and maintain the interface (Priority: P1)

Inside Wright, the engineer requests an interface suited to the process. A coding
role uses Wright's API/kit instructions and the default model, shows authoring
progress, and creates a preview tab. The engineer saves it, uses it on another
run and later requests a focused update.

**Independent test:** Actual configured-model generation, preview, save, update
and reuse occur through Wright; reopening the saved interface requires no model
call or fresh build.

**Acceptance scenarios:**

1. The user selects Create interface: Wright resolves the coding role, model,
   instruction version and scope, records provenance and creates a draft.
2. Generated code has invalid bindings or build errors: bounded correction
   attempts receive diagnostics; failure remains actionable and common view works.
3. A generated preview opens: it is isolated, uses Wright styling, and cannot
   execute real engineering actions as a side effect of mounting.
4. The user saves and reopens: the same built revision is reused without model
   access, package installation or build tooling.
5. The accepted process changes: compatible bindings remain usable; required
   incompatible bindings disable mutations and offer common view/Update interface.
6. The selected platform cannot honor a requested model/scope override: Wright
   discloses that limitation rather than changing global model configuration.

### User Story 4 — Use one foundation for different engineering jobs (Priority: P1)

The engineer uses both an isolated printed-replacement-part preparation and an
isolated heat-spreader-sizing analysis. The interfaces suit their different jobs
and share the same client, kit, workspace hosting and backend authority.

**Independent test:** Both common and AI-created tailored views carry each
supported journey, using actual engineering outputs between substantive tools.

**Acceptance scenarios:**

1. Manufacturing preparation passes real geometry into repair/measurement and an
   existing independent slicer, exposes an actual package/toolpath representation
   and exact checks, and stops at its declared preparation review.
2. Thermal analysis passes actual CAD measurements into conduction analysis,
   compares candidates/fields and shows independent correspondence/balance checks.
   It has no mandatory printer, material-slot or camera controls.
3. Missing optional observations/viewers are disclosed; required missing evidence
   holds the applicable action. An attractive preview does not establish validity.
4. Historical prototype links remain inspectable after migration; old run records,
   campaign decisions and evidence are neither overwritten nor reapproved.

### Edge cases

- Invalid source draft while an accepted process/run remains open.
- Input/file/profile change between preparation and start, or review and action.
- Stale provider option list, changed destination or expired observation.
- Backend restart during an unknown external outcome; safe reconciliation only.
- No default model or authoring compiler available; common view remains usable.
- UI generation cancelled, malformed source, oversized assets or incompatible kit.
- Tab restoration referring to a removed UI/result or a different workspace.
- Unsupported source semantics, result format or provider capability.
- Multi-hour external operation with bounded polling, rather than a model call
  held open for hours.

## Requirements

### Functional requirements

- **FR-001:** Preserve the refined authoring experience and add working/preview
  views in the existing workspace document tabs, with exact block/result links.
- **FR-002:** Publish a versioned interaction description of inputs, outputs,
  evidence, declared pending interactions, observations and permitted actions.
- **FR-003:** Keep run-input values separate from the accepted process; persist
  an immutable, schema-validated input snapshot before dispatch.
- **FR-004:** Check every required supported-path dependency as supplied,
  explicitly defaulted, upstream-produced, declared human response or unresolved.
  Unresolved required dependencies block start with actionable reasons.
- **FR-005:** Backend-own execution and durable start identity; detach observation
  from execution and reconcile state after disconnect/reopen without replay.
- **FR-006:** Support an explicit structured-input checkpoint alongside existing
  review/approval checkpoints, exact-subject responses and same-run continuation.
- **FR-007:** Enforce no opportunistic runtime questions in unattended segments;
  expose declared human waiting, external waiting, failure and uncertainty distinctly.
- **FR-008:** Assemble a shared, accessible, themed client/UI kit and common view
  using Wright style and supported result representations.
- **FR-009:** Enforce process/workspace/run/UI/presentation scope on the server.
  Generated apps receive no admin/device credentials or arbitrary gateway authority.
- **FR-010:** Implement UI authoring through Wright's existing agent boundary,
  with a replaceable coding-role profile and versioned instructions; start with
  inherited default model and record the actual resolution.
- **FR-011:** Build bounded static interfaces using a fixed Wright toolchain;
  validate bindings/imports, isolate previews and save immutable source/build revisions.
- **FR-012:** Reuse saved interfaces across runs, support update/rollback, check
  compatibility and provide a useful common-view fallback.
- **FR-013:** Preserve exact result/profile/evidence/review identities and 082
  validation/rework rules; provider success or rendering cannot establish pass.
- **FR-014:** Expose only backend-permitted actions with reasons; use the existing
  approval/consume/reconciliation machinery for a bounded configured MCP action.
- **FR-015:** Keep device/vendor implementation external, using existing independent
  MCPs and ordinary qualification; retire active embedded prototype code after migration.
- **FR-016:** Prove both selected existing engineering jobs with fresh isolated
  runs, actual model/UI generation and substantive engineering tool handoffs.
- **FR-017:** Preserve 081 campaign and 082 evidence, reporting-branch ownership,
  historical source/run compatibility and useful saved-result access.
- **FR-018:** Ship client/kit/instructions/builder/asset runtime as installed
  resources; saved UI use needs no Wright source checkout or authoring compiler.
- **FR-019:** Surface readable progress, observations with freshness, file previews,
  failures and next actions; retain detailed diagnostics and trace identity on demand.

### Key entities

Accepted process reference; immutable input snapshot; readiness assessment;
interaction snapshot; checkpoint/response; saved UI revision/binding manifest;
coding-role resolution; authoring job; presentation scope. Existing runs,
EngineeringResults, assessments and action receipts remain their owning authorities.

## Success criteria

- **SC-001:** Both reference journeys work from the normal workspace entry in
  common and tailored views without an external browser window by default.
- **SC-002:** All intentionally omitted required pre-run choices are caught before
  dispatch; declared upstream outputs and human-response dependencies remain usable.
- **SC-003:** Two successive checkpoint responses, duplicate delivery, disconnect
  and restart checks preserve the same run and exactly one authorized continuation.
- **SC-004:** Actual model generation, preview/save, a focused update and a second
  run reuse are evidenced for each reference UI through Wright.
- **SC-005:** Required evidence, stale subject and incompatible-binding cases
  block the relevant action identically in common and tailored views.
- **SC-006:** Closing/restoring a tab and losing a start/response acknowledgement
  produce no duplicate engineering dispatch.
- **SC-007:** The two proofs identify actual tools, artifacts/digests passed,
  useful outcomes, checks and limitations; fixture tests alone do not meet this criterion.
- **SC-008:** Existing editor behavior and native/Docker installed-resource checks
  pass; saved UI reopening performs no model generation or frontend build.
- **SC-009:** No active vendor control/compatibility implementation remains in
  Wright's migrated path. Historic metadata/evidence stays accessible.

## Scope and assumptions

Version 1 supports the accepted source compiler's connected data/order graph and
bounded existing rework segments. Unsupported conditional/control semantics are
reported; this feature does not promise arbitrary new graph execution.

The manufacturing proof ends at digital preparation/review, using existing MCP
providers. Physical dispatch, printer/cloud compatibility, camera availability,
supplier submission and human engineering acceptance are separate evidence and
authorization. Generic permitted-action behavior is exercised with isolated
nonphysical operations and failure fixtures; that is not machine qualification.

The thermal proof retains the existing assignment and rectangular-link
idealization. A legitimate failed/uncertain assessment is allowed; bypassing
engineering review is not a way to complete the demonstration.

No new vendor integration project, new reporting dashboard, wholesale example
rewrite, universal screen language or separate execution engine is included.
Tests/evidence for this feature are required by this specification and are
authorized only when its implementation goal is submitted.
