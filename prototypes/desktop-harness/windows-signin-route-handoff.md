# Windows → GB10 sign-in route: developer qualification

Status: prepared, not executed. This is a temporary developer spike, not the
qualified low-friction demo experience. SteveCAD account setup is confirmed;
no real authorization attempt should start until the route is proved.

The B: mapping shares files, but SteveCAD's browser redirect goes to a loopback
HTTP listener on GB10. A Windows browser's `127.0.0.1` reaches Windows unless that
port is explicitly forwarded. Keep Wright's existing SDK OAuth/PKCE/state and
private token store; do not copy cookies or tokens or accept callbacks manually.

For the Windows agent:

1. Use `promaxgb10-9666`, the remote connection identified by the desktop's
   project list on 14 October. No user-supplied alias is needed. Verify its
   existing SSH configuration on Windows; do not edit it or create credentials. Coordinate with the GB10 agent to start a bounded, plain
   HTTP loopback probe on an available port. The probe must use a non-OAuth path,
   contain no credentials and record only whether the exact request arrived.
2. In a dedicated Windows terminal, run:

   ```powershell
   ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:<port>:127.0.0.1:<port> promaxgb10-9666
   ```

   Substitute the confirmed port in both places. Stop if Windows cannot bind it;
   do not stop another process, expose a public listener or silently change ports.
3. Open the supplied plain probe URL in the Windows browser and have the GB10
   agent confirm the exact request. Stop the probe and preserve its receipt.
4. For actual sign-in, confirm the runner's **actual** callback port. It can differ
   from its usual 9505 when occupied. Recreate the tunnel for that exact port if
   needed. Use only the Wright panel's explicit provider sign-in action, within
   the callback timeout. Do not paste the authorization URL or callback code into
   chat, logs, screenshots or the repository.
5. Wright must report protocol validation from its existing owner. A successful
   browser page alone does not prove token storage, tool readiness or permission.
   Workspace grants and engineering reviews remain separate steps.
6. Close only this dedicated SSH tunnel after callback/validation completes.

Retain separate evidence for synthetic route reachability, actual OAuth,
protocol validation and Windows panel acceptance. If no working SSH path exists,
report that limitation; do not invent a desktop forwarding API or switch accounts.
The tested 0.8.0 candidate is now installed with these sign-in controls. This
existing conversation still exposes the older tool connection; use a fresh
conversation and verify the connection before testing. Actual Windows sign-in
and panel acceptance remain unverified.

Connection discovery is verified; Windows forwarding is not. GB10 observed
an active Windows SMB connection, but reverse SSH to Windows timed out. That
does not test Windows-to-GB10 SSH. The earlier synthetic browser request was
queued and expired without a receipt; it is inconclusive, not an OAuth failure.
