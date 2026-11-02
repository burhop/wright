# Current produced evidence first in reviews

Date: 2026-10-23. Scope: T009 backend presentation ordering, controlled tests and
a read-only projection of retained evidence. Installed UI re-verification after
the next coordinated candidate build remains pending.

The installed geometry review showed four original concept/context files first,
with its actual preview farther down in Results. The shared approval projection
previously sorted every exact reference alphabetically. It now presents matching
current-run produced representations before static references. Supported image
formats from the existing viewer map come first among produced files, so visual
review can begin with the actual geometry preview or analysis plot.

Promotion requires an exact retained `workspace_file` representation matching
both path and SHA-256, the checkpoint's run identity in both continuation and
result provenance, and no explicit conflicting result definition digest. Named
exports retain their own provenance checks. Unknown or malformed optional result
metadata does not promote references. No filename prefix, extension guess,
example-specific branch, prompt text or successful tool-call claim supplies
identity. File opening and engineering acceptance retain their existing owners.

All original deduplicated path/digest pairs remain present. Ordering adds no
result ID, representation ID or read/approval authority. The existing
`PAGE_ITEMS` overflow refusal remains; the list is never silently truncated.

Verification:

- Owning interaction projection suite: **25 passed in 1.78 s**. It includes the
  concrete thermal comparison: formerly four static references led; now the
  exact produced temperature plot precedes the temperature table and static
  concept, with every reference unchanged. Controls cover stale run/source,
  path/hash mismatch, non-file representations, missing hashes, named exports,
  duplicate paths with different revisions and the existing size limit.
- After a conservative optional-metadata guard, only its three added cases were
  run: **3 passed in 0.17 s**, giving **28 unique tests**. The guard preserves the
  original reference inventory when optional result metadata is unusable.
- Focused Ruff and tracked diff checks passed. Tests use temporary controlled
  data and no model/provider calls. The owning asynchronous suite ran outside the
  sandbox because of the previously established executor wakeup limitation.

The retained handle checkpoint was also projected locally without contacting or
mutating the native service. All 13 exact references remain; `mesh-preview.png`
now leads, followed by `geometry-basis.json`, `mesh-repair-report.json` and
`repaired_mesh.stl`. Full before/after identities and the input run-record hash
are retained in
`artifacts/first-contact/084/review-evidence-ordering-001/retained-handle-projection.json`.
This is projection evidence, not a new engineering result or installed screenshot.

Owned code: `process_interfaces/owners.py` and
`tests/test_process_interaction_owners.py` under `packages/workspace_service`.
No frontend, execution policy, source, review decision, native build or runtime
update was changed by this subtask.
