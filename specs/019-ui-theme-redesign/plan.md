# Implementation Plan: UI Redesign and Global Color Schemes

**Branch**: `019-ui-theme-redesign` | **Date**: 2026-06-06 | **Spec**: [spec.md](file:///home/burhop/repos/wright/specs/019-ui-theme-redesign/spec.md)

**Input**: Feature specification from `/specs/019-ui-theme-redesign/spec.md`

## Summary

This plan outlines the visual redesign and typography improvements of the Wright user interface. It focuses on fixing panel overlaps, alignment of icons/buttons, size/font scaling, and implementing a single-source-of-truth theming system. The theme (e.g., light or dark) is loaded dynamically at startup from a backend configuration file or environment variables and applied to the root of the document. We will write both unit (Vitest) and end-to-end (Playwright) tests to ensure layout consistency and correct styling application across the app.

## Technical Context

**Language/Version**: Python 3.11 (Backend), TypeScript 5.x / React 19.x (Frontend)

**Primary Dependencies**: FastAPI (Backend), React, Vite (Frontend), CSS Variables (Design Tokens)

**Storage**: Local system configuration (via environment variables and SQLite system_settings table)

**Testing**: Vitest + React Testing Library (Component tests), Playwright (UI integration/E2E tests)

**Target Platform**: Modern Web Browsers, Headless Linux Environments (Docker compose / dev workspace)

**Project Type**: Web Application (React frontend + FastAPI backend)

**Performance Goals**: Active theme loaded and applied in <50ms; zero visual shifting or flash of unstyled content (FOUC).

**Constraints**: Offline-capable, zero external CDNs for styles/fonts (fonts hosted locally or using system fallbacks), strict adherence to the typography scale.

**Scale/Scope**: Entire application UI (Dashboard, Tool Registry, File Vault, navigation sidebar).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Component Layers**: **Pass**. All visual properties (colors, border-radii, shadows, fonts) will be bound strictly to design tokens in `design-tokens.css` using CSS custom properties. No ad-hoc colors or custom inline dimensions.
- **Testing**: **Pass**. Component-level rendering tests will run under Vitest. Page-level layout consistency and theme loading will be validated via a new Playwright UI integration test.
- **Test IDs**: **Pass**. All interactive elements and core containers (cards, panels, toggles) will include specific `data-testid` attributes (e.g., `theme-container`, `tool-card`).
- **Offline-First Mandate**: **Pass**. The CSS and typography changes will not query external assets; all fonts and icons will use local files or standard SVG packages.

## Project Structure

### Documentation (this feature)

```text
specs/019-ui-theme-redesign/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 data modeling schema
└── quickstart.md        # Developer setup and instructions
```

### Source Code (repository root)

```text
apps/api/
├── src/api/
│   ├── config.py             # Add UI_THEME configuration
│   └── routers/setup.py      # Include theme setting in SetupStatusResponse
└── tests/
    └── test_setup_api.py     # Update backend tests for the theme endpoint

apps/web/
├── src/
│   ├── tokens/
│   │   └── design-tokens.css # Light and dark theme CSS Custom Properties
│   ├── App.css               # Consistent layout styling and neomorphic improvements
│   ├── index.css             # Typography scale and general card shapes
│   ├── App.tsx               # Fetch/apply configuration theme at root
│   └── test/
│       └── UITheme.spec.tsx  # NEW: Frontend component test
└── tests/
    └── ToolRegistry.spec.tsx # Keep existing tests

tests/ui-integration/
└── ui-consistency-theme.spec.ts  # NEW: Playwright layout/theme consistency integration test
```

**Structure Decision**: A Web Application architecture (React + FastAPI backend) with existing folder structures. We are adding layout styling files (`design-tokens.css`, `App.css`) and integration tests under `tests/ui-integration`.

## Complexity Tracking

*No violations of the Constitution identified.*
