# Local Control-Plane Security

Wright's HTTP API and WebMCP socket are control-plane interfaces: they can edit
files, run workspace Python, invoke tools, manage MCP subprocesses, read logs,
and change configuration. Authentication is therefore enforced by default.

## Configuration

Generate a unique token for each installation and put it in the process
environment or an environment file with owner-only permissions:

```bash
openssl rand -hex 32
```

```env
WRIGHT_AUTH_MODE=enforced
WRIGHT_API_TOKEN=<generated value>
WRIGHT_BIND_HOST=127.0.0.1
WRIGHT_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Use `Authorization: Bearer <token>` for API clients. A local browser can
exchange the same token for an HttpOnly, SameSite=Strict cookie:

```bash
curl -i -c wright.cookies \
  -H 'Content-Type: application/json' \
  -d '{"token":"<generated value>"}' \
  http://127.0.0.1:8000/api/auth/session
curl -b wright.cookies http://127.0.0.1:8000/api/settings
```

Do not put the token in a URL, shell history, committed `.env` file, log, bug
report, or browser local storage. Feature 043 will replace remaining plaintext
provider-secret storage; this control-plane token does not solve that separate
problem.

WebSocket clients authenticate with the session cookie, an Authorization
header where supported, or the `wright.bearer.<token>` subprotocol. The server
checks the configured Origin before accepting the connection.

## Remote bind

`WRIGHT_BIND_HOST` must describe the actual server bind. A non-loopback value
such as `0.0.0.0` refuses startup unless enforced mode and a token are both
configured. A token does not provide transport encryption: remote deployments
also require a trusted TLS reverse proxy and a narrow origin allowlist.

## Compatibility migration and rollback

For one migration release, a loopback-only operator may set
`WRIGHT_AUTH_MODE=compat`. This restores the old unauthenticated behavior and
must never be combined with a remote bind. Return to `enforced` after clients
are configured. There is intentionally no wildcard-origin compatibility mode.

Legacy scratch references must be moved from global `/tmp` into
`<workspace>/.wright/tmp`. Absolute paths, traversal, Windows drive/UNC/device
paths, alternate data streams, symlinks, junctions, and reparse points are
rejected. Backup IDs are exactly 64 lowercase hexadecimal characters. There is
no rollback switch for path escapes.

## Current role boundary

The installation token represents the local administrator. The middleware
records an admin principal and the `require_admin` dependency is the route-level
extension seam for future operator/read-only identities. Multi-user identity,
password login, and remote authorization are not claimed by Feature 042.
