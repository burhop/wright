# Developer Quickstart: Engineering Workspace

This guide explains how to get started developing and testing the Engineering Workspace features.

## 1. Setup & Environment

Ensure that `git` is installed on your local host (GB10 machine) and available in your environment:
```bash
git --version
```

Verify that the FastAPI backend runs on Python 3.13 and uses uv workspace:
```bash
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

Start the React Web UI in dev mode:
```bash
npm run dev --workspace=web -- --force
```

## 2. Initializing database migrations

Run the database migration script to ensure the `engineering_workspaces` metadata table is initialized:
```bash
uv run python -m api.database.migrate
```

## 3. Developing and Testing Backend Endpoints

Backend tests for workspace operations are written under `apps/api/tests/`. 
To run all workspace and Git tests:
```bash
uv run pytest apps/api/tests/test_workspace_api.py -v
```

### Manual testing with Curl
You can hit the local endpoints to test tree traversal, CRUD, or git commands.

**Fetch Workspace File Tree**:
```bash
curl -X GET "http://127.0.0.1:8000/api/workspace/files?session_id=your-session-id"
```

**Get Git status**:
```bash
curl -X GET "http://127.0.0.1:8000/api/workspace/git/status?session_id=your-session-id"
```

**Commit changes**:
```bash
curl -X POST "http://127.0.0.1:8000/api/workspace/git/commit" \
     -H "Content-Type: application/json" \
     -d '{"session_id": "your-session-id", "message": "feat: add initial mock brackets"}'
```

**Get Workspace Remote Configuration**:
```bash
curl -X GET "http://127.0.0.1:8000/api/workspace/config?session_id=your-session-id"
```

**Update Workspace Remote Configuration**:
```bash
curl -X POST "http://127.0.0.1:8000/api/workspace/config" \
     -H "Content-Type: application/json" \
     -d '{"session_id": "your-session-id", "git_remote_url": "https://github.com/username/repo.git", "git_username": "username", "git_token": "token"}'
```

**Push changes to Remote**:
```bash
curl -X POST "http://127.0.0.1:8000/api/workspace/git/push" \
     -H "Content-Type: application/json" \
     -d '{"session_id": "your-session-id"}'
```

**Pull changes from Remote**:
```bash
curl -X POST "http://127.0.0.1:8000/api/workspace/git/pull" \
     -H "Content-Type: application/json" \
     -d '{"session_id": "your-session-id"}'
```

## 4. Frontend Component Testing

The React code resides in `apps/web/src/`.
- File tree UI is tested via Vitest:
```bash
npm run test --workspace=web
```
- E2E interactions (like drag-and-drop or context menu clicks) can be checked using Playwright:
```bash
npx playwright test tests/ui-integration/
```
