# Feature Specification: Python and OCI Release Train

**Feature Branch**: `codex/047-python-oci-release-train`

**Created**: 2026-07-12

**Status**: Complete

**Input**: Implement the approved roadmap's complete R3 release train: one validated product version, intentional public Python packaging, a useful lightweight CLI, build-once exact-artifact Python and OCI validation, protected least-privilege promotion, supply-chain evidence, byte-identical registry mirroring, and recovery runbooks. Actual publication is out of scope.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Produce Intentional Python Artifacts (Priority: P1)

A release engineer builds `wright-engineering` once and receives a small, intentional wheel and source archive that contain only the public CLI, documentation, metadata, and required resources. Internal monorepo packages are never publishable artifacts.

**Why this priority**: The existing oversized source archive and ambiguous internal package names create the most immediate Python distribution risk.

**Independent Test**: Build the wheel and source archive from a clean checkout, compare their contents against an explicit policy, install each artifact independently on every supported Python version, and run the public commands without access to the source tree.

**Acceptance Scenarios**:

1. **Given** a reviewed product version, **When** the public distribution is built, **Then** exactly one wheel and one source archive are produced with approved names, metadata, files, and hashes.
2. **Given** either built artifact, **When** it is installed in a clean supported environment, **Then** version, doctor, appliance status, configuration diagnostics, and direct MCP bridge commands work without private package imports.
3. **Given** an internal Wright package or the unrelated `wright-core` name, **When** publication eligibility is evaluated, **Then** it is rejected before any upload stage.

---

### User Story 2 - Validate One Release Identity (Priority: P1)

A maintainer starts a rehearsal from a reviewed commit and receives one release identity that consistently binds the source commit, product version, Python hashes, OCI digest, platform policy, and generated evidence.

**Why this priority**: Promotion cannot be trustworthy when tags, package metadata, image labels, or rebuilt artifacts can disagree.

**Independent Test**: Run release preflight against valid and deliberately mismatched tags, versions, changelog entries, labels, manifests, and source commits; only the fully consistent candidate proceeds.

**Acceptance Scenarios**:

1. **Given** a protected SemVer tag matching the product metadata, **When** preflight runs, **Then** it records one normalized product version and reviewed source commit for all downstream jobs.
2. **Given** any tag, Python version, OCI label, compatibility declaration, changelog, or candidate manifest mismatch, **When** preflight runs, **Then** the release fails before artifact publication.
3. **Given** a retry for the same product version, **When** recorded hashes or digests differ, **Then** the retry fails rather than replacing or silently rebuilding artifacts.

---

### User Story 3 - Test and Attest One OCI Candidate (Priority: P1)

A release engineer builds the Wright appliance once for the supported architecture, pushes or exports it as a candidate, and tests, scans, inventories, attests, and later promotes that exact digest without rebuilding it.

**Why this priority**: The current CI and release workflows build different images, so a passing scan does not prove the published image was tested.

**Independent Test**: Build an amd64 candidate once, capture its digest, perform blocking smoke and vulnerability checks by digest, generate SBOM/provenance evidence, and prove every promotion reference resolves to the same manifest digest.

**Acceptance Scenarios**:

1. **Given** a reviewed release commit, **When** the OCI candidate job runs, **Then** it builds once with pinned inputs and records an immutable candidate digest.
2. **Given** the candidate digest, **When** smoke, inventory, vulnerability, SBOM, and provenance gates run, **Then** every gate targets that digest and a defined blocking policy rejects non-exempt fixable High or Critical findings.
3. **Given** a passing candidate, **When** version and mutable aliases are promoted or mirrored, **Then** no build occurs and every destination resolves to the tested source manifest.
4. **Given** no native arm64 evidence, **When** the release manifest is produced, **Then** only linux/amd64 is claimed and arm64 publication remains disabled.

---

### User Story 4 - Rehearse Protected Promotion (Priority: P1)

A release owner can rehearse the complete publication order without uploading public artifacts: exact Python files go through TestPyPI verification before protected PyPI promotion, the tested OCI digest is promoted and optionally mirrored, post-publish verification runs, documentation follows, and the GitHub Release remains last.

**Why this priority**: Ordering, protected approvals, and least privilege are required to prevent partial or unreviewed releases.

**Independent Test**: Execute an offline/local rehearsal and workflow contract suite that records planned environment gates, permissions, artifacts, promotion commands, and terminal publication order while proving all real upload steps remain disabled.

**Acceptance Scenarios**:

1. **Given** validated Python artifacts, **When** the TestPyPI stage completes, **Then** the exact downloaded hashes are installed and verified before the protected PyPI stage becomes eligible.
2. **Given** validated Python and OCI candidates, **When** promotion is approved, **Then** each job receives only its required permissions and protected environment.
3. **Given** optional Docker Hub credentials are unavailable, **When** promotion is rehearsed, **Then** canonical GHCR verification remains required and the mirror is reported as skipped rather than weakening the release.
4. **Given** any failed verification, **When** release orchestration evaluates completion, **Then** documentation and the GitHub Release are not published.

---

### User Story 5 - Recover Safely from Release Failure (Priority: P2)

A maintainer can diagnose and safely retry, yank, quarantine, restore aliases, or roll forward from a failed or vulnerable release using recorded hashes, digests, decisions, and commands.

**Why this priority**: Immutable package files and image tags require deliberate recovery instead of replacement or ad hoc rebuilds.

**Independent Test**: Run tabletop and executable dry-run scenarios for interrupted upload, conflicting retry, bad Python artifact, vulnerable OCI digest, mirror divergence, mutable-alias rollback, and draft GitHub Release recovery.

**Acceptance Scenarios**:

1. **Given** an interrupted retry with identical artifacts, **When** recovery runs, **Then** completed stages are recognized and missing stages can resume without rebuilding.
2. **Given** a bad Python release, **When** the runbook is followed, **Then** maintainers choose a corrected patch and documented yank criteria without attempting file replacement.
3. **Given** a bad OCI digest, **When** quarantine runs, **Then** immutable version and SHA references remain auditable, mutable aliases can be restored to the last verified digest, and a patch is required.
4. **Given** mirror divergence, **When** verification detects it, **Then** the GitHub Release remains draft and the divergent mirror is quarantined.

### Edge Cases

- Tag formats that are valid SemVer but not valid normalized Python versions, including prerelease spelling and leading `v`.
- A dirty checkout, unreviewed commit, missing changelog entry, or version already associated with different hashes.
- Wheel and source archive file lists that contain symlinks, absolute paths, traversal entries, secrets, specs, screenshots, sandbox scripts, caches, or unrelated packages.
- A source archive that builds a wheel differing in package contents or metadata from the primary wheel.
- Supported Python versions unavailable on one runner, dependency resolution drift, command collisions, uninstall/reinstall, and source-tree import leakage.
- OCI base/tool references that use moving tags, unverified downloads, architecture-specific URLs, mutable package resolution, or nondeterministic timestamps.
- Scanner outage, expiring exception, unfixed finding, malformed SBOM, missing provenance subject, digest mismatch, and smoke-test timeout.
- Candidate upload succeeds but later gates fail; one registry succeeds while another fails; mutable aliases partially move.
- Workflow rerun after artifacts expire, a protected environment rejects approval, or an upload reports an already-existing file.
- Docker Hub credentials are absent, mirror credentials exist but repository identity differs, or copied manifests resolve to different digests.
- Documentation or GitHub Release attempts to publish before post-publication verification.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Wright MUST use the root product metadata as the single version source and validate the release tag, Python version, OCI labels/tags, changelog, compatibility declarations, and release manifest against it.
- **FR-002**: Release preflight MUST bind every candidate to one reviewed source commit and reject dirty, mismatched, unsupported, or previously conflicting release identities.
- **FR-003**: `wright-engineering` MUST remain the only public Wright Python distribution in this release train.
- **FR-004**: Internal monorepo distributions MUST be explicitly marked private/non-publishable and MUST NOT appear in any public artifact dependency graph or publication matrix; `wright-core` MUST never be published.
- **FR-005**: The public Python wheel and source archive MUST use explicit include/exclude policies and MUST contain no secrets, unrelated packages, specs, screenshots, sandbox assets, caches, local outputs, or private implementation packages.
- **FR-006**: Python artifact validation MUST produce deterministic content manifests and hashes, reject unsafe archive paths/symlinks, run strict metadata/README checks, and compare source-built and primary wheel contents.
- **FR-007**: The release train MUST build one wheel and one source archive once, store them as immutable candidate artifacts, and reuse the same byte hashes for TestPyPI and PyPI stages.
- **FR-008**: Each admitted Python version MUST clean-install and test the wheel and the source archive independently with no source-tree access; the declared range MUST be capped if an admitted version cannot pass.
- **FR-009**: The public package MUST provide a lightweight, dependency-safe CLI for version, doctor, appliance status, configuration diagnostics/dry-run, and a direct MCP STDIO bridge; it MUST NOT embed the full appliance.
- **FR-010**: Public commands MUST work after install, uninstall/reinstall, and under command-collision diagnostics without importing workspace-private packages.
- **FR-011**: TestPyPI publication and install verification MUST precede protected PyPI promotion in the same release run; PyPI MUST consume the exact previously tested files.
- **FR-012**: Python retries MUST be idempotent for identical hashes and fail closed for any differing file associated with the same product version.
- **FR-013**: Every third-party GitHub Action used by release, publishing, container, or supply-chain workflows MUST be pinned to a full commit SHA.
- **FR-014**: Release jobs MUST declare least-privilege permissions and use protected `testpypi`, `pypi`, `release`, and `dockerhub` environments appropriate to their side effects.
- **FR-015**: PyPI publication MUST use OIDC Trusted Publishing and MUST NOT require stored API tokens.
- **FR-016**: The production OCI build MUST use digest-pinned base images, version/checksum-pinned downloaded tools, locked dependencies, aligned supported Node/Python versions, no unbounded upgrade step, and an intentional minimal runtime inventory.
- **FR-017**: The OCI train MUST build and push or export each supported-platform candidate exactly once, capture the canonical digest, and forbid a later release rebuild.
- **FR-018**: OCI smoke, content/license inventory, vulnerability scan, SBOM generation, and provenance/attestation MUST identify and validate the exact candidate digest.
- **FR-019**: The vulnerability policy MUST block fixable High and Critical findings unless a reviewed exception names the finding, owner, rationale, expiry, and compensating control; expired or malformed exceptions MUST fail closed.
- **FR-020**: OCI provenance MUST bind the digest to source commit, workflow identity, build parameters, and materials; the SBOM and attestations MUST be included in the release evidence manifest.
- **FR-021**: Version, SHA, prerelease, and stable aliases MUST be promoted from the already-tested digest without rebuilding; `latest` MUST move only after stable verification.
- **FR-022**: Docker Hub mirroring, when configured, MUST copy the verified canonical manifest rather than rebuild it and MUST prove the destination digest/manifest is byte-identical before completion.
- **FR-023**: GHCR MUST remain the canonical registry; an absent optional mirror MUST be reported honestly and MUST NOT prevent canonical candidate validation.
- **FR-024**: Initial release support MUST remain linux/amd64 only; arm64 MUST stay disabled until architecture-aware dependencies and a native exact-image smoke test provide evidence.
- **FR-025**: The release workflow MUST publish in this order: preflight and CI, Python/OCI candidate builds, exact-artifact gates, TestPyPI, protected approval, PyPI and OCI promotion, post-publish verification, versioned docs, then GitHub Release last.
- **FR-026**: Any failure before final verification MUST leave the GitHub Release absent or draft and MUST prevent unsupported registry/docs claims.
- **FR-027**: A machine-readable release evidence manifest MUST record version, commit, Python filenames/hashes/content manifests, OCI digest/platform/labels, scan policy result, SBOM/provenance subjects, promotion destinations, approvals, verification results, and skipped optional stages.
- **FR-028**: Release rehearsals MUST exercise orchestration and evidence generation without publishing to PyPI, TestPyPI, GHCR, Docker Hub, GitHub Releases, or versioned documentation.
- **FR-029**: CI MUST cover the declared Python/OS and Node support policy, Python packaging, plugin lint/package checks, staged blocking type/coverage gates, dependency review, code scanning, Python/npm audits, license policy, workflow-policy validation, and docs examples.
- **FR-030**: Expensive, live, and clean-container engineering MCP validation MUST remain explicitly separated and MUST NOT be made to pass by adding engineering host applications to the production base image.
- **FR-031**: Runbooks MUST define retry, partial failure, TestPyPI/PyPI correction and yank criteria, OCI quarantine, mutable-alias restore, mirror divergence, evidence retention, and GitHub Release recovery.
- **FR-032**: Recovery MUST never overwrite immutable Python files or immutable OCI version/SHA references; corrections require a new patch version and mutable aliases may only return to a previously verified digest.
- **FR-033**: Workflow and policy tests MUST prove that publication paths cannot bypass exact-artifact gates, protected approvals, scan policy, post-publish verification, or GitHub-Release-last ordering.
- **FR-034**: Existing independent tag-triggered publication/rebuild paths MUST be disabled or converted to delegates of the unified release train.
- **FR-035**: Documentation MUST state artifact topology, supported versions/platforms, verification commands, environment prerequisites, dry-run limitations, rollback semantics, and that a rehearsal is not a successful production release.

### Key Entities

- **Release Identity**: Normalized product version and reviewed source commit shared by every artifact, label, tag, compatibility declaration, and evidence record.
- **Python Candidate Set**: Immutable wheel and source archive with filenames, hashes, safe content manifests, metadata results, and clean-install evidence.
- **OCI Candidate**: Immutable platform manifest digest with labels, build inputs, smoke result, inventory, vulnerability decision, SBOM, and provenance.
- **Release Evidence Manifest**: Machine-readable record connecting release identity, exact artifact subjects, gates, approvals, promotions, skips, and verification outcomes.
- **Vulnerability Exception**: Reviewed time-bounded waiver with finding identity, owner, rationale, compensating control, and expiry.
- **Promotion Record**: Source subject and destination references proving no rebuild and, for mirrors, manifest identity.
- **Recovery Decision**: Auditable retry, yank, quarantine, restore, or roll-forward action tied to immutable evidence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: One hundred percent of release version consumers agree with the root product version, and every injected mismatch fails before candidate publication.
- **SC-002**: Wheel and source archive content policies report zero unapproved files, unsafe paths, secrets, or workspace-private imports; both artifacts install and pass command smokes on every declared Python version.
- **SC-003**: TestPyPI and protected PyPI stages reference exactly the same Python filenames and SHA-256 hashes produced by the single build job.
- **SC-004**: Every OCI scan, smoke, SBOM, provenance, promotion, and verification record references the same tested candidate digest, with zero release-stage image rebuilds.
- **SC-005**: One hundred percent of fixable High and Critical OCI findings are either blocked or covered by complete, unexpired reviewed exceptions.
- **SC-006**: One hundred percent of third-party Actions in scoped workflows use full commit SHA pins, and each job's permissions contain no scope beyond its documented side effect.
- **SC-007**: The dry-run release rehearsal completes with a self-consistent evidence manifest and performs zero public registry, release, tag, or documentation mutations.
- **SC-008**: Workflow contract tests prove GitHub Release publication is unreachable until all exact-artifact, promotion, mirror-if-configured, and post-publication verification gates pass.
- **SC-009**: Retry, conflicting-hash, partial-promotion, yank, quarantine, alias-restore, and mirror-divergence drills each produce the documented safe terminal state without rebuilding or overwriting immutable artifacts.
- **SC-010**: The full repository dev merge gate passes with no release-specific skip, timeout, warning-only security gate, or undocumented host limitation.

## Assumptions

- Actual PyPI, TestPyPI, GHCR, Docker Hub, Git tag, documentation deployment, and GitHub Release publication remain explicitly out of scope; only safe dry-run/rehearsal and workflow preparation are authorized.
- The root `pyproject.toml` remains the product version source, with SemVer tags converted to an equivalent valid PEP 440 form for prereleases.
- The intended supported Python range begins at 3.11 and may extend through 3.14 only where clean installs pass; the declared range and classifiers must match executable evidence.
- GHCR remains canonical and Docker Hub remains an optional byte-identical mirror.
- linux/amd64 is the only release architecture for this feature; adding arm64 requires later native evidence rather than emulation-only confidence.
- Protected environment reviewers and registry Trusted Publisher settings are repository/account configuration prerequisites that code can validate and document but cannot create locally.
- Existing Feature 046 MCP service behavior is the direct bridge target; the polished Codex plugin remains Feature 048 scope and Hermes thinning remains Feature 049 scope.
- Clean-container MCP catalog validation stays operator-invoked and separate from ordinary release tests.
