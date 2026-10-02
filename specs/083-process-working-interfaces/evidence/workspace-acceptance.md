# Workspace acceptance evidence

## Process tab controls, 2 October 2026

Branch: `codex/083-process-working-interfaces`; served UI `http://127.0.0.1:5243`,
normal API `http://127.0.0.1:8030`, isolated workspace `083-heat-live-005`.
Workflow recovery/composer/process-definition flags are enabled by the owned
`t047-web-isolated-cache.mjs` host. The existing wheel second run remains at its
unanswered declared review; the browser does not start or approve work.

The process workspace navigation was using recovery-editor button classes outside
their styling context. Managed embedded-view controls also lacked scoped spacing
and styles. `process-workspace.css` now styles those host controls using existing
Wright tokens with fallbacks, without changing generated source, runtime actions
or ordinary provider surface controls. Interface controls expose a named group;
the authoring disclosure exposes its expanded state.

Served browser evidence:
`artifacts/process-interfaces/083/20261002-workspace-process-controls/`.
Five checks pass: normal workspace Workflows entry, established editor file
controls, and saved working-interface controls at 1440, 1024 and 480 pixels.
Actual measurements verify 44px navigation/view buttons, 1px borders, no outer
horizontal overflow and a 3px focus outline after Tab from Open workflow to
Create or choose interface. Raw and annotated screenshots are retained separately.
S05 was visually inspected and confirms wrapping and spaced controls at 480px.
The walkthrough validator passes and public local artifacts were scanned for
credential values; the authenticated trace remains private.

Focused regression command, from `apps/web`:

```text
node ../../node_modules/vitest/vitest.mjs run src/components/process-interfaces/ProcessWorkspaceTab.spec.tsx src/components/process-interfaces/ProcessInterfaceView.spec.tsx src/components/surfaces/LiveAppSurface.spec.tsx --reporter=dot
```

All 22 tests pass, covering scoped host callbacks, authoring disclosure, existing
presentation lifetime and ordinary surface behavior. Component tests do not
establish CSS layout; the browser measurements provide that separate evidence.

T052 remains pending: these checks do not cover complete editor manipulation,
preview parity, real browser zoom, all accessibility paths, both process journeys
or installed distribution. No human product or engineering acceptance is claimed.
