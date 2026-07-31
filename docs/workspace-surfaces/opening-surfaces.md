# Open an application in Wright or your browser

A ready web application such as BREP can be presented inside the Wright
workspace, in the system browser, or in both places. Wright always returns a
backend-issued absolute preview link; the web UI never constructs or accepts a
raw upstream target URL.

## Choose panel, browser, or both

- **Open in panel** keeps the application beside chat in Wright. The app runs at
  a distinct preview origin, not at Wright's control-plane origin.
- **Open in browser** asks the operating system for a new browser window or tab.
  If that action is refused, Wright leaves an existing panel intact and reports
  a copyable recovery action.
- **Open both** is available for a shareable app. Both views use the same ready
  instance and generation, so application state changes appear in both.

Managed applications are not passed through the sanitized Python-display
renderer. Their declared JavaScript, normal HTTP requests, WebSockets, and
event streams run in the application's distinct preview origin, subject to the
manifest and administrator policy. This is the path intended for BREP and
other full web applications. The workspace frame remains sandboxed; an app
that needs a browser feature the panel policy cannot grant should use **Open in
browser**.

An application that declares isolated presentations creates a separate instance
for each view. Wright names that consequence and requires acknowledgement before
opening it; it never labels isolated views as shared.

Select **Remember this presentation choice** to store a non-secret preference
for the current user, workspace, and immutable source identity. The preference
is only a hint. Wright revalidates source version, workspace authority, current
runtime identity, host support, and panel/browser eligibility every time. If it
is stale, Wright explains why and offers the safest eligible fallback; the
version-1 fallback order prefers the system browser, then the panel.

## Closing is not stopping

These controls intentionally have different effects:

- **Close panel/browser presentation** revokes and removes only that view. A
  workspace-lifetime application keeps running and another presentation can be
  opened later.
- **Close surface tab** closes its panel view but retains the declared surface.
- **Stop application** revokes all presentation authority and asks the managed
  runtime controller to stop and reconcile the complete owned process tree.
  Restarting creates a new generation.
- Deleting a durable Python output is a separate destructive operation and does
  not stop an unrelated application.

## Framing refusal and recovery

An application may send `X-Frame-Options` or CSP `frame-ancestors` rules that
prevent embedding. Wright preserves those headers—it does not weaken the app's
security to make a panel appear to work. Because browsers do not expose every
cross-origin framing failure reliably, the panel may report **embedding status
unknown**. **Open in browser** remains available whenever browser presentation
is eligible.

After reload, persisted tabs are inert intent rather than runtime authority.
Wright reconciles them with the server's current source version, instance ID,
generation, and lifecycle. A stale ready snapshot becomes the current stopped
or failed state without silently launching a new process. Use the explicit
restart action when a new generation is wanted.

## Desktop troubleshooting

The desktop shell accepts only HTTP(S) preview links issued for the configured
preview host, or a direct origin that an administrator explicitly allowlists.
It denies unexpected renderer navigation and window creation, and child frames
do not receive the Wright preload bridge.

If **Open in browser** fails:

1. Keep the panel open; the running app is not stopped.
2. Retry after checking the operating-system default-browser setting.
3. Open diagnostics for the stable `SURFACE_HOST_*` error.
4. For a remotely hosted Wright deployment, verify the configured public
   preview scheme/domain/port. Do not replace the issued URL with a localhost or
   upstream target URL.
