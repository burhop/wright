"""Mock-only credential-minimization checks. No credentials or VM used."""

import json
import os
from pathlib import Path
import shlex
from types import SimpleNamespace

import pytest

from scripts.synthetic_beta_testing import guest


@pytest.fixture
def access(tmp_path, monkeypatch):
    source = tmp_path / "auth-fixture.json"
    value = {
        "credential_pool": {
            "other-provider": [{"access_token": "UNRELATED"}],
            "openai-codex": [
                {
                    "id": "exhausted",
                    "access_token": "EXHAUSTED",
                    "last_status": "exhausted",
                },
                {
                    "id": "usable",
                    "auth_type": "oauth",
                    "access_token": "ACCESS_FIXTURE",
                    "refresh_token": "REFRESH_MUST_NOT_TRANSFER",
                    "id_token": "IDENTITY_MUST_NOT_TRANSFER",
                    "account_id": "PRIVATE_ACCOUNT_MUST_NOT_TRANSFER",
                    "base_url": "https://chatgpt.com/backend-api/codex",
                },
            ],
        },
        "unrelated_settings": {"private": "PROFILE_MUST_NOT_TRANSFER"},
    }
    source.write_text(json.dumps(value))
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "runtime_profile": "/run/hermes-beta",
                    "storage": "tmpfs",
                    "refresh_token_transferred": False,
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(guest.subprocess, "run", fake_run)
    return source, value, calls


def test_only_selected_access_credential_is_transferred_to_tmpfs(access, tmp_path):
    source, _, calls = access
    before = source.read_bytes()
    receipt = guest.supply_runtime_access(tmp_path, source)
    assert source.read_bytes() == before
    assert receipt["original_auth_unchanged"] is True
    assert len(calls) == 1
    command, options = calls[0]
    payload_text = options["input"]
    assert "ACCESS_FIXTURE" in payload_text
    assert all(
        secret not in payload_text
        for secret in [
            "EXHAUSTED",
            "REFRESH_MUST_NOT_TRANSFER",
            "IDENTITY_MUST_NOT_TRANSFER",
            "PRIVATE_ACCOUNT_MUST_NOT_TRANSFER",
            "PROFILE_MUST_NOT_TRANSFER",
            "UNRELATED",
        ]
    )
    assert "ACCESS_FIXTURE" not in " ".join(command)
    assert "ACCESS_FIXTURE" not in json.dumps(receipt)
    assert "findmnt" in command[-1] and "tmpfs" in command[-1]
    assert "swapoff" in command[-1]
    assert options["timeout"] == 30
    compile(shlex.split(command[-1])[-1], "<guest-runtime-preparation>", "exec")


def test_rejected_credentials_do_not_trigger_guest_access(access, tmp_path):
    source, value, calls = access
    for item in value["credential_pool"]["openai-codex"]:
        item["last_status"] = "rejected"
    source.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="No usable"):
        guest.supply_runtime_access(tmp_path, source)
    assert calls == []


@pytest.mark.parametrize(
    "status", ["expired", "revoked", "disabled", "invalid", "failed", "exhausted"]
)
def test_unusable_credential_statuses_never_transfer(access, tmp_path, status):
    source, value, calls = access
    for item in value["credential_pool"]["openai-codex"]:
        item["last_status"] = status
    source.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="No usable"):
        guest.supply_runtime_access(tmp_path, source)
    assert calls == []


def test_unapproved_model_endpoint_rejected_before_transfer(access, tmp_path):
    source, value, calls = access
    value["credential_pool"]["openai-codex"][1]["base_url"] = (
        "https://unexpected.invalid"
    )
    source.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="Unexpected configured"):
        guest.supply_runtime_access(tmp_path, source)
    assert calls == []


def test_restored_sessions_use_distinct_known_hosts_without_disabling_checks(tmp_path):
    first = guest.ssh_command(tmp_path, session_id="first")
    second = guest.ssh_command(tmp_path, session_id="second")
    first_hosts = next(
        value for value in first if value.startswith("UserKnownHostsFile=")
    )
    second_hosts = next(
        value for value in second if value.startswith("UserKnownHostsFile=")
    )
    assert first_hosts != second_hosts
    assert "/first/known-hosts" in first_hosts
    assert "/second/known-hosts" in second_hosts
    assert "StrictHostKeyChecking=accept-new" in first
    assert "StrictHostKeyChecking=no" not in first


@pytest.mark.parametrize(
    "session_id", ["../escape", "session/child", "/absolute", "", "a" * 49]
)
def test_ssh_rejects_unsafe_session_scope(tmp_path, session_id):
    with pytest.raises(ValueError, match="session identity"):
        guest.ssh_command(tmp_path, session_id=session_id)


@pytest.mark.parametrize("port", [22, 0, 65536, "18091", 18091.0, True])
def test_ssh_rejects_invalid_ports(tmp_path, port):
    with pytest.raises(ValueError, match="port"):
        guest.ssh_command(tmp_path, port=port)


def test_ssh_rejects_symlinked_lab_or_known_hosts(tmp_path):
    actual = tmp_path / "actual"
    actual.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(actual, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        guest.ssh_command(linked)
    guest.ssh_command(actual, session_id="first")
    known_hosts = actual / "private/guest-hosts/first/known-hosts"
    known_hosts.symlink_to(tmp_path / "outside")
    with pytest.raises(ValueError, match="symlink"):
        guest.ssh_command(actual, session_id="first")


@pytest.fixture
def storage(tmp_path, monkeypatch):
    profile, disk = tmp_path / "profile", tmp_path / "disk"
    profile.mkdir()
    private, target = profile / "wright-private", profile / "wright-home"
    provisioned, memory = tmp_path / "provisioned.json", tmp_path / "meminfo"
    provisioned.write_text("{}")
    memory.write_text(
        "MemTotal: 1024 kB\nMemAvailable: 512 kB\nShmem: 0 kB\nSwapTotal: 0 kB\n"
    )
    mapped = {
        "/run/hermes-beta": profile,
        "/var/lib/wright-beta/native-software": disk,
        "/var/lib/wright-beta/provisioned.json": provisioned,
        "/proc/meminfo": memory,
    }
    monkeypatch.setattr(
        guest, "Path", lambda value: mapped.get(str(value), Path(value))
    )
    aliases = {
        target: disk,
        **{target / n: private / n for n in ("data", "state", "logs")},
    }
    original = Path.stat

    def stat(path, *args, **kwargs):
        result = original(aliases.get(path, path), *args, **kwargs)
        if path in {target, disk} or path.is_relative_to(profile):
            fields = list(result)
            fields[4] = 1000
            return os.stat_result(fields)
        return result

    monkeypatch.setattr(Path, "stat", stat)
    rows = {}
    for path in (
        profile,
        private,
        target,
        disk,
        *(target / n for n in ("data", "state", "logs")),
    ):
        rows[path] = {
            "target": str(path),
            "fstype": "ext4" if path in {target, disk} else "tmpfs",
            "options": "rw,exec,nosuid,nodev,uid=1000,gid=1000,mode=700",
            "size": 4 * 1024**3,
        }
    calls = []

    def observe(argv, **kw):
        if "-T" in argv:
            return "ext4"
        return json.dumps({"filesystems": [rows[Path(argv[-1])]]})

    monkeypatch.setattr(guest.subprocess, "check_output", observe)
    monkeypatch.setattr(guest.subprocess, "run", lambda argv, **kw: calls.append(argv))
    monkeypatch.setattr(os, "chown", lambda *args: None)

    def prepare_dirs():
        for path in (target, disk, private):
            path.mkdir()
        for n in ("data", "state", "logs"):
            (target / n).mkdir()
            (private / n).mkdir()

    return profile, disk, private, target, rows, calls, prepare_dirs


def test_fresh_split_storage_and_no_parent_mount(storage, monkeypatch):
    profile, disk, private, target, rows, calls, _ = storage
    monkeypatch.setattr(os, "getuid", lambda: 0)
    result = guest.prepare_runtime_mount(profile)
    assert result["software_source"] == str(disk)
    assert result["private_mount"]["fstype"] == "tmpfs"
    assert len(result["private_bindings"]) == 3
    assert len(calls) == 6 and all(call[-1] != str(profile) for call in calls)


@pytest.mark.parametrize("wrong", ["noexec", "fstype", "target", "size", "uid"])
def test_private_mount_tampering_is_rejected(storage, wrong):
    profile, _, private, _, rows, calls, prepare = storage
    prepare()
    row = rows[private]
    if wrong == "noexec":
        row["options"] += ",noexec"
    elif wrong == "fstype":
        row["fstype"] = "ext4"
    elif wrong == "target":
        row["target"] = str(profile)
    elif wrong == "size":
        row["size"] = 512 * 1024**2
    else:
        row["options"] = row["options"].replace("uid=1000", "uid=0")
    with pytest.raises(RuntimeError, match="dedicated tmpfs"):
        guest.verify_runtime_storage(profile)
    assert calls == []


def test_existing_state_not_adopted_or_modified(storage, monkeypatch):
    profile, _, _, target, _, calls, prepare = storage
    prepare()
    retained = target / "installation.json"
    retained.write_text("preserved")
    monkeypatch.setattr(os, "getuid", lambda: 0)
    with pytest.raises(RuntimeError, match="Existing Wright state"):
        guest.prepare_runtime_mount(profile)
    assert retained.read_text() == "preserved" and calls == []


def test_verification_is_read_only(storage):
    profile, _, _, target, _, calls, prepare = storage
    prepare()
    assert guest.verify_runtime_storage(profile)["target"] == str(target)
    assert calls == []
