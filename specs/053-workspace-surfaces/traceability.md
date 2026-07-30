# Workspace Surfaces Traceability

**Purpose**: Map every approved requirement and success criterion to planned
automated/manual evidence before implementation. `Planned` is not a claim that
the feature passes; each row must be changed to `Pass`, `Fail`, or `Blocked`
with an evidence link during final audit.

## Functional Requirements

| ID | Planned automated evidence | Documentation / fixture evidence | Status |
|---|---|---|---|
| FR-001 | T011, T016, T026, T029 | Architecture and surface contract | Planned |
| FR-002 | T011, T013, T014, T056, T081, T148 | Threat model identity/scoping | Planned |
| FR-003 | T011, T013, T016, T062, T071 | Lifecycle state/action matrix | Planned |
| FR-004 | T055-T061, T178 | Opening-surfaces and BREP guides | Planned |
| FR-005 | T055, T060, T070 | Sharing disclosure and shareable fixture | Planned |
| FR-006 | T055, T060 | Presentation-choice guide | Planned |
| FR-007 | T039, T042, T048, T049, T052, T055, T059, T070 | UX command/consequence and output-retention matrix | Planned |
| FR-008 | T012, T016, T055, T062 | Migration and preference fallback guide | Planned |
| FR-009 | T017, T192 | Viewer compatibility/migration evidence | Planned |
| FR-010 | T019, T035, T042, T043 | Beginner graph and Python API docs | Planned |
| FR-011 | T035, T042 | One-import/no-server beginner fixture | Planned |
| FR-012 | T036-T041 | Display gallery and MIME contract | Planned |
| FR-013 | T037-T041 | Display envelope and Python API docs | Planned |
| FR-014 | T036-T041, T152 | Safe/active HTML and renderer docs | Planned |
| FR-015 | T037-T039, T052 | Revision behavior and vault model | Planned |
| FR-016 | T036-T042 | Novice error/troubleshooting guide | Planned |
| FR-017 | T043, T053 | Installed offline examples | Planned |
| FR-018 | T114, T128, T135 | Manifest and framework guides | Planned |
| FR-019 | T114, T117, T118, T129 | No-shell/workspace launch contract | Planned |
| FR-020 | T115, T117-T119, T130, T138 | Endpoint ownership policy | Planned |
| FR-021 | T120-T122, T125 | HTTP/WS/SSE fixtures and protocol contract | Planned |
| FR-022 | T115, T116, T124 | Readiness/health operations guide | Planned |
| FR-023 | T114-T116, T135 | Lifetime defaults and activity rules | Planned |
| FR-024 | T115, T117-T119, T196 | Process cleanup/operations guide | Planned |
| FR-025 | T083, T114-T122 | Policy defaults and limit diagnostics | Planned |
| FR-026 | T115, T123, T195 | Colliding two-instance fixtures | Planned |
| FR-027 | T126, T127, T177, T200, T201 | Native/Docker/remote framework guide | Planned |
| FR-028 | T145, T146, T150, T154 | MCP Apps guide and official fixture | Planned |
| FR-029 | T146-T148, T154 | Server-scoped resource fixture | Planned |
| FR-030 | T149, T151-T154 | App Bridge/sandbox guide | Planned |
| FR-031 | T149, T151, T156 | Same-server authorization guide | Planned |
| FR-032 | T155-T158 | WebMCP matrix/scoped SDK guide | Planned |
| FR-033 | T155-T158 | Scoped message/teardown contract | Planned |
| FR-034 | T145, T151-T158 | Stable errors and fallback fixtures | Planned |
| FR-035 | T058, T076, T079, T080, T152 | Threat model/source profiles | Planned |
| FR-036 | T076, T079, T080, T152 | Preview-origin deployment guide | Planned |
| FR-037 | T061, T078-T080, T152 | Browser policy/security guide | Planned |
| FR-038 | T013, T014, T074, T081, T175 | RBAC/consent matrix | Planned |
| FR-039 | T038, T076, T078, T082 | Bootstrap/token/redaction guide | Planned |
| FR-040 | T077, T078, T088, T197 | Target policy/SSRF fixture | Planned |
| FR-041 | T081, T197 | File escape hostile fixture | Planned |
| FR-042 | T056-T061, T097 | External URL/host-adapter guide | Planned |
| FR-043 | T037, T075, T079, T083, T156 | Default limits and hostile fixture | Planned |
| FR-044 | T015, T082, T137, T174 | Security/diagnostics guide | Planned |
| FR-045 | T012, T013, T074, T076, T095, T119 | Revocation/reconciliation guide | Planned |
| FR-046 | T099, T102, T104, T107-T110 | Focus/layout guide | Planned |
| FR-047 | T099-T113 | Keyboard/accessibility contract | Planned |
| FR-048 | T059, T071, T094, T143, T174-T180 | Status/action/diagnostics guide | Planned |
| FR-049 | T015, T039, T081, T174-T180 | Authorized artifact verification docs | Planned |
| FR-050 | T015, T023, T027, T174, T179 | Trace/SQLite/vault evidence | Planned |
| FR-051 | T043, T127, T166, T202, T203 | Offline installation/examples | Planned |
| FR-052 | T117, T118, T126, T200 | Native platform matrix | Planned |
| FR-053 | T005, T011, T014, T019, T176, T177, T190 | Versioned contracts/migration docs | Planned |
| FR-054 | T059, T068, T094, T100, T105, T106, T175, T180 | Test-ID inventory in UI docs | Planned |
| FR-055 | T006, T072, T098, T127, T173, T177, T178, T188, T189 | Reference/hostile fixture catalog | Planned |
| FR-056 | T176, T181-T189 | Versioned user/developer/security/ops docs | Planned |

## Success Criteria

| ID | Planned evidence and timing boundary | Status |
|---|---|---|
| SC-001 | T205: five representative novice sessions; at least four complete create+revise under ten minutes without undocumented help | Planned |
| SC-002 | T035, T042, T053: installed one-import, <=10 executable lines, no server/port, durable after exit | Planned |
| SC-003 | T193-T194 using `policy-defaults.md` reference profile and timing marks; >=95/100 within each target | Planned |
| SC-004 | T060, T125, T198: 100 declared presentation switches with exact sharing/isolation result | Planned |
| SC-005 | T102, T103, T198, T204: chat continuity, keyboard/manual matrix, zero critical/serious axe findings | Planned |
| SC-006 | T123, T125, T195: 100 simultaneous mixed HTTP/WS/SSE interactions with zero cross-instance routing errors | Planned |
| SC-007 | T117-T119, T125, T196: 100 cycles per process adapter and zero descendant/port/credential/grant/stream leaks after bound | Planned |
| SC-008 | T080, T098, T197: hostile matrix in every supported deployment with zero successful listed boundary crossings | Planned |
| SC-009 | T147, T149, T152, T154, T158, T197: MCP metadata/interaction coverage and stable denial for every undeclared operation | Planned |
| SC-010 | T126, T198-T201: Windows/macOS/Linux, Docker, browser and desktop matrix with documented deterministic limitations only | Planned |
| SC-011 | T017, T192: unchanged viewer/editor suites and provider/API/layout compatibility record | Planned |
| SC-012 | T176, T190, T206: unfamiliar developer completes launch/failure/denial diagnosis under 30 minutes | Planned |
| SC-013 | T010, T191, T208-T214: every row finalized against tests, docs, artifacts and environment-dependent evidence | Planned |

## User-Story Journey Evidence

| Story | Independent journey | Primary task/evidence |
|---|---|---|
| US1 | Create, revise, and retain a novice graph | T042, T043, T193, T205 |
| US2 | Panel/browser same-instance choice and recovery | T060-T062, T198 |
| US3 | Hostile surface denied at every boundary | T080-T083, T197, T207 |
| US4 | Focus mode, chat update, resize, narrow layout, keyboard | T102-T103, T198, T204 |
| US5 | Start, transport, recover, restart, stop, clean tree | T120-T127, T194-T196, T200-T201 |
| US6 | MCP App and WebMCP authorized/denied/fallback/teardown | T154-T158, T197-T198 |
| US7 | Installed integration quickstart and diagnostics | T176-T178, T190, T206 |

## Completion Rule

No row becomes `Pass` from code inspection alone. A passing row names the exact
test command/result, documentation/example, packaged artifact digest where
applicable, and evidence file. Environment-dependent rows name OS/browser/build,
procedure, result, limitation, and reviewer. A failed or missing row keeps the
feature from the corresponding rollout stage; it is never converted to `Pass`
by weakening the requirement after execution without a reviewed spec change.
