# Bounded desktop reasoning image handoff

Status: inspected implementation boundaries; not enabled or qualified.

The current adapter rejects images in both response and bounded-action tasks.
The accepted workflow reference owner already verifies files and produces inline
`data:<media>;base64,...` images. Desktop requests are persisted with their exact
payload and digest, capped at 256 KiB. The existing invocation evidence helper
replaces image data with media type, encoded size and SHA-256 before redaction.
The current pending-task MCP tool emits text/structured data only. Viewing an
artifact in the panel does not prove the desktop model received it.

Preferred next spike, keeping existing owners and limits:

1. Add an explicitly opt-in image-input profile to the desktop composition and
   frozen runtime binding; preserve the installed default's denial. Preserve
   current source/input and request digest semantics, not a parallel blob store.
2. Accept only already resolved inline PNG/JPEG references, rejecting remote URLs,
   malformed encodings, unsupported formats and a total task over 256 KiB before
   persisting or waiting. Do not resize, omit images, truncate instructions or
   raise the budget silently. Oversize remains an explicit readiness/transport
   limitation until separately designed and qualified.
3. Preserve the complete inline request in its existing private durable owner.
   Reuse existing invocation redaction; capture the exact MCP presentation
   boundary separately with request and image identities, never claim model uptake
   merely from a prepared payload.
4. Deliver explicit MCP image content together with the exact pending-task
   identities and saved instructions. Keep image bytes out of ordinary text
   projections; digest/metadata must identify the original frozen request, not
   claim a rewritten presentation is identical. No independent file/URL read port.
5. Qualify real desktop image perception on a small non-engineering fixture,
   with wrong-request/image identity, malformed bytes, cancellation, late reply,
   restart/orphan and drift checks. Local schema/unit tests alone cannot enable
   dependent engineering image tasks. No fallback model or hidden API worker.
6. Then use unchanged real CAD captures inside the accepted engineering process,
   preserving meaningful stages and original verification requirements. Model
   interpretation never becomes geometric measurement or human review authority.

A 13,661-byte retained PNG used in the display proof fits the existing payload
budget by itself; that does not prove a multi-image task plus instructions/tool
schemas fits. Measure each full request. Larger rendering assets are a separate
requirement, not permission to weaken the current guard.

Baseline verification before changes: 33 desktop boundary, durable repository and
workflow execution tests passed together on 8267f93e. Installed 0.6.0 remains on
its original runtime; all spike implementation must stay in the continuation
worktree until a separately qualified candidate is selected.
