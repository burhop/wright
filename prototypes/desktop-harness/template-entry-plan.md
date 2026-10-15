# Next missing panel capability: use an existing engineering template

Implementation and isolated qualification, 15 October 2026. This work is in
`codex/desktop-template-entry`, based on 33afba8a; neither the current gate
candidate nor the installed plugin was changed.

Observed: GET /api/workspace/workflow-source-templates returns catalog 1.0.0
with ten built-in templates, including Robot Tracking Diagnosis and Conduction
Heat-Spreader Sizing. All report reference or setup_required. None is the required
SteveCAD native four/six-hole workflow. Exposing this catalog must not relabel
reference workflows runnable or substitute them for the accepted SteveCAD demos.
The full existing 30-example collection remains unchanged.

Reuse:
- Existing EngineeringTemplateDialog for selection, name and readiness wording.
- Existing template list/detail/readiness/instances API and source owner.
- Existing source version/digest, workflow_path and request_id creation contract.
- Native home workspace/session identity and existing editor open/read path.

Small change: give the existing dialog an optional typed service interface with
the current workspaceService as default. Supply a native MCP transport for the
same operations. Read-only list/detail may be model/app visible; instance creation
must enforce exact workspace/session through the existing scope check. Extend the
prototype mutation gate only for exact template-instantiation/readiness paths.
Do not add a generic HTTP proxy. Preview URLs need a qualified resource transport
or an explicit unavailable preview; a GB10 localhost URL is not a Windows preview.

Keep scope/grants/runtime authority unchanged. Instantiation copies accepted
source/dependencies through its existing owner; it is not readiness approval or
execution. Failure after creation must reconcile the exact saved path rather
than issue a new request identity silently. Preserve the same editor and canvas.

Validation: template version/digest drift, wrong workspace, duplicate click and
uncertain acknowledgement; both Hermes/default service and native transport;
actual panel Workflows entry and exact saved source/dependencies. Use the existing
Robot and manufacturing templates as differing source-copy cases without running
protected originals. Do not count copying these templates as their required
engineering regression runs. Native Windows acceptance stays separate.

This can proceed while genuine Windows callback/sign-in remains unavailable.
It does not remove the original engineering-demo completion requirements.

## Implemented boundary

The shared dialog accepts an optional typed service with the current Wright
service as default. Native home supplies the two-method MCP client; list and
copy both check the exact workspace/session before reaching existing owners.
Only the exact template instance route is added to the preview mutation gate.
There is no generic HTTP proxy and no new execution authority. An explicit retry
of the same template/path retains its request identity so the existing owner's
idempotency contract can reconcile it. Changed template/path choices receive
a distinct identity; owner conflict rules still prevent overwrite.

The native picker uses the existing host theme and a scoped scrolling layout to
keep its header/footer visible. Template image previews remain explicitly
unavailable in this host; no relative GB10 URL is presented as a Windows image.
The workflow canvas and editor remain shared.

An initial real browser walkthrough copied Robot and manufacturing templates but
visual inspection found header clipping. Native-only layout correction was
verified with header/footer bounds at 460 and 1100 pixels. A final compact
placeholder adjustment correctly caused the previous resource binding to refuse
connection; the exact denial was retained and final qualification uses fresh
state. No configuration guard was relaxed.
