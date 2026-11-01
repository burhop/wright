# Native editor discovery — 29 October 2026

The compiled native panel uses the same shared Add step palette as Hermes,
with a scoped MCP read adapter. The screenshot shows a labeled fixture server,
not a connected engineering provider. The test makes no tool invocation or source
save. The report records exact native resource bytes and calls.

40 component tests pass across native discovery/routing/editor and existing
Hermes HTTP discovery. Wrong requested session, mismatched returned scope,
invalid metadata and unavailable native discovery are rejected without HTTP
fallback. 16 Python bridge tests pass; only advertised tool metadata and matching
server names are returned, with no connection configuration or execution grant.
TypeScript and native build pass. Linux Chromium compiled-panel rendering passes;
Windows and installed candidate delivery remain unverified.

Reproduce using `native_readiness_acceptance.mjs` with a fresh output directory.
The unconfigured generic CAD step still needs an explicit safe configuration
path; adding a new MCP task does not configure that existing step. The palette's
legacy Add or enable a server link also needs native Connections navigation.
