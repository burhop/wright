# Workspace Surfaces Protocol Contracts

This document adds transport semantics that JSON Schema/OpenAPI cannot express completely. Normative keywords apply to implementation and conformance fixtures.

## Preview Host Contract

### Routing

- A preview request arrives on an effective hostname bound to exactly one active presentation, such as `s-<opaque>.localhost` natively or `<opaque>.<configured-preview-domain>` when hosted. Port-only isolation is invalid.
- The preview router runs before the Wright control-plane/SPA router and MUST expose only `/__wright/bootstrap` plus the bound application root. `/api`, `/mcp`, control/static assets, another presentation host and unbound Host values MUST be denied without falling through.
- The hostname or host-routing table identifies the presentation. Client-controlled path/query/header/body values MUST NOT select a target, presentation, workspace, user or upstream authority.
- Root, deep links, relative/absolute assets and application routes are presented at the preview hostname root. The adapter maps them to the immutable target pin/base path and rewrites only same-target `Location` values when required.

### Bootstrap

1. The control plane returns `absoluteBootstrapUrl = <preview-origin>/__wright/bootstrap#<single-use-token>`.
2. Fragments are never transmitted in HTTP. The restrictive bootstrap document reads the fragment, immediately clears it with `history.replaceState`, and POSTs `{token}` to `/__wright/bootstrap` with `Referrer-Policy: no-referrer`.
3. The router verifies hash, single use, TTL, user/workspace/surface/instance/generation/presentation, exact Host and audience. Failure consumes or invalidates the attempt according to replay policy.
4. Success returns 204 with a random host-only HttpOnly SameSite=Strict cookie, Secure where transport supports it, `Path=/`, no Domain, and a lifetime no longer than the presentation. The script navigates to `/` only after success.
5. Raw tokens/cookies are excluded from persistence, structured attributes, traces, logs, diagnostics, errors and upstream requests. Logout, revocation, close, stop, generation replacement and workspace closure invalidate them within the specified bound.

The browser presentation uses the same flow. Electron/browser host adapters receive the authorized bootstrap URL and cannot substitute a destination.

### HTTP

- Preserve permitted methods, path, query, body, duplicate request headers and end-to-end headers. Support HEAD and declared OPTIONS; reject TRACE and undeclared methods. Relay permitted informational 1xx responses when the ASGI/server adapter exposes them (101 is governed by the WebSocket contract), preserve 204/304 no-body semantics, duplicate response headers such as Set-Cookie, compressed/chunked responses, cancellation and backpressure. If a platform adapter cannot surface a non-upgrade 1xx response, it must declare that deterministic limitation in the conformance matrix rather than synthesize or buffer it.
- Parse and remove `Connection` plus every nominated field and known hop-by-hop/proxy fields. Remove Wright Authorization/cookies/CSRF, all `X-Wright-*`, forwarding/identity and presentation fields. Upstream Host/SNI derive only from the target pin.
- Do not automatically follow redirects. Relay relative/same-pinned-target redirects after safe rewriting; reject every authority/address change and return a stable action that may offer policy-controlled browser navigation.
- Preserve upstream CSP, X-Frame-Options, content/security headers and cache semantics. Never weaken framing controls to make the panel work.
- Stream request/response bodies without whole-body buffering when supported, while enforcing the declared or `policy-defaults.md` header-count/header-byte, body, decoded/decompressed-body, rate, concurrency, first-byte, idle and total limits.
- Target cookies may be accepted only as host-scoped cookies for the isolated preview host. Reject/strip Domain escapes and attributes that would broaden another surface's authority; never forward Wright cookies.

### WebSocket

- Upgrade only when the manifest declares WebSocket and the browser `Origin` equals the presentation origin.
- Preserve requested/selected subprotocol semantics. Proxy text/binary messages, ordering, close code/reason and cancellation in both directions with the declared or `policy-defaults.md` message/total/rate/idle limits and backpressure.
- Re-authorize presentation/generation and reuse the same immutable target pin on every upgrade/reconnect. No URL or Host value can redirect the connection.
- Tear down both halves on revocation, presentation/runtime close, target identity loss, limit violation or peer disconnect; emit one redacted outcome.

### SSE

- Preserve `text/event-stream` bytes, comments/heartbeats, event IDs, retry fields and `Last-Event-ID` without proxy buffering.
- Preserve 204 termination. Distinguish first-byte, heartbeat/idle and optional total lifetime bounds. Cancel upstream promptly when the client disconnects or authority expires.

### Framing eligibility

Panel eligibility requires a distinct preview hostname and compatible upstream `frame-ancestors`/XFO/browser features. Wright can preflight declared/managed responses where safe but MUST NOT claim it can reliably diagnose every cross-origin iframe refusal. Browser action remains available when source policy permits.

## Managed App Contract

- The manifest validates against `live-app-manifest.schema.json`; validation is not authorization.
- `command.argv` is executed directly without shell interpretation. Only documented Wright placeholders may be interpolated (`WRIGHT_BIND_HOST`, `WRIGHT_PORT`, `WRIGHT_PUBLIC_ORIGIN`, `WRIGHT_BASE_PATH`, `WRIGHT_INSTANCE_ID`); unknown placeholders fail validation. Secret references resolve through the existing secret boundary and are never reflected.
- Launched applications bind to the allocated loopback endpoint. Attach mode requires explicit approval plus target/ownership policy and creates a pinned target; an arbitrary approved URL never enters this contract.
- Readiness must succeed before `ready`. Health can move `ready <-> unhealthy`; process/ownership loss fails the generation. A runtime generation is guarded by per-instance serialization/idempotency.
- Process ownership is POSIX group/session, Windows kill-on-close Job Object, container/remote adapter equivalent, plus PID creation time/executable/listener evidence where available. Stops are bounded graceful then escalated and reconciled.
- The app lifetime declaration wins; omission means workspace lifetime. Lease uses an absolute bounded deadline. Idle lifetime is refreshed only by defined application/presentation activity (authorized HTTP/WS/SSE or an active presentation heartbeat), never unrelated workspace/chat traffic. Presentation close and runtime stop are different operations. Endpoint reservation, listener proof, stop escalation, cleanup ordering and omitted resource/transport limits follow `policy-defaults.md`.
- Framework declarations remain generic manifests. Pinned FastAPI, Panel, Streamlit, Gradio and Dash templates translate only the common placeholders and settings in `framework-conformance.md`; the core does not infer or weaken per-framework security behavior.

## Python Producer Contract

Public API:

```python
wright.display(value, *, title=None, description=None, active_html=False,
               display_id=None, durability="durable") -> DisplayHandle
wright.line(*, x, y, title, x_label, y_label, description, display_id=None) -> DisplayHandle
wright.bar(...); wright.scatter(...); wright.histogram(...)
```

- Import has no process/server/network side effect. Optional adapters are lazy.
- `DisplayHandle` exposes stable surface/display/revision metadata and an explicit `update` convenience; it contains no reusable workspace credential.
- The runner injects endpoint, contract version and execution-scoped token. The helper may also accept an explicitly configured development endpoint, but never discovers or starts Wright implicitly.
- Adapters run in this order: Wright-native graph/table/image values; Matplotlib; Plotly; pandas/PIL; bounded `_repr_mimebundle_`; safe scalar/text fallback. Producer media labels do not grant execution.
- The serialized request validates against `display-envelope.schema.json`. Server-side limits and policy remain authoritative. Duplicate idempotency keys return the original revision; stale/lower revisions never replace current.
- Ordinary HTML is sanitized at the renderer boundary. `active_html=True` is an explicit isolated unprivileged profile, not a way to access the surface bridge.

## MCP Apps Host Contract

- Negotiate stable extension `io.modelcontextprotocol/ui` and MIME `text/html;profile=mcp-app` only when the full host/sandbox implementation is enabled.
- Preserve canonical tool/content UI metadata and accept deprecated inbound `ui/resourceUri` only as compatibility input. Preserve all MCP content blocks and result metadata.
- Resolve UI resources through exact child `resources/read` with `(gateway session, server connection, upstream URI)` identity even when omitted from list. Preserve templates/subscriptions/notifications and invalidate content-hash cache on updates.
- Use official extension protocol types/AppBridge lifecycle and the mandated distinct-origin double iframe. The outer sandbox proxy receives raw HTML, enforces validated restrictive-default CSP/Permissions Policy and creates the inner view; no message is delivered before initialization.
- Verify browser source/origin and the surface envelope, then route tool/resource/context/user-message operations through gateway authorization, cancellation and audit. An app may call only same-server tools with app visibility; app-only tools are not exposed to the model.
- Unsupported UI capability or resource/render failure shows meaningful fallback content and never broadens authority.

## WebMCP/Wright SDK Contract

- Wright's versioned SDK uses `surface-message.schema.json` and exact route identity `(principal, workspace, session, surface, instance generation, document origin, server, tool name)`; duplicate tool names in other surfaces do not collide.
- Registration is abortable and ends on abort, navigation, origin change, surface disposal, session/workspace close or runtime generation change. Pending calls are cancelled; late results are ignored/audited.
- Tool descriptions/schemas/arguments/results are untrusted, bounded and validated. Server-side policy/grants and user intent controls apply to every call.
- The SDK feature-detects the current draft at `document.modelContext?.registerTool` and may dual-register only under a tested host-adapter capability. It does not polyfill the standards namespace or depend on native invocation behavior.
- The deprecated global Wright WebMCP relay cannot carry privileged operations. It is gated for at most the documented compatibility release and then removed under `migration.md` criteria.

## Browser/Desktop Host Adapter

```typescript
interface SurfaceHostAdapter {
  resolveApiUrl(path: string): URL;
  acceptAbsolutePreviewUrl(url: URL): URL;
  openExternalAuthorized(url: URL): Promise<void>;
  surfaceCapabilities(): Promise<SurfaceHostCapabilities>;
}
```

- `acceptAbsolutePreviewUrl` accepts only a backend-issued URL matching configured preview-host policy; it never turns an arbitrary URL into one.
- Browser open uses normal safe navigation. Electron uses a narrow main-process IPC method, validates scheme/host against the issued presentation or explicitly approved direct URL, invokes `shell.openExternal`, and exposes no generic shell.
- Electron blocks/handles unexpected `will-navigate` and `window.open`, retains context isolation and renderer sandboxing, and does not expose the privileged preload object to child surface frames.
- Desktop `file:` is not an active-content/message origin. Absolute preview/control URLs come from the configured backend adapter and support HTTP/WebSocket regardless of the wrapper's document URL.

## Stable Error Families

| Family | Examples | Retry rule |
|---|---|---|
| `SURFACE_STATE_*` | invalid transition, stale generation, already stopping | Retry only after descriptor refresh/action change |
| `SURFACE_POLICY_*` | capability denied, source changed, presentation ineligible | No automatic retry |
| `SURFACE_TARGET_*` | prohibited address, ownership mismatch, redirect rejected | No automatic retry; user may inspect/browser-open if offered |
| `SURFACE_RUNTIME_*` | readiness timeout, process exit, cleanup incomplete | Retry/restart only when projected action permits |
| `SURFACE_PROTOCOL_*` | version/schema/visibility/origin/replay error | Fix integration; no authority fallback |
| `SURFACE_LIMIT_*` | body/frame/rate/time/process/log bound | Retry only after bounded input/policy change |
| `SURFACE_HOST_*` | browser unavailable, preview domain unavailable, frame policy | Use projected alternative action |

Every problem includes a safe message, stable code, retryability and correlation ID. It excludes raw credentials, sensitive URLs/content, target pins and internal-only identifiers.
