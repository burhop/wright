# Quickstart: Dual-Mode Desktop Integration

**Feature**: 032-dual-mode-desktop | **Date**: 2026-06-23

## For Wright Developers

### Running in Browser Mode (unchanged)

```bash
# Start the backend
cd ~/repos/wright
uv run uvicorn api.main:app --host 0.0.0.0 --port 8000

# Start the frontend (dev)
npm run dev --workspace=apps/web -- --host

# Open http://localhost:5173
```

### Building for Desktop

```bash
# Build the desktop-compatible version
npm run build:desktop --workspace=apps/web

# Output: apps/web/dist-desktop/
# This can be loaded by any Electron app with the hermes-wright-panel package
```

### Testing Desktop Mode Locally

```bash
# Run the adapter unit tests
npx vitest run apps/web/src/services/host-adapter/

# Run all existing tests (must still pass)
npm run test --workspace=apps/web
```

## For Electron App Integrators

### Installing the Integration Package

```bash
npm install hermes-wright-panel
# or from local development:
npm install ../wright/hermes-wright-panel
```

### Minimal Integration (10 lines)

```javascript
// In your Electron main process:
const { WrightPanel } = require('hermes-wright-panel');

app.whenReady().then(() => {
  const mainWindow = new BrowserWindow({ width: 1200, height: 800 });
  
  const wright = new WrightPanel(mainWindow, {
    wrightApiPort: 8000,
    distPath: '/path/to/wright/apps/web/dist-desktop'
  });
  
  const view = wright.createView();
  mainWindow.setBrowserView(view);
  view.setBounds({ x: 0, y: 0, width: 1200, height: 800 });
});
```

### Configuration Options

| Option | Type | Default | Description |
|:---|:---|:---|:---|
| `wrightApiPort` | `number` | `8000` | Port of the running Wright FastAPI backend |
| `distPath` | `string?` | `null` | Path to Wright's `dist-desktop/` directory. If null, loads from `http://localhost:{wrightApiPort}` |
| `workspacePath` | `string?` | `null` | Default workspace root for file operations |

## Development Workflow

1. **Modify Wright UI** → Changes are automatically picked up in browser mode via Vite HMR
2. **Test desktop adapter** → Run Vitest with the mock `window.wrightDesktop` bridge
3. **Build for desktop** → `npm run build:desktop --workspace=apps/web`
4. **Test in Electron** → Load `dist-desktop/` in a test Electron shell
5. **Package** → `cd hermes-wright-panel && npm pack`
