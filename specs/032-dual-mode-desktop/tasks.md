# Tasks: Dual-Mode Wright UI (Standalone + Hermes Desktop)

**Input**: Design documents from `/specs/032-dual-mode-desktop/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Include unit tests for the new adapter layer to verify environment detection and adapter behavior.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the host adapter abstraction and types — the foundation everything else builds on.

- [x] T001 Create HostAdapter interface and shared types in apps/web/src/services/host-adapter/host-adapter.ts
- [x] T002 [P] Create environment detection module in apps/web/src/services/host-adapter/detect.ts
- [x] T003 [P] Create WrightDesktopBridge type declarations in apps/web/src/services/host-adapter/wright-desktop.d.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Implement both adapter backends and the singleton export — MUST complete before user story work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Implement BrowserHostAdapter in apps/web/src/services/host-adapter/browser-adapter.ts
- [x] T005 Implement DesktopHostAdapter in apps/web/src/services/host-adapter/desktop-adapter.ts
- [x] T006 Create auto-detection singleton export in apps/web/src/services/host-adapter/index.ts
- [x] T007 [P] Write unit tests for environment detection in apps/web/tests/host-adapter/detect.spec.ts
- [x] T008 [P] Write unit tests for BrowserHostAdapter in apps/web/tests/host-adapter/browser-adapter.spec.ts
- [x] T009 [P] Write unit tests for DesktopHostAdapter (mocked bridge) in apps/web/tests/host-adapter/desktop-adapter.spec.ts

**Checkpoint**: Adapter layer complete — both adapters work, detection picks the right one, all tests pass.

---

## Phase 3: User Story 1 — Browser Standalone Experience Unchanged (Priority: P1) 🎯 MVP

**Goal**: Refactor existing services to use the adapter without changing any browser-mode behavior. All existing tests pass.

**Independent Test**: Run `npm run test --workspace=apps/web` — all existing Vitest tests pass. Run Vite dev server and confirm full UI works.

### Implementation for User Story 1

- [x] T010 [US1] Refactor api-client.ts to use hostAdapter.fetch() instead of raw fetch() in apps/web/src/services/api-client.ts
- [x] T011 [US1] Refactor App.tsx to use dynamic router (BrowserRouter/HashRouter) based on hostAdapter.getRouterType() in apps/web/src/App.tsx
- [x] T012 [US1] Refactor workspace-service.ts to use hostAdapter for file operations in apps/web/src/services/workspace-service.ts
- [x] T013 [US1] Run full existing test suite and fix any regressions from the refactoring
- [x] T014 [US1] Manual verification: start Vite dev server, exercise all pages, confirm zero behavioral changes

**Checkpoint**: All existing tests pass. Browser standalone experience is identical to before the refactoring.

---

## Phase 4: User Story 6 — Desktop Build Target (Priority: P1)

**Goal**: Produce an Electron-compatible `dist-desktop/` build with relative asset paths.

**Independent Test**: Run `npm run build:desktop`, then open `dist-desktop/index.html` via `file://` — all assets load without 404s.

### Implementation for User Story 6

- [x] T015 [P] [US6] Modify Vite config to support desktop build mode in apps/web/vite.config.ts
- [x] T016 [P] [US6] Add `build:desktop` npm script in apps/web/package.json
- [x] T017 [US6] Run `npm run build:desktop` and verify dist-desktop/ output has relative paths
- [x] T018 [US6] Verify standard `npm run build` output (dist/) is unchanged
- [x] T019 [US6] Add dist-desktop/ to .gitignore in .gitignore

**Checkpoint**: Both build targets work. Browser build unchanged, desktop build produces `file://`-compatible output.

---

## Phase 5: User Story 8 — Integration Package (Priority: P1)

**Goal**: Create the `hermes-wright-panel` npm package with preload script, panel manager, and TypeScript types.

**Independent Test**: Import `hermes-wright-panel` in a minimal Electron test and verify BrowserView loads and IPC channels respond.

### Implementation for User Story 8

- [x] T020 [US8] Create package.json for hermes-wright-panel/ with metadata and exports
- [x] T021 [US8] Implement preload.cjs with contextBridge exposing window.wrightDesktop in hermes-wright-panel/preload.cjs
- [x] T022 [US8] Implement WrightPanel class with BrowserView creation and IPC handler registration in hermes-wright-panel/panel.cjs
- [x] T023 [P] [US8] Implement wright:api IPC handler (HTTP proxy to Wright FastAPI) in hermes-wright-panel/panel.cjs
- [x] T024 [P] [US8] Implement wright:readFile, wright:writeFile, wright:listDirectory IPC handlers in hermes-wright-panel/panel.cjs
- [x] T025 [P] [US8] Implement wright:selectFiles IPC handler (native dialog.showOpenDialog) in hermes-wright-panel/panel.cjs
- [x] T026 [P] [US8] Implement wright:notify IPC handler (Electron Notification) in hermes-wright-panel/panel.cjs
- [x] T027 [US8] Implement wright:terminal:* IPC handlers (node-pty lifecycle) in hermes-wright-panel/panel.cjs
- [x] T028 [US8] Implement file path security validation (workspace root constraint) in hermes-wright-panel/panel.cjs
- [x] T029 [P] [US8] Create TypeScript declarations in hermes-wright-panel/types.d.ts
- [x] T030 [P] [US8] Write README.md with integration guide and minimal example in hermes-wright-panel/README.md

**Checkpoint**: Integration package complete with all IPC channels matching contracts/ipc-contract.md.

---

## Phase 6: User Story 2 — Wright Loads Inside Hermes Desktop (Priority: P1)

**Goal**: End-to-end: load Wright's desktop build in an Electron BrowserView with the integration package, and verify full workflow.

**Independent Test**: Load dist-desktop/index.html in a test Electron shell with preload → Wright detects desktop mode → API calls routed via IPC → UI renders and responds.

### Implementation for User Story 2

- [x] T031 [US2] Create a minimal Electron test harness script in hermes-wright-panel/test/electron-test.cjs
- [x] T032 [US2] Verify DesktopHostAdapter activates when window.wrightDesktop is detected
- [x] T033 [US2] Verify HashRouter is used in desktop mode (URLs show as #/path)
- [x] T034 [US2] Verify API calls proxy through IPC and reach the FastAPI backend
- [x] T035 [US2] Verify graceful error message when Wright FastAPI backend is not running
- [x] T036 [US2] Document the end-to-end test procedure in hermes-wright-panel/test/README.md

**Checkpoint**: Wright runs inside Electron with full API connectivity.

---

## Phase 7: User Story 3 — Native File Dialogs (Priority: P2)

**Goal**: File selection in desktop mode uses native OS file dialogs instead of the browser's `<input type="file">`.

**Independent Test**: In desktop mode, trigger file selection → native dialog opens → selected paths returned to Wright UI.

### Implementation for User Story 3

- [x] T037 [US3] Add selectFiles() method to DesktopHostAdapter using window.wrightDesktop.selectFiles() in apps/web/src/services/host-adapter/desktop-adapter.ts
- [x] T038 [US3] Add selectFiles() fallback to BrowserHostAdapter using HTML input element in apps/web/src/services/host-adapter/browser-adapter.ts
- [x] T039 [US3] Integrate selectFiles() into workspace-service.ts file upload flows in apps/web/src/services/workspace-service.ts
- [x] T040 [US3] Write unit test verifying adapter selection for file dialogs in apps/web/tests/host-adapter/select-files.spec.ts

**Checkpoint**: Native file dialogs work in desktop mode; browser mode uses standard file picker.

---

## Phase 8: User Story 5 — Direct Filesystem Access (Priority: P2)

**Goal**: Desktop mode uses direct Node.js filesystem access (via IPC) for file listing and reading, bypassing HTTP.

**Independent Test**: In desktop mode, navigate to workspace → file listing uses IPC (not HTTP) → file preview reads directly from disk.

### Implementation for User Story 5

- [x] T041 [P] [US5] Implement readFile() via IPC in DesktopHostAdapter in apps/web/src/services/host-adapter/desktop-adapter.ts
- [x] T042 [P] [US5] Implement listDirectory() via IPC in DesktopHostAdapter in apps/web/src/services/host-adapter/desktop-adapter.ts
- [x] T043 [US5] Update workspace-service.ts to use adapter readFile/listDirectory for file browser in apps/web/src/services/workspace-service.ts
- [x] T044 [US5] Write unit test for filesystem adapter methods with mocked bridge in apps/web/tests/host-adapter/filesystem.spec.ts

**Checkpoint**: File operations in desktop mode bypass HTTP and use direct filesystem access.

---

## Phase 9: User Story 4 — System Notifications (Priority: P2)

**Goal**: Long-running operations send native OS notifications in desktop mode.

**Independent Test**: Trigger a test notification → OS notification appears with correct title and body.

### Implementation for User Story 4

- [x] T045 [P] [US4] Implement notify() via IPC in DesktopHostAdapter in apps/web/src/services/host-adapter/desktop-adapter.ts
- [x] T046 [P] [US4] Implement notify() via browser Notification API in BrowserHostAdapter in apps/web/src/services/host-adapter/browser-adapter.ts
- [x] T047 [US4] Integrate notifications into long-running operations (e.g., agent tasks) in apps/web/src/services/agent-service.ts
- [x] T048 [US4] Write unit test for notification adapter methods in apps/web/tests/host-adapter/notifications.spec.ts

**Checkpoint**: Notifications work in both desktop (native OS) and browser (Notification API) modes.

---

## Phase 10: User Story 7 — Theme Synchronization (Priority: P3)

**Goal**: Wright auto-matches and live-syncs with the Hermes Desktop theme.

**Independent Test**: Change host theme → Wright UI updates without page reload.

### Implementation for User Story 7

- [x] T049 [US7] Create useDesktopIntegration hook in apps/web/src/hooks/useDesktopIntegration.ts
- [x] T050 [US7] Implement theme change listener via window.wrightDesktop.onThemeChange() in the hook
- [x] T051 [US7] Integrate hook into App.tsx to apply theme on mount and on change in apps/web/src/App.tsx
- [x] T052 [US7] Modify AppShell.tsx for titlebar overlay awareness (34px height) in desktop mode in apps/web/src/components/layout/AppShell.tsx
- [x] T053 [US7] Add CSS variable --titlebar-height and conditional sidebar behavior in apps/web/src/index.css

**Checkpoint**: Theme synchronization works. Desktop mode respects host theme and titlebar.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cleanup.

- [x] T054 [P] Update docs/dual-mode-desktop-integration.md with final implementation details
- [x] T055 [P] Update docs/deployment-configurations.md to add Hermes Desktop as 4th configuration
- [x] T056 Run full test suite (Vitest + Playwright) and verify zero regressions
- [x] T057 Run both build targets (dist/ and dist-desktop/) and verify output
- [x] T058 Run quickstart.md validation — follow the guide from scratch and verify it works
- [x] T059 Code review: verify no direct fetch() calls remain outside the adapter layer

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — refactors existing services
- **US6 (Phase 4)**: Depends on Phase 2 — can run in parallel with US1
- **US8 (Phase 5)**: Depends on Phase 2 — can run in parallel with US1 and US6
- **US2 (Phase 6)**: Depends on US1 + US6 + US8 (needs refactored services, desktop build, and integration package)
- **US3 (Phase 7)**: Depends on Phase 2 — can run in parallel with other P2 stories
- **US5 (Phase 8)**: Depends on Phase 2 — can run in parallel with US3, US4
- **US4 (Phase 9)**: Depends on Phase 2 — can run in parallel with US3, US5
- **US7 (Phase 10)**: Depends on US2 (needs desktop mode working end-to-end)
- **Polish (Phase 11)**: Depends on all user stories

### User Story Dependencies

- **US1 (P1)**: After Phase 2 — No cross-story dependencies
- **US6 (P1)**: After Phase 2 — Independent of US1
- **US8 (P1)**: After Phase 2 — Independent of US1, US6
- **US2 (P1)**: After US1 + US6 + US8 — Integration story, combines all P1 outputs
- **US3 (P2)**: After Phase 2 — Independent
- **US5 (P2)**: After Phase 2 — Independent
- **US4 (P2)**: After Phase 2 — Independent
- **US7 (P3)**: After US2 — Needs working desktop mode

### Within Each User Story

- Types/interfaces before implementations
- Adapter methods before service integration
- Core implementation before integration tests
- Story complete before moving to next priority

### Parallel Opportunities

- T002, T003 can run in parallel (Phase 1)
- T007, T008, T009 can run in parallel (Phase 2 tests)
- US1 (Phase 3), US6 (Phase 4), US8 (Phase 5) can run in parallel after Phase 2
- T015, T016 can run in parallel (Phase 4)
- T023, T024, T025, T026 can run in parallel (Phase 5 IPC handlers)
- T029, T030 can run in parallel (Phase 5 docs/types)
- US3, US4, US5 (Phases 7-9) can all run in parallel
- T054, T055 can run in parallel (Phase 11 docs)

---

## Parallel Example: After Foundational Phase

```bash
# Once Phase 2 completes, launch three workstreams in parallel:

# Workstream A: Refactor services (US1)
Task: T010 "Refactor api-client.ts"
Task: T011 "Refactor App.tsx"
Task: T012 "Refactor workspace-service.ts"

# Workstream B: Desktop build (US6)
Task: T015 "Modify Vite config"
Task: T016 "Add build:desktop script"

# Workstream C: Integration package (US8)
Task: T020 "Create package.json"
Task: T021 "Implement preload.cjs"
Task: T022 "Implement WrightPanel"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 6 + 8 + 2)

1. Complete Phase 1: Setup (adapter types)
2. Complete Phase 2: Foundational (adapter implementations)
3. Complete Phase 3: US1 — refactor services (browser still works)
4. Complete Phase 4: US6 — desktop build target
5. Complete Phase 5: US8 — integration package
6. Complete Phase 6: US2 — end-to-end desktop verification
7. **STOP and VALIDATE**: Wright works in both browser and Electron

### Incremental Delivery

1. Setup + Foundational → Adapter ready
2. Add US1 → Browser works with adapter → Deploy/Demo (refactored MVP!)
3. Add US6 + US8 → Desktop build + package exist → Can demo Electron loading
4. Add US2 → End-to-end verified → Full desktop integration!
5. Add US3 + US4 + US5 → Native capabilities enabled → Enhanced desktop UX
6. Add US7 → Theme sync → Polished experience

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Constraint: Zero modifications to NousResearch/hermes-agent code
