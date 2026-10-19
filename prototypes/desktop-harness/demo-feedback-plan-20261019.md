# Desktop demo corrections — 19 October 2026

Users must be able to reopen a saved workflow, edit its source, inspect the same
run and outputs, and return to its producing block inside the desktop panel.
The installed 0.16.0 demo exposed failures in this journey despite a completed
run. This is corrective prototype work under the existing desktop goal.

Original evidence is preserved in
`/home/burhop/repos/wright/artifacts/wright-plugin-audit/20261019` and the user
handoff at `/tmp/wright-desktop-resume-evidence-20261019/USER-FEEDBACK-WRIGHT-DEMO-20261019.txt`.
The accepted spacer source SHA256 is
`699c74b1103eab0bd59475e13346fa18fb29cc0f73e4a7ab7dfafbb2d5857a0c`;
run `a2fdbea2608247d08e794d389c9d7148` must not be replayed or rewritten.

## Tasks and decisions

- [x] F04: cold reconstruction must not inherit example connection-point identities.
  Reuse the canonical parser and vocabulary; retain strict same-document port
  kind/ownership checks and lossless save. Test the unchanged demo, existing
  Robot Tracking Diagnosis, and deliberate type/ownership mismatches.
- [x] F05: expose raw source correction when no diagram can be constructed.
  Keep invalid drafts separate; only explicit validated Save may create a new
  revision through the existing source CAS owner. Preserve results access.
- [x] F06: resolve exact navigation through the existing process navigation
  owner and scoped client; compose the editor and existing run/result controls.
  No inferred block, new executor, or bypass of absent/stale targets.
- [x] F02/F03/F07: stop advertising unverified loopback web links. This remote
  prototype supports the native panel; an API HTML response or open TCP listener
  does not establish an authenticated Windows browser handoff. Keep authorization
  intact and give explicit native-panel reopening instructions.
- [x] F08: make file-list workflow paths compose with source reads, retaining
  exact relative source identities and traversal/scope validation.
- [ ] F01: inspect current host metadata and widget restoration; retain exact
  workspace/source/run hints and provide a read-only reopen route. Qualify actual
  Windows streaming/final-answer/chat-switch/panel-close behavior separately.
  A simulated host cannot establish why the Windows panel disappeared.
- [ ] Regression: preserved refined editor, Hermes shared UI, native Home →
  Workflows entry, source/draft/save/reopen, result navigation, narrow layout,
  immutable accepted demo identities. Repository gates and exact installed build
  verification remain required; no test result implies user acceptance.

Wright keeps accepted source, runs, gateway authority, evidence, reviews and
recovery. These fixes change presentation, identity reconstruction and handoff;
they add no authentication framework, provider workaround or workflow engine.
Generated process UI stays gated, and the common working view remains available.
SteveCAD was uninstalled/unconfigured in the observed isolated workspace;
personal sign-in and engineering-provider qualification remain separate tasks.

## Integration

Work in `codex/desktop-demo-ui-corrections` based on local `b8879fcf`, isolated
from PR162's running image/security qualification and all live state. Integrate
after its prerequisite correction through normal feature PR gates. Preserve
original evidence and compare source/resource identities before deployment.
OpenAI UI guidance describes widget state as optional per-instance presentation
state, not durable business data or a guarantee of panel visibility:
https://developers.openai.com/plugins/build/chatgpt-ui#manage-state

## Evidence index

- Original handoff and captures above: installed 0.16.0, user observations plus
  clearly labelled recorded-response browser reproduction; no live mutation.
- `apps/web/src/prototypes/workflow-recovery/fixtures/codex-spacer-comparison.workflow.wflow`:
  byte-identical accepted source for regression, without credentials or live run
  authority. Qualification results will be appended after actual execution.

Implemented locally, not installed or user accepted: 319 focused frontend checks,
310 existing prototype boundary checks, and 40 owning workspace checks after the
final explicit no-panel fallback adjustment passed. TypeScript passed. The first
candidate's copied recorded-response reproduction produced 19 captures without
page errors, unsupported calls or horizontal overflow. That is simulated-host
evidence, not a Windows capture. The initial resource SHA256 was
`7fc090844ea0221d1cfa7b7e1dffb9f1696ab9423fb9c472a22a157d6aed3f46`.

All local logs and exact original-demo readback are indexed in
`/tmp/wright-desktop-resume-evidence-20261019/demo-feedback-progress.json`.
The original demo is still revision 1 with its one original completed run.
Fresh source-only spacer and Robot copies retain requirements; Robot's first save
adds the existing versioned default instruction snapshot visibly. No run started.

Cold loading clears the example's connection points while retaining the shared
parser's existing schema, binding and legacy grouping vocabulary. Source edits
still use their own accepted document, and type/owner mismatches remain errors.
This does not introduce arbitrary new schema vocabulary. Native navigation now
uses the public client's existing resolution owner and stable host dispatcher;
process/block targets focus the same editor, and run targets use the existing
read-only evidence view. Other target kinds remain explicitly unavailable.

F01 remains a user-observed lifecycle issue with unknown cause. The existing
read-only Home/workflow/history reopening route remains available; no synthetic
host result establishes Windows visibility after final response. Final served
Workflows checks, repository gates, current-head CI, dev integration, exact named
deployment and Windows acceptance are still pending for this correction.

The initial normal gate stopped at formatting, after security/history/Ruff/lint
passed. Installed the committed root lockfile's Prettier3.9.6 in this isolated
worktree (the workspace-only install had omitted it) and formatted only the eight
changed frontend files. The complete frontend formatting check now passes.
A rendered error-state check also found the raw correction field was only181×43px;
it now reuses shared source-editor styling, fits entirely at1280/480px, and stays
selectable/read-only after an uncertain save. Five owning recovery checks pass.
The regenerated resource SHA256 is `24b7acaa4e256d886a6d6f1864f003c679a2de7949ee7dee768c9fec3eb0366a`.
This candidate still requires its own exact image, normal gates and served checks;
no failed gate or earlier image is reused as a pass.

## Raw correction draft/reconciliation follow-up

Three deterministic regressions found a gap in the earlier c544/1dc candidate:
raw correction did not notify the existing inert draft owner or restore its
explicitly resumed draft; an exact read after lost save acknowledgement did not
update the surrounding native accepted-source context. The earlier gates remain
actual passes for that candidate, but this required behavior blocks its push.

The correction connects `initialDraft`/`onDraftChange` and reuses the existing
guarded `onReloadStoredSource` after an exact read. It keeps original accepted
source separate from raw corrections, retains layout, and lets the native source
client refuse adoption while source/layout remains uncertain. Known old state
and a mismatched viewport do not authorize acceptance or another save. No new
client, backend, executor, authentication flow or retry mechanism was added.

Before the change, all three external regressions failed. After the change,
21 owning recovery/source/draft checks, TypeScript, lint and locked formatting
passed. The maintained reconstruction suite now includes the regressions, with
exact negative and single-write assertions. Native resource SHA256: `80c24ab1fc77bb1e42cc8d97b2802ce031cd5a604e9d21bb72b43f7208fb88c4`.
New image/full/push gates, real served recovery/draft-owner checks and current-head
CI are still required for this product change; no earlier image/gate is relabelled.
Evidence: `/tmp/wright-desktop-resume-evidence-20261019/raw-correction-recovery-regression/`.
