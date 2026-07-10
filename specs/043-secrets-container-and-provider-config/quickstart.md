# Quickstart: Feature 043 Verification

1. Create isolated temporary database, workspace, secret store, and log paths.
2. Seed representative legacy global API keys, a Git token, MCP credentials, and integration auth.
3. Run the credential migration and verify a restricted backup exists.
4. Read settings/status endpoints and scan database, API payloads, logs, argv captures, and generated configuration for the seeded values; expect zero matches.
5. Run concurrent fallback-store writers and verify every update is present in valid storage.
6. Execute a fake Git remote operation and assert the remote URL/argv are clean while askpass receives the credential.
7. Exercise MCP startup and errors; verify child environment receives required credentials while logs remain redacted.
8. Render/inspect default Compose configuration and run the container smoke gate where available; verify non-root execution, no default key/sudo, restricted privileges, and only documented volumes.
9. Exercise migration restore and the legacy Compose transition instructions.
10. Run focused suites, leak scanners, strict docs build, and `scripts/check-dev-merge.sh` before review.
