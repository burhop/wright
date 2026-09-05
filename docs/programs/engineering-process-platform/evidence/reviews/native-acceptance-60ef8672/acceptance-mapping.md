# Exact native acceptance mapping after the local full gate

Candidate `60ef8672f1f61c2f4942e618638ec8901e9aa9a0`, tree `7b5747eb5cf79f8193c8561eea70dc813c4eaa50`. The coordinator observed full gate session 74393 exit 0 at `2026-09-05T02:32:37Z`; its retained log ends `Dev merge gate passed.` The read-only mapping independently verifies that terminal text and the embedded Playwright report. It does not grant completed push/merge/CI acceptance, final independent approval, human participation, dev integration or deployment.

## Proposed current evidence counts

| Check | Required cases | Passing evidence |
| --- | ---: | --- |
| Q-SEMANTICS | 65 | 41 language/quantity tests and 24 resource/path-conformance cases. |
| Q-RUNTIME | 204 | 14 runtime JSON/tracing, 21 native persistence/artifact/run, 32 API/startup, 50 workspace runtime/MCP unit/restart, 77 frontend and 10 browser cases. |
| Q-COMBINED | 269 | The 204 runtime cases plus the 65 semantics cases. |
| Q-DASHBOARD | 124 | 68 publisher/reader, 5 API, 47 frontend and 4 browser cases. |

For each row, the proposed quality counts are `total = passed = required cases`, `failed = skipped = not_run = 0`. These are explicit required test-case populations, not rewritten whole-suite totals. The mapping retains exact unique IDs, source-file hashes and execution evidence for every case. Check populations intentionally overlap and must not be summed as independent test executions. No test was rerun to produce this mapping: pytest collect-only, Vitest list and Playwright list supplied identities; execution results came from the retained full-gate log/HTML and the separate real browser evidence.

Python full-gate file progress matches every selected per-file count and contains no selected skip except the two explicitly separate MCP cases. The compact program-control stage has one host-symlink skip in `test_git_subject.py`, outside the selected publisher files; the selected files have no executable skip and the stage completed 361 passed/1 skipped. All 547 frontend tests passed, so the exact selected frontend IDs have terminal passing coverage. HTML detail confirms all eight native simulated and four program-status browser cases had expected outcomes, with no unexpected or flaky result.

The selected native frontend files cover all 51 model/command vectors, 10 editor cases, 6 run-panel cases and 10 service/client cases. This is a fixed file-based selection, not a successful-only filter. The dashboard selection covers projection arithmetic, strict readers, missing evidence/attestation rejection, refresh/history/work/evidence presentation, source publication and operator/accessibility journeys.

## Live cases and retained skips

The full browser gate reports 170 passed and 5 skipped. Its two native live tests require an explicitly prepared `WRIGHT_NATIVE_LIVE_SESSION`, which was absent in that gate. The exact same test IDs ran on the restarted c7 real API and passed 2/2 in 25.5 seconds, with real output/failed/corrected run JSON and no mocked requests. Both cases appear once in Q-RUNTIME and Q-COMBINED; their actual execution commit remains c7. Every declared quality scope is byte-identical between c7 and 60, and the mapping retains both the gate skip and the separate actual pass source. The other three browser skips are the installed Hermes walkthrough, installed Rivet file walkthrough and MCP appliance opt-in. They remain unclaimed host/appliance coverage.

The default workspace suite skipped these two required real MCP cases:

- `packages/workspace_service/tests/test_native_process_mcp_protocol.py::test_native_adapter_real_stdio_protocol[adapter]`
- `packages/workspace_service/tests/test_native_process_mcp_protocol.py::test_native_adapter_real_stdio_protocol[native-process-artifact]`

They are satisfied only through the separate, still-current `Q-MCP-20260904-2` evidence (2 actual passes at `0f40f414e6daf5d4a2c2b63e891a73ce5e6c03de`, declared scope `fbc299767c2da64cb4f180f9a1a62d716836dcdd534909c0dc8200f23cb012ee`). They are not relabeled as executions in the default gate and are excluded from the four new denominators. Q-MCP remains a separate required task check; these new rows cannot replace it if its evidence becomes missing or stale.

The raw full-gate counts remain: program control 361 passed/1 skipped; release 102 passed; native/release/distribution slice 153 passed/10 skipped; coverage slice 235 passed/10 skipped with 85.28% coverage; security slice 51 passed/2 skipped; program-hardening slice 80 passed/2 skipped; API 447 passed/1 skipped; adapters 111 passed; core 143 passed; data 126 passed/1 skipped; model 185 passed/1 performance case deselected; tool registry 411 passed; workspace 485 passed/9 skipped; broad root 461 passed/39 skipped; Hermes 13 passed; frontend 547 passed; Playwright 170 passed/5 skipped. Overlapping gate slices are not added together. The raw skip annex retains all five browser identities/reasons and the Python per-file skip counts visible in the verbose stages. Compact native-runtime skips stay in the raw stage counts; this mapping supplies no missing packaging/other-OS claim for them.

## Evidence identity and remaining obligations

The standalone implementation dashboard's versioned server, index and publisher have no diff between reviewed checkpoint 88d36f37 and 60. Retain that prior real-browser checkpoint and the subsequently closed frontend schema review alongside these current 124 automated dashboard cases. The new browser mapping itself exercises the React operator page; it does not claim a fresh real browser visit to port 8765.

The copied independent planning report explicitly passes current Q-PLANNING/T001/T002 at scope `0f32facf01d293314af410c5ba849ee7ba1a5b100a03898d6f179239d08b42d4`. It may be appended as a distinct agent technical-review record with a verifier independent of the implementation team. It does not pass Q-REVIEW or complete T027. Current task checkboxes still yield 26 implemented, and all five promoted checks plus the retained current checks can support 26 verified, provided the actual projection remains current. Changing task checkboxes later changes the Q-PLANNING specs scope and requires an explicit bounded freshness reassessment.

Append evidence records rather than editing earlier failed/inconclusive attempts. Bind the four new quality rows to actual candidate 60 and this durable mapping; the summary should identify the combined local-gate/separate-live evidence and preserve its limits. Keep Q-GATES inconclusive while required push/merge work and terminal CI remain outstanding. Do not mark T027–T032 complete or grant integration credit from this report. All new raw JSON is retained byte-for-byte with `.json.txt` names so it is unambiguously an archived artifact, not an unschematized authoritative program JSON object. The retained-file mapping records original names and hashes.

## File-level acceptance populations

### Q-SEMANTICS

| Source test file | Cases |
| --- | ---: |
| `packages/core/tests/test_native_process.py` | 41 |
| `packages/core/tests/test_native_process_resources.py` | 24 |

### Q-RUNTIME

| Source test file | Cases |
| --- | ---: |
| `apps/api/tests/test_database_startup.py` | 2 |
| `apps/api/tests/test_native_process_api.py` | 10 |
| `apps/api/tests/test_native_process_execution_api.py` | 13 |
| `apps/api/tests/test_native_process_route_ids.py` | 7 |
| `apps/web/src/components/native-process/NativeEditor.test.tsx` | 10 |
| `apps/web/src/components/native-process/NativeRunPanel.test.tsx` | 6 |
| `apps/web/src/components/native-process/model.test.ts` | 51 |
| `apps/web/src/services/native-process.test.ts` | 10 |
| `packages/core/tests/test_native_runtime_json.py` | 9 |
| `packages/core/tests/test_native_tracing.py` | 5 |
| `packages/data_vault/tests/test_native_process_artifacts.py` | 4 |
| `packages/data_vault/tests/test_native_process_repository.py` | 8 |
| `packages/data_vault/tests/test_native_process_runs.py` | 9 |
| `packages/workspace_service/tests/test_native_process_mcp.py` | 34 |
| `packages/workspace_service/tests/test_native_process_restart.py` | 1 |
| `packages/workspace_service/tests/test_native_process_runtime.py` | 15 |
| `tests/ui-integration/native-process-live.spec.ts` | 2 |
| `tests/ui-integration/native-process.spec.ts` | 8 |

### Q-COMBINED

| Source test file | Cases |
| --- | ---: |
| `apps/api/tests/test_database_startup.py` | 2 |
| `apps/api/tests/test_native_process_api.py` | 10 |
| `apps/api/tests/test_native_process_execution_api.py` | 13 |
| `apps/api/tests/test_native_process_route_ids.py` | 7 |
| `apps/web/src/components/native-process/NativeEditor.test.tsx` | 10 |
| `apps/web/src/components/native-process/NativeRunPanel.test.tsx` | 6 |
| `apps/web/src/components/native-process/model.test.ts` | 51 |
| `apps/web/src/services/native-process.test.ts` | 10 |
| `packages/core/tests/test_native_process.py` | 41 |
| `packages/core/tests/test_native_process_resources.py` | 24 |
| `packages/core/tests/test_native_runtime_json.py` | 9 |
| `packages/core/tests/test_native_tracing.py` | 5 |
| `packages/data_vault/tests/test_native_process_artifacts.py` | 4 |
| `packages/data_vault/tests/test_native_process_repository.py` | 8 |
| `packages/data_vault/tests/test_native_process_runs.py` | 9 |
| `packages/workspace_service/tests/test_native_process_mcp.py` | 34 |
| `packages/workspace_service/tests/test_native_process_restart.py` | 1 |
| `packages/workspace_service/tests/test_native_process_runtime.py` | 15 |
| `tests/ui-integration/native-process-live.spec.ts` | 2 |
| `tests/ui-integration/native-process.spec.ts` | 8 |

### Q-DASHBOARD

| Source test file | Cases |
| --- | ---: |
| `apps/api/tests/test_program_status_api.py` | 5 |
| `apps/web/src/__tests__/NativeMilestone.test.tsx` | 5 |
| `apps/web/src/__tests__/PackagedProgramStatus.test.ts` | 1 |
| `apps/web/src/__tests__/ProgramStatusEvidence.test.tsx` | 2 |
| `apps/web/src/__tests__/ProgramStatusHistory.test.tsx` | 2 |
| `apps/web/src/__tests__/ProgramStatusPage.test.tsx` | 5 |
| `apps/web/src/__tests__/ProgramStatusPageRefresh.test.tsx` | 6 |
| `apps/web/src/__tests__/ProgramStatusRefresh.test.ts` | 14 |
| `apps/web/src/__tests__/ProgramStatusWork.test.tsx` | 4 |
| `apps/web/src/__tests__/milestone-status.test.ts` | 8 |
| `packages/tool_registry/tests/test_milestone_status.py` | 16 |
| `packages/tool_registry/tests/test_program_status.py` | 18 |
| `tests/program_control_plane/test_native_milestone_publisher.py` | 3 |
| `tests/program_control_plane/test_program_status_publisher.py` | 31 |
| `tests/ui-integration/program-status.spec.ts` | 4 |

## Raw evidence hashes

Full gate log SHA-256: `3b4758ad651920c3f372d4abfc9898d1608bf8d376500dec850a0c6646ea3040` (514407 bytes).

Playwright HTML report SHA-256: `d8cfc9e37b46b659541703264fccd9075df4471985b1420dd1ddc96bb1d63110`.

Complete test IDs, source-file digests, individual execution attribution and raw skip observations are retained in `required-acceptance-60ef8672.json.txt`. Listing artifacts are collection-only and must not be treated as separate test runs.
