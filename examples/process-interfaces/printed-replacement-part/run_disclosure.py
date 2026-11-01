"""Stage an inspectable preparation snapshot through ordinary reference inputs."""

import hashlib
import json
from pathlib import Path


def stage_limits(sections):
    rows = []
    for section in sections:
        if section["kind"] != "task":
            continue
        fields = section["fields"]
        settings = fields.get("settings", {})
        kind = settings.get("authoring_template", "model")
        governed = {
            key: settings[key]
            for key in (
                "authoring_template",
                "timeout_seconds",
                "max_tool_calls",
                "validation",
            )
            if key in settings
        }
        row = {
            "step_id": section["id"],
            "title": fields["name"],
            "kind": kind,
            "estimate_seconds": None,
            "estimate_cost": None,
            "estimate_basis": "No measured duration or provider-price basis for this fresh run",
            "settings_sha256": hashlib.sha256(
                json.dumps(
                    governed,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode()
            ).hexdigest(),
        }
        if kind in {"mcp-task", "mcp-tool"}:
            seconds = settings.get("timeout_seconds", 300)
            if type(seconds) is not int or not 30 <= seconds <= 600:
                raise ValueError("Invalid declared tool timeout")
            row["timeout_seconds"] = seconds
            row["timeout_scope"] = "agent_loop" if kind == "mcp-task" else "tool_call"
            if kind == "mcp-task":
                maximum = settings.get("max_tool_calls", 8)
                if type(maximum) is not int or not 1 <= maximum <= 32:
                    raise ValueError("Invalid declared tool-call limit")
                row["max_tool_calls"] = maximum
        rows.append(row)
    return rows


def attach(flow, basis_review):
    rows = stage_limits(flow.sections)
    template = Path(__file__).with_name("run-disclosure-template.md").read_text()
    lines = []
    for row in rows:
        limit = (
            f"{row['timeout_seconds']} seconds per {row['timeout_scope'].replace('_', ' ')}"
            if "timeout_seconds" in row
            else "No tool deadline projected; inspect this block and its adapter"
        )
        if "max_tool_calls" in row:
            limit += f"; at most {row['max_tool_calls']} selected tool calls per attempt"
        lines.append(f"- **{row['title']}** (`{row['step_id']}`): {limit}.")
    reference = flow.input_bytes(
        "run-disclosure.md",
        template.format(stages="\n".join(lines)).encode(),
        title="Review intended work, limits and unknown estimates",
    )
    flow.reference(reference, basis_review, "work_and_limits")
    structured = flow.input_bytes(
        "run-disclosure.json",
        (json.dumps({"schema_version": 1, "stages": rows}, indent=2) + "\n").encode(),
        title="Exact block-limit snapshot",
    )
    flow.reference(structured, basis_review, "exact_block_limits")
