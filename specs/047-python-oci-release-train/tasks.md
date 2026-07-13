# Tasks: Python and OCI Release Train

**Input**: Design documents from `/specs/047-python-oci-release-train/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Required by the feature specification. Write policy and contract tests before the corresponding implementation and retain failure evidence where practical.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish release-domain structure, current-state evidence, and shared validation fixtures.

- [x] T001 Record the Feature 047 baseline, selected R3 roadmap items, and in-progress state in docs/gpt5-6-implementation-status.md
- [x] T002 Inventory every version consumer, public package candidate, tag trigger, image build, promotion path, workflow action, permission, and release document in specs/047-python-oci-release-train/research.md
- [x] T003 [P] Create the release-domain Python package skeleton in scripts/release/__init__.py
- [x] T004 [P] Create shared release fixtures for valid/mismatched identities, artifacts, digests, reports, and manifests in tests/release/fixtures/
- [x] T005 [P] Add the release test marker and focused suite paths to pyproject.toml
- [x] T006 Verify .gitignore and .dockerignore exclude generated release artifacts, evidence scratch data, credentials, caches, and source-control metadata in .gitignore and .dockerignore

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Define common version, evidence, policy, and workflow validators used by every story.

- [x] T007 [P] Add failing release identity/tag/PEP 440 mismatch tests in tests/release/test_version_contract.py
- [x] T008 [P] Add failing release evidence schema, state-order, and subject-consistency tests in tests/release/test_release_evidence.py
- [x] T009 [P] Add failing semantic workflow pin, permission, environment, and dependency-order tests in tests/release/test_workflow_policy.py
- [x] T010 Implement canonical product version parsing and tag/metadata/changelog/label validation in scripts/release/version.py
- [x] T011 Implement typed release identity, artifact, OCI, promotion, stage, and recovery records in scripts/release/evidence.py
- [x] T012 Implement JSON schema and transition validation against specs/047-python-oci-release-train/contracts/release-evidence.schema.json in scripts/verify-release-evidence.py
- [x] T013 Implement dirty-source, reviewed-commit, conflict, and dry-run preflight in scripts/release-preflight.py
- [x] T014 Implement semantic GitHub Actions YAML validation for full SHA pins, least privilege, protected environments, and required dependencies in scripts/release/workflow_policy.py
- [x] T015 Convert brittle legacy release substring tests to semantic shared assertions in tests/test_publish_python_packages_workflow.py and tests/test_release_policy.py
- [x] T016 Run the foundational release contract suite and update specs/047-python-oci-release-train/quickstart.md with exact passing commands

**Checkpoint**: One validated release identity and evidence model can fail closed before artifact work begins.

---

## Phase 3: User Story 1 - Produce Intentional Python Artifacts (Priority: P1) 🎯 MVP

**Goal**: Build a small public wheel/sdist pair once, prove safe contents, independently install both across the supported matrix, and expose useful dependency-safe commands.

**Independent Test**: Build from a clean checkout, validate exact content/hashes, install wheel and sdist with no source access on Python 3.11-3.14, and run every public command.

### Tests for User Story 1

- [x] T017 [P] [US1] Add failing wheel/sdist allowlist, traversal, symlink, secret, and unrelated-file tests in tests/release/test_python_artifacts.py
- [x] T018 [P] [US1] Add failing internal-package classifier and public-dependency-graph tests in tests/release/test_private_packages.py
- [x] T019 [P] [US1] Add failing version/doctor/appliance/config/MCP command and private-import tests in tests/release/test_public_cli.py
- [x] T020 [P] [US1] Add failing wheel-versus-sdist-build parity and isolated install-plan tests in tests/release/test_python_install_matrix.py

### Implementation for User Story 1

- [x] T021 [US1] Add explicit Hatch wheel and sdist include/exclude policies plus Python 3.14 metadata/classifier alignment in pyproject.toml
- [x] T022 [US1] Mark all workspace-internal distributions Private :: Do Not Upload and bound/private dependencies in packages/*/pyproject.toml and apps/api/pyproject.toml
- [x] T023 [US1] Enforce the sole-public-distribution allowlist and reject wright-core/internal publication in scripts/release/python_artifacts.py
- [x] T024 [US1] Implement safe archive inspection, deterministic content manifests, SHA-256 files, metadata/readme checks, and sensitive-content scanning in scripts/release/python_artifacts.py
- [x] T025 [US1] Update scripts/build-python-distributions.sh to build wheel/sdist once, remove release-path skip-clean-install behavior, compare sdist-built wheel contents, and emit evidence
- [x] T026 [P] [US1] Implement dependency-free version and doctor diagnostics in src/wright_engineering/diagnostics.py
- [x] T027 [P] [US1] Implement authenticated appliance status and configuration diagnostic/dry-run helpers in src/wright_engineering/appliance.py
- [x] T028 [P] [US1] Implement the direct provider-neutral STDIO MCP bridge client in src/wright_engineering/mcp_bridge.py
- [x] T029 [US1] Compose stable version/doctor/appliance/config/mcp commands and collision diagnostics in src/wright_engineering/cli.py and src/wright_engineering/__init__.py
- [x] T030 [US1] Add a Python 3.11-3.14 wheel/sdist independent install matrix with source-tree isolation, uninstall/reinstall, import, and command smokes in .github/workflows/ci.yml
- [x] T031 [US1] Run the local package build/content/install suite and record exact artifact counts, sizes, hashes, and commands in docs/gpt5-6-implementation-status.md

**Checkpoint**: User Story 1 is independently usable as a trustworthy public CLI artifact set.

---

## Phase 4: User Story 2 - Validate One Release Identity (Priority: P1)

**Goal**: Bind all package/image/workflow consumers to one immutable version and reviewed commit.

**Independent Test**: Inject tag, metadata, changelog, image-label, plugin-range, dirty-tree, and retry conflicts and prove preflight rejects each one.

### Tests for User Story 2

- [x] T032 [P] [US2] Add matrixed dirty checkout, tag/version/changelog/label/compatibility mismatch tests in tests/release/test_release_preflight.py
- [x] T033 [P] [US2] Add identical-retry and conflicting-subject tests in tests/release/test_release_identity_conflicts.py

### Implementation for User Story 2

- [x] T034 [US2] Replace independently parsed workflow versions with preflight outputs in .github/workflows/release.yml and .github/workflows/publish-python-packages.yml
- [x] T035 [US2] Align OCI labels, Python metadata, docs examples, and integration compatibility declarations to the canonical version in docker/Dockerfile, docs/versioning.md, and relevant manifests
- [x] T036 [US2] Generate the initial immutable release evidence manifest and conflict index from scripts/release-preflight.py
- [x] T037 [US2] Add version consistency and conflicting-retry checks to scripts/check-dev-merge.sh
- [x] T038 [US2] Run valid and adversarial preflight/retry scenarios and record results in specs/047-python-oci-release-train/checklists/completion-audit.md

**Checkpoint**: No artifact build or promotion can begin with an inconsistent release identity.

---

## Phase 5: User Story 3 - Test and Attest One OCI Candidate (Priority: P1)

**Goal**: Build one pinned amd64 candidate, validate that digest, and promote/mirror it without rebuilding.

**Independent Test**: Produce a candidate digest, run smoke/scan/inventory/SBOM/provenance gates by digest, and prove all destination manifests match it.

### Tests for User Story 3

- [x] T039 [P] [US3] Add failing Dockerfile moving-tag, unbounded-upgrade, unchecked-download, Node-line, platform, and inventory tests in tests/release/test_oci_build_policy.py
- [x] T040 [P] [US3] Add failing digest-subject, no-rebuild, alias, mirror-identity, and GitHub attestation tests in tests/release/test_oci_release_contract.py
- [x] T041 [P] [US3] Add failing vulnerability threshold and exception completeness/expiry/scope tests in tests/release/test_vulnerability_policy.py

### Implementation for User Story 3

- [x] T042 [US3] Pin production base images by digest, select Node 24 LTS, pin uv/micromamba/dependency inputs and checksums, remove apt upgrade, and keep amd64 explicit in docker/Dockerfile
- [x] T043 [US3] Document pinned runtime inputs, licenses, architecture limits, update procedure, and rebuild comparison in docker/dependency-inventory.md
- [x] T044 [US3] Define blocking High/Critical fixable policy and exception schema instance in docker/release-policy.json
- [x] T045 [US3] Implement vulnerability report normalization and expiring-exception evaluation in scripts/release/vulnerability_policy.py
- [x] T046 [US3] Implement OCI reference/digest/manifest/promotion/mirror identity helpers in scripts/release/oci.py
- [x] T047 [US3] Convert .github/workflows/docker-build.yml into a reusable build-once amd64 candidate workflow that outputs the pushed digest and evidence artifact
- [x] T048 [US3] Add exact-digest container smoke, content/license inventory, blocking Trivy policy, SPDX SBOM, provenance attestation, and verification jobs in .github/workflows/docker-build.yml
- [x] T049 [US3] Add no-rebuild GHCR tag promotion and optional byte-identical Docker Hub manifest copy/verification jobs in .github/workflows/release.yml
- [x] T050 [US3] Run Docker policy tests and, where the host supports it, build/smoke/inspect the exact local candidate digest; record any genuine host limitation in docs/gpt5-6-implementation-status.md

**Checkpoint**: The tested OCI digest is the only promotable image subject and supported architecture claims are evidence-backed.

---

## Phase 6: User Story 4 - Rehearse Protected Promotion (Priority: P1)

**Goal**: Enforce TestPyPI-first Python promotion, digest-only OCI promotion, post-verification, documentation, and GitHub Release last with no mutations in rehearsal mode.

**Independent Test**: Run the complete dry-run stage machine and semantic workflow tests; inspect the terminal manifest and prove zero public side effects.

### Tests for User Story 4

- [x] T051 [P] [US4] Add failing TestPyPI-before-PyPI, exact-hash download, protected-environment, OIDC, and idempotent-retry tests in tests/release/test_python_publish_contract.py
- [x] T052 [P] [US4] Add failing unified stage-order, optional-mirror, post-verification, docs, and GitHub-Release-last tests in tests/release/test_release_orchestration.py
- [x] T053 [P] [US4] Add dry-run credential rejection, mutation denial, and honest-terminal-status tests in tests/release/test_release_rehearsal.py

### Implementation for User Story 4

- [x] T054 [US4] Convert .github/workflows/publish-python-packages.yml into exact-artifact TestPyPI verification and protected PyPI promotion with OIDC, hash checks, and no build step
- [x] T055 [US4] Replace independent tag builds with the unified dependency graph, scoped permissions, environments, evidence transfers, post-verification, docs, and terminal draft/publish logic in .github/workflows/release.yml
- [x] T056 [US4] Pin every third-party Action in scoped workflows to a verified full commit SHA and document tag provenance in .github/dependabot.yml
- [x] T057 [US4] Add dependency review, CodeQL, Python/npm audit, license, staged type/coverage, plugin lint/package, and scheduled rescan jobs in .github/workflows/
- [x] T058 [US4] Implement the no-publication stage machine, evidence aggregation, and mutation guard in scripts/release-rehearsal.py
- [x] T059 [US4] Add semantic release workflow/rehearsal policy checks to scripts/check-dev-merge.sh
- [x] T060 [US4] Run the complete rehearsal twice and prove deterministic subjects, idempotent transitions, zero credentials, and zero external mutations in test-results/release-rehearsal/

**Checkpoint**: The protected release graph is executable in rehearsal and cannot bypass exact-artifact gates or publish early.

---

## Phase 7: User Story 5 - Recover Safely from Release Failure (Priority: P2)

**Goal**: Make interrupted, conflicting, vulnerable, or divergent releases recoverable without overwriting immutable subjects.

**Independent Test**: Execute all recovery fixtures and inspect safe terminal decisions and commands.

### Tests for User Story 5

- [x] T061 [P] [US5] Add retry, partial upload, conflicting hash, yank/new-patch, quarantine, alias restore, mirror divergence, and draft-release tests in tests/release/test_recovery_drills.py

### Implementation for User Story 5

- [x] T062 [US5] Implement evidence-driven resume/new-patch/yank/quarantine/restore/hold-draft decisions and dry-run commands in scripts/release/recovery.py
- [x] T063 [P] [US5] Document routine release operation, protected prerequisites, verification, and retry semantics in docs/release/release-runbook.md
- [x] T064 [P] [US5] Document PyPI correction/yank, OCI quarantine/alias restore, mirror divergence, evidence retention, and GitHub Release recovery in docs/release/release-recovery.md
- [x] T065 [US5] Execute all recovery drills, verify immutable subjects remain unchanged, and capture results in specs/047-python-oci-release-train/checklists/completion-audit.md

**Checkpoint**: Every named release failure has a safe, auditable, non-overwriting terminal path.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Reconcile documentation, policies, artifacts, full gates, and review evidence.

- [x] T066 [P] Update public artifact topology, sole-public-package policy, supported matrix, and verification commands in docs/release/artifact-topology.md, docs/release/python-packaging.md, docs/release/container-publishing.md, and docs/versioning.md
- [x] T067 [P] Update contributor/release ownership and required-check guidance in CONTRIBUTING.md, SECURITY.md, and docs/release/community-release-readiness.md
- [x] T068 [P] Add release documentation and executable examples to mkdocs.yml and tests/test_docs_release_gate.py
- [x] T069 Reconcile or remove legacy independent release scripts/tests/docs and prove no bypassing tag build or private publication path remains with rg and semantic policy tests
- [x] T070 Run ruff, format, mypy, focused/full pytest, Python package builds and clean installs, npm tests/lint/build, strict docs, workflow policy, and available Docker gates; record exact results in docs/gpt5-6-implementation-status.md
- [x] T071 Complete requirement-by-requirement evidence in specs/047-python-oci-release-train/checklists/completion-audit.md and mark every task/checklist item complete only with authoritative proof
- [x] T072 Run scripts/check-dev-merge.sh with no release-specific skips or timeouts and resolve every failure
- [x] T073 Mark Feature 047 review-ready/complete in docs/gpt5-6-implementation-status.md with migration, rollback, remaining external prerequisites, and exact Feature 048 next action

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup has no dependencies.
- Foundational depends on Setup and blocks all stories.
- US1 and US2 may begin after Foundational; US2 consumes foundational evidence but not US1 runtime code.
- US3 begins after foundational identity/evidence contracts; its image work is independent of US1 CLI implementation.
- US4 integrates completed US1 Python artifacts and US3 OCI candidates and therefore depends on both.
- US5 depends on the US4 stage machine and promotion records.
- Polish depends on all stories.

### User Story Dependencies

- **US1**: Foundational only; delivers the independently testable Python artifact MVP.
- **US2**: Foundational only; independently proves release identity consistency.
- **US3**: Foundational only; independently proves OCI exact-digest validation.
- **US4**: US1 + US2 + US3; orchestrates already-built subjects without changing them.
- **US5**: US4; consumes stage/evidence state to produce recovery decisions.

### Parallel Opportunities

- Setup inventory, fixtures, test configuration, and ignore checks touch separate files.
- Foundational test files can be authored in parallel before shared implementations.
- US1 public CLI modules and artifact policy tests are separable until CLI composition.
- US1, US2, and US3 can proceed concurrently after foundational contracts.
- Documentation tasks T063/T064 and T066-T068 are file-independent.

## Parallel Example: User Story 3

```text
Task T039: Dockerfile policy tests in tests/release/test_oci_build_policy.py
Task T040: Digest/promotion contract tests in tests/release/test_oci_release_contract.py
Task T041: Vulnerability policy tests in tests/release/test_vulnerability_policy.py
```

## Implementation Strategy

1. Complete setup/foundational contracts and demonstrate fail-closed release identity.
2. Deliver US1 as the smallest independently useful vertical slice: intentional artifacts plus public CLI.
3. Complete US2 and US3 exact-identity subjects in parallel where possible.
4. Integrate immutable subjects through US4 protected orchestration and dry-run rehearsal.
5. Add US5 recovery, documentation, audit, and full gates.

## Notes

- Actual registry, tag, docs, or GitHub Release publication is prohibited in this feature.
- Every completed task must be checked only after its focused evidence passes.
- Full-SHA Action pins must be resolved from authoritative upstream refs and captured in tests/docs.
- A dry-run proves orchestration and local identity, not a successful production release.
- Clean-container MCP validation remains separate and no host software may be added to the base image for catalog validation.

## Local Spec Kit Limitation

`.specify/scripts/bash/setup-tasks.sh --json` was attempted on 2026-07-12 and failed on checked-in CRLF line endings. The active task template was read directly and populated manually without modifying shared scripts.
