# Contract: Progress, Replay, and Diagnostics

## Progress phases

The stable phase vocabulary is:

- `planning`
- `capability_discovery`
- `solid_edge_creation`
- `saving`
- `verification`
- `result_transfer`
- `final_response`

Internal MCP-prefixed tool identifiers may be retained in redacted operator diagnostics but are not the sole user-facing label.

## Progress event

Each SSE `progress` event contains:

```json
{
  "eventIndex": 3,
  "turnId": "turn-id",
  "correlationId": "correlation-id",
  "phase": "solid_edge_creation",
  "status": "running",
  "label": "Creating a new Solid Edge part",
  "message": "Creating the new part and keeping it visible in Solid Edge.",
  "elapsedSeconds": 12.3,
  "phaseElapsedSeconds": 4.1,
  "operationRequestId": "optional-request-id",
  "heartbeat": true
}
```

Requirements:

1. The first planning event is buffered before waiting for agent/model output and is observable within 1 second under a healthy local API.
2. While work continues, the server emits a progress event at least every 10 seconds.
3. Phase elapsed and total elapsed values use monotonic time and never decrease.
4. A tool event updates the current phase and human label; heartbeats repeat that current phase rather than reverting to a generic identifier.
5. Failure/cancellation/timeout emits an actionable error plus terminal completion semantics.
6. If the agent returns no user-facing text after a successful tool, the stream emits a concise terminal result derived from safe structured result fields.
7. Progress values pass through shared redaction before buffering or logging.

## Reconnect/replay

The authenticated existing endpoint `GET /api/agent/chat/stream?session_id=<id>&after=<event-index>` attaches to an active or recently completed turn.

- `after=0` replays all retained events.
- A valid later index resumes with the next retained event.
- Event order and indices are stable across reconnects.
- The replay includes progress, content/result, error, and stream completion events.
- If the requested index predates bounded retention, return an explicit replay-reset/expired response; never silently omit terminal state.
- Replay retention is bounded by event count, byte count, and recent-completion TTL.

## Diagnostic records

For each gateway tool call, persist one `started` record followed by exactly one terminal record: `succeeded`, `failed`, `timed_out`, `cancelled`, or `denied`.

Required fields:

- event, turn, correlation, request, session, principal, and workspace identities;
- phase, operation, server, and tool name;
- allowed flag, reason code, policy version, and outcome;
- duration in milliseconds for terminal records;
- argument count, bounded timeout, request bytes, and redacted response bytes;
- redacted error type where applicable.

Forbidden fields:

- credentials, environment values, authorization headers;
- full arguments, recipe bodies, results, file contents, protocol frames;
- raw exception text that may contain secrets or paths outside the approved diagnostic shape.

## Diagnostic summary

The authenticated session-scoped diagnostics adapter returns:

```json
{
  "sessionId": "session-id",
  "turnId": "optional-turn-id",
  "summary": {
    "activeCalls": 0,
    "completedCalls": 1,
    "outcomes": {"succeeded": 1},
    "totalDurationMs": 1250,
    "averageDurationMs": 1250,
    "maximumDurationMs": 1250,
    "phaseTotalsMs": {"solid_edge_creation": 1000},
    "turnDurationMs": 1500,
    "attributedDurationMs": 1480,
    "attributionRatio": 0.9867
  },
  "active": [],
  "slowest": [],
  "events": []
}
```

The package service, not the FastAPI route, pairs records and computes summaries. Results are limited, sorted deterministically, redacted, and authorized to the bound principal/session.

## Child-process logging

- HTTP/API processes may emit structured JSON logs to stdout.
- STDIO MCP server stdout is exclusively MCP JSON-RPC framing.
- STDIO structured diagnostics are emitted to stderr.
- A configured slow-call threshold changes the event classification, not the captured data shape.
- Tests must exchange valid MCP messages while diagnostics are enabled and assert zero stdout contamination.

## Attribution acceptance

For each completed live turn:

`attributionRatio = min(1, attributedDurationMs / turnDurationMs)`

Named planning, discovery, Solid Edge execution, result transfer, and final-response intervals must explain at least 95% of total elapsed time. Overlapping child intervals are not double-counted in the attributed total.
