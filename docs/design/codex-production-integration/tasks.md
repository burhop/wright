# Production integration tasks

**Status:** implementation active; qualification pending. Parent: [production plan](../codex-production-integration-plan.md).
This is the sole implementation checklist. Historical implementation remains credited;
an unchecked task means the new delivery claim has not yet been qualified.

## Current checkpoint

- Planning baseline: `4f370caa9743f869f769f8c8e2332b6b63be438b`, 4 November 2026.
- Fresh isolated installed-artifact proofs only; no existing service, workflow, plugin or account changed.
- Goal submitted on 4 November. Active branch: `codex/codex-production-integration`.
- P01 baseline preserved; P02 screen/action map recorded; P03 automatic viewer observation FAIL on 0.38.1, offline diagnosis retained.
- P04/P05 implemented: packaged authenticated desktop composition, CLI, scoped option reads, plugin/skill and content-hashed editor. Boundary suite: 408 passed, 10 skipped; focused UI suite: 50 passed.
- P06 copied-state rehearsal passes without credentials/live jobs/grants. Installed results journey passes in Linux Chromium with a simulated host: fallback editor, exact image, producing-step availability, same-run return, narrow layout.
- Dependency-light managed install/start/status/doctor/MCP/stop/restart/update passes on Linux ARM64 (`light-manager-update/receipt.json`). The exact saved workflow survives. Existing live plugin remains 0.38.1; the isolated maintained candidate is prepared.
- Earlier Docker security scan passes after Debian apt 3.0.4 correction. Native update exposed a missing dependency boundary; corrected native suite passes (147, 7 skips). Fresh full gate/image needed. Mandatory engineering basis/reviews and Windows acceptance remain unresolved.
- Evidence: `.local-run/production-integration/`; no live instance changed.
- Preserve the prior plan and private/native evidence. Move this checklist into
  the accepted feature record if required; replace this page with a pointer then.
- During implementation keep this section short: exact candidate, completed IDs,
  current task, blockers, next action, and evidence index. Logs belong in evidence.

## Ordered checklist

| ID | Milestone / work | Owning boundary | Depends on | Completion evidence |
| --- | --- | --- | --- | --- |
| P01 | M0: Reconcile current dev/PRs, dirty work, installed plugin and active instances; record versions, hashes, capability inventory and migration inputs | Integration owner / native lifecycle | Accepted goal | No ambiguity about checkout versus installed/mounted build; preservation manifest |
| P02 | M0: Freeze supported stories and screen/action map from the accepted plan; classify required, optional and unsupported operations | Existing experience plan / UI | P01 | Empty, draft, ready, running, waiting, blocked, completed and changed-run screens; every visible control has a purpose and return path |
| P03 | M0: Finish one controlled file-viewer/display/download capability spike; select documented routes and explicit fallback | Desktop adapter | P01 | Protocol receipts separate from actual Windows observations; maximum 60 active minutes per capability; unresolved rows remain open |
| P04 | M1: Integrate desktop registration, composition and resources with packaged runtime and existing direct Codex profile | CLI/runtime, API, workspace service, integrations/codex | P01–P02 | Clean wheel install opens existing workflow/result without repository, private launcher or `/tmp` assets |
| P05 | M1: Preserve handoff repository, capability negotiation and version compatibility; consolidate source-of-truth health/diagnostics | Core/adapters/vault and runtime | P04 | Stale resources and incompatible client/backend diagnosed; no secret leakage or profile substitution |
| P06 | M1: Rehearse migration on copied state, then retire active prototype imports/entrypoints whose replacements pass | Existing storage and packaging | P04–P05 | Old source/drafts/history/files readable and unchanged; no credential transfer; audited active caller graph |
| P07 | M2: Finish simple chooser, named workspace, selected tools and explicit workspace-bound chat handoff | Workspace owner, native shell | P02/P04 | Both chat-first and UI-first routes reach the same intended workspace; duplicate names/ambiguous destinations handled |
| P08 | M2: Finish compact MCP management and readiness repair including add, reconnect, update, disable/remove and impact | Registry/OAuth/credential owners | P07 | Current status distinct from saved setup; missing/expired/denied/incompatible cases actionable; no implicit grants |
| P09 | M2: Finish files/viewer navigation and download feedback; distinguish duplicate filenames and internal records | Existing file/result/viewer owners, host adapter | P03/P07 | Visible preview, exact bytes, same-run return; actual Windows transfer pending until observed |
| P10 | M2: Qualify authoring and portability through normal entry: new/name/edit, typed ports, source, instructions, Undo/Redo, save/reopen, export/import, conflicts | Shared editor/source/transfer owners | P07–P09 | Existing editor capabilities preserved, accepted title searchable, portable instructions/dependencies intact |
| P11 | M3: Map exact handle stages/reviews/validators/provider bindings to supported canonical execution; resolve bounded missing semantics in their owners | Runtime/validator/registry | P05/P08/P10 | No weakened requirements or flattened rework; exact reviewed engineering basis; readiness before effects |
| P12 | M3: Complete desktop reasoning, helper/recovery, durable waits, cancellation and reconnection paths | Existing desktop reasoner and run owners | P05/P11 | Observable request evidence, duplicate/stale reply rejection, same-run continuation, no unknown-effect replay |
| P13 | M3: Run fresh bounded digital handle proof and one meaningful changed-input full rerun; present engineering results | Existing workflow and independent providers | P09–P12; real input/review availability | Actual tool outputs/measurements, invalidation and repeated review; old run preserved; no physical dispatch |
| P14 | M3: Prove shared mechanisms with existing Robot Tracking Diagnosis and regress retained block history | Same shared owners | P09–P12 | Different data/metrics/report journey, preserved tolerances, exact result navigation; no claim this proves handle strength |
| P15 | M4: Installed/platform/security/migration and host usability qualification, including actual desktop observation | Existing test/lifecycle owners | P06/P10/P12; P13–P14 for final acceptance | Complete acceptance matrix; Windows-local and Windows-to-GB10 separate; Linux/Docker evidence labeled |
| P16 | M4: Finish maintained docs, removal of obsolete active paths, compatible packaging/tests; run gates and consolidate CI fixes | Integration owner | Relevant P04–P15 | Exact tested head/artifact, complete current-head CI, release-readiness report; unresolved mandatory rows block readiness |
| P17 | M5: Authorized dev integration and later production release | Repository/release owners | P16 plus specific permissions | Dev merge separately from release; published artifact and native lifecycle verification per runbook |

## Work scheduling

Finish one useful slice before another redesign. P03 must not block independent
packaging or common-view work. Provider/login/review blockers on P11/P13 must not
block deterministic negative tests, P14 preparation or platform qualification.
Do not add new viewers, provider implementations, a general host framework or a
CI rewrite merely to make a task appear unblocked.

During an unattended goal, report completed IDs and concrete blockers at milestone
boundaries; keep ordinary in-turn updates brief. At the first hour checkpoint,
state what changed and whether the selected scope still fits the run. No fabricated
deadline guarantee. If all actionable tasks are exhausted, record the exact
remaining external dependency and stop rather than run tests in a loop.

## Evidence index format

Use existing private evidence roots and sanitized repository summaries. Each
receipt contains task/story, source commit or dirty patch digest, runtime/plugin/
UI resource identities, environment, workspace/source/run/step/result identities
where applicable, command/action, observed result and limitations. Never store
credentials, private sign-in URLs or invented model attestation.

For each task link: changed behavior; focused checks; installed evidence; actual
host evidence if required; retained failure; current limitation. A CI job receipt
does not replace an engineering assessment or a Windows screenshot/interaction.

Morning handoff: exact candidate and branch, completed/pending IDs, main remaining
blockers, three or fewer short user checks, and a few accurately captioned images.
