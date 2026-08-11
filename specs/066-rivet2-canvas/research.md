# Research: Modern Rivet Canvas Editor

## Decision 1: Pin Rivet 2 at one reviewed revision

**Decision**: Use `https://github.com/valerypopoff/rivet2.0` commit `4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053`; the pinned app package reports version 2.8.9.

**Rationale**: The repository is independently maintained from Ironclad Rivet and exposes the source-host seams needed by Wright. An exact revision makes the checked-in build and patch set reproducible.

**Alternatives considered**: Floating `main` or an npm range were rejected because the editor app is a private source package and floating inputs violate the offline/supply-chain contract.

## Decision 2: Retain iframe/process isolation

**Decision**: Build Rivet 2 as a separate React 18 application and serve it through the existing isolated retained surface.

**Rationale**: Wright uses React 19 and Vite 8 while Rivet 2 uses React 18 and Vite 6 with a large editor dependency graph. The separate build prevents React, Jotai, Atlaskit, Monaco, portal, and CSS collisions while preserving retained DOM behavior.

**Alternatives considered**: Importing Rivet source directly into `apps/web` was rejected because it would merge incompatible dependency and styling domains. Launching the desktop app was rejected because it would lose Wright workspace retention and policy.

## Decision 3: Use supported host lifecycle and workspace seams

**Decision**: Mount `RivetAppHost`, receive `onActiveProjectChanged`, `onOpenError`, and workspace-ready callbacks, and open/replace documents through `RivetWorkspaceHost`.

**Rationale**: Rivet 2 explicitly documents source embedding and exposes project open, replace, close, metadata, path, comparison, and clean-baseline operations. This replaces Wright's legacy file-picker, localStorage, and IndexedDB manipulation.

**Alternatives considered**: Continuing to seed editor-private atoms or browser storage was rejected as brittle and non-authoritative.

**Sources**:

- <https://github.com/valerypopoff/rivet2.0/blob/4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053/packages/app/src/host.tsx>
- <https://github.com/valerypopoff/rivet2.0/blob/4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053/packages/app/src/hooks/workspaceHost/types.ts>
- <https://github.com/valerypopoff/rivet2.0/blob/4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053/packages/app/src/providers/ProvidersContext.tsx>

## Decision 4: Add a bounded canvas-only upstream patch

**Decision**: Track and apply a small patch that extends `RivetAppHostUiConfig` with a canvas-only policy and conditionally omits non-canvas surfaces in `RivetApp`.

**Rationale**: The public UI config currently controls only file-menu items and desktop web-app preview. CSS selectors can hide some chrome, but they leave unrelated code and keyboard behavior mounted; the current Wright `MutationObserver` and text-label filtering have already proven fragile. A typed source policy is explicit and testable.

**Alternatives considered**: Pure CSS suppression was retained only as a layout supplement, not the authority for mounted features. Copying the full `RivetApp` component into Wright was rejected as a high-drift fork.

**Sources**:

- <https://github.com/valerypopoff/rivet2.0/blob/4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053/packages/app/src/providers/HostUiConfigContext.tsx>
- <https://github.com/valerypopoff/rivet2.0/blob/4f4a165a03f8da89c3d1cce2cb1a8c6eb6aa2053/packages/app/src/components/RivetApp.tsx>

## Decision 5: Preserve Wright's bridge envelope

**Decision**: Implement the existing `wright-rivet:set-project` and `wright-rivet:get-project` messages natively in the Rivet 2 wrapper, adding ready, acknowledgement, and structured error messages without changing Wright's workflow API.

**Rationale**: The current toolbar already loads and saves revision-aware workspace documents around that request/response model. Preserving it limits the replacement to the editor boundary and enables incremental tests.

**Alternatives considered**: Exposing workspace HTTP credentials directly to the frame was rejected because it would broaden authority and couple the editor to Wright routing.

## Decision 6: Build from source, ship only verified output

**Decision**: Source acquisition and Yarn installation occur only in the reproducible build workflow. Wright runtime packages contain the resulting checked-in `dist/`, the source/patch manifest, and no source checkout requirement.

**Rationale**: This matches Wright's existing native and Docker packaging model and keeps operation air-gapped.

**Alternatives considered**: Runtime clone/install and CDN delivery were rejected. A Git submodule was rejected because it would make production installation depend on fetching a 1.8 GB upstream repository.

## Decision 7: Use the companion server as integration evidence, not as a dependency

**Decision**: Follow the demonstrated pattern from Rivet Studio Server—separate iframe, `RivetAppHost`, provider overrides, and a typed message bridge—without importing its control plane or deployment stack.

**Rationale**: The companion project proves the host seams work in a browser wrapper and also shows that bounded wrapper overrides remain necessary for complete UI control.

**Sources**:

- <https://github.com/valerypopoff/Rivet-Studio-Server/blob/main-rivet2/wrapper/web/dashboard/HostedEditorApp.tsx>
- <https://github.com/valerypopoff/Rivet-Studio-Server/blob/main-rivet2/docs/editor-bridge.md>
- <https://github.com/valerypopoff/Rivet-Studio-Server/blob/main-rivet2/wrapper/web/vite.config.ts>
