# Implementation Plan: Python and OCI Release Train

**Branch**: `codex/047-python-oci-release-train` | **Date**: 2026-07-12 | **Spec**: [spec.md](spec.md)

## Summary

Replace Wright's independent Python and container publication paths with one dry-run-safe, exact-artifact release train. The root `pyproject.toml` remains the validated product-version source. Build the sole public distribution (`wright-engineering`) once, enforce intentional archive contents, install wheel and sdist independently on Python 3.11-3.14, and pass the identical hashes through TestPyPI and protected PyPI stages. Build one linux/amd64 OCI candidate from digest/checksum-pinned inputs, scan and smoke that digest, generate SBOM/provenance subjects, then promote and optionally mirror the same manifest without rebuilding. Record all subjects and gates in a machine-readable release manifest, publish GitHub Release last, and provide executable dry-run recovery drills. No public publication occurs in this feature.

## Technical Context

**Language/Version**: Python 3.11-3.14 for the public CLI/release tools; Bash and PowerShell entrypoints; GitHub Actions YAML; Dockerfile syntax; Node.js 24 LTS for web builds

**Primary Dependencies**: Hatchling/build, packaging, twine, check-wheel-contents, pip/venv, Docker Buildx/BuildKit, Trivy, Syft/SPDX, GitHub artifact attestations, OCI registry tooling, existing pytest/ruff/mypy/npm/mkdocs gates

**Storage**: Immutable workflow artifacts plus JSON release-evidence manifests, checksums, content manifests, SBOMs, scan reports, provenance subject metadata, and local rehearsal outputs under ignored `dist/`/`test-results/`

**Testing**: pytest policy/unit/contract tests; clean wheel and sdist builds/installs; Python 3.11-3.14 CI matrix; shell/PowerShell release-tool tests; action-pin/permission/dependency-order validation; Docker build/smoke/inspect when available; full `scripts/check-dev-merge.sh`

**Target Platform**: GitHub-hosted Ubuntu release runners; Windows/Linux local rehearsal tools; linux/amd64 OCI appliance; GHCR canonical registry with optional byte-identical Docker Hub mirror

**Performance Goals**: One Python build and one OCI build per release identity; preflight and manifest verification under 10 seconds excluding builds/scans; deterministic repeat rehearsals; bounded 15-minute image smoke and scan stages

**Constraints**: No registry, tag, release, or docs mutation during local verification; only `wright-engineering` public; never publish `wright-core`; exact files/digest promoted; full-SHA Actions; least privilege; protected environments; no unreviewed High/Critical fixable findings; GitHub Release last; no arm64 claim; clean-container MCP process remains separate

**Scale/Scope**: One public wheel/sdist pair, one amd64 OCI manifest, four protected environment contracts, canonical plus optional mirror registry, Python 3.11-3.14, all scoped release/supply-chain workflows and recovery scenarios R3.1-R3.7

## Constitution Check

- **Modular boundaries**: Pass. Release domain parsing/evidence lives in standalone `scripts/release` modules; the public CLI remains dependency-free and does not import private packages.
- **Offline-first**: Pass. Preflight, artifact inspection, evidence validation, and recovery drills run locally; online publication stages are explicit protected adapters.
- **Container policy**: Pass with operator/roadmap precedence over stale thick-base wording. The appliance stays OCI-only, uses a minimal pinned runtime, and gains no engineering host applications.
- **Agent abstraction**: Pass. The CLI bridge targets the provider-neutral Feature 046 service and adds no provider coupling.
- **SQLite/local files**: Pass. Release evidence is immutable files; no server database is introduced.
- **Security/identity**: Pass. Trusted Publishing uses OIDC; no registry tokens are stored; environment gates and least privilege are explicit.
- **Engineering protocol**: Pass. Direct MCP bridge behavior delegates to Feature 046 and clean-container catalog validation stays separate.
- **Testing**: Pass. Exact Python artifacts, OCI digest identity, workflows, recovery, docs, and full dev gate are executable requirements.
- **Observability**: Pass. Release decisions are structured in evidence manifests; runtime telemetry work remains Feature 051.
- **Branch/manual gate**: Pass. Work is isolated on Feature 047, actual publication is frozen, and `scripts/check-dev-merge.sh` remains the merge authority.

## Project Structure

```text
src/wright_engineering/
├── __init__.py                 # product version API
├── cli.py                      # version/doctor/appliance/config/mcp commands
├── diagnostics.py              # public dependency-free checks
├── appliance.py                # authenticated appliance status client
└── mcp_bridge.py               # direct STDIO-to-appliance bridge

scripts/release/
├── __init__.py
├── version.py                  # SemVer/PEP 440/tag/metadata validation
├── python_artifacts.py         # archive policies, hashes, clean-install plan
├── evidence.py                 # release manifest model/validation
├── vulnerability_policy.py    # blocking findings and expiring exceptions
├── oci.py                      # digest/promotion/mirror identity helpers
└── recovery.py                 # retry/quarantine/restore dry-run decisions

scripts/
├── build-python-distributions.sh
├── release-preflight.py
├── release-rehearsal.py
└── verify-release-evidence.py

.github/workflows/
├── ci.yml
├── docker-build.yml            # non-release candidate validation delegate
├── publish-python-packages.yml # reusable exact-files publication stages
├── release.yml                 # unified build-once promotion orchestrator
├── dependency-review.yml
└── codeql.yml

docker/
├── Dockerfile                  # digest/checksum-pinned amd64 production build
├── dependency-inventory.md
└── release-policy.json

docs/release/
├── artifact-topology.md
├── python-packaging.md
├── container-publishing.md
├── release-runbook.md
└── release-recovery.md

tests/release/
├── test_version_contract.py
├── test_python_artifacts.py
├── test_public_cli.py
├── test_workflow_policy.py
├── test_oci_release_contract.py
├── test_vulnerability_policy.py
├── test_release_evidence.py
└── test_recovery_drills.py
```

**Structure Decision**: Keep public runtime code under the existing root distribution, isolate release-policy logic in importable repository scripts, keep side-effecting orchestration in thin CLI/workflow adapters, and validate workflows through semantic YAML/evidence tests rather than brittle substring-only assertions.

## Implementation Sequence

1. Characterize current Python contents, version consumers, publication paths, Docker inputs, workflow pins/permissions, and release docs; add failing policy tests for every R3 invariant.
2. Establish one version parser/validator and release-evidence schema; make preflight reject dirty/mismatched/conflicting identities.
3. Constrain Hatch wheel/sdist contents, mark internal packages private, add archive safety/secret/content checks, and independently build/install/test wheel and sdist across the admitted Python matrix.
4. Complete the lightweight public CLI surfaces without private imports and add collision/uninstall/source-leak diagnostics.
5. Convert Python publishing to reusable build-once artifacts, TestPyPI verification, protected PyPI promotion, OIDC-only permissions, identical-hash retries, and full SHA pins.
6. Pin Docker bases/tools/checksums and Node 24 LTS, remove mutable upgrades, generate inventory, and keep amd64 honest.
7. Build the OCI candidate once by digest; scan/smoke/inventory/attest that subject; promote tags and optional mirror from the digest without a build.
8. Unify release ordering and evidence, disable independent tag rebuilds, implement dry-run rehearsal and post-publication verification contracts, and make GitHub Release terminal.
9. Add CI supply-chain workflows and ratcheted gates without conflating scheduled/live/clean-container validation.
10. Add retry/yank/quarantine/alias restore/mirror divergence runbooks and executable recovery drills, update the status ledger, complete the audit, and run the full dev merge gate.

## Migration and Rollback

- **Upgrade**: Existing public `wright-engineering` 0.1.0 remains immutable. A later corrected patch uses explicit contents and the unified train. No published artifact is mutated by this feature.
- **Workflow migration**: Existing tag triggers stop building/publishing independently. Compatibility entry workflows may call the unified reusable workflow but cannot bypass its preflight or evidence inputs.
- **Existing consumers**: The `wright` console alias remains for alpha compatibility with collision diagnostics; canonical documentation also names the `wright-engineering` distribution.
- **Container compatibility**: Immutable prior image references remain valid. The production Dockerfile is hardened in place; rollback selects a known prior image digest rather than restoring mutable build inputs.
- **Failure**: Invalid version, content, hash, digest, vulnerability policy, attestation subject, environment order, or mirror identity fails closed before later promotion.
- **Retry**: The evidence manifest recognizes identical subjects and resumes missing stages; a differing subject for the same release identity is a conflict requiring a new patch version.
- **Rollback**: Python correction is a new patch and optional yank under documented criteria. OCI version/SHA tags never move; bad digests are quarantined and mutable aliases return only to a previously verified digest.
- **External configuration**: Protected environments, reviewers, and Trusted Publishers are documented prerequisites and verified where APIs permit; local code does not create or weaken them.

## Phase 0: Research

See [research.md](research.md).

## Phase 1: Design and Contracts

See [data-model.md](data-model.md), [contracts/release-evidence.schema.json](contracts/release-evidence.schema.json), [contracts/release-train-contract.md](contracts/release-train-contract.md), [contracts/vulnerability-policy.schema.json](contracts/vulnerability-policy.schema.json), and [quickstart.md](quickstart.md).

## Constitution Check — Post-Design

All gates remain passing under the stated precedence. The design preserves the OCI appliance and lightweight public client split, prevents private package publication, uses files and explicit adapters for release evidence, retains offline rehearsal, and treats every public mutation as a protected external operation. The stale constitution's thick-base and premature manual-phase wording are not reintroduced; the approved roadmap and current AGENTS merge gate remain authoritative.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Unified workflow plus reusable Python publisher | Separate protected environments need different permissions while sharing immutable artifacts | One privileged monolithic job cannot enforce least privilege or TestPyPI-before-PyPI approvals |
| Compatibility console alias retained | Existing alpha users may already invoke `wright` | Removing it immediately would create an unrelated breaking migration; collision diagnostics make the temporary risk explicit |

## Local Spec Kit Limitation

`.specify/scripts/bash/setup-plan.sh --json` was attempted on 2026-07-12 and failed because the checked-in script has CRLF line endings (`$'\r': command not found`). The template and required artifacts were therefore resolved and populated manually without rewriting the shared Spec Kit scripts.
