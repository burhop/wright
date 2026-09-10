# Web OpenSCAD relay follow-up

Reviewed 10 September 2026. Owner: Wright catalog maintainers. Next review:
10 October 2026.

The pinned `jherr/webmcp-openscad` commit
`a3acb68578701001f0251459c75716a55aadfa10` built successfully in a disposable
Wright-derived Intel Linux container. Headless Chromium loaded the page,
`navigator.modelContext.listTools()` returned all 16 documented tools, and the
OpenSCAD worker mounted 56 BOSL2 files.

The documented extension-free bridge did not complete. Pinned
`@mcp-b/webmcp-local-relay@5.1.0` initialized over stdio and exposed its four
management tools, but it did not attach the page. A subsequent MCP `tools/list`
still contained only those four tools, so `get_render_status` and the other 15
browser tools were unavailable to Wright. The gateway and STL artifact stages
were therefore not reached.

Reproduce with the exact versions in
`../evidence/curation-2026-09-10/webmcp-openscad-linux-x64.json`. Inspect the
relay embed WebSocket handshake, page origin, and current browser local-network
policy. Once the page attaches, require `get_render_status`, a small deterministic
render, STL export, independent mesh dimensions and volume, Wright gateway
invocation, controlled-error behavior, and clean browser/relay shutdown before
promotion.

Do not classify the browser page itself as broken: the page registered its full
WebMCP surface and started the OpenSCAD worker. The unresolved defect is the
documented browser-to-relay path used by external MCP clients.
