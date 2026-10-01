# Confined model and presentation-authoring checkpoint

**Date:** 2026-10-01. **Branch:** `codex/083-process-working-interfaces`.
**Scope:** T029–T033 foundation. T042 remains pending.

## Actual configured model

Wright's Hermes adapter resolved the installed default `gpt-5.6-sol` through
the existing Hermes `openai-codex` model SDK. One actual generation returned
structured frontend source and its binding manifest. The fixed local compiler
built it successfully on the first attempt, with no diagnostic repair.

The native Hermes chat endpoint constructs its normal agent with configured
toolsets. Supplying an empty OpenAI tool list there does not establish a confined
authoring role. The optional invocation context therefore uses the installed
model-only SDK client through the existing Hermes adapter. It creates no
`AIAgent`, dispatcher, native workspace chat, global profile or model change.
Ordinary adapter chat remains on its previous path. Other adapters fail closed
until they qualify this role.

The subprocess resolves the actual default, hashes the configured public model,
provider mode, endpoint identity and installed resolver/client sources, and
checks that resolution again before inference. Every turn supplies the prepared
versioned system instructions, one self-contained user message, `tools=[]` and
`tool_choice=none`. Returned tool requests are rejected without execution.
Provider credentials remain with the installed SDK and are not retained in
prompts, results or provenance. Model/configuration and effective instruction
hashes are checked by the adapter and authoring owner.

The live payload contained only a synthetic process reference, public shared UI
contracts and reference template. No repository workflow, customer engineering
data, process execution, MCP request or hardware effect was included. Automatic
approval initially rejected a proposed smoke described as exporting private
workflow data. That call did not execute. The revised, explicitly synthetic
payload and egress audit were approved before the successful call.

The retained [model scope](../../../../artifacts/process-interfaces/083/20261001-authoring-foundation/model/checked-scope.json)
records exact model/instructions/source/manifest/toolchain/bundle identities.
The smoke used the adapter and builder directly; it did **not** exercise a native
authoring route, managed browser preview, saved working UI, real process, MCP
provider or engineering acceptance. The installed Codex model mode is live
qualified here; other SDK modes are not claimed live qualified by these tests.

## Durable owner and revisions

The application owner now retains immutable requests and attempt records with
trace identity, resource/instruction hashes, assigned UI/revision/process
identities, previous source, exact diagnostics and model attestation. Duplicate
request reconciliation happens before model/compiler preparation. Closing an
observer does not cancel generation. Explicit cancellation or service shutdown
stops the owned task and its bounded model/compiler child. Restart reads durable
jobs and the existing cooperative application lease; interrupted work is reported
without automatic generation replay.

At most two repairs are persisted. Source schema and supported stable
input/output binding checks precede compilation. Unsupported mandatory selectors
remain unavailable; this catalog does not invent provider schemas, assessments
or runtime observations. Compiler drafts use a short owned temporary path to
avoid Windows child-process working-directory length limits. Build reports and
successful files are retained before the temporary draft is disposed.

Source, binding, report and compiled bytes are published once through an immutable
file set over the existing FileVault. All hashes and sizes are verified when
reading a revision. Saving requires exact expected build hashes and a
server-derived preview observation. Activation/rollback checks current accepted
source, binding/client/kit versions and requested process capabilities. An update
reads the verified previous source. UI revision selection does not write run
inputs, execute engineering steps or change validation/review records.

The preview observation tests use a **synthetic presenter observation**. Managed
origin authority and actual browser loading are later integration tasks, not
established by constructing that internal value in a unit test. Packaged public
client/kit distributions and installed native/Docker checks also remain pending.

## Verification

Final focused group: **155 passed**, zero skips, **67.51 seconds**. It covers
adapter context/provenance, model-only SDK request construction, ordinary Hermes
regressions, fixed compiler/import/CSS/binding limits, durable job/cancel/reopen,
two repairs and exhausted budget, immutable revisions, synthetic preview/save,
update/rollback/source reuse, preparation and existing artifact-access regressions,
and additive database migrations. The authoring test includes an actual local
TypeScript/Vite build with a controlled model response. Other model/build
responses in that module are explicit fixtures.

Command, environment, logs, code hashes, earlier failures and preserved-work
checks are in the [checkpoint manifest](../../../../artifacts/process-interfaces/083/20261001-authoring-foundation/checked-scope.json).
Earlier 73- and 130-check groups overlap this group and are not additive coverage.
The first job group passed 17/18 and exposed the deep Windows compiler cwd;
the subsequent group passed all 18 authoring cases but caught an old migration
expectation. Those failures were corrected without weakening assertions.
One final command used a nonexistent test filename and ran no tests; the corrected
155-check command is the accepted result.

## Remaining work

T032's installed public package build envelope, T034–T042's managed runtime,
presentation grants/bridge, native API/UI and live preview/save/update journey
remain pending. T021's retained editor regressions and M4/M5's two engineering
tool chains, migration, distribution and full workspace acceptance remain required.
The common view is retained; this checkpoint does not complete the full goal.

---

# Actual model, managed browser and installed-resource checkpoint

**Date:** 2026-10-01. **Branch:** `codex/083-process-working-interfaces`.
**Parent:** `818f76af5a94f0fdbf2e9162112a79e214c1a42e`.
**Scope:** T032 fixed compiler/public resources; actual T042 authoring smoke.
Remaining M3, engineering and distribution acceptance are listed below.

## Observed user journey

Entered the workspace through its normal **Workflows** control, opened the common
working document, requested an interface through Wright, watched creation progress,
opened its isolated preview in another existing document tab, saved the observed
revision, and opened its built working interface without another generation.

The qualified continuation reopened an exact previously saved model-generated
interface, propagated a theme token into the frame, reloaded that document without
generation or process submission, requested a focused update through Wright,
previewed/saved the new revision, and restored the earlier revision using the
native revision control. All three owned presentations closed with HTTP 204;
no process was cancelled. A refresh race that overwrote the user's chosen
revision was reproduced, fixed, and covered by a component regression.

This is a software qualification with controlled workspace chrome and accepted
source discovery. The process/authoring API, storage, security middleware, actual
configured model, fixed compiler, Windows managed worker/containment, isolated
bootstrap, bridge, theme connection and browser were real. The harness used a
fresh private database and workspace outside the repository. It did not execute
an engineering process, call an engineering MCP, or perform any hardware action.

## Evidence and identities

- [Fresh generation/build/preview/save/reopen scope](../../../artifacts/process-interfaces/083/20261001-t042-managed-active-tab/process-ui-authoring-live--96b7f--through-the-workspace-live-chromium/checked-scope.json):
  `job-13729e8a9926418bb12e266d7e76c815`,
  `ui-4e066eedc93242a59d1846a6fd0df7b3`,
  `revision-afd5bee54a8f4cc5af795df94e5959b7`.
- [Saved UI/update/theme/reload/rollback scope](../../../artifacts/process-interfaces/083/20261001-t042-managed-qualified/process-ui-authoring-live--96b7f--through-the-workspace-live-chromium/checked-scope.json):
  initial `job-5f7dca9233024b5c8b5080f0ef7fdff3`,
  `ui-eff1d6941f434c3691c79716da3a82fd`,
  `revision-c27524b10e1b435f86cff705f8224a15`;
  update `job-b4eba82ef64845578235f73b4e6c160e`,
  `revision-be39192b3db048fd981cc10f39f0db2c`.
  This browser run reused the initial saved job; its fresh model call was the update.
- [Checkpoint manifest and prompt/response digests](../../../artifacts/process-interfaces/083/20261001-live-authoring-package/checked-scope.json)
  identifies the original private `attempt-0` records and resolved model/role
  attestations. Raw prompts/responses remain in the isolated owner database;
  credentials, cookies, bootstrap URLs and traces are excluded from published evidence.
- [Working interface screenshot](../../../artifacts/process-interfaces/083/20261001-t042-managed-qualified/process-ui-authoring-live--96b7f--through-the-workspace-live-chromium/saved-working-interface.png),
  [updated preview](../../../artifacts/process-interfaces/083/20261001-t042-managed-qualified/process-ui-authoring-live--96b7f--through-the-workspace-live-chromium/updated-preview.png),
  [revision rollback](../../../artifacts/process-interfaces/083/20261001-t042-managed-qualified/process-ui-authoring-live--96b7f--through-the-workspace-live-chromium/revision-rollback.png).

The actual inherited model was `gpt-5.6-sol` through Hermes. The versioned
`process-ui-author/1` role supplied prepared instructions on the scoped no-tools
SDK path. Global model configuration and workspace tool activation were unchanged.
Successful initial/update jobs needed zero repair attempts. This does not qualify
other agent platforms or models.

## Defects corrected

1. Managed readiness allowed only one second for complete Windows startup.
   The fixed manifest now allows a bounded 30 seconds, polling every 250 ms.
   Existing immutable declarations were preserved; a fresh workspace was used.
2. Vite library mode left `process.env.NODE_ENV` in the browser bundle. The fixed
   builder now defines its production value. A regression evaluates the compiled
   module in a browser-like realm without Node's `process` global.
3. The development proxy forwarded its preview port as the write Origin, while
   the backend checked the issued API preview Origin. It now translates only
   the exact matching isolated preview; foreign/control/null origins stay denied.
4. Frame reloads did not re-arm the bounded host handshake. Each document now
   gets a new challenge; the same native parent can renew that hello. Receipt
   reads remain separate from process submission and duplicate starts stay deduplicated.
5. Async revision refresh replaced a manual selection. Refresh now preserves a
   valid chosen revision, while saving explicitly selects the new revision.
6. A surface without a real maximization callback exposed an inert button.
   Such documents use the workspace's existing maximization control.

Browser qualification also corrected ambiguous hidden-tab locators and implicit
label matching after text/select values changed. Request waits and cleanup are
bounded. An earlier interrupted qualification closed its two abandoned views
through the native owner; it did not interrupt a process.

## Installed resources and checks

Root and private service wheels carry the public client/kit sources, manifests,
styles, documentation, role instructions, template and fixed asset runtime.
The private service source archive rebuilds with identical public resources
without sibling package directories. Installed compiler discovery requires an
explicit trusted native dependency root; it cannot guess an ancestor checkout
or borrow missing public sources from that root.

An extracted root wheel was imported with isolated Python and explicit module
path assertions. Its immutable saved assets served actual loopback HTTP with
the restrictive CSP while compiler launch/model/network access were unavailable.
A second check compiled the shipped reference against shipped client/kit source
using explicitly configured pre-existing native dependencies. No package download
or script supplied by the model was involved. This qualifies native Python/static
resources, not the packaged workspace frontend or Docker runtime.

Observed checks:

- Fresh browser: **1 passed, 2.4 minutes**; update/reload/rollback browser:
  **1 passed, 2.1 minutes**.
- Backend/API/build/authoring/authority/distribution group: **109 passed**, zero
  skips, 79.72 seconds. Subsequent final compiler/static/toolchain/distribution
  group: **49 passed**, zero skips, 65.41 seconds.
- Frontend group before revision fix: **51 passed**, six files, 8.97 seconds;
  focused revision regression group: **9 passed**, 4.43 seconds.
- App TypeScript and changed Python Ruff checks passed. The broader Vite test-file
  ESLint check also encountered a pre-existing `no-unsafe-finally` error at line 62;
  its new origin cases passed. That unrelated cleanup rule was not disabled.

Commands were the feature's selected pytest modules with `-p no:cacheprovider`,
Vitest selected host/panel/presenter/proxy files, and opt-in
`process-ui-authoring-live.spec.ts` with the system-Chrome qualification config.
Private runtime/context files are under `.local-run/process-interfaces-083/`.
The source API stayed running while compiler provenance added the Three/type
manifest checks; the final installed compilation tests qualify those additional
checks separately from the live browser's recorded toolchain digest.

## Remaining acceptance

T034/T037/T040/T041 retain full installed launch, broader audit/navigation,
accessibility/error and second-run obligations where not already covered by their
earlier controlled evidence. The common-view Run regressions in T021 remain
pending. T043–T049 require two actual engineering tool chains, exact 082 checks,
both tailored interfaces and migration. T050–T057 retain final production frontend,
clean Docker/native lifecycle, walkthrough, documentation and completion gates.
The existing Docker engine is available; its campaign containers were only listed,
not changed or reused for this qualification.

The full implementation goal remains active. No engineering/product acceptance,
physical dispatch, push, release or feature completion is claimed.
