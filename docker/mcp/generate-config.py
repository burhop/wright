#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any

import yaml


VERIFY_PATH = Path(__file__).with_name("verify-bundle.py")


def _load_verifier():
    spec = importlib.util.spec_from_file_location("verify_bundle", VERIFY_PATH)
    if not spec or not spec.loader:
        raise RuntimeError(f"cannot load verifier at {VERIFY_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_yaml(path: Path) -> dict[str, Any]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("bundle must be a mapping")
    return payload


def _server_config(server: dict[str, Any]) -> dict[str, Any] | None:
    if server.get("availability") != "local_enabled":
        return None
    launch = server.get("launch")
    if not isinstance(launch, dict):
        return None
    command = launch.get("command")
    if not isinstance(command, list) or not command:
        return None
    config: dict[str, Any] = {"command": str(command[0])}
    if len(command) > 1:
        config["args"] = [str(item) for item in command[1:]]
    env = launch.get("env")
    if isinstance(env, dict) and env:
        config["env"] = {str(key): str(value) for key, value in env.items()}
    return config


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _compliance(status: dict[str, Any]) -> dict[str, Any]:
    return {
        "bundle_id": status["bundle_id"],
        "applications": [
            {
                "id": item["id"],
                "display_name": item["display_name"],
                "availability": item["availability"],
                "status": item["status"],
                "compliance": item["compliance"],
            }
            for item in status["applications"]
        ],
        "mcp_servers": [
            {
                "id": item["id"],
                "display_name": item["display_name"],
                "application_id": item["application_id"],
                "availability": item["availability"],
                "status": item["status"],
                "compliance": item["compliance"],
            }
            for item in status["mcp_servers"]
        ],
    }


def generate(bundle_path: str | Path, output_dir: str | Path) -> dict[str, Any]:
    bundle_path = Path(bundle_path)
    output_dir = Path(output_dir)
    bundle = _load_yaml(bundle_path)
    verifier = _load_verifier()
    status = verifier.validate_bundle(bundle)

    mcp_servers = {}
    for server in bundle["mcp_servers"]:
        config = _server_config(server)
        if config is not None:
            mcp_servers[server["id"]] = config

    hermes_config = {"mcp_servers": mcp_servers}
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "hermes-mcp.generated.yaml").write_text(
        yaml.safe_dump(hermes_config, sort_keys=True),
        encoding="utf-8",
    )
    _write_json(output_dir / "mcp-bundle-status.json", status)
    _write_json(output_dir / "licenses" / "THIRD-PARTY-COMPLIANCE.json", _compliance(status))
    _write_text(
        output_dir / "licenses" / "NO-WARRANTY-GPL-2.0.txt",
        "NO WARRANTY\n\n"
        "GPL-2.0 runtime components are provided WITHOUT ANY WARRANTY; "
        "without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.\n",
    )
    _write_text(
        output_dir / "licenses" / "NO-WARRANTY-LGPL.txt",
        "NO WARRANTY\n\n"
        "LGPL runtime components are provided WITHOUT ANY WARRANTY; "
        "without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.\n",
    )
    _write_text(
        output_dir / "licenses" / "LGPL-RUNTIME-NOTICE.txt",
        "LGPL Runtime Notice\n\n"
        "LGPL components in this image are included as unmodified runtime dependencies. "
        "Use the exact component identity recorded in THIRD-PARTY-COMPLIANCE.json to retrieve "
        "the corresponding upstream source and license text.\n",
    )
    _write_text(
        output_dir / "licenses" / "source-offer.md",
        "# Source Access\n\n"
        "For copyleft runtime components redistributed in this image, use the exact package "
        "or release identity recorded in THIRD-PARTY-COMPLIANCE.json to retrieve complete "
        "corresponding source from the matching upstream package source, release source archive, "
        "or internal repository named in the compliance record. If a release uses a written offer, "
        "publish that offer beside this file before distributing the image.\n",
    )
    return status


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Wright MCP bundle config")
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    generate(args.bundle, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
