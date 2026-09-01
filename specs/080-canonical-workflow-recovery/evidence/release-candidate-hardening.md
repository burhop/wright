# T059 local release-candidate hardening

**Date**: 2026-09-01

**Exact subject**: commit `fe6140d85f0598454394d7b7105d756c3794a7dd` / tree `8df2b19c94926c8fe922870de4bbad92bb285720`

**Task status**: **COMPLETE FOR THE AUTHORIZED LOCAL T059 SCOPE**. No push,
merge, tag, publication, registry promotion, documentation deployment, GitHub
Release, or customer action occurred. T060 and customer readiness remain open.

## Qualification result

| Boundary | Result |
|---|---|
| Release preflight | Passed from a clean detached worktree for `v0.1.9` and exact source commit `fe6140d8...`. |
| Packaging contracts | 275 passed, 12 host-conditioned skips; 8 pre-existing tracing deprecation warnings. |
| Docker/OCI contracts | 18 passed; Ruff clean. |
| Python candidates | One wheel and one sdist built; both passed isolated clean-install/import validation. |
| Determinism | Three rebuilds across the Docker-only repair retained identical wheel and sdist bytes. |
| Native lifecycle | Windows 11 amd64 / Python 3.13.14 / Hermes 0.19.0 / Codex 0.144.1 passed install, start, status, doctor, update, rollback, stop, uninstall, reinstall preservation, and exact purge. |
| Manager profile | Direct Codex STDIO profile loaded without a Hermes intermediary; MCP `2025-11-25`, 18 tools, and exact workspace binding passed. |
| Docker smoke | Exact local image passed non-root user, dependency reconciliation, offline Rivet assets, immutable manifest/entrypoint permissions, setup-pending and configured startup, ephemeral recovery, entrypoint bypass, API readiness, Hermes gateway readiness, and agent connection. |
| Release rehearsal | Dry-run manifest status `release_ready`; every stage records `external_mutation: false`. This is rehearsal state, not a production release or public verification. |

## Exact artifacts

| Artifact | SHA-256 |
|---|---|
| `wright_engineering-0.1.9-py3-none-any.whl` | `53a48234f18c4b1b2457a31dc8c5da95c67dfa29db1d8a5faca1ec890f36a77d` |
| `wright_engineering-0.1.9.tar.gz` | `988c95f8b3af5fa255cb0278c5ce40432f4efe5d5d4abaf3374a7b37aab7b9a3` |
| Local OCI manifest | `sha256:666ed2dee57fa1a4c65a2e3dedc290e70035078e29b948d52f2408b4cddab76a` |
| Native lifecycle evidence | `079947625b85c080f7ada14f34cce9b205432ef2aae5f8e6c74784723658bb64` |
| Dry-run release evidence | `0130502ac46ef689b6753b5a6f841beaee50691fdde56ec5888d15355d343bf6` |

The retained machine-readable files are under
`artifacts/t059-release-candidate/`. Candidate binaries remain local build
outputs and are represented by `SHA256SUMS` rather than committed binary blobs.

## Failure and repair history

1. The first package build used WSL's `/usr/bin/python3`, which lacked the
   `build` module. The corrected Git-for-Windows invocation used the locked
   candidate interpreter.
2. Hermes 0.19.0 could not install on Python 3.14 because its pinned
   `pywinpty`/PyO3 dependency supports through Python 3.13. The authoritative
   release workflow pins Python 3.13, where installation and lifecycle passed.
3. The first lifecycle home was mistakenly placed beneath the source checkout.
   Wright correctly rejected the managed workspace as a protected overlapping
   path. Repeating in the external host temp root, matching CI, passed.
4. The first Docker build exposed missing cross-package TypeScript fixtures in
   the web-builder stage. After adding the two build-only fixture copies, a
   second run proved the recovery spec fixture was still excluded by
   `.dockerignore`. The final repair re-includes only that file and its parent
   chain. The exact `fe6140d8` image then passed the full smoke.

Failed attempts were not reclassified as passes. They produced the two Docker
hardening commits `51934985` and `fe6140d8` and remain part of this audit trail.

The first refreshed dashboard verification at `2026-09-01T06:06:49.773Z`
also failed honestly: the new exact checkpoint identifier expanded the 390 px
document by 44 px. The dashboard was repaired with narrow-width containment
and break-anywhere handling for checkpoint identifiers. The rerun at
`2026-09-01T06:09:36.766Z` passes at 57/60 with 8/8 images loaded, zero desktop
or mobile document overflow, zero browser diagnostics, all evidence URLs at
HTTP 200, both traversal probes rejected with HTTP 403, exact approval subject
identity intact, and `customerReady: false`. Both the failed-first and final
screenshots/result history remain represented by the regenerated dashboard
verification artifacts.

## Explicit residual boundary

Linux and macOS native lifecycle matrices, vulnerability scan/SBOM/provenance,
public TestPyPI/PyPI and registry verification, GHCR/Docker Hub digest parity,
versioned docs, protected approvals, tag creation, and GitHub Release are
production integration work. They require separate T060 authorization and are
not inferred from this local Windows rehearsal. T056 human accessibility and
usability gates and T058 independent-oracle qualification also remain open.
