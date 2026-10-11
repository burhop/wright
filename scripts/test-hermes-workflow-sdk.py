"""Offline stock Hermes SDK qualification with synthetic loopback responses.

Run with the installed Wright Python, selecting a qualified Hermes Python/root
through HERMES_ROLE_PYTHON and HERMES_ROLE_RUNTIME_ROOT. No model credits, MCP
operations, global profile edits or external network requests are used.
"""

import asyncio
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import tempfile
import threading


def main():
    repository = Path(__file__).resolve().parents[1]
    for package in ("core", "agent_adapters"):
        sys.path.insert(0, str(repository / "packages" / package / "src"))
    from agent_adapters.workflow_sdk import (
        workflow_sdk_capabilities,
        workflow_sdk_completion,
    )
    from agent_adapters.report_generation import generate_workflow_response
    from agent_adapters.hermes_openai_bridge import (
        HermesOpenAICompatibilityBridge,
        HermesOpenAIBridgeSettings,
    )
    from agent_adapters.workflow_model_routing import ModelRouteChangedError

    requests = []
    mode = "text"

    class Fixture(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            request = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(request)
            if mode == "text":
                content = json.dumps(
                    {
                        "version": "wright.unattended-step/1",
                        "status": "completed",
                        "reason": None,
                        "response": "Isolated transport report",
                    }
                )
            elif mode == "tool":
                content = json.dumps(
                    {
                        "kind": "tool_call",
                        "name": "inspect",
                        "arguments": {"part": "exact-part"},
                    }
                )
            else:
                content = None
            value = {
                "id": "synthetic-sdk-proof",
                "object": "chat.completion",
                "created": 1,
                "model": "synthetic-model-revision",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": content},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 17,
                    "completion_tokens": 8,
                    "total_tokens": 25,
                },
            }
            raw = json.dumps(value).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    runtime_python = os.environ["HERMES_ROLE_PYTHON"]
    runtime_root = os.environ["HERMES_ROLE_RUNTIME_ROOT"]
    with tempfile.TemporaryDirectory(prefix="wright-stock-sdk-proof-") as home:
        os.environ.update(
            HERMES_HOME=home,
            HERMES_PROFILE="wright",
            WRIGHT_HERMES_PROFILE="wright",
            HERMES_ROLE_PYTHON=runtime_python,
            HERMES_ROLE_RUNTIME_ROOT=runtime_root,
            WRIGHT_WORKFLOW_MODEL_TRANSPORT="hermes-model-sdk",
            CUSTOM_API_KEY="fake-offline-test-secret",
        )
        paths = [Path(home) / "config.yaml", Path(home) / "profiles/wright/config.yaml"]

        def write_config(model):
            text = (
                "model:\n  default: "
                + model
                + "\n  provider: custom\n  base_url: http://127.0.0.1:"
                + str(server.server_port)
                + "/v1\n  api_key: fake-offline-test-secret\n"
            )
            for path in paths:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)

        write_config("synthetic-model")

        async def proof():
            nonlocal mode
            route = (await workflow_sdk_capabilities())["resolution"]
            assert route["model_reference"] == "synthetic-model"
            assert not requests
            evidence = []

            async def observe(record):
                evidence.append(record)

            result = await generate_workflow_response(
                "Inspect this isolated digital fixture",
                "text",
                expected_resolution=route,
                images=[
                    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl2exUAAAAASUVORK5CYII="
                ],
                invocation_observer=observe,
            )
            assert (
                str(result) == "Isolated transport report"
                and result.wright_usage["input_tokens"] == 17
            )
            assert (
                len(requests) == 1
                and requests[0]["tools"] == []
                and requests[0]["tool_choice"] == "none"
            )
            assert requests[0]["messages"][1]["content"][1]["type"] == "image_url"
            assert any(
                x.get("capture_scope") == "provider_sdk_request" for x in evidence
            )
            assert "fake-offline-test-secret" not in json.dumps(evidence)
            mode = "tool"
            bridge = HermesOpenAICompatibilityBridge(
                HermesOpenAIBridgeSettings(
                    base_url="http://unused.invalid",
                    api_key="",
                    workflow_task=True,
                    expected_resolution=route,
                )
            )
            decision = await bridge.complete(
                {
                    "model": "wright-hermes",
                    "stream": False,
                    "tool_choice": "required",
                    "messages": [{"role": "user", "content": "Inspect the exact part"}],
                    "tools": [
                        {
                            "type": "function",
                            "function": {
                                "name": "inspect",
                                "description": "Read-only fixture inspection",
                                "parameters": {
                                    "type": "object",
                                    "properties": {"part": {"type": "string"}},
                                    "required": ["part"],
                                    "additionalProperties": False,
                                },
                            },
                        }
                    ],
                },
                invocation_observer=observe,
            )
            assert (
                decision["choices"][0]["message"]["tool_calls"][0]["function"]["name"]
                == "inspect"
            )
            assert len(requests) == 2 and requests[-1]["tools"] == []
            mode = "invalid"
            failed = []

            async def retain(record):
                failed.append(record)

            try:
                await workflow_sdk_completion(
                    {
                        "messages": [
                            {"role": "system", "content": "Prepared isolated fixture"},
                            {"role": "user", "content": "No external action"},
                        ]
                    },
                    route,
                    invocation_observer=retain,
                )
            except ValueError:
                pass
            else:
                raise AssertionError("Invalid provider output was accepted")
            assert len(requests) == 3 and any(
                x.get("capture_scope") == "provider_sdk_request" for x in failed
            )
            write_config("changed-synthetic-model")
            try:
                await workflow_sdk_completion({"messages": []}, route)
            except ModelRouteChangedError:
                pass
            else:
                raise AssertionError("Changed route was accepted")
            assert len(requests) == 3
            print(
                json.dumps(
                    {
                        "status": "passed",
                        "scope": "stock Hermes 0.19 SDK with explicitly synthetic loopback responses; no real inference or MCP effects",
                        "route": route,
                        "sdk_calls": 3,
                        "text_and_image_input": True,
                        "validated_tool_proposal": True,
                        "failure_evidence": True,
                        "changed_route_held": True,
                        "private_credentials_exported": False,
                    },
                    indent=2,
                )
            )

        asyncio.run(proof())
    server.shutdown()


if __name__ == "__main__":
    main()
