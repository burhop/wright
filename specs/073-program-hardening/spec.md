# Feature Specification: Engineering Capability Program Hardening

**Feature Branch**: `codex/rivet-engineering-program`

**Created**: 2026-08-13

**Status**: Draft

**Input**: User description: "Harden the complete Wright engineering capability experience for usability, compatibility, diagnostics, upgrade, rollback, offline operation, native and Docker persistence, and deterministic release gates without publishing a release."

## Clarifications

### Session 2026-08-13

- Q: What evidence establishes usability completion without an available moderated engineer panel? → A: Deterministic human-repeatable walkthroughs and automated task/recovery assertions are acceptance evidence; an external moderated study remains a clearly labeled follow-up.
- Q: How may support diagnostics leave the local appliance? → A: Only as a user-previewed, explicitly confirmed, inert local export; no automatic upload or remote support destination is introduced.
- Q: What happens when rollback cannot safely expose state written by a newer version? → A: Preserve and quarantine the newer state with an explicit compatibility explanation; never delete it or let the older runtime claim it as current.
- Q: When may a platform or architecture be called supported? → A: Only when exact artifact-bound lifecycle and persistence evidence exists for that platform/architecture; fixture, contract, skipped, or inferred results remain non-supporting evidence.
- Q: What integration action closes the program? → A: One exact-tree authoritative development gate, one reviewed no-fast-forward merge to `dev`, and synchronization with `origin/dev`; no `main` merge or release action.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Complete a guided engineering journey (Priority: P1)

As an engineer, I can move from an unfamiliar capability through inspection, compatibility review, workspace enablement, Rivet preflight, execution, evidence review, and safe recovery without needing to understand Wright's internal architecture.

**Why this priority**: The catalog, models, and Rivet capabilities are only valuable when engineers can discover the next safe action and understand why an action is blocked.

**Independent Test**: Follow deterministic first-use journeys for one MCP-only scenario and one MCP-plus-local-model scenario, using only visible instructions and recovery actions, and verify that every decision can be completed without source-code knowledge.

**Acceptance Scenarios**:

1. **Given** a clean supported installation with no enabled engineering capability, **When** an engineer follows the Capability Library journey, **Then** the engineer can inspect trust and compatibility, complete a reviewed plan, enable the capability, and see the next Rivet action within five minutes in the deterministic walkthrough.
2. **Given** an incompatible, unavailable, unvalidated, or externally blocked capability, **When** the engineer inspects it, **Then** the interface states what is known, what is missing, whether the block is local or external, and one safe recovery or follow-up without offering a misleading start action.
3. **Given** a completed or failed scenario, **When** the engineer reviews the report, **Then** provider identities, engineering assertions, material evidence, observations, cleanup, and next action are understandable without exposing commands, credentials, private paths, model features, or reusable authority.

---

### User Story 2 - Diagnose and recover safely (Priority: P1)

As an engineer or support maintainer, I can inspect a bounded diagnostic summary, preview exactly what it contains, export it deliberately, and use stable recovery guidance without disclosing proprietary engineering data.

**Why this priority**: Multi-provider engineering workflows fail across application, runtime, policy, compatibility, and cleanup boundaries; support evidence must identify the boundary without becoming a data-exfiltration path.

**Independent Test**: Create deterministic capability, model, gateway, Rivet, cancellation, residue, and upgrade failures; verify stable attribution and recovery, preview a diagnostic bundle, export it, and scan all surfaces for secrets and proprietary payloads.

**Acceptance Scenarios**:

1. **Given** a failure at any managed provider boundary, **When** diagnostics are opened, **Then** the engineer sees the responsible provider kind, stable reason, safe identities and digests, cleanup truth, and an actionable recovery step.
2. **Given** a diagnostic export request, **When** the engineer reviews the preview, **Then** every included category, omission, redaction, truncation, and time/run scope is visible before explicit confirmation.
3. **Given** credentials, environment values, private paths, model inputs, proprietary artifact bodies, prompts, or reusable authority in underlying state, **When** diagnostics are built, displayed, logged, or exported, **Then** those values are absent or irreversibly redacted while safe correlation remains possible.
4. **Given** a failed, cancelled, or residue-possible operation, **When** the engineer follows recovery, **Then** late success is suppressed and inspect-before-retry is required wherever cleanup is not proven clean.

---

### User Story 3 - Upgrade, roll back, and work offline (Priority: P1)

As an engineer, I can upgrade or roll back Wright while preserving compatible catalog, workspace, model, workflow, cache, and evidence state, and I can understand exactly which state is retained, migrated, rebuilt, or removed.

**Why this priority**: The program introduced new durable catalogs, packages, bindings, manifests, reports, and caches; an ordinary upgrade must not silently discard user choices or make stale evidence appear current.

**Independent Test**: Start from the recorded predecessor state, populate representative Loop 068-072 data, perform upgrade, restart, offline use, rollback, uninstall, reinstall, and purge drills, and compare exact retained-state inventories at every transition.

**Acceptance Scenarios**:

1. **Given** a supported predecessor with local custom catalog entries, disabled items, workspace grants, tested model installations, Rivet bindings, reports, and cached public artifacts, **When** Wright upgrades, **Then** state is preserved or migrated additively and every stale identity requires fresh review rather than silent rebinding.
2. **Given** an interrupted or incompatible upgrade, **When** Wright restarts, **Then** the previous usable version or an explicit recoverable state remains available with no mixed-version success claim.
3. **Given** an offline host after a successful upgrade or rollback, **When** the engineer uses previously available capabilities and evidence, **Then** no network is required and unavailable remote refreshes degrade to visible cached state.
4. **Given** uninstall or purge, **When** the engineer reviews and confirms the exact effect, **Then** executable runtime removal, retained user data, referenced evidence, reclaimable cache, and irreversible deletion are distinguished and reference-safe.

---

### User Story 4 - Use the experience accessibly during long operations (Priority: P2)

As an engineer using keyboard navigation, magnification, narrow layouts, reduced motion, or assistive technology, I can complete the same inspection, confirmation, progress, cancellation, diagnosis, and recovery journeys without losing context.

**Why this priority**: Long-running installs and engineering workflows are high-consequence operations; status, cancellation, and recovery cannot depend on color, animation, pointer use, or a wide display.

**Independent Test**: Exercise the complete journeys at 320 CSS pixels and 200% zoom using keyboard-only interaction and automated accessibility analysis, including loading, blocked, confirming, running, cancelling, failed, residue, and restored states.

**Acceptance Scenarios**:

1. **Given** any critical operation state, **When** it changes, **Then** status is conveyed in text, focus remains predictable, live updates are bounded, and controls retain accessible names and disabled reasons.
2. **Given** a long operation, **When** progress is delayed or repeated, **Then** the engineer sees the current phase, elapsed observation, cancellation availability, and a non-deceptive stalled or timeout state without an endless indeterminate success impression.
3. **Given** browser reload or application restart, **When** the engineer returns, **Then** durable progress or terminal truth is restored and focus reaches the recovery or next-action summary.

---

### User Story 5 - Trust the supported environment and merge gate (Priority: P2)

As a maintainer, I can determine which native and Docker environments have evidence, rehearse release readiness without publication, and rely on the development merge gate to reproduce every deterministic failure found during the engineering capability program.

**Why this priority**: Support claims and release confidence must follow exact evidence rather than fixture-only success or inferred architecture support.

**Independent Test**: Build distribution candidates once, exercise the available host and container lifecycle/persistence matrix, validate compatibility records and rehearsal evidence, and run the authoritative development merge gate against the exact integration tree.

**Acceptance Scenarios**:

1. **Given** a platform or architecture claim, **When** support status is inspected, **Then** it points to exact lifecycle evidence or is labeled unverified; skipped and fixture-only runs never create a support claim.
2. **Given** native and Docker candidates, **When** deterministic lifecycle and persistence tests run, **Then** install/start/status/doctor/use/stop/update/rollback/uninstall behavior and catalog/model/cache retention are covered without publishing or contacting paid/proprietary systems.
3. **Given** a regression found during Loops 068-073, **When** the merge gate runs, **Then** a deterministic local check fails for that regression class and the contributor documentation names the gate.
4. **Given** the final integration branch and latest remote development state, **When** the gate passes and the branch is merged, **Then** the merged tree equals the tested tree and local and remote development refs are synchronized.

### Edge Cases

- A catalog update changes metadata while the user has a local custom entry, disabled official item, cached snapshot, or workspace grant.
- A model or MCP is present but its platform, license, runtime, validation, policy, or resource evidence becomes stale during an upgrade.
- Upgrade is interrupted between artifact activation and durable state migration, or rollback starts after a partial restart.
- The current version can read predecessor state but the predecessor cannot understand newly created state.
- Diagnostics contain nested secrets, credential-shaped keys, local usernames, UNC paths, proprietary filenames, unusually large values, binary bodies, or adversarial text intended to escape redaction.
- A run produces thousands of events, repeated progress, partial provider receipts, unavailable provider evidence, truncated artifacts, or possible cleanup residue.
- The browser reloads during confirmation, cancellation, export preview, or recovery and must not repeat a mutation or recreate authority.
- A supported architecture lacks a local host during this loop; deterministic contract evidence must not be relabeled as native lifecycle evidence.
- Docker is available but optional MCP host software, GPU, paid credentials, or proprietary applications are not.
- Release rehearsal succeeds locally while a required cross-platform or registry-dependent production check remains unavailable; rehearsal must remain non-publishing and incomplete.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Wright MUST define versioned representative engineering journeys spanning capability discovery, trust/compatibility review, reviewed plan, workspace enablement, Rivet preflight, run, report, diagnosis, upgrade/rollback, and uninstall.
- **FR-002**: Every journey step MUST present one primary next action, its consequence, and any exact blocker without requiring knowledge of package, process, protocol, or database internals.
- **FR-003**: Capability, model, and scenario surfaces MUST distinguish loading, empty, available, blocked, incompatible, stale, confirming, running, cancelling, failed, residue-possible, and restored states.
- **FR-004**: Support status MUST distinguish verified, partial, fixture-only, unavailable, and externally blocked evidence, and MUST NOT promote a claim from a skipped or fixture-only result.
- **FR-005**: The complete onboarding journey MUST preserve local custom entries, explicit disablement, workspace scope, and review decisions across refresh and restart.
- **FR-006**: Blocked states MUST identify whether recovery is local, requires an optional external prerequisite, or is a recorded follow-up; they MUST NOT imply that unavailable credentials, licenses, applications, hardware, or unreleased services are installed or approved.
- **FR-007**: Scenario reports MUST distinguish material engineering evidence from observations and show provider kind, assertion outcome, cleanup, and safe recovery without executable machine authority.
- **FR-008**: Wright MUST define a bounded diagnostic snapshot with exact scope, generation time, product/runtime identity, platform claim, capability/model/scenario states, safe event summaries, redaction/truncation counts, and recovery categories.
- **FR-009**: Diagnostic preview MUST enumerate every included category and every omitted, redacted, or truncated category before export is confirmable.
- **FR-010**: Diagnostic export MUST require explicit current-user confirmation bound to the exact preview digest and MUST be inert data with no reusable authority, commands, executable content, or auto-upload destination.
- **FR-011**: Diagnostics MUST exclude credentials, tokens, environment values, request bodies, prompts, private model features, artifact bodies, proprietary filenames and paths, database rows, process endpoints, and manager-owned private configuration.
- **FR-012**: Safe correlation MUST use bounded public identities, stable reason/recovery codes, content or evidence digests, counts, timestamps, and redaction facts rather than raw private values.
- **FR-013**: Diagnostic display, export, logs, traces, and error responses MUST apply the same recursive redaction and size boundaries and MUST fail closed on serialization or policy errors.
- **FR-014**: Failures MUST retain provider kind and stable attribution across catalog, acquisition, runtime, gateway, Rivet, model, scenario, persistence, and lifecycle boundaries.
- **FR-015**: Cancellation MUST revoke transient authority before provider cancellation, suppress late success, and report clean cleanup or bounded possible residue with inspect-before-retry recovery.
- **FR-016**: Wright MUST define an additive compatibility contract for catalog snapshots, user catalog overrides, disablement, workspace grants, model packages/installations/evidence, workflow bindings, run manifests, scenario reports, caches, and diagnostic records.
- **FR-017**: Upgrade MUST inventory retained, migrated, invalidated, rebuilt, and removed state before mutation and MUST preserve prior usable state until activation and required migrations succeed.
- **FR-018**: Upgrade and rollback MUST be restart-safe, idempotent for the same exact plan, and incapable of claiming mixed-version state as successful.
- **FR-019**: Material identity changes after upgrade or rollback MUST invalidate affected readiness/review evidence and require explicit fresh review; cached bytes alone MUST NOT preserve authority.
- **FR-020**: Rollback MUST restore a compatible prior runtime and configuration while preserving newer durable data in a form that is either backward-readable or explicitly quarantined from the older version.
- **FR-021**: Offline operation after install, upgrade, or rollback MUST use verified local snapshots/artifacts and MUST expose remote refresh as unavailable rather than failing unrelated local capabilities.
- **FR-022**: Uninstall and purge MUST use reviewed effect plans that distinguish runtime removal, retained user state, reference-held evidence, reclaimable cache, and irreversible deletion.
- **FR-023**: Reference-safe purge MUST refuse deletion while any installation, workspace, workflow run, report, export, lease, or rollback record requires the content.
- **FR-024**: Native and Docker lifecycle tests MUST populate representative catalog, model, workspace, Rivet, scenario, cache, and evidence state before update/rollback/uninstall persistence assertions.
- **FR-025**: Compatibility evidence MUST bind product version, artifact digest, platform, architecture, manager profile when applicable, lifecycle steps, persistence assertions, source isolation, and forbidden executable audit.
- **FR-026**: Windows x64, Linux x64, Linux ARM64, macOS x64/ARM64, and Docker support MUST remain evidence-driven; unavailable environments MUST remain explicitly unverified rather than blocking deterministic work on available environments.
- **FR-027**: Docker validation MUST use the clean selected-server process and MUST NOT add MCP-specific host software to the base image merely to make catalog validation pass.
- **FR-028**: Release rehearsal MUST build or select immutable candidates once, perform only local/non-publishing validation, and never create tags, publish packages/images/docs, accept licenses, or mutate production systems.
- **FR-029**: The development merge gate MUST include deterministic tests for every regression class found during Loops 068-073 and MUST remain the feature-to-development source of truth.
- **FR-030**: If CI exposes a deterministic failure absent from the merge gate, the gate and contributor documentation MUST be updated in the same fix.
- **FR-031**: Every critical interactive control MUST have a stable test identity, accessible name, keyboard operation, visible focus, and text that does not rely on color alone.
- **FR-032**: Critical journeys MUST remain usable at 320 CSS pixels, 200% zoom, keyboard-only navigation, and reduced-motion preferences without hidden confirmations, status, cancellation, evidence, or recovery.
- **FR-033**: Long-running operations MUST expose current phase, bounded progress or honest indeterminate status, elapsed observation, cancellation availability, terminal state, and recovery without excessive live-region repetition.
- **FR-034**: Reload and restart MUST restore durable state without replaying confirmation, export, install, enable, start, cancel, update, rollback, uninstall, or purge mutations.
- **FR-035**: Automated accessibility evidence MUST cover normal, blocked, failure, cancellation, residue, restart, comparison, and export-preview journeys and report serious/critical findings separately from pre-existing unrelated warnings.
- **FR-036**: Wright MUST provide support and operator documentation for onboarding, diagnostic preview/export, compatibility interpretation, offline use, update, rollback, uninstall, purge, and retained state.
- **FR-037**: Documentation and interfaces MUST preserve the distinctions among confirmed MCPs, hosted/API candidates, watchlist entries, generated model fixtures, qualified private models, and vetted public models.
- **FR-038**: Gate E MUST remain closed: no test, diagnostic, recovery, rehearsal, or workflow may start printers, spindles, motion, heat, robots, PLCs, or other physical machinery.
- **FR-039**: Normal validation MUST require no paid service, proprietary application, credential, GPU, hardware, large download, remote-code execution, or license acceptance.
- **FR-040**: The final integration MUST incorporate the latest remote development and engineering catalog history, pass the authoritative gate on the exact merge tree, preserve a clean worktree, and verify local/remote synchronization after one reviewed development merge.

### Non-Functional Requirements

- **NFR-001**: Diagnostic preview and ordinary status reads MUST complete within one second for up to 1,000 capabilities, 1,000 model artifacts, 2,000 run events, and 200 retained reports on the reference host.
- **NFR-002**: Diagnostic exports MUST be bounded to 2 MiB, 2,000 records, 4 KiB per safe string, and 100 item values per collection, with explicit truncation evidence.
- **NFR-003**: Cancellation delivery MUST begin within one second and owned cleanup MUST finish within five seconds or record possible residue and a recovery action.
- **NFR-004**: Deterministic material evidence MUST be byte-stable across unchanged runs; time, host, trace, request, and observed resource values MUST remain separate observations.
- **NFR-005**: State migrations and lifecycle plans MUST be atomic, restart-safe, and idempotent for the same immutable identity.
- **NFR-006**: Offline paths MUST perform zero network requests and fail remote-only refreshes within two seconds with cached-state guidance.
- **NFR-007**: Security scans MUST find zero credential, private path, raw engineering payload, model weight, reusable authority, or forbidden executable in diagnostic and distribution artifacts.
- **NFR-008**: Accessibility analysis MUST report zero serious or critical findings in the scoped critical journeys.
- **NFR-009**: Compatibility and release evidence MUST be schema-valid, content-digest-bound, and capped so one platform result cannot overwrite or imply another.
- **NFR-010**: All new boundaries MUST use structured logging and local trace correlation with safe fields only.

### Key Entities

- **Engineering Journey**: Versioned sequence of user-visible states, actions, blockers, recovery, environment, and measurable completion evidence for one representative workflow.
- **Diagnostic Snapshot**: Immutable bounded safe projection of current product, platform, capability, model, workflow, run, cleanup, and recovery state plus redaction/truncation facts.
- **Diagnostic Export Plan**: Expiring principal-bound preview, exact effect, policy identity, digest, and confirmation state for one inert local export.
- **State Inventory**: Exact retained, migrated, invalidated, rebuilt, quarantined, removed, and reference-held state associated with an upgrade, rollback, uninstall, or purge plan.
- **Compatibility Evidence**: Platform/architecture/manager/artifact/lifecycle/persistence result with exact validation level and no cross-platform implication.
- **Release Rehearsal Evidence**: Non-publishing candidate identities, deterministic checks, omissions, unavailable external validations, and final readiness decision.
- **Program Gate Finding**: Regression class, first observed failure, deterministic reproducer, owning gate, remediation, and verification evidence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Both representative deterministic engineering journeys complete in no more than five minutes and twenty primary interactions, and every intentionally blocked variant reaches the correct recovery in no more than three primary interactions.
- **SC-002**: One hundred percent of catalog, model, gateway, Rivet, scenario, lifecycle, cancellation, residue, and upgrade failures in the acceptance set show the correct provider category, stable reason, and safe next action with no false success.
- **SC-003**: Diagnostic preview and export pass all secret/private-payload scans across at least twenty adversarial value classes, stay within declared limits, and retain exact safe correlation for every included failure.
- **SC-004**: Predecessor-to-current upgrade, current-to-predecessor rollback, reinstall, uninstall, purge, restart, and offline drills preserve or explicitly account for one hundred percent of seeded durable state.
- **SC-005**: Unchanged retained catalog/model/workflow/run material identities compare equal after restart; every deliberately changed material identity becomes stale or appears as an explicit difference.
- **SC-006**: Available native and Docker lifecycle tests pass every claimed step and persistence assertion; unavailable platform/architecture combinations produce zero supported claims.
- **SC-007**: Every critical journey passes keyboard-only, 320 CSS pixel, 200% zoom, reduced-motion, focus restoration, non-color status, and automated accessibility checks with zero serious/critical findings.
- **SC-008**: Progress and cancellation tests produce no late success, no repeated mutation, cancellation delivery within one second, and either clean owned cleanup within five seconds or explicit residue recovery.
- **SC-009**: Normal gates perform zero paid/proprietary/hardware actions, zero license acceptance, zero private data publication, and zero physical actuation.
- **SC-010**: The development merge gate passes on the exact final integration tree and contains a deterministic check for every recorded program gate finding.
- **SC-011**: The integration branch, local development branch, and remote development branch are clean and synchronized after the single reviewed merge, with matching tested/merged tree hashes recorded in the progress log.

## Assumptions

- The user-approved shared integration branch and pre-authorized safest gate decisions supersede the default per-loop branch and manual pause cadence while preserving review records and constitution checks.
- Scripted, human-repeatable engineering walkthroughs and automated usability assertions provide deterministic acceptance evidence; a moderated external engineer study is useful follow-up evidence but is not fabricated or required for this non-publishing closeout.
- Support status follows `src/wright_engineering/compatibility.json` and exact lifecycle evidence. A missing host remains unverified rather than inferred from portable code or fixture tests.
- Existing additive SQLite migrations, content-addressed model storage, catalog snapshots, workflow manifests, and native lifecycle plans are extended rather than replaced.
- Diagnostic exports remain local inert JSON; Wright does not upload support bundles or create an external support service in this feature.
- Existing package, container, and runtime candidates may be built and rehearsed locally, but no release, tag, registry publication, production environment change, or `dev`-to-`main` merge is authorized.
- Optional proprietary applications, hosted services, credentials, GPUs, hardware, and unreleased MCP servers remain transparent external follow-ups and do not block independent deterministic work.
