"""Restore an explicitly installed, qualified demo bootstrap after catalog sync."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from tool_registry.db import get_server, update_server


def configure(run_root: Path, database: Path) -> dict:
    run_root = run_root.resolve()
    evidence = run_root / "agentcad-bootstrap-qualification/attempt-002"
    receipt = evidence / "demo-installation.json"
    if not receipt.is_file():
        return {"configured": False, "reason": "no_explicit_demo_installation"}
    installed = json.loads(receipt.read_text(encoding="utf-8"))
    proof = json.loads((evidence / "qualification.json").read_text(encoding="utf-8"))
    snapshot = Path(proof["snapshot"]).resolve()
    if not snapshot.is_relative_to(run_root / "sources") or not snapshot.is_file():
        raise ValueError("Qualified bootstrap must be a local immutable source snapshot")
    digest = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    if (proof.get("status") != "passed" or not proof.get("continuous_open_stdin")
            or proof.get("native_status") != "success"
            or digest != proof.get("bootstrap_sha256")
            or digest != installed.get("bootstrap_sha256")):
        raise ValueError("Demo bootstrap qualification or source identity changed")
    command = ["uv", "run", "--no-project", "--isolated", "--python", "3.12.11",
               "--with", "agentcad[mcp]==0.6.0", "--with", "numpy==2.5.2",
               "--with", "build123d==0.10.0", "python", "-B", str(snapshot)]
    if proof.get("command") != command or installed.get("command") != command:
        raise ValueError("Only the exact qualified demo bootstrap command can be restored")
    server = get_server(str(database), "agentcad")
    if server is None or not server.is_installed:
        raise ValueError("Demo AgentCAD installation is missing")
    changed = server.command != command
    if changed:
        update_server(str(database), "agentcad", {"command": command})
    return {"configured": True, "changed": changed, "server_id": "agentcad",
            "bootstrap_sha256": digest}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-root", required=True, type=Path)
    parser.add_argument("--database", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(configure(args.run_root, args.database)))
