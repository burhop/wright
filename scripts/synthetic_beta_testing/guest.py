"""Explicit preparation-only SSH operations; never exposed to the customer AI."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import inspect
import json
from pathlib import Path
import re
import shlex
import subprocess

from .desktop import redact_evidence


def ssh_command(lab_root, port=18091, *, session_id="preparation"):
    """Trust each restored guest independently; never disable host-key checks."""
    root = Path(lab_root).absolute()
    if root.resolve() != root:
        raise ValueError("Guest lab path cannot contain symlinks")
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,47}", session_id):
        raise ValueError("Invalid guest session identity")
    if not isinstance(port, int) or not 1024 <= port <= 65535:
        raise ValueError("Guest SSH port must be an unprivileged numeric port")
    private = root / "private"
    hosts = private / "guest-hosts" / session_id
    if hosts.resolve() != hosts:
        raise ValueError("Guest known-hosts directory cannot contain symlinks")
    hosts.mkdir(parents=True, exist_ok=True, mode=0o700)
    known_hosts = hosts / "known-hosts"
    if known_hosts.is_symlink():
        raise ValueError("Guest known-hosts file cannot be a symlink")
    return [
        "ssh",
        "-i",
        str(private / "provision-key"),
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=5",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        f"UserKnownHostsFile={known_hosts}",
        "-p",
        str(port),
        "customer@127.0.0.1",
    ]


def verify_runtime_storage(profile):
    """Guest-only mount observation; fail before Hermes can write credentials."""
    import os

    profile = Path(profile)
    disk = Path("/var/lib/wright-beta/native-software")
    private = profile / "wright-private"
    target = profile / "wright-home"
    if profile != Path("/run/hermes-beta") or not Path(
        "/var/lib/wright-beta/provisioned.json"
    ).is_file():
        raise RuntimeError("Runtime storage requires the disposable beta guest")

    def observe(path):
        if path.resolve() != path or not path.is_dir():
            raise RuntimeError("Runtime storage path is missing or contains a symlink")
        rows = json.loads(subprocess.check_output(
            ["findmnt", "--json", "--bytes", "--output",
             "TARGET,FSTYPE,OPTIONS,SIZE", "--target", str(path)], text=True
        )).get("filesystems", [])
        if len(rows) != 1:
            raise RuntimeError("Runtime storage mount identity is ambiguous")
        return rows[0]

    def same_directory(left, right):
        a, b = left.stat(), right.stat()
        return (a.st_dev, a.st_ino) == (b.st_dev, b.st_ino)

    if observe(profile).get("fstype") != "tmpfs":
        raise RuntimeError("Hermes credentials must remain on tmpfs")
    software = observe(target)
    source = observe(disk)
    if (
        source.get("fstype") not in {"ext4", "xfs", "btrfs"}
        or software.get("target") != str(target)
        or software.get("fstype") != source.get("fstype")
        or not same_directory(disk, target)
        or target.stat().st_uid != 1000
    ):
        raise RuntimeError("Wright software is not on the verified guest disk")
    options = set(software.get("options", "").split(","))
    if "noexec" in options or not {"rw", "nosuid", "nodev"}.issubset(options):
        raise RuntimeError("Wright software mount options are incorrect")
    private_mount = observe(private)
    options = set(private_mount.get("options", "").split(","))
    if (
        private_mount.get("target") != str(private)
        or private_mount.get("fstype") != "tmpfs"
        or "noexec" in options
        or not {"nosuid", "nodev", "uid=1000", "gid=1000"}.issubset(options)
        or not ({"mode=700", "mode=0700"} & options)
        or int(private_mount.get("size", 0)) != 4 * 1024**3
    ):
        raise RuntimeError("Private Wright state must remain on its dedicated tmpfs")
    protected = []
    for name in ("data", "state", "logs"):
        path = target / name
        row = observe(path)
        options = set(row.get("options", "").split(","))
        if (
            row.get("target") != str(path)
            or row.get("fstype") != "tmpfs"
            or not same_directory(private / name, path)
            or not {"nosuid", "nodev"}.issubset(options)
        ):
            raise RuntimeError("Wright private state binding is missing or changed")
        protected.append(row)
    memory = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        name, _, value = line.partition(":")
        if name in {"MemTotal", "MemAvailable", "Shmem", "SwapTotal"}:
            memory[name + "_bytes"] = int(value.split()[0]) * 1024
    if memory.get("SwapTotal_bytes") != 0:
        raise RuntimeError("Guest swap must be disabled before supplying credentials")
    capacity = os.statvfs(disk)
    return {
        "target": str(target),
        "storage": "software on guest disk; private state on tmpfs",
        "software_mount": software,
        "software_source": str(disk),
        "private_mount": private_mount,
        "private_bindings": protected,
        "disk_available_bytes": capacity.f_bavail * capacity.f_frsize,
        "memory_observed_bytes": memory,
        "control_plane_token_storage": "tmpfs (data/control-plane.token)",
        "engineering_data_storage": "tmpfs; not moved in this milestone",
        "purge": "not qualified: mounted data cannot be removed; discard guest instead",
    }


def prepare_runtime_mount(profile):
    """Fresh guest only: disk software, RAM credentials, no runtime deletion."""
    import os

    profile = Path(profile)
    target = profile / "wright-home"
    private = profile / "wright-private"
    disk = Path("/var/lib/wright-beta/native-software")
    if (
        os.getuid() != 0
        or profile != Path("/run/hermes-beta")
        or not Path("/var/lib/wright-beta/provisioned.json").is_file()
        or profile.resolve() != profile
        or not profile.is_dir()
    ):
        raise RuntimeError("Storage preparation requires the fresh disposable guest")
    for path in (target, private, disk):
        if path.resolve() != path or path.exists() or path.is_symlink():
            raise RuntimeError("Existing Wright state was preserved; use a fresh guest")
    if subprocess.check_output(
        ["findmnt", "-n", "-o", "FSTYPE", "-T", str(disk.parent)], text=True
    ).strip() not in {"ext4", "xfs", "btrfs"}:
        raise RuntimeError("Software storage must be on the disposable guest disk")
    for path in (target, private, disk):
        path.mkdir(mode=0o700)
        os.chown(path, 1000, 1000)
    subprocess.run(
        ["mount", "-t", "tmpfs", "-o",
         "exec,nosuid,nodev,uid=1000,gid=1000,mode=0700,size=4G",
         "wright-beta-private-state", str(private)], check=True
    )
    subprocess.run(["mount", "--bind", str(disk), str(target)], check=True)
    subprocess.run(
        ["mount", "-o", "remount,bind,rw,exec,nosuid,nodev", str(target)],
        check=True,
    )
    for name in ("data", "state", "logs"):
        source, destination = private / name, target / name
        for path in (source, destination):
            path.mkdir(mode=0o700)
            os.chown(path, 1000, 1000)
        subprocess.run(
            ["mount", "--bind", str(source), str(destination)], check=True
        )
    return verify_runtime_storage(profile)


def prepare_guest_display():
    """Keep only the disposable customer's desktop accessible during observation."""
    import signal

    home = Path("/home/customer")
    if os.getuid() != 0 or not Path(
        "/var/lib/wright-beta/provisioned.json"
    ).is_file():
        raise RuntimeError("Desktop preparation requires the disposable beta guest")
    autostart = home / ".config/autostart"
    autostart.mkdir(parents=True, exist_ok=True)
    os.chown(autostart, 1000, 1000)
    lockers = {"light-locker", "xfce4-screensaver", "xscreensaver"}
    for name in sorted(lockers):
        path = autostart / f"{name}.desktop"
        if path.is_symlink():
            raise RuntimeError("Guest desktop configuration contains a symlink")
        path.write_text(
            "[Desktop Entry]\nType=Application\nName=Disposable beta desktop\n"
            "Hidden=true\n"
        )
        os.chown(path, 1000, 1000)
    stopped = []
    for process in Path("/proc").glob("[0-9]*"):
        try:
            if process.stat().st_uid != 1000:
                continue
            executable = (process / "exe").resolve(strict=True)
            if executable.parent == Path("/usr/bin") and executable.name in lockers:
                os.kill(int(process.name), signal.SIGTERM)
                stopped.append({"pid": int(process.name), "name": executable.name})
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    command = [
        "runuser", "-u", "customer", "--", "env", "DISPLAY=:0",
        "XAUTHORITY=/home/customer/.Xauthority", "xset", "s", "off", "-dpms",
    ]
    result = subprocess.run(command, capture_output=True, text=True, timeout=10)
    if result.returncode:
        raise RuntimeError("Disposable desktop display is not ready")
    return {
        "scope": "Disposable guest only; baseline and host unchanged",
        "idle_lock_autostart": "disabled for customer",
        "screensaver_and_dpms": "disabled on guest display :0",
        "stopped_locker_processes": stopped,
        "visible_access": "requires handoff screenshot; configuration is not UI evidence",
    }


def supply_runtime_access(
    lab_root, auth_source, *, port=18091, session_id="preparation"
):
    """Only after explicit VM-credential approval; no refresh credential transfer.

    The entire supported HERMES_HOME is on guest /run tmpfs so atomic auth-store
    replacement cannot turn a symlink into a persistent credential file.
    """
    source_path = Path(auth_source)
    before = hashlib.sha256(source_path.read_bytes()).hexdigest()
    source = json.loads(source_path.read_text())
    candidates = source.get("credential_pool", {}).get("openai-codex", [])
    usable = [
        item
        for item in candidates
        if item.get("access_token")
        and item.get("last_status")
        not in {
            "exhausted",
            "rejected",
            "invalid",
            "failed",
            "expired",
            "revoked",
            "disabled",
        }
    ]
    if not usable:
        raise ValueError(
            "No usable existing Codex credential; a supported sign-in is required"
        )
    selected = usable[0]
    entry = {
        key: selected[key]
        for key in (
            "id",
            "auth_type",
            "priority",
            "source",
            "access_token",
            "base_url",
            "last_refresh",
        )
        if key in selected
    }
    entry.update(label="isolated-guest-access", request_count=0)
    if entry.get("base_url") not in (None, "https://chatgpt.com/backend-api/codex"):
        raise ValueError("Unexpected configured model endpoint")
    payload = {
        "auth": {
            "version": 1,
            "active_provider": "openai-codex",
            "credential_pool": {"openai-codex": [entry]},
        },
        "storage_guard": (
            "import json,subprocess\nfrom pathlib import Path\n"
            + inspect.getsource(verify_runtime_storage)
            + '\nprint(json.dumps(verify_runtime_storage("/run/hermes-beta")))\n'
        ),
        "config": "model:\n  provider: openai-codex\n  default: gpt-6.1-sol\n  base_url: https://chatgpt.com/backend-api/codex\n",
    }
    program = (
        "import sys,json,pathlib,os,subprocess\nfrom pathlib import Path\n"
        + inspect.getsource(verify_runtime_storage)
        + "\n"
        + inspect.getsource(prepare_runtime_mount)
        + "\n"
        + inspect.getsource(prepare_guest_display)
        + """
value=json.load(sys.stdin)
subprocess.run(["swapoff","-a"],check=True)
display=prepare_guest_display()
profile=pathlib.Path("/run/hermes-beta");profile.mkdir(mode=0o700,exist_ok=True)
assert subprocess.check_output(["findmnt","-n","-o","FSTYPE","-T",str(profile)],text=True).strip()=="tmpfs"
os.chown(profile,1000,1000)
temporary=profile/"tmp";temporary.mkdir(mode=0o700,exist_ok=True);os.chown(temporary,1000,1000)
runtime_mount=prepare_runtime_mount(profile)
guard=pathlib.Path("/usr/local/lib/wright-beta/check-runtime-storage.py")
if guard.resolve()!=guard or guard.exists():raise RuntimeError("Existing storage guard was preserved; use a fresh guest")
guard.parent.mkdir(parents=True,exist_ok=True)
guard.write_text(value["storage_guard"]);guard.chmod(0o644)
for name,body in [("auth.json",json.dumps(value["auth"])),("config.yaml",value["config"])]:
 p=profile/name;p.write_text(body);p.chmod(0o600);os.chown(p,1000,1000)
wrapper=pathlib.Path("/usr/local/bin/hermes")
if wrapper.is_symlink():wrapper.unlink()
wrapper.write_text('#!/bin/sh'+chr(10)+'python3 /usr/local/lib/wright-beta/check-runtime-storage.py >/dev/null || exit $?'+chr(10)+'exec env HERMES_HOME=/run/hermes-beta WRIGHT_HOME=/run/hermes-beta/wright-home TMPDIR=/run/hermes-beta/tmp /home/customer/.hermes/hermes-agent/venv/bin/hermes "$@"'+chr(10))
wrapper.chmod(0o755)
print(json.dumps({"runtime_profile":"/run/hermes-beta","storage":"tmpfs","runtime_mount":runtime_mount,"desktop_preparation":display,"refresh_token_transferred":False,"swap":"disabled","wright_state":"/run/hermes-beta/wright-home (disk software; private state tmpfs; same-boot reopen only)","model":"gpt-6.1-sol","provider":"openai-codex"}))
"""
    )
    result = subprocess.run(
        ssh_command(lab_root, port, session_id=session_id)
        + ["sudo -n python3 -c " + shlex.quote(program)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode:
        raise RuntimeError(
            "Guest runtime access preparation failed: "
            + str(redact_evidence(result.stderr[-2000:]))
        )
    receipt = json.loads(result.stdout)
    receipt.update(
        supplied_at=datetime.now(timezone.utc).isoformat(),
        original_auth_unchanged=before
        == hashlib.sha256(source_path.read_bytes()).hexdigest(),
        approval="User explicitly approved temporary access token in this VM",
    )
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab-root", type=Path, required=True)
    parser.add_argument("--port", type=int, default=18091)
    parser.add_argument("--session", default="preparation")
    commands = parser.add_subparsers(dest="command", required=True)
    runtime = commands.add_parser("supply-runtime-access")
    runtime.add_argument("--auth-source", type=Path, required=True)
    runtime.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    receipt = supply_runtime_access(
        args.lab_root, args.auth_source, port=args.port, session_id=args.session
    )
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))


if __name__ == "__main__":
    main()
