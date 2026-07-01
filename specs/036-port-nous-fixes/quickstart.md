# Quickstart: Port Nous Fixes

## 1. Confirm Branch and Candidate Folder

```powershell
git status --short --branch
Get-Content scratch/nous_hackathon_candidates/MANIFEST.md
```

Expected:

- Current branch is `codex/port-nous-good-fixes`.
- Candidate folder exists and contains copied review files.

## 2. Review a Candidate

```powershell
git diff --no-index -- apps/api/src/api/routers/gateway.py scratch/nous_hackathon_candidates/apps/api/src/api/routers/gateway.py
```

Expected:

- Diff is reviewed before live files are modified.
- Mixed-risk hunks are skipped unless they are independent bug fixes.

## 3. Apply Selected Changes

```powershell
git restore -p --source=nous_hackathon -- apps/api/src/api/routers/gateway.py
```

Expected:

- Only selected hunks are applied to the live file.
- Excluded prototype behavior remains absent.

## 4. Validate

```powershell
uv run pytest apps/api/tests/test_gateway_api.py packages/agent_adapters/tests/test_hermes_gateway_adapter.py
npm run test --workspace=apps/web
```

Expected:

- Targeted tests pass, or failures are documented with next actions.

## 5. Final Exclusion Check

```powershell
git diff --name-only
git diff -- apps/api/src/api/routers/billing.py packages/tool_registry/src/tool_registry/paid_demo_mcp.py
```

Expected:

- No excluded prototype source files appear in the final applied diff.
