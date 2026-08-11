# Contract: Rivet AI Compatibility Bridge

The bridge is loopback-only and hosted on the same origin as the pinned Rivet iframe. Paths outside this contract are rejected or handled by the existing static host.

## `GET /wright-ai/config`

Response `200`, `Cache-Control: no-store`:

```json
{
  "available": true,
  "provider": "custom",
  "model": "wright-hermes",
  "baseUrl": "/wright-ai/v1",
  "token": "<short-lived opaque editor token>",
  "expiresAt": "2026-08-05T12:34:56Z"
}
```

Unavailable response remains `200` with `available: false`, no token, and a stable non-secret reason code. The browser must not be prompted for another provider key.

## `POST /wright-ai/v1/chat/completions`

Required headers:

```text
Authorization: Bearer <editor token>
Content-Type: application/json
```

Supported request subset:

```json
{
  "model": "wright-hermes",
  "messages": [{"role": "user", "content": "..."}],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "safe_unique_name",
        "description": "...",
        "parameters": {"type": "object"}
      }
    }
  ],
  "tool_choice": "auto",
  "parallel_tool_calls": false,
  "stream": true
}
```

Rules:

- Unknown top-level model-tuning fields may be ignored only if Rivet sends them and tests prove compatibility; authority-bearing fields are rejected.
- Tool names are unique and match a bounded safe identifier.
- Only function tools are accepted.
- The bridge returns at most one tool call for Rivet's legacy Graph Builder loop.
- The supplied model is an alias, not a provider selector.
- Body, messages, tools, schema depth, output, and duration are bounded.

Non-streaming tool response:

```json
{
  "id": "chatcmpl-<id>",
  "object": "chat.completion",
  "created": 0,
  "model": "wright-hermes",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": null,
        "tool_calls": [
          {
            "id": "call_<id>",
            "type": "function",
            "function": {"name": "safe_unique_name", "arguments": "{\"key\":\"value\"}"}
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ]
}
```

Streaming responses use standard `data:` Chat Completion chunks and `[DONE]`. Tool-call argument fragments follow OpenAI-compatible delta shape. Hermes-specific progress may be mapped to comments or a separate safe event only when Rivet's client tolerates it; it must never corrupt standard SSE parsing.

Errors use an OpenAI-style envelope with stable codes such as `invalid_token`, `invalid_request`, `unsupported_tool_contract`, `hermes_unavailable`, `hermes_auth_failed`, `translation_invalid`, `upstream_timeout`, and `cancelled`. Messages are redacted.

## Translation invariant

For tool-bearing requests, the bridge sends Hermes a canonical prompt containing conversation text, the allowed tool names/descriptions/schemas, the requested choice, and an instruction to return exactly one JSON object:

```json
{"kind":"tool_call","name":"allowed_name","arguments":{}}
```

or, when tools are optional:

```json
{"kind":"message","content":"..."}
```

The bridge parses JSON without executing it, verifies `name` belongs to the request, validates `arguments` against that tool's schema, and only then emits the OpenAI-compatible response. Markdown fences, extra prose, unknown tools, multiple calls, or invalid arguments fail closed.
