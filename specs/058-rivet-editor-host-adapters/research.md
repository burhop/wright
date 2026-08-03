# Research

1. Use an opaque short-lived bootstrap grant: no workspace path, project,
dataset, secret, tool, or debugger authority is encoded client-side.
2. Reuse slice-056 workflow use cases so revision conflict and path confinement
have one implementation.
3. Keep distribution declarative until offline packaging is proven. Slice 055
selected Rivet 1.25.0 but its Windows cache lacks build dependencies; no CDN
fallback is allowed.
4. Do not expose Rivet debugger/native APIs. The spike found unauthenticated
debugger WebSockets; a future owned bridge requires separate policy work.
