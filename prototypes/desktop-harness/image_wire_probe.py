"""Read a private synthetic image task over real MCP stdio and loopback HTTP.

No model answer or engineering run is produced. Requires fresh isolated state.
"""

import argparse
import asyncio
import base64
import hashlib
import json
from pathlib import Path
import sys

from core.desktop_reasoning import DesktopHarnessBinding, DesktopReasoningRequest
from data_vault.desktop_reasoning_repository import DesktopReasoningRepository
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main(state):
    receipt = state / "image-wire.json"
    if receipt.exists():
        raise ValueError("Preserve existing evidence; use fresh isolated state")
    binding = DesktopHarnessBinding.model_validate_json(
        (state / "desktop-binding.json").read_text()
    )
    if binding.image_input_profile != "inline-png-jpeg-v1":
        raise ValueError("Image transport is not explicitly enabled")
    repo = DesktopReasoningRepository(str(state / "wright.sqlite"))
    data = (
        Path(__file__).resolve().parents[2]
        / "artifacts/stevecad-demonstrations/qualification/native/06-inspect-coupon-1.png"
    ).read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    parameters = StdioServerParameters(
        command=sys.executable,
        args=[
            str(Path(__file__).with_name("mcp_bridge.py")),
            "--state-dir",
            str(state),
        ],
    )
    async with stdio_client(parameters) as streams:
        async with ClientSession(*streams) as session:
            initialized = await session.initialize()
            result = await session.call_tool(
                "wright_workspace_create", {"name": "Private image transport fixture"}
            )
            assert not result.isError
            workspace = result.structuredContent or json.loads(result.content[0].text)
            scope = {key: workspace[key] for key in ("workspace_id", "session_id")}
            request = DesktopReasoningRequest(
                **scope,
                request_id="synthetic-image-wire",
                run_id="synthetic-no-engineering-run",
                ordinal=1,
                created_at="2026-10-14T00:00:00Z",
                kind="response",
                output_format="text",
                binding=binding,
                instruction_set_digest="a" * 64,
                payload={
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Private transport fixture; do not answer.",
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": "data:image/png;base64," + encoded,
                                    },
                                },
                            ],
                        }
                    ]
                },
            )
            repo.put_request(request)
            pending = await session.call_tool("wright_reasoning_pending", scope)
            assert not pending.isError
            assert encoded not in pending.model_dump_json()
            args = {
                **scope,
                "request_id": request.request_id,
                "request_digest": request.digest,
                "binding_digest": binding.digest,
                "image_index": 0,
            }
            delivered = await session.call_tool("wright_reasoning_image", args)
            assert not delivered.isError
            images = [part for part in delivered.content if part.type == "image"]
            assert len(images) == 1 and images[0].mimeType == "image/png"
            assert base64.b64decode(images[0].data, validate=True) == data
            assert encoded not in json.dumps(delivered.structuredContent)
            denied = await session.call_tool(
                "wright_reasoning_image", {**args, "request_digest": "b" * 64}
            )
            assert denied.isError and not any(p.type == "image" for p in denied.content)
            retained = repo.get_request(**scope, request_id=request.request_id)
            assert retained.digest == request.digest
            assert len(repo.pending(**scope)) == 1
            evidence = {
                "scope": "real MCP stdio + loopback HTTP + durable request; synthetic task",
                "protocol_version": initialized.protocolVersion,
                "workspace": scope,
                "request_digest": request.digest,
                "binding_digest": binding.digest,
                "image_sha256": hashlib.sha256(data).hexdigest(),
                "image_bytes": len(data),
                "checks": {
                    "exact_image": True,
                    "projection_omits_base64": True,
                    "wrong_digest_denied": True,
                    "request_unchanged_pending": True,
                },
                "model_perception": "unverified",
                "engineering_run": "none",
                "fixture_source": "retained historical CAD capture",
            }
            receipt.write_text(json.dumps(evidence, indent=2) + "\n")
            print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    asyncio.run(main(parser.parse_args().state_dir.resolve()))
