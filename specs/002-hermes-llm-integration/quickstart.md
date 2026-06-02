# Quickstart: Hermes & LLM Integration

**Branch**: `002-hermes-llm-integration` | **Date**: 2026-06-02

## Prerequisites

- Hermes Agent v0.15+ installed (`hermes --version`)
- Hermes gateway running (`hermes gateway status`)
- LLM inference server accessible (vLLM at `http://promaxgb10-5c88:8000/v1`)
- Wright monorepo cloned and dependencies installed (`uv sync`, `npm install`)

## Setup

### 1. Create the Wright Hermes Profile

```bash
# Create isolated profile, cloning LLM config from default
hermes profile create wright --clone --description "Wright engineering assistant"

# Verify
hermes profile list
# Should show: ◆default + wright
```

### 2. Start the Wright Profile WebUI

```bash
# Start a dedicated WebUI instance for the wright profile on port 8788
cd ~/hermes-webui
HERMES_HOME=~/.hermes/profiles/wright ./ctl.sh start 8788

# Verify
curl http://127.0.0.1:8788/api/health
```

### 3. Start the Wright Application

```bash
# From the wright repo root
cd ~/repos/wright

# Start both API and frontend
# Option A: Use VS Code/Antigravity IDE Run configuration
# Select "Wright App (API + Frontend - Standard Run)" and press F5

# Option B: Manual start
uv run uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload &
cd apps/web && npm run dev &
```

### 4. Verify End-to-End

1. Open `http://localhost:5173` in your browser
2. Navigate to "Agent Chat" in the sidebar
3. Create a new session (click "+")
4. Type a message and press Send
5. You should see a streamed response from the Hermes agent

## Running Tests

```bash
# Component tests (Vitest)
npm run test --prefix apps/web

# Integration tests (Playwright)
npx playwright test

# Python tests
uv run pytest
```

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Status bar shows red "Hermes Agent" | Wright profile WebUI not running | `HERMES_HOME=~/.hermes/profiles/wright /home/burhop/hermes-webui/ctl.sh start 8788` |
| Status bar shows red "LLM Inference" | vLLM server offline | Check `curl http://promaxgb10-5c88:8000/health` |
| "Hermes agent unavailable" error in chat | Backend cannot reach WebUI | Verify `curl http://127.0.0.1:8788/api/health` |
| Profile already exists error | Wright profile was previously created | Safe to ignore — profile is idempotent |
