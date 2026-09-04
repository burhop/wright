# Native process authoring

The official Wright process language is the semantic document. The canvas is an adapter: it projects stable step and port IDs, emits commands, and stores positions separately. It does not introduce hidden operation state, a Rivet serializer or an independent execution model.

The service's `/api/native-processes/contract` supplies the same schema and operation descriptors used by native backend validation. Forms derive configuration fields and exact port signatures from that discovery response. `model.ts` gives immediate atomic structural feedback against the published schema and retains complete undo entries. The backend remains authoritative for check/save/run semantics. Frozen language fixtures verify frontend conformance; they are not AI-generated study evidence.

The Inspector retains unapplied fields outside the semantic document. Applying a valid form updates the document once; invalid values remain editable without corrupting it. Explicit empty text remains distinguishable from missing configuration. Deleting a step previews affected ports, connections and output declarations and supports complete undo.

Save uses an opaque expected token and a request ID retained across ambiguous retries. The client submits only definition/presentation, never response metadata. A stale writer keeps its draft and can load the current version after confirmation or create a separately identified copy. A saved idempotent replay is compared with current service state. Tab recovery is scoped by session and preserves unapplied fields; it makes no durability claim when browser storage rejects the checkpoint.

Workspace selection uses existing authoritative workspace discovery. Changing workspace or following a link with unsaved changes offers a keyboard-trapped confirmation. Browser close/refresh uses the native before-unload warning; back navigation preserves the tab recovery draft.

## Renderer and dependency review

`@xyflow/react` is pinned to **12.11.6** (MIT), with React 19-compatible peer ranges. Installed package integrity:

```text
sha512-9XsEJNHjatKYndszKTF/bsU7FOP9dJ6V/EQwzy3oMdtqgBuUq7BjKSwkEo+C7s4qHstHQfwwoHA3E8QfpPxZZQ==
```

The workspace root `package-lock.json` is authoritative. The installation added 20 locked package entries, including `@xyflow/system` 0.0.82, D3 interaction helpers and Zustand. No existing resolved package version changed. Existing Linux libc selectors were preserved after npm 11.6 removed that metadata during regeneration.

The native page loads as a separate route chunk. The authoring checkpoint produced approximately 215 kB minified / 69 kB gzip native JavaScript and 21.6 kB / 3.85 kB gzip native CSS. With run inspection, the measured chunk is 231.85 kB / 73.46 kB gzip JavaScript and 22.64 kB / 3.98 kB gzip CSS. The existing main/Plotly chunk-size warning remains. Renderer colors, focus states and controls are adapted through Wright design tokens. Keyboard/click port controls expose exact identities alongside pointer drag handles.

The September 4 npm audit reported four pre-existing package findings: browserslist (high), fast-uri (high), DOMPurify 3.4.12 (moderate), and qs (moderate). None identified the renderer or its added dependency tree. This is an open repository quality concern, not a clean audit claim. Node 25.2.0 emitted the existing jsdom 30 engine warning; focused tests and production build nevertheless ran successfully on this host.

## Verification and delivery boundary

Focused Vitest coverage checks strict canonical UTF-8 vectors/rejections, exact decimal limits, descriptor ports, invalid edits, endpoints, deletion/undo, layout independence, empty input preservation, mocked authoring/save/reopen/conflict/recovery and traced client envelopes. Mocked component tests replace the canvas and identify themselves accordingly.

`tests/ui-integration/native-process.spec.ts` uses actual Chromium and React Flow with an explicitly simulated service. It verifies keyboard creation/connections, programmatic IDs, save/reopen, selection and keyboard layout movement, deletion/undo, stale writes, modal focus, axe, narrow layout and 200% zoom. It records 20 warm opens of a 25-step fixture; timings include automation overhead and are diagnostic.

Original findings were corrected before the authoring checkpoint: a decimal boundary rounded by JavaScript Number, response-only metadata leaking through structural object typing, loss of explicit empty text on form apply, an invalid ARIA label on decorative renderer handles, and initial/new-layout fitting. Browser setup also required the correct existing authentication status endpoint and host-authorized Chromium launch.

The subsequent run-inspection increment uses frozen native DTOs for immutable saved snapshots, step inputs/outputs, actual failures, trace events, cancellation, reconnect and a new corrected run linked to its predecessor. Exact MCP tool choices stay outside semantic definitions; readiness and run submission receive the same binding selections, and changed schemas require rebinding. Neither canvas edits nor a refreshed inspection mutate a prior run.

Artifact inspection streams at most the recorded size and 10 MiB, then compares SHA-256 against both the run index and response header before exposing any preview/download. The text preview is bounded to 64 KiB. Downloads use an inert binary MIME type, while the UI shows the actual recorded media type. No prompt or source code is invented for a deterministic operation. Run and artifact DTOs retain their actual failure/state labels, including earlier completed artifacts within a failed run.

Six mocked component checks cover failure/provenance boundaries, dirty-version gating, ambiguous linked-run retry, cancellation, reconnect, altered artifacts and changed bindings. Three additional real Chromium journeys against a simulated runtime exercise failure/correction/linked rerun, SHA-256 verification of actually downloaded fixture bytes, deliberate byte tampering, reconnect and cancellation. Automated run-panel accessibility checks are included. These are explicitly simulated runtime results, not proof of backend execution or a real MCP invocation.

Actual backend/browser round trips, runtime/artifact parity, human participants, packaged/native/Docker verification, independent exact-candidate review and dev deployment remain milestone work. Readiness responses and declared outputs are never displayed as successful execution evidence.

Local verification on September 4: **42 focused Vitest checks and 8 Chromium journeys passed**, targeted ESLint and the production TypeScript/Vite build passed, and `git diff --check` passed. Browser evidence uses a simulated service/runtime and actual browser rendering/crypto/downloads; it must not be credited as actual backend execution. The retained local output directory is `test-results/native-editor-run-final/`, including screenshots and 20 raw warm-open timing observations.
