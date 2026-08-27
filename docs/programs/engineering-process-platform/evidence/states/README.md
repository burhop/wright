# Program state history

`program-state.json` is the current snapshot. This directory preserves each accepted prior revision so transitions can verify compare-and-swap history without relying on Git archaeology.

- Revision 1 is the genesis `PLAN_DRAFT` snapshot and has `last_transition: null`.
- Every later revision names the transition that produced it.
- Transition records live in `../transitions/` and bind both canonical state digests and raw state-file SHA-256 values.
- Canonical state digests use `wright-json-c14n-v1-sha256` as defined in `coordinator-state-machine.md`.
- Archived state bytes are immutable even when a later append-only correction identifies a factual field defect. A correction record never changes a historical canonical/raw digest, creates a virtual state, or rewrites a pointer; validators retain the original finding and separately derive its approved disposition.

Snapshots and transitions are append-only after acceptance. Corrections create a new revision; they do not rewrite history.
