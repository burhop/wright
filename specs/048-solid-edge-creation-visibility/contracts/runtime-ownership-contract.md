# Contract: Solid Edge Runtime Ownership

## Owner modes

Exactly one component owns a configured local SolidEdgeMCP subprocess:

- `api`: Wright API/lifecycle coordinator may start, reconcile, stop, and restart the child.
- `external`: Hermes or another explicitly configured host owns the child; Wright API is passive.

The current compatibility environment setting `WRIGHT_API_MCP_AUTOSTART=0` selects external ownership. Implementation may introduce a typed owner setting, but compatibility behavior must remain explicit and fail closed for invalid values.

## API-owned behavior

When mode is `api`:

- API lifespan may reconcile configured active servers.
- Workspace activation/update may request lifecycle reconciliation.
- Status reads may consult the API-owned coordinator.
- Per-server lifecycle locks/generations from Feature 046 prevent duplicate API-owned runners.

## External/Hermes-owned behavior

When mode is `external`:

- API lifespan does not start or reconcile MCP child servers.
- Agent-turn preparation does not start MCP child servers.
- Workspace activation/update does not start, stop, or reconcile MCP child servers.
- Passive workspace/UI status polling does not mutate lifecycle state.
- The API may read persisted configuration/audit state and expose authenticated passive diagnostics.
- Hermes owns launch, shutdown, and failure recovery for its child process.

## Ownership transition

Changing owner is an operator action:

1. Stop the old owner's child and verify it is inactive.
2. Change the explicit owner configuration.
3. Start the new owner.
4. Verify one matching child process and one usable gateway session.

Automatic ownership takeover or process killing is prohibited.

## Authenticated bridge queries

Hermes bridge requests to protected Wright API routes send:

```text
Authorization: Bearer <WRIGHT_API_TOKEN>
```

The token is read at call time, never included in query strings or logs, and is not cached in diagnostic records. Missing or invalid authentication returns the API's protected error; it does not downgrade to anonymous access.

## Acceptance evidence

Repeated workspace activation and UI polling while Hermes owns SolidEdgeMCP must show:

- one owner and one child process;
- no API lifecycle start/stop/reconcile call;
- successful authenticated passive queries;
- no MCP protocol parse error;
- clean owner shutdown without the API killing an unowned process.

The evidence may use a fake process counter in CI and a Windows process/handle count in the operator-invoked live smoke.
