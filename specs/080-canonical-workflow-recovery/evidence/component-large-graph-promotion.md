# T055 component and large-graph behavior evidence

**Date**: 2026-09-01

**Exact implementation subject**: commit `f7cc7273d92e1d9d4b5d1e383a67c763cdc2e99d` / tree `802b9d2522e819b3a8b6578cdb1fe56487e23a75`

**Scope**: renderer-neutral component projection/validation plus approved React Flow collapse, expansion, identity navigation, and bounded large-graph behavior. No semantic mutation, definition/layout/run persistence change, external execution, benchmark qualification, push, merge, publication, release, or customer action.

## Verified behavior

- Reusable component definitions project stable identity, version, reviewed boundary ports, internal-definition digest, and non-empty internal semantic addresses through the production renderer seam.
- Internal addresses fail closed when their component scope, collection-root path, uniqueness, digest, or component reference is invalid.
- A collapsed instance retains the exact scope tuple `(component_instance_id, component_id, component_version, internal_semantic_id)` for diagnostics and immutable run lineage.
- The collapsed card displays the number of stable internal addresses and any active internal target. Expansion reveals the address list without changing the accepted workflow revision or semantic digest.
- Stable-ID/title search selects and centers a block through the host-owned selection intent. No renderer-native identity or semantic write is introduced.
- Graphs through 25 blocks keep detailed cards. Graphs above 25 use deterministic compact presentation while retaining all 100 stable nodes, minimap, fit, selection, and identity search.
- Component geometry exposed a real overlapping-edge-label failure in the first complete Chromium run. The renderer now assigns deterministic presentation-only label lanes; the relationship remains clickable without a forced test action.

## Failed-first and repair evidence

The first renderer contract run failed exactly two new assertions because component collapse and compact large-graph mode did not yet exist (`2 failed, 4 passed`). After implementation, the focused renderer/projection/composer suite passed `29/29`.

The first complete Chromium run after implementation passed five tests and failed the typed-handle journey because two edge labels overlapped after component card geometry changed. The first repair exposed an empty second status region; that was corrected rather than weakening the existing assertion. The exact final suite passed `6/6` in 13.7 seconds. The exact sequence is retained in [t055-chromium-repair.md](t055-chromium-repair.md).

## Final validation

```text
Vitest focused projection/component/renderer/composer: 29 passed
Vitest complete web suite: 114 files, 524 tests passed
Playwright Chromium recovery suite: 6 passed
TypeScript/Vite production build: passed
ESLint: 0 errors; 3 pre-existing hook warnings outside this change
git diff --check: passed
frozen spec 079 tasks diff from b4a7e996: empty
```

The 100-block Vitest renderer observation is bounded automated behavior evidence, not a production performance benchmark. It does not change CAP-026's separate representative performance qualification or the independent engineering benchmark, which remains `0/100`.

The refreshed dashboard verifier passed at `2026-09-01T04:40:01.802Z` with
55/60 recovery tasks, visible T055 component/large-graph status, the exact
approved product subject, eight loaded evidence images, zero browser
diagnostics, zero desktop/mobile overflow, evidence HTTP checks at 200,
traversal checks at 403, and customer readiness still false.
