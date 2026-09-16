"""Compile actual jig drafts and resolve their source-path handoff, with no CAD."""
import ast
import asyncio
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
from types import SimpleNamespace

import pytest

from scripts.agentcad_source_contract import GUIDANCE
from workspace_service.workflow_source_execution import _parse, compile_prompt_workflow
from workspace_service.workflow_mcp_execution import WorkflowMcpRuntime
from workspace_service.workspace_document_gateway import WorkspaceDocumentGatewayProvider
from workspace_service.workspace_file_inspection import inspection_tool, WorkspaceFileInspector
from agent_adapters.hermes_openai_bridge import (
    HermesBridgeError, HermesOpenAIBridgeSettings, HermesOpenAICompatibilityBridge,
)

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("jig_path_preparer", ROOT / "scripts/prepare-drill-jig-dataset-campaign.py")
preparer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preparer)


@pytest.mark.parametrize("ordinal", [1, 2, 3])
def test_author_path_literals_match_actual_producers_and_native_run_arguments(tmp_path, ordinal):
    config = json.loads(preparer.BINDING.read_text())
    tools = [{"server_id": server, "tool_name": name, "name": server + "__" + name, "schema_digest": "a" * 64}
        for server, names in config["allowed_tools"].items() for name in names]
    args = SimpleNamespace(workspace_root=str(tmp_path / "workspace"), draft_root=str(tmp_path / "draft"),
        attempt="path-contract-unit", instance_source=None, initialize_agentcad=False)
    directory = next(p for p in (ROOT / "tests/datasets/engineering-workflows/scenarios/parametric-drill-jig").iterdir()
        if p.name.startswith(f"{ordinal:02d}"))
    result = preparer.prepare(args, directory, tools)
    source = Path(result["draft"]).read_text(encoding="utf-8")
    report = json.loads(Path(result["draft"]).with_name("staging-manifest.json").read_text())
    plan = compile_prompt_workflow(source)
    original = _parse(preparer.TEMPLATE.read_text().replace("__instance__", report["scenario_id"].replace("-", "_") + "_path_contract_unit"))
    assert all(edge in _parse(source) for edge in original if edge["kind"] == "connection")
    assert all(any(step.id == node["id"] for step in plan.steps) for node in original if node["kind"] == "task")
    for author_prefix, consumer_prefix, filename in (
        ("author_jig_source_", "generate_jig_", "jig-source.py"),
        ("author_jig_inspection_", "check_alignment_", "inspect-jig-source.py"),
    ):
        author = next(step for step in plan.steps if step.id.startswith(author_prefix))
        consumer = next(step for step in plan.steps if step.id.startswith(consumer_prefix))
        literal = re.search(r"Set SOURCE_PATH = ('.*?') for actual", author.prompt).group(1)
        source_path = Path(ast.literal_eval(literal))
        expected = Path(args.workspace_root) / report["output_root"] / filename
        assert source_path == expected and source_path.is_absolute()
        assert expected.relative_to(Path(args.workspace_root)).as_posix() in author.expected_files
        assert consumer.arguments["script"] == str(expected)
        assert not consumer.agent_task and consumer.tool_name == "agentcad__run"
        project = expected.parent / "agentcad-project"
        assert consumer.arguments["cwd"] == str(project)
        assert consumer.source_contract == "agentcad-build123d-0.10"
        assert f"PROJECT_DIR = {str(project)!r}" in author.prompt
        assert f"OUTPUT_DIR = {str(expected.parent)!r}" in author.prompt
        assert GUIDANCE in author.prompt
        assert "inspect_file on the complete written source" in author.prompt
    assert result["executed"] is False
    assert report["native_project_initialization"] == "requires_native_agentcad_init"
    generated = next(step for step in plan.steps if step.id.startswith("generate_jig_"))
    inspected = next(step for step in plan.steps if step.id.startswith("check_alignment_"))
    assert {Path(path).name for path in generated.expected_files} == set(config["expected_generated_files"])
    assert {Path(path).name for path in inspected.expected_files} == {"dimension-report.json"}
    observer = next(step for step in plan.steps if step.id.startswith("inspect_jig_exports_"))
    assert not observer.references
    observer_section = next(node for node in _parse(source) if node.get("id") == observer.id)
    assert observer_section["fields"]["inputs"] == []
    assert any(node["kind"] == "connection" and node["fields"].get("type") == "order"
        and node["fields"].get("from") == inspected.id and node["fields"].get("to") == observer.id
        for node in _parse(source))
    for filename in (*config["expected_generated_files"], "dimension-report.json"):
        assert report["output_root"] + "/" + filename in observer.prompt
    assert "includeText=true,maxTextBytes=8192" in observer.prompt and "includeText=false" in observer.prompt
    assert "nextOffsetBytes until complete" in observer.prompt and "file hashes" in observer.prompt
    assert not any((Path(args.workspace_root) / name).exists() for name in report["expected_tool_created_files"])
    asyncio.run(assert_saved_page_fits_after_removing_native_bindings(observer, Path(args.workspace_root)))


async def assert_saved_page_fits_after_removing_native_bindings(step, workspace):
    """Actual saved native page, actual file-tool schemas and the real bridge."""
    fixture = json.loads((ROOT / "tests/fixtures/jig-final-inspection-context.json").read_text(encoding="utf-8"))
    observation = fixture["observation"]
    assert observation["result"]["nextOffsetBytes"] == 32768
    assert observation["result"]["bytes"] == 35692
    native = sorted([WorkspaceDocumentGatewayProvider._tool(), inspection_tool()], key=lambda tool: tool.name)
    runtime = WorkflowMcpRuntime.__new__(WorkflowMcpRuntime)
    runtime.task_tools = lambda _: native

    class Captured(Exception):
        pass

    async def emit(*args, **kwargs):
        pass

    async def request_for(prompt, observations=None):
        captured = {}

        async def decide(messages, schemas, **kwargs):
            captured.update(messages=copy.deepcopy(messages), schemas=schemas)
            raise Captured

        with pytest.raises(Captured):
            await runtime.run_task(step, prompt, decide, emit)
        alias = f"tool_{next(index for index, tool in enumerate(native) if tool.tool_name == 'inspect_file')}"
        for index, item in enumerate(observations or [observation], 1):
            identity = f"saved-inspection-{index}"
            content = json.dumps({"tool_call_number": index, "status": item["status"],
                "result": item["result"], "text": item["text"]}, ensure_ascii=False)
            captured["messages"].extend([
                {"role": "assistant", "content": None, "tool_calls": [{"id": identity, "type": "function",
                    "function": {"name": alias, "arguments": json.dumps(item["arguments"])}}]},
                {"role": "tool", "tool_call_id": identity, "content": content},
            ])
        bridge = HermesOpenAICompatibilityBridge(HermesOpenAIBridgeSettings(
            base_url="http://invalid.offline-only", api_key="unused", workflow_task=True,
            maximum_tools=64, maximum_translation_prompt_bytes=200000, maximum_text_bytes=16 * 1024 * 1024))
        request = bridge._validate({"model": "wright-hermes", "messages": captured["messages"],
            "tools": captured["schemas"], "tool_choice": "auto", "stream": False})
        return bridge._upstream_payload(request, translate=True, stream=False)

    with pytest.raises(HermesBridgeError) as failure:
        await request_for(fixture["original_prompt"])
    assert failure.value.code == "workflow_context_limit"
    prompt = step.prompt + f"\n\nWorkspace directory: {workspace}. File references are relative to this directory."
    # Removing references alone cannot fix an oversized individual observation.
    with pytest.raises(HermesBridgeError):
        await request_for(prompt)
    files = json.loads((ROOT / "tests/fixtures/jig-final-inspection-files.json").read_text(encoding="utf-8"))["files"]
    inspector = WorkspaceFileInspector()
    session = SimpleNamespace(session_id="unit", workspace_id="unit", workspace_path=str(workspace), principal_id="wright-native-workflow")
    history = []
    maximum_part_chars = 0
    for name, artifact in files.items():
        # Exact existing output bytes copied only to this unit-test directory.
        target = workspace / name
        payload = artifact["text"].encode("utf-8")
        assert hashlib.sha256(payload).hexdigest() == artifact["sha256"]
        target.write_bytes(payload)
        offset, pages = 0, []
        while offset < len(payload):
            arguments = {"relativePath": name, "includeText": True, "maxTextBytes": 8192, "offsetBytes": offset}
            identity = f"unit-read-{len(history)}"
            inspector.grant(request_id=identity, session_id="unit", workspace_id="unit", workspace_path=str(workspace),
                arguments=arguments, expected_sha256=artifact["sha256"], policy_digest="a" * 64)
            page = inspector.inspect(session, arguments, identity)
            history.append({"status": "succeeded", "arguments": arguments, "result": page, "text": json.dumps(page, ensure_ascii=False)})
            outgoing = await request_for(prompt, history)
            parts = [part["text"] for message in outgoing["messages"]
                for part in (message["content"] if isinstance(message["content"], list) else [{"type": "text", "text": message["content"]}])
                if part["type"] == "text"]
            assert max(map(len, parts)) <= 65536
            maximum_part_chars = max(maximum_part_chars, max(map(len, parts)))
            joined = "\n".join(parts)
            assert page["sha256"] in joined and str(page["bytes"]) in joined
            encoded = page["text"]
            for _ in range(4):
                if encoded in joined:
                    break
                encoded = json.dumps(encoded, ensure_ascii=False)[1:-1]
            else:
                raise AssertionError("The complete latest page is absent from the reversible tool transcript")
            pages.append(page["text"].encode("utf-8"))
            assert page["nextOffsetBytes"] > offset
            offset = page["nextOffsetBytes"]
        assert b"".join(pages) == payload
        assert target.read_bytes() == payload
    assert len(history) == 7
    return {"pages": len(history), "maximum_transport_text_part_chars": maximum_part_chars,
        "exact_file_bytes": {name: artifact["bytes"] for name, artifact in files.items()},
        "complete_bytes_reconstructed": True, "old_failure_reproduced": True,
        "removing_bindings_alone_insufficient": True, "model_calls": 0, "native_calls": 0}
