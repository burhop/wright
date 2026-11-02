"""Isolated optional official SDK process. No Wright application imports.

The parent supplies a clean environment and fixed worker path. SDK call arguments
and returned notifications are observable here; provider-internal requests are not.
"""

from concurrent.futures import ThreadPoolExecutor
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import threading
import uuid

# -I omits the script directory; load the adjacent trusted policy explicitly.
import importlib.util

_policy_spec = importlib.util.spec_from_file_location(
    "wright_codex_policy", Path(__file__).with_name("codex_policy.py")
)
policy = importlib.util.module_from_spec(_policy_spec)
_policy_spec.loader.exec_module(policy)

MAX_BYTES = 2_097_152
_output_lock = threading.Lock()


def emit(value):
    raw = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if len(raw.encode("utf-8")) > MAX_BYTES:
        raise ValueError("Codex bridge record exceeds its bound")
    with _output_lock:
        print(raw, flush=True)


def wire(value):
    return (
        value.model_dump(mode="json", by_alias=True, exclude_none=True)
        if hasattr(value, "model_dump")
        else value
    )


def main():
    from openai_codex.client import CodexClient, CodexConfig
    from openai_codex.generated.v2_all import ConfigReadResponse

    if (
        importlib.metadata.version("openai-codex") != policy.SDK_VERSION
        or importlib.metadata.version("openai-codex-cli-bin") != policy.RUNTIME_VERSION
    ):
        raise ValueError("Codex SDK/runtime version differs from the qualified pair")
    config = CodexConfig(
        cwd=str(Path.cwd()),
        config_overrides=policy.CONFIG_OVERRIDES,
        client_name="wright_codex",
        client_title="Wright experimental Codex",
        experimental_api=True,
    )
    permission_failure = threading.Event()
    gateway_enabled = os.getenv("WRIGHT_CODEX_GATEWAY_ENABLED") == "1"
    gateway_pending = {}
    gateway_lock = threading.Lock()

    def deny(method, params):
        if (
            method == "item/tool/call"
            and gateway_enabled
            and policy.permitted_gateway_request(params)
        ):
            key = str(uuid.uuid4())
            ready, result = threading.Event(), {}
            with gateway_lock:
                if len(gateway_pending) >= 4:
                    return {"success": False, "contentItems": []}
                gateway_pending[key] = (ready, result)
            try:
                emit({"kind": "gateway_request", "id": key, "params": params})
                if not ready.wait(timeout=20):
                    return {"success": False, "contentItems": []}
                return result["value"]
            finally:
                with gateway_lock:
                    gateway_pending.pop(key, None)
        # Do not forward approval parameters: they may contain platform secrets.
        emit({"kind": "permission_denied", "method": method})
        try:
            return policy.deny_permission_request(method, params)
        except ValueError:
            permission_failure.set()
            raise

    with CodexClient(config=config, approval_handler=deny) as client:

        def global_notifications():
            try:
                while True:
                    event = client.next_notification()
                    emit(
                        {
                            "kind": "runtime_notice",
                            "method": event.method,
                            "params": wire(event.payload),
                        }
                    )
            except Exception:
                emit({"kind": "transport_error", "code": "CODEX_GLOBAL_STREAM_LOST"})

        threading.Thread(target=global_notifications, daemon=True).start()

        def stream(turn_id):
            try:
                while True:
                    event = client.next_turn_notification(turn_id)
                    emit(
                        {
                            "kind": "notification",
                            "method": event.method,
                            "params": wire(event.payload),
                        }
                    )
                    if event.method == "turn/completed":
                        break
            except Exception:
                emit({"kind": "transport_error", "code": "CODEX_EVENT_STREAM_LOST"})
            finally:
                client.unregister_turn_notifications(turn_id)

        def dispatch(message):
            request_id, method = message["id"], message["method"]
            params = message.get("params") or {}
            if method not in policy.RPC_METHODS or permission_failure.is_set():
                emit({"id": request_id, "error": {"code": "CODEX_METHOD_UNAVAILABLE"}})
                return
            try:
                params = policy.confined_rpc_params(method, params)
                if method == "thread/start" and gateway_enabled:
                    params["dynamicTools"] = [policy.GATEWAY_READ_TOOL]
                # This event marks entry to the SDK call, not provider acceptance.
                emit({"kind": "call_started", "id": request_id, "method": method})
                if method == "initialize":
                    response = client.initialize()
                elif method == "account/read":
                    response = client.account_read({"refreshToken": False})
                elif method == "model/list":
                    response = client.model_list()
                elif method == "config/read":
                    response = client.request(
                        method,
                        {"includeLayers": True},
                        response_model=ConfigReadResponse,
                    )
                elif method == "thread/start":
                    response = client.thread_start(params)
                elif method == "thread/resume":
                    response = client.thread_resume(params["threadId"], params)
                elif method == "thread/read":
                    response = client.thread_read(
                        params["threadId"], include_turns=True
                    )
                elif method == "thread/list":
                    response = client.thread_list(params)
                elif method == "thread/archive":
                    response = client.thread_archive(params["threadId"])
                elif method == "turn/start":
                    response = client.turn_start(
                        params["threadId"], params["input"], params
                    )
                elif method == "turn/interrupt":
                    response = client.turn_interrupt(
                        params["threadId"], params["turnId"]
                    )
                emit({"id": request_id, "result": wire(response)})
                if method == "turn/start":
                    threading.Thread(
                        target=stream, args=(response.turn.id,), daemon=True
                    ).start()
            except Exception:
                # Raw exception text can contain credentials or provider URLs.
                emit({"id": request_id, "error": {"code": "CODEX_RPC_FAILED"}})

        in_flight = threading.BoundedSemaphore(8)
        with ThreadPoolExecutor(max_workers=4) as executor:
            while True:
                raw = sys.stdin.buffer.readline(MAX_BYTES + 1)
                if not raw:
                    break
                if len(raw) > MAX_BYTES or not raw.endswith(b"\n"):
                    raise ValueError("Codex bridge input exceeds its bound")
                message = json.loads(raw)
                if isinstance(message, dict) and message.get("kind") == "gateway_reply":
                    if set(message) != {"kind", "id", "result"} or not isinstance(
                        message["id"], str
                    ):
                        raise ValueError("Invalid gateway reply")
                    result = message["result"]
                    if (
                        not isinstance(result, dict)
                        or set(result) != {"success", "contentItems"}
                        or type(result["success"]) is not bool
                    ):
                        raise ValueError("Invalid gateway outcome")
                    with gateway_lock:
                        pending = gateway_pending.get(message["id"])
                        if pending:
                            pending[1]["value"] = result
                            pending[0].set()
                    continue
                if not isinstance(message, dict) or set(message) - {
                    "id",
                    "method",
                    "params",
                }:
                    raise ValueError("Invalid Codex bridge request")
                if (
                    type(message.get("id")) is not int
                    or message["id"] < 1
                    or not isinstance(message.get("method"), str)
                    or not isinstance(message.get("params"), dict)
                ):
                    raise ValueError("Invalid Codex bridge request identity")
                if not in_flight.acquire(blocking=False):
                    emit(
                        {"id": message["id"], "error": {"code": "CODEX_REQUEST_LIMIT"}}
                    )
                    continue
                future = executor.submit(dispatch, message)
                future.add_done_callback(lambda finished: in_flight.release())


if __name__ == "__main__":
    try:
        main()
    except Exception:
        emit({"kind": "transport_error", "code": "CODEX_RUNTIME_UNAVAILABLE"})
        raise SystemExit(1)
