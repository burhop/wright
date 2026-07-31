# User Story 5 Red Baseline

Recorded: 2026-07-30

## Manifest contract

Command:

```text
uv run pytest tests/contract/workspace_surfaces/test_live_app_manifest.py -q
```

Expected result: **failed** before implementation.

- Collection failed because `core.surfaces.live_app_manifest` did not exist.
- After the initial implementation landed, 14 of 15 tests passed and the remaining
  test proved that unsupported command placeholders could be masked by unavailable
  secret references. Validation was reordered so malformed declarations now fail
  deterministically before secret-store lookup.

This baseline demonstrates that the immutable manifest model, documented-only
interpolation, no-shell command boundary, ownership rules, exact lifetime semantics,
and complete runtime/proxy policy projection were absent from the prior runtime.
