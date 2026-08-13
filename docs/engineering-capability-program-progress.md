# Wright Engineering Capability Program Progress

**Last updated**: 2026-08-13
**Current loop**: 069 - Rivet workspace MCP execution through the Wright gateway
**Program state**: Active; Gate E closed; no `main` merge or release authorized.

## Completed foundation

### Dynamic engineering MCP catalog integration

- Integrated the latest `origin/codex/engineering-mcp-dynamic-catalog`, including `80ed3fc` and both GB10 evidence records, with Feature 067's current `dev`.
- Preserved the 69-entry rich catalog, platform selectors, bundle policy, weekly validation workflow, setup recipes, follow-ups, and clean-container evidence.
- Added LF normalization for manifest-hashed Rivet source inputs after the installed-wheel gate exposed Windows line-ending drift.
- Replaced a stale gateway resource assertion that hard-coded the prior 42-entry catalog with an exact canonical-document comparison.
- Full `scripts/check-dev-merge.sh` result: passed. Evidence included 1,434 repository tests passed/52 skipped, 265 web tests passed, strict docs, production web build, 13 Hermes plugin tests, and 130 live Playwright tests passed/1 skipped.
- Feature commits: `2622c2a`, `9d1618a`; validated feature tip `9d1618a`.
- Merged and pushed `dev`: `c6dc90c` (`Merge dynamic engineering MCP catalog`). Local `dev` and `origin/dev` matched after push.
- Deferred external validation: NVIDIA Omniverse needs an NVIDIA/NGC API key; this did not block the catalog foundation.

## Loop 068

### Spec Kit phases

- [x] `speckit-git-feature`: branch `068-capability-library` created from clean `origin/dev` at `c6dc90c`.
- [x] `speckit-specify`: `spec.md` and specification quality checklist completed; all checklist items pass.
- [x] `speckit-clarify`: no critical ambiguity; the program's safest reversible defaults cover scope, roles, trust, lifecycle, error, and recovery behavior.
- [x] `speckit-plan`: research, plan, data model, API/schema/UI contracts, Gate A record, and quickstart drafted.
- [x] `speckit-checklist`: 56 UX, security, compatibility, recovery, and testability requirements-quality checks pass.
- [x] `speckit-tasks`: 119 dependency-ordered tasks with story checkpoints, test-first slices, traceability, hardening, and merge verification.
- [x] `speckit-analyze` and remediation: final rerun has 45/45 requirement coverage, zero critical/high findings, and no constitution conflict. The production adapter seam, complete filter/detail contract, installed precondition, three-backend journey, and dialog accessibility findings were repaired before the rerun.
- [x] `speckit-implement`: T001-T119 complete; exact-tree confirmation and integration are the only remaining operations.
- [x] Focused, integration, UI, packaging, and docs verification
- [x] Full dev gate
- [x] Push feature, merge to `dev`, push `dev`, verify synchronization (performed only after the final exact-tree confirmation passes)

### Gate A decision

- Selected a Wright-pinned Ed25519 public trust root, canonical signed envelopes, SHA-256 payload binding, monotonic sequence and expiry checks, administrator diff/activation, and transactional active/previous rollback.
- Catalog metadata remains separate from custom records, install/process state, credentials, explicit disablement, and workspace grants.
- Selected a digest-bound exact Install Plan before effects.
- Selected the UI sequence Discover -> Understand -> Add -> Review plan -> Validate -> Use in workspace. Invocation approval remains separate.
- Rollback: activate the prior verified snapshot; packaged catalog remains the immutable recovery root. Storage migration is additive.
- Detailed evidence, alternatives, risks, and rollback: `specs/068-capability-library/contracts/gate-a-decision.md`.

### Research and external validation status

- Official MCP Registry is an ingestion source for Wright's reviewed aggregate, not an online dependency for end-user discovery.
- Supported first import grammars: Claude `mcpServers`, VS Code `servers`/`inputs`, and plain single-server JSON.
- Onshape published the official Onshape Labs FeatureScript MCP on 2026-08-11 with endpoint `https://fs-mcp.labs.onshape.app/mcp`.
- Onshape remains external-live-validation deferred: Wright has not subscribed, accepted App Store terms, supplied credentials, contacted the endpoint, or claimed protocol/tool success.

### Implementation checkpoint 1

- Added explicit standalone Ed25519 verification dependency and synchronized the lock file.
- Packaged the three JSON contracts and a public-only trust root with no default update channel.
- Added additive migration 13 for snapshots, active/previous state, previews, activations, observations, plans, runs, validation evidence, reports, and exact transport variant metadata.
- Added strict domain records with digest/time invariants, external-license blocking, secret-like field rejection, and honest passed-evidence requirements.
- Focused evidence: 17 migration/model/schema tests passed; Ruff check passed; formatting and `git diff --check` passed.

### Implementation checkpoint 2

- Added exact `streamable_http` versus legacy `sse` catalog metadata while preserving the existing network runner and legacy API type.
- Added conservative evidence mapping that never infers official status, stable redacted diagnostic codes, deterministic fixture adapters/import documents, and explicit service dependency-injection seams.
- Added shared typed web contracts for capability, snapshot, compatibility, import, plan, and diagnostics.
- Focused evidence: 51 API/catalog/registry/model/migration tests passed; Python lint, TypeScript compile, Prettier, and `git diff --check` passed.

### Implementation checkpoint 3 - offline discovery

- Expanded the final bundled recovery catalog to 70 distinct entries with the vendor-grounded Onshape Labs FeatureScript MCP as an `official_preview`; the two community Onshape records retain their identities and evidence classes.
- Official evidence claims now require an explicitly authoritative primary vendor/publisher record. Legacy metadata never maps to an official class.
- Added bounded read-only machine observation and reason-coded compatible/incompatible/uncertain/blocked results. Observation does not contact a capability endpoint or run a catalog-supplied command.
- Added the merged, searchable, paginated CapabilityView projection across catalog, registered/custom, installation, credential-boolean, and workspace membership state.
- Added thin list/detail/observe APIs and a capability-first responsive UI with stable URL filters, evidence/compatibility badges, comparison cards, progressive details, alternatives, explicit offline provenance, keyboard operation, and accessible narrow layout.
- Focused evidence: 228 package/API tests passed; all 267 web component/service tests passed; production web build passed; five mocked Capability Library Playwright journeys passed, including WCAG serious/critical scan. Ruff, Prettier, and `git diff --check` passed.
- Live Onshape validation remains deliberately deferred: no endpoint contact, authentication, subscription, term acceptance, or paid use occurred.

### Implementation checkpoint 4 - signed catalog updates

- Added bounded canonical signed envelopes with Ed25519 verification, exact SHA-256 payload binding, key identity, issue/expiry windows, monotonic sequence enforcement, strict schemas, duplicate-key rejection, and a 5 MiB ceiling.
- Added immutable bundled/candidate/active/previous snapshots, retention, safe packaged recovery, exact identity/field/provenance diffs, actor/expiry-bound previews, and atomic activation/rollback audit records.
- Catalog reconciliation now accepts an already validated document and caller-owned transaction while preserving custom entries, install/process state, explicit disablement, credential references/booleans, workspace grants, and legacy identities.
- Replaced arbitrary catalog URL loading with exact approved HTTPS channels, bounded reads and timeouts, no redirects, no ambient authentication, and explicit loopback-only test support.
- Added administrator state/preview/activate/rollback APIs, standardized redacted error contracts, active-snapshot capability projection, and an accessible UI panel for no-channel, checking, verified diff, failure, activation, history, and rollback states.
- Focused evidence: 20 signing/snapshot/diff/activation/fetch/API tests passed; 10 component/layout tests passed; production web build and TypeScript/lint/Prettier checks passed; five mocked Playwright journeys passed, including activation/restart projection/rollback and zero install requests.
- The signed update flow changes reviewed metadata only. It does not install, enable, start, authenticate to, or contact any catalog capability.

### Implementation checkpoint 5 - guided MCP onboarding

- Added bounded, duplicate-safe Claude, VS Code, and plain JSON import previews that normalize configuration without executing commands, expanding variables, contacting endpoints, registering servers, retaining pasted source, or exposing credential values.
- Added immutable, expiry- and digest-bound Install Plans for catalog, remote endpoint, local package/command, and host-bridge sources. Plans show exact requirements, steps, effects, validation, rollback, approval gates, license state, and external-term blockers; Wright never accepts vendor terms.
- Added injected local, remote, and host-bridge adapter boundaries plus idempotent apply, structured progress, cancellation, validation, rollback, and explicit residue reporting.
- Added administrator approval/apply/cancel APIs and an accessible multi-source onboarding wizard covering normalization, current-machine observations, exact plan review, credential boundaries, apply progress, completion, changed-plan conflicts, and failure states.
- Focused evidence: 22 parser/security/plan/adapter/API tests passed; 8 web component/layout tests passed; production web build, TypeScript, ESLint, Ruff, Prettier, and Python format checks passed; all three mocked onboarding Playwright journeys passed.
- Production local-package, local-command, and remote-endpoint plans now have reversible registry-backed application adapters; normal validation uses Wright's existing MCP lifecycle. Proprietary host effects remain allowlisted and fail closed until a reviewed host adapter is configured. Tests use deterministic fixtures and did not install software, contact vendors, accept licenses, or mutate proprietary hosts.

### Implementation checkpoint 6 - legacy and user-state preservation

- Added a realistic schema-12 database fixture with catalog, custom, installed-but-disabled, error, credential-definition, tool-disablement, and workspace-membership sentinels.
- Migration 13 now reports redacted backup/preservation diagnostics while retaining the existing verified pre-upgrade backup, one-transaction rollback, idempotency, and old-column reader/writer compatibility.
- Startup now reconciles the active verified snapshot rather than blindly reapplying packaged metadata. Bundled bootstrap initializes only absent state and cannot downgrade a newer active catalog pointer.
- Active capability projection recognizes legacy IDs and aliases from every retained snapshot. Removed catalog rows remain visible whenever installation, process/error, credential, or workspace state belongs to the user; pristine rolled-back rows remain hidden without deletion.
- Existing server, tool, credential, install, and toggle endpoints retain their established response models and persisted-row semantics after migration.
- Focused evidence: all 76 data-vault tests passed with one platform skip; 14 catalog/projection preservation tests passed; 29 neighboring API/startup/catalog compatibility tests passed. Ruff and Python formatting checks passed.

### Implementation checkpoint 7 - validation and workspace enablement

- Added append-only, digest-bound local validation evidence with explicit protocol-step results, failure/blocked/stale states, schema and server-revision binding, credential-binding digests, limitations, and redacted reason codes.
- Added deterministic MCP initialize, initialized notification, tools/list, optional catalog-approved read-only probe, cancellation, and gateway-visibility validation through injected lifecycle boundaries. The production default delegates to Wright's real MCP engine; tests can inject a deterministic client.
- Added engineer/administrator validation and exact single-workspace enablement APIs. Enablement requires current passed evidence for the active catalog snapshot, machine observation, capability schema, server revision, and configured credential binding.
- Extended onboarding and capability details with configured/not-configured credential booleans, local evidence, workspace selection, enabled-workspace visibility, and an explicit warning that availability never grants invocation or destructive-action authority.
- Added negative secret-boundary scans across snapshots, imports, plans, evidence, workspaces, workflows, database rows, and serialized logs.
- Focused evidence: 27 validation/workspace/security/API tests passed; 12 onboarding/library component tests passed; production web build passed; all three mocked onboarding Playwright journeys passed. Prettier and `git diff --check` passed.

### Implementation checkpoint 8 - missing-capability reports

- Replaced prompt-based missing-MCP submission with a keyboard-accessible structured report dialog covering vendor, public source, engineering domain/task, platform, host application, notes, and the visible search/filter context.
- Added a user-owned report repository with explicit submitted/exported/under-review/matched/closed transitions, deterministic retry idempotency, safe public-source URL normalization, bounded fields, and reviewed-capability-only matching.
- New and compatibility APIs record reports outside catalog snapshots and `mcp_servers`; a report cannot become trusted, installable, active, or workspace-enabled through submission or refresh.
- Added role enforcement and redacted validation failures. Credential-bearing URLs and secret-like context fields are rejected without persisting or echoing their values.
- Focused evidence: 5 repository tests and 23 report/neighboring API tests passed; 8 report/library/layout component tests passed; production web build passed; all six mocked Capability Library Playwright journeys passed, including empty-result reporting with no browser prompts.

### Implementation checkpoint 9 - cross-cutting hardening

- Added public wheel/sdist assertions for the catalog, JSON contracts, public-only trust metadata, and the explicit `cryptography` dependency. The standalone distribution can verify signed catalogs without relying on Wright's monorepo dependency graph.
- Added bounded 1,000-record discovery and 100-server import performance coverage plus hostile update-channel coverage for redirects, size/timeout limits, ambient credentials, replay, and concurrent writers.
- Completed every promised discovery filter and detail group, including lifecycle, platform/architecture, maturity, evidence, compatibility, risk, locality, host, validation, installation, field provenance, data touched, reviewed examples, supported-platform claims, and bounded validation history.
- Added an installed/connected precondition before validation. Workspace enablement still requires current digest-bound passed evidence and never grants invocation authority.
- Added reversible default registry adapters for local-package, local-command, and remote-endpoint plans. Adapter-reported failure rolls back; local changes restore prior state, newly imported remote rows are deleted, and residue is surfaced rather than hidden. Proprietary host effects remain separately reviewed and fail closed.
- Added stable IDs to feature-owned controls and complete Escape, focus-trap, and focus-restore behavior to all dialogs. Mocked browser acceptance now completes apply, validation, and workspace-A-only enablement for local-package, remote-endpoint, and host-bridge backends.
- Added an actual local FastAPI plus deterministic child MCP system smoke and live-local browser annotations without turning external services into a routine gate.
- Feature implementation commits before final hardening: `eaf5cc1`, `92c47dd`, `8347adb`, `5f29566`, `ac4903c`, `16564fb`, `13f2e73`, and `60166c2`.

Focused evidence against the hardened tree:

- 75 capability/package/API/system Python tests passed.
- 285 web component/service tests passed.
- 10 focused mocked Playwright journeys passed.
- Linux AMD64, Linux ARM64/GB10, and Windows AMD64 MCP bundle verifiers passed.
- Four standalone packaging tests passed.
- Ruff, Python format, ESLint, Prettier, TypeScript, production web build, strict MkDocs, and `git diff --check` passed. ESLint retained three pre-existing warnings and no errors.

Rollback proof is deterministic: signed catalog activation restores the named prior snapshot; failed adapter effects invoke rollback; local registry rows restore their prior values; newly imported remote rows are removed; cancellation records residue explicitly; and no routine test writes credentials, accepts a license, contacts Onshape, mutates a proprietary host, or actuates hardware.

### Quickstart acceptance rerun

| Quickstart section | Evidence status | Result |
|---|---|---|
| 1. Bundled catalog | Deterministic | Passed offline discovery, source labeling, compatibility/recovery reasons, and zero-process/zero-user-state mutation tests. |
| 2. Signed update and rollback | Deterministic | Passed activation, restart, rollback, adversarial-envelope, interrupted-write, and user-state preservation tests. |
| 3. Onshape evidence | Deterministic metadata | Passed distinct identity, vendor source, official-preview, prerequisite, and unvalidated-limitation checks; no endpoint contact occurred. |
| 4. Safe configuration import | Deterministic | Passed Claude, VS Code, plain-server, malformed, mixed, duplicate, secret-bearing, shell-like, and oversized input coverage with zero preview effects. |
| 5. Exact preflights | Deterministic | Passed local-package, remote-endpoint, host-bridge, missing-requirement, stale-observation, blocked-record, digest, and material-change coverage. |
| 6. Apply, validate, workspace | Deterministic | Passed all three backends through ordered effects, MCP lifecycle validation, workspace-A-only availability, no invocation authority, and rollback/residue checks. |
| 7. User journey/accessibility | Deterministic | Passed component states, keyboard journeys, focus behavior, live regions, non-color status text, and serious/critical automated accessibility scans. |
| Optional Onshape live validation | Deferred external | Requires the user to accept external terms and provide permitted credentials. It remains explicitly unvalidated and is not a normal gate. |

SC-009's five-person moderated usability target also remains unvalidated until the study occurs. Automated journey and accessibility evidence is not represented as a substitute for human study evidence.

### Final hardening and merge-gate evidence

- Repaired native schema compatibility after migration 13 exposed a stale schema-12 ceiling, isolated duplicate test-fixture module names, regenerated packaged native assets, and kept capability runtime labels provider-neutral.
- Preserved offline discovery by removing the browser's external font request and by projecting legacy validation summaries conservatively when current digest-bound evidence is absent.
- Made onboarding import previews application-scoped so preview and plan requests retain the same bounded in-memory state, and added explicit copy that source review installs, connects, and enables nothing.
- Updated the retained UI-alignment test to assert the current capability-card layout rather than removed legacy server-card identifiers.
- Final hardening commits: `c9d1ea7`, `0a83a67`, `2d51ba9`, `f1291b9`, `5f1765e`, `ebd1be8`, `85105b5`, `3bac0ab`, and `04d340e`.
- Standalone live-browser preflight: 135 passed and 1 intentionally skipped across Chromium, Firefox, WebKit, and the desktop-surface project.
- Authoritative `scripts/check-dev-merge.sh` passed on `04d340e` after fetching `origin/dev` at `c6dc90c`; `origin/dev` was already an ancestor of the feature tip and required no conflict resolution.
- Gate evidence: 1,592 Python tests collected with 1,540 passed and 52 skipped; 86 release tests passed; 140 native/release tests passed and 9 skipped; 206 coverage tests passed and 9 skipped at 85.48%; 44 security-boundary tests passed and 2 skipped; standalone wheel and source distributions built and clean-installed; 285 web tests and 13 Hermes plugin tests passed; production web build and strict documentation passed; 135 live Playwright tests passed and 1 skipped.
- The broad mypy pass retained its established warning-mode duplicate `conftest` diagnostic. Focused release-source mypy passed, and the authoritative gate treats the broad diagnostic as a warning rather than a failure.

### Integration checkpoint (completed)

The documentation-complete exact tree was gated again before publication. The feature was pushed and merged only after the final `origin/dev` race check, and its feature/merged tree hashes were required to match.

### Integration result

- Exact-tree confirmation gate passed on feature tip `538ede1` with the same authoritative suite profile recorded above.
- Pushed `origin/068-capability-library` at `538ede1`.
- Merged with `--no-ff` into `dev` as `7093b55` (`Merge capability library and MCP onboarding`) and pushed GitHub.
- Local/remote feature commit identities matched, local/remote `dev` commit identities matched, and the feature and merged tree hashes both equaled `87f8e70cd3de2d21e58aeee62a2c66bff4867645`.
- Worktree was clean after integration; no `main` merge or release action occurred.

## Loop 069

### Spec Kit phases

- [x] `speckit-git-feature`: branch `069-rivet-mcp-gateway` created from clean synchronized `dev` at `7093b55`.
- [x] `speckit-specify`: five prioritized user journeys, 35 functional requirements, five non-functional requirements, ten measurable outcomes, and a 16/16 specification-quality checklist completed and subsequently strengthened by checklist/analysis remediation.
- [x] `speckit-clarify`: no critical ambiguity required a user question. Safest reversible defaults are explicit for run-bound authority, exact capability binding, stale-review invalidation, existing per-call approval policy, cancellation truthfulness, deterministic normal tests, optional live applications, and closed Gate E.
- [x] `speckit-plan` and Gate B decision: native Rivet MCP nodes use an injected Wright provider over an exact-origin loopback bridge; opaque authority is memory-only and bound to one run/workspace/review/binding set; exact external bindings invalidate on workflow, graph, node, schema, server, validation, grant, or policy change; approval remains exact-call and Wright-owned; cancellation revokes authority and explicitly reaches the gateway child request; bounded Run Manifest evidence records truth without credentials.
- [x] `speckit-checklist`: 42/42 security, authority, binding, approval, cancellation, lifecycle, evidence, UX, dependency, and recovery requirements-quality checks passed after adding explicit authority lifetime, performance, evidence-bound, and accessibility NFRs plus a deterministic performance outcome.
- [x] `speckit-tasks`: 89 dependency-ordered tasks cover shared authority/persistence/runner foundations; all five user stories with tests-first checkpoints; deterministic two-child, cancellation, BREP/host lifecycle, evidence, performance, security, accessibility, packaging, exact-tree gate, and merge work. All tasks pass the required checkbox/ID/story/path format.
- [x] `speckit-analyze` and remediation: all 49 buildable FR/NFR/SC items map to the 89-task graph; the separate five-engineer SC-009 remains explicitly deferred, with zero unmapped tasks and no constitution conflict. Repaired the stable API path, runner-supplied tool-name contradiction, actual gateway cancellation API, explicit tracing/logging work, authorized artifact boundary, exactly-once terminal manifest lifecycle, dedicated loopback isolation, and fail-closed MCP prompt scope.
- [ ] `speckit-implement`
- [ ] Focused, integration, UI, packaging, and documentation verification
- [ ] Full exact-tree dev gate
- [ ] Push feature, merge to `dev`, push `dev`, verify synchronization

### Implementation checkpoint 1 - authority, persistence, and runner protocol

- Added migration 14 with additive immutable binding-set/binding, Run Manifest, child-call, and exact-call approval storage while preserving schema-13 workflow reviews and runs.
- Added canonical secret-rejecting models for exact bindings, binding sets, pending approvals, child evidence, authorized artifacts, and exactly-once terminal manifests.
- Added memory-only 256-bit run authority with exact loopback audience, run/generation/node/binding scope, expiry, revocation, terminal, and restart invalidation.
- Added workspace-scoped capability discovery and deterministic binding projection, current-state stale comparison, bounded result/evidence redaction, authorized Wright artifact enforcement, and exact one-shot approval waiting in the governed gateway bridge.
- Upgraded the pinned Rivet worker to protocol v2 while retaining protocol-v1 non-MCP execution. It validates exact loopback grants, transforms MCP nodes only in memory, injects a Wright provider, sends no server/tool namespace as call authority, rejects project child configuration/dynamic names/prompts/missing-or-extra bindings, and redacts run tokens from output.
- Added the API composition graph for feature settings, repository, authority, approvals, discovery, and the gateway bridge. The feature defaults off until a reviewed MCP execution path is issued.
- Rebuilt and integrity-pinned the 12.9 MiB Node worker at Rivet source revision `4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053`, package `2.1.9`, protocol `2`.
- Focused evidence: 47 Python migration/model/authority/discovery/evidence/bridge/validation/runtime tests and eight Node runner contract tests passed; runner manifest integrity reported `available`; Ruff, Python formatting, Prettier, and `git diff --check` passed.

### Next checkpoint

Implement User Story 1: preview only current workspace-enabled capabilities, resolve every MCP node to one exact binding, persist/review the immutable binding set, expose stale reasons, and add the binding/review API and accessible UI without invoking a child.

## Program guardrails

- No paid usage, license acceptance, external production mutation, user-data deletion, physical actuation, `dev` to `main` merge, or release publication.
- Normal tests use deterministic fixtures, not proprietary apps, paid credentials, GPUs, or hardware.
- `.local-run/`, downloaded repositories, model weights, caches, and build output remain untracked.
