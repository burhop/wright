# Completion Audit: Python and OCI Release Train

**Status**: Complete for review — every local gate passed; the explicitly documented Linux-engine limitation remains an external CI validation prerequisite and is not represented as a runtime pass.
**Audit date**: 2026-07-12

## Requirement evidence

| Requirements | Evidence | State |
| --- | --- | --- |
| FR-001–FR-002 | `scripts/release/version.py`, `release-preflight.py`, mismatch/dirty/conflict contracts | Proven focused |
| FR-003–FR-004 | Private classifiers on every internal project; sole-public-package tests; publication workflow scan | Proven focused |
| FR-005–FR-008 | Explicit Hatch contents; archive path/link/content policy; deterministic manifests/hashes; independent wheel/sdist installs on Python 3.11–3.14 | Proven focused |
| FR-009–FR-010 | Dependency-free version/doctor/appliance/config/MCP bridge; clean artifact commands from `C:\tmp`; private-import tests | Proven focused |
| FR-011–FR-015 | Reusable exact-files workflow, TestPyPI verification before protected PyPI, OIDC-only jobs, full SHA pins | Proven statically/actionlint; external environments pending administrator configuration |
| FR-016–FR-020 | Digest-pinned bases/uv, version+checksum micromamba, locked/exact runtime versions, amd64 candidate workflow, blocking vulnerability policy, SBOM/provenance digest subject | Proven policy/workflow; exact image runtime blocked by unavailable local Linux engine |
| FR-021–FR-024 | Registry-native digest promotion, stable-only latest, optional mirror copy and digest verification, GHCR canonical, explicit amd64-only contract | Proven workflow/actionlint |
| FR-025–FR-028 | Required dependency graph, final evidence, docs before GitHub Release last, failure gating, deterministic no-mutation rehearsal | Proven focused/actionlint |
| FR-029–FR-030 | Python/OS artifact matrix, Node 24, plugin lint/package tests, blocking focused mypy/coverage, dependency review, CodeQL, audits/license policy, clean-container separation | Proven configuration plus focused local runs |
| FR-031–FR-032 | Retry/yank/quarantine/alias/mirror/draft recovery implementation, tests, and runbooks | Proven focused |
| FR-033–FR-034 | Semantic workflow tests prove no publication rebuild/bypass; old independent tag build paths replaced | Proven focused/search/actionlint |
| FR-035 | Artifact topology, packaging, container, operation, recovery, version, contributor, and security docs | Proven focused; strict docs gate pending |

## Success criteria

| Criterion | Evidence | State |
| --- | --- | --- |
| SC-001 | Canonical version parser and adversarial mismatch tests | Proven |
| SC-002 | Safe manifests; 3.11/3.12/3.13/3.14 wheel and sdist clean installs | Proven |
| SC-003 | One workflow artifact, SHA256SUMS verification at every Python publication stage | Proven statically |
| SC-004 | One release build action and digest reused by smoke/scan/attest/promotion/mirror | Proven statically; runtime CI evidence pending |
| SC-005 | Blocking evaluator and complete/expiry tests | Proven |
| SC-006 | Full-SHA repository scan and checksum-verified actionlint | Proven |
| SC-007 | Two deterministic rehearsals, identical `ec25cf…5f5d`, zero mutations | Proven |
| SC-008 | Workflow dependency/order tests and actionlint | Proven |
| SC-009 | Recovery decision tests and runbooks | Proven |
| SC-010 | `scripts/check-dev-merge.sh` terminal log | Proven: 496 Python passed, 82 Hermes passed, 99 frontend passed, strict docs passed, 38 Playwright passed; `Dev merge gate passed.` |

## Explicit non-claims

- No TestPyPI, PyPI, GHCR, Docker Hub, documentation, tag, or GitHub Release publication occurred.
- Protected GitHub environment and Trusted Publisher configuration cannot be proven from the local checkout.
- No OCI runtime pass is claimed while Docker Desktop's Linux engine is unavailable.
- No arm64 support is claimed.
