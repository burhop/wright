# Research: Initial UI Foundation

**Feature**: 001-initial-ui | **Date**: 2026-06-02

## R1: Hermes WebUI Integration Approach

**Decision**: Re-implement Hermes WebUI's three-panel chat layout and interaction patterns in React, rather than embedding Hermes WebUI directly via iframe or forking the vanilla JS codebase.

**Rationale**:
- Hermes WebUI is vanilla JS (no framework, no build step). Embedding it inside a React application would create two separate DOM management systems, leading to state synchronization issues and conflicting event handlers.
- The Hermes architecture (ARCHITECTURE.md) shows a tightly-coupled design: global `S` state object, module-level side effects, process-global environment variables. This is designed for standalone operation, not embedding.
- Re-implementing the UI patterns in React allows us to use React's component model, hooks, and state management — aligning with the rest of the Wright frontend.
- We specifically adopt Hermes's **layout structure** (three-panel: sessions sidebar, chat center, workspace panel), **design language** (calm-console aesthetic), and **interaction patterns** (session CRUD, SSE streaming, tool call cards) while using idiomatic React.

**Alternatives considered**:
- **iframe embed**: Would isolate Hermes but prevent deep integration (shared design tokens, routing, telemetry). The user would experience two separate apps. Rejected.
- **Fork and modify vanilla JS**: Would inherit ~22,000+ lines of JS without React's component model. Maintenance burden would diverge quickly from upstream. Rejected.
- **Use Hermes as a backend only**: Hermes WebUI serves the chat API — Wright's React frontend could talk to Hermes's Python API. This is the eventual goal for the agent backend, but for v1 we need the UI to work without a running Hermes server. The React UI uses stub data. Decided to implement the UI layer now and wire to Hermes's API later.

## R2: React + Vite Stack Selection

**Decision**: Use React 19 with Vite 6 and TypeScript 5.x.

**Rationale**:
- React is explicitly requested by the user.
- Vite provides instant HMR, fast builds, and native TypeScript support without ejection or complex Webpack config.
- TypeScript enforces type safety for components, services, and the data model — important for a growing monorepo.
- The existing monorepo uses `uv` for Python packages. The `apps/web/` member will use npm/package.json for JS tooling (no uv conflict — uv ignores non-Python workspace members).

**Alternatives considered**:
- **Next.js**: SSR/SSG features are unnecessary for a single-user local application. Adds complexity (server components, routing conventions) without benefit. Rejected.
- **Create React App**: Deprecated in favor of Vite. Rejected.

## R3: Design Token System (Hermes Calm-Console Alignment)

**Decision**: Implement design tokens as CSS custom properties, using the Hermes WebUI DESIGN.md color palette and typography as the starting point.

**Rationale**:
- The constitution (§ 6) mandates atomic design with tokens as the foundation.
- Hermes DESIGN.md provides a complete token set: colors (primary #EAE0D5, surface #22333B, neutral #0A0908), typography (Georgia serif for body, system sans-serif for UI, SF Mono for code), spacing (4/8/12/16px), and border radius (4/8/12px + pill).
- CSS custom properties work natively in any browser, require no build tooling, and can be overridden at runtime for theming.
- All Wright components will reference tokens like `--color-surface`, `--font-body-md`, `--space-md` rather than hardcoded values.

**Alternatives considered**:
- **Tailwind CSS**: Utility-first approach conflicts with atomic design mandate. Design token changes would require touching every component. Not requested by user. Rejected.
- **CSS-in-JS (styled-components/emotion)**: Adds runtime overhead, requires build tooling integration. CSS custom properties achieve the same theming capability with zero runtime cost. Rejected.

## R4: Structured Logging for Browser

**Decision**: Implement a lightweight structured JSON logger that writes to `console.log` with structured payloads.

**Rationale**:
- Constitution § 7 mandates structured JSON logging. No text logs.
- Browser applications don't have access to `structlog` (Python). We need a JS equivalent.
- A thin wrapper around `console.log` that emits JSON objects (`{timestamp, level, message, component, metadata}`) satisfies the requirement without adding a dependency.
- In a future feature, these logs can be forwarded to the backend (FastAPI → structlog → Jaeger) or collected via the OTLP log exporter.

**Alternatives considered**:
- **pino (browser build)**: Full-featured structured logger, but adds a dependency for something achievable in ~50 lines. Can adopt later if log volume grows. Rejected for v1.
- **console.log with no structure**: Violates constitution § 7. Rejected.

## R5: OpenTelemetry Web SDK

**Decision**: Use `@opentelemetry/sdk-trace-web` with `ConsoleSpanExporter` for v1. Upgrade to OTLP exporter when Jaeger is wired via Docker.

**Rationale**:
- Constitution § 7 mandates OpenTelemetry traces with trace IDs on every user request.
- The OTEL Web SDK provides `TracerProvider`, `SimpleSpanProcessor`, and automatic instrumentation for fetch/XHR.
- `ConsoleSpanExporter` outputs traces to the browser console — visible for debugging, satisfies the "generate trace context" requirement, and can be swapped for OTLP later.
- Trace IDs will be surfaced in the UI status area (SC-006).

**Alternatives considered**:
- **Custom trace implementation**: Would reinvent OTEL's context propagation. Not standards-compliant. Rejected.
- **Skip telemetry, add later**: Constitution mandates it from day one. Rejected.

## R6: Playwright Test Strategy

**Decision**: Playwright tests in `tests/ui-integration/` at the repo root. Dev server started by Playwright's `webServer` config pointing to `apps/web/`.

**Rationale**:
- Constitution § 6 mandates Tier 2 Playwright tests in `tests/ui-integration/`.
- Playwright's `webServer` option auto-starts Vite dev server before tests, no manual server management.
- Tests validate page-level user journeys: dashboard renders, navigation works, agent chat layout loads.
- Component-level tests (Tier 1) use Vitest + React Testing Library inside `apps/web/tests/`.

**Alternatives considered**:
- **Cypress**: Slower, heavier, less first-class support for modern React. Playwright is the industry standard for headless browser testing. Rejected.
- **Tests inside apps/web/**: Would violate constitution § 6 which specifies `tests/ui-integration/` at repo root. Rejected.

## R7: State Management for Chat Sessions

**Decision**: Use React Context + useReducer for chat session state. No external state library in v1.

**Rationale**:
- The chat state is modest: a list of sessions, active session, messages array, and busy flag — similar to Hermes's global `S` object but decomposed into React state.
- React Context + useReducer provides predictable state transitions without adding a dependency (Redux, Zustand, etc.).
- If state complexity grows (multi-agent sessions, concurrent streams), we can migrate to Zustand or Redux Toolkit without changing component APIs.

**Alternatives considered**:
- **Redux Toolkit**: Overkill for ~4 state slices. Adds boilerplate and a dependency. Revisit if state grows. Rejected for v1.
- **Zustand**: Lightweight and excellent, but Context + useReducer is sufficient for the initial scope and has zero dependencies. Can upgrade later. Rejected for v1.
