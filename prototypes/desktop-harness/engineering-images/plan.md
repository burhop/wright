# Required original engineering images: next bounded spike

Read-only finding, 15 October 2026. The accepted native SteveCAD review requires
three CAD captures and three original Blender renderings. Historical block and
six-hole artifacts contain respectively 1,538,736 and 1,551,834 raw image bytes;
base64 alone requires 2,051,652 and 2,069,120 bytes. Their immutable inventory is
in inventory.json. No historical run was resumed or artifact changed.

Current code imposes 262,144 bytes on the entire request payload and on each
inline image URL. This rejects these original reviews regardless of authentication.
The create-design task separately declares a 1 MiB MCP context budget, so tool
schema/result growth must be measured too. The inventory is a lower bound, not
an actual serialized task or evidence of delivery to the model.

Preferred smallest spike: introduce an explicit, versioned opt-in engineering
image profile, retaining the existing default and inline-png-jpeg-v1 bounds.
Start with a proposed 8 MiB complete canonical request ceiling, at most eight
PNG/JPEG images and 2 MiB decoded bytes per image. Keep reply/action size bounds
unchanged and enforce a separate 256 KiB non-image text/tool envelope until real
source qualification establishes whether that envelope suffices. These are
proposed limits, not enabled capabilities or proven host limits.

Reuse current durable request storage, exact request/image digests, redaction,
MCP ImageContent port and frozen binding/routing verification. No new blob service,
image conversion, resizing, URL fetch, executor or fallback model. The profile
must be included in the resolved binding; continuation with a changed profile
must fail. Keep old receipts readable under their original profile. Report an
oversize task explicitly rather than silently dropping images or tools.

Before enabling: exact-bound and over-bound checks; malformed encoding/media;
wrong workspace/request/image identity; cancelled and orphaned request denial;
restart/drift denial; full six-original-image delivery and desktop-authored
comparison through a live supervised fixture. Record actual image bytes observed
at the MCP boundary. Historical-image perception is a transport qualification,
not a new CAD result, numerical geometry verification or human acceptance.

Inspect actual complete request sizes before implementing the proposed limits.
If the text/tool envelope exceeds its existing bound, document the measured need
and qualify an explicit additional contract change; do not weaken it to pass.
Native Windows delivery remains a distinct check. Fresh four/six-hole SteveCAD
runs, all downstream native export/render providers and genuine reviews remain
required after authentication and this capability are qualified.
