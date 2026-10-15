# Prototype task record

This record tracks verification, not product acceptance or release readiness.

## PR158 correction checkpoint — 15 October 2026

The file-transfer candidate is draft PR158 at the original pushed head1a079bc2.
Its normal local push gate passed, including 416 affected UI tests, 18 shared
editor Chromium checks and 5 onboarding checks. The separately corrected full
UI suite passed all1,910 tests. CI finished with 27 passes, one intentional skip
and one Windows backend failure: an existing cancellation test measured3.166
seconds against its combined three-second wall-clock assertion.

The test correction observes the real poll-wait and cancellation-wakeup events,
preserving all durable request, one-cancel and uncertain-outcome checks. All55
affected tests pass locally; a temporary suppressed-signal negative control fails
at the wakeup assertion as required. No production cancellation code changed.
Normal correction push checks and the consolidated second CI cycle remain due.
Evidence: `/tmp/wright-transfer-integration-evidence-20261015/`.

Named plugin0.13 is installed from the previously qualified immutable runtime04db87cd,
with exact package/protocol/resource verification and all24 older cache files
preserved. This existing chat still reports its earlier image-unavailable binding;
actual Windows acceptance is pending a fresh chat. The installed state contains
**SteveCAD desktop demo** with exact unchanged native example source. Its common
view blocks Start because SteveCAD has no available tools. No engineering run,
sign-in or tool grant was created. Full engineering and user-acceptance requirements
below remain unchanged. This checkpoint supersedes earlier installation/CI status.

## Integration candidate checkpoint — 15 October 2026

This checkpoint supersedes the historical observations below. Named plugin0.11
is still installed; upload/transfer changes are local and not installed or pushed.
PR156 is merged at dev3b994c56. Both image builds passed; its published ARM64
image has 503 exact runtime/dependency hashes verified, healthy isolated startup
and four shipped-workspace save/reopen checks. Evidence:
`/tmp/wright-dev-3b994c56-deployment-evidence/checkpoint.json`.

The combined file-transfer candidate reuses existing declared-input and portable
bundle owners. Native input upload, definition export/import, declared-reference
transfer and uncertain import recovery have scoped local evidence. See
[transfer plan](workflow-transfer-plan.md) and [input upload plan](input-upload/plan.md).
Eight actual-owner browser checks include lost-reply recovery without a repeated
import; 38 focused frontend tests pass. Native controls preserve the common
editor/header and draft guards. The artifact source and dependency manifests
remain authoritative; an unrelated workspace file is not offered as a reference.

The clean-archive image at 04db87cd passed its isolated smoke and served shared
workspace export/import checks. Candidate plugin0.13 passed local protocol,
upload, transfer, image-fixture and synthetic-review checks; it is not installed.
The full merge gate passed its Python/Hermes suites but failed one of 1,910 UI
tests: the saved-default test did not open the new File details disclosure before
asserting the reference was visible. The correction preserves exact-reference,
no-mutation and prepared-binding checks; all 61 tests in that file pass. Full UI
revalidation is running. The failed gate and generated assets are preserved in
`/tmp/wright-transfer-integration-evidence-20261015`; production code is unchanged
by this test correction. This is not a passing full gate.

Next: finish corrected gates, push checks and hosted CI; apply the qualified
named plugin update and complete Windows acceptance. Saved-interface portability, actual Windows delivery and
original prepared engineering input cases remain separately unqualified.
SteveCAD authentication, full four-/six-hole and heat-spreader runs, genuine
reviews, Robot Tracking Diagnosis and manufacturing digital regression remain
required. Prototype infrastructure tests do not replace those engineering proofs.

## Historical local follow-on checkpoint — 15 October 2026

This section supersedes the older checkpoint below; historical evidence remains
intact. Complete engineering demonstrations and Windows acceptance are unfinished.

| Area | Observed state | Next required evidence |
| --- | --- | --- |
| Installed named plugin |0.11.0, retained isolated runtime; no new installation | Actual Windows walkthrough and exact next-candidate qualification |
| Engineering image transport | PR157 merged to dev a4e80d66; six-image desktop reply and same-run continuation qualified in isolated0.12 candidate | Reconcile candidate with integrated runtime; install only after gates, then Windows observation |
| Connections integration | PR156 still open at pushed3f7ad9b2;26 CI successes,1 skip,2 failures | Local consolidated dab89787 corrects interrupted asset download and bounded Windows record reads; full gate currently running, then push gate/current CI/dev deployment |
| Declared file inputs |75ad57dd local implementation and seven actual-owner browser checks; exact small/32 MiB wire proof | Original prepared workflow declarations, repository gates and actual Windows limits/interaction |
| Public readiness messages |3e771584 local correction,74 transport tests and actual owning rejection observed | Remains separate from successful upload, execution or Windows acceptance |
| SteveCAD four-/six-hole and heat-spreader demos | Existing requirements/evidence retained; no new desktop-driven full engineering run | Windows callback route, account consent, current provider discovery, exact grants, real outputs and genuine reviews |
| Robot Tracking Diagnosis | Full corrective-CAD/FEA requirements retained; independent recording tools qualified in isolated state | Exact AgentCAD platform and CalculiX transport/field capability; no simplified workflow substitution |
| Manufacturing preparation | Original requirements/profiles and protected campaigns retained | Independent mesh/slicer bindings and exact PETG HF/P1S profile qualification, then fresh digital regression |

The upload state03 browser screenshot is an actual GB10 preview with a simulated
host and synthetic inputs, not a completed engineering demonstration. The newer
state05 proves the real standardized readiness reason reaches MCP, with accepted
source unchanged and zero uploads/runs. An unbound library template is correctly
rejected before input upload; its original diagnostic remains failed.

Current evidence owners (private local paths, no credentials):

- /tmp/wright-desktop-custom-connections-evidence-20261015/combined-integration-checkpoint.json
- /tmp/wright-run-record-read-recovery-20261015/checkpoint.json
- /tmp/wright-desktop-input-upload-evidence-20261015/checkpoint.json
- /tmp/wright-desktop-images-012-evidence/checkpoint.json
- /tmp/wright-windows-callback-handoff-20261015/WINDOWS-STEPS.md

The sole callback receipt is tied to local-self-check.json and is not Windows
reachability evidence. Desktop reasoning remains the requested harness; no model,
authentication route, provider or engineering assignment was substituted.
Generic workspace file download, portable export/import and remaining routine
management still require implementation/qualification; image display and declared
input upload do not establish them. Generated process-UI authoring stays gated.
No new push, merge, release, external post or plugin update accompanies this index.

## Earlier checkpoint — 15 October 2026

Named0.11 is installed and protocol/resource verified. Its custom HTTPS connection
flow, explicit source review and saved-plan discovery have isolated qualification.
See [installation evidence](installed-011-evidence.json),
[walkthrough](desktop-011-walkthrough.md) and the current
[demo readiness plan](demo-readiness-plan.md). The full local custom-connection
gate passed at934c70e5 with the documented GB10 WebKit limitation; push checks,
current-head CI, dev integration and deployment proof remain outstanding.

The separate image follow-on lives at /tmp/wright-desktop-engineering-images.
Its local six-original-image and owner-loss proofs do not enable that profile
in installed0.11 or replace fresh SteveCAD/heat-spreader engineering runs,
Robot/manufacturing regressions, actual Windows acceptance or genuine reviews.

## Historical next-work checkpoint — 14 October 2026

See the refreshed [continuation checkpoint and priorities](demo-readiness-plan.md#current-continuation-checkpoint--14-october-2026)
and [short goal prompt](demo-readiness-next-goal.md). Continue the existing goal;
finish the current home slice before duplicating implementation.

The installed named plugin is now **0.9.0**, frozen in
`/tmp/wright-desktop-continuation-candidate` with API8156 and fresh isolated
review-only state. See [installation evidence](installed-09-evidence.json) and
[walkthrough](desktop-09-walkthrough.md). The actual package/protocol, eight
browser checks, 96 affected review/boundary tests and 140 prototype tests pass.
A real desktop reply, private synthetic review, reconnect and explicit Continue
completed one run with one request/reply and no engineering-tool enablement.
Windows acceptance remains pending; this existing chat still reported the older
`4d76cd14…` binding after installation. Do not infer 0.9 use from skill refresh.

The main execution candidate d070e351 is draft PR 154. Its full local gate
passed with the documented GB10 WebKit host exception; the normal pre-push gate
passed including 18 Chromium editor checks. Current-head CI remains authoritative
before merge. The 0.9 descendant and subsequent work are separate from that gate.

The next isolated UI candidate is `/tmp/wright-desktop-workflow-entry`, branch
`codex/desktop-workflow-entry`. New workflow in the native Workflows view reuses
the shared blank source and creation owner. It is not installed. See
[workflow entry plan](workflow-entry-plan.md) for scope and retained proof.

The isolated `codex/desktop-template-entry` follow-on exposes the existing template
owner through the shared picker and two scoped MCP operations. It is not installed
or included in the 33afba8a full gate. See [template entry](template-entry-plan.md).

Use [demo-readiness-plan.md](demo-readiness-plan.md) as the current forward plan.
The user submitted the [new goal](demo-readiness-goal.md). M0 is active; its
[baseline correction evidence](ui-concepts/2026-10-12/baseline-correction-20261014.md)
records actual checks separately from remaining qualification.

- [ ] M0: qualify/merge the existing baseline and resolve critical desktop,
      reasoning/action, image/artifact and headless-auth uncertainties.
- [ ] M1: deliver workspace/workflow/connection entry and a real desktop-driven
      SteveCAD four-hole run, then six-hole reuse of the same accepted process.
- [ ] M2: complete routine management, file/results/history and trustworthy
      continuation/reviews; fix observed Windows UI problems.
- [ ] M3: qualify the fresh SteveCAD/OASiS engineering comparison, different-workflow
      regressions, actual desktop acceptance and repository integration gates.
- [ ] Retain exact capability/version evidence and real milestone screenshots,
      captions and demo instructions, without publishing externally.

## Historical prototype checks

The entries below retain their original checkpoint context. In particular,
early unchecked installation and connection tasks are not a current status
report; later installation/UI evidence and the forward plan take precedence.

- [x] Inspect and preserve old checkout, current-dev worktree and earlier pilot.
- [x] Read current architectural/editor instructions and official plugin docs.
- [x] Install locked dependencies only in the feature worktree/private caches.
- [x] Implement durable scoped handoff in existing Data Vault ownership.
- [x] Dispatch desktop callbacks per canonical run, rejecting legacy fallback.
- [x] Preserve immutable platform association when creating workspaces/sessions.
- [x] Transport real desktop replies through authenticated MCP without a model worker.
- [x] Verify hosted editor entry and saved results with no Wright agent API calls.
- [x] Verify declared input, disconnect and API restart continuation on one run.
- [x] Record invalid input, wrong scope, auth, stale/duplicate and drift denials.
- [x] Prepare local plugin manifests/skill and exact live connection/rollback.
- [x] Request specific live-configuration approval and desktop-host clarification.
- [x] Receive Windows-host clarification; prepare a reviewed Windows handoff
      instead of modifying GB10 desktop settings.
- [ ] Obtain and apply approved connection setup; verify actual installed tools.
- [ ] Prove chat beside rendered Wright in desktop, including host/GB10 connection.
- [x] Qualify one exact enrolled read-only gateway operation through local MCP.
- [x] Qualify typed action proposals through Wright's bounded gateway decision loop.
- [x] Reconnect after an accepted inspection proposal and complete the same run
      with exactly one observed gateway dispatch; no first-decision replay.
- [ ] Verify a connected checkpoint view and user journey through desktop tools.
      Connected common-view UI selection/Submit and exact same-run completion
      now verified after restart at a durable wait; first output unchanged,
      normal tab close/readback passed. Installed desktop tools remain required.
- [ ] Handle abrupt MCP disappearance and pending-reasoning restart reconciliation.
      New development lease qualifies actual MCP child loss/expiry and same-live-
      run reconnect; current-profile response API restart now retains pending state
      and denies late answers, with no replay. Uncertain outcomes remain.
      Abrupt API SIGKILL/reopen was observed: same run/request and no replay pass;
      late answer incorrectly accepted with no live consumer. Retained failure
      blocks automatic reasoning restart; current Windows target preserved. New leased response runtime now passes the
      same SIGKILL/reopen denial probe; automatic task resurrection unsupported.
- [x] Qualify a narrow live-owner admission patch in a separate temporary
      candidate: actual desktop live response completes, post-SIGKILL answer
      receives 409, same pending request/run retained with no output or replay.
- [ ] Promote the tested admission patch into the main prototype with a deliberate
      new runtime profile; keep the prepared Windows baseline stable until its
      connection experiment is reconciled. Requalify action tasks separately.
      Patch applied in the new development worktree after freezing Windows at
      local checkpoint a17acb85. All 102 focused tests passed before fresh leased profile qualification.
      Subsequent leased development response/action profiles are now qualified
      for live reconnect and one permitted read; combined suite passes 107.
- [ ] Verify no automatic replay for lost acknowledgements/uncertain gateway outcomes.
      Controlled timeout/internal effect-boundary tests pass: one marker, one
      dispatch, no second desktop decision. Real-provider/restart outcomes remain.
- [ ] Reuse the existing served editor acceptance harness and preserve full authoring.
      Existing harness reused: all 11 current hosted-authoring cases now pass
      together in reports 09 and post-format 10; source/layout readback, real CAS, invalid source,
      keyboard typed connections/rejection, drag/pan/zoom, Undo/Redo and compact
      layout. Full legacy and installed/right-panel acceptance remain separate.
- [x] Make fresh original manufacturing/Robot template and scenario copies,
      verify hashes, and retain explicit compiler/readiness blocks without runs.
- [ ] Exercise fresh manufacturing-preparation and Robot Tracking Diagnosis copies.
      Read-only exact stage/input/provider readiness audit saved; originals
      unchanged. Missing bindings/providers/image delivery explicit. Manufacturing
      needs a simulated local receipt, never a physical printer transfer.
- [ ] Complete appropriate shared-code/platform regressions and local review gates.
      Current scoped regressions pass: preserved pilot 40, platforms 32, recovery
      69, frontend 180; lint/type/build/format and served authoring pass. Full
      repository integration gates remain required before a PR integration claim.
- [x] Format the three reported Python files and requalify the observable runtime
      profile after the adapter bytes change; preserve earlier proof identities.
      Leased response/action profiles qualified in fresh isolated proofs; old
      Windows bytes retained. Current-profile pending-reasoning restart is separate.
- [ ] Commit coherent reviewed checkpoint locally; no push, merge or release.
      Experimental baseline checkpoint a17acb85 created locally. Integration gates
      and final candidate commit remain separate; nothing pushed/merged/released.
- [ ] Finish reproducible walkthrough, version/capability matrix and social gallery.

Generated process-UI authoring remains gated. It is separate from desktop
authoring of ordinary accepted workflow source through the current source owner.
The read-only proof does not qualify arbitrary tools or installed desktop loading.

### 15 October: combined 0.10 candidate and baseline integration

- PR #154 merged to dev as 3ff4339ea341b4486778578997d01ca2b96f392f
  after exact-head local gates and all required CI. Post-merge development
  build/deployment/smoke remains pending; later candidate changes are separate.
- Prepared named 0.10 package; actual protocol/resource, eleven browser checks
  and fresh private review/same-run continuation pass. See
  `native-home-010-evidence.json` and `native-home-010-update.md`.
- Installed plugin remains 0.9. No live update or Windows acceptance claim.

- Named 0.10 installed; actual installed 34-tool/resource/package verification passed.
  All 18 prior cache files retained, only named marketplace source changed.
  See `installed-010-evidence.json` and `desktop-010-walkthrough.md`.

### Image response restart qualification

Fresh synthetic image task retained the same request after an abrupt private API
loss. Reopened run requires reconciliation, late answer was denied, and counts
remain one request/zero responses. See `image-restart-evidence.json`. This does
not qualify restart during an action or uncertain tool outcome; installed image
inputs stay disabled.

The cumulative 1988beec integration gate failed on Prettier formatting in the new
template-client test. Formatting was corrected without changing assertions;
retain the failed gate log and rerun on the corrected candidate before push.

## PR156 first-cycle correction — 15 October 2026

The completed first cycle found one ambiguous onboarding locator and two Windows
cancellation-test failures. See ci-first-cycle-correction.json. A deterministic
GB10 test reproduced cancellation returning before generated-file publication
finished. The use case now reuses the existing owned-write completion mechanism;
no provider action is repeated. The fixture retains its outcome and 3s wakeup
assertions with a 1s confirmation window. All12 focused cancellation/concurrency,
36 gate-contract and five onboarding browser checks pass. The normal frontend
gate now includes the live read-only onboarding check. Corrected full gates and
current-head Windows CI remain required before the second push/merge.

## PR156 integration packaging correction — 15 October 2026

The integration-sync head 3f7ad9b2 passed local gates but its x64 engineering
image download failed with curl TLS error 56 twice (one bounded CI retry).
A local interrupted-body reproducer showed that the existing curl retry option
did not retry partial transfers and left a truncated file. The release-asset
installer now retains five retries, retries transfer failures and removes failed
partial output. This applies only to build-time GETs, not workflow actions.
The actual embedded installer passes local recover-on-second-request and
exhaust-after-six-attempts tests; all 31 Docker bundle tests pass. The test is
already included in the container push slice and full merge gate.

Evidence: /tmp/wright-artifact-download-recovery-20261015/result.json and
installer-qualification.json. The local HTTP proof is not an exact reproduction
of TLS56 or qualification of SourceForge. Native x64 image CI remains required.
The pending Windows backend check must reach a terminal state before any new
push. A fourth push would be an exceptional consolidated packaging correction
after the independently merged image capability, not another blind CI retry.
Current-candidate gates, CI and dev integration remain pending; no plugin update
or engineering run follows from these unit checks.
