"""A single fresh customer/evaluator turn over Codex app-server stdio.

The caller supplies an isolated command/environment and desktop tool callbacks.
This transport never provisions a VM or substitutes scripted customer actions.
Protocol inspected against the installed CLI's experimental JSON schemas and
https://learn.chatgpt.com/docs/app-server on 2026-10-25.
"""

from __future__ import annotations

import hashlib
import json
import os
import queue
import re
import signal
import subprocess
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


class AgentProtocolError(RuntimeError):
    """The server violated the narrow protocol or isolated-session contract."""


def redact_record(value):
    """Conservative transport-log filtering; caller also redacts guest captures."""
    if isinstance(value, dict):
        return {
            key: "[REDACTED]"
            if key.lower()
            in {
                "authorization",
                "access_token",
                "refresh_token",
                "id_token",
                "api_key",
                "password",
            }
            else redact_record(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_record(item) for item in value]
    if isinstance(value, str):
        if value.startswith("data:image/"):
            return {"image_data_sha256": hashlib.sha256(value.encode()).hexdigest()}
        value = re.sub(r"(?i)bearer\s+[A-Za-z0-9._~+/-]+=*", "Bearer [REDACTED]", value)
        value = re.sub(r"\bsk-[A-Za-z0-9_-]{16,}", "[REDACTED_API_KEY]", value)
        value = re.sub(
            r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b",
            "[REDACTED_JWT]",
            value,
        )
    return value


def normalize_tool_result(value: dict) -> dict:
    """Accept native contentItems or {text, image_url, success} shorthand."""
    if not isinstance(value, dict):
        raise AgentProtocolError("tool callback must return an object")
    success = value.get("success", True)
    if type(success) is not bool:
        raise AgentProtocolError("tool success must be boolean")
    items = value.get("contentItems")
    if items is None:
        items = []
        if "text" in value:
            items.append({"type": "inputText", "text": value["text"]})
        if "image_url" in value:
            items.append({"type": "inputImage", "imageUrl": value["image_url"]})
    if not isinstance(items, list) or not items:
        raise AgentProtocolError("tool result must have content")
    for item in items:
        if not isinstance(item, dict):
            raise AgentProtocolError("tool content item must be an object")
        if item.get("type") == "inputText" and isinstance(item.get("text"), str):
            continue
        if item.get("type") == "inputImage" and isinstance(item.get("imageUrl"), str):
            if not item["imageUrl"].startswith(
                ("data:image/png;base64,", "data:image/jpeg;base64,")
            ):
                raise AgentProtocolError(
                    "screenshots must be inline PNG/JPEG, not external URLs"
                )
            continue
        raise AgentProtocolError("only text and inline screenshot content supported")
    return {"success": success, "contentItems": items}


def run_agent(
    command: list[str],
    instructions: str,
    task: str,
    tools: list[dict],
    on_tool: Callable[[str, dict], dict],
    timeout_seconds: float,
    output_dir: str | Path,
    model: str = "gpt-6.1-sol",
    effort: str = "medium",
    *,
    env: dict | None = None,
    redact: Callable = redact_record,
    output_schema: dict | None = None,
    passive_observer: Callable | None = None,
) -> dict:
    """Run one ephemeral thread and preserve its terminal result and provenance.

    `command` must already enforce the caller's process isolation. No shell is
    used. Callbacks must independently bound/cancel guest actions: Python cannot
    safely cancel an in-flight external callback. On timeout the agent process
    group is stopped, and late callback results are never delivered to the model.
    Failed sessions remain failed; the client never retries a customer attempt.
    """
    if (
        not isinstance(command, list)
        or not command
        or not all(isinstance(x, str) for x in command)
    ):
        raise ValueError("command must be a nonempty argv list")
    if timeout_seconds <= 0:
        raise ValueError("timeout must be positive")
    if not instructions.strip() or not task.strip():
        raise ValueError("versioned instructions and customer task are required")
    if output_schema is not None and not isinstance(output_schema, dict):
        raise ValueError("output_schema must be a JSON schema object")
    names = set()
    for tool in tools:
        if (
            tool.get("type") != "function"
            or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", tool.get("name", ""))
            or tool["name"] in names
            or not isinstance(tool.get("inputSchema"), dict)
            or not isinstance(tool.get("description"), str)
        ):
            raise ValueError(
                "unique named dynamic function tools with schemas required"
            )
        names.add(tool["name"])
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    if any(root.iterdir()):
        raise ValueError(
            "agent output directory must be fresh; prior attempts are retained"
        )
    started = time.monotonic()
    deadline = started + timeout_seconds
    record = {
        "schema_version": 1,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "starting",
        "requested_model": model,
        "requested_effort": effort,
        "instructions_sha256": hashlib.sha256(instructions.encode()).hexdigest(),
        "task_sha256": hashlib.sha256(task.encode()).hexdigest(),
        "tool_names": sorted(names),
        "thread_id": None,
        "turn_id": None,
        "resolved_model": None,
        "resolved_effort": None,
        "provider": None,
        "usage": None,
        "upstream_revision": None,
        "output_schema_sha256": hashlib.sha256(
            json.dumps(output_schema, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        if output_schema is not None
        else None,
        "provenance_scope": "app-server observable routing/usage only; no provider-internal prompt claim",
        "isolation_scope": "caller-owned process/container; fresh ephemeral thread verified here",
    }
    transcript = (root / "transport.jsonl").open("x", encoding="utf-8")
    incoming: queue.Queue = queue.Queue()
    process = None
    final_messages = []
    next_id = 0

    def log(direction, message):
        # Do not collect hidden/internal reasoning or analysis summaries.
        method = message.get("method", "")
        item = message.get("params", {}).get("item", {})
        if "reasoning" in method.lower() or item.get("type") == "reasoning":
            return
        transcript.write(
            json.dumps(
                {
                    "elapsed_seconds": time.monotonic() - started,
                    "direction": direction,
                    "message": redact(message),
                }
            )
            + "\n"
        )
        transcript.flush()

    def send(message):
        log("client", message)
        process.stdin.write(json.dumps(message) + "\n")
        process.stdin.flush()

    def request(method, params):
        nonlocal next_id
        next_id += 1
        send({"id": next_id, "method": method, "params": params})
        return next_id

    def read_stream(stream, tag):
        try:
            for line in stream:
                incoming.put((tag, line))
        finally:
            incoming.put((tag + "_closed", None))

    def next_message():
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("customer turn deadline reached")
            try:
                tag, line = incoming.get(timeout=remaining)
            except queue.Empty as exc:
                raise TimeoutError("customer turn deadline reached") from exc
            if tag == "stderr":
                log("server_stderr", {"text": line.rstrip()})
                continue
            if tag == "stdout_closed":
                raise AgentProtocolError("app-server closed before terminal turn")
            if tag != "stdout":
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AgentProtocolError("app-server stdout is not JSONL") from exc
            if not isinstance(message, dict):
                raise AgentProtocolError("app-server message is not an object")
            log("server", message)
            return message

    def handle(message):
        method, params = message.get("method"), message.get("params", {})
        if method in {"item/started", "item/completed"}:
            item_type = params.get("item", {}).get("type")
            if item_type == "sleep":
                item = params["item"]
                duration = item.get("durationMs")
                if (set(item) != {"type", "id", "durationMs"}
                        or not isinstance(item.get("id"), str)
                        or type(duration) is not int or not 0 <= duration <= 60000
                        or params.get("threadId") != record["thread_id"]
                        or params.get("turnId") != record["turn_id"]):
                    raise AgentProtocolError("Invalid or out-of-budget native sleep notification")
                # Installed CLI schema: passive delay only, no shell/network/UI
                # access. The existing overall deadline remains authoritative.
                record.setdefault("native_pauses", []).append({
                    "item_id": item["id"], "boundary": method,
                    "duration_ms": duration, "elapsed_seconds": time.monotonic() - started,
                })
                if passive_observer:
                    passive_observer(method, duration)
                return False
            if item_type not in {
                "userMessage",
                "agentMessage",
                "functionCallOutput",
                "plan",
                "reasoning",
                "dynamicToolCall",
                "contextCompaction",
            }:
                raise AgentProtocolError(
                    f"unexpected built-in item in isolated session: {item_type}"
                )
        if method == "item/tool/call" and "id" in message:
            if (
                params.get("threadId") != record["thread_id"]
                or params.get("turnId") != record["turn_id"]
                or params.get("namespace") not in (None, "")
            ):
                raise AgentProtocolError("dynamic tool call belongs to another scope")
            name = params.get("tool")
            if name not in names:
                send(
                    {
                        "id": message["id"],
                        "result": {
                            "success": False,
                            "contentItems": [
                                {
                                    "type": "inputText",
                                    "text": "Unknown or unavailable tool.",
                                }
                            ],
                        },
                    }
                )
                raise AgentProtocolError(f"unknown dynamic tool: {name}")
            if not isinstance(params.get("arguments"), dict):
                raise AgentProtocolError("dynamic tool arguments must be an object")
            outcome: queue.Queue = queue.Queue()

            def invoke():
                try:
                    outcome.put((True, on_tool(name, params["arguments"])))
                except Exception as exc:
                    outcome.put((False, exc))

            threading.Thread(target=invoke, daemon=True).start()
            try:
                ok, value = outcome.get(timeout=max(0, deadline - time.monotonic()))
            except queue.Empty as exc:
                raise TimeoutError(
                    "deadline reached during guest tool callback"
                ) from exc
            if not ok:
                # Keep implementation traceback and credentials out of model context.
                error_type = type(value).__name__
                value = {
                    "success": False,
                    "text": "Desktop action failed; the controller recorded the failure.",
                }
                log("callback_error", {"error_type": error_type})
            send({"id": message["id"], "result": normalize_tool_result(value)})
        elif "id" in message and method:
            # No escalation, shell, interactive input or external approval grants.
            send(
                {
                    "id": message["id"],
                    "error": {
                        "code": -32601,
                        "message": "Request not available in this isolated observation.",
                    },
                }
            )
            raise AgentProtocolError(f"unexpected server request: {method}")
        elif method == "thread/tokenUsage/updated":
            if (
                params.get("threadId") == record["thread_id"]
                and params.get("turnId") == record["turn_id"]
            ):
                record["usage"] = params.get("tokenUsage")
        elif method == "turn/started":
            if params.get("threadId") == record["thread_id"]:
                received_id = params.get("turn", {}).get("id")
                if record["turn_id"] not in (None, received_id):
                    raise AgentProtocolError("unexpected concurrent turn")
                record["turn_id"] = received_id
        elif method == "item/completed":
            item = params.get("item", {})
            if (
                params.get("threadId") == record["thread_id"]
                and params.get("turnId") == record["turn_id"]
                and item.get("type") == "agentMessage"
                and item.get("phase") != "commentary"
            ):
                final_messages.append(item.get("text", ""))
        elif method == "turn/completed":
            if (
                params.get("threadId") != record["thread_id"]
                or params.get("turn", {}).get("id") != record["turn_id"]
            ):
                raise AgentProtocolError(
                    "terminal notification belongs to another scope"
                )
            record["turn_status"] = params["turn"].get("status")
            if record["turn_status"] != "completed":
                raise AgentProtocolError(f"customer turn ended {record['turn_status']}")
            return True
        return False

    def response(identity):
        while True:
            message = next_message()
            if message.get("id") == identity and "method" not in message:
                if "error" in message:
                    raise AgentProtocolError(
                        f"app-server request failed: {redact(message['error'])}"
                    )
                return message.get("result", {})
            handle(message)

    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
            env=env,
            start_new_session=True,
        )
        for stream, tag in ((process.stdout, "stdout"), (process.stderr, "stderr")):
            threading.Thread(
                target=read_stream, args=(stream, tag), daemon=True
            ).start()
        record["initialize"] = response(
            request(
                "initialize",
                {
                    "clientInfo": {"name": "wright_synthetic_beta", "version": "1"},
                    "capabilities": {"experimentalApi": True},
                },
            )
        )
        send({"method": "initialized", "params": {}})
        result = response(
            request(
                "thread/start",
                {
                    "model": model,
                    "cwd": "/tmp/customer",
                    "ephemeral": True,
                    "baseInstructions": instructions,
                    "developerInstructions": instructions,
                    "approvalPolicy": "never",
                    "sandbox": "read-only",
                    "environments": [],
                    "runtimeWorkspaceRoots": [],
                    "selectedCapabilityRoots": [],
                    "dynamicTools": tools,
                    "allowProviderModelFallback": False,
                    "config": {
                        "model_reasoning_effort": effort,
                        "features.shell_tool": False,
                        "features.multi_agent": False,
                        "web_search": "disabled",
                    },
                },
            )
        )
        record.update(
            thread_id=result.get("thread", {}).get("id"),
            resolved_model=result.get("model"),
            resolved_effort=result.get("reasoningEffort"),
            provider=result.get("modelProvider"),
            instruction_sources=result.get("instructionSources", []),
        )
        thread = result.get("thread", {})
        record["ephemeral"] = thread.get("ephemeral")
        record["resolved_cwd"] = result.get("cwd")
        if thread.get("ephemeral") is not True or thread.get("turns") != []:
            raise AgentProtocolError(
                "thread is not confirmed ephemeral with empty history"
            )
        if result.get("cwd") != "/tmp/customer":
            raise AgentProtocolError(
                "thread cwd differs from isolated customer directory"
            )
        if not record["thread_id"] or record["instruction_sources"]:
            raise AgentProtocolError(
                "thread lacks identity or inherited instruction files"
            )
        if result.get("model") != model or result.get("reasoningEffort") not in (
            None,
            effort,
        ):
            raise AgentProtocolError(
                "resolved model/effort differs from frozen request"
            )
        turn_params = {
            "threadId": record["thread_id"],
            "input": [{"type": "text", "text": task}],
            "model": model,
            "effort": effort,
            "summary": "none",
            "serviceTierForTurn": "default",
        }
        if output_schema is not None:
            turn_params["outputSchema"] = output_schema
        turn = response(request("turn/start", turn_params))
        returned_turn_id = turn.get("turn", {}).get("id")
        if record["turn_id"] not in (None, returned_turn_id):
            raise AgentProtocolError(
                "turn response conflicts with observed turn identity"
            )
        record["turn_id"] = returned_turn_id
        if not record["turn_id"]:
            raise AgentProtocolError("turn/start returned no turn identity")
        record["status"] = "running"
        if record.get("turn_status") != "completed":
            while not handle(next_message()):
                pass
        if not final_messages or not final_messages[-1].strip():
            raise AgentProtocolError("completed turn has no final customer report")
        record["status"] = "completed"
        record["final_text"] = redact(final_messages[-1])
        (root / "final.txt").write_text(record["final_text"], encoding="utf-8")
    except Exception as exc:
        record["status"] = "timed_out" if isinstance(exc, TimeoutError) else "failed"
        record["error"] = redact(str(exc))
    finally:
        if process is not None:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=3)
            record["process_exit_code"] = process.returncode
        record["elapsed_seconds"] = time.monotonic() - started
        record["finished_at"] = datetime.now(timezone.utc).isoformat()
        transcript.close()
        (root / "agent-result.json").write_text(
            json.dumps(redact(record), indent=2) + "\n", encoding="utf-8"
        )
    return record
