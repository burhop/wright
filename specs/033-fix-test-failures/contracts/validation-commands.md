# Validation Command Contract

The bugfix is complete only when these commands behave as follows from the repository root on Windows.

| Command | Expected Result |
|---------|-----------------|
| `npm run test --workspace=apps/web` | Exits 0 with all Vitest tests passing |
| `npm run build --workspace=apps/web` | Exits 0 and writes standard browser assets |
| `npm run build:desktop --workspace=apps/web` | Exits 0 and writes `apps/web/dist-desktop/` |
| `uv run pytest` | Does not fail collection because declared workspace packages or dependencies are missing |

Any remaining test failure after these fixes must be an actionable assertion/runtime failure, not a shell portability or missing declared dependency failure.
