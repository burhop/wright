"""Reproducible commands for the approved ARM64/KVM disposable customer lab.

This provisions a real guest through an existing Docker daemon and KVM device.
It does not install or reconfigure host virtualization. Invoke with PYTHONPATH
pointing at the repository's scripts directory; no product runtime imports occur.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import uuid
import zlib

from .vm import VMBackend, VMError, sha256


DEFAULT_LAUNCHER = (
    "sha256:172e37d60f74c316521b1ff81d9d3d228e76809b3c917aa3a0feee9ecf2f55ee"
)
DEFAULT_IMAGE_SHA256 = (
    "50e24e1fb79e89116e939d90aa7738f7af48c442fa1bc2510131e0b39c50348e"
)
DEFAULT_IMAGE_URL = (
    "https://cloud-images.ubuntu.com/noble/20261017/noble-server-cloudimg-arm64.img"
)
MAX_IMAGE_BYTES = 8 * 1024**3


def _run(argv, timeout=30):
    result = subprocess.run(
        argv, capture_output=True, text=True, timeout=timeout, check=False
    )
    if result.returncode:
        raise VMError(f"Command failed ({argv[0]}): {result.stderr[-2000:]}")
    return result.stdout.strip()


def _real_root(path):
    root = Path(path).absolute()
    if root.resolve() != root:
        raise VMError("Lab parent must be a real absolute path without symlinks")
    return root


def _write_json(path, value):
    if path.is_symlink() or path.with_suffix(".json.tmp").is_symlink():
        raise VMError("Refusing symlinked lab configuration")
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n")
    temporary.replace(path)


def _launcher_identity(identity):
    if not isinstance(identity, str) or not re.fullmatch(
        r"sha256:[0-9a-f]{64}", identity
    ):
        raise VMError("Launcher must be an immutable local sha256 image ID")
    observed = _run(["docker", "image", "inspect", identity, "--format", "{{.Id}}"])
    if observed != identity:
        raise VMError("Docker launcher image identity mismatch")


def init_lab(lab_root, launcher_image=DEFAULT_LAUNCHER, ssh_port=18091, kvm_gid=None):
    root = _real_root(lab_root)
    if not isinstance(ssh_port, int) or not 1024 <= ssh_port <= 65535:
        raise VMError("SSH host port must be an unprivileged numeric port")
    _launcher_identity(launcher_image)
    device = os.stat("/dev/kvm")
    if not stat.S_ISCHR(device.st_mode):
        raise VMError("Existing /dev/kvm is not a character device")
    selected_gid = device.st_gid if kvm_gid is None else kvm_gid
    if selected_gid != device.st_gid:
        raise VMError("KVM group must match the existing device")
    backend = VMBackend(root / "machine")
    configuration = {
        "schema": 1,
        "owner": backend.owner,
        "architecture": "aarch64",
        "launcher_image": launcher_image,
        "ssh_port": ssh_port,
        "uid": os.getuid(),
        "gid": os.getgid(),
        "kvm_gid": selected_gid,
        "memory_mib": 8192,
        "cpus": 4,
        "overlay_gib": 24,
        "created_at_unix": time.time(),
        "baseline_status": "recipe-only-until-installed-observation",
    }
    config_path = root / "provision.json"
    if config_path.exists():
        existing = load_config(root)
        for field in configuration.keys() - {"created_at_unix", "baseline_status"}:
            if existing[field] != configuration[field]:
                raise VMError(
                    f"Refusing to replace existing lab configuration: {field}"
                )
        return existing
    _write_json(config_path, configuration)
    return configuration


def load_config(lab_root):
    root = _real_root(lab_root)
    path = root / "provision.json"
    if path.is_symlink():
        raise VMError("Lab configuration cannot be a symlink")
    config = json.loads(path.read_text())
    backend = VMBackend(root / "machine")
    if config.get("schema") != 1 or config.get("owner") != backend.owner:
        raise VMError("Lab configuration ownership/schema mismatch")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", config.get("launcher_image", "")):
        raise VMError("Lab launcher identity is not immutable")
    if config.get("architecture") != "aarch64":
        raise VMError("Only the approved ARM64 guest backend is implemented")
    port = config.get("ssh_port")
    if not isinstance(port, int) or not 1024 <= port <= 65535:
        raise VMError("SSH host port must be an unprivileged numeric port")
    if config.get("uid") != os.getuid() or config.get("gid") != os.getgid():
        raise VMError("Lab must run as its recorded unprivileged owner")
    if (
        config.get("memory_mib") != 8192
        or config.get("cpus") != 4
        or config.get("overlay_gib") != 24
    ):
        raise VMError("Lab resource limits differ from the approved backend")
    if not isinstance(config.get("kvm_gid"), int) or config["kvm_gid"] < 0:
        raise VMError("Invalid recorded KVM group")
    return config


def image_prefix(lab_root, config):
    root = _real_root(lab_root)
    return [
        "docker",
        "run",
        "--rm",
        "--pull",
        "never",
        "--network",
        "none",
        "--user",
        f"{config['uid']}:{config['gid']}",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,mode=1777",
        "--volume",
        f"{root}:{root}",
        config["launcher_image"],
    ]


def backend_for(lab_root, config=None):
    root = _real_root(lab_root)
    config = load_config(root) if config is None else config
    return VMBackend(
        root / "machine", launcher_prefix=image_prefix(root, config), timeout=30
    )


def download_image(
    lab_root,
    url=DEFAULT_IMAGE_URL,
    expected_sha256=DEFAULT_IMAGE_SHA256,
    filename="noble-server-cloudimg-arm64.img",
):
    root = _real_root(lab_root)
    load_config(root)
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise VMError("OS download requires an exact SHA256")
    parsed = urllib.parse.urlparse(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        raise VMError(
            "OS image URL must use authenticated HTTPS without URL credentials"
        )
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}", filename):
        raise VMError("Image filename must be a simple lab-local name")
    directory = root / "images"
    directory.mkdir(exist_ok=True)
    if directory.resolve() != directory:
        raise VMError("Images directory cannot be a symlink")
    target = directory / filename
    if target.exists() or target.is_symlink():
        if target.is_symlink() or sha256(target) != expected_sha256:
            raise VMError("Existing image has another identity; it was preserved")
        return {"path": str(target), "sha256": expected_sha256, "downloaded": False}
    partial = directory / f".{filename}.{uuid.uuid4().hex}.part"
    digest = hashlib.sha256()
    count = 0
    deadline = time.monotonic() + 900
    # urllib's default TLS context verifies host and CA. Reject redirects to HTTP.
    try:
        with (
            urllib.request.urlopen(url, timeout=30) as response,
            partial.open("xb") as output,
        ):
            if urllib.parse.urlparse(response.geturl()).scheme != "https":
                raise VMError("Image download redirected away from HTTPS")
            while True:
                block = response.read(1024 * 1024)
                if not block:
                    break
                count += len(block)
                if count > MAX_IMAGE_BYTES or time.monotonic() > deadline:
                    raise VMError("Image download exceeded byte/time budget")
                digest.update(block)
                output.write(block)
        if digest.hexdigest() != expected_sha256:
            raise VMError(
                "Downloaded OS image SHA256 mismatch; partial retained for diagnosis"
            )
        partial.replace(target)
    except Exception:
        # Retain failed bytes; never promote them to an installable baseline.
        raise
    receipt = {
        "path": str(target),
        "sha256": expected_sha256,
        "bytes": count,
        "url": url,
        "downloaded": True,
        "downloaded_at_unix": time.time(),
    }
    _write_json(directory / f"{filename}.json", receipt)
    return receipt


def _public_key(value):
    text = value.strip()
    if (
        "\n" in text
        or "\r" in text
        or not re.fullmatch(
            r"(?:ssh-ed25519|ssh-rsa|ecdsa-sha2-nistp(?:256|384|521)) [A-Za-z0-9+/=]+(?: [^\r\n]*)?",
            text,
        )
    ):
        raise VMError(
            "Expected one OpenSSH public key; no private key or multiline data"
        )
    if len(text) > 16000:
        raise VMError("SSH public key exceeds budget")
    return text


def _ensure_capacity(lab_root, config, overlay):
    """Grow a small image to the declared minimum; never shrink a saved baseline."""
    prefix = image_prefix(lab_root, config)
    info = json.loads(
        _run(prefix + ["qemu-img", "info", "--output=json", str(overlay)])
    )
    current = info.get("virtual-size")
    if not isinstance(current, int) or isinstance(current, bool) or current <= 0:
        raise VMError("Cannot establish overlay virtual disk size")
    minimum = config["overlay_gib"] * 1024**3
    if current < minimum:
        _run(prefix + ["qemu-img", "resize", str(overlay), f"{config['overlay_gib']}G"])
        return minimum
    return current


def prepare_session(
    lab_root,
    session_id,
    base_image,
    base_sha256,
    public_key=None,
    no_seed=False,
    clone_seed=False,
):
    root = _real_root(lab_root)
    config = load_config(root)
    _launcher_identity(config["launcher_image"])
    backend = backend_for(root, config)
    base = Path(base_image).absolute()
    if base.resolve() != base or not base.is_relative_to(root):
        raise VMError("Base image must be a real file inside this lab")
    if no_seed and clone_seed:
        raise VMError("Choose either a minimal clone seed or explicit no seed")
    if no_seed and public_key is not None:
        raise VMError("A clean baseline clone cannot carry provisioning SSH keys")
    if not no_seed and public_key is None:
        raise VMError(
            "Preparation requires a public SSH key, or explicit --no-seed for a frozen baseline"
        )
    key = None if no_seed else _public_key(public_key)
    manifest = backend.prepare(base, base_sha256, session_id)
    path = backend._session(session_id)
    virtual_size = _ensure_capacity(root, config, manifest["overlay"])
    seed = None
    template = None
    if not no_seed:
        template = (
            Path(__file__).parent
            / "assets"
            / (
                "hermes-clone.cloud-init.yaml"
                if clone_seed
                else "hermes-baseline.cloud-init.yaml"
            )
        )
        rendered = template.read_text().replace('"@@SSH_PUBLIC_KEY@@"', json.dumps(key))
        if re.search(r"@@[A-Z_]+@@", rendered):
            raise VMError("Cloud-init template has unresolved placeholders")
        user_data = path / "user-data.yaml"
        user_data.write_text(rendered)
        metadata = path / "meta-data.yaml"
        metadata.write_text(
            f"instance-id: beta-{config['owner']}-{session_id}\nlocal-hostname: wright-beta-customer\n"
        )
        seed = path / "seed.img"
        _run(
            image_prefix(root, config)
            + ["cloud-localds", str(seed), str(user_data), str(metadata)]
        )
    receipt = {
        "schema": 1,
        "owner": config["owner"],
        "session_id": session_id,
        "seed_path": str(seed) if seed else None,
        "seed_sha256": sha256(seed) if seed else None,
        "template_sha256": sha256(template) if template else None,
        "seed_mode": "none"
        if no_seed
        else "restored-baseline-access"
        if clone_seed
        else "baseline-provisioning",
        "base_sha256": base_sha256,
        "minimum_overlay_gib": config["overlay_gib"],
        "virtual_size_bytes": virtual_size,
        "credential_source": "none; test access must be attached after restoration",
        "baseline_assertion": "not verified by provisioning",
    }
    _write_json(path / "provision.json", receipt)
    return {**manifest, "provision": receipt}


def _session_receipt(backend, session_id):
    path, _ = backend._load(session_id)
    receipt_path = path / "provision.json"
    if receipt_path.is_symlink():
        raise VMError("Session provisioning receipt cannot be a symlink")
    receipt = json.loads(receipt_path.read_text())
    if receipt.get("owner") != backend.owner or receipt.get("session_id") != session_id:
        raise VMError("Session provisioning receipt ownership mismatch")
    seed = receipt.get("seed_path")
    if seed:
        if (
            Path(seed) != path / "seed.img"
            or Path(seed).is_symlink()
            or sha256(Path(seed)) != receipt.get("seed_sha256")
        ):
            raise VMError("Cloud-init seed identity changed")
    return path, receipt


def _clear_absent_container_id(path):
    cidfile = path / "container.id"
    if not cidfile.exists() and not cidfile.is_symlink():
        return
    if cidfile.is_symlink():
        raise VMError("Container identity file cannot be a symlink")
    cid = cidfile.read_text().strip()
    if not re.fullmatch(r"[0-9a-f]{64}", cid):
        raise VMError("Cannot establish stale container identity")
    present = _run(
        [
            "docker",
            "container",
            "ls",
            "--all",
            "--no-trunc",
            "--filter",
            f"id={cid}",
            "--format",
            "{{.ID}}",
        ]
    )
    if present:
        raise VMError(
            "Recorded container still exists; inspect/stop the exact owned guest first"
        )
    # Docker successfully answered that the exact CID is absent, not a daemon error.
    cidfile.unlink()


def start_arguments(lab_root, config, backend, session_id):
    root = _real_root(lab_root)
    path, receipt = _session_receipt(backend, session_id)
    _, manifest = backend._load(session_id)
    base = Path(manifest["base_image"])
    if base.resolve() != base or not base.is_relative_to(root):
        raise VMError("Recorded base image escapes this lab")
    prefix = [
        "docker",
        "run",
        "--rm",
        "--pull",
        "never",
        "--user",
        f"{config['uid']}:{config['gid']}",
        "--group-add",
        str(config["kvm_gid"]),
        "--device",
        "/dev/kvm:/dev/kvm:rwm",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,mode=1777",
        "--memory",
        "10g",
        "--cpus",
        "4",
        "--volume",
        f"{root}:{root}",
        "--publish",
        f"127.0.0.1:{config['ssh_port']}:2222",
        "--label",
        f"wright.synthetic-beta.owner={backend.owner}",
        "--label",
        f"wright.synthetic-beta.session={session_id}",
        "--cidfile",
        str(path / "container.id"),
    ]
    images = root / "images"
    if images.is_dir():
        if images.resolve() != images:
            raise VMError("Images directory cannot be a symlink")
        prefix += ["--volume", f"{images}:{images}:ro"]
    prefix += ["--volume", f"{base}:{base}:ro"]
    prefix.append(config["launcher_image"])
    arguments = [
        "-machine",
        "virt,accel=kvm",
        "-cpu",
        "host",
        "-smp",
        "4",
        "-m",
        "8192",
        "-bios",
        "/usr/share/qemu-efi-aarch64/QEMU_EFI.fd",
        "-display",
        "none",
        "-device",
        "virtio-gpu-pci,xres=1280,yres=800",
        "-device",
        "qemu-xhci",
        "-device",
        "usb-kbd",
        "-device",
        "usb-tablet",
        "-netdev",
        "user,id=net0,hostfwd=tcp:0.0.0.0:2222-:22",
        "-device",
        "virtio-net-pci,netdev=net0,romfile=",
        "-serial",
        f"file:{path / 'serial.log'}",
    ]
    if receipt.get("seed_path"):
        arguments += [
            "-drive",
            f"file={receipt['seed_path']},if=virtio,format=raw,readonly=on",
        ]
    return prefix, arguments


def start_session(lab_root, session_id):
    root = _real_root(lab_root)
    config = load_config(root)
    _launcher_identity(config["launcher_image"])
    backend = backend_for(root, config)
    if backend.state(session_id)["live"]:
        raise VMError("Guest is already running")
    path, _ = _session_receipt(backend, session_id)
    _clear_absent_container_id(path)
    prefix, arguments = start_arguments(root, config, backend, session_id)
    return backend.start(session_id, arguments, start_launcher_prefix=prefix)


def reset_session(lab_root, session_id):
    root = _real_root(lab_root)
    config = load_config(root)
    _launcher_identity(config["launcher_image"])
    backend = backend_for(root, config)
    path, _ = _session_receipt(backend, session_id)
    if backend.state(session_id)["live"]:
        raise VMError("Refusing reset of a live guest")
    _clear_absent_container_id(path)
    manifest = backend.reset(session_id)
    virtual_size = _ensure_capacity(root, config, manifest["overlay"])
    receipt_path = path / "provision.json"
    receipt = json.loads(receipt_path.read_text())
    receipt["virtual_size_bytes"] = virtual_size
    _write_json(receipt_path, receipt)
    return manifest


def _bare_git_file(relative, path):
    """Qualify the bounded dumb-HTTP adapter route, never execute Git hooks."""
    if relative.parts[0] != "adapter.git":
        return False, False
    inside = Path(*relative.parts[1:]).as_posix()
    metadata = {
        "HEAD",
        "config",
        "description",
        "packed-refs",
        "shallow",
        "info/refs",
        "info/exclude",
        "objects/info/packs",
    }
    if inside in metadata or re.fullmatch(
        r"refs/(?:heads|tags)/[A-Za-z0-9_./-]+", inside
    ):
        return True, False
    if re.fullmatch(r"objects/[0-9a-f]{2}/[0-9a-f]{38}", inside):
        compressed = path.read_bytes()
        if len(compressed) > 16 * 1024**2:
            raise VMError("Adapter Git object exceeds inspection budget")
        decoder = zlib.decompressobj()
        value = decoder.decompress(compressed, 16 * 1024**2 + 1)
        if len(value) > 16 * 1024**2 or not decoder.eof or decoder.unused_data:
            raise VMError("Adapter Git object has invalid or oversized compressed data")
        expected = relative.parts[-2] + relative.parts[-1]
        if hashlib.sha1(value).hexdigest() != expected:
            raise VMError("Adapter Git object identity mismatch")
        header, separator, body = value.partition(b"\0")
        if not separator or not re.fullmatch(
            rb"(?:blob|tree|commit|tag) [0-9]+", header
        ):
            raise VMError("Adapter Git object header is invalid")
        if int(header.split(b" ")[1]) != len(body):
            raise VMError("Adapter Git object size is invalid")
        if b"PRIVATE KEY-----" in body:
            raise VMError("Adapter Git object contains private-key material")
        return True, True
    raise VMError(
        "Only bare adapter Git metadata/refs/loose objects are supported; remove hooks and retain exact adapter identity"
    )


def _public_inventory(lab_root):
    """Inspect only deliberately staged public material, never the lab parent."""
    from .desktop import redact_evidence

    root = _real_root(lab_root)
    public = root / "public"
    if public.resolve() != public or not public.is_dir():
        raise VMError("Candidate server requires a real LAB/public staging directory")
    rows = []
    total = 0
    allowed = {
        ".whl",
        ".zip",
        ".gz",
        ".html",
        ".md",
        ".txt",
        ".json",
        ".css",
        ".js",
        ".svg",
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
    }
    binary = {".whl", ".zip", ".gz", ".png", ".jpg", ".jpeg", ".webp"}
    for path in sorted(public.rglob("*")):
        relative = path.relative_to(public)
        if path.is_symlink() or path.resolve() != path:
            raise VMError("Public candidate content cannot contain symlinks")
        if any(part.startswith(".") for part in relative.parts):
            raise VMError("Hidden files are not public candidate material")
        if path.is_dir():
            continue
        git_file, git_binary = _bare_git_file(relative, path)
        if not path.is_file() or (path.suffix.lower() not in allowed and not git_file):
            raise VMError("Unsupported public candidate file type")
        if re.search(
            r"(?:auth|credential|cookie|private|provision-key|known.hosts|secret|token)",
            path.name,
            re.I,
        ):
            raise VMError(
                "Sensitive-looking file cannot be served as public candidate material"
            )
        if relative.as_posix() == "public-manifest.json":
            continue
        size = path.stat().st_size
        total += size
        if len(rows) >= 5000 or total > MAX_IMAGE_BYTES:
            raise VMError("Public candidate material exceeds file/byte budget")
        if path.suffix.lower() not in binary and not git_binary:
            if size > 16 * 1024**2:
                raise VMError("Public text exceeds credential-inspection budget")
            text = path.read_text()
            if (
                redact_evidence(text) != text
                or "PRIVATE KEY-----" in text
                or re.search(
                    r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", text
                )
            ):
                raise VMError(
                    "Public candidate text contains credential-shaped material"
                )
        rows.append(
            {"path": relative.as_posix(), "sha256": sha256(path), "bytes": size}
        )
    if not rows:
        raise VMError("No candidate material is staged for serving")
    return public, rows


def freeze_public(lab_root):
    root = _real_root(lab_root)
    config = load_config(root)
    public, rows = _public_inventory(root)
    manifest = {
        "schema": 1,
        "owner": config["owner"],
        "files": rows,
        "scope": "Only explicitly staged public candidate artifacts; archive identities are checked, not an exhaustive secret audit",
    }
    path = public / "public-manifest.json"
    if path.exists():
        if json.loads(path.read_text()) != manifest:
            raise VMError(
                "Frozen public material changed; retain this candidate and stage a new identity"
            )
    else:
        _write_json(path, manifest)
    return {"path": str(path), "sha256": sha256(path), "files": len(rows)}


def _owned_container(lab_root, session_id):
    root = _real_root(lab_root)
    config = load_config(root)
    backend = backend_for(root, config)
    path, _ = backend._load(session_id)
    if not backend.state(session_id).get("qmp_status"):
        raise VMError(
            "Candidate serving requires a live guest with verified QMP identity"
        )
    cidfile = path / "container.id"
    if cidfile.is_symlink():
        raise VMError("Container identity file cannot be a symlink")
    cid = cidfile.read_text().strip()
    if not re.fullmatch(r"[0-9a-f]{64}", cid):
        raise VMError("Cannot establish exact container identity")
    value = json.loads(_run(["docker", "container", "inspect", cid]))
    if not isinstance(value, list) or len(value) != 1:
        raise VMError("Container inspect result is ambiguous")
    observed = value[0]
    labels = observed.get("Config", {}).get("Labels", {}) or {}
    if (
        observed.get("Id") != cid
        or observed.get("Image") != config["launcher_image"]
        or not observed.get("State", {}).get("Running")
        or labels.get("wright.synthetic-beta.owner") != backend.owner
        or labels.get("wright.synthetic-beta.session") != session_id
    ):
        raise VMError("Container owner/session/image/running identity mismatch")
    return config, path, cid


def serve_public(lab_root, session_id):
    root = _real_root(lab_root)
    config, path, cid = _owned_container(root, session_id)
    public, rows = _public_inventory(root)
    manifest_path = public / "public-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("owner") != config["owner"] or manifest.get("files") != rows:
        raise VMError(
            "Public candidate manifest no longer matches exact staged artifacts"
        )
    digest = sha256(manifest_path)
    receipt_path = path / "public-server.json"
    if receipt_path.exists():
        previous = json.loads(receipt_path.read_text())
        if (
            previous.get("container_id") != cid
            or previous.get("manifest_sha256") != digest
        ):
            raise VMError(
                "Existing server receipt belongs to another container/candidate"
            )
    else:
        # No shell; the directory and operational arguments are separate argv items.
        program = """import functools,http.server,os,pathlib,sys
directory,logpath=sys.argv[1:]
log=open(logpath,"a",buffering=1);os.dup2(log.fileno(),1);os.dup2(log.fileno(),2)
handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory=directory)
http.server.ThreadingHTTPServer(("127.0.0.1",18092),handler).serve_forever()
"""
        _run(
            [
                "docker",
                "exec",
                "--detach",
                "--user",
                f"{config['uid']}:{config['gid']}",
                cid,
                "python3",
                "-c",
                program,
                str(public),
                str(path / "public-server.log"),
            ]
        )
    probe = """import hashlib,sys,time,urllib.request
expected=sys.argv[1]
for attempt in range(50):
 try:
  observed=hashlib.sha256(urllib.request.urlopen("http://127.0.0.1:18092/public-manifest.json",timeout=1).read()).hexdigest()
  assert observed==expected,"Served candidate identity mismatch"
  print(observed);break
 except OSError:
  if attempt==49:raise
  time.sleep(.1)
"""
    observed = _run(
        [
            "docker",
            "exec",
            "--user",
            f"{config['uid']}:{config['gid']}",
            cid,
            "python3",
            "-c",
            probe,
            digest,
        ],
        timeout=15,
    )
    if observed != digest:
        raise VMError("Candidate server did not prove its exact manifest identity")
    receipt = {
        "schema": 1,
        "owner": config["owner"],
        "session_id": session_id,
        "container_id": cid,
        "manifest_sha256": digest,
        "directory": str(public),
        "bind": "127.0.0.1",
        "port": 18092,
        "guest_url": "http://10.0.2.2:18092/",
        "host_port_published": False,
        "cleanup": "Server lifetime is confined to this owned QEMU container",
    }
    _write_json(receipt_path, receipt)
    return receipt


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab-root", required=True, type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    initialize = commands.add_parser("init")
    initialize.add_argument("--launcher-image", default=DEFAULT_LAUNCHER)
    initialize.add_argument("--ssh-port", type=int, default=18091)
    download = commands.add_parser("download-image")
    download.add_argument("--url", default=DEFAULT_IMAGE_URL)
    download.add_argument("--sha256", default=DEFAULT_IMAGE_SHA256)
    download.add_argument("--filename", default="noble-server-cloudimg-arm64.img")
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--session", required=True)
    prepare.add_argument("--base-image", required=True, type=Path)
    prepare.add_argument("--base-sha256", required=True)
    keys = prepare.add_mutually_exclusive_group()
    keys.add_argument("--ssh-public-key", type=Path)
    keys.add_argument("--ssh-public-key-stdin", action="store_true")
    seed_modes = prepare.add_mutually_exclusive_group()
    seed_modes.add_argument("--no-seed", action="store_true")
    seed_modes.add_argument(
        "--clone-seed",
        action="store_true",
        help="Attach a fresh public SSH key to a restored baseline; perform no package setup",
    )
    for command in ("start", "state", "stop", "reset"):
        commands.add_parser(command).add_argument("--session", required=True)
    commands.add_parser("freeze-public")
    commands.add_parser("serve-public").add_argument("--session", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            result = init_lab(args.lab_root, args.launcher_image, args.ssh_port)
        elif args.command == "download-image":
            result = download_image(args.lab_root, args.url, args.sha256, args.filename)
        elif args.command == "prepare":
            key = (
                args.ssh_public_key.read_text()
                if args.ssh_public_key
                else sys.stdin.read()
                if args.ssh_public_key_stdin
                else None
            )
            result = prepare_session(
                args.lab_root,
                args.session,
                args.base_image,
                args.base_sha256,
                key,
                args.no_seed,
                args.clone_seed,
            )
        elif args.command == "start":
            result = start_session(args.lab_root, args.session)
        elif args.command == "reset":
            result = reset_session(args.lab_root, args.session)
        elif args.command == "freeze-public":
            result = freeze_public(args.lab_root)
        elif args.command == "serve-public":
            result = serve_public(args.lab_root, args.session)
        else:
            backend = backend_for(args.lab_root)
            result = getattr(backend, args.command)(args.session)
        print(json.dumps(result, indent=2))
        return 0
    except (VMError, OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(
            json.dumps({"error": str(error), "command": args.command}), file=sys.stderr
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
