# Workspace Surfaces Research

**Date**: 2026-07-30  
**Scope**: primary-source standards research plus read-only repository discovery  
**Decision status**: all investigated choices are resolved

## Executive Findings

The proposed surface abstraction is viable, but it must not collapse materially different trust models into one iframe implementation. Wright needs one user-facing descriptor and lifecycle vocabulary backed by distinct execution profiles:

| Source | Correct profile | Active JavaScript | Privileged bridge | Panel eligibility |
|---|---|---:|---|---|
| Durable Python result | MIME renderer; isolated document only for explicit active HTML | Typed renderers only by default | Display update channel only | Yes |
| Existing workspace file | Compatibility viewer provider | Existing per-viewer policy | Existing provider contract | Yes |
| BREP/conventional server UI | Managed live application | Yes | Only declared, granted surface capabilities | Yes when isolated preview origin and framing policy allow; browser otherwise |
| Packaged MCP UI | Stable MCP Apps `ui://` resource | Yes, in mandated sandbox | Official App Bridge routed through Wright policy | Yes |
| WebMCP-aware page | Managed app plus scoped compatibility adapter; native draft when detected | Yes | Exact surface/origin/tool scope | Same as managed app |
| Arbitrary approved URL | Direct navigation only | Whatever the remote page runs | None | Browser-enforced iframe if allowed; always offer browser |

The novice graphics path should use MIME bundles and a tiny `wright.display` API rather than a custom canvas protocol. Typed Plotly data provides offline interactive graphs; Matplotlib/SVG/PNG cover durable static results; a managed app covers rich interaction. This combination is smaller, more accessible, and more interoperable than inventing a scene graph and draw/event RPC.

## Repository Discovery

### Existing strengths

- `packages/workspace_service` already owns workspace-scoped execution, process services, models, ports, use cases, adapters, and composition. It is the correct owner for surfaces and runtimes.
- `packages/tool_registry` already owns session/workspace-scoped MCP gateway, policy, audit, tool calls, and resources. It is the correct owner for child-server UI metadata/resources and app-originated tool policy.
- `packages/data_vault` and the existing SQLite/file-vault architecture satisfy the constitution's embedded persistence model.
- `apps/api` already composes these services and supplies authenticated FastAPI routers, SSE/gateway facilities, CORS/security middleware, and tracing.
- `apps/web` has a viewer registry, panel host, iframe provider, workspace tabs/layout, and browser/desktop host adapters that can be migrated incrementally.
- The packaged FastAPI application serves the Vite bundle, Docker builds the same artifact, Vite already proxies HTTP/WebSocket API traffic in development, and the release wheel can be extended to ship the public helper and UI assets.

### Gaps that drive the design

- Viewer selection and tab identity are path/file-oriented. The store normalizes every identity as a path, so it cannot represent an MCP URI, display result, two live app instances, or presentation identity safely.
- Only the active tab DOM is mounted; switching tabs disposes the host. JavaScript-heavy applications would lose browser-side state. A bounded retained surface deck is required.
- The current panel bridge validates `contentWindow` only and sends to `targetOrigin="*"`. It is not a security boundary for MCP Apps or WebMCP.
- The current iframe preview lacks a complete CSP, Permissions Policy, referrer policy, origin, and token contract. HTML is returned as JSON by the real file endpoint while an existing UI test mocks HTML, so a dedicated preview route is needed without changing editor semantics.
- Current WebMCP routing uses global window events with only call ID/method/params, includes a hard-coded demo handler, and is not wired as a production connection. It lacks workspace/session/surface/origin/tool binding.
- Current compatibility authentication projects every accepted local request as the `local-admin` principal. New records must nevertheless use the authenticated principal ID and an explicit engineer/admin authorization matrix so a future multi-principal implementation does not require a state-model rewrite; tests must cover both roles even while the default local deployment remains single-admin.
- Workspace layout persistence is unversioned, responsive mode hides the surface entirely below 768px, resize handles are pointer-only, and tabs lack tab semantics/keyboard navigation.
- Browser/desktop host adapters do not expose a guarded `openExternal` operation or an absolute surface-origin resolver. Desktop `file://` cannot be used as the active-content trust boundary.
- The MCP gateway needs to preserve child UI metadata and resource bodies. A UI resource can be addressable by `resources/read` even when omitted from `resources/list`, so list-only projection is insufficient.
- Existing Playwright configuration is Chromium-only and existing WebMCP tests cover only a single connection/call. Cross-browser presentation, simultaneous surface, isolation, teardown, desktop, and live transport coverage must be added.

## Protocol and Standards Decisions

### MCP Apps

Use the stable MCP Apps extension (2026-01-26), identifier `io.modelcontextprotocol/ui`. Revalidated against the official specification on 2026-07-30, it defines capability negotiation, `ui://` resources with media type `text/html;profile=mcp-app`, canonical tool `_meta.ui.resourceUri`, UI resource metadata, JSON-RPC over `postMessage`, visibility rules, and a distinct-origin double-iframe sandbox proxy for web hosts. The host fetches the referenced UI through `resources/read`; UI-only resources may be absent from list results. Wright should use version-pinned official `@modelcontextprotocol/ext-apps` types/AppBridge primitives and record the package version plus specification date in conformance evidence while owning the missing authorization, audit, resource scoping, cache, and lifecycle controls. [Stable MCP Apps specification](https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx), [official repository](https://github.com/modelcontextprotocol/ext-apps), [AppBridge API](https://apps.extensions.modelcontextprotocol.io/api/classes/app-bridge.AppBridge.html)

Compatibility rules:

- Negotiate and advertise UI support only when the host implementation is enabled.
- Read canonical nested `_meta.ui.resourceUri`; accept deprecated `_meta["ui/resourceUri"]`; emit only canonical metadata. [Compatibility key](https://apps.extensions.modelcontextprotocol.io/api/variables/app.RESOURCE_URI_META_KEY.html)
- Preserve tool and content-item UI metadata across every gateway boundary.
- Key resources internally by server connection/session plus URI and content hash; never let identical `ui://` strings collide across servers/workspaces.
- Preserve `resources/list`, templates, read, subscriptions, and update notifications; enforce URI validation and access control from MCP core. [MCP resources](https://modelcontextprotocol.io/specification/2025-11-25/server/resources)
- Default tool visibility to model+app. App-originated calls may use only same-server tools visible to the app; app-only tools remain outside the model list.
- Require useful non-UI fallback content and degrade when UI capabilities are absent.

External URL resources were deferred from the stable MCP Apps MVP. Consequently BREP or another conventional server is a `LiveAppSurface`, not an `McpAppSurface`, unless it publishes the packaged `ui://` contract.

### WebMCP

The WebMCP document dated 2026-07-28 was revalidated on 2026-07-30 as a Draft Community Group Report, explicitly not a W3C Standard or standards-track document. Its current imperative API is `document.modelContext`, with Promise-returning `registerTool`, `getTools`, `toolchange`, SecureContext/origin-keyed behavior, Permissions Policy feature `tools` with default allowlist `self`, and `exposedTo` controls. Declarative WebMCP and several same-origin/intent questions remain unsettled. Every test record must name the draft date, browser/build, feature-detected members and Permissions Policy result; native support is never inferred from browser brand. [Current WebMCP draft](https://webmachinelearning.github.io/webmcp/), [community repository](https://github.com/webmachinelearning/webmcp)

Wright will therefore:

- Publish a stable, versioned compatibility SDK using an abortable surface-scoped bridge.
- Route registrations and calls by `workspace_id + session_id + surface_id + document_origin + server_id + tool_name`.
- Validate schema, arguments, result, provenance, size/rate, grant, and trace context at the backend boundary.
- Tear down registrations on navigation, origin change, surface/session close, or abort.
- Feature-detect `document.modelContext?.registerTool`; dual-register only when a tested host adapter proves support.
- Never polyfill the standards namespace or assume a parent page can drive the browser agent's private consumer surface.
- Keep compatibility matrices pinned to tested draft/browser versions and guarantee the scoped fallback when native support is absent or changes.

### Browser isolation

An origin is scheme/host/port, not path. Combining `allow-scripts` and `allow-same-origin` is unsafe for a child sharing the embedder's origin; active children need a separate origin. `postMessage` requires exact target origins and validation of both `event.origin` and `event.source`. [MDN same-origin policy](https://developer.mozilla.org/en-US/docs/Web/Security/Defenses/Same-origin_policy), [MDN iframe](https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe), [MDN postMessage](https://developer.mozilla.org/en-US/docs/Web/API/Window/postMessage)

`frame-ancestors` and X-Frame-Options belong to the upstream response and must not be weakened. `frame-ancestors` checks every ancestor and cannot be supplied in a meta element. Iframe load/error signals cannot reliably prove cross-origin framing failure, so the panel needs an explicit browser fallback instead of pretending detection is perfect. [CSP frame-ancestors](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Content-Security-Policy/frame-ancestors), [X-Frame-Options](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options)

Permissions Policy is deny-by-default. Only manifest-declared, policy-allowed, user-granted features appear in iframe `allow`. [Permissions Policy](https://www.w3.org/TR/permissions-policy/)

Decisions:

- Never run active app/MCP/Python HTML on the Wright control-plane origin.
- Use a distinct effective hostname per managed app instance and MCP sandbox; different ports on one hostname do not isolate cookies.
- Present active surfaces over HTTP origins even in desktop mode; do not use opaque `file:` origins or wildcard messages as the boundary.
- Preserve upstream CSP/XFO and refuse panel presentation when policy prohibits embedding.
- Treat arbitrary approved URLs as direct, view-only navigation: no proxy, credentials, App Bridge, WebMCP adapter, or privileged message channel.

## Managed Application and Proxy Research

The proxy is a capability-bound reverse proxy, never a `proxy?url=` endpoint. A validated manifest or launch creates an immutable target pin containing numeric address, port, scheme, ownership proof, base path, and allowed public origin. Public routes expose only opaque instance/presentation IDs. No browser request can replace the upstream authority.

HTTP intermediaries must remove connection-specific fields, including fields named by the `Connection` header, and treat authority/Host as security-critical. WebSocket servers should validate Origin and preserve subprotocol/close semantics. SSE must stream `text/event-stream`, preserve `Last-Event-ID`, reconnect semantics, comments/heartbeats, and 204 termination. [RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html), [RFC 6455](https://www.rfc-editor.org/rfc/rfc6455.html), [WHATWG SSE](https://html.spec.whatwg.org/dev/server-sent-events.html)

OWASP recommends allowlisting known targets, validating all A/AAAA answers, defending against rebinding, and disabling automatic redirect following. [OWASP SSRF guidance](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)

Required proxy behavior:

- Wright-launched applications bind only to allocated `127.0.0.1`/`::1` endpoints. Attached targets require explicit declaration/approval, normalized DNS/IP validation, address-class policy, numeric pinning, and revalidation without authority changes.
- Never follow redirects automatically. Rewrite/relay only same-pinned-target redirects; reject cross-target redirects and offer browser navigation subject to policy.
- Set upstream Host from the target record. Strip Wright Authorization, cookies, CSRF, preview tokens, identity and forwarding headers plus all hop-by-hop headers.
- Put a single-use, short-lived, audience-bound bootstrap token in the URL fragment, which is not sent in HTTP. A restrictive bootstrap document POSTs the token body, exchanges it for a host-only HttpOnly/SameSite=Strict preview cookie (Secure when transport permits), clears the fragment and redirects to a clean URL. The token never reaches traced request URLs, Referer, target headers, or durable state.
- Validate the browser Origin on every WebSocket upgrade. Stream HTTP/SSE without whole-body buffering, propagate cancellation, and apply separate first-byte/idle deadlines.
- Proxy WebSocket text/binary frames, subprotocols, close codes/reasons, backpressure, cancellation, and limits.
- Preserve end-to-end response/security headers and host-scoped app cookies; reject attempts to escape the isolated preview origin.
- Bound app count, processes, memory/CPU where supported, connections, headers, bodies, frames, logs, restarts, streams, time, and update history.

FastAPI/Starlette already provide streaming response and ASGI WebSocket primitives suitable for an application adapter; they do not remove Wright's responsibility for protocol, policy, and cancellation correctness. [Starlette responses](https://www.starlette.io/responses/), [Starlette WebSockets](https://www.starlette.io/websockets/)

## Process Ownership and Cleanup

- POSIX launches use a new session/process group; graceful stop sends the declared signal to the group, waits a bounded interval, then escalates. `psutil` reconciles descendants, process creation time, ports, and leftovers.
- Windows launches use a Job Object with kill-on-job-close so descendants form one cleanup unit, with `psutil` reconciliation and explicit reporting for breakaway/assignment failures. [Windows Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects), [AssignProcessToJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject)
- Process identity is PID plus creation time, target ownership evidence, generation, and workspace/instance identity. A PID alone is never trusted after restart.
- On startup/recovery, Wright reconciles stale records and owned processes before allowing presentation. Unknown/unprovable processes are never silently adopted.
- The app's declared lifetime policy wins; when omitted, the clarified fallback is workspace lifetime. Closing a presentation and stopping a runtime remain distinct.

## Python Display Research

Jupyter's MIME bundle plus `display_id`/`update_display_data` model is a proven producer-neutral format for durable output and retained identity. IPython exposes `_repr_mimebundle_`; Plotly already serializes typed figures; Matplotlib can save PNG/SVG. [Jupyter messaging](https://jupyter-client.readthedocs.io/en/latest/messaging.html), [IPython formatters](https://ipython.readthedocs.io/en/8.24.0/api/generated/IPython.core.formatters.html), [Plotly renderers](https://plotly.com/python/renderers/), [Matplotlib savefig](https://matplotlib.org/stable/api/_as_gen/matplotlib.figure.Figure.savefig.html)

`wright.display(value, *, title=None, active_html=False, display_id=None)` will:

1. Apply explicit bounded adapters: Matplotlib to PNG/SVG, Plotly to typed JSON plus fallback, table-like objects to typed table+text, bytes/PIL to image, strings to text.
2. Then accept `_repr_mimebundle_` under strict media allowlists, time, depth, item, and byte limits.
3. Store immutable payload revisions in the vault and an indexed logical display record in SQLite.
4. Render typed Plotly with a version-pinned local JS bundle; no CDN.
5. Sanitize ordinary HTML using a bundled browser sanitizer and a locked renderer document. Producer MIME labels are not trust claims.
6. Require `active_html=True` for scripts; open it in a separate opaque/unprivileged surface with no Wright/MCP/WebMCP bridge.
7. Use an execution-scoped endpoint/token injected by the Wright runner, never a general workspace credential.
8. Provide `wright.line`, `wright.bar`, `wright.scatter`, and `wright.histogram` so the beginner example meets the one-import, ten-line requirement without an optional plotting package.

### Canvas decision

Do not introduce a Python `Canvas.drawLine()` protocol in this feature. HTML Canvas is bitmap-oriented and places accessibility fallback responsibility on the author, whereas SVG and typed chart renderers preserve semantic structure more naturally. [WHATWG Canvas](https://html.spec.whatwg.org/multipage/canvas.html), [SVG accessibility](https://www.w3.org/TR/SVG/access)

A retained-mode canvas would require a versioned scene graph, patches, hit testing, events, text/font rules, animation, resources, accessibility, quotas, and cross-language conformance. MIME/SVG/Plotly plus managed apps cover the stated needs. Reconsider only after two consecutive release cycles record at least three independent supported integrations that cannot meet a documented user journey with typed MIME/SVG/Plotly or a managed app, and an approved proposal demonstrates materially lower authoring complexity while defining scene versioning, patch/idempotency, events, accessibility fallback, quotas, offline rendering and cross-language conformance. Even then, the candidate is a bounded `application/vnd.wright.scene+json` document, not chatty primitive RPC.

## Framework Evaluation

The core must be framework-neutral: explicit argv (never a shell string), working directory, environment references, allocated port, loopback bind, base path, readiness probe, capability declarations, lifetime, limits, and log rules. `framework-conformance.md` fixes the placeholder-to-setting contract for pinned templates. Test/document these adapters without making their frameworks core dependencies:

- **FastAPI/Uvicorn**: baseline custom application, HTTP, WebSocket, and SSE fixture.
- **Panel**: strong novice dashboard template; configure exact address/port/base prefix/liveness/WebSocket origin, never wildcard origin. [Panel server CLI](https://panel.holoviz.org/how_to/server/commandline.html)
- **Streamlit**: configure allocated address/port/base path, headless mode, exact origin/CORS, XSRF enabled, upload/message limits, and health. [Streamlit configuration](https://docs.streamlit.io/develop/api-reference/configuration/config.toml)
- **Gradio**: `share=False`, loopback name, allocated port, root path, strict allowed/blocked paths, no browser auto-open. [Gradio launcher](https://www.gradio.app/main/docs/gradio/blocks)
- **Dash**: configure URL/request/route prefixes. [Dash reference](https://dash.plotly.com/reference)

Pyodide is deferred: workers cannot manipulate DOM directly, sockets/local files/subprocesses differ materially, and it would create a second Python/package runtime without solving BREP. [Pyodide worker model](https://pyodide.org/en/stable/usage/webworker.html), [limitations](https://pyodide.org/en/stable/usage/faq.html)

## Dependency Decisions

| Dependency | Decision | Reason/control |
|---|---|---|
| `@modelcontextprotocol/ext-apps` | Add, version-pinned | Official MCP Apps types and bridge; bundled and audited |
| `dompurify` | Add, version-pinned | Mature client-side HTML sanitizer; use only with locked renderer policy |
| `plotly.js-dist-min` | Add, version-pinned | Offline typed interactive renderer; lazy-load and performance-test |
| New server HTML sanitizer | Do not add initially | Sanitization occurs at the final browser rendering boundary; backend validates format/size and stores untrusted data as data |
| Panel/Streamlit/Gradio/Dash | Test extras/examples only | Generic manifest is core; avoid heavy framework coupling |
| Pyodide | Defer | Different runtime/package matrix and does not cover server apps |
| Custom canvas protocol | Reject for initial feature | Duplicates established document/rendering systems |

Dependency versions must be locked through the repository's normal lock/update process during implementation and validated for license, provenance, known vulnerabilities, offline bundling, and production artifact inclusion.

## Alternatives Rejected

- **One permissive iframe for every source**: conflates trust, loses MCP lifecycle/capability semantics, enables credential/message confusion, and cannot safely proxy arbitrary URLs.
- **General reverse proxy accepting a URL parameter**: creates SSRF/open-proxy and authority-confusion risk.
- **Run active HTML on the Wright origin**: permits same-origin credential/state access and sandbox removal.
- **Browser-only presentation**: breaks the chat+UI feedback loop and the core request.
- **Panel-only presentation**: fails sites that prohibit framing or need full browser behavior.
- **Treat BREP as an MCP App automatically**: MCP Apps stable MVP does not define conventional external-server resources.
- **Adopt native WebMCP as the contract**: current draft is unstable and unavailable across required browsers/desktop.
- **Destroy inactive surface DOM**: breaks stateful JavaScript applications and reconnect behavior.
- **Persist runtime tokens/PIDs as truth**: stale/reused identifiers create authority and recovery failures.

## Validation Implications

Release-blocking suites must cover resource metadata loss, UI resource read without list visibility, canonical/deprecated MCP metadata, wrong-origin/source/replayed/oversized messages, same-server app-tool rules, CSP and Permissions Policy defaults, WebMCP absence/change, DNS/IP/rebinding/redirect variants, HTTP duplicate/hop-by-hop headers, cookies, streaming, WebSocket frames and close propagation, SSE reconnection/204, frame refusal, cross-instance isolation, desktop `file://`, full process-tree cleanup, and beginner display safety/update/durability.
