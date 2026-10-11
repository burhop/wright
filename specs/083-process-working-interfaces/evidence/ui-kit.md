# T018 public UI kit evidence

Date: 2026-09-30, branch `codex/083-process-working-interfaces`.

## Implemented

`packages/ui_kit/` exports composable public React patterns for declared inputs,
image thumbnails, readiness/reasons, observations/freshness, exact results and
assessments, findings, declared checkpoints, permitted actions and navigation.
It owns the unchanged existing Wright token definitions; the native token file
imports that resource. No private `apps/web` import, process executor, provider
protocol, model call, review authority or browser job-state authority exists in
the package. The npm workspace/root lock adds only the local kit metadata/link.

Existing STL preview camera fitting is extracted to the public viewer with
bounded finite geometry, Z-up display mapping, theme-aware materials/background,
visible unsupported/invalid/WebGL fallback and scene/resource cleanup. The old
component path reexports it, retaining its public named/default exports. The
document-provider renderer remains in its existing owner; this does not replace
the workspace editor or its document lifecycle.

Neutral toolpath view data is bound to its exact package digest, with ordered
layers, finite coordinates and bounded segments. All supported layers have
orbit/zoom/reveal controls. Model/support filters require an explicit reader
classification method; legacy files lacking that evidence show unclassified
paths. No device envelope/protocol/profile or fabricated support geometry is
introduced. The view does not certify machine compatibility or support adequacy.

Bounded bitmap/STL/plaintext/CSV representations, paginated tables, numeric
profiles and sampled scalar fields are reusable. HTML/SVG is not embedded as
executable content. Numeric figures plot supplied finite samples and report
ranges/units without generating analysis or acceptance decisions. Unsupported
or oversized views disclose the limit and retain exact-file inspection fallback.

Input widgets preserve supplied false values and units, use actual configured
option/capability identities, and never materialize a schema default on mount.
Unsupported schemas remain explicit. Upload is a host callback returning an
ArtifactRef; replacing a file clears the prior binding. Object URLs are bound to
the current Blob, revoked on change/close, and not reused under a new title.

Actions require both backend permission and an explicit callback; checkpoint
actions match exact checkpoint and subject. A cancellation request is labelled
as a request. Idle observations expire without renewing their timestamp;
terminal percentages remain historical and do not advertise remaining time.
Empty findings and successful rendering do not imply engineering acceptance.

## Verification

Final focused frontend command, from `apps/web`:

```text
node ../../node_modules/vitest/vitest.mjs run src/components/common/ProcessUIKit.spec.tsx tests/ThreeDViewer.spec.tsx src/services/process-client.spec.ts vite.config.spec.ts
```

**94 passed**, four files, 2.65 seconds: 30 kit checks, four geometry lifecycle/
layer checks, 45 client checks and 15 configuration/proxy/license checks.
Geometry renderer tests use an explicitly mocked WebGL renderer; actual geometry
objects, visibility, controls and disposal are exercised. They are not a browser
GPU, engineering, live-provider or real-package proof.

From the repository:

```text
node apps/web/node_modules/typescript/bin/tsc -p packages/ui_kit/tsconfig.json
node apps/web/node_modules/typescript/bin/tsc -p packages/process_client/tsconfig.json
node apps/web/node_modules/typescript/bin/tsc -p apps/web/tsconfig.app.json --noEmit
.venv/Scripts/python.exe -m pytest packages/core/tests/test_process_client_contracts.py packages/core/tests/test_process_interface_contracts.py --basetemp C:/Users/markb/.codex/visualizations/2026/09/24/01a0d4b8-b5fa-79d0-8e8b-fc78c3dfd056/process-interfaces-083-tests/t018-contracts -q -p no:cacheprovider
```

Both public-package and whole-app type checks pass. **54 Python checks pass** in
1.60 seconds. Actual owning schemas remain unchanged. A discovered tagged-union
gap was fixed in the public validator: the owning Pydantic discriminator is
required even though an individual defaulted field may appear optional in its
JSON schema. The additional negative fixture passes.

The final production build also passed:

```text
npm run build --workspace apps/web -- --outDir D:/repos/wright/.local-run/process-interfaces-083/t018-web-dist-final
```

TypeScript and Vite completed with exit 0; Vite transformed 908 modules in
1.78 seconds. The fresh output includes `third-party-licenses-web.txt`
(236,029 bytes). Existing bundle-size warnings remain. This establishes bundle
compilation, not a served common working view or browser acceptance.

The owning token file was compared to its pre-extraction HEAD bytes normalized
to LF: the public copy is identical. Protected campaign hashes, current feature
pointer, ten original prototype file hashes and startup/router deltas remain
preserved. Public package sources were checked for private imports.

## Observed corrections and limits

- Initial red kit tests confirmed that the package implementation was absent.
- The standalone package type check initially lacked a CSS module declaration;
  the public package now declares its bundled stylesheet imports.
- The prior viewer fixture supplied an eight-byte empty model. It now supplies
  bounded triangle geometry to the mocked loader, and a separate negative test
  proves the eight-byte representation yields an explicit fallback rather than
  a claimed rendered model. Layer visibility and renderer disposal are verified.
- One formatter invocation used the app directory with a root-relative tool
  path. Corrected that command; the final formatting/type/test results above
  supersede it. No failed command is treated as successful evidence.
- The existing Node 25.2.0/jsdom engine warning remains recorded; these checks
  prove this host only. Supported installed native/Docker proofs are later tasks.
- The build uses a fresh owned output directory, preserving existing served
  files. Production compile/bundle proof is separate from served-workspace proof.

Native/common view, exact representation/assessment host wiring, actual theme
handshake, actual browser/responsive/accessibility checks and default-model/
engineering/distribution demonstrations remain later tasks. No service was
restarted, protected subject resumed, provider/model called, physical action
sent or remote change published during this milestone.
