"""Deterministic single-tool engineering MCP subprocess fixture."""

from __future__ import annotations

import argparse
import copy
import json
import sys
import threading

from workspace_service.engineering_scenario_catalog_service import fixture_documents
from workspace_service.engineering_scenario_artifacts import artifact_content_digest


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--server", required=True)
    parser.add_argument("--tool", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--profile",
        choices=(
            "success",
            "delay",
            "malformed_artifact",
            "unit_mismatch",
            "domain_failure",
            "cleanup_residue",
        ),
        default="success",
    )
    parser.add_argument("--delay-seconds", type=float, default=5.0)
    return parser.parse_args()


def _profile_artifact(artifact: dict, profile: str) -> dict:
    result = copy.deepcopy(artifact)
    if profile == "malformed_artifact":
        result.pop("source_schema", None)
    elif profile == "unit_mismatch":
        first_unit = next(iter(result.get("units", {})), None)
        if first_unit:
            result["units"][first_unit] = "s"
    elif profile == "domain_failure":
        content = result.get("content", {})
        if "converged" in content:
            content["converged"] = False
        elif "degenerate_faces" in content:
            content["degenerate_faces"] = 1
        elif "root" in content:
            content["root"] = "invalid_board"
        elif "branches" in content:
            content["branches"] = list(reversed(content["branches"]))
        elif "relationships_valid" in content:
            content["relationships_valid"] = False
        elif "program" in content:
            content["program"] += "\nM3 S1000"
        else:
            for key, value in content.items():
                if isinstance(value, (int, float)):
                    content[key] = value * 1_000_000
                    break
        result["content_digest"] = artifact_content_digest(content)
    return result


def _tool_result(artifact: dict, profile: str) -> dict:
    result = {
        "content": [
            {
                "type": "text",
                "text": f"generated:{artifact.get('artifact_id', 'malformed')}",
            }
        ],
        "structuredContent": {"artifact": artifact},
    }
    if profile == "cleanup_residue":
        result["structuredContent"]["cleanup"] = {
            "state": "residue",
            "kinds": ["temporary_file"],
            "recovery": "Inspect and remove the bounded disposable fixture residue.",
        }
    return result


def main() -> None:
    settings = _arguments()
    artifact = _profile_artifact(
        next(
            value
            for value in fixture_documents(settings.scenario, run_id=settings.run_id)
            if value["producer"]["capability"] == f"{settings.server}__{settings.tool}"
        ),
        settings.profile,
    )
    output_lock = threading.Lock()
    pending: dict[object, threading.Event] = {}

    def send(response: dict) -> None:
        with output_lock:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()

    def delayed_call(request_id: object) -> None:
        cancelled = pending[request_id].wait(max(0.0, settings.delay_seconds))
        pending.pop(request_id, None)
        if cancelled:
            send(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32800, "message": "Request cancelled"},
                }
            )
            return
        send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": _tool_result(artifact, settings.profile),
            }
        )

    for raw in sys.stdin:
        try:
            request = json.loads(raw)
        except (TypeError, ValueError):
            continue
        method = request.get("method")
        if method == "notifications/cancelled":
            cancelled_id = request.get("params", {}).get("requestId")
            event = pending.get(cancelled_id)
            if event is not None:
                event.set()
            continue
        request_id = request.get("id")
        if request_id is None:
            continue
        if method == "initialize":
            result = {
                "protocolVersion": "2025-06-18",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": f"wright-engineering-{settings.server}",
                    "version": "1.0",
                },
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": settings.tool,
                        "title": f"{settings.server} deterministic fixture",
                        "description": "Wright-generated engineering scenario artifact",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"fixture": {"type": "string"}},
                            "required": ["fixture"],
                            "additionalProperties": False,
                        },
                        "outputSchema": {
                            "type": "object",
                            "properties": {"artifact": {"type": "object"}},
                            "required": ["artifact"],
                        },
                    }
                ]
            }
        elif method == "tools/call":
            progress_token = (
                request.get("params", {}).get("_meta", {}).get("progressToken")
            )
            if progress_token is not None:
                send(
                    {
                        "jsonrpc": "2.0",
                        "method": "notifications/progress",
                        "params": {
                            "progressToken": progress_token,
                            "progress": 0.5,
                            "total": 1,
                            "message": f"{settings.server} fixture working",
                        },
                    }
                )
            if settings.profile == "delay":
                pending[request_id] = threading.Event()
                threading.Thread(
                    target=delayed_call,
                    args=(request_id,),
                    daemon=True,
                ).start()
                continue
            result = _tool_result(artifact, settings.profile)
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": "Method not found"},
            }
            send(response)
            continue
        response = {"jsonrpc": "2.0", "id": request_id, "result": result}
        send(response)


if __name__ == "__main__":
    main()
