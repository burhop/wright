# Evidence index — 11 October 2026

This is an opt-in experimental **chat** candidate on GB10 Linux ARM64. The user
accepted remaining native Codex tools for chat and required authoring/workflows to
stay gated. A passing chat test never replaces the failed zero-tools test. See
[qualification](qualification.md) and [exceptions](exceptions.md).

## Baseline and isolation

Original `/home/burhop/repos/wright` remains clean dev at
`a4a31c97ff4d47818574b67fb95b9f0a0c2914ac`. Fetch established remote dev
`ba2fad68c181165b96b9c15c40b1a1f63c88acb3`; the dedicated worktree is
`/tmp/wright-codex-platform-integration`, branch `codex/codex-platform-integration`.
The installed Wright command is not the source baseline. Existing desktop Codex
0.159.2, installations, original configurations, campaigns and other worktrees
were preserved. SDK and CLI runtime 0.162.1 were installed only in isolated
`/tmp/wright-codex-sdk-qualify`; Wright test dependencies belong to this worktree.

Fixtures, SQLite state, private authentication copies, browser output and ports
are separate from the independent MCP testing session. Served pilot API/UI ports
were 18184/15184; owned processes were stopped. Both source-auth comparisons passed
and disposable auth copies were removed. Read-only final state inspection found
zero engineering/native/workflow runs, reviews, authoring jobs and presentations:
[isolated state report](evidence/served-no-engineering-runs-arm64.json).

## Current official sources and inspected version

- [Python SDK](https://learn.chatgpt.com/docs/codex-sdk): stable SDK; actual installed public low-level lifecycle/configuration/approval/event interfaces were inspected.
- [App-server](https://learn.chatgpt.com/docs/app-server): experimental command; documented stdio is the chosen transport. This is not private stdio.
- [Noninteractive CLI](https://learn.chatgpt.com/docs/non-interactive-mode): documented automation/resume/JSON route, separate from interactive embedding.
- [Removed MCP-server wrapper](https://learn.chatgpt.com/docs/mcp-server): historical examples are not a supported embedding route.
- [Official 0.162.1 release](https://github.com/openai/codex/releases/tag/rust-v0.162.1): exact runtime/public schema boundary inspected, including experimental dynamic tools and missing public startup tool ceiling.

Official documentation establishes availability/maturity, not a local pass. Codex
as Wright's development agent, this embedded agent platform, and Codex Cloud
development jobs are separate uses. Cloud was not exercised.

## Runtime and observable-boundary proof

| Evidence | Observed result and scope |
| --- | --- |
| [No-tools negative control](evidence/no-tools-arm64.json), [actual runtime controls](evidence/runtime-controls-and-tool-surface.json) | **FAILED_EXECUTABLE_TOOL**: collaboration.list_agents executed despite disable flags/read-only/never/empty environment. No approval callback. No physical or external effect was exercised. Remaining native tools are not qualified. |
| [Early lifecycle](evidence/lifecycle-arm64.json), [bridge lifecycle](evidence/bridge-lifecycle-arm64.json) | Real pinned-runtime fixture history/continuation/cancellation and public SDK bridge observations. Earlier scope retained separately from later pilot. |
| [Chat/gateway pilot](evidence/chat-gateway-arm64.json) | **PASSED_LOCAL_CHAT_GATEWAY_PILOT**: actual SDK/runtime against a credential-free local Responses fixture, real GatewayService/SQLite audit. Five provider requests; one allowed read, malformed-argument denial, foreign scope/principal drift denied, same native history after restart, durable interrupted cancellation. Native external MCP is explicitly unqualified. |
| [Authenticated chat](evidence/authenticated-chat-arm64.json) | **PASSED_AUTHENTICATED_CHAT_RESTART**: two bounded real ChatGPT gpt-6.1-sol/high turns, exact same thread after restart, completed native/ durable receipts, source auth unchanged, disposable copy removed. No API-key fallback. |
| [Served workspace pilot](evidence/served-chat-workflows-arm64.json), [repeat/history](evidence/served-chat-history-repeat-arm64.json) | Actual HTTP/browser text turn and reloaded history, saved Codex default, normal Workflows entry; no route mocks, page errors or HTTP errors. Repeat did not send another model turn. |
| [Actual browser source identity](evidence/served-source-identity-arm64.json) | Ten browser-loaded source-map modules match worktree bytes, including chat changes and current editor implementation; no missing module. This is a source-served build, not installed-package proof. |
| [API restart and role gates](evidence/served-api-restart-gates-arm64.json) | Exact history after actual API restart, confined-authoring capabilities unavailable, both canonical/legacy native-start paths return 409 NATIVE_AGENT_UNAVAILABLE. Zero new model turns. Served backend source hashes recorded. |
| [Credential cleanup](evidence/served-credential-cleanup-arm64.json), [restart cleanup](evidence/served-restart-credential-cleanup-arm64.json) | Original authentication bytes unchanged; disposable copies removed after owned servers stopped. No credentials are committed. |

SDK call/notification sidecars, native turn ACK/terminal receipts, gateway audit and
fixture-provider requests are distinct scopes. Opaque provider prompts, downstream
effects and dollar cost are not inferred from app-server payloads. Unknown/lost-ACK
outcomes are held; automatic replay is forbidden and tested deterministically.

## Preserved current editor, through Workflows

The current reviewed Feature 083 editor has four groups and creates blank source.
Historical Feature 080 seven-group assertions failed against that baseline; retained
failed attempts are not erased. No editor implementation was replaced or old fixture
requirements rewritten. The normal workflow-sources API creates only isolated copies.

[004](evidence/editor-004-arm64.json) passes nine served cases: normal Workflows entry,
blank creation, direct input, Undo/Redo, two separate prompt blocks, typed keyboard
connection, exact saved reopen and invalid managed-field draft containment.
[007](evidence/editor-007-arm64.json) passes four: mismatch diagnostic without semantic
change, live drag/commit-on-release and layout reopen, zoom and actual pointer pan.
[008](evidence/editor-008-arm64.json) passes two: measured 2x compact viewport and
keyboard inspector, real CAS 409 preserving both local and concurrent saved edits.
Total **15 passed**. Creating prompt blocks sends no model requests. The stronger
current reviewed 008 proves the compact case instead of the obsolete 007 assertion.

Parameterized harnesses in `probes/qualify_workspace_editor_{004,007,008}.mjs` derive
from retained reviewed Feature 083 harnesses; their source artifacts remain untouched.
Run in order with fresh `--output`, private `--contextRoot`, actual API/UI and a scratch
workspace. Browser traces/screenshots remain local and are hashed in the artifact index.
No managed presentation was opened; final state confirms zero presentations.

## Final regression results

Each tranche is a scoped result; overlapping tranches are not summed as unique tests.
Raw logs remain under the feature worktree's ignored `.local-run`.

| Log | Result |
| --- | --- |
| codex-final-foundations.log | Core/DataVault/adapters: **1018 passed, 18 optional skips**, 34.74 seconds; Hermes, OpenClaw stub and Pi unavailable behavior included |
| codex-final-safety-regression-2.log | Mixed routing, authoring/native/process-interface gates and Codex safety: **95 passed**, 18.07 seconds |
| codex-final-routing-role-2.log | Session routing, first/cached role ownership and architecture: **47 passed**, 14.06 seconds |
| codex-existing-platform-regression-2.log | Existing workspace API/platform behavior: **49 passed**, 88.07 seconds |
| codex-final-web-regression.log | Four chat/service/session/transcript files: **71 passed**, 7.49 seconds |
| codex-web-build-final-2.log | Production frontend TypeScript/Vite build passed; ordinary bundle-size warning retained |

Ruff check, Ruff format and git diff whitespace checks passed. Focused ESLint
passes with two existing WorkspacePanel hook warnings; Prettier 3.9.6 passes after
formatting six touched files. Browser source hashes refer to implementation commit
25476bce; [format equivalence](evidence/frontend-format-equivalence.json) proves
the subsequent formatting emits the same JavaScript syntax for all six files.
Raw-TS comparisons differed on JSX whitespace/grouping; their reports are retained. API test warnings are
existing Starlette/httpx deprecations. Earlier failed probes/tests/browser attempts
remain local; later fixes have explicit new result logs. Reproduction probes and
isolated authentication/runtime setup are in [quickstart](quickstart.md).

## Repository gates and contrasting workflows

Actual `scripts/check-dev-push.sh` and `scripts/check-dev-merge.sh` attempts retained
`.local-run/codex-dev-push-gate.log` and `codex-dev-merge-gate.log`. The full merge
attempt passes source checks, isolated dependency sync and dependency audit (no known
vulnerabilities), then fails the required image-security scan because no immutable
candidate image was supplied. Its public failure projection is retained under
`test-results/docker-image-security/20261011T174820Z-94734761/public`. Docker 27.5.1 is
responsive; this is an incomplete prerequisite, **not an unavailable-host waiver**.
An ARM64 image from clean implementation commit 25476bce built successfully in
100.69 seconds. Its source is pinned and its reports remain separate; a formatted
candidate image and further gate results are recorded separately below.
The formatted candidate from clean commit 0d45fbbd built in 23.85 seconds with cache
reuse. [Container report](evidence/container-arm64.json) identifies immutable image
sha256:19ec7e09db2d3f43302ec8490e00c01f99e80c7220963a3eb1e2ab013425609e.
Existing offline exact-image API/Hermes smoke passed. Its separately installed private
SDK/runtime worker passed the [gateway/lifecycle fixture](evidence/container-chat-gateway-arm64.json)
inside a read-only-root container with external networking disabled. No credentials,
new model turns, host ports or protected engineering state were used. Disposable
containers were removed; candidate images/evidence were preserved.

[Trivy policy evidence](evidence/container-security-arm64.json) passes with fresh
11 October database, scanner 0.70.0, exact OCI/source binding and no findings.
This scans the candidate image, not the mounted optional SDK worker inventory.
The [full gate attempt](evidence/merge-gate-attempt-arm64.json) ran for 844.96 seconds
and failed only the already-collected startup fixture in its API tranche: **770 passed,
1 failed**. The fixture assumed engine construction before saved-default resolution.
The correction strengthens the check for both saved Hermes/Codex defaults and retains
migration-before-runtime ordering: **13 targeted tests passed** and the separately
[rerun full API suite](evidence/full-api-corrected-arm64.json) passes **772 tests**,
12 existing warnings, 358.78 seconds. Original source/failure logs remain indexed.

Before that stop the full gate passed lint/format/TypeScript, strict release/control-plane
mypy, distribution metadata/policy, **392 control-plane tests**, **192 release tests**,
**156 native/release tests (7 skips)**, **328 coverage tests (7 skips)**, native wheel/sdist
validation, security boundary and hardening tranches. Broad warning-mode mypy stopped on
duplicate existing conftest modules, not a checked Codex type error. Later suites,
full frontend/docs and managed live browser gate were **not reached**. The gate has not
been rerun as a whole after the test-fixture correction; it is **not green**.
The tested image is exactly source commit 0d45fbbd; final test/docs descendants require
fresh gate input binding. Runtime/UI source bytes are unchanged after that image. Packaging regenerated the
root runtime-extra-lock uv digest (required by the changed uv.lock) and staged frontend
assets. [Staging retention](evidence/native-gate-staging.json) preserves all eight
generated/deleted-file observations before restoring only owned generated static
source files to their clean baseline. Built wheel/sdist output remains in dist.
The refreshed runtime lock digest is included as required metadata; compiled staging
files are retained as artifacts, not added to this feature diff.

The locked frontend tooling was restored only in this worktree, then the four
chat files passed **71 tests in 7.29 seconds** and the production build passed.
[Baseline npm audit](evidence/baseline-npm-audit.json) reports 13 inherited package
findings: 1 low, 6 moderate, 5 high, 1 critical. Root/frontend package manifests and
lockfile match dev byte-for-byte. No automatic audit fix or version change was made.
Advisory presence does not prove exposure; image policy and development lock inventory
are different scopes, and baseline remediation remains independent work.

The existing manufacturing/heat preparation and Robot Tracking Diagnosis regression
tranche retained **24 failed, 159 passed, 3 skipped**. Eleven baseline manifest hashes
match CRLF reconstructions while pristine Git/GB10 inputs contain LF; exact-byte guards
reject them. [Byte evidence](evidence/baseline-byte-mismatches.json) and the raw
`codex-contrasting-workflow-regressions.log` are unchanged. Robot and other shared
analysis/representation checks passed offline. These are contrasting existing-platform
regressions, **not Codex workflow execution proof**. Original requirements/manifests
were preserved. See [Windows handoff](windows-handoff.md) for independent provenance
investigation; do not normalize originals or bypass guards to obtain a pass.

## Artifact retention and remaining qualification

[Local artifact index](evidence/local-artifact-index.json) retains hashes/byte counts
for original negative/lifecycle probes, current reports, SDK/fixture evidence, final
logs, browser harnesses/traces and gate projection. Absolute /tmp entries are local
artifacts, not portable bundled evidence. Curated JSONs contain no auth secrets;
private native transcripts, account metadata and SQLite contents are not committed.
The two served-repeat JSONs were recovered from their retained console JSON because
the harness reused a report filename; distinct raw logs retain provenance.

Native Windows startup and API-key auth remain explicitly gated. Linux x64, broader
authenticated/packaged Docker,
external Codex MCP, broader models/tools and usage/cost accounting require separate
proof. Public enforced zero/gateway-only tool sets are a prerequisite for the deferred
confined authoring and workflow stages. Full repository/packaged/host gates and baseline
provenance correction remain pending; experimental chat is not production qualification.
