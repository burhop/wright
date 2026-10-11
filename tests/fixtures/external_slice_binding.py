"""Synthetic declaration fixtures only; no provider or engineering qualification."""
import hashlib
import json


def make_binding(directory, scenario, process):
    directory.mkdir(parents=True, exist_ok=True)
    binding = {
        "schema_version": 1, "scenario_id": scenario,
        "slicer": {"server": "independent-offline-slicer", "tool": "slice_model_file",
                   "schema_digest": "a" * 64,
                   "arguments": {"source": "{source}", "output": "{package}",
                                 "plate": 1, "orient": False, "arrange": True, "confirm": True}},
        "files": {"server": "wright-workspace-files", "tool": "write_text_document", "schema_digest": "b" * 64},
        "inspection": {"server": "independent-python", "tool": "run_simulation",
                       "schema_digest": "c" * 64, "workspace_mount": "/workspace", "backend": "skfem"},
        "success_field": "ok", "success_contract": "Fixture declaration only; not qualification",
        "gcode_entry": "Metadata/plate_1.gcode",
        "expected_response_fields": {"source": "{source}", "output": "{package}", "plate": 1},
        "profiles": {},
    }
    for role, value in (("machine", {"name": "synthetic machine"}),
                        ("filament", {"name": "synthetic filament"}),
                        ("process", {key: item for key, item in process.items() if key != "base"})):
        path = directory / (role + ".json")
        raw = (json.dumps(value) + "\n").encode()
        path.write_bytes(raw)
        binding["profiles"][role] = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}
    path = directory / "binding.json"
    path.write_text(json.dumps(binding), encoding="utf-8")
    tools = [{"server_id": choice["server"], "tool_name": choice["tool"],
              "name": choice["server"] + "__" + choice["tool"], "schema_digest": choice["schema_digest"]}
             for choice in (binding[role] for role in ("slicer", "files", "inspection"))]
    return path, tools
