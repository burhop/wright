# Implementation Plan: Dual-Mode Wright UI (Standalone + Hermes Desktop)

**Branch**: `032-dual-mode-desktop` | **Date**: 2026-06-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/032-dual-mode-desktop/spec.md`

## Summary

This feature adds a Host Adapter abstraction layer to the Wright web frontend so the same React codebase runs both as a standalone browser app and embedded inside Hermes Desktop's Electron shell via a BrowserView with a custom preload bridge. The implementation includes:

1. **Host Adapter Layer**: A `HostAdapter` interface with `BrowserHostAdapter` (wraps current fetch/routing behavior) and `DesktopHostAdapter` (delegates to `window.wrightDesktop` IPC bridge).
2. **Service Refactoring**: Migrate `api-client.ts`, `workspace-service.ts`, and `App.tsx` to use the adapter instead of direct fetch() and hardcoded BrowserRouter.
3. **Dual Build Targets**: Vite config supporting `dist/` (browser) and `dist-desktop/` (Electron, relative paths).
4. **Integration Package**: `hermes-wright-panel/` — a standalone npm package with Electron preload, panel manager, and TypeScript types. Does NOT modify Hermes Desktop.
5. **Desktop Enhancements**: Theme sync, titlebar awareness, native file dialogs, system notifications, direct filesystem access, and terminal integration.

## Technical Context

**Language/Version**: TypeScript 6.0 (frontend), Python 3.13 (backend — unchanged), JavaScript/CommonJS (Electron integration)

**Primary Dependencies**: React 19, Vite 8, react-router-dom 7, Electron 30+ (integration target)

**Storage**: N/A (no new storage — uses existing Wright API backend)

**Testing**: Vitest 4 (unit), Playwright (integration)

**Target Platform**: Browser (standalone), Electron 30+ on macOS/Windows/Linux (desktop)

**Project Type**: Web Application + Electron Integration Package

**Performance Goals**: Desktop IPC proxy adds <50ms latency over direct HTTP; filesystem operations are 2x+ faster than HTTP-based.

**Constraints**: Zero modifications to `NousResearch/hermes-agent`. Existing browser-mode tests must pass unchanged.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Modular Monorepo Boundaries**: The Host Adapter is a new service module within `apps/web/src/services/` — clean boundary. The integration package (`hermes-wright-panel/`) is a separate, self-contained npm package at the repo root. (Pass)
- **Offline-First Mandate**: Desktop mode works fully offline when the Wright FastAPI backend is running locally. The adapter has no cloud dependencies. (Pass)
- **Agent Abstraction**: No changes to agent/LLM integration. The adapter only affects the transport layer for API calls. (Pass)
- **Container Strategy**: The desktop build (`dist-desktop/`) is an additional build target — does not affect Docker builds which use the standard `dist/`. (Pass)
- **UI Component Layers**: The adapter is a service-layer concern. The only UI changes are in `App.tsx` (router selection) and `AppShell.tsx` (titlebar awareness) — both follow the existing component hierarchy. (Pass)
- **Structured Logging**: The adapter uses the existing `logger` service for diagnostic output. (Pass)

## Project Structure

### Documentation (this feature)

```text
specs/032-dual-mode-desktop/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research findings
├── data-model.md        # Phase 1 entity definitions
├── quickstart.md        # Phase 1 developer quickstart
└── contracts/
    └── ipc-contract.md  # IPC channel definitions
```

### Source Code (repository root)

```text
apps/web/
├── src/
│   ├── services/
│   │   └── host-adapter/          # [NEW] Host adapter abstraction
│   │       ├── host-adapter.ts    # Core interface + types
│   │       ├── browser-adapter.ts # Browser implementation
│   │       ├── desktop-adapter.ts # Desktop/Electron implementation
│   │       ├── detect.ts          # Environment detection
│   │       └── index.ts           # Auto-detect + singleton export
│   ├── hooks/
│   │   └── useDesktopIntegration.ts  # [NEW] Desktop integration hook
│   ├── components/layout/
│   │   └── AppShell.tsx           # [MODIFIED] Titlebar awareness
│   ├── App.tsx                    # [MODIFIED] Dynamic router
│   └── services/
│       ├── api-client.ts          # [MODIFIED] Use adapter
│       └── workspace-service.ts   # [MODIFIED] Use adapter for file ops
├── vite.config.ts                 # [MODIFIED] Desktop build mode
└── package.json                   # [MODIFIED] build:desktop script

hermes-wright-panel/               # [NEW] Integration package
├── package.json
├── preload.cjs
├── panel.cjs
├── types.d.ts
└── README.md
```

**Structure Decision**: Web application with existing `apps/web` frontend. The integration package is a separate standalone directory at the repo root alongside `hermes-plugin-wright/`, following the established pattern of Hermes-integration packages.

## Complexity Tracking

*No Constitution violations detected.*
