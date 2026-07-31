# User Story 2 green evidence: panel and browser presentation

**Recorded**: 2026-07-30
**Scope**: T055-T073

## Outcome

A declared ready live application can now be presented in the Wright panel,
the system browser, or both. Shareable presentations retain one instance and
generation; isolated presentations require explicit acknowledgement. Backend
issued URLs are absolute, distinct-origin, short-lived bootstrap URLs with the
raw token only in the fragment. Scoped idempotent replay rotates that token,
and closing one presentation does not stop the underlying application.

The user can remember a panel or browser default per user, workspace, and
immutable source identity. Every read revalidates source version, current
instance, lifecycle, and eligibility, with browser-first safe fallback and a
plain-language reason. Persisted frontend tabs contain no presentation token
and remain inert until server reconciliation; a service outage never exposes a
persisted `ready` snapshot as current authority.

The browser and Electron host adapters validate issued preview URLs and guarded
external navigation. Electron denies renderer navigation/window creation,
keeps child frames away from the preload bridge, and accepts only configured
preview subdomains or explicitly allowlisted direct origins. The panel uses a
restricted iframe, preserves stateful inactive hosts within a bounded LRU deck,
reports framing uncertainty truthfully, and keeps browser fallback available.

## Automated evidence

- Python service/API/migration/composition/schema/fixture gate: **22 passed**.
  This includes an upgrade from immutable migration 6 to migration 7, where
  legacy presentation authority is expired and its bootstrap hash cleared.
- Ruff across all scoped Python implementation and tests: **passed**.
- Web Vitest gate: **6 files, 34 tests passed**.
- Web ESLint gate: **passed**.
- Production TypeScript/Vite build: **passed**. Plotly remains a separate lazy
  local chunk; Vite's existing advisory for chunks over 500 kB is informational.
- Electron host security gate: **3 passed**.
- Chromium mocked journeys: **5 passed**, covering shared panel/browser state,
  remembered choice, close-versus-stop, safe browser-open failure, CSP/XFO
  framing refusal, stale restore, reload, and reconciliation outage.
- Deterministic shareable-app fixture: manifest schema and real shared HTTP
  counter smoke tests both passed without a production process manager.

The only Python warning is the repository's pre-existing Starlette `httpx`
compatibility deprecation.

## Red-to-green defects closed

- The initial implementation modified committed migration 6. It now leaves
  migration 6 byte-for-byte immutable and uses contiguous migration 7 with a
  fail-closed authority upgrade.
- `window.open(..., "noopener")` can return `null` even after opening a page,
  which made Wright report false browser failures. Wright now opens a blank
  same-origin window, severs `opener`, installs `no-referrer`, and only then
  navigates to the validated URL, retaining reliable popup-block detection.
- Restored local state could render briefly before server reconciliation and
  could survive a reconciliation outage. Restored surfaces now remain behind a
  truthful restore status until the scoped server list succeeds.
- A stale instance-generation update could leave an old iframe mounted. The
  presenter now disposes it and clears stale local presentation state exactly
  once.
- The retained-deck test initially queried an `aria-hidden` panel by accessible
  name; browsers correctly remove that name from the accessibility tree. The
  assertion now verifies the retained DOM node and its hidden semantics.
- TypeScript found an unused presenter container field; it was removed before
  the production build passed.

The Electron assertions were test-authored first, but their separate failing
runner output was not retained before the initial green execution. This
test-first evidence limitation is recorded rather than rewritten as a red run.
See [us2-red.md](us2-red.md) for the observed failing state.
