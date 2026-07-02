# Wright Web App

React + TypeScript + Vite frontend for the Wright local-first engineering UI.

## Development

```bash
npm run dev --workspace=apps/web
npm run test --workspace=apps/web
```

The app consumes checked-in generated domain contracts from:

```text
apps/web/src/types/generated/wright-contracts.ts
```

Regenerate or verify them from the repository root:

```bash
uv run python scripts/generate-frontend-contracts.py
uv run python scripts/generate-frontend-contracts.py --check
```

Generated contracts mirror backend/package schemas for workspace lifecycle,
agent runtime metadata, MCP safety decisions, and validation evidence. UI-only
presentation constants can remain hand-authored, but domain truth should come
from generated contracts or API responses.
