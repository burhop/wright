# Quickstart: Migrate to Hermes Native API

**Feature**: 025-migrate-hermes-native-api | **Date**: 2026-06-11

## Prerequisites

- `hermes-agent` v0.15.2+ installed (via `uv tool install hermes-agent`)
- Wright profile created: `hermes profile create wright --clone`
- LLM inference endpoint accessible

## Local Development Setup

### 1. Configure the Wright Profile

```bash
# Enable the API server in the wright profile
hermes -p wright config set API_SERVER_ENABLED true
hermes -p wright config set API_SERVER_KEY "wright-dev-key-change-me"
hermes -p wright config set API_SERVER_PORT 8642
```

### 2. Write the MCP Config (one-time)

Ensure `~/.hermes/profiles/wright/config.yaml` contains:

```yaml
mcp_servers:
  wrightgateway:
    command: uv
    args:
      - run
      - --project
      - /home/burhop/repos/wright
      - python
      - -m
      - tool_registry.gateway
```

### 3. Start the Gateway

```bash
hermes -p wright gateway start
```

Verify it's running:

```bash
curl -s http://127.0.0.1:8642/health
# Expected: {"status": "ok"}
```

### 4. Start the Wright API

```bash
cd /home/burhop/repos/wright
HERMES_API_PORT=8642 HERMES_API_KEY=wright-dev-key-change-me uv run uvicorn api.main:app --reload --port 8000
```

### 5. Start the Frontend

```bash
cd /home/burhop/repos/wright
npm run dev --workspace=apps/web
```

### 6. Verify End-to-End

1. Open `http://localhost:5173`
2. Create or open a workspace
3. Send a message in the chat composer
4. Verify streamed response appears in the transcript
5. Enable/disable an MCP tool in workspace settings
6. Verify tool availability changes without service interruption

## Docker Deployment

```bash
docker build -t wright:latest -f docker/Dockerfile .
docker run -p 8000:8000 wright:latest
```

Verify inside container:

```bash
docker exec <container> supervisorctl status
# Expected:
# wright-api          RUNNING
# hermes-gateway      RUNNING
```

## Verification Checklist

| Check | Command | Expected |
|-------|---------|----------|
| Gateway health | `curl http://127.0.0.1:8642/health` | `{"status": "ok"}` |
| Wright API health | `curl http://localhost:8000/api/health` | `{"state": "connected", ...}` |
| Agent health via Wright | `curl http://localhost:8000/api/agent/health` | `{"state": "connected", ...}` |
| Create session | `curl -X POST http://localhost:8000/api/agent/sessions/new -H 'Content-Type: application/json' -d '{"workspace": "/tmp/test"}'` | `{"session_id": "...", ...}` |
| Chat | Send message in UI | Streamed response appears |
| MCP toggle | Enable tool in workspace settings | Tool available without restart |
| Status bar | Check status bar indicators | Green connected state |

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Status bar shows red "Hermes Agent" | Gateway not running | `hermes -p wright gateway start` |
| "401 Unauthorized" in API logs | API key mismatch | Verify `HERMES_API_KEY` matches `API_SERVER_KEY` in profile `.env` |
| Tools not updating after toggle | Gateway not watching config | Check `gateway.py` SSE connection to Wright API |
| Port 8642 already in use | Previous gateway instance | `hermes -p wright gateway stop` then restart |
| Pre-migration Session (404 Error) | Legacy session from `hermes-webui` | A clean session start is required. Legacy sessions are incompatible. |
