"""Actual adapter/MCP image perception fixture, answered by the desktop conversation.

Not an engineering run or an installed-plugin rendering claim. Ground truth stays
out of pending task text; compare it only after the desktop supplies its answer.
"""

import argparse
import asyncio
import base64
import hashlib
import io
import json
from pathlib import Path
import secrets
import sys

from PIL import Image, ImageDraw
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from core.desktop_reasoning import DesktopHarnessBinding
from data_vault import WorkspaceRepository
from data_vault.secret_provider import FileSecretProvider
from gateway_probe import SOURCE
import re


async def main(state):
    receipt = state / "image-perception.json"
    if receipt.exists():
        raise ValueError("Use fresh isolated state; retain prior evidence")
    (state / "image-perception-started").touch(exist_ok=False)
    binding = DesktopHarnessBinding.model_validate_json(
        (state / "desktop-binding.json").read_text()
    )
    if binding.image_input_profile != "inline-png-jpeg-v1":
        raise ValueError("Image profile unavailable")
    colors = ["red", "green", "blue"]
    shapes = ["circle", "square", "triangle"]
    secrets.SystemRandom().shuffle(colors)
    secrets.SystemRandom().shuffle(shapes)
    expected = [dict(color=c, shape=s) for c, s in zip(colors, shapes)]
    picture = Image.new("RGB", (480, 160), "white")
    draw = ImageDraw.Draw(picture)
    for index, item in enumerate(expected):
        x = 30 + index * 160
        box = (x, 30, x + 100, 130)
        if item["shape"] == "circle":
            draw.ellipse(box, fill=item["color"])
        elif item["shape"] == "square":
            draw.rectangle(box, fill=item["color"])
        else:
            draw.polygon([(x + 50, 30), (x, 130), (x + 100, 130)], fill=item["color"])
    buffer = io.BytesIO()
    picture.save(buffer, format="PNG")
    data = buffer.getvalue()
    (state / "fixture.png").write_bytes(data)
    (state / "fixture-ground-truth.json").write_text(json.dumps(expected))
    repo = WorkspaceRepository(
        str(state / "wright.sqlite"),
        secrets=FileSecretProvider(state / "credentials.json"),
    )
    params = StdioServerParameters(
        command=sys.executable,
        args=[
            str(Path(__file__).with_name("mcp_bridge.py")),
            "--state-dir",
            str(state),
        ],
    )
    async with stdio_client(params) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()

            async def call(name, args):
                result = await session.call_tool(name, args)
                if result.isError:
                    raise ValueError(f"{name} failed: {result.content}")
                return result

            created = await call(
                "wright_workspace_create", {"name": "Image perception fixture"}
            )
            workspace = created.structuredContent or json.loads(created.content[0].text)
            scope = {k: workspace[k] for k in ("workspace_id", "session_id")}
            root = Path(repo.get_by_session(scope["session_id"])["local_path"])
            (root / "inputs").mkdir(exist_ok=True)
            (root / "inputs/fixture.png").write_bytes(data)
            source = SOURCE.replace(
                '"kind":"engineering_document"', '"kind":"reference_images"', 2
            )
            source = source.replace("inputs/requirements.md", "inputs/fixture.png")
            source = re.sub(
                r"^  prompt: .*$",
                '  prompt: "Describe the three colored shapes from left to right in the attached image. Return JSON text containing an array of objects with only color and shape fields, using lowercase English names. This is a synthetic perception fixture, not engineering evidence."',
                source,
                flags=re.MULTILINE,
            )
            source = re.sub(
                r'^  settings: \{"authoring_template".*$',
                '  settings: {"authoring_template":"ai-prompt","output_format":"json","output_filename":"outputs/perception.json"}',
                source,
                flags=re.MULTILINE,
            )

            async def document(name, arguments):
                result = await call(name, arguments)
                return result.structuredContent or json.loads(result.content[0].text)

            saved = await document(
                "wright_workflow_create",
                {
                    **scope,
                    "path": "workflows/image-perception.workflow.wflow",
                    "source": source,
                },
            )
            source_scope = {
                **scope,
                "path": saved["path"],
                "source_digest": saved["storage_digest"],
            }
            prepared = await document(
                "wright_process_prepare", {**source_scope, "bindings": []}
            )
            started = await document(
                "wright_process_start",
                {
                    **source_scope,
                    "input_snapshot_id": prepared["snapshot_id"],
                    "input_digest": prepared["digest"],
                    "request_id": "image-perception-start-01",
                },
            )
            async with asyncio.timeout(30):
                while True:
                    pending = await call("wright_reasoning_pending", scope)
                    tasks = (
                        pending.structuredContent or json.loads(pending.content[0].text)
                    )["tasks"]
                    if tasks:
                        break
                    await asyncio.sleep(0.1)
            task = tasks[0]
            identity = {
                "request_id": task["request"]["request_id"],
                "request_digest": task["request_digest"],
                "binding_digest": task["binding_digest"],
            }
            delivered = await call(
                "wright_reasoning_image", {**scope, **identity, "image_index": 0}
            )
            images = [part for part in delivered.content if part.type == "image"]
            assert len(images) == 1 and base64.b64decode(images[0].data) == data
            # The orchestrator forwards this exact MCP content block to the model.
            (state / "delivered-mcp-image.json").write_text(images[0].model_dump_json())
            (state / "pending-image-task.json").write_text(json.dumps(task, indent=2))
            evidence = {
                "scope": "synthetic workflow + MCP + desktop perception; no engineering acceptance",
                "start_receipt": started,
                "workspace": scope,
                **identity,
                "image_sha256": hashlib.sha256(data).hexdigest(),
                "image_bytes": len(data),
                "state": "awaiting_desktop_answer",
            }
            receipt.write_text(json.dumps(evidence, indent=2))
            answer_file = state / "desktop-image-answer.json"
            async with asyncio.timeout(550):
                while not answer_file.exists():
                    await asyncio.sleep(0.25)
            answer = json.loads(answer_file.read_text())
            response = await call(
                "wright_reasoning_answer",
                {
                    **scope,
                    **identity,
                    "response_id": "image-perception-answer-01",
                    "reply": json.dumps(answer),
                },
            )
            async with asyncio.timeout(30):
                while True:
                    snapshot = await document(
                        "wright_process_read",
                        {**source_scope, "run_id": started["run_id"]},
                    )
                    if snapshot["state"] != "running":
                        break
                    await asyncio.sleep(0.1)
            if snapshot["state"] != "completed":
                raise ValueError(f"Actual run did not complete: {snapshot['state']}")
            output = (root / "outputs/perception.json").read_bytes()
            observed = json.loads(output)
            if observed != json.loads(answer["response"]):
                raise ValueError("Saved output differs from the desktop response")
            evidence.update(
                state="completed",
                matched=observed == expected,
                observed=observed,
                expected=expected,
                response_receipt=response.structuredContent,
                final_snapshot=snapshot,
                output_sha256=hashlib.sha256(output).hexdigest(),
            )
            receipt.write_text(json.dumps(evidence, indent=2))
            if observed != expected:
                raise ValueError(
                    "Perception answer differs from hidden fixture ground truth"
                )
            print(json.dumps({"state": "completed", "matched": True}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", required=True, type=Path)
    asyncio.run(main(parser.parse_args().state_dir.resolve(strict=True)))
