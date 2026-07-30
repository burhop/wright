# Managed Framework Conformance Contract

The managed-app core is framework-neutral. Framework adapters are versioned
examples/test extras that translate the same manifest placeholders and never
add framework branches to `core`, the preview router, or lifecycle state.

## Common Adapter Contract

Wright resolves these placeholders before executing the manifest argv:

| Placeholder | Meaning |
|---|---|
| `WRIGHT_BIND_HOST` | Allocated numeric loopback address; never `0.0.0.0` |
| `WRIGHT_PORT` | Race-safe allocated port |
| `WRIGHT_PUBLIC_ORIGIN` | Exact per-instance preview origin accepted by the host adapter |
| `WRIGHT_BASE_PATH` | Normalized public prefix; `/` for the preferred root-host mode |
| `WRIGHT_INSTANCE_ID` | Non-secret instance correlation value, not authority |

The application must use relative URLs or the injected base path for HTML,
assets, redirects, WebSocket, and SSE. It must accept only the exact injected
public origin for browser-origin checks, retain CSRF protection, expose a
bounded readiness endpoint, avoid auto-opening a browser, and load no
undeclared CDN/remote asset. Wright still strips untrusted forwarding/identity
headers and does not make a framework proxy-aware by forwarding client input.

Every shipped template must pass root/deep-link, asset, redirect, cookie,
upload/body-limit, WebSocket, SSE where supported, readiness/health, shutdown,
offline, and two-instance collision tests through the real preview origin. A
framework/version for which the pinned template no longer passes is reported as
unsupported; Wright does not weaken origin, CSRF, framing, or path controls to
make it pass.

## Pinned Template Requirements

| Framework | Required adapter settings |
|---|---|
| FastAPI/Uvicorn | Bind `--host ${WRIGHT_BIND_HOST}` and `--port ${WRIGHT_PORT}`; set ASGI/FastAPI `root_path` from `WRIGHT_BASE_PATH`; generate external links from `WRIGHT_PUBLIC_ORIGIN` or relative paths; expose `/health`; do not trust arbitrary forwarded hosts; use explicit WebSocket Origin validation. |
| Panel/Bokeh | `panel serve APP --address ${WRIGHT_BIND_HOST} --port ${WRIGHT_PORT} --prefix ${WRIGHT_BASE_PATH} --allow-websocket-origin <host[:port] from WRIGHT_PUBLIC_ORIGIN> --liveness --liveness-endpoint health`; do not use `--show`, wildcard WebSocket origins, or development autoreload; keep XSRF cookies enabled for mutating handlers. |
| Streamlit | Set `server.address`, `server.port`, `server.baseUrlPath`, and exact `server.corsAllowedOrigins` from the injected values; set `server.headless=true`, `server.enableCORS=true`, `server.enableXsrfProtection=true`, `server.fileWatcherType=none`; cap `server.maxUploadSize` and `server.maxMessageSize` at the effective Wright policy and retain compatible WebSocket ping settings. |
| Gradio | Call `launch(server_name=WRIGHT_BIND_HOST, server_port=int(WRIGHT_PORT), root_path=WRIGHT_BASE_PATH, share=False, inbrowser=False, strict_cors=True, allowed_paths=<explicit minimum>, blocked_paths=<workspace/vault deny set>, max_file_size=<effective policy>)`; never create a public share tunnel; keep monitoring/SSR/external theme behavior disabled unless explicitly declared and tested. |
| Dash | Bind the server to the injected host/port; set `url_base_pathname` (or mutually consistent `requests_pathname_prefix` and `routes_pathname_prefix`) from `WRIGHT_BASE_PATH`; set `serve_locally=True`; prohibit undeclared external scripts/styles/assets; disable debug/hot reload/browser auto-open; provide an explicit health route and build redirects from relative paths or `WRIGHT_PUBLIC_ORIGIN`. |

The exact optional package versions live in the test-extra lock and are recorded
with conformance evidence. Configuration keys are revalidated against their
official documentation whenever that lock changes: [FastAPI proxy/root path](https://fastapi.tiangolo.com/advanced/behind-a-proxy/),
[Panel server CLI](https://panel.holoviz.org/how_to/server/commandline.html),
[Streamlit configuration](https://docs.streamlit.io/develop/api-reference/configuration/config.toml),
[Gradio launch](https://gradio.app/docs/gradio/blocks), and
[Dash reference](https://dash.plotly.com/reference).

## BREP and Unknown Frameworks

BREP uses the generic manifest unless a dedicated companion adapter is needed.
That adapter supplies the same host, port, public-origin, base-path, readiness,
health, lifetime, capability, and limit inputs; it does not receive a privileged
proxy exception. Unknown frameworks use `framework: generic` and must pass the
same HTTP/live-transport conformance fixture before panel eligibility. Browser
presentation may remain available when the app cannot satisfy panel framing or
origin requirements.
