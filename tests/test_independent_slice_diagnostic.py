"""Provider-receipt fixtures, not live slicing or geometry qualification."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("independent_slice_diagnostic", ROOT / "scripts/probe_printed_blender_binding.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)
SCHEMA = {"type": "object", "properties": {"source": {"type": "string"}, "output": {"type": "string"}},
          "required": ["source", "output"]}


@pytest.fixture
def diagnostic(tmp_path):
    workspace = tmp_path / "workspace"
    (workspace / "diagnostic/inputs").mkdir(parents=True)
    (workspace / "diagnostic/artifacts").mkdir()
    (workspace / "diagnostic/artifacts/repaired_mesh.stl").write_bytes(b"synthetic geometry identity; not CAD proof")
    value = {"schema_version": 1, "offline_only": True, "command": ["fixture-never-launched"],
             "tool": "slice_model_file", "input_schema_sha256": hashlib.sha256(json.dumps(SCHEMA, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
             "arguments": {"source": "{source}", "output": "{package}"},
             "success_field": "ok", "success_contract": "Fixture contract only",
             "expected_response_fields": {"source": "{source}", "output": "{package}"},
             "gcode_entry": "Metadata/plate_1.gcode", "profiles": {}}
    for role in ("machine", "process", "filament"):
        path = tmp_path / (role + ".json")
        raw = json.dumps({"fixture_role": role}).encode()
        path.write_bytes(raw)
        value["profiles"][role] = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}
    path = tmp_path / "provider.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return workspace, path, value


class Runner:
    def __init__(self, *args, mode="success", **kwargs):
        self.mode, self.calls, self.stopped = mode, [], False

    async def start(self):
        pass

    async def list_tools(self):
        return [{"name": "slice_model_file", "inputSchema": {} if self.mode == "schema" else SCHEMA}]

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        if self.mode == "timeout":
            raise TimeoutError("Fixture unknown response; no retry is permitted")
        archive_bytes = io.BytesIO()
        with zipfile.ZipFile(archive_bytes, "w") as archive:
            archive.writestr("Metadata/plate_1.gcode", "G90\nG21\nM83\nG1 X0 Y0 Z0.2\n;CHANGE_LAYER\n;Z_HEIGHT:0.2\n;FEATURE:Support\nG1 X10 Y0 E1\n")
            archive.writestr("Metadata/plate_1.png", b"\x89PNG\r\n\x1a\n" + b"fixture signature only")
        Path(arguments["output"]).write_bytes(archive_bytes.getvalue())
        return {"content": [{"type": "text", "text": json.dumps({"ok": self.mode != "error", **arguments})}]}

    async def stop(self):
        self.stopped = True


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["success", "schema", "timeout", "error"])
async def test_exact_one_call_and_passive_response_identity(diagnostic, mode):
    workspace, path, _ = diagnostic
    definition = probe.external_slice_definition(path)
    runner = Runner(mode=mode)
    def factory(*args, **kwargs):
        return runner
    if mode == "success":
        result = await probe.external_slice_probe(definition, workspace, factory)
        assert result["engineering_acceptance"] is False
        evidence = json.loads((workspace / "diagnostic/artifacts/slice-evidence.json").read_bytes())
        assert evidence["source_sha256"] == probe.sha(workspace / "diagnostic/artifacts/repaired_mesh.stl")
        assert evidence["package_sha256"] == result["package_sha256"]
        assert evidence["provider_response_sha256"] == result["response_sha256"]
        assert result["protocol_scope"].startswith("direct MCP diagnostic")
    else:
        with pytest.raises(TimeoutError if mode == "timeout" else ValueError):
            await probe.external_slice_probe(definition, workspace, factory)
        assert not (workspace / "diagnostic/artifacts/slice-evidence.json").exists()
    assert runner.stopped is True
    assert len(runner.calls) == (0 if mode == "schema" else 1)
    state = json.loads((workspace / "diagnostic/artifacts/external-slice-attempt.json").read_bytes())["state"]
    assert state == {"schema": "not_called", "timeout": "outcome_unknown"}.get(mode, "response_received")
    with pytest.raises(ValueError, match="do not replay"):
        await probe.external_slice_probe(definition, workspace, factory)
    assert len(runner.calls) == (0 if mode == "schema" else 1)


@pytest.mark.parametrize("change", ["command", "embedded", "offline", "paths", "profile", "partial", "schema", "environment"])
def test_predictable_configuration_defects_reject_before_native_owner(diagnostic, change):
    _, path, value = diagnostic
    if change == "command":
        value["command"] = "unsafe shell string"
    elif change == "embedded":
        value["command"] = ["python", "scripts/engineering_dataset_slice_mcp.py"]
    elif change == "offline":
        value["offline_only"] = False
    elif change == "paths":
        del value["arguments"]["source"]
    elif change == "profile":
        Path(value["profiles"]["machine"]["path"]).write_bytes(b"changed")
    elif change == "partial":
        value["arguments"]["extra"] = "prefix{source}"
    elif change == "schema":
        value["input_schema_sha256"] = ""
    elif change == "environment":
        value["env"] = {"key": 123}
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(ValueError):
        probe.external_slice_definition(path)
