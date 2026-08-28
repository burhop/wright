# Spec Kit Analysis: Browser Program Status

**Analyzed**: 2026-08-28

**Artifacts**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `checklists/`, `tasks.md`, constitution v3.0.0

## Result

**LOCAL PASS under the user-authorized final enumerated repair exception — exact-commit GB10 and independent re-verification pending.**

- Functional requirements: 39
- Requirements mapped to implementation/test tasks: 39/39
- Dependency-ordered tasks: 48, sequential and unique
- Requirements-quality checks: 36/36 passed
- Unresolved clarification markers: 0
- Constitution violations: 0
- Hidden or unresolved P0 questions: 0

## Coverage map

| Requirement group | Requirements | Primary task coverage | Result |
| --- | --- | --- | --- |
| Authority, identity, atomicity | FR-001–FR-003, FR-020–FR-024 | T005–T012, T035–T044 | Covered |
| Four readiness areas and release rule | FR-004–FR-008 | T013–T020 | Covered |
| Product, benchmark, commercial, program health | FR-009–FR-012, FR-034 | T013–T020, T021–T025 | Covered |
| Work, blockers, evidence, corrections | FR-013–FR-018 | Exact EPP-F01 dashboard, typed governance supplement, and T026–T034 | Covered |
| Sensitive-data and offline boundaries | FR-025–FR-026 | T005, T012–T013, T041 | Covered |
| Accessibility and dedicated page | FR-027–FR-030 | T014–T020, T027, T042–T043 | Covered |
| Exact-time histories and honest task scope | FR-031–FR-035, FR-039 | T021–T025, T040 | Covered |
| Proposed catalog vs qualified benchmark | FR-036 | T015, T030–T034 | Covered |
| Integration and development lanes | FR-037–FR-038 | T030–T034 | Covered |

## Findings resolved during initial analysis

1. **Identity-change blind spot**: the initial data model described `bundle_id` as a projection-only digest, which could miss a changed committed source with identical values. It now binds canonical `source + projection`, excluding only non-semantic publisher observation time.
2. **Allowlist/schema mismatch**: the initial nested contract admitted open-ended objects despite the sensitive-field allowlist. A separate closed, digest-bound source catalog now names exact paths or filename grammars, schema IDs, parser contracts, selection rules, projection targets, and precedence; canonical paths and parsed URLs fail closed.
3. **Non-executable packaging task**: the fallback packaging task lacked exact paths. T040 now names the packaged resource, wheel-content/native-lifecycle tests, and documentation target.

## Final enumerated repair disposition

Both independent audits rejected repair-attempt-2 commit `e76e9b4296751faa8721f3b572cf53e3764aacc2`. The user then authorized one final exception covering exactly four consolidated areas and no implementation or scope expansion. This repaired planning tree now specifies:

1. **Action precedence and benchmark context**: the embedded dashboard action is immutable historical snapshot context; `work.current_next_action`, reconciled with validated current program state and lifecycle policy, is the sole current program action. Metric, lane, and benchmark actions carry non-governing purposes. A required typed benchmark context supplies phase, hold state/reason, dependency states, authority, and next qualifying action; unexplained or contradictory `0/100` fails publication.
2. **Raw identity and source boundaries**: the repository publisher attests exact Git-blob bytes and binds one evidence detail; source-free runtime never claims to recompute bytes it does not possess. Runtime/browser independently recompute canonical dashboard and bundle identities. A new closed source catalog and schema bind exact paths/filename grammars, schema IDs, parser contracts, selection rules, projection targets, precedence, and the one identity-only legacy V8 record.
3. **Correction/finding/verification relationships**: exact claim, finding, correction, and verification ID sets replace trusted aggregate counts; resolved findings require reciprocal correction links and a passing independent verification with explicit verdict/blocking outcome.
4. **Strict URL/path validation**: canonical relative paths reject empty, dot, parent, duplicate, and backslash segments. Optional GitHub URLs require both strict schema grammar and parsed HTTPS origin/path validation with no credentials, port, query, or fragment.

The same two reviewers must review one exact repaired commit. GB10 must independently run the Linux contract/consistency checks. Any new material finding stops the run; there is no further repair authority.

## Consistency conclusions

- The five stories remain independently demonstrable after the shared identity/read foundation.
- Proposed customer stories cannot enter the governed qualification numerator.
- Feature-local task completion cannot be presented as whole-program completion.
- Historical points require exact commits and trustworthy timestamps; omitted data remains disclosed.
- Runtime has no source-checkout, Git, network, benchmark, product-execution, or mutation dependency.
- Implementation, dependency, benchmark, push/PR/merge, publication, and release authority remain absent.
- The Spec Kit Bash prerequisite helper could not start on this Windows host (`E_ACCESSDENIED`); the checked-in `.specify/feature.json` selected `specs/077-browser-program-status`, and the required spec, plan, tasks, research, data model, contracts, quickstart, and constitution were verified directly.
- Both schemas are Draft 2020-12 meta-valid; the 17-source catalog and a full cross-schema bundle fixture validate; canonical-path and malformed-query/fragment URL negatives pass; task/requirement/check counts remain 48/39/36; and the full local program-control suite passes 262 with one declared platform skip.

## Remaining review gate

Commit this exact planning tree, run GB10 Linux verification and the same engineering-usability and architecture/test reviews on that one subject, then—only if all three are green—preserve their audit evidence, advance append-only planning state, and freeze the exact commit/tree/program-tree/digest/lease subject. Stop at human approval before T001. Any new material finding stops immediately.
