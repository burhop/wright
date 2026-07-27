# Research: Python and OCI Release Train

## Decision 1: Product and artifact topology

**Decision**: Keep root `pyproject.toml` as the only product version source; publish only `wright-engineering`; keep the full application OCI-only and every workspace package private.

**Rationale**: This matches the approved artifact ADR, avoids the unrelated `wright`/`wright-core` namespaces, and prevents the public helper from acquiring appliance or private-package dependencies.

**Alternatives considered**: Independent component versions and publications were rejected because names and APIs are not stable. Putting the appliance on PyPI was rejected because its UI, supervisor, Hermes, and OS runtime belong in OCI.

## Decision 2: Supported runtime matrix

**Decision**: Validate Python 3.11, 3.12, 3.13, and 3.14 for the public artifact; align frontend/release builds on Node 24 LTS; claim only linux/amd64 for OCI.

**Rationale**: The roadmap explicitly requires testing every admitted Python version or narrowing metadata. Node's official July 2026 schedule identifies 24 as LTS while 26 is Current, so production builds should not use the current `node:26-slim`. The current architecture-specific dependency path lacks native arm64 evidence.

**Alternatives considered**: Python 3.13-only contradicts current metadata. Node 26 Current is unsuitable for the production support line. Buildx emulation alone is not evidence for arm64 runtime support.

## Decision 3: Python exact-artifact flow

**Decision**: Build wheel and sdist once, compute SHA-256 and safe content manifests, build a comparison wheel from the sdist, then independently clean-install and smoke both artifacts for each supported Python version. TestPyPI and PyPI jobs download the same workflow artifact and verify the recorded hashes.

**Rationale**: Immutable artifact reuse closes PKG-01 and makes retries objectively comparable. Independent sdist installation detects missing build inputs and oversized/unrelated contents that wheel-only tests miss.

**Alternatives considered**: Rebuilding per index or per Python version was rejected because it produces different subjects. `--skip-clean-install` was rejected for release jobs. Installing from the source checkout was rejected because it can hide missing files.

## Decision 4: OCI build and promotion

**Decision**: Build and push/export one SHA candidate, capture the digest, and make smoke, vulnerability, inventory, SBOM, provenance, promotion, mirror, and verification consume that digest. Promote with registry-native manifest copy/tag operations, never a Docker rebuild.

**Rationale**: Digest identity is the only reliable proof that tested and released images are the same subject. GitHub's official attestation contract accepts `subject-name` plus `subject-digest` and supports associated SPDX/CycloneDX SBOM predicates.

**Alternatives considered**: The current separate CI and release builds were rejected. Loading and re-pushing a mutable local tag was rejected because platform manifests and provenance can change.

## Decision 5: Vulnerability policy

**Decision**: Block fixable High and Critical OS/library vulnerabilities. Permit only reviewed exception records with finding identity, owner, rationale, compensating control, and future expiry. Scheduled rescans evaluate the same policy.

**Rationale**: A warning-only scan does not protect publication, while a scoped expiring exception format handles upstream lag without silently normalizing permanent risk.

**Alternatives considered**: Blocking all unfixed findings was rejected as operationally brittle. Non-blocking output was rejected because it leaves the existing release blocker open.

## Decision 6: Attestations and evidence

**Decision**: Generate SHA-256 checksums and GitHub build provenance for Python files, plus SPDX SBOM and provenance bound to the OCI digest. Consolidate subjects, gates, approvals, promotions, and skips into one JSON release-evidence manifest and verify it after every transition.

**Rationale**: Attestations link subjects to source/build identity, while the manifest captures Wright-specific ordering, policy, and cross-registry identity. Verification—not generation alone—creates useful evidence.

**Alternatives considered**: A Markdown checklist alone was rejected as non-machine-verifiable. Signing mutable tags was rejected in favor of immutable hashes/digests.

## Decision 7: Protected promotion and least privilege

**Decision**: Separate build/test, TestPyPI, PyPI, OCI promotion, Docker Hub mirror, release verification, docs, and GitHub Release jobs. Use OIDC for package publication, minimal per-job permissions, and protected environments for `testpypi`, `pypi`, `release`, and `dockerhub`.

**Rationale**: Separate trust boundaries allow required review and keep registry/release credentials away from untrusted build code. Full commit SHA pins reduce action supply-chain drift.

**Alternatives considered**: A repository-wide `contents: write, packages: write` permission was rejected. Long-lived PyPI tokens were rejected in favor of Trusted Publishing.

## Decision 8: Rehearsal model

**Decision**: Provide a deterministic local `--dry-run` rehearsal that builds/inspects local subjects, simulates stage transitions, writes evidence and recovery decisions, and refuses every public mutation. Workflow-dispatch rehearsal uses non-publishing validation paths unless maintainers later explicitly authorize external TestPyPI activity.

**Rationale**: The operator explicitly excludes actual publication. A useful rehearsal must prove artifact identity and ordering while honestly distinguishing simulated registry behavior from a production release.

**Alternatives considered**: Calling workflow lint a release rehearsal was rejected as insufficient. Uploading to TestPyPI was rejected in this feature because it is still an external publication.

## Decision 9: Retry and rollback

**Decision**: Identical subjects are resumable; different subjects under one version fail. Python corrections use a new patch and optional yank under PyPI criteria. OCI immutable version/SHA references never move; mutable aliases may restore only a previous verified digest; divergent mirrors are quarantined; GitHub Release remains draft until verification.

**Rationale**: PyPI files and content-addressed OCI subjects cannot be safely overwritten. Evidence-driven roll-forward and alias restoration preserve auditability.

**Alternatives considered**: Deleting/replacing published files and force-moving immutable tags were rejected.

## Primary evidence reviewed

- Python Packaging User Guide: Trusted Publishing/tool recommendations and TestPyPI isolation/install guidance, reviewed 2026-07-12.
- GitHub Actions documentation: artifact attestations for files and OCI digests, SBOM predicate support, required permissions, and verification, reviewed 2026-07-12.
- Node.js official release schedule: Node 24 is LTS and Node 26 is Current on 2026-07-12.
- Wright `docs/gpt5-6plan.md`, current workflows, Dockerfile, package metadata, package tests, and release documentation.
