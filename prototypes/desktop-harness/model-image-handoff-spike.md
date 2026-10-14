# Bounded desktop reasoning image handoff

Status: opt-in transport and one actual image-input workflow qualified locally
on 14 October 2026; installed plugin remains disabled for image inputs.

The completed synthetic run `cdfbe5b7969745c39cdede500e38c60d` used the canonical
workflow supervisor, resolved reference-image owner, desktop adapter, actual MCP
image content and this desktop conversation's reply. The exact MCP image block
was forwarded to the model through the orchestration image output. Ground-truth
shape/color order was not read before answering. The saved 116-byte JSON output
matches both the desktop answer and hidden fixture; SHA-256
`d175a40360988e58f4600077157572d5b1c225f858c8f46dd54e3cb9f5060000`.
Evidence: `/tmp/wright-desktop-image-perception-20261014-04/image-perception.json`
and `saved-output-verification.json`. This proves the observed image/response
route, not automatic native-plugin delivery or CAD interpretation accuracy.

The separate qualification service's explicit `--enable-image-inputs` now permits
bounded reference-image tasks as well as image transport. Default denial,
PNG/JPEG format and complete-request size bounds are unchanged. Image generation,
CAD/application/direct-tool/external-action gates remain. Installed 0.7.0 and its
runtime are unchanged. Image-action tasks, actual engineering captures, multi-image
budgets and current-profile restart/recovery still need qualification.

Three failed attempts are preserved: 01 lacked the MCP text-result fallback in
the fixture client; 02 delivered a correctly perceived image but its standalone
reasoner was rightly rejected as having no live supervised run; 03 used an invalid
source filename. The corrected fourth attempt used an actual supervised workflow.
No consumer check, filename contract or permission guard was relaxed.

## Original investigation (historical baseline)


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
