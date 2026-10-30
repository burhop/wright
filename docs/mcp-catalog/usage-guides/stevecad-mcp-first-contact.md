# SteveCAD first-contact addendum

Recorded 26 October 2026. Status: observed setup/account boundary only; no new CAD
or MCP engineering qualification. The [main SteveCAD guide](stevecad-mcp.md)
retains its existing successful geometry, export, recovery and exact-output
verification evidence. This addendum keeps the new customer research separate.

## Identity, sources and installation

Catalog ID `stevecad-mcp`; hosted Streamable HTTP endpoint
`https://stevecad.studio/mcp`; OAuth browser authorization.
[Existing qualification](../followups/stevecad-mcp.md) and
[setup recipe](../mcp-server-setup-recipes.md#stevecad-steve-cad--11-october-2026)
remain authoritative for their historical scopes. No local CAD application is
required, but the consumer needs its MCP client and an authorized SteveCAD account.

## Observed use and evidence

A fresh Ubuntu ARM64 synthetic customer installed Wright's original private
candidate, discovered SteveCAD after changing the catalog's Curated filter to
All records, and reached its OAuth sign-in page. That page offered Google/X and
said first sign-in creates an account and continuing agrees to terms. No account
completion fact or sign-in was available; the customer stopped. Its original
[report](../../../artifacts/first-contact/synthetic-beta-002/session-records/gh2-base-beginner/report.json)
and independent
[assessment](../../../artifacts/first-contact/synthetic-beta-002/session-records/gh2-base-beginner/verification.json)
retain those observations. Installed/inactive is not connected or ready CAD.

A later prepared checkpoint could read Wright workspace status through actual
Hermes MCP calls after following the native SDK diagnostic. It also inspected
SteveCAD's bundled help without enrolling or creating geometry. The reviewer
supported that declared task, but the overall record was rejected for disagreement
on checkpoint-stage accounting. Preserve that rejection; do not call it a passed
full first-contact journey or provider qualification.

## Pitfalls, recovery and authority

A browser sign-in session alone does not authorize an MCP client. A configured
Wright gateway alone does not establish consumer-side SDK readiness. Hermes's
optional MCP support and the nonsecret native root binding are separate Wright
integration prerequisites; neither fixes an absent SteveCAD account.

Do not assert independent publisher completion on behalf of a simulated user.
The old Wright installer automatically supplied that flag; it was a Wright
interface defect, not human acceptance or a SteveCAD bug. The corrected candidate
preserves the backend's terms barrier and requests a new reviewed plan only after
a genuine independent completion statement. Reconcile the existing account and
installation state after that input; do not invent credentials or repeatedly
launch authorization to force a green result.

No new design, geometry measurement, export, physical acceptance or provider
version was established. No provider bug was reported. A future authorized
account-backed run should discover current contracts and create a new owned
document, then apply the main guide's revision-bound geometry/output checks.

## Hosted connection preparation — 28 October 2026

The human authorized use of the existing SteveCAD account and independently
confirmed publisher requirements. In isolated ARM64 VM106, Wright candidate105
accepted that statement through the ordinary installation review. This removes
the earlier authorization barrier; it does not establish an authenticated client.

The SSH-started runtime had no `DISPLAY` or `XAUTHORITY`; its normal OAuth browser
launch failed, while the UI remained on “Validating”. Start native Wright from
the customer's desktop session so sign-in opens on that same machine. The lab
preparation helper now checks the existing desktop and supplies its environment;
this is not a requirement to install a CAD application or create an SSH tunnel.
The shared OAuth runner correction surfaces a failed browser launch rather than
waiting for a callback that cannot arrive. That was the initial diagnosis;
the later installed observations and remaining limits are below. See the
[campaign issue](../../../artifacts/first-contact/synthetic-beta-003/issues.md#hosted-sign-in-no-browser-107-observed-during-preparation).

## Current recovery checklist — 28 October 2026

**Later reconciliation:** the existing desktop Wright connection completed two
live read-only SteveCAD calls and its saved inspection workflow at14:07EDT.
See the [connection verification](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/hosted-signin-107/DESKTOP-CONNECTION-VERIFIED.md).
Existing device-code support is implemented in the desktop integration's shared
OAuth client, with its own device-grant registration and server-scoped keys.
The older VM candidate lacks that path. A device request using its browser-flow
registration was rejected; this does not disqualify device-code support.
Do not use Google account recovery to connect SteveCAD. The mistaken recovery
page was closed on the user's instruction; no account settings were changed.
Automatic browser opening in VM106 was subsequently observed after correcting
its desktop environment, but that VM remains unauthenticated. Desktop success
does not establish a successful VM journey.

SteveCAD is hosted. **Do not install a local SteveCAD application or native CAD
host to address these sign-in failures.** Register its remote endpoint, complete
account authorization, check the actual connection, then enable it in the intended
workspace. Browser login and successful MCP authorization are separate facts.

| Observed obstacle | Recovery / current evidence |
|---|---|
| No browser opened; runtime lacked `DISPLAY` and `XAUTHORITY` | Use the customer's existing desktop environment when launching native Wright. The isolated Ubuntu VM uses `DISPLAY=:0` and `XAUTHORITY=/home/customer/.Xauthority`; these are lab-specific values, not settings for every customer. |
| Desktop variables present, but `gio` could not find an application for `text/html` | SSH also omitted Snap Firefox's desktop-entry search path. Include `/var/lib/snapd/desktop` in `XDG_DATA_DIRS` for this existing Snap installation. With that path, `gio mime text/html` and `gio mime x-scheme-handler/https` both identified `firefox_firefox.desktop`. The same installed runtime was restarted with that environment; Subsequent ordinary Check connection opened SteveCAD automatically; the later device route avoids desktop browser launch entirely. |
| Installed server offered no retry after closing setup | Candidate109 provides **Check connection** on the installed MCP card, calling the existing validation service. The actual click and returned failed result were observed. It does not reinstall, grant workspace access or prove authentication. |
| Hosted service described as a local installation | Candidate109 uses **Connect** / **Connection setup** for hosted catalog actions. Necessary builds passed; broad UI regression coverage remains deferred. |
| Google login appeared in the VM | The human confirmed the existing account uses Google on Windows. The VM has no Google session. The browser route remained incomplete. The subsequent device-code route was approved on Windows and completed inVM106; no Google credentials were copied and no account was created. |

The provider sign-in page and Google page were reached by manually opening the
same pending authorization URL in the VM's existing Firefox. This is an
**operator-assisted recovery**, not proof that automatic login or a first-hour
customer journey succeeded. Never publish authorization URLs, state, tokens,
cookies or one-use callback codes in these notes.

For a browser on a different computer, remember that `127.0.0.1` in the redirect
refers to that browser's computer, not the VM. Complete the existing authorized
flow through a supported handoff; do not repeatedly register clients, copy browser
cookies, silently claim sign-in, or ask again for already-recorded account-use
permission. The user rejected a manual PC SSH-tunnel requirement. Browser-callback completion across machines remains unverified. The later
device-code route was approved on Windows and completed inVM106, as recorded
below; use that verified route for this configuration.

After an actual authorization completes, verify protocol/tool discovery and a
safe read-only call through Wright before marking the connection ready. The later device connection and safe read-only gateway call are verified below.
No CAD result or engineering qualification was established by connection preparation.

Evidence: [readable preparation result](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/hosted-signin-107/RESULT.md),
[retained observations](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/hosted-signin-107/observation.json),
and the existing account-authorization receipt. Sources: `48b115aa` (browser error
and lab display), `ba4ebe9f` (connection retry), `be82df1e` (hosted wording).
Candidate109 is a local private build, not a published Wright release.

## Native device-code correction111

The existing device client and presentation validation were reused from desktop
source2e1367de. It requires the already-declared MCP SDK1.30.0. Native Wright
retains its browser-flow default; explicitly selecting
`WRIGHT_MCP_OAUTH_FLOW=device_code` at runtime startup uses the device-grant client
with separate `MCP_OAUTH_DEVICE_CLIENT` / `MCP_OAUTH_DEVICE_TOKEN` keys in the
existing server secret bundle. Browser-flow credentials remain intact. Unsupported
providers fail explicitly; no grant or legacy transport is silently substituted.

Native setup and installed **Check connection** display the actual provider
approval URL and user code while the backend owns polling, expiry and validation.
The read-only presentation endpoint requires engineer/admin authority and uses
no-store responses; it exposes neither device polling secrets nor bearer/refresh
tokens. Closing a UI does not start another connection attempt. This is a local
candidate correction, not a release or verified fresh first-hour outcome.

## Native device connection verified — 28 October 2026

Candidate111 onVM106 completed real human device approval. Native validation
`validation-feae649f67f74fb29d2c98b18888d09d` passed with29tools; the provider is
active. Wright's actual public gateway returned `api_reference(name="Model.box")`
in a separate operator workspace. See the [readable native proof](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/hosted-signin-107/NATIVE-CONNECTED-112.md).
Do not ask for another login while this connection works. The failed first check
and late human reply remain separate; the next check was explicit after terminal
state was observed. Generic RuntimeError failure feedback is still an open defect.
This is private-candidate operator connection qualification, not a fresh beta
journey, CAD qualification, release or website-ready demonstration.

## Actual hosted CAD and structural work — 28 October2026

The retained ARM64 guest now has a verified device-authorized SteveCAD connection.
No local CAD or solver application was installed for these provider operations.
During prepared customer116, the native assistant created a separate unapproved
handle document, generated and inspected its geometry, and subsequently completed
two revision-bound40N studies using SteveCAD's CalculiX path. Actual provider
receipts, STEP/STL, model/dimension image and solver contour images are retained in
[the readable late-result record](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/late-handle-121/RESULT.md).

| Observed result | Boundary |
|---|---|
| One generated solid; revision5 exports and dimensions | New unapproved preview, not the historical approved baseline |
|3mm and1.5mm studies succeeded | Same preview; assumed isotropic solid and fixed pad backs |
|0.1419/0.1441mm displacement;3.416/4.096MPa peak stress | Peak stress is not converged; no printed-strength or improvement claim |
| Native chat completed after the observer's15-minute cutoff | Not a completed customer visit or saved-workflow execution |

The original Printed02 process and reviews were preserved. Independent full
printing checks, washer access, exact recess interpretation, physical properties,
final slicing and a complete reusable customer journey remain unproved. This
records real hosted engineering use in this authorized VM, not clean-container
qualification for every platform or out-of-the-box availability.

The missing-workspace-write error was from Wright's reviewed-document publisher,
not SteveCAD. It created no pending approval request. Candidate118 preserves that
gate and explains it; the versioned authoring guide uses supported workflow
inputs/settings for assumptions instead of claiming a nonexistent approval link.
The installed public gateway returned the exact corrected asset and denied an
unapproved diagnostic publication as expected. No approval was synthesized.

Future retries must retain these distinctions and resolve the saved process's
actual bindings before another user is sent through its known setup obstacle.
Use the provider's current contracts and existing usage guidance; a successful
chat-driven preview does not automatically configure a Wright workflow.

### Saved-process handoff readiness — 28 October 2026

A read-only inspection of candidate118's customer116 workspace found all29
SteveCAD tools exposed, but no remote-file download or shell capability in its
workflow gateway. File inspection, local copy and reviewed text publication do
not fetch a provider export. The retained customer106 CAD binding asked for a real
local mesh while allowing only SteveCAD tools; its own prompt disclosed that
transfer might be unavailable. Do not copy this as a complete runnable binding.

The existing independent [file-transfer recipe](mcp-shell-server.md) has actual
SteveCAD export evidence and is the reuse candidate. Resolve its scoped workspace
setup, private ticket handling and actual file output binding before advertising
CAD export as ready. A successful chat session with terminal access does not
establish the saved workflow's capabilities. Analysis also needs an explicit
saved stage consuming the exact upstream CAD identity; it was absent from the
inspected customer116 source. Original measurement, slicing and human-review
requirements remain. No additional login or solver refinement addresses this gap.
See [observed readiness](../../../artifacts/first-contact/synthetic-beta-003/operator-retries/workflow-readiness-124/RESULT.md).

### Connection restored — 30 October, 9:16 a.m. EDT

After the user indicated readiness, normal native connection validation/device authorization completed with real Windows-browser approval. Initialization and 29-tool discovery passed; a separate read-only `list_designs` call through Wright succeeded. Browser login alone had not restored this MCP session. Preserve failed attempts and do not cycle codes without user readiness. Evidence: `artifacts/first-contact/synthetic-beta-003/operator-retries/stevecad-recheck-161/CONNECTED-173.md`. No CAD or engineering acceptance is established by this check.
