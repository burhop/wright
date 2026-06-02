# Implementation Plan: Initial UI Foundation

**Branch**: `001-initial-ui` | **Date**: 2026-06-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-initial-ui/spec.md`

## Summary

Build the first interactive frontend for Wright: a React-based web application in `apps/web/` featuring an engineering dashboard, Hermes-style three-panel agent chat interface (sessions sidebar, chat transcript, workspace file browser), section routing, and service health indicators. The UI integrates structured logging (console-based structured JSON) and OpenTelemetry-compatible telemetry from day one. Playwright provides integration testing. The design system follows the Hermes WebUI "calm-console" aesthetic, re-implemented in React with CSS custom properties as design tokens. No Docker integration in this phase.

## Technical Context

**Language/Version**: TypeScript 5.x on Node.js 22+ (frontend); Python 3.11+ (existing backend — not modified in this feature)

**Primary Dependencies**: React 19, React Router 7, Vite 6 (dev/build), OpenTelemetry Web SDK (@opentelemetry/sdk-trace-web), Playwright (testing)

**Storage**: N/A for this feature (client-side state only; localStorage for session persistence)

**Testing**: Playwright (Tier 2 UI integration tests), Vitest (Tier 1 component tests)

**Target Platform**: Modern desktop browsers (Chrome, Firefox, Edge — latest 2 major versions)

**Project Type**: Web application (frontend SPA within the `apps/web/` monorepo member)

**Performance Goals**: Dashboard interactive in <3s, chat message render <500ms, agent chat three-panel layout render <2s

**Constraints**: Offline-capable (must render without backend), single-user (no auth in v1), dark-theme-first, all interactive elements have `data-testid`

**Scale/Scope**: 4 routable sections (Dashboard, Agent Chat, Tool Registry, File Vault), 1 chat interface with session management, ~15–20 React components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Requirement | Status | Notes |
|------|-------------|--------|-------|
| § 1 — Modular Monorepo | Frontend lives in `apps/web/` workspace member | ✅ PASS | Added to `uv` workspace as a non-Python member; managed via npm |
| § 1 — Offline-First | UI must function without backend | ✅ PASS | Stub data, placeholder states, localStorage persistence |
| § 2 — Agent Abstraction | Hermes integrated via adapter, not hardcoded | ✅ PASS | Chat uses an `AgentService` abstraction; Hermes is one provider |
| § 6 — Atomic Design | Tokens → Primitives → Components → Patterns | ✅ PASS | CSS custom properties as tokens, shared component library |
| § 6 — Tier 1 Tests | Component tests for interactive elements | ✅ PASS | Vitest + React Testing Library for component states |
| § 6 — Tier 2 Tests | Playwright in `tests/ui-integration/` | ✅ PASS | Playwright config at project root; tests in `tests/ui-integration/` |
| § 6 — Test IDs | `data-testid` on all interactive elements | ✅ PASS | Enforced by component conventions |
| § 7 — Structured Logging | Structured JSON logging, no text logs | ✅ PASS | Browser-side structured logger emitting JSON to console |
| § 7 — OpenTelemetry | Trace context for user actions | ✅ PASS | @opentelemetry/sdk-trace-web with ConsoleSpanExporter initially |
| § 7 — UI Transparency | Surface agent decisions to user | ✅ PASS | Chat transcript shows tool calls, trace IDs visible in status area |
| § 8 — Branch Discipline | Feature branch for work | ✅ PASS | Working on `001-initial-ui` |

## Project Structure

### Documentation (this feature)

```text
specs/001-initial-ui/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── ui-contracts.md  # Component and service API contracts
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
apps/web/
├── package.json              # Vite + React + TypeScript + Playwright deps
├── vite.config.ts            # Vite config with dev server proxy
├── tsconfig.json             # TypeScript config
├── index.html                # Vite entry HTML
├── playwright.config.ts      # Playwright configuration
├── src/
│   ├── main.tsx              # React entry point — initializes telemetry + logger
│   ├── App.tsx               # Root component with router
│   ├── tokens/
│   │   └── design-tokens.css # CSS custom properties (Hermes calm-console palette)
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppShell.tsx      # Top-level layout (header + sidebar + content)
│   │   │   ├── Sidebar.tsx       # Navigation sidebar
│   │   │   ├── Header.tsx        # App header with status area
│   │   │   └── StatusBar.tsx     # Service health indicators
│   │   ├── chat/
│   │   │   ├── ChatLayout.tsx    # Three-panel Hermes-style layout
│   │   │   ├── SessionsSidebar.tsx # Left panel: session list + management
│   │   │   ├── ChatTranscript.tsx  # Center panel: message list
│   │   │   ├── MessageComposer.tsx # Composer with send button
│   │   │   ├── MessageBubble.tsx   # Individual message rendering
│   │   │   └── WorkspacePanel.tsx  # Right panel: file tree browser
│   │   ├── common/
│   │   │   ├── StatusDot.tsx     # Colored status indicator primitive
│   │   │   ├── NavItem.tsx       # Navigation item primitive
│   │   │   ├── FileTree.tsx      # Recursive file tree component
│   │   │   └── Placeholder.tsx   # Placeholder content for empty states
│   │   └── pages/
│   │       ├── DashboardPage.tsx    # Dashboard view
│   │       ├── AgentChatPage.tsx    # Agent chat (wraps ChatLayout)
│   │       ├── ToolRegistryPage.tsx # Tool registry placeholder
│   │       ├── FileVaultPage.tsx    # File vault placeholder
│   │       └── NotFoundPage.tsx     # 404 page
│   ├── services/
│   │   ├── logger.ts           # Structured JSON logger (console output)
│   │   ├── telemetry.ts        # OpenTelemetry initialization + trace helpers
│   │   ├── agent-service.ts    # Agent communication abstraction (stub in v1)
│   │   └── health-service.ts   # Service health polling
│   ├── hooks/
│   │   ├── useLogger.ts        # React hook for component-scoped logging
│   │   ├── useTrace.ts         # React hook for action tracing
│   │   └── useHealthStatus.ts  # React hook for service health polling
│   ├── store/
│   │   ├── sessions.ts         # Chat session state management
│   │   └── types.ts            # Shared TypeScript types
│   └── test/
│       └── setup.ts            # Vitest setup (JSDOM, test utilities)
├── tests/
│   └── *.spec.ts               # Vitest component tests (Tier 1)
│
tests/ui-integration/           # Tier 2 — Playwright (at repo root per constitution)
├── dashboard.spec.ts
├── navigation.spec.ts
└── agent-chat.spec.ts
```

**Structure Decision**: The `apps/web/` directory follows a feature-grouped component structure aligned with the Hermes WebUI layout patterns. Components are organized by domain (layout, chat, common, pages) rather than by type. Services provide abstraction boundaries for logging, telemetry, and agent communication. The `tests/ui-integration/` directory remains at the repo root per constitution § 6.

## Complexity Tracking

No constitution violations requiring justification. All gates pass.
