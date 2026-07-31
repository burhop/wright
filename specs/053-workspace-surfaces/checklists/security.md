# Workspace Surfaces Security Requirements Checklist

**Purpose**: Challenge the completeness, clarity and auditability of the security requirements before implementation
**Created**: 2026-07-30
**Feature**: [spec.md](../spec.md)
**Depth**: formal security design/release review

## Trust Boundaries and Authority

- [x] CHK101 Does the design state that active content is untrusted regardless of workspace provenance and enumerate a distinct trust profile for safe MIME data, active HTML, managed apps, MCP Apps, WebMCP pages and arbitrary URLs? [Threat Model: Source Trust Profiles](../threat-model.md#source-trust-profiles)
- [x] CHK102 Is every authority-bearing operation bound to user, workspace, session, surface, instance/generation, exact origin and server/operation where applicable, with no friendly name, URI, path, PID, port or URL used as authorization identity? [Data Model: Identity and Scoping](../data-model.md#identity-and-scoping), [FR-002]
- [x] CHK103 Are declarations explicitly distinguished from grants, and are policy narrowing, user consent, risk-tier persistence, expiry and revocation semantics stated without allowing remembered consent to override policy? [Data Model: CapabilityGrant](../data-model.md#capabilitygrant), [FR-038], [FR-045]
- [x] CHK104 Are high-risk and mutating operations required to be operation- or instance-scoped by default while low-risk persistence is limited to exact user/workspace/source/version? [Clarifications](../spec.md#clarifications), [FR-038]

## Browser and Message Isolation

- [x] CHK105 Does the design require distinct effective hostnames rather than ports alone, explain the cookie consequence, prohibit active content on Wright's control origin and define a safe hosted/Docker fallback when an isolated origin is unavailable? [Plan: Architecture Decision 6](../plan.md#architecture-decisions), [Threat Model: Cross-origin escape](../threat-model.md#cross-origin-escape-and-credential-theft)
- [x] CHK106 Are iframe sandbox, CSP, Permissions Policy, referrer, popup/navigation and upstream XFO/`frame-ancestors` requirements explicit for every active-content profile, including the rule never to weaken upstream framing policy? [Threat Model: Security Headers](../threat-model.md#security-headers-and-browser-policy), [FR-035 through FR-037], [FR-042]
- [x] CHK107 Are both `event.origin` and `event.source`, exact outbound target origin, protocol/schema, surface/generation, correlation/replay/deadline, size/rate and teardown checks required for every privileged browser message? [Threat Model: Message spoofing](../threat-model.md#message-spoofing-confused-deputy-and-replay), [Surface Message Contract](../contracts/surface-message.schema.json)
- [x] CHK108 Is arbitrary URL behavior unequivocally limited to explicit per-instance direct-navigation/view-only presentation with no proxy, credentials, App Bridge, WebMCP or privileged `postMessage`? [Clarifications](../spec.md#clarifications), [Research: Browser isolation](../research.md#browser-isolation)
- [x] CHK109 Does the token design keep raw presentation credentials out of HTTP request URLs, logs and Referer by using fragment-to-body POST exchange, and define single use, TTL, audience, clean redirect, host-only cookie and revocation? [Data Model: Presentation](../data-model.md#presentation), [Threat Model: Credential leakage](../threat-model.md#credentialtoken-leakage)

## Network, Process and Data Security

- [x] CHK110 Is the preview data plane defined as capability-bound to an immutable numeric target pin, never an arbitrary URL, and are DNS/IP normalization, address classes, rebinding, redirects, Host/SNI and every reconnect/upgrade covered? [Research: Managed Application and Proxy](../research.md#managed-application-and-proxy-research), [FR-021], [FR-040]
- [x] CHK111 Are all Wright identity/authorization/cookie/CSRF/forwarded/proxy/hop-by-hop fields stripped before upstream, while target end-to-end semantics and security headers are preserved? [Threat Model: SSRF](../threat-model.md#ssrf-dns-rebinding-and-target-substitution), [FR-039 through FR-040]
- [x] CHK112 Are command launch requirements injection-safe (argv/no shell), minimally environmental, workspace-confined, loopback-only and tied to provable process/listener ownership? [Data Model: LiveAppManifest](../data-model.md#managed-app-declaration), [FR-018 through FR-020]
- [x] CHK113 Are POSIX process groups, Windows Job Objects, PID creation-time/generation verification, bounded escalation, unknown-process non-adoption and stale-startup reconciliation specified? [Research: Process Ownership](../research.md#process-ownership-and-cleanup), [Lifecycle: Startup Reconciliation](../lifecycle.md#startup-reconciliation)
- [x] CHK114 Are path traversal, symlink/reparse/ADS/UNC/drive escape, cross-workspace vault access, dangerous MIME and representation/decompression bounds all within the explicit requirements or existing preserved workspace-path contract? [Threat Model: File and workspace escape](../threat-model.md#file-and-workspace-escape), [Spec Edge Cases](../spec.md#edge-cases)

## Protocol and Evidence

- [x] CHK115 Are MCP resources and app tool calls scoped by server connection and session, including read-without-list, URI collisions, metadata preservation, visibility and meaningful fallback content? [Research: MCP Apps](../research.md#mcp-apps), [FR-028 through FR-031]
- [x] CHK116 Is native WebMCP explicitly non-authoritative/experimental, with exact scoped fallback, abort/navigation teardown, untrusted schema/description/result handling and protocol-version evidence? [Research: WebMCP](../research.md#webmcp), [FR-032 through FR-034]
- [x] CHK117 Are diagnostic/audit requirements explicit about stable codes, correlation/trace identity, decision provenance and mandatory redaction of credentials, secrets, sensitive queries and protected content? [Data Model: Diagnostics](../data-model.md#diagnostics-and-audit), [FR-044], [FR-049 through FR-050]
- [x] CHK118 Does the release gate require all hostile boundary cases, dependency/provenance scans, cross-platform containment evidence and zero successful critical cross-boundary attempts before default-on? [Threat Model: Release Security Gates](../threat-model.md#release-security-gates), [SC-008], [Policy Defaults](../policy-defaults.md)

## Notes

- Check each item only after the cited requirements are specific enough for an independent security reviewer to derive acceptance evidence without relying on implementation intent.
- Any ambiguity that could broaden target, origin, credential, process or tool authority is release-blocking and must be corrected in the spec/design before tasks are generated.
- Resolved 2026-07-30 after explicit identity/grant, preview, target, process, redaction, hostile-fixture, policy-default and release-gate review. This checks requirements quality only; implementation evidence remains `Planned` in `traceability.md`.
