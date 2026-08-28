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

Expected: the exact source catalog validates and its digest is reported; repository validation passes; one `current.json` is atomically installed; and output reports commit, tree, program tree, publisher-attested raw Git-blob digest/evidence, independently recomputed canonical dashboard digest, bundle ID, and path. Re-running unchanged `HEAD` produces identical canonical `source + dashboard + supplement` identity bytes and bundle ID.

## 2. Run focused verification

```powershell
uv run pytest packages/tool_registry/tests/test_program_status.py apps/api/tests/test_program_status_api.py tests/program_control_plane/test_program_status_publisher.py
npm --prefix apps/web run test -- --run ProgramStatus
npx playwright test tests/ui-integration/program-status.spec.ts
```

Expected: valid, corrupt, stale, empty, source-catalog mutation, raw-attestation evidence mismatch, canonical-identity mismatch, current/historical-action conflict, zero-benchmark missing context, correction/finding/verification mislink, non-canonical path, malformed parsed GitHub URL, auth, refresh, accessibility, and deterministic-regeneration cases pass.

## 3. Open the page

Configure `WRIGHT_DATA_ROOT` to the demo root using Wright's normal local runtime command, then open `http://127.0.0.1:<wright-port>/program-status`.

Confirm:

1. Four independent readiness areas and non-compensating release state are clear.
2. Benchmark is honestly `0/100` with typed phase, hold state/reason, dependency states, authority, and non-governing next qualifying action.
3. `100 proposed customer stories` is separate from qualified benchmark results.
4. Charts use exact times and commits and explain change, importance, limitation, and next action.
5. Task completion is explicitly feature-local and does not imply whole-product completion.
6. The dashboard's old action is visibly historical, exactly one current program action comes from current program state, and metric/lane guidance cannot supersede it.
7. Integration/CI and continued-development lanes have distinct branches and purpose-labeled actions.
8. Evidence details use canonical relative paths and parsed-safe URLs, expose freshness/recovery without sensitive content, and show reciprocal correction/finding/verification links plus verdict/blocking outcome.

## 4. Demonstrate failure containment

Alter an isolated copy of the demo projection without changing its envelope digest. Do not edit committed evidence.

Expected: the fixture is rejected; the last valid page remains visible and is labeled failed/stale with recovery. Starting without a valid bundle shows unavailable values only.

## 5. Demonstrate committed refresh

Start the standard contributor publisher in a third terminal, then commit an isolated approved fixture change while the page remains open:

```powershell
uv run python scripts/publish-engineering-program-status.py --watch-committed --data-root .local-run/program-status-demo
```

Expected: the watcher uses its declared two-second default; within 10 seconds it observes the new committed identity, atomically installs it, the ETag changes, and every panel swaps together. Unchanged identity returns 304 and adds no history point. The separate publisher endpoint and refresh state show activity or bounded failure without changing bundle identity.

## 6. Delivery gates

After implementation authority exists, run normal repository checks, packaged-runtime smoke without `.git` or network, and then the dev push/merge runbooks. Direct push to `dev` is never permitted.
