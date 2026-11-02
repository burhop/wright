"""Technical-clone preparation only; not an observed customer install route.

Copy a digest-checked cached AppImage to the disposable guest separately. This
script fetches the public pinned provider, installs it normally into a private
venv and prepares its matching GUI addon. It never invokes an engineering tool,
registers Wright bindings, starts FreeCAD, or changes a reusable baseline.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys


SOURCE_URL = "https://github.com/neka-nat/freecad-mcp.git"
SOURCE_COMMIT = "63acb305573194a011641ab13ccfb391fe95769f"
APPIMAGE_SHA256 = "8004e166dc5c516cc8e8d85a5f58b5d56c3836cf8652301c2e6b9e4b1fd27827"
SDK_VERSION = "1.28.1"
PROVIDER_VERSION = "0.1.18"
PACKAGES = [
    "xvfb",
    "xauth",
    "libgl1",
    "libegl1",
    "libxkbcommon-x11-0",
    "libxcb-cursor0",
    "libxrender1",
    "libxi6",
    "libxrandr2",
    "libxinerama1",
    "libxcursor1",
    "libxcomposite1",
    "libxdamage1",
    "libxtst6",
    "libfontconfig1",
    "libdbus-1-3",
]


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def check_guest():
    if os.getuid() != 1000 or Path.home() != Path("/home/customer"):
        raise RuntimeError("Run only as customer in the disposable technical clone")
    if platform.machine() != "aarch64":
        raise RuntimeError("This native recipe is ARM64 only")
    release = Path("/etc/os-release").read_text()
    if "ID=ubuntu\n" not in release or 'VERSION_ID="24.04"' not in release:
        raise RuntimeError("This recipe requires Ubuntu 24.04")
    if not Path("/var/lib/wright-beta/provisioned.json").is_file():
        raise RuntimeError("Disposable beta-guest marker is absent")


def run(argv, *, cwd=None, timeout=600):
    result = subprocess.run(
        argv, cwd=cwd, capture_output=True, text=True, check=False, timeout=timeout
    )
    if result.returncode:
        raise RuntimeError(
            f"Technical prerequisite failed ({argv[0]}), exit {result.returncode}: {result.stderr[-2000:]}"
        )
    return result.stdout.strip()


def prepare(appimage, output_root):
    check_guest()
    home = Path("/home/customer")
    source_image = Path(appimage).absolute()
    root = Path(output_root).absolute()
    if source_image.resolve() != source_image or not source_image.is_relative_to(home):
        raise RuntimeError(
            "AppImage must be an owned real file inside the guest customer home"
        )
    if (
        root.resolve() != root
        or not root.is_relative_to(home)
        or root == home
        or root.exists()
    ):
        raise RuntimeError(
            "Technical preparation root must be a fresh contained directory"
        )
    if digest(source_image) != APPIMAGE_SHA256:
        raise RuntimeError("Technical-cache AppImage SHA256 mismatch")
    root.mkdir(parents=True)
    # Normal package/provider installation; no Docker or historical source mount.
    run(["sudo", "-n", "apt-get", "update"], timeout=180)
    run(
        ["sudo", "-n", "apt-get", "install", "-y", "--no-install-recommends"] + PACKAGES
    )
    source = root / "provider"
    run(["git", "init", str(source)])
    run(["git", "-C", str(source), "remote", "add", "origin", SOURCE_URL])
    run(["git", "-C", str(source), "fetch", "--depth", "1", "origin", SOURCE_COMMIT])
    run(["git", "-C", str(source), "checkout", "--detach", "FETCH_HEAD"])
    if run(["git", "-C", str(source), "rev-parse", "HEAD"]) != SOURCE_COMMIT:
        raise RuntimeError("Provider checkout identity mismatch")
    venv = root / "venv"
    run(["python3", "-m", "venv", str(venv)])
    run([str(venv / "bin/pip"), "install", f"mcp[cli]=={SDK_VERSION}", str(source)])
    versions = json.loads(
        run(
            [
                str(venv / "bin/python"),
                "-c",
                "import importlib.metadata,json;print(json.dumps({n:importlib.metadata.version(n) for n in ['mcp','freecad-mcp']}))",
            ]
        )
    )
    if versions != {"mcp": SDK_VERSION, "freecad-mcp": PROVIDER_VERSION}:
        raise RuntimeError("Installed provider/SDK versions differ from qualification")
    (root / "pip-freeze.txt").write_text(run([str(venv / "bin/pip"), "freeze"]) + "\n")
    native = root / "native"
    native.mkdir()
    copied_image = native / "FreeCAD_1.1.1-Linux-aarch64-py311.AppImage"
    shutil.copy2(source_image, copied_image)
    copied_image.chmod(0o755)
    run([str(copied_image), "--appimage-extract"], cwd=native)
    application = native / "squashfs-root/AppRun"
    if not application.exists():
        raise RuntimeError("Extracted AppImage lacks AppRun")
    settings = {
        "remote_enabled": False,
        "allowed_ips": "127.0.0.1",
        "auto_start_rpc": True,
    }
    addon = source / "addon/FreeCADMCP"
    for parent in (
        home / ".local/share/FreeCAD",
        home / ".local/share/FreeCAD/v1-1",
        home / ".FreeCAD",
    ):
        destination = parent / "Mod/FreeCADMCP"
        if destination.exists() or destination.is_symlink():
            raise RuntimeError(
                "Existing FreeCAD addon was preserved; use a fresh technical clone"
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(addon, destination)
        (parent / "freecad_mcp_settings.json").write_text(json.dumps(settings) + "\n")
    readiness = home / "wright-readiness"
    readiness.mkdir(exist_ok=True)
    launcher = root / "start-freecad.sh"
    launcher.write_text(
        "#!/bin/sh\nexec env DISPLAY=:0 XAUTHORITY=/home/customer/.Xauthority "
        + shlex.quote(str(application))
        + ' "$@"\n'
    )
    launcher.chmod(0o755)
    receipt = {
        "scope": "technical clone only; not a customer installation observation",
        "source_url": SOURCE_URL,
        "source_commit": SOURCE_COMMIT,
        "versions": versions,
        "appimage_sha256": APPIMAGE_SHA256,
        "appimage_source": "explicit technical cache copied into guest",
        "mcp_command": [
            str(venv / "bin/freecad-mcp"),
            "--only-text-feedback",
            "--host",
            "127.0.0.1",
        ],
        "gui_start": str(launcher),
        "rpc_host": "127.0.0.1",
        "rpc_port": 9875,
        "operation": "Use the unchanged predeclared provider-operation.json after actual discovery",
        "readiness": "not assessed; FreeCAD was not started and no MCP tool was called",
        "baseline": "This technical clone must never become the Hermes-only customer baseline",
    }
    (root / "preparation.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--technical-preparation-only", action="store_true", required=True
    )
    parser.add_argument("--appimage", type=Path, required=True)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("/home/customer/wright-provider-readiness/freecad-001"),
    )
    args = parser.parse_args(argv)
    print(json.dumps(prepare(args.appimage, args.output_root), indent=2))


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
