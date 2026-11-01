# Installed handle geometry review and reopen

Date: 2026-10-23. This is an actual installed Chromium capture against the owned
native candidate at `http://wright.localhost:18084`, using the normal loopback
cookie. It records a pending digital geometry review, not engineering acceptance,
support qualification, a physical print or a completed workflow.

The capture opens the source in the normal workspace workflow editor and uses
**Open working view**. It then follows the exact saved run's normal workspace
process link, inspects the pending review, follows **Open interaction step** to
the exact block inspector, and opens `mesh-preview.png` from its recorded result
in Wright's common working-view file reader. Closing and reopening that same
view restores the same pending checkpoint without submitting a decision.

Exact subjects:

- Workspace `7e720c97-6048-4a50-944f-2376186db36b`;
  source `workflows/replacement-drawer-handle.workflow.wflow`, storage revision 5,
  SHA-256 `9cd2acc8b36df3abea002a9e62b3171a8df0fc1b5c327eb35bdd20e047caeaef`.
- Run `3735dcf5678847219bc88ca2c80cedc8`; checkpoint
  `checkpoint-5ae08ffa9e4b881c120b8416`; step
  `review_geometry_before_slice_printed_handle_084_section`.
- Checkpoint subject
  `3d310462ea799bb4c9f8e0512fdbaf02f0871114abfb01efe44d3c7ad9f4d11f`;
  input snapshot `inputs-062c2793115942ddb976b1c4a50b7d45`, digest
  `c4aed04db58c46939e16d54a51588771848857c67fc5b11086d10451557b51b0`.
- Preview under
  `process-proofs/printed-replacement-part/printed-handle-084-section/outputs/3735dcf5678847219bc88ca2c80cedc8/mesh-preview.png`:
  601259 bytes, 1280 × 720 pixels, SHA-256
  `4462b03bdabec4123cd21816ff64ad0f99930ff13a203acc00b28b18eb9bf3f5`.
  Recorded reference, actual file and representation response hashes agree.

The durable run remains `awaiting_approval` with 34 events and the pending
checkpoint. Its complete record hash is unchanged before/after the capture:
`6c20eb33c933c8fb090c350b1955dada9e3bc6d1b494e87dcb8def94ecd0c9f0`.
Non-GET traffic consists only of workspace activation and the existing read-only
navigation/representation endpoints. No run start, decision, resume, input
preparation, engineering-tool call or native update was requested.

Evidence is in `artifacts/first-contact/084/native-handle-geometry-review-011/`.
`report-002.json` is the passing attempt; `capture-002.mjs` is its exact harness.
Screenshots 03, 04, 06 and 07 were visually inspected for the review, exact block,
actual rendered geometry preview, and reopened wait respectively. `media.json`
records the retained local video's path, hash and metadata. Two working-view
tabs can coexist; this is not evidence of two runs.

The initial `report.json` failure is retained: its capture script used the wrong
source-read query key (`workflow_path` instead of `path`). The unchanged backend
correctly rejected that request; the run record was unchanged. Only the harness
query was corrected for the passing attempt.

Observed presentation limitation: the review card's initial file list contains
the original concept/context references. The actual geometry preview is
available farther down in Results. No product change was made during this
capture. The initial unpinned working-view screenshot was captured while loading;
it is an entry observation, not an additional readiness qualification.
