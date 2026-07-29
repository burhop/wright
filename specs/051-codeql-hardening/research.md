# Research: CodeQL Security Hardening

## Outbound Health-Probe Policy

**Decision**: Move probe policy into a provider-neutral `agent_adapters` service. Accept only bounded HTTP/HTTPS URLs with a hostname and valid port; reject user information, fragments, controls, backslashes, encoded authority ambiguity, malformed IPv6, and non-canonical numeric host forms. Resolve every address, reject any mixed or prohibited result, and pin a validated numeric IP in the outbound request while preserving the logical `Host` header and HTTPS SNI. Disable environment proxies and automatic redirects. Revalidate at most three same-host redirects, allow HTTP-to-HTTPS upgrades, reject HTTPS downgrades/cross-host redirects, and build the `/health` fallback structurally.

Loopback literals and exact `localhost` remain permitted. Private IPv4 and IPv6 ULA targets are permitted only when their exact origin is Wright's currently configured LLM/health origin; globally routable targets remain permitted. Unspecified, link-local/metadata, multicast, reserved/documentation, CGNAT, IPv4-mapped IPv6, NAT64, 6to4, and Teredo destinations are rejected even when configured. Ordinary DNS names must resolve entirely to globally routable addresses unless the name is the configured local LLM/health host.

**Rationale**: Scheme-only validation or DNS preflight followed by a normal hostname request leaves parser, redirect, proxy, and DNS-rebinding gaps. The installed httpx/httpcore stack supports connecting to a numeric request host while carrying the logical Host/SNI, so the validated address can be the address actually contacted without adding a network dependency. Exact configured-local-origin authority preserves legitimate LAN LLMs without turning the endpoint into a general private-network fetch primitive or adding a new configuration surface.

**Alternatives considered**:

- Ban all private and loopback destinations: rejected because it breaks Hermes/local-LLM operation.
- Permit all private destinations: rejected because it preserves a general internal-network SSRF primitive.
- Validate DNS and call the original hostname: rejected because the client resolves again and can be rebound.
- Follow redirects automatically: rejected because a permitted origin can pivot to metadata or another internal host.
- Disable all redirects: safe but needlessly breaks common same-host/HTTPS-upgrade health endpoints.
- Add another HTTP library or a low-level socket client: rejected as dependency and implementation expansion.

## Vault and Workspace Containment

**Decision**: Store uploads under generated UUID keys with only an allowlisted display extension; never put a raw client filename into a storage path. The `data_vault` package resolves reads against the canonical vault root, rejects all POSIX/Windows separator, drive, UNC, NUL, sibling-prefix, and symlink escapes, and returns only a proven contained file. A supplied session workspace path is a reference to an existing registered workspace and is never created; only an omitted workspace may generate a UUID child through `WorkspaceService`'s managed-root creation logic.

**Rationale**: Basename-only handling is platform-dependent, UUID-prefixing raw traversal still escapes, and API string-prefix checks do not establish filesystem authority. Existing data-vault/workspace packages already own these rules and SQLite registration supports explicit workspaces outside the managed root.

**Alternatives considered**:

- Permit any canonical path below the managed root: rejected because a request still should not create a caller-selected directory.
- Require only workspace IDs: clean long-term contract but unnecessarily expands the API/frontend change.
- Keep containment logic in routes: rejected by package ownership and modular-boundary requirements.

## Bounded Parsers and Package Identity

**Decision**: Parse `/title` with linear string operations, require whitespace after the command, strip surrounding quote characters, and cap the resulting title at 200 characters. Translate glob patterns in one pass, escaping every regular-expression metacharacter except supported `*` and `?` tokens. Parse only explicit VCS URL forms structurally and validate PyPI/uv/pip and npm package identities with manager-specific grammars before using them in registry URLs or subprocess arguments; percent-encode registry path segments.

**Rationale**: One-pass parsers remove polynomial regex behavior and replacement-order mistakes. Structural URL/package grammars prevent trusted-looking substrings and option/path injection while preserving valid scoped npm and VCS-backed uv commands.

**Alternatives considered**:

- Patch the existing title regex: rejected because direct parsing is simpler and eliminates the risky engine behavior.
- Add more chained glob replacements: rejected because replacement output can be reinterpreted and another metacharacter can be missed.
- Validate only the GitHub hostname: rejected because malformed package identifiers would still reach URLs and subprocesses.

## Safe Errors, SPA Files, and Viewer Origins

**Decision**: Log complete proxy/chat exceptions with their existing trace/session context, but return stable generic messages plus trace IDs. Sanitize both the CodeQL-reported SSE attach failure and the normal chat-job failure path. Resolve SPA assets canonically and require `Path.relative_to(root)` before serving a regular file. Build iframe/PDF sources as root-relative `/api/workspace/files/content` URLs with `URLSearchParams`; retain the HTML sandbox without `allow-same-origin`.

**Rationale**: Removing only one error sink leaves equivalent information exposure in the same flow. Canonical relative-path proof is clearer than a string prefix and rejects outside symlinks. Root-relative viewer URLs express the actual same-origin contract and remove the location-derived protocol taint without forcing HTTPS on native localhost.

**Alternatives considered**:

- Remove useful error context entirely: rejected because operators need correlated diagnostics.
- Dismiss the viewer findings as same-origin: possible but a tiny behavior-preserving source change eliminates ambiguity.
- Dismiss the SPA finding immediately: rejected until clearer code and traversal/sibling/symlink tests are present.

## Alert Disposition

**Decision**: Let fixed production instances close through CodeQL on the feature/dev commit. Dismiss #2 as `used in tests` only after confirming `respx` mocks the synthetic `http://llm.local` request. Prefer rewriting #13 so CodeQL closes it; dismiss as `false positive` only if the canonical containment regression evidence passes and the clearer code still produces the finding.

**Rationale**: Scanner state should reflect real code safety. Suppression or configuration weakening would hide production risk and is prohibited by the feature scope.
