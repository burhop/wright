# Retained image display correction

The user opened `block-isometric.png` in the actual Windows desktop panel on
28 October. The file preview displayed **A bitmap preview is unavailable**.
This is a native acceptance failure, despite the earlier Linux simulated-host
pass. The screenshot is retained at
`/home/burhop/.codex/attachments/b5ef9e59-a0c9-4293-8c61-6156c688183d/codex-clipboard-df4d4b74-b953-4a4f-bfb7-b1e766550645.png`.

## Diagnosis and correction

The shared `ImageThumbnail` received a supported image Blob but rendered it using
a temporary `blob:` URL. The earlier test host imposed no image-loading policy.
Adding `img-src data:` reproduces the same unavailable-preview state with the
installed 0.32 resource and actual retained file. The original PNG is intact.
This establishes a reproducible compatibility defect; the actual desktop's CSP
has not been captured, so it is not proof of its precise failure cause.

The existing shared viewer now displays bounded inline raster bytes. It keeps
the PNG/JPEG/WebP/GIF allowlist and 32 MiB viewer limit (the native bridge still
limits reads to 1 MiB), excludes SVG/HTML, ignores stale asynchronous reads,
shows loading separately, and gives an explicit failure/download message.
No image bytes, MIME type, artifact identity, gateway checks, run record, or
validation outcome are changed. No external image fetch, host-policy expansion,
additional viewer, provider call, or new executor is introduced. Download links
still refer to the original bytes. The common/shared view remains the owner.

OpenAI's [UI guidance](https://developers.openai.com/plugins/build/chatgpt-ui)
and [resource metadata reference](https://developers.openai.com/plugins/reference)
describe host-enforced resource policies and versioned resource URIs. They do
not establish that temporary Blob URLs work in this particular desktop build.
The candidate leaves Wright's empty external-resource allowlists unchanged.

## Qualification

Evidence directory:
`.local-run/engineering-run-journey-20261028/bitmap-preview/`.

| Check | Result | Boundary |
|---|---|---|
| Installed 0.32 Windows image preview | FAIL | User screenshot above |
| 0.32 with restrictive image policy | FAIL, reproduced | `baseline-032/failure.png`, `csp-reproduction.json` |
| Corrected image visible, in viewport, exact original hash | PASS | `candidate-033/image-1100.png`, `image-480.png`, `report.json`; actual owners/storage, simulated Linux host |
| Producing step, Results 1/1, no false source mismatch, return to same run | PASS | Same read-only compiled-resource journey |
| Report precision, exact file bytes, narrow layout, reopen | PASS | Same journey; no Windows download claim |
| Shared image viewer, different historical coupon image, malformed-image fallback | PASS | `shared-viewer-csp/report.json`; controlled transport, real browser decoding |
| Native process client / UI kit checks | PASS | 130 tests; includes stale reads, active-format/size rejection, failure and readiness |
| TypeScript, changed-source lint, native resource build | PASS | `local-checks.json`; zero external assets; not full repository gates |
| Corrected actual Windows image preview | PASS | User screenshot and confirmation of 0.33 below |
| Windows file delivery/open, chat-switch restoration | UNVERIFIED | No substituted Linux claim |

The read-only journey uses workspace `4bcda80f-0afe-44d7-a8ef-33b2395300b0`,
`workflows/block-preview-recovery.workflow.wflow`, completed run
`91c3fe3f4e0c477e9d9ea0d0dde477b2`, and image SHA-256
`1a1f6ca6c17ef90e5e0e9d6f70eb8f4e867405a0f89669ecdaca5dda1d23698f`.
Historical runs, the CAD document/revision/build, source and outputs remain
unchanged. No engineering run was started, resumed or retried. This rendering
correction does not establish engineering acceptance or finish the broader UI
goal. Engineer-facing report summaries and clearer return navigation remain open.

The previous Robot Tracking Diagnosis editor regression is retained; this change
does not add workflow semantics. The tracked `native_image_acceptance.mjs` now
enforces the restrictive image policy so an unrestricted test cannot conceal
this rendering dependency again.

## Installed candidate

Only `wright-desktop-gb10-prototype` was updated to **0.33.0**, from local commit
`290f8c12969783ce7dcd3046a0a0f3c4253921df`. UI resource SHA-256:
`a12381ebc9bd75420a89f0a35fdd57e1516ff2c7cee3789cbd6cf412123ffc55`.
The frozen candidate and installed package both pass MCP initialization,
59-tool discovery, exact resource bytes and retained-run/output identity checks.
Installation preserved unrelated settings, earlier named caches, and nine
protected source/run/result/backend metadata files. The backend was not restarted.

At 19:30 UTC, the documented MCP reload reconnected this conversation with no
tool error and identical configuration hashes before/after reload. This chat then
called the exposed connection tool and requested the exact completed run read-only.
Receipts are `installed-only-protocol.json`, `install-step-{0,1,2}.json`,
`preserved-state-after-install.json`, and
`host-mcp-discovery-20261028T193050Z.json` in the evidence directory.
Actual Windows image display remains pending a screenshot of this candidate;
installation and a successful open request do not establish it.

## Actual Windows confirmation

The user subsequently confirmed **“Ah. oK. it works then.”** and supplied a
Windows desktop screenshot showing `block-isometric.png` rendered in the right
panel. The screenshot is retained at
`/home/burhop/.codex/attachments/739dc2c2-074f-44a8-b5ba-08e599dadc6d/codex-clipboard-d453d7e3-14e3-41c4-8a9d-dc500461b8e8.png`.
The current panel also reported one loaded image, no failed images, the exact
retained run and 0.33 bundle payload
`6dd04511a34bd998487693b0e57a3007769811ca9ea3668ad65c4ead467b54ea`
at 19:33:52 UTC. The screenshot and user's observation establish actual native
image display; telemetry corroborates the build/run but is not a screenshot.

An already-open 0.32 panel remained alongside the new 0.33 view and initially
reproduced the old failure after installation. Its old error wording and payload
identity distinguished it from the corrected view. Identical tab labels made
this confusing; installing a plugin does not replace existing mounted panels.
Both the original failure and corrected Windows evidence are preserved.
Windows download/open, chat-switch restoration and the broader usability goal
remain unqualified by this image-display check.
