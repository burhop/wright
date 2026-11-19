"""Write the caller's explicit local bindings for the two reviewed example programs."""

import hashlib
import json
import sys
from pathlib import Path

REVIEWED = {
    "writer": {
        "version": "wright.mcp-binding/1",
        "provider": "example-write_points",
        "build": "1.0.0",
        "tool": "write_points",
        "contract_sha256": "27ed9e6381d5e3b3164cc2b200b74603a76197523dfaf1a9215700b32bbcbfc4",
    },
    "reader": {
        "version": "wright.mcp-binding/1",
        "provider": "example-measure_length",
        "build": "1.0.0",
        "tool": "measure_length",
        "contract_sha256": "8dd5b2f16c5b2217d4cbcbcd8fdf5f9face35f196caf4acfb8bc80530a3666ac",
    },
}


def configuration():
    here = Path(__file__).resolve().parent
    program = here / "provider.py"
    python = Path(sys.executable).resolve()
    pins = {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (python, program)
    }
    bindings = {}
    for alias, identity in REVIEWED.items():
        name = identity["tool"]
        bindings[alias] = {
            "command": str(python),
            "args": ["-I", "-B", str(program), name],
            "provider": identity["provider"],
            "build": identity["build"],
            "build_files": pins,
            "tools": {
                name: {"upstream": name, "contract_sha256": identity["contract_sha256"]}
            },
        }
    return bindings


if __name__ == "__main__":
    Path(sys.argv[1]).write_text(
        json.dumps(configuration(), indent=2), encoding="utf-8"
    )
