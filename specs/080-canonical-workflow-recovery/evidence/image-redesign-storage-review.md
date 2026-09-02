# Image-led editor: storage and operator-helper review

Recorded 2026-09-02T22:40:34Z, Windows native development host.

## Later final checkpoint

After the review below, the complete source/layout/API/operator-helper suite
passed **123 tests with 5 genuine platform skips** (22.90s, 143 existing
deprecation warnings), using `--basetemp .test-tmp/image-redesign-storage-final-all`.
This includes 25 pure helper provenance/ownership tests. The skips and
power-loss/junction/native-POSIX limits below are unchanged.

The controlled live restart subsequently recorded exact commit `4cfab9ba8091b766805e00157739204675385c0c`
and tree `93bc29cabb266f454efa5f6157e31fd302789ce1` in
`.local-run/image-redesign-committed-api-4cfab9ba/verification.json`. Listener
49328 was replaced by verified listener36544 from the same checkout/venv,
with exact backend module origins/hashes and five existing workflow source
files unchanged. This later operation is separate from the earlier review,
which performed no process control. Operational stdout/stderr are not asserted
to be secret-free publication artifacts.

## Original bounded review

This is working-tree evidence against base commit `7e95b0c748975df247effb4bc70f1f67f92a8e81`, not final committed-subject acceptance. The reviewer implemented the storage seam earlier in this task: this is a fresh implementer review and follow-up, **not author-independent verification**. The separate prior `code_gap` review and its findings are not attributed to this reviewer.

## Scope and result

Reviewed changes in the workflow-source API route, schemas, error headers, workspace source/layout store, and `scripts/recovery/restart_authoring_api.py`. Re-read the existing pinned-directory operations, exact session scope resolver, and relevant storage/API tests. No server restart, process signal, live workflow mutation, frozen-evidence edit, push, or release was performed during this review.

Two concerns were reported to the parent before editing and then repaired with explicit authorization:

- **POSIX directory-listing race:** the file picker pinned a directory descriptor but enumerated its pathname. A rename/swap-back could escape the before/after pathname identity checks and disclose outside filenames, though this endpoint never reads contents. Listing now uses the pinned descriptor when available; Windows retains its existing directory handle that denies rename. The cross-platform argument-selection regression failed before the fix and passed afterward. A real POSIX rename/swap-back regression was added but was not executed on this Windows host.
- **Restart ownership matching:** the optional operator helper previously accepted the expected executable as a substring anywhere in the command line. It now accepts only the exact same-checkout uvicorn launcher or its same-checkout Python wrapper, followed by the exact app, loopback host and port arguments. Extra/reordered arguments, reload flags, wrong cwd, invalid ports and lookalike executable arguments fail before any signal. Fifteen pure validation tests exercise these branches without running the helper's process-control path.

No additional unresolved code finding was identified in this bounded pass. The platform and evidence limits below still apply.

## Boundary review

- The file-choice API snapshots one persisted session-to-workspace binding, checks the registered path, and has no desktop/global-root fallback. It returns relative path/name pairs, not file contents or executable capabilities. Hidden paths, dependency folders, symlinks/reparse points, unsafe names and excessive enumeration are excluded or rejected. The client rechecks the returned workspace identity and reference shape. Any future content read or execution must reauthorize the exact current workspace and path.
- Source paths remain confined to `workflows/<safe-slug>.workflow.wflow`; reserved names, links and unsupported paths are rejected. Existing source content remains syntax-neutral. The storage layer does not claim to validate semantic workflow membership from an opaque source string.
- Layout has a closed, size-bounded schema; finite numeric bounds, safe IDs, supported version and independent layout CAS are checked. API validation rejects malformed layout before the source write. Layout positions and viewport do not enter the visible source file.
- Immutable layout generations and a digest-bound head pointer are written under the existing source lock. Source revision/digest CAS remains required. Host-managed semantic/layout revisions are rebased on save; no-op and layout-only saves retain source identity. A stale but well-formed generation is not applied to a different source digest or semantic revision. The source A → B → A regression preserves readability and marks the old layout stale.
- Synchronous publication failure tests cover rollback of source and prior layout, including a failure after a layout pointer switch. Orphan layout generations remain preserved evidence; retries do not overwrite the old generation. These tests do **not** prove multi-file power-loss atomicity. Interrupted or corrupted source/head state remains fail-closed under the existing recovery contract.
- Storage/API errors retain bounded, typed, no-store envelopes; successful input-file and workflow-source responses are no-store. Corrupt layout generation content fails closed without rewriting the visible source.
- The restart helper is a Windows/check-out-specific operator tool, not an unattended general process manager. It also verifies the specified process owns the listening port, constrains a newly created evidence directory beneath the checkout's `.local-run`, checks exact workspace/source identity, keeps the old process environment in memory, launches a hidden loopback process, and compares workflow source contents plus revision/digest identities afterward. Verification JSON excludes source contents and environment values. Redirected API stdout/stderr remain operational logs, not certified secret-free artifacts. A failed launch leaves an operator-visible failure/logs; no automatic second restart or rollback is claimed.
- Read-only OS inspection during this review found the API listener at port 8018 using the same-checkout Python/uvicorn command supported by the tightened validator (PID 49328 at inspection time). It was not signaled. This does not claim the running process has loaded this review's source changes.

## Commands and observed results

All commands used cwd `D:/repos/wright/.local-run/epp-f02b-writer/wright`.

Initial unchanged focused suite:

```powershell
.venv/Scripts/python.exe -m pytest packages/workspace_service/tests/test_workflow_sources.py packages/workspace_service/tests/test_workflow_source_layouts.py apps/api/tests/test_workflow_sources_api.py -q -rs --basetemp .test-tmp/redesign-storage-review-final-20260902
```

Observed: **97 passed, 4 skipped, 143 warnings in 14.07s**. The initial sandbox launcher attempt was denied before executing tests; the same isolated command then ran with approved host-runtime access.

Red descriptor regression before the implementation fix:

```powershell
.venv/Scripts/python.exe -m pytest packages/workspace_service/tests/test_workflow_source_layouts.py -q -rs --basetemp .test-tmp/redesign-storage-descriptor-red-20260902
```

Observed: **1 failed, 20 passed, 3 skipped**. `test_input_choices_scan_the_pinned_descriptor_when_available` received the pathname instead of descriptor `123`, demonstrating the old selection path. This test supplies a mock pinned capability and real temporary-directory entries; it is not represented as a native POSIX race execution.

Final focused suite after the authorized fixes:

```powershell
.venv/Scripts/python.exe -m pytest packages/workspace_service/tests/test_workflow_sources.py packages/workspace_service/tests/test_workflow_source_layouts.py apps/api/tests/test_workflow_sources_api.py tests/test_restart_authoring_api.py -q -rs --basetemp .test-tmp/redesign-storage-review-hardened-20260902
```

Observed: **113 passed, 5 skipped, 143 warnings in 13.84s**. No helper test invokes `main`, terminates a process, or starts a service. The warnings are 142 existing `asyncio.iscoroutinefunction` deprecations and one Starlette/httpx test-client deprecation.

The five skips are explicitly not passes:

1. Source-file symlink containment: Windows `WinError 1314`, required privilege unavailable.
2. Dangling lock-file symlink rejection: the same privilege limitation.
3. Input-choice external file symlink: the same privilege limitation.
4. Input-choice external directory symlink: the same privilege limitation.
5. Real directory rename/swap-back listing test: POSIX-only descriptor behavior; skipped on Windows. The descriptor-argument selection test passed here. No real Windows junction or native POSIX race execution is claimed.

```powershell
.venv/Scripts/ruff.exe check apps/api/src/api/main.py apps/api/src/api/routers/workspace.py apps/api/src/api/schemas/workspace.py apps/api/tests/test_workflow_sources_api.py packages/workspace_service/src/workspace_service/workflow_sources.py packages/workspace_service/tests/test_workflow_source_layouts.py scripts/recovery/restart_authoring_api.py tests/test_restart_authoring_api.py
git diff --check -- apps/api/src/api/main.py apps/api/src/api/routers/workspace.py apps/api/src/api/schemas/workspace.py apps/api/tests/test_workflow_sources_api.py packages/workspace_service/src/workspace_service/workflow_sources.py packages/workspace_service/tests/test_workflow_source_layouts.py scripts/recovery/restart_authoring_api.py tests/test_restart_authoring_api.py
```

Observed: Ruff **all checks passed**; scoped diff check exited 0 (line-ending notices only). This does not substitute for a final clean-subject build or full product acceptance.

## Tested file identities

SHA-256 of the on-disk implementation/test bytes after the final focused run:

| Relative path | SHA-256 |
| --- | --- |
| `apps/api/src/api/main.py` | `c1d9090862531bfd6b9408acde8a3ca5e71820bb67317fc1f892bc19ef793f9d` |
| `apps/api/src/api/routers/workspace.py` | `0838b6c215a0a29340a6d01fa7d638ccba63da0bb36e3e4b0f1fbf30cf8c6941` |
| `apps/api/src/api/schemas/workspace.py` | `e175d299808704fadaae715a76b6ebaa00edc90bd263a4602d3ee0173b9b6eab` |
| `apps/api/tests/test_workflow_sources_api.py` | `ff81ce59d5141ebd1dd86d1d08cdfc5dca95253b34fc0a1c1d58ca404943a67a` |
| `packages/workspace_service/src/workspace_service/workflow_sources.py` | `92c79666bfd703fd3aa03a0aca3aa27201089a7938fc74f7370afa4a3a9b2055` |
| `packages/workspace_service/tests/test_workflow_sources.py` | `bf6da268063c3b192c599dbaf48e0be3922fcd4469854369f1a50b92c4c51c80` |
| `packages/workspace_service/tests/test_workflow_source_layouts.py` | `9e450e8678fd19fb676fd7f5b6ac994d42dec751654ada85b506c910987f319a` |
| `scripts/recovery/restart_authoring_api.py` | `d7ae91890c7cc0e9b44edda38feea32419292d19d7af6b2a11f428ca00a8a865` |
| `tests/test_restart_authoring_api.py` | `a522be54ec309a08aa9bb498d4e1f63bc580a7157245ed8c04218ba31937df73` |
