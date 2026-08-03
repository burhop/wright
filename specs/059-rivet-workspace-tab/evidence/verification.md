# Verification

- `vitest` feature-flag test: passed.
- Web lint: passed with one pre-existing `ModelSetupPage` hook dependency warning.
- The tab is default-off and describes the missing verified editor bundle rather
than embedding or downloading Rivet.

## Rollback

Set `VITE_RIVET_WORKFLOWS_TAB_ENABLED=0`; the navigation entry disappears and
no workspace files, grants, or surface instances are changed.

## Limitation

The real retained Rivet host remains unavailable until the local manifest has a
verified offline editor asset. Existing `SurfaceDeck` is the sole retained-host
owner; this slice adds no alternate iframe or React import path.
