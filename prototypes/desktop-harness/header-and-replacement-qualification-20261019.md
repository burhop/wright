# Header credentials and reviewed replacement connections — 19 October

Implementation candidate; installed prototype remains 0.15 until the tested,
backed-up transition. This extends the existing Connections journey: import or
enter a literal MCP source, review setup, enter missing private credentials,
validate the protocol, and separately enable tools in the exact workspace.

HTTPS authentication headers are declared by name in the reviewed configuration.
Values use the existing one-use encrypted credential form and SecretProvider;
only the transport receives them. Header mode explicitly disables OAuth and
redirect/legacy-SSE fallback. Reserved routing/protocol headers, insecure or
credential-bearing URLs and duplicate names are rejected. Default environment
serialization is unchanged, preserving existing catalog/configuration identities.
The current SDK receives headers on its HTTP client, not a deprecated helper
argument. This is static provider authentication, not an account/grant substitute.

“Set up a replacement” reads a public draft only on an explicit panel action,
checking the workspace/session, provider and observed control digest. Reviewed
imports can prefill declared public launch settings and credential names; legacy
or catalog overrides with uncertain confidentiality have no inferred public
projection. Users can instead review catalog setup or import sanitized source.
A new name and normal setup review create a separate connection. Existing
source, keys, permissions, accepted workflow bindings and runs are preserved.
Workflows need a visible revision to bind the replacement. There is no global
in-place package updater, credential cloning or automatic uncertain replay.

Owners reused: registry configuration import and install plans, onboarding,
server-scoped secrets, lifecycle/SseRunner, validation, existing workspace grants,
scoped native MCP tools and Connections UI. No new database or authentication
framework. Default provider-state reads continue to omit launch configuration;
the replacement tool is app-only and read-only.

Local component and owner checks cover absent credentials, forbidden scope,
operator authentication, configuration drift, private transport errors,
redirect/permission denial, cancellation, old-owner preservation and no implicit
workspace grant. Exact logs and subsequent actual-provider/browser receipts are
indexed under `/tmp/wright-desktop-resume-evidence-20261019`. Retain failures and
corrected continuations separately. Browser fixtures simulate the host frame;
none establish actual Windows rendering or personal SteveCAD account consent.
