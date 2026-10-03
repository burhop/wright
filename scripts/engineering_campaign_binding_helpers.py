"""Shared declaration and staging helpers for existing engineering examples.

These helpers render inputs/connections and preserve exact source/file identities;
they never execute workflows, slice packages or operate external equipment.
The retained AgentCAD entrypoint guidance is existing example metadata, not a
provider protocol or a new integration. Original campaign records are unchanged.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def _renewal_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "campaign_example_renewal", ROOT / "scripts/campaign_example_renewal.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _agentcad_guidance():
    import importlib.util
    spec = importlib.util.spec_from_file_location("agentcad_source_contract",ROOT/"scripts/agentcad_source_contract.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.GUIDANCE


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def confined(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if not candidate.is_relative_to(root.resolve()):
        raise ValueError("A campaign path escapes its declared workspace")
    return candidate


def write_once(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f"Refusing to replace a different staged file: {path}")
    path.write_bytes(data)


def port(key: str, kind: str = "engineering_document") -> dict:
    return dict(key=key, name=key.replace("_", " "), kind=kind, item=None,
                required=True, quantity="one", description="Campaign input or same-run output")


def render(sections: list[dict]) -> str:
    return "\n\n".join(
        f"{s['kind']} {s['id']}\n" + "\n".join(
            f"  {k}: {json.dumps(v, ensure_ascii=False, separators=(',', ':'))}"
            for k, v in s["fields"].items()
        ) + "\nend" for s in sections
    ) + "\n"


def add_reference(sections, producer, target, key, kind="engineering_document"):
    key = f"{target['id']}_{key}"
    target["fields"]["inputs"].append(port(key, kind))
    sections.append(dict(kind="connection", id=f"bind_{target['id']}_{key}", fields={
        "type": "item", "from": producer, "to": f"{target['id']}.{key}",
        "label": "campaign input binding", "when": None,
    }))


def add_file_input(sections, suffix, name, path):
    identity = f"campaign_{name}_{suffix}"
    sections.append(dict(kind="input", id=identity, fields={
        "name": name.replace("_", " "), "purpose": "Human-submitted campaign context",
        "step_type": "work", "group": None, "provided_by": "engineer",
        "inputs": [], "outputs": [port(identity + "_document")],
        "instructions": "Use the original supplied document; do not invent measurements.",
        "settings": {"input_mode": "workspace-file", "workspace_file": path},
        "tool": None, "reusable_step": None,
    }))
    return identity + "." + identity + "_document"


def selected_tool(tools, server, name):
    matches = [
        value
        for value in tools.values()
        if value.get("server_id") == server and value.get("tool_name") == name
    ]
    if len(matches) != 1:
        raise ValueError(f"Required configured tool is missing or ambiguous: {server}/{name}")
    return matches[0]


def publish_input_binding_evidence(report, scenario_directory):
    """Future-only sidecar; never changes staged bytes or canonical source."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("engineering_dataset_input_bindings", ROOT/"scripts/engineering_dataset_input_bindings.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.emit_for_preparation(report,scenario_directory)


AGENTCAD_ENTRYPOINT_GUIDANCE = _agentcad_guidance()
