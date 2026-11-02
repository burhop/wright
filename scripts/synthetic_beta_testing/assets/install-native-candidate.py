"""Technical calibration preparation through normal Hermes/native boundaries.

No download, model call, customer attribution, source checkout or fallback.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile


VERSION = "0.1.9"


def sha256(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def extract_candidate(bundle, destination):
    with tarfile.open(bundle) as archive:
        members, seen, size = [], set(), 0
        for member in archive:
            parts = PurePosixPath(member.name).parts
            if (
                not parts
                or parts[0] != "wright-candidate"
                or ".." in parts
                or not (member.isfile() or member.isdir())
                or tuple(parts) in seen
            ):
                raise RuntimeError(
                    "Bundle violates the fixed candidate archive boundary"
                )
            seen.add(tuple(parts))
            members.append(member)
            size += member.size
            if len(members) > 4000 or size > 4 * 1024**3:
                raise RuntimeError("Candidate extraction exceeds its file/byte budget")
        archive.extractall(destination, members=members, filter="data")


def check_runtime_mount(target):
    """Observe the fresh split storage prepared before model access was supplied."""
    if (
        target != Path("/run/hermes-beta/wright-home")
        or target.resolve() != target
        or not target.is_dir()
        or target.stat().st_uid != 1000
        or {path.name for path in target.iterdir()} != {"data", "state", "logs"}
        or any(any((target / name).iterdir()) for name in ("data", "state", "logs"))
    ):
        raise RuntimeError(
            "Wright requires fresh disk software storage and empty private state mounts"
        )
    guard = Path("/usr/local/lib/wright-beta/check-runtime-storage.py")
    if (
        guard.resolve() != guard
        or not guard.is_file()
        or guard.stat().st_uid != 0
        or guard.stat().st_mode & 0o022
    ):
        raise RuntimeError("Root-owned guest storage verifier is missing or changed")
    result = subprocess.run(
        ["python3", str(guard)], capture_output=True, text=True, check=True,
        timeout=10,
    )
    observed = json.loads(result.stdout)
    if observed.get("target") != str(target):
        raise RuntimeError("Guest storage verifier returned another Wright installation")
    return observed


def install(bundle, bundle_sha256, wheel_sha256):
    home, profile = Path("/home/customer"), Path("/run/hermes-beta")
    bundle = Path(bundle).absolute()
    if (
        Path.home() != home
        or os.getuid() != 1000
        or not Path("/var/lib/wright-beta/provisioned.json").is_file()
    ):
        raise RuntimeError("Run only in the fresh disposable customer guest")
    if not all(
        re.fullmatch(r"[0-9a-f]{64}", value) for value in (bundle_sha256, wheel_sha256)
    ):
        raise RuntimeError("Exact bundle and wheel SHA256 identities are required")
    if (
        bundle.resolve() != bundle
        or not bundle.is_relative_to(home)
        or sha256(bundle) != bundle_sha256
    ):
        raise RuntimeError("Candidate bundle path or identity mismatch")
    wright_home, plugin = (
        profile / "wright-home",
        profile / "plugins/wright/bootstrap.py",
    )
    root, receipt_path = (
        bundle.parent / "wright-candidate",
        bundle.parent / "technical-native-install.json",
    )
    if any(
        path.exists() or path.is_symlink()
        for path in (home / ".wright", plugin.parent, root, receipt_path)
    ):
        raise RuntimeError(
            "Existing Wright state/evidence was preserved; restore a fresh guest"
        )
    runtime_storage = check_runtime_mount(wright_home)
    if not (profile / "tmp").is_dir() or (profile / "tmp").stat().st_uid != 1000:
        raise RuntimeError(
            "Prepare customer-owned runtime access and TMPDIR before installation"
        )
    if (
        subprocess.check_output(
            ["findmnt", "-n", "-o", "FSTYPE", "-T", str(profile)], text=True
        ).strip()
        != "tmpfs"
    ):
        raise RuntimeError("Runtime Hermes profile must reside on tmpfs")
    extract_candidate(bundle, bundle.parent)
    wheel = root / f"wheelhouse/wright_engineering-{VERSION}-py3-none-any.whl"
    if sha256(wheel) != wheel_sha256:
        raise RuntimeError("Extracted native wheel identity mismatch")
    env = dict(
        os.environ,
        HERMES_HOME=str(profile),
        TMPDIR=str(profile / "tmp"),
        WRIGHT_HOME=str(wright_home),
        WRIGHT_RUNTIME_ARTIFACT=str(wheel),
        WRIGHT_RUNTIME_WHEELHOUSE=str(wheel.parent),
        WRIGHT_RUNTIME_VERSION=VERSION,
        WRIGHT_RUNTIME_CHANNEL="local_candidate",
        WRIGHT_RUNTIME_SHA256=wheel_sha256,
    )
    env.pop("WRIGHT_REPO_DIR", None)
    env.pop("PYTHONPATH", None)
    # SSH preparation must launch into the same desktop a normal customer uses.
    # Otherwise browser-based MCP sign-in silently has nowhere to open.
    env.update(DISPLAY=":0", XAUTHORITY=str(home / ".Xauthority"))
    # The frozen Ubuntu desktop uses Snap Firefox; SSH omits its desktop-entry
    # search path even though a normal desktop login includes it.
    desktop_dirs = env.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
    if Path("/var/lib/snapd/desktop").is_dir() and "/var/lib/snapd/desktop" not in desktop_dirs:
        desktop_dirs.append("/var/lib/snapd/desktop")
    env["XDG_DATA_DIRS"] = ":".join(desktop_dirs)
    desktop = subprocess.run(
        ["xset", "q"], env=env, capture_output=True, timeout=10
    )
    if desktop.returncode:
        raise RuntimeError("Disposable customer desktop is unavailable; preserve this preparation")
    receipt = {
        "scope": "Technical calibration preparation; not customer installation evidence",
        "runtime_storage": runtime_storage,
        "bundle_sha256": bundle_sha256,
        "wheel_sha256": wheel_sha256,
        "commands": [],
    }

    def save():
        receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")

    save()
    command = [
        "/usr/local/bin/hermes",
        "plugins",
        "install",
        (root / "adapter.git").as_uri(),
        "--enable",
    ]
    result = subprocess.run(
        command, env=env, input="y\n", capture_output=True, text=True, timeout=180
    )
    receipt["commands"].append(
        {
            "command": "hermes plugins install <frozen-file-URI> --enable",
            "returncode": result.returncode,
        }
    )
    save()
    if result.returncode or not plugin.is_file():
        raise RuntimeError(
            "Normal Hermes candidate installation failed; receipt retained, no retry performed"
        )
    receipt["plugin_bootstrap_sha256"] = sha256(plugin)
    receipt["adapter_commit"] = subprocess.check_output(
        ["git", "--git-dir", str(root / "adapter.git"), "rev-parse", "HEAD"], text=True
    ).strip()
    os.environ.update(
        env
    )  # This preparation process only; no saved model/profile changes.
    spec = importlib.util.spec_from_file_location(
        "installed_candidate_bootstrap", plugin
    )
    bootstrap = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bootstrap)
    for operation in ("start", "doctor"):
        value = bootstrap.invoke_lifecycle(operation)
        receipt["commands"].append(
            {
                "command": "installed adapter invoke_lifecycle " + operation,
                "ok": value.get("ok"),
                "code": value.get("code"),
                "state": value.get("state"),
            }
        )
        save()
        if value.get("ok") is not True:
            raise RuntimeError(
                "Native lifecycle failed; receipt retained, no retry performed"
            )
        if operation == "doctor":
            receipt["doctor_checks"] = {
                key: item.get("ok")
                for key, item in value.get("details", {}).get("checks", {}).items()
            }
    manifest = json.loads((wright_home / "state/installation.json").read_text())
    observed = manifest["runtimes"][manifest["active_runtime_id"]]
    if (
        observed["artifact_sha256"] != wheel_sha256
        or observed["version"] != VERSION
        or observed["source_channel"] != "local_candidate"
    ):
        raise RuntimeError("Installed native artifact identity mismatch")
    receipt["installed"] = {
        key: observed[key]
        for key in (
            "runtime_id",
            "version",
            "artifact_sha256",
            "source_channel",
            "python_version",
            "platform_tag",
            "status",
        )
    }
    receipt["manifest_sha256"] = sha256(wright_home / "state/installation.json")
    save()
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--technical-preparation-only", action="store_true", required=True
    )
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--bundle-sha256", required=True)
    parser.add_argument("--wheel-sha256", required=True)
    args = parser.parse_args(argv)
    print(
        json.dumps(
            install(args.bundle, args.bundle_sha256, args.wheel_sha256), indent=2
        )
    )


if __name__ == "__main__":
    main()
