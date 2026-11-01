"""Mock-only credential-minimization checks. No credentials or VM used."""

import json
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


def mount_description(target, *, exact=True, noexec=False):
    return {
        "target": str(target) if exact else str(target.parent.parent),
        "fstype": "tmpfs",
        "size": 4 * 1024**3,
        "options": "rw,nosuid,nodev,uid=1000,gid=1000,mode=700"
        + (",noexec" if noexec else ""),
    }


def test_runtime_mount_is_nested_exec_tmpfs_and_never_remounts_parent(
    tmp_path, monkeypatch
):
    profile = tmp_path / "profile"
    profile.mkdir()
    target = profile / "wright-home"
    replies = [
        mount_description(target, exact=False, noexec=True),
        mount_description(target),
    ]
    calls = []
    monkeypatch.setattr(
        guest.subprocess,
        "check_output",
        lambda argv, **_: json.dumps({"filesystems": [replies.pop(0)]}),
    )
    monkeypatch.setattr(guest.subprocess, "run", lambda argv, **_: calls.append(argv))
    receipt = guest.prepare_runtime_mount(profile)
    assert len(calls) == 1
    assert calls[0] == [
        "mount",
        "-t",
        "tmpfs",
        "-o",
        "exec,nosuid,nodev,uid=1000,gid=1000,mode=0700,size=4G",
        "wright-beta-runtime",
        str(target),
    ]
    assert "remount" not in " ".join(calls[0])
    assert receipt["target"] == str(target)
    assert receipt["size_bytes"] == 4294967296
    assert "noexec" not in receipt["options"]


def test_existing_nonempty_runtime_state_is_never_overmounted(tmp_path, monkeypatch):
    target = tmp_path / "wright-home"
    target.mkdir()
    (target / "installation.json").write_text("preserved")
    monkeypatch.setattr(
        guest.subprocess, "run", lambda *_a, **_k: pytest.fail("mount reached")
    )
    monkeypatch.setattr(
        guest.subprocess,
        "check_output",
        lambda *_a, **_k: pytest.fail("findmnt reached"),
    )
    with pytest.raises(RuntimeError, match="Existing Wright runtime state"):
        guest.prepare_runtime_mount(tmp_path)
    assert (target / "installation.json").read_text() == "preserved"


@pytest.mark.parametrize("wrong", ["noexec", "fstype", "target", "size", "uid"])
def test_existing_dedicated_mount_must_match_without_remount(
    tmp_path, monkeypatch, wrong
):
    target = tmp_path / "wright-home"
    description = mount_description(target)
    if wrong == "noexec":
        description["options"] += ",noexec"
    elif wrong == "uid":
        description["options"] = description["options"].replace("uid=1000", "uid=0")
    elif wrong == "target":
        description["target"] = str(tmp_path)
    elif wrong == "fstype":
        description["fstype"] = "ext4"
    else:
        description["size"] = 800 * 1024**2
    # A wrong parent target causes a new nested mount attempt; emulate its still
    # wrong observed result, never an actual mount or parent remount.
    calls = []
    monkeypatch.setattr(
        guest.subprocess,
        "check_output",
        lambda *_a, **_k: json.dumps({"filesystems": [description]}),
    )
    monkeypatch.setattr(guest.subprocess, "run", lambda argv, **_: calls.append(argv))
    with pytest.raises(RuntimeError, match="tmpfs verification failed"):
        guest.prepare_runtime_mount(tmp_path)
    if wrong == "target":
        assert len(calls) == 1 and calls[0][-1] == str(target)
    else:
        assert calls == []


def test_empty_correct_dedicated_mount_is_idempotently_verified(tmp_path, monkeypatch):
    target = tmp_path / "wright-home"
    monkeypatch.setattr(
        guest.subprocess,
        "check_output",
        lambda *_a, **_k: json.dumps({"filesystems": [mount_description(target)]}),
    )
    monkeypatch.setattr(
        guest.subprocess,
        "run",
        lambda *_a, **_k: pytest.fail("must not remount verified child"),
    )
    assert guest.prepare_runtime_mount(tmp_path)["fstype"] == "tmpfs"
