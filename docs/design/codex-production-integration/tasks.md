# Production integration tasks

**Status:** implementation active; qualification pending. Parent: [production plan](../codex-production-integration-plan.md).
This is the sole implementation checklist. Historical implementation remains credited;
an unchecked task means the new delivery claim has not yet been qualified.

## Native desktop profile qualification — 5 November

The installed product at `df6ea4c4` passes the normal pre-push gate and its
owned-runtime update/readback checks. Full gate 15 ran on parent `2114dd23`;
its generated assets were committed unchanged and the final wheel is byte-identical
to the installed qualified artifact. These are distinct receipts, not a new full
suite run on the descendant commit.

P15 now adds the existing desktop MCP lifecycle harness to the native Windows,
Linux and macOS candidate matrix, alongside required Hermes checks. An exact
local execution of that CI step passes on Linux ARM64: separate dependency-light
manager, installed runtime, authenticated connection, exact packaged viewer,
save/reopen and restart with identical source. No engineering runs occurred.
Evidence: `desktop-native-matrix-local/dist/desktop-native-Linux/receipt.json`.
Native Windows/macOS desktop-profile results remain pending this correction's CI;
actual Codex rendering, file delivery and chat restoration remain unverified.
This test/CI-only correction preserves the installed product and all mandatory
engineering/desktop acceptance blockers.

## Latest qualification checkpoint — 5 November, Connections correction

The earlier checkpoints below remain historical evidence. P08 now has an actual
installed, isolated custom-MCP setup/validation/enablement and management proof
using pinned OASiS: start/stop, workspace disable, replacement draft without apply,
and explicit removal. No engineering tools were invoked and enablement granted no
invocation authority. Connection checks are now visible independently of credential
editing. OAuth reconnect/update-impact acceptance remains incomplete.

The final tested wheel SHA-256 is
`59d8274e048ddb08a72d3e746d1ce0224eab0ab571ceff2a7cf97dd3ab679abe`, with UI
`6a8d381b7970c5415b0640362f315038ba815c8deede41bd77b971e2a949bd74`.
Installed setup/management, retained-results/authoring and authenticated Docker
checks pass on Linux; these do not establish actual Windows desktop acceptance.
Current checked-in bundles are regenerated to match that tested UI. A prior gate
correctly rejected stale checked-in bundles even though the normal artifact build
had regenerated them. The failure is preserved; complete final gates/CI remain
required. All 30 checks/11 workflows on the preceding pushed `b9553937` passed.
The full engineering and actual desktop blockers below are unchanged.

## Current checkpoint

- Baseline dev: `4f370caa9743f869f769f8c8e2332b6b63be438b`, rechecked 5 November.
- Active branch: `codex/codex-production-integration`; goal submitted 4 November.
- P01/P02 preserved baseline and screen/action map. P03 automatic viewer observation FAIL on 0.38.1; external controls lacked accepted workspace context. Canonical controls now exist, without a new Windows rendering claim.
- P04/P05 maintained package, CLI, authenticated composition, scoped reads, plugin and hashed UI implemented. P06 copied-state and dependency-light install/restart/update proofs pass; original engineering state is unchanged.
- Named GB10 prototype wrapper **0.39.0** now uses the owned maintained candidate. Original prototype services/data and other settings are preserved. This conversation still reports its older connection; no desktop restart or further human request while the user is absent.
- P09/P10 installed Linux simulated-host proof passes: duplicate-file folders, collapsed technical run records, narrow file types, explicit editor fallback, exact retained image/producing-step/same-run return, rename/Undo/Redo/save/search/reopen and exact import destination. Full engineering summaries and full dependency portability remain open.
- Full gate 7 at `3f373cf0` passed backend, 2,310 frontend tests, docs and exact-image security, then failed at 36 missing Firefox/WebKit executables (164 browser passes, 15 skips). Firefox was installed and its isolated 19-test workspace suite now passes. WebKit 2370 aborts before Wright loads: its binary has a 16 KiB page ceiling, while GB10 uses 64 KiB. That earlier gate remains recorded as FAIL; the subsequent gate is below.
- Gate 9 passes at `de0886b9` with the documented local browser-host exception; separate installed Chromium journeys and Firefox checks pass. Normal pre-push/current-head CI remain pending. The newer file-list wheel now runs in the named owned candidate and its exact-image Docker checks pass. Actual Windows acceptance, reviewed handle analysis basis/provider bindings and complete Robot proof remain open.
- Additional installed evidence qualifies first-contact workspace creation/exact-scoped chat handoff, declared reference-byte transfer/collision rejection, and edited-source mismatch/Undo with unchanged historical files. These are bounded proofs, not full engineering or Windows acceptance.
- Evidence: private `.local-run/production-integration/`; [acceptance](acceptance.md) separates subset proofs from mandatory stories. No engineering run or production publication occurred.

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
