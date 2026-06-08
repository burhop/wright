# Developer Quickstart: Theme Configuration

## 1. Setting the Active Theme
The UI color scheme is configuration-driven. Developers and administrators can set it using the `UI_THEME` environment variable.

### Option A: Local Dev Environment
Set the environment variable when launching the uvicorn API backend server:
```bash
export UI_THEME=light
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

### Option B: Docker Environment
Add the environment variable definition inside `docker/.env`:
```env
UI_THEME=light
```
Then start the stack:
```bash
docker compose up -d --build
```

---

## 2. Running the UI Consistency Test Suite

### Running Component Unit Tests (Vitest)
```bash
npm run test --workspace=apps/web
```

### Running Playwright Layout Consistency Tests
```bash
npx playwright test tests/ui-integration/ui-consistency-theme.spec.ts
```
