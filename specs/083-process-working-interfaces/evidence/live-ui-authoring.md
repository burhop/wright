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
