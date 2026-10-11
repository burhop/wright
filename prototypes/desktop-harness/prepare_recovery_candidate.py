"""Make a private recovery candidate without changing the Windows handoff target.

This temporary copy is a qualification fixture, not a second maintained runtime.
Only Wright's reviewed backend patch is applied. The locked feature environment
still supplies shared packages; the manifest records that explicit limitation.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def prepare(destination):
    origin = Path(__file__).resolve().parent
    destination = destination.resolve()
    if destination.is_relative_to(origin) or origin.is_relative_to(destination):
        raise ValueError("Use a separate fresh private candidate directory")
    destination.mkdir(parents=True, mode=0o700, exist_ok=False)
    names = (
        "desktop_backend.py",
        "mcp_bridge.py",
        "preview_server.py",
        "protocol_probe.py",
        "restart_reconcile_probe.py",
    )
    files = {}
    for name in names:
        source = origin / name
        shutil.copyfile(source, destination / name)
        files[name] = {
            "original_sha256": hashlib.sha256(source.read_bytes()).hexdigest()
        }
    patch = origin / "recovery-admission.patch"
    command = ["git", "apply", "-p3"]
    subprocess.run([*command, "--check", str(patch)], cwd=destination, check=True)
    subprocess.run([*command, str(patch)], cwd=destination, check=True)
    for name in names:
        files[name]["candidate_sha256"] = hashlib.sha256(
            (destination / name).read_bytes()
        ).hexdigest()
    changed = [
        name
        for name, hashes in files.items()
        if hashes["original_sha256"] != hashes["candidate_sha256"]
    ]
    if changed != ["desktop_backend.py"]:
        raise ValueError("The candidate changes more than the reviewed backend patch")
    manifest = {
        "status": "isolated temporary qualification; main Windows candidate unchanged",
        "origin": str(origin),
        "files": files,
        "reviewable_patch": str(patch),
        "patch_sha256": hashlib.sha256(patch.read_bytes()).hexdigest(),
        "code_baseline": "current local worktree; dependencies imported from locked feature environment",
    }
    (destination / "candidate.json").write_text(json.dumps(manifest, indent=2))
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", required=True, type=Path)
    args = parser.parse_args()
    result = prepare(args.candidate_dir)
    print(
        json.dumps(
            {
                "candidate": str(args.candidate_dir.resolve()),
                "patch_sha256": result["patch_sha256"],
                "changed_runtime_files": ["desktop_backend.py"],
            }
        )
    )
