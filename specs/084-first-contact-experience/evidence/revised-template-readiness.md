# Accepted starter revision: readiness transition

The source-readiness endpoint now distinguishes an accepted revision from the
unchanged supplied starter using the backend lineage helper and the exact current
source read. It retains the original template ID, version and source/layout
digests, and exposes the current accepted digest and definition revision
separately. A revised source has unknown qualification flags, not inherited
`ready` or `verified` status. Unchanged, reverted and legacy origins retain their
existing catalog setup gate.

The editor labels this state **Revised · preflight required** and permits its
existing Run path. The existing backend preflight still decides whether a run may
start; this change supplies no grant and adds no executor or status owner.

Focused verification:

- API: six lineage cases passed (unchanged, revised, revision-one mismatch,
  reverted, legacy and malformed origin); 22 unrelated cases deselected.
- Editor: two targeted cases passed, including exact accepted-digest dispatch and
  propagation of a backend readiness rejection; 55 unrelated cases skipped.
- TypeScript build, Ruff and changed-file whitespace checks passed.
- Served Chromium workspace scenario passed: unchanged starter blocks before a
  start request; applying and saving an edit exposes revised status; Run reaches
  the ordinary backend route, whose controlled rejection remains visible. No
  live model/provider was used and no run was created.

The served scenario uses controlled HTTP responses and therefore proves client
integration, not live engineering qualification. Its screenshot was visually
checked at
`artifacts/first-contact/084/revised-template-preflight-final/revised-template-readiness-887a7--retaining-template-lineage-chromium/revised-template-preflight.png`.
An earlier test attempt omitted the editor's Enter-to-apply action and correctly
left Save disabled; the corrected test uses the existing interaction. The
original failure artifact remains under `revised-template-preflight/`.
