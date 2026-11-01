"""Real isolated Wright SDK bridge lifecycle with an unauthenticated local fixture.

Run using Wright's feature-worktree Python, supplying the isolated pinned SDK
interpreter. This does not send a live OpenAI request or use a Wright gateway.
An output directory must be fresh. Windows process containment remains unqualified.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from agent_adapters.codex_transport import CodexRuntimeSettings, CodexSdkTransport


async def qualify(output: Path, sdk_python: Path):
    captured = []
    in_flight = threading.Event()
    release = threading.Event()
    evidence = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            size = int(self.headers["Content-Length"])
            if size > 2_097_152 or len(captured) >= 2:
                self.send_error(400)
                return
            captured.append(json.loads(self.rfile.read(size)))
            item = {
                "type": "message",
                "id": "bridge-fixture-message",
                "role": "assistant",
                "status": "completed",
                "content": [
                    {
                        "type": "output_text",
                        "text": "bridge fixture complete",
                        "annotations": [],
                    }
                ],
            }
            events = [
                {
                    "type": "response.created",
                    "response": {
                        "id": "bridge-fixture-response",
                        "status": "in_progress",
                        "output": [],
                    },
                },
                {"type": "response.output_item.done", "output_index": 0, "item": item},
                {
                    "type": "response.completed",
                    "response": {
                        "id": "bridge-fixture-response",
                        "status": "completed",
                        "output": [item],
                    },
                },
            ]
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            try:
                for index, event in enumerate(events):
                    self.wfile.write(("data: " + json.dumps(event) + "\n\n").encode())
                    self.wfile.flush()
                    if len(captured) == 2 and index == 0:
                        in_flight.set()
                        release.wait(timeout=10)
            except (BrokenPipeError, ConnectionResetError):
                pass

    async def observe(record):
        evidence.append(record)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    home = output / "home"
    home.mkdir(mode=0o700)
    endpoint = f"http://127.0.0.1:{server.server_port}/v1"
    # Only a fresh fixture home is configured. Never copy a personal config/auth file.
    (home / "config.toml").write_text(
        'model_provider="qualification"\n[model_providers.qualification]\n'
        'name="local bridge fixture"\nwire_api="responses"\n'
        f'base_url="{endpoint}"\nrequires_openai_auth=false\n'
        "request_max_retries=0\nstream_max_retries=0\n"
    )
    settings = CodexRuntimeSettings(output, python=sdk_python, timeout_seconds=15)
    identity = {
        "model": "gpt-6.1-sol",
        "baseInstructions": "Local bridge qualification input.",
        "developerInstructions": "Local bridge qualification instructions.",
    }
    client = CodexSdkTransport(settings, observer=observe)
    restarted = None
    try:
        await client.start()
        config_before = (await client.request("config/read", {}))["config"]
        assert not (await client.request("account/read", {})).get("account")
        started = await client.request("thread/start", identity)
        thread_id = started["thread"]["id"]
        first = await client.request(
            "turn/start",
            {
                "threadId": thread_id,
                "model": identity["model"],
                "input": [{"type": "text", "text": "Local bridge fixture."}],
            },
        )
        first_events = [event async for event in client.events(first["turn"]["id"])]
        assert first_events[-1]["params"]["turn"]["status"] == "completed"
        await client.close()

        restarted = CodexSdkTransport(settings, observer=observe)
        await restarted.start()
        config_after = (await restarted.request("config/read", {}))["config"]
        assert config_before == config_after
        history = await restarted.request("thread/read", {"threadId": thread_id})
        assert [turn["status"] for turn in history["thread"]["turns"]] == ["completed"]
        resumed = await restarted.request(
            "thread/resume", {"threadId": thread_id, **identity}
        )
        assert resumed["thread"]["id"] == thread_id
        second = await restarted.request(
            "turn/start",
            {
                "threadId": thread_id,
                "model": identity["model"],
                "input": [{"type": "text", "text": "Cancellation fixture."}],
            },
        )
        assert await asyncio.to_thread(in_flight.wait, 5)
        ack = await restarted.request(
            "turn/interrupt", {"threadId": thread_id, "turnId": second["turn"]["id"]}
        )
        second_events = [
            event async for event in restarted.events(second["turn"]["id"])
        ]
        terminal = second_events[-1]["params"]["turn"]["status"]
        assert terminal == "interrupted"
        after = await restarted.request("thread/read", {"threadId": thread_id})
        statuses = [turn["status"] for turn in after["thread"]["turns"]]
        assert statuses == ["completed", "interrupted"]
        report = {
            "schema": "wright.codex-bridge-qualification/1",
            "result": "PASSED_LOCAL_BRIDGE_LIFECYCLE",
            "live_openai_request": False,
            "authenticated": False,
            "same_thread_on_resume": True,
            "resolved_configuration_unchanged": True,
            "configuration_sha256": hashlib.sha256(
                json.dumps(config_before, sort_keys=True).encode()
            ).hexdigest(),
            "interruption_acknowledgement": ack,
            "persisted_terminal_statuses": statuses,
            "capture_scopes": sorted({record["capture_scope"] for record in evidence}),
            "no_tools_qualified": False,
            "gateway_qualified": False,
        }
        (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        (output / "sdk-call-evidence.json").write_text(
            json.dumps(evidence, indent=2) + "\n"
        )
        (output / "fixture-provider-requests.json").write_text(
            json.dumps(captured, indent=2) + "\n"
        )
        print(json.dumps(report, indent=2))
    finally:
        release.set()
        await client.close()
        if restarted:
            await restarted.close()
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sdk-python", type=Path, required=True)
    args = parser.parse_args()
    if os.name == "nt":
        raise SystemExit("Windows process-tree containment is not qualified")
    output = args.output.absolute()
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    asyncio.run(qualify(output, args.sdk_python.absolute()))


if __name__ == "__main__":
    main()
