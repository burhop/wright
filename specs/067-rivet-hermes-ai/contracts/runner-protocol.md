# Contract: Supervised Rivet Runtime Worker

The Python runtime host owns the process tree, Hermes compatibility bridge, path confinement, cancellation, limits, and secret redaction. The bundled Node worker owns Rivet project loading and graph execution.

## Invocation

```text
node <inventoried-wright-runner.mjs>
```

One JSON request is written to stdin, then stdin closes:

```json
{
  "protocolVersion": 1,
  "runId": "<uuid>",
  "projectPath": "<canonical server-selected workflow file>",
  "expectedDigest": "<sha256>",
  "graph": "Main",
  "inputs": {},
  "context": {},
  "ai": {
    "baseUrl": "http://127.0.0.1:<ephemeral>/v1",
    "token": "<ephemeral run token>",
    "model": "wright-hermes"
  },
  "capabilities": []
}
```

`projectPath`, AI endpoint, and capabilities are trusted host values, never copied from project data or public API input. The worker independently hashes the project before execution and fails if it differs.

## Stdout

Stdout is JSON Lines only. Each line is at most the configured event cap.

Progress:

```json
{"type":"progress","runId":"<uuid>","sequence":1,"kind":"graph-started","message":"Running Main"}
```

Success terminal (exactly once):

```json
{"type":"result","runId":"<uuid>","state":"succeeded","outputs":{},"usage":{},"timingMs":123}
```

Failure terminal (exactly once when the worker can report):

```json
{"type":"result","runId":"<uuid>","state":"failed","error":{"code":"RIVET_GRAPH_INVALID","message":"..."}}
```

Stderr is bounded diagnostic output, structured/redacted by the Python host, and never parsed as results.

## Cancellation and exit

- Closing/terminating the worker aborts the Rivet processor.
- Python first requests graceful termination, then enforces the existing deadline on the entire process tree.
- Exit `0` requires one successful terminal result.
- Nonzero exit, missing terminal result, invalid JSONL, sequence regression, run ID mismatch, or oversized output becomes a stable failed run.

## Capability defaults

Without explicit approved capabilities the worker registers the normal deterministic Rivet runtime and AI provider but denies arbitrary filesystem access, arbitrary network access, native APIs, external functions, code execution, user-interactive nodes, and direct MCP configuration. The worker reports required denied capabilities during validation or before their first use.
