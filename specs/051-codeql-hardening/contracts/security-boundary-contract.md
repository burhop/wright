# Security Boundary Contract

## Setup Health Probe

`GET /api/setup/health?url=<candidate>` retains its authenticated control-plane endpoint and `HealthCheckResponse` shape.

- Only syntactically unambiguous HTTP/HTTPS targets are evaluated.
- Loopback is intentionally permitted.
- Non-global private/ULA origins require an exact match to Wright's current configured LLM/health origin.
- Metadata, link-local, unspecified, multicast, reserved/documentation, CGNAT, mapped, and transition addresses are always prohibited.
- Every DNS answer and redirect is revalidated; the actual connection uses a validated pinned address.
- Redirects are same-host, bounded, loop-detected, and never downgrade HTTPS.
- Environment proxies and automatic redirects are disabled.
- Success returns `status=healthy`; all failures return `status=unhealthy` and a bounded generic error. No response body, address inventory, credential, URL userinfo, or raw exception is returned.

## Session Creation

`POST /api/agent/sessions/new` keeps the existing optional `workspace` field.

- When `workspace` is supplied, it must resolve to an existing registered workspace; Wright does not create it.
- When it is omitted, Wright creates one UUID-named direct child beneath its managed workspace root.
- Unregistered, missing, alias/symlink, traversal, absolute attacker-selected, and sibling-prefix locations are rejected without filesystem mutation.

## Vault Upload and Read

- Upload response retains the original display filename and a generated download URL.
- On-disk keys contain no client path segments.
- Reads accept only a generated or legacy confined basename that resolves to a regular file inside the canonical vault.
- Invalid and missing names produce the existing not-found behavior without revealing filesystem details.

## Title and Glob Parsing

- `/title` is case-insensitive, requires at least one whitespace separator and non-empty content, and produces at most 200 title characters.
- Title parsing and glob translation are linear in input length.
- Glob `*` and `?` retain their supported wildcard meanings; every other regex metacharacter is literal.

## Package and VCS References

- Only explicit structurally valid VCS URL forms are treated as VCS requirements.
- PyPI/uv/pip names and npm/scoped npm names must satisfy their manager-specific identity grammar before registry or subprocess use.
- Invalid identities produce a package-not-found/unsupported result and cause no registry request or package-manager subprocess.

## Client Error Disclosure

- Onshape proxy and chat SSE failures return a stable generic message and trace identifier.
- Raw exception text, stack details, paths, credentials, command output, response bodies, and internal endpoints remain server-side only.
- Structured logs preserve complete diagnostic context correlated by trace ID.

## SPA and Viewer Content

- A static asset is served only after canonical proof that it is a regular file inside the configured frontend distribution root; otherwise the SPA entry point is served.
- HTML/PDF viewer sources are root-relative same-origin workspace content URLs.
- HTML preview remains sandboxed with scripts allowed but same-origin privilege withheld.

## CodeQL Disposition

- Production alerts #3, #4, #5, #7, #8, #10, #12, #24, #25, #27, #28, and #29 must close through code changes on dev.
- Alert #2 is dismissed as `used in tests` with evidence that `respx` fully mocks the synthetic hostname.
- Alert #13 is expected to close through clearer containment code. It may be dismissed as `false positive` only if CodeQL still reports it after traversal, sibling-prefix, encoded traversal, and supported-host symlink tests pass.
