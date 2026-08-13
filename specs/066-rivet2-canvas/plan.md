# Implementation Plan: Modern Rivet Canvas Editor

**Branch**: `066-rivet2-canvas` | **Date**: 2026-08-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/066-rivet2-canvas/spec.md`

## Summary

Replace the checked-in Rivet 1.25.0 editor bundle and browser-state compatibility shim with an offline build of Rivet 2 pinned at commit `4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053` (`@valerypopoff/rivet-app` 2.8.9). Build a Wright-specific hosted entry from Rivet's supported `RivetAppHost` and `RivetWorkspaceHost` seams, add a small reviewed canvas-only source patch, and keep the result inside the existing isolated retained surface. Wright continues to own workflow selection, revision-aware persistence, linting, execution, the streamlined surrounding toolbar, and a packaged template catalog that instantiates fresh workspace projects offline.

## Technical Context

**Language/Version**: Python 3.11; TypeScript 5.7+; upstream Rivet Node 20.x/Yarn 4.17.1 build toolchain

**Primary Dependencies**: FastAPI workspace APIs; React 19 Wright shell; isolated React 18 Rivet 2 hosted build; `@valerypopoff/rivet2-core`; `@valerypopoff/rivet-app`; existing workspace surface supervisor

**Storage**: Existing workspace-authored `.rivet-project` files and dataset payloads; no new durable store

**Testing**: pytest; Vitest/Testing Library; Node artifact and offline tests; Playwright retained-surface acceptance coverage

**Target Platform**: Wright native packages on Linux, macOS, and Windows plus Docker; browser-hosted retained surface on loopback origin

**Project Type**: Modular monorepo web application with a separately built embedded editor artifact

**Performance Goals**: Canvas interactive within 5 seconds on the packaged test host; no additional runtime process beyond the existing bounded static editor host

**Constraints**: Offline-first; exact upstream pin and checksums; no runtime source checkout or npm download; no React 18 packages imported into Wright's React 19 bundle; no DOM text matching or mutation observer used to shape the editor UI; Wright remains authoritative for saves and execution

**Scale/Scope**: One retained editor session per declared workspace surface; current workflow catalog scale and project format fixtures; editor replacement only

## Constitution Check

*GATE: Passed before research and re-checked after design.*

| Principle | Design evidence |
|---|---|
| Modular/API thinness | The existing workspace workflow and surface services remain authoritative; no route gains editor business logic. |
| Offline-first | An exact upstream source revision is built ahead of packaging, all remote asset references are removed, and the verified `dist/` is checked into the product artifact. |
| Production distribution | Native and Docker packages consume the same checked-in editor artifact and retain existing package/lifecycle gates. |
| Native runtime isolation | Rivet remains a separately built, isolated browser application served by the Wright runtime; it is not imported into an agent manager or Wright's React bundle. |
| Embedded storage | Workspace files remain authoritative; no server database or editor-private project catalog is introduced. |
| UI layering and test pyramid | Wright toolbar changes retain token usage and test IDs; component, UI integration, and lifecycle/offline tests are included. |
| Security and identity | The editor receives only the already scoped workflow bridge; the surface retains isolated sharing, loopback hosting, origin validation, and no tool/secret capability. |
| Phase isolation | Planning artifacts require operator approval before the implementation tasks are executed. |

Post-design re-check: the bridge and artifact contracts preserve the same authority, isolation, offline, and packaging boundaries. No constitutional exception is required.

## Project Structure

### Documentation (this feature)

```text
specs/066-rivet2-canvas/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── editor-bridge.md
│   └── editor-artifact.md
└── tasks.md
```

### Source Code (repository root)

```text
integrations/rivet/
├── editor/
│   ├── dist/                         # replaced checked-in Rivet 2 hosted build
│   ├── patches/                      # reviewed canvas-only/source-host patch
│   ├── wrapper/                      # Wright bridge and hosted entry sources
│   ├── host.py                       # static loopback host without DOM injection
│   └── manifest.json                 # source revision, app version, patch and dist integrity
└── spike/
    ├── baseline/baseline.json        # Rivet 2 source/package baseline
    ├── scripts/                      # reproducible acquire/build/inventory tooling
    └── tests/                        # checksum, offline, reproducibility tests

apps/web/src/
├── components/surfaces/
│   ├── DirectRivetSurface.tsx
│   └── DirectRivetSurface.spec.tsx
└── services/
    └── rivet-editor.ts

packages/workspace_service/tests/
└── test_rivet_editor_host.py

tests/ui-integration/
└── test_rivet2_canvas_surface.py     # or existing equivalent Playwright suite
```

**Structure Decision**: Preserve the existing isolated editor surface and Wright toolbar. Replace only its verified artifact and bridge implementation. The Rivet 2 build remains a separate React 18 compilation under `integrations/rivet`, avoiding dependency and CSS collisions with Wright's React 19 frontend.

## Implementation Design

1. Update the compatibility baseline from Ironclad Rivet 1.25.0 to `valerypopoff/rivet2.0` at the exact reviewed commit and replace package metadata with the 2.x package names.
2. Add a reproducible hosted build that starts from the pinned source, applies Wright-owned patches, mounts `RivetAppHost`, imports `host.css`, removes network-backed fonts/assets, and emits the checked-in `dist/`.
3. Add a narrow `canvasOnly` host UI policy upstream through the tracked patch. In this mode `RivetApp` renders `GraphBuilder` and required graph-authoring overlays while omitting `ProjectSelector`, `LeftSidebar`, `ActionBar`, `StatusBar`, settings/help, Prompt Designer, Trivet, Chat Viewer, Data Studio, Node Library, and Web App builder entry surfaces. The patch includes an upstream-style unit/source contract test.
4. Implement a wrapper bridge using `RivetWorkspaceHost` plus Rivet core serialization. Preserve the existing Wright `postMessage` envelope for opening and requesting the active project, add readiness/error acknowledgements, validate `event.origin`, and reject stale request IDs.
5. Simplify `host.py` to static hosting, health, SPA fallback, and security headers. Remove the file-picker shim, IndexedDB seeding, CSS label filters, and `MutationObserver` chrome removal.
6. Keep Wright's `DirectRivetSurface` toolbar and workspace service calls. Gate project transmission on editor readiness and surface bridge errors in the existing status element.
7. Replace the checked-in bundle and manifest, prove no 1.25.0 executable fallback remains, and validate offline/native/Docker packaging.
8. Package a curated template catalog with provenance, expose thin list/instantiate APIs, regenerate Rivet identities per creation, and reduce the canvas toolbar to blank, template, save, lint, run, and browser actions.

## Verification and Rollback

- Unit/contract: bridge origin/request correlation, serialization round trip, canvas-only allowlist, readiness, unavailable artifact, and exact manifest identity.
- UI integration: only graph-authoring UI is visible; node add/edit/connect/delete works; Wright create/open/save/lint/run controls remain usable.
- Lifecycle: hide/reopen retention, stop/restart, workspace isolation, revision conflict, missing artifact, and no legacy fallback.
- Offline/package: deny network during startup and interaction; scan generated HTML/CSS/JS for remote assets and legacy version references; verify artifact checksum in native and Docker package layouts.
- Rollback before release: revert the feature commit and keep the prior product release. Do not retain Rivet 1.25.0 as a runtime fallback inside the new package.

## Complexity Tracking

No constitutional violations require justification. The tracked upstream patch is bounded to the host UI policy and hosted entry contract because Rivet 2's public `ui` configuration does not yet expose full chrome suppression.
