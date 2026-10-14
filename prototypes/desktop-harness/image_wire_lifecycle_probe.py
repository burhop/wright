"""Reconnect to the synthetic image fixture, then revoke it at its existing owner.

This tests read-port reconciliation, not workflow cancellation or desktop uptake.
"""

import argparse
import asyncio
import hashlib
import base64
import json
from pathlib import Path
import sys

from data_vault.desktop_reasoning_repository import DesktopReasoningRepository
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main(state):
    receipt = state / "image-wire-lifecycle.json"
    if receipt.exists():
        raise ValueError("Existing lifecycle receipt must be preserved")
    previous = json.loads((state / "image-wire.json").read_text())
    scope = previous["workspace"]
    repo = DesktopReasoningRepository(str(state / "wright.sqlite"))
    request = repo.get_request(**scope, request_id="synthetic-image-wire")
    if request.run_id != "synthetic-no-engineering-run":
        raise ValueError("Only the private transport fixture may be interrupted")
    assert request.digest == previous["request_digest"]
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
            await session.initialize()
            args = {
                **scope,
                "request_id": request.request_id,
                "request_digest": request.digest,
                "binding_digest": request.binding.digest,
                "image_index": 0,
            }
            result = await session.call_tool("wright_reasoning_image", args)
            assert not result.isError
            images = [p for p in result.content if p.type == "image"]
            assert len(images) == 1
            digest = hashlib.sha256(
                base64.b64decode(images[0].data, validate=True)
            ).hexdigest()
            assert digest == previous["image_sha256"]
            assert repo.interrupt(
                **scope, request_id=request.request_id, outcome="cancelled"
            )
            stale = await session.call_tool("wright_reasoning_image", args)
            assert stale.isError and not any(p.type == "image" for p in stale.content)
            assert not repo.pending(**scope)
            assert (
                repo.get_request(**scope, request_id=request.request_id).digest
                == request.digest
            )
            evidence = {
                "scope": "synthetic request owner + real MCP/HTTP read port",
                "checks": {
                    "new_mcp_process_reconnect": True,
                    "same_image_after_reconnect": True,
                    "owner_cancelled_image_unavailable": True,
                    "original_request_retained": True,
                },
                "request_digest": request.digest,
                "workflow_cancellation": "not tested; direct synthetic owner interruption",
                "api_restart": "not tested",
                "model_perception": "unverified",
            }
            receipt.write_text(json.dumps(evidence, indent=2) + "\n")
            print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    asyncio.run(main(parser.parse_args().state_dir.resolve()))
