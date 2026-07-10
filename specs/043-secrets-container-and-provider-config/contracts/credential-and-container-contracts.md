# Contracts: Credentials and Container Security

## Settings read contract

Authenticated administrative reads return non-secret preferences plus a credential-status map. Each credential reports `configured` and may report a non-sensitive source. Stored values are never returned. Legacy `api_keys` values are not echoed; compatibility clients receive empty/masked data only during the documented transition.

## Settings write contract

Writes may set or explicitly remove named credentials. Omitted credentials remain unchanged. Empty or masked placeholder values never overwrite an existing credential accidentally. Non-secret preferences retain current response shapes.

## MCP credential contract

Existing save/delete/status operations remain available through the registry service. Status reports booleans per required variable. Reads of raw values remain package-internal and occur only when constructing a child process environment.

## Git execution contract

Git remotes and argv contain no credential. Authentication material is supplied through a short-lived helper environment, removed after the process exits, and redacted from all returned errors. Existing success/error response shapes remain compatible.

## Logging contract

All sinks receive redacted events. Credential-shaped keys are replaced with `[REDACTED]`; registered values are replaced even under unknown keys. MCP transport logs include operation metadata only, not raw JSON-RPC bodies or child stderr.

## Migration contract

Upgrade creates a restricted backup, imports known plaintext credentials, verifies them, and clears plaintext transactionally. Any error prevents readiness for affected operations and provides a redacted recovery command. Restore is explicit and backup-driven.

## Container contract

The default appliance runs non-root, has no sudo/default secret, drops capabilities, prevents privilege escalation, and persists only Wright-owned data paths. A separately named legacy Compose file may mount the old volumes for one migration release and must not be used by default documentation or CI smoke commands.
