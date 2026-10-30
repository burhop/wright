"""Provisioning fixtures only; no Docker daemon, download or guest is used."""

import hashlib
import importlib
import json
from pathlib import Path
import sys

import pytest
import yaml


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
sys.path.insert(0, str(SCRIPTS))
provision = importlib.import_module("synthetic_beta_testing.provision")
vm = importlib.import_module("synthetic_beta_testing.vm")


@pytest.fixture
def lab(tmp_path, monkeypatch):
    root = tmp_path / "lab"
    backend = vm.VMBackend(root / "machine")
    config = {
        "schema": 1,
        "owner": backend.owner,
        "architecture": "aarch64",
        "launcher_image": provision.DEFAULT_LAUNCHER,
        "ssh_port": 18091,
        "uid": provision.os.getuid(),
        "gid": provision.os.getgid(),
        "kvm_gid": 994,
        "memory_mib": 8192,
        "cpus": 4,
        "overlay_gib": 24,
        "baseline_status": "fixture-not-real-VM",
    }
    provision._write_json(root / "provision.json", config)
    (root / "images").mkdir()
    base = root / "images/base.qcow2"
    base.write_bytes(b"Fixture OS image, not bootable")
    digest = hashlib.sha256(base.read_bytes()).hexdigest()
    calls = []

    def run(argv, timeout=30):
        calls.append(argv)
        if "qemu-img" in argv and "info" in argv:
            return json.dumps({"virtual-size": 2 * 1024**3})
        if "cloud-localds" in argv:
            Path(argv[argv.index("cloud-localds") + 1]).write_bytes(b"Fixture seed")
        return ""

    def create(argv, **kwargs):
        calls.append(argv)
        assert "qemu-img" in argv and "create" in argv
        Path(argv[-1]).write_bytes(b"Fixture overlay")
        return provision.subprocess.CompletedProcess(argv, 0, "", "")

    monkeypatch.setattr(provision, "_run", run)
    monkeypatch.setattr(provision, "_launcher_identity", lambda _: None)
    monkeypatch.setattr(vm.subprocess, "run", create)
    return root, config, backend, base, digest, calls


def prepare(lab, no_seed=False, public_key='ssh-ed25519 YWJj fixture: "comment"'):
    root, _, _, base, digest, _ = lab
    return provision.prepare_session(
        root,
        "customer-1",
        base,
        digest,
        public_key=None if no_seed else public_key,
        no_seed=no_seed,
    )


def test_exact_launcher_image_is_required(monkeypatch):
    calls = []
    monkeypatch.setattr(
        provision, "_run", lambda argv: calls.append(argv) or provision.DEFAULT_LAUNCHER
    )
    for mutable in ("ubuntu:24.04", "wright-lab:latest", "sha256:bad"):
        with pytest.raises(vm.VMError, match="immutable"):
            # Retrieve actual implementation: the lab fixture is not active here.
            provision._launcher_identity(mutable)
    assert calls == []
    provision._launcher_identity(provision.DEFAULT_LAUNCHER)
    assert calls[0][0:3] == ["docker", "image", "inspect"]
    monkeypatch.setattr(provision, "_run", lambda _: "sha256:" + "0" * 64)
    with pytest.raises(vm.VMError, match="identity mismatch"):
        provision._launcher_identity(provision.DEFAULT_LAUNCHER)


def test_preparation_is_networkless_and_launcher_filesystem_readonly(lab):
    root, config, _, _, _, _ = lab
    prefix = provision.image_prefix(root, config)
    assert prefix[prefix.index("--network") + 1] == "none"
    assert "--read-only" in prefix
    assert "--cap-drop" in prefix and "ALL" in prefix
    assert prefix[prefix.index("--user") + 1] == f"{config['uid']}:{config['gid']}"
    assert "--privileged" not in prefix
    assert prefix[-1] == config["launcher_image"]


def test_prepare_seed_has_safe_yaml_key_and_exact_hash(lab):
    root, config, _, _, digest, calls = lab
    result = prepare(lab)
    path = root / "machine/sessions/customer-1"
    parsed = yaml.safe_load((path / "user-data.yaml").read_text())
    assert parsed["users"][0]["ssh_authorized_keys"] == [
        'ssh-ed25519 YWJj fixture: "comment"'
    ]
    assert result["base_sha256"] == digest
    receipt = json.loads((path / "provision.json").read_text())
    assert receipt["seed_sha256"] == hashlib.sha256(b"Fixture seed").hexdigest()
    assert receipt["baseline_assertion"] == "not verified by provisioning"
    assert any("cloud-localds" in argv for argv in calls)
    assert any(
        argv[-3:] == ["resize", str(path / "disk.qcow2"), "24G"] for argv in calls
    )


def test_start_limits_ports_mounts_identity_and_guest_args(lab):
    root, config, backend, base, _, _ = lab
    prepare(lab)
    prefix, arguments = provision.start_arguments(root, config, backend, "customer-1")
    assert prefix[prefix.index("--publish") + 1] == "127.0.0.1:18091:2222"
    assert prefix[prefix.index("--memory") + 1] == "10g"
    assert prefix[prefix.index("--cpus") + 1] == "4"
    assert "--read-only" in prefix and "--privileged" not in prefix
    assert f"{base}:{base}:ro" in prefix
    assert f"{root / 'images'}:{root / 'images'}:ro" in prefix
    assert f"wright.synthetic-beta.owner={backend.owner}" in prefix
    assert "wright.synthetic-beta.session=customer-1" in prefix
    assert prefix[-1] == config["launcher_image"]
    assert arguments[arguments.index("-machine") + 1] == "virt,accel=kvm"
    assert "virtio-net-pci,netdev=net0,romfile=" in arguments
    assert arguments[-1].endswith("seed.img,if=virtio,format=raw,readonly=on")
    assert "--volume" not in arguments


def test_frozen_clone_has_no_provisioning_seed_or_key(lab):
    root, config, backend, _, _, calls = lab
    result = prepare(lab, no_seed=True)
    assert result["provision"]["seed_path"] is None
    assert not any("cloud-localds" in argv for argv in calls)
    _, arguments = provision.start_arguments(root, config, backend, "customer-1")
    assert "-drive" not in arguments  # Main overlay is added by VMBackend itself.


def test_64g_frozen_baseline_never_shrinks_during_prepare_or_reset(lab, monkeypatch):
    root, _, _, base, digest, calls = lab
    original_run = provision._run

    def large_disk(argv, timeout=30):
        if "qemu-img" in argv and "info" in argv:
            calls.append(argv)
            return json.dumps({"virtual-size": 64 * 1024**3})
        return original_run(argv, timeout)

    monkeypatch.setattr(provision, "_run", large_disk)
    result = provision.prepare_session(root, "customer-1", base, digest, no_seed=True)
    assert result["provision"]["virtual_size_bytes"] == 64 * 1024**3
    assert result["provision"]["minimum_overlay_gib"] == 24
    provision.reset_session(root, "customer-1")
    assert not any("qemu-img" in argv and "resize" in argv for argv in calls)


def test_clone_seed_only_restores_access_without_installation(lab):
    root, _, _, base, digest, _ = lab
    result = provision.prepare_session(
        root,
        "customer-1",
        base,
        digest,
        public_key="ssh-ed25519 YWJj fixture",
        clone_seed=True,
    )
    path = root / "machine/sessions/customer-1"
    parsed = yaml.safe_load((path / "user-data.yaml").read_text())
    assert parsed["users"] == [
        {"name": "customer", "ssh_authorized_keys": ["ssh-ed25519 YWJj fixture"]}
    ]
    assert parsed["ssh_deletekeys"] is True
    assert "ed25519" in parsed["ssh_genkeytypes"]
    assert parsed["package_update"] is False
    assert parsed["package_upgrade"] is False
    assert "packages" not in parsed
    assert "runcmd" not in parsed
    assert "write_files" not in parsed
    assert "hermes-agent==" not in (path / "user-data.yaml").read_text()
    assert result["provision"]["seed_mode"] == "restored-baseline-access"
    assert (
        result["provision"]["seed_sha256"]
        == hashlib.sha256(b"Fixture seed").hexdigest()
    )


def test_clone_and_no_seed_modes_are_exclusive(lab):
    root, _, _, base, digest, calls = lab
    with pytest.raises(vm.VMError, match="either a minimal clone seed"):
        provision.prepare_session(
            root,
            "customer-1",
            base,
            digest,
            public_key=None,
            clone_seed=True,
            no_seed=True,
        )
    assert calls == []


def test_hash_mismatch_never_creates_session(lab):
    root, _, _, base, _, calls = lab
    with pytest.raises(vm.VMError, match="base identity changed"):
        provision.prepare_session(root, "customer-1", base, "0" * 64, no_seed=True)
    assert not (root / "machine/sessions/customer-1").exists()
    assert calls == []


@pytest.mark.parametrize(
    "key", ["PRIVATE KEY\nsecret", "ssh-ed25519 abc\ninjected", "not a key"]
)
def test_bad_key_rejected_before_overlay_creation(lab, key):
    root, _, _, base, digest, calls = lab
    with pytest.raises(vm.VMError, match="public key"):
        provision.prepare_session(root, "customer-1", base, digest, key)
    assert calls == []
    assert not (root / "machine/sessions/customer-1").exists()


def test_bad_port_in_config_is_not_interpolated(lab):
    root, config, _, _, _, _ = lab
    for port in ("18091:extra", 22, 65536):
        config["ssh_port"] = port
        provision._write_json(root / "provision.json", config)
        with pytest.raises(vm.VMError, match="numeric port"):
            provision.load_config(root)


def test_seed_change_blocks_start(lab):
    root, config, backend, _, _, _ = lab
    prepare(lab)
    (root / "machine/sessions/customer-1/seed.img").write_bytes(b"changed")
    with pytest.raises(vm.VMError, match="seed identity changed"):
        provision.start_arguments(root, config, backend, "customer-1")


def test_stale_cid_removed_only_after_successful_exact_absence(lab, monkeypatch):
    root, _, _, _, _, _ = lab
    prepare(lab)
    path = root / "machine/sessions/customer-1"
    cidfile = path / "container.id"
    cidfile.write_text("a" * 64)
    calls = []
    monkeypatch.setattr(provision, "_run", lambda argv: calls.append(argv) or "a" * 64)
    with pytest.raises(vm.VMError, match="still exists"):
        provision._clear_absent_container_id(path)
    assert cidfile.exists()
    assert f"id={'a' * 64}" in calls[0]
    monkeypatch.setattr(
        provision,
        "_run",
        lambda _: (_ for _ in ()).throw(vm.VMError("daemon unavailable")),
    )
    with pytest.raises(vm.VMError, match="daemon unavailable"):
        provision._clear_absent_container_id(path)
    assert cidfile.exists()
    monkeypatch.setattr(provision, "_run", lambda _: "")
    provision._clear_absent_container_id(path)
    assert not cidfile.exists()


def test_download_hash_failure_preserves_existing_or_partial_bytes(lab, monkeypatch):
    import io

    root, _, _, _, _, _ = lab
    payload = b"fixture downloaded image"

    class Response(io.BytesIO):
        def geturl(self):
            return "https://example.test/image"

    monkeypatch.setattr(
        provision.urllib.request, "urlopen", lambda *a, **k: Response(payload)
    )
    with pytest.raises(vm.VMError, match="SHA256 mismatch"):
        provision.download_image(
            root, "https://example.test/image", "0" * 64, "candidate.img"
        )
    assert not (root / "images/candidate.img").exists()
    assert list((root / "images").glob(".candidate.img.*.part"))
    digest = hashlib.sha256(payload).hexdigest()
    receipt = provision.download_image(
        root, "https://example.test/image", digest, "candidate.img"
    )
    assert receipt["sha256"] == digest
    assert (root / "images/candidate.img").read_bytes() == payload
    with pytest.raises(vm.VMError, match="another identity"):
        provision.download_image(
            root, "https://example.test/image", "0" * 64, "candidate.img"
        )
    assert (root / "images/candidate.img").read_bytes() == payload


@pytest.mark.parametrize(
    "url,name",
    [
        ("http://example.test/image", "image.img"),
        ("https://user:secret@example.test/image", "image.img"),
        ("https://example.test/image", "../outside.img"),
    ],
)
def test_download_scope_rejected_without_network(lab, monkeypatch, url, name):
    root, _, _, _, _, _ = lab
    monkeypatch.setattr(
        provision.urllib.request,
        "urlopen",
        lambda *_a, **_k: pytest.fail("network reached"),
    )
    with pytest.raises(vm.VMError):
        provision.download_image(root, url, "0" * 64, name)


def test_default_os_source_is_the_qualified_dated_image():
    assert (
        provision.DEFAULT_IMAGE_URL
        == "https://cloud-images.ubuntu.com/noble/20261017/noble-server-cloudimg-arm64.img"
    )
    assert (
        provision.DEFAULT_IMAGE_SHA256
        == "50e24e1fb79e89116e939d90aa7738f7af48c442fa1bc2510131e0b39c50348e"
    )


def public_files(lab):
    root, _, _, _, _, _ = lab
    public = root / "public"
    public.mkdir()
    (public / "index.html").write_text(
        "<p>Private candidate download, development build.</p>"
    )
    (public / "candidate.whl").write_bytes(
        b"Fixture package identity, not an installable wheel"
    )
    return public


def test_technical_freecad_recipe_never_runs_host_commands_before_guest_guard(
    monkeypatch,
):
    import importlib.util

    path = SCRIPTS / "synthetic_beta_testing/assets/prepare-freecad-arm64.py"
    specification = importlib.util.spec_from_file_location(
        "freecad_technical_fixture", path
    )
    recipe = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(recipe)
    monkeypatch.setattr(
        recipe,
        "check_guest",
        lambda: (_ for _ in ()).throw(RuntimeError("guest required")),
    )
    monkeypatch.setattr(
        recipe, "run", lambda *_args, **_kwargs: pytest.fail("host command reached")
    )
    with pytest.raises(RuntimeError, match="guest required"):
        recipe.prepare(Path("/tmp/fixture.AppImage"), Path("/tmp/fixture-provider"))
    assert recipe.SOURCE_COMMIT == "63acb305573194a011641ab13ccfb391fe95769f"
    assert recipe.SDK_VERSION == "1.28.1"
    assert (
        recipe.APPIMAGE_SHA256
        == "8004e166dc5c516cc8e8d85a5f58b5d56c3836cf8652301c2e6b9e4b1fd27827"
    )


def test_public_manifest_freezes_only_explicit_staged_artifacts(lab):
    root, _, _, _, _, _ = lab
    public = public_files(lab)
    receipt = provision.freeze_public(root)
    manifest = json.loads((public / "public-manifest.json").read_text())
    assert {row["path"] for row in manifest["files"]} == {"index.html", "candidate.whl"}
    assert receipt["sha256"] == vm.sha256(public / "public-manifest.json")
    assert provision.freeze_public(root) == receipt
    (public / "candidate.whl").write_bytes(b"changed")
    with pytest.raises(vm.VMError, match="Frozen public material changed"):
        provision.freeze_public(root)


def test_public_bare_adapter_git_is_hashed_without_executing_hooks(lab):
    import zlib

    root, _, _, _, _, _ = lab
    public = public_files(lab)
    bare = public / "adapter.git"
    bare.mkdir()
    (bare / "HEAD").write_text("ref: refs/heads/main\n")
    (bare / "config").write_text("[core]\n bare = true\n repositoryformatversion = 0\n")
    (bare / "info").mkdir()
    (bare / "info/refs").write_text("a" * 40 + "\trefs/heads/main\n")
    body = b"A frozen adapter README"
    obj = b"blob " + str(len(body)).encode() + b"\0" + body
    identity = hashlib.sha1(obj).hexdigest()
    object_path = bare / "objects" / identity[:2] / identity[2:]
    object_path.parent.mkdir(parents=True)
    object_path.write_bytes(zlib.compress(obj))
    receipt = provision.freeze_public(root)
    manifest = json.loads(Path(receipt["path"]).read_text())
    paths = {row["path"] for row in manifest["files"]}
    assert "adapter.git/HEAD" in paths
    assert f"adapter.git/objects/{identity[:2]}/{identity[2:]}" in paths


def test_public_adapter_hooks_and_private_key_objects_are_rejected(lab):
    import zlib

    root, _, _, _, _, _ = lab
    public = public_files(lab)
    hooks = public / "adapter.git/hooks"
    hooks.mkdir(parents=True)
    sample = hooks / "pre-push.sample"
    sample.write_text("#!/bin/sh\nexit 0\n")
    with pytest.raises(vm.VMError, match="remove hooks"):
        provision.freeze_public(root)
    sample.unlink()
    body = b"-----BEGIN OPENSSH PRIVATE KEY-----"
    obj = b"blob " + str(len(body)).encode() + b"\0" + body
    identity = hashlib.sha1(obj).hexdigest()
    object_path = public / "adapter.git/objects" / identity[:2] / identity[2:]
    object_path.parent.mkdir(parents=True)
    object_path.write_bytes(zlib.compress(obj))
    with pytest.raises(vm.VMError, match="private-key"):
        provision.freeze_public(root)


@pytest.mark.parametrize(
    "kind", ["symlink", "secret-name", "secret-text", "private-key", "hidden"]
)
def test_public_material_cannot_expose_private_files_or_credentials(lab, kind):
    root, _, _, _, _, _ = lab
    public = public_files(lab)
    if kind == "symlink":
        private = root / "private.txt"
        private.write_text("must remain private")
        (public / "link.txt").symlink_to(private)
    elif kind == "secret-name":
        (public / "auth.json").write_text("{}")
    elif kind == "secret-text":
        (public / "notes.txt").write_text("api_key=FAKE_CREDENTIAL")
    elif kind == "private-key":
        (public / "notes.txt").write_text("-----BEGIN OPENSSH PRIVATE KEY-----")
    else:
        (public / ".env").write_text("unrelated=value")
    with pytest.raises(vm.VMError):
        provision.freeze_public(root)
    assert not (public / "public-manifest.json").exists()


def owned_container_fixture(lab, monkeypatch, wrong_owner=False):
    root, config, backend, _, _, _ = lab
    prepare(lab)
    path = root / "machine/sessions/customer-1"
    (path / "container.id").write_text("a" * 64)
    monkeypatch.setattr(provision, "backend_for", lambda *_: backend)
    monkeypatch.setattr(backend, "state", lambda _: {"qmp_status": {"running": True}})
    observed = [
        {
            "Id": "a" * 64,
            "Image": config["launcher_image"],
            "State": {"Running": True},
            "Config": {
                "Labels": {
                    "wright.synthetic-beta.owner": "unknown"
                    if wrong_owner
                    else backend.owner,
                    "wright.synthetic-beta.session": "customer-1",
                }
            },
        }
    ]
    calls = []

    def run(argv, timeout=30):
        calls.append(argv)
        if argv[1:3] == ["container", "inspect"]:
            return json.dumps(observed)
        if "exec" in argv and "--detach" not in argv:
            return argv[-1]
        return ""

    monkeypatch.setattr(provision, "_run", run)
    return path, calls


def test_candidate_server_is_only_inside_exact_owned_guest_container(lab, monkeypatch):
    root, _, _, _, _, _ = lab
    path, calls = owned_container_fixture(lab, monkeypatch)
    public = public_files(lab)
    frozen = provision.freeze_public(root)
    receipt = provision.serve_public(root, "customer-1")
    assert receipt["manifest_sha256"] == frozen["sha256"]
    assert receipt["directory"] == str(public)
    assert receipt["guest_url"] == "http://10.0.2.2:18092/"
    assert receipt["host_port_published"] is False
    detach = [argv for argv in calls if "--detach" in argv]
    assert len(detach) == 1
    assert detach[0][:3] == ["docker", "exec", "--detach"]
    assert "127.0.0.1" in detach[0][-3] and "18092" in detach[0][-3]
    assert str(public) == detach[0][-2]
    assert all("--publish" not in argv for argv in calls)
    assert (path / "public-server.json").exists()
    assert provision.serve_public(root, "customer-1") == receipt
    assert len([argv for argv in calls if "--detach" in argv]) == 1


def test_candidate_server_refuses_other_container_owner(lab, monkeypatch):
    root, _, _, _, _, _ = lab
    _, calls = owned_container_fixture(lab, monkeypatch, wrong_owner=True)
    public_files(lab)
    provision.freeze_public(root)
    with pytest.raises(vm.VMError, match="identity mismatch"):
        provision.serve_public(root, "customer-1")
    assert not any("exec" in argv for argv in calls)
