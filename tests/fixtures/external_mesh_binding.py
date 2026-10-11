"""Synthetic argument/declaration fixture; never a native or engineering proof."""
import hashlib
import json
from pathlib import Path


def make_binding(directory, scenario, workspace, attempt, policy_path, machine_profile, provider):
    directory.mkdir(parents=True, exist_ok=True)
    original = json.loads(Path(policy_path).read_bytes())
    policy = {key: value for key, value in original.items()
              if key not in {"schema_version", "basis", "archived_operation_sha256", "handle_triangle_limit"}}
    if scenario == "printed-replacement-part-02":
        policy["triangle_limit"] = original["handle_triangle_limit"]
    policy["planar_cleanup"] = scenario == "printed-replacement-part-02"
    arguments = directory / "provider-arguments.json"
    arguments.write_bytes((json.dumps({"code": "print('Synthetic supplied arguments; do not execute')"}) + "\n").encode())
    binding = {"schema_version": 1, "scenario_id": scenario,
               "workspace_root": str(Path(workspace).resolve()),
               "output_root": f"campaign/{scenario}/{attempt}/artifacts",
               "provider": {"server": provider["server_id"], "tool": provider["tool_name"], "schema_digest": provider["schema_digest"]},
               "policy": policy, "machine_profile_sha256": hashlib.sha256(Path(machine_profile).read_bytes()).hexdigest(),
               "arguments": {"path": str(arguments), "sha256": hashlib.sha256(arguments.read_bytes()).hexdigest()}}
    path = directory / "binding.json"
    path.write_text(json.dumps(binding), encoding="utf-8")
    return path
