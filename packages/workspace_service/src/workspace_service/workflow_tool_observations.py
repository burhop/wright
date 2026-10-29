"""Connected MCP observations, projected by the existing evidence owner.

This is transport evidence, not engineering validation or action authority.
The bounded task still owns dispatch, failures and completion decisions.
"""

import hashlib
import json

from .rivet_evidence import project_result_value


def _provider_result(value):
    """Decode JSON text envelopes before field redaction; omit opaque text bodies."""
    if not isinstance(value, dict) or not isinstance(
        value.get("content"), (list, tuple)
    ):
        return value
    content = []
    for item in value["content"]:
        if isinstance(item, dict) and item.get("type") == "text":
            text = item.get("text", "")
            try:
                parsed = json.loads(text) if len(text) <= 262_144 else None
            except (ValueError, TypeError):
                parsed = None
            if isinstance(parsed, (dict, list)):
                content.append({"type": "json", "value": parsed})
            else:
                content.append(
                    {
                        "type": "text",
                        "body": "not retained",
                        "sha256": hashlib.sha256(str(text).encode()).hexdigest(),
                        "evidence_state": "not-retained",
                    }
                )
        else:
            content.append(item)
    return {**value, "content": content}


def response_from_observations(server_id: str, calls: list[dict]) -> str:
    """Keep actual call order/identity; never use a model summary as tool output."""
    observed = []
    for index, call in enumerate(calls, 1):
        record = {
            "call_number": index,
            "tool": call.get("tool"),
            "schema_digest": call.get("schema_digest"),
            "status": call.get("status"),
            "arguments": call.get("arguments"),
            "result": _provider_result(call.get("result")),
        }
        text = call.get("text")
        if text:
            try:
                duplicate = len(text) <= 262_144 and json.loads(text) == call.get(
                    "result"
                )
            except (ValueError, TypeError):
                duplicate = False
            if not duplicate:
                record["supplementary_response"] = _provider_result(
                    {"content": [{"type": "text", "text": text}]}
                )
        observed.append(record)
    projection = project_result_value(
        observed,
        name="tool_calls",
        origin=server_id,
        maximum_bytes=262_144,
    )
    if any(
        isinstance(value, dict)
        and isinstance(value.get("content"), (list, tuple))
        and any(
            isinstance(item, dict) and item.get("evidence_state") == "not-retained"
            for item in value["content"]
        )
        for record in observed
        for value in (record["result"], record.get("supplementary_response"))
    ):
        projection.update(
            complete=False,
            value=None,
            evidence_state="not-retained",
            truncation_reason="opaque_text_omitted",
        )
    return json.dumps(
        {
            "schema_version": "wright.mcp-tool-observations/1",
            "server_id": server_id,
            "call_count": len(calls),
            "observations": projection,
        },
        sort_keys=True,
    )
