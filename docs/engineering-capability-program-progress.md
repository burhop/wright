# Wright Engineering Capability Program Progress

**Last updated**: 2026-08-12
**Current loop**: 068 - Capability Library and MCP onboarding
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
- [x] `speckit-checklist`: 40 UX, security, compatibility, recovery, and testability requirements-quality checks pass.
- [x] `speckit-tasks`: 119 dependency-ordered tasks with story checkpoints, test-first slices, traceability, hardening, and merge verification.
- [x] `speckit-analyze` and remediation: initial two high/two medium findings repaired; rerun has 45/45 requirement coverage, zero critical/high findings, and no constitution conflict.
- [ ] `speckit-implement`
- [ ] Focused, integration, UI, packaging, docs, and full dev gate
- [ ] Push feature, merge to `dev`, push `dev`, verify synchronization

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
- Added injected local, remote, and host-bridge adapter boundaries with fail-closed defaults plus idempotent apply, structured progress, cancellation, validation, rollback, and explicit residue reporting.
- Added administrator approval/apply/cancel APIs and an accessible multi-source onboarding wizard covering normalization, current-machine observations, exact plan review, credential boundaries, apply progress, completion, changed-plan conflicts, and failure states.
- Focused evidence: 22 parser/security/plan/adapter/API tests passed; 8 web component/layout tests passed; production web build, TypeScript, ESLint, Ruff, Prettier, and Python format checks passed; all three mocked onboarding Playwright journeys passed.
- Default production adapters remain fail-closed until a reviewed capability-specific backend is configured. Tests use deterministic fakes and did not install software, contact vendors, accept licenses, or mutate proprietary hosts.

### Implementation checkpoint 6 - legacy and user-state preservation

- Added a realistic schema-12 database fixture with catalog, custom, installed-but-disabled, error, credential-definition, tool-disablement, and workspace-membership sentinels.
- Migration 13 now reports redacted backup/preservation diagnostics while retaining the existing verified pre-upgrade backup, one-transaction rollback, idempotency, and old-column reader/writer compatibility.
- Startup now reconciles the active verified snapshot rather than blindly reapplying packaged metadata. Bundled bootstrap initializes only absent state and cannot downgrade a newer active catalog pointer.
- Active capability projection recognizes legacy IDs and aliases from every retained snapshot. Removed catalog rows remain visible whenever installation, process/error, credential, or workspace state belongs to the user; pristine rolled-back rows remain hidden without deletion.
- Existing server, tool, credential, install, and toggle endpoints retain their established response models and persisted-row semantics after migration.
- Focused evidence: all 76 data-vault tests passed with one platform skip; 14 catalog/projection preservation tests passed; 29 neighboring API/startup/catalog compatibility tests passed. Ruff and Python formatting checks passed.

### Implementation checkpoint 7 - validation and workspace enablement

- Added append-only, digest-bound local validation evidence with explicit protocol-step results, failure/blocked/stale states, schema and server-revision binding, credential-binding digests, limitations, and redacted reason codes.
- Added deterministic MCP initialize, initialized notification, tools/list, optional catalog-approved read-only probe, cancellation, and gateway-visibility validation through injected lifecycle boundaries. Production remains fail-closed when no reviewed client is configured.
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

### Next checkpoint

Complete packaging, bounded-performance, security, local system smoke, documentation, accessibility, quickstart, and authoritative merge-gate hardening for Loop 068.

## Program guardrails

- No paid usage, license acceptance, external production mutation, user-data deletion, physical actuation, `dev` to `main` merge, or release publication.
- Normal tests use deterministic fixtures, not proprietary apps, paid credentials, GPUs, or hardware.
- `.local-run/`, downloaded repositories, model weights, caches, and build output remain untracked.
