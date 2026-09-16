"""Snapshot the selected local Solid Edge MCP source and repair null serialization.

Leaves the upstream checkout/binary untouched. This prepares source only; build
and native/gateway qualification are separate observable prerequisite operations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def prepare(source: Path, destination: Path) -> dict:
    source, destination = source.resolve(), destination.resolve()
    if destination.exists():
        raise ValueError("Choose a fresh snapshot directory; existing evidence is immutable")
    if source == destination or source in destination.parents:
        raise ValueError("The snapshot must be outside the upstream checkout")
    projects = (
        "CadMcp.Api", "CadMcp.Core", "CadMcp.Provider.Fake",
        "CadMcp.Provider.SolidEdge", "CadMcp.Verification", "SolidEdgeMcpServer",
    )
    files = [source / "Directory.Build.props"]
    for project in projects:
        files.extend(path for path in (source / "src" / project).rglob("*")
                     if path.is_file() and not {"bin", "obj"}.intersection(path.relative_to(source).parts))
    rows = []
    for path in sorted(files):
        data = path.read_bytes()
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        rows.append({"path": relative.as_posix(), "sha256": hashlib.sha256(data).hexdigest(),
                     "bytes": len(data)})
    program = destination / "src/SolidEdgeMcpServer/Program.cs"
    original = program.read_text(encoding="utf-8")
    marker = "    .WithToolsFromAssembly()"
    if original.count(marker) != 1:
        raise ValueError("Upstream registration changed; review before applying the repair")
    replacement = (
        "    // Keep required nullable result fields present in structured MCP output.\n"
        "    .WithToolsFromAssembly(serializerOptions: new System.Text.Json.JsonSerializerOptions(\n"
        "        ModelContextProtocol.McpJsonUtilities.DefaultOptions)\n"
        "    {\n"
        "        DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.Never\n"
        "    })"
    )
    program.write_text(original.replace(marker, replacement), encoding="utf-8")
    revision = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    report = {
        "schema_version": 1, "source_checkout": str(source), "base_revision": revision,
        "source_identity": "working_tree_snapshot_including_local_changes",
        "snapshot_root": str(destination), "files": rows,
        "patch": {"path": "src/SolidEdgeMcpServer/Program.cs",
                  "purpose": "Serialize actual null fields required by the existing MCP output schemas",
                  "patched_sha256": hashlib.sha256(program.read_bytes()).hexdigest()},
        "build_status": "not_run", "backend_qualification": "not_run",
        "upstream_modified": False,
    }
    (destination / "snapshot-manifest.json").write_text(json.dumps(report, indent=2) + "\n")
    return {"snapshot_root": str(destination), "files": len(rows), "prepared_only": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.destination)))
