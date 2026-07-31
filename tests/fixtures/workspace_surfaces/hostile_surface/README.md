# Hostile Workspace Surface Fixture

Protocol version: `1.0`.

This test-only application deliberately attempts to read the parent document and
storage, inherit a Wright host-only cookie, open a popup, reach a Wright `/api`
route through its preview origin, request camera access, trigger a download,
navigate the top-level page, and send a wildcard privileged-looking message.

Every attempt must either be blocked by the distinct origin, iframe sandbox,
Permissions Policy, preview-host dispatcher, or ignored by exact bridge binding.
`expected-audit.json` lists the safe diagnostic shape. It intentionally contains
no raw cookie, URL query, target pin, user content, or upstream log value.

Cleanup: close the presentation, revoke its cookie and grants, remove the iframe,
and stop the test server. This fixture must never be packaged as a user example.
