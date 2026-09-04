# Native Milestone Verification and Handoff

Owning checkout: `D:/repos/wright/.local-run/native-process-milestone/wright`; branch `codex/079-native-process-milestone`. Original root checkout/uncommitted files are preserved. Commit `6daeb214` preserves the original proposal.

## Current checkpoint

The existing independent implementation dashboard is at [http://127.0.0.1:8765/](http://127.0.0.1:8765/). It reads published task/evidence records without requiring Wright to run. The local Wright product preview is separately at `http://127.0.0.1:5188/native-processes` while the isolated preview service is running; it is not the implementation dashboard.

Authoring/save/reopen/CAS has passed an actual browser/SQLite journey. Native runtime corrections, exact MCP binding corrections and native exception-safe telemetry have passed independent review. Three local development processes compute actual outputs; a complete real local stdio tool process has written and read back its measured artifact with provenance. The combined HTTP/browser journey and packaging/restart checks are being completed. Dev integration and independent human usability remain pending. See [checkpoint observations](evidence/implementation-checkpoint-20260904.md) and [correction/tool proof](evidence/native-runtime-correction-and-tool-proof.md); those dated records retain prior failures.

## Reproduce the actual browser journey

Use a disposable registered workspace and the corresponding running API/web build. Set `WRIGHT_NATIVE_LIVE_SESSION` to that session, `PLAYWRIGHT_BASE_URL` to the web origin, and `PLAYWRIGHT_INCLUDE_LIVE=1`. Run `npx playwright test tests/ui-integration/native-process-live.spec.ts --project=chromium --workers=1`. This journey uses real requests, validates downloaded bytes/digests/provenance, retains failed run evidence, and checks linked correction and reload. It creates new process identities in the selected workspace.

The safe local tool fixture is opt-in: set `WRIGHT_NATIVE_MCP_PROTOCOL=1`, then run `python -m pytest packages/workspace_service/tests/test_native_process_mcp_protocol.py -q`. Optional `WRIGHT_NATIVE_MCP_EVIDENCE` writes evidence beneath the current test worktree. Both adapter and complete process paths launch the real stdio child and verify teardown. This fixture does not qualify any engineering catalog server or benchmark case.

## Acceptance journey

1. Inspect dashboard capabilities, current work, remaining criteria and quality gaps.
2. Create/configure/connect/save/reopen in an authorized workspace.
3. Execute each example, inspect actual artifact bytes/provenance and independent assertions.
4. Inject failure, inspect blocked dependencies, correct/rerun and retain linked immutable history.
5. Cancel/refresh and verify no late artifact publication; exercise restart interruption.
6. Run the same definition headlessly and compare semantic/artifact digests.
7. Preflight/invoke exact local MCP; reject changed/denied binding without invocation.
8. Keyboard/click-only/narrow/zoom checks and actual independent human protocol.
9. Offline/package/migration/recovery/legacy checks, independent candidate review and required gates.
10. PR merge to dev; verify exact built/deployed identity and browser journeys; publish final status.

## Evidence log

- 2026-09-04: live dev observed at `7404a549`; independent read-only architecture/dashboard investigations completed. Planning evidence only.
