# Feature 048 Completion Audit

**Scope date**: 2026-07-24
**Branch**: `048-solid-edge-creation-visibility`
**Merge scope**: production-test stabilization

## Delivered behavior

| Area | Evidence |
| --- | --- |
| Creation-only projection | `GatewayPolicy` hides Solid Edge inspection and inventory tools and denies guessed direct calls; policy and service tests cover discovery and execution. |
| Creation guidance | `.hermes.md` requires one new-document recipe call, an explicit workspace path, a visible/open result, and no inspection fallback. |
| User-visible progress | Chat streams emit an immediate planning event, friendly Solid Edge labels, elapsed time, and periodic heartbeats; API tests cover delayed and completed-tool behavior. |
| Stream continuity | The existing indexed chat job retains progress and terminal events for reconnect and supports steering prompts into an active turn. |
| Runtime ownership | `WRIGHT_API_MCP_AUTOSTART=0` prevents API startup, chat preparation, workspace reconciliation, and passive status polling from starting a competing MCP subprocess. |
| Workspace rebinding | Hermes configuration changes are detected, synchronized, and followed by one bounded gateway restart before chat continues. |
| Protected bridge calls | Hermes bridge requests propagate `WRIGHT_API_TOKEN` without logging it. |
| CI portability | The Playwright backend selects compatibility authentication explicitly, and API tests place fallback secrets in a private temporary directory on Linux. |

## Requirement disposition

| Requirement group | Disposition |
| --- | --- |
| FR-001, FR-005, FR-007, FR-008 | Implemented for gateway projection and agent guidance. Provider-side mutation safety remains the SolidEdgeMCP provider's responsibility. |
| FR-009 through FR-012 | Implemented by the current chat stream and UI integration. The buffer remains process-local and bounded by the current job lifecycle. |
| FR-016 through FR-019 | Implemented for Hermes-owned local sessions and protected bridge requests. |
| FR-002 through FR-004, FR-006 | Enforced by canonical guidance and the SolidEdgeMCP recipe/export contracts; a new Wright-side immutable artifact-binding model is deferred. |
| FR-013 through FR-015, FR-020 | Deferred with the proposed diagnostics aggregation service. Existing gateway audit and subprocess logging remain in place. |
| SC-001, SC-003 through SC-006 | Not claimed. These require the deferred 20-trial live evidence and diagnostic attribution work. |
| SC-002, SC-007, SC-008 | Deterministic contract coverage is included; workstation-wide percentage claims are not made. |

## Deferred follow-up

- immutable `solid_edge_creation_v1` session/profile and created-artifact binding;
- provider-neutral progress service and durable/bounded replay abstraction;
- paired operation diagnostics, aggregation, and phase attribution;
- reviewed inventory/schema benchmark and executable live smoke harness;
- at least 20 redacted Windows trials for percentage-based success criteria.

The detailed draft backlog remains in `tasks.md` under its deferred section so
no proposed work is silently presented as completed.

## Validation ledger

| Gate | Result |
| --- | --- |
| Focused Wright regressions | Passed: 80 tests, one existing deprecation warning |
| Full `scripts/check-dev-merge.sh` | Passed end to end on 2026-07-24 |
| Full Python suite | Passed: 516 passed, 12 skipped |
| Hermes plugin | Passed: 82 tests |
| Frontend | Passed: 24 files/103 unit tests, lint, TypeScript, Prettier, and production build |
| Release/package checks | Passed: 36 tests, 87.53% focused coverage, exact wheel/sdist build and clean installs |
| Documentation | Strict MkDocs build passed |
| Live browser gate | Passed: 38 Playwright tests |
| GitHub PR #44 checks | Pending the final pushed commit |
| SolidEdgeMCP STL provider tests | Passed: 1272 tests/34 skipped plus the live STL regression in 5 seconds |

## Catalog and live-host boundary

This feature does not change engineering MCP catalog validation status and does
not treat a Windows Solid Edge run as clean-container catalog evidence.
