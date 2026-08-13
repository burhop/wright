# Spec Kit Analysis: 068 Capability Library

**Final analysis date**: 2026-08-13
**Artifacts analyzed**: `spec.md`, `plan.md`, `tasks.md`, contracts, data model,
quickstart, and project constitution
**Result**: No unresolved critical or high-severity findings

## Coverage summary

| Metric | Result |
|---|---:|
| Functional requirements | 35 |
| Success criteria | 10 |
| Requirements with task coverage | 45 / 45 (100%) |
| Dependency-ordered tasks | 119 |
| Requirements-quality checklist items | 56 / 56 checked |
| Constitution conflicts | 0 |

The requirements traceability table in `tasks.md` maps every FR and SC to
implementation, verification, hardening, or explicitly deferred evidence work.
Routes remain thin, domain behavior remains in `tool_registry`, core discovery
remains offline-capable, and the repository's component, mocked page, and local
system test tiers are present.

## Findings and remediation

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| A1 | High | The API supported many catalog filters, but the page exposed only search, domain, evidence, and compatibility. This did not satisfy FR-003. | Added lifecycle, current platform/architecture, maturity, risk, locality, host, validation, and installed filters, complete option sets, URL persistence, client/API mapping, and tests. |
| A2 | High | Validation and workspace enablement could proceed for a merely registered server without proof of installation or connection, contrary to FR-028. | Added an installed/connected precondition before validation, retained current digest-bound validation before workspace enablement, and added negative API coverage. |
| A3 | High | `CapabilityView` did not expose all FR-004 detail groups, notably field provenance, data touched, reviewed examples, supported-platform claims, and bounded validation history. | Extended catalog/view contracts, details UI, search text, Onshape evidence, append-only history projection, schemas, documentation, and tests. Empty catalog fields now state that evidence is unavailable rather than inventing a claim. |
| A4 | High | Acceptance covered all backend preflights but did not complete apply, validation, and single-workspace enablement for local-package, remote-endpoint, and host-bridge paths as SC-005 requires. | Added a deterministic three-backend browser acceptance journey and retained contract/rollback tests for each adapter. |
| A5 | High | Several new interactive controls lacked stable test IDs, and capability/report dialogs did not fully trap and restore focus, conflicting with FR-035 and the constitution. | Added stable IDs to every feature-owned interactive control, Escape handling, focus trap/restore, component tests, keyboard browser coverage, and serious/critical accessibility scanning. |
| A6 | Critical | The production service constructed no default onboarding adapters or validation client. The wizard could produce a plan but normal apply/validate would stop at an unconfigured test seam. | Added reversible registry-backed local-package, local-command, and remote-endpoint application through Wright's existing MCP registry. Normal validation now uses Wright's real MCP lifecycle, while injected deterministic clients remain available for tests. Host-specific adapters remain allowlisted and fail closed. Adapter-reported failure now triggers rollback. |
| A7 | Medium | The plan's source tree omitted implemented modules for installers, registry application, validation running, missing reports, and system smoke coverage. | Updated `plan.md` so the architecture description matches the delivered structure. |

## Residual evidence status

| ID | Severity | Status | Justification |
|---|---|---|---|
| R1 | Medium | Deferred external evidence | SC-009's five-person moderated usability study has not occurred. The spec explicitly requires the outcome to remain labeled unvalidated until that study; product documentation and the program progress record do so. This does not substitute automated accessibility and journey evidence. |
| R2 | Low | Deferred optional live evidence | Credentialed Onshape Labs protocol validation remains intentionally deferred. Wright has not subscribed, accepted external terms, supplied credentials, or contacted the endpoint. The vendor-backed record remains `official_preview` with an explicit unvalidated limitation, as FR-015 and the assumptions require. |

## Final conclusion

The specification, plan, tasks, contracts, implementation, and constitution are
consistent after remediation. The remaining items are named external validation
activities already anticipated by the specification, not missing product
implementation or untracked critical/high defects. Loop 068 may proceed to its
authoritative merge gate after the quickstart evidence and progress record are
updated against the exact final tree.
