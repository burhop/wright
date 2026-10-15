"""Deliver six unchanged historical review images through a live supervised fixture.

No provider execution, new CAD result or human engineering acceptance.
"""

import argparse
import asyncio
import base64
import hashlib
import json
from pathlib import Path
import sys
from uuid import uuid4

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from core.desktop_reasoning import DesktopHarnessBinding
from data_vault import WorkspaceRepository
from data_vault.secret_provider import FileSecretProvider
from gateway_probe import SOURCE
import re


async def main(state):
    receipt = state / "engineering-images.json"
    if receipt.exists():
        raise ValueError("Use fresh isolated state; retain prior evidence")
    (state / "engineering-images-started").touch(exist_ok=False)
    binding = DesktopHarnessBinding.model_validate_json(
        (state / "desktop-binding.json").read_text()
    )
    if binding.image_input_profile != "inline-png-jpeg-engineering-v1":
        raise ValueError("Image profile unavailable")
    historical = (
        Path(__file__).resolve().parents[2]
        / "artifacts/stevecad-demonstrations/prompt-to-reviewed-cad/block-native-006/outputs"
    )
    names = (
        "cad-isometric.png",
        "cad-top.png",
        "cad-front.png",
        "render_isometric.png",
        "render_top.png",
        "render_front.png",
    )
    originals = [(name, (historical / name).read_bytes()) for name in names]
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
                "wright_workspace_create", {"name": "Engineering images " + uuid4().hex[:12]}
            )
            workspace = created.structuredContent or json.loads(created.content[0].text)
            scope = {k: workspace[k] for k in ("workspace_id", "session_id")}
            root = Path(repo.get_by_session(scope["session_id"])["local_path"])
            (root / "inputs").mkdir(exist_ok=True)
            input_template = SOURCE[
                SOURCE.index("input requirements\n") : SOURCE.index("task inspect\n")
            ]
            connection_template = SOURCE[SOURCE.index("connection supplied\n") :]
            inputs = []
            connections = []
            ports = []
            for index, (name, data) in enumerate(originals):
                (root / "inputs" / name).write_bytes(data)
                key = f"image{index}"
                inputs.append(
                    input_template.replace("input requirements\n", f"input {key}\n")
                    .replace("inputs/requirements.md", f"inputs/{name}")
                    .replace('"key":"document"', f'"key":"{key}_document"')
                    .replace(
                        '"kind":"engineering_document"', '"kind":"reference_images"'
                    )
                )
                connections.append(
                    connection_template.replace(
                        "connection supplied", f"connection supplied{index}"
                    )
                    .replace("requirements.document", f"{key}.{key}_document")
                    .replace("inspect.requirements", f"inspect.{key}")
                )
                ports.append(
                    {
                        "key": key,
                        "kind": "reference_images",
                        "name": name,
                        "item": None,
                        "required": True,
                        "quantity": "one",
                        "description": "Unchanged historical capture; transport fixture only",
                    }
                )
            task_source = SOURCE[
                SOURCE.index("task inspect\n") : SOURCE.index("connection supplied\n")
            ]
            task_source = re.sub(
                r"^  inputs: .*$",
                "  inputs: " + json.dumps(ports),
                task_source,
                flags=re.MULTILINE,
            )
            prompt = "Compare these six historical images in order: CAD isometric, CAD top, CAD front, rendering isometric, rendering top, rendering front. Return JSON with three view-pair observations and a limitations field. Describe only visible features, count holes when visible, compare silhouette and appearance, and identify anything obscured or uncertain. These are retained artifacts used to qualify original-byte image transport, not a new CAD run, geometric measurement, compliance verdict or human acceptance. Do not read other files or use tools."
            task_source = re.sub(
                r"^  prompt: .*$",
                "  prompt: " + json.dumps(prompt),
                task_source,
                flags=re.MULTILINE,
            )
            task_source = re.sub(
                r"^  settings: .*$",
                '  settings: {"authoring_template":"ai-prompt","output_format":"json","output_filename":"outputs/perception.json"}',
                task_source,
                flags=re.MULTILINE,
            )
            source = (
                SOURCE[: SOURCE.index("input requirements\n")]
                + "".join(inputs)
                + task_source
                + "".join(connections)
            )

            async def document(name, arguments):
                result = await call(name, arguments)
                return result.structuredContent or json.loads(result.content[0].text)

            saved = await document(
                "wright_workflow_create",
                {
                    **scope,
                    "path": "workflows/engineering-images.workflow.wflow",
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
                    "request_id": "engineering-images-start-01",
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
            delivered_images = []
            for index, (name, data) in enumerate(originals):
                delivered = await call(
                    "wright_reasoning_image",
                    {**scope, **identity, "image_index": index},
                )
                images = [part for part in delivered.content if part.type == "image"]
                assert len(images) == 1 and base64.b64decode(images[0].data) == data
                (state / f"delivered-mcp-image-{index}.json").write_text(
                    images[0].model_dump_json()
                )
                delivered_images.append(
                    {
                        "name": name,
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "bytes": len(data),
                        "index": index,
                    }
                )
            (state / "pending-image-task.json").write_text(json.dumps(task, indent=2))
            evidence = {
                "scope": "six unchanged historical images, supervised fixture and actual MCP; no new CAD or engineering acceptance",
                "start_receipt": started,
                "workspace": scope,
                **identity,
                "images": delivered_images,
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
                    "response_id": "engineering-images-answer-01",
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
                reply_matches_saved_output=True,
                observed=observed,
                response_receipt=response.structuredContent,
                final_snapshot=snapshot,
                output_sha256=hashlib.sha256(output).hexdigest(),
            )
            receipt.write_text(json.dumps(evidence, indent=2))
            print(
                json.dumps({"state": "completed", "reply_matches_saved_output": True})
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", required=True, type=Path)
    asyncio.run(main(parser.parse_args().state_dir.resolve(strict=True)))
