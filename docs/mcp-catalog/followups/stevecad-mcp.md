# SteveCAD MCP qualification

Recorded 11 October 2026. Source: [official MCP documentation](https://stevecad.studio/docs/agents/).

Wright connects to `https://stevecad.studio/mcp` using its existing streamable-HTTP
runner and OAuth 2.1 browser authorization. This is STEVE Studio's hosted server,
not the separate Fusion STEVE add-in or a VibeCAD repository inferred from a name.
No vendor software belongs in Wright's base image.

Public resource discovery succeeded on Windows. Its issuer is
`https://auth.stevecad.studio/realms/users`; unauthenticated tool metadata returned
401. This establishes the endpoint and authentication boundary, not MCP/backend
qualification. Published tool references report account-scoped CAD source,
geometry inspection, STEP/mesh exports, and revision-bound studies. Live tools and
account limits must be discovered after authorization. Hosted licensing and
commercial-use terms remain unverified; no purchase is authorized or claimed.

Native qualification now passed: Wright's registry/installer and existing OAuth
runner connected to **STEVE CAD 4.0.10**, initialized MCP 2025-11-25, discovered
26 tools, and called `list_skills` and `api_reference`. Wright's existing gateway
listed 26 prefixed tools and proxied `api_reference(name="Model.box")` successfully.
Redacted receipts are in `docs/mcp-catalog/evidence/stevecad-2026-10-11/`.
This proves connection and read-only provider use, not CAD correctness.

The disposable coupon build/export and subsequent block workflow now have
separate evidence. Consult the [usage guide](../usage-guides/stevecad-mcp.md) before
new work; it links the actual outputs, practices and remaining capability limits.
Report native Windows and clean Linux container evidence separately. A browser
session alone does not authorize an MCP client; never copy session cookies.

Read [provider agent guidance](https://stevecad.studio/docs/agents/working-with-steve/)
before modifying documents. Download/upload tickets stay out of evidence. Human
share-link decisions, settings and manufacturing reference acceptance remain
with the user, as required by that guidance.
