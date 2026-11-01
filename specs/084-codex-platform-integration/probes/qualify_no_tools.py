"""Bounded local negative control against the pinned real Codex runtime.

No OpenAI request, authentication, shell invocation, file edit, agent spawn or
Wright engineering run occurs. A loopback Responses fixture asks the runtime to
execute only collaboration.list_agents. An executed result fails qualification.
Run with the isolated SDK interpreter; output must be a new evidence directory.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def load_policy():
    path = (
        Path(__file__).resolve().parents[3]
        / "packages/agent_adapters/src/agent_adapters/codex_policy.py"
    )
    spec = importlib.util.spec_from_file_location("wright_probe_policy", path)
    policy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(policy)
    return policy, hashlib.sha256(path.read_bytes()).hexdigest()


def event_stream(output, response_id):
    return [
        {
            "type": "response.created",
            "response": {"id": response_id, "status": "in_progress", "output": []},
        },
        {"type": "response.output_item.done", "output_index": 0, "item": output},
        {
            "type": "response.completed",
            "response": {
                "id": response_id,
                "status": "completed",
                "output": [output],
                "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            },
        },
    ]


def worker(output: Path, mode: str):
    from openai_codex.client import CodexClient, CodexConfig
    from openai_codex.generated.v2_all import ConfigReadResponse

    policy, policy_digest = load_policy()
    versions = {
        name: importlib.metadata.version(name)
        for name in ("openai-codex", "openai-codex-cli-bin")
    }
    if versions != {
        "openai-codex": policy.SDK_VERSION,
        "openai-codex-cli-bin": policy.RUNTIME_VERSION,
    }:
        raise ValueError("Pinned runtime/client pair required")
    captured = []
    approvals = []
    cancellation_request_received = threading.Event()
    release_response = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            size = int(self.headers["Content-Length"])
            if size > 2_097_152 or len(captured) >= 3:
                self.send_error(400)
                return
            captured.append(json.loads(self.rfile.read(size)))
            if len(captured) == 1 and mode == "no-tools":
                item = {
                    "type": "function_call",
                    "id": "qualification-item",
                    "call_id": "qualification-call",
                    "name": "list_agents",
                    "namespace": "collaboration",
                    "arguments": "{}",
                }
            else:
                item = {
                    "type": "message",
                    "id": "qualification-final",
                    "role": "assistant",
                    "status": "completed",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "fixture complete",
                            "annotations": [],
                        }
                    ],
                }
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            try:
                for index, event in enumerate(
                    event_stream(item, "qualification-response")
                ):
                    self.wfile.write(("data: " + json.dumps(event) + "\n\n").encode())
                    self.wfile.flush()
                    if mode == "lifecycle" and len(captured) == 2 and index == 0:
                        cancellation_request_received.set()
                        release_response.wait(timeout=10)
            except (BrokenPipeError, ConnectionResetError):
                pass  # Expected if the cancelled real runtime closes its request.

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    endpoint = f"http://127.0.0.1:{server.server_port}/v1"
    config = CodexConfig(
        cwd=str(output / "cwd"),
        experimental_api=True,
        config_overrides=policy.CONFIG_OVERRIDES
        + (
            'model_provider="qualification"',
            "model_providers.qualification="
            + json.dumps(
                {
                    "name": "local qualification fixture",
                    "base_url": endpoint,
                    "wire_api": "responses",
                    "requires_openai_auth": False,
                    "request_max_retries": 0,
                    "stream_max_retries": 0,
                }
            ).replace(": ", " = "),
        ),
    )

    def deny(method, params):
        approvals.append(method)
        return policy.deny_permission_request(method, params)

    try:
        with CodexClient(config, approval_handler=deny) as client:
            client.initialize()
            account_present = bool(client.account_read().account)
            resolved = client.request(
                "config/read",
                {"includeLayers": True},
                response_model=ConfigReadResponse,
            ).model_dump(mode="json", by_alias=True)
            started = client.thread_start(
                {
                    "model": "gpt-6.1-sol",
                    "baseInstructions": "Local qualification input.",
                    "developerInstructions": "Local qualification instructions.",
                    "environments": [],
                    "allowProviderModelFallback": False,
                    "approvalPolicy": "never",
                    "sandbox": "read-only",
                }
            )
            turn = client.turn_start(
                started.thread.id,
                "Return a short text response.",
                {"environments": [], "model": "gpt-6.1-sol"},
            )
            while True:
                notification = client.next_turn_notification(turn.turn.id)
                if notification.method == "turn/completed":
                    terminal = notification.payload.turn.status.value
                    break
        lifecycle = {}
        if mode == "lifecycle":
            with CodexClient(config, approval_handler=deny) as restarted:
                restarted.initialize()
                read = restarted.thread_read(started.thread.id, include_turns=True)
                persisted_first = read.thread.turns
                if (
                    len(persisted_first) != 1
                    or persisted_first[0].status.value != "completed"
                ):
                    raise ValueError("Completed turn was not preserved across restart")
                resumed = restarted.thread_resume(
                    started.thread.id,
                    {
                        "model": "gpt-6.1-sol",
                        "baseInstructions": "Local qualification input.",
                        "developerInstructions": "Local qualification instructions.",
                        "approvalPolicy": "never",
                        "sandbox": "read-only",
                    },
                )
                if resumed.thread.id != started.thread.id:
                    raise ValueError("Resume substituted the thread")
                second = restarted.turn_start(
                    resumed.thread.id,
                    "Cancellation fixture.",
                    {"environments": [], "model": "gpt-6.1-sol"},
                )
                if not cancellation_request_received.wait(timeout=5):
                    raise ValueError(
                        "Cancellation fixture did not observe the in-flight request"
                    )
                interrupted_ack = restarted.turn_interrupt(
                    resumed.thread.id, second.turn.id
                )
                while True:
                    notification = restarted.next_turn_notification(second.turn.id)
                    if notification.method == "turn/completed":
                        interrupted_status = notification.payload.turn.status.value
                        break
                after = restarted.thread_read(resumed.thread.id, include_turns=True)
                lifecycle = {
                    "same_thread_on_resume": True,
                    "completed_turn_persisted_after_restart": True,
                    "first_terminal_status": terminal,
                    "interruption_acknowledgement": interrupted_ack.model_dump(
                        mode="json"
                    ),
                    "interrupted_terminal_status": interrupted_status,
                    "persisted_terminal_statuses": [
                        turn.status.value for turn in after.thread.turns
                    ],
                }
                if interrupted_status != "interrupted":
                    raise ValueError(
                        "Cancellation did not reach an interrupted terminal outcome"
                    )
    finally:
        release_response.set()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    capture_path = output / "fixture-provider-requests.json"
    capture_path.write_text(json.dumps(captured, indent=2) + "\n")
    tool_results = [
        item
        for request in captured[1:]
        for item in request.get("input", [])
        if item.get("type") == "function_call_output"
        and item.get("call_id") == "qualification-call"
    ]
    executed = any('"agents"' in str(item.get("output", "")) for item in tool_results)
    report = {
        "schema": "wright.codex-local-qualification/1",
        "versions": versions,
        "policy_sha256": policy_digest,
        "provider_requests_sha256": hashlib.sha256(
            capture_path.read_bytes()
        ).hexdigest(),
        "boundary": "local fixture provider requests plus actual runtime tool result",
        "live_openai_request": False,
        "credentials_present": account_present,
        "configured_mcp_servers": len(
            resolved.get("config", {}).get("mcp_servers", {})
        ),
        "fixture_request_count": len(captured),
        "approval_methods": approvals,
        "terminal_status": terminal,
        "adversarial_tool": "collaboration.list_agents",
        "adversarial_tool_results": tool_results,
        "no_tools_qualified": False,
        "probe": mode,
        "lifecycle": lifecycle,
        "result": (
            "PASSED_LOCAL_LIFECYCLE"
            if mode == "lifecycle"
            else "FAILED_EXECUTABLE_TOOL"
            if executed
            else "INCONCLUSIVE"
        ),
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if mode == "lifecycle" else 2 if executed else 3


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=("no-tools", "lifecycle"), default="no-tools")
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    output = args.output.absolute()
    if args.worker:
        return worker(output, args.mode)
    if os.name == "nt":
        print("INCONCLUSIVE: native Windows process-tree cleanup is not qualified")
        return 3
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name in ("home", "cwd"):
        (output / name).mkdir(mode=0o700)
    env = {"PATH": os.defpath, "CODEX_HOME": str(output / "home")}
    if os.name == "nt":
        for name in ("SystemRoot", "SYSTEMROOT", "WINDIR"):
            if name in os.environ:
                env[name] = os.environ[name]
    process = subprocess.Popen(
        [
            sys.executable,
            "-I",
            str(Path(__file__).resolve()),
            "--worker",
            "--mode",
            args.mode,
            "--output",
            str(output),
        ],
        cwd=output / "cwd",
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=45)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
        (output / "worker.stdout.txt").write_text(stdout)
        (output / "worker.stderr.txt").write_text(stderr)
        print("INCONCLUSIVE: bounded qualification timed out; no capability enabled")
        return 3
    (output / "worker.stdout.txt").write_text(stdout)
    (output / "worker.stderr.txt").write_text(stderr)
    print(stdout or "INCONCLUSIVE: inspect retained worker diagnostics")
    return process.returncode


if __name__ == "__main__":
    raise SystemExit(main())
