"""Package existing passive code/profile dependencies; never execute engineering.

Usage: python build_inspection_resources.py /fresh/output.zip
The ordinary ZIP is a workflow input, not a new runtime or plugin format.
"""

import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[4]
PROFILES = (
    ROOT
    / "prototypes/desktop-harness/engineering-experience/evidence/support-profile-qualification/profiles"
)
SOURCES = {
    "passive_representations.py": ROOT
    / "packages/workspace_service/src/workspace_service/process_interfaces/representations.py",
    "inspect_manufacturing_package.py": ROOT
    / "scripts/engineering/inspect_manufacturing_package.py",
    "compare_handle_slices.py": ROOT / "scripts/engineering/compare_handle_slices.py",
    **{
        f"profiles/{name}.json": PROFILES / f"{name}.json"
        for name in ("machine", "process", "filament")
    },
}


def package():
    contents = {name: path.read_bytes() for name, path in SOURCES.items()}
    manifest = {
        "purpose": "Pinned passive handle-package inspection dependencies; not engineering approval",
        "files": {
            name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
            for name, data in contents.items()
        },
        "provider_scope": "Offline OrcaSlicer 2.5.0-alpha ARM64; separately qualified provider configuration required",
    }
    contents["manifest.json"] = (
        json.dumps(manifest, sort_keys=True, indent=2).encode() + b"\n"
    )
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(contents.items()):
            entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            # Preserve the accepted Unix metadata on every build host.
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data)
    return output.getvalue()


if __name__ == "__main__":
    data = package()
    with Path(sys.argv[1]).open("xb") as destination:
        destination.write(data)
    print(
        json.dumps(
            {
                "path": sys.argv[1],
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
        )
    )
