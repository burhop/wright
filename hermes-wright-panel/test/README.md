# hermes-wright-panel Test Harness

This directory contains a minimal Electron test harness to verify that the `WrightPanel` successfully instantiates, creates a BrowserView, sets up preload IPC channels, and loads the desktop build.

## Prerequisites

1. Build the desktop-compatible frontend bundle:
   ```bash
   npm run build:desktop --workspace=apps/web
   ```

2. Make sure the local FastAPI backend server is running:
   ```bash
   uv run uvicorn api.main:app --host 0.0.0.0 --port 8000
   ```

## Running the Test

Run the test using Electron. If Electron is not installed globally, you can execute it via `npx`:

```bash
npx electron hermes-wright-panel/test/electron-test.cjs
```

The script will launch Electron in headless mode (`show: false`), load the panel and `dist-desktop` build, verify IPC channel registration, and exit with status code `0` on success.
