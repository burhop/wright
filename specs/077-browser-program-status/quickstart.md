# Quickstart: Browser Program Status Acceptance

This is the planned human-repeatable acceptance path. Commands become executable only after the exact EPP-F01B approval subject and lease are approved.

## Preconditions

- Checkout is clean and on the approved implementation branch.
- The implementation commit matches the active lease.
- No benchmark, product operation, push, publication, or release is implied.

## 1. Publish one committed status bundle

```powershell
uv run python scripts/publish-engineering-program-status.py --source HEAD --data-root .local-run/program-status-demo
```

Expected: validation passes, one `current.json` is atomically installed, and output reports commit, tree, program tree, snapshot digest, bundle ID, and path. Re-running unchanged `HEAD` produces identical canonical projection bytes and bundle ID.

## 2. Run focused verification

```powershell
uv run pytest packages/workspace_service/tests/test_program_status.py apps/api/tests/test_program_status_api.py tests/program_control_plane/test_program_status_publisher.py
npm --prefix apps/web run test -- --run ProgramStatus
uv run pytest tests/ui-integration -k program_status
```

Expected: valid, corrupt, stale, empty, identity-mismatch, unsafe-link, auth, refresh, accessibility, and deterministic-regeneration cases pass.

## 3. Open the page

Configure `WRIGHT_DATA_ROOT` to the demo root using Wright's normal local runtime command, then open `http://127.0.0.1:<wright-port>/program-status`.

Confirm:

1. Four independent readiness areas and non-compensating release state are clear.
2. Benchmark is honestly `0/100` with hold/blocker, dependencies, authority, and next action.
3. `100 proposed customer stories` is separate from qualified benchmark results.
4. Charts use exact times and commits and explain change, importance, limitation, and next action.
5. Task completion is explicitly feature-local and does not imply whole-product completion.
6. Integration/CI and continued-development lanes have distinct branches and actions.
7. Evidence details use safe relative links and expose freshness/recovery without sensitive content.

## 4. Demonstrate failure containment

Alter an isolated copy of the demo projection without changing its envelope digest. Do not edit committed evidence.

Expected: the fixture is rejected; the last valid page remains visible and is labeled failed/stale with recovery. Starting without a valid bundle shows unavailable values only.

## 5. Demonstrate committed refresh

Publish a second approved committed fixture with a different exact identity while the page remains open.

Expected: within 15 seconds every panel swaps together. Unchanged identity returns 304 and adds no history point.

## 6. Delivery gates

After implementation authority exists, run normal repository checks, packaged-runtime smoke without `.git` or network, and then the dev push/merge runbooks. Direct push to `dev` is never permitted.
