# User Story 3 test-first evidence

Recorded 2026-07-30 on branch `053-workspace-surfaces` before User Story 3
implementation.

## URL, IP, DNS, and immutable target policy

The test source passed Ruff before execution.

```text
uv run pytest packages/workspace_service/tests/surfaces/test_target_policy.py -q

1 collection error:
ModuleNotFoundError: No module named 'core.surfaces.network_values'
```

The missing pure network-value and workspace target-policy modules prove that
alternate address parsing, all-answer validation, rebinding rejection,
control-plane denial, Host/SNI derivation, and immutable numeric target pins
were not satisfied by an existing generic URL path.

## Preview bootstrap and host dispatch

The test source passed Ruff before execution.

```text
uv run pytest apps/api/tests/test_surface_preview_bootstrap.py -q

1 collection error:
ModuleNotFoundError: No module named 'api.routers.surface_preview'
```

No existing route could exchange a fragment-held token through a body,
atomically consume it, issue a host-only cookie, enforce TTL/audience/revocation,
or prevent a preview hostname from falling through to Wright control routes.

## Capability grants

The test source passed Ruff before execution.

```text
uv run pytest packages/workspace_service/tests/surfaces/test_capability_grants.py -q

1 collection error:
ModuleNotFoundError: No module named 'workspace_service.surfaces.grants'
```

The repository had persistence values but no policy service capable of enforcing
declared risk, exact principal/source scope, bounded persistence, transactional
operation consumption, revocation, or administrator-only decisions.

## Surface messages

The test source passed Ruff before execution.

```text
uv run pytest packages/workspace_service/tests/surfaces/test_surface_messages.py -q

1 collection error:
ModuleNotFoundError: No module named 'workspace_service.surfaces.messages'
```

No authenticated composite-bound router existed for schema, deadline,
generation, replay/idempotency, ordering, size/depth, rate, or cancellation
enforcement.

## Preview proxy security helpers

The test source passed Ruff before execution.

```text
uv run pytest apps/api/tests/test_surface_preview_security.py -q

1 collection error:
ModuleNotFoundError: No module named 'api.surface_proxy_security'
```

The API had no centralized boundary for stripping Wright/control/hop-by-hop
headers and cookies, containing target cookies, validating redirects against
the immutable pin, or preserving upstream framing and content policies.

## Browser policy projection

The test source passed Ruff before execution.

```text
uv run pytest packages/workspace_service/tests/surfaces/test_browser_policy.py -q

1 collection error:
ModuleNotFoundError: No module named 'workspace_service.surfaces.browser_policy'
```

No source-profile projector existed to distinguish inert active HTML, compatible
distinct-origin JavaScript applications, sandbox features, Permissions Policy,
navigation, popups, downloads, and direct-only external URLs.

## Centralized limits

The test source passed Ruff before execution.

```text
uv run pytest tests/security/test_surface_limits.py -q

1 collection error:
ModuleNotFoundError: No module named 'workspace_service.surfaces.limits'
```

There was no common most-restrictive policy composition and fail-closed
enforcement surface for request, message, stream, runtime, buffering, logging,
timeout, or degraded platform-limit decisions.

An expanded exhaustive pass then found the remaining unimplemented boundaries:

```text
uv run pytest tests/security/test_surface_limits.py -q

3 failed, 3 passed
- validate_response and validate_frame were absent
- admit_log_bytes was absent
- concurrent_starts was absent from runtime demand
```

## Security redaction

The test source passed Ruff, then exposed two concrete leaks:

```text
uv run pytest tests/security/test_surface_redaction.py -q

2 failed
- user_content and upstream_logs retained super-secret-value
- diagnostic Cookie: wright_surface=cookie-value retained cookie-value
```

Existing redaction covered bearer and explicit token/secret keys but not the
surface-specific target-pin, user-content, upstream-log, and cookie text forms.

## Coordinated revocation

The test source passed Ruff before execution.

```text
uv run pytest packages/workspace_service/tests/surfaces/test_revocation.py -q

1 collection error:
ModuleNotFoundError: No module named 'workspace_service.surfaces.revocation'
```

No single transaction coordinated presentation credential and grant invalidation
for logout, workspace closure, presentation disposal, or runtime replacement.

## Direct-only external URLs

The test source passed Ruff before execution.

```text
uv run pytest packages/workspace_service/tests/surfaces/test_external_urls.py -q

1 collection error:
ModuleNotFoundError: No module named 'workspace_service.surfaces.external_urls'
```

There was no exact-scope, expiring approval that guarantees an undeclared URL is
opened directly without Wright proxy, credential, bridge, or lifecycle authority.

## Browser bridge

The isolated Vitest file failed before implementation:

```text
npm run test -- src/services/surfaces/bridge/surface-bridge.spec.ts

Failed to resolve import "./surface-bridge"
```

No exact-origin/window/composite-binding bridge existed to reject sibling,
wildcard, stale-generation, malformed, oversized, or post-disposal messages.

## Capability consent UI

The isolated Vitest file failed before implementation:

```text
npm run test -- src/components/surfaces/CapabilityDialog.spec.tsx

Failed to resolve import "./CapabilityDialog"
```

No accessible consent surface disclosed the exact source/version, workspace,
operation, bounded data, risk, reason, effective policy, duration, persistence,
denial consequence, or distinct allow/deny/cancel decisions.

## External URL UI

The isolated Vitest file failed before implementation:

```text
npm run test -- src/components/surfaces/ExternalUrlSurface.spec.tsx

Failed to resolve import "./ExternalUrlSurface"
```

No browser-only host component prevented iframe promotion while clearly
disclosing the absence of proxy, credentials, tool bridge, and lifecycle authority.
