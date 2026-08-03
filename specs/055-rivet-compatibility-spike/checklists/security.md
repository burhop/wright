# Security Checklist: Rivet Compatibility Spike

**Purpose**: Confirm experimental probing cannot weaken Wright security boundaries.

- [x] No real workspace, user, session, token, credential, or engineering tool is used by the fixture.
- [x] Editor/runner/browser/debugger requests are bounded, synthetic, and redacted in evidence.
- [x] Workspace-safe per-instance provider isolation is a mandatory test, not an assumed property.
- [x] Direct MCP, arbitrary plugin install, filesystem access, code, and unrestricted network are classified explicitly.
- [x] Generated endpoint/capability values are not persisted in project files, logs, or URLs.
- [x] Offline request logs disclose no secrets and identify every attempted authority.
- [x] Cleanup targets only controlled spike assets and is proven non-destructive.
- [x] A failed mandatory boundary produces no-go rather than a security exception.
