from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).parents[2]
PROFILES = (
    ROOT / "docker-compose.yml",
    ROOT / "docker-compose.minimal.yml",
    ROOT / "docker-compose.mcp.yml",
)
REQUIRED_TARGETS = {
    "/home/agent/.local/share/wright",
    "/home/agent/workspace",
    "/home/agent/.config/wright",
    "/home/agent/.hermes",
}


def _volume_target(spec: str | dict) -> str:
    if isinstance(spec, str):
        parts = spec.split(":")
        return parts[1] if len(parts) > 1 else ""
    return str(spec.get("target", ""))


def test_supported_compose_profiles_persist_every_program_state_root() -> None:
    for path in PROFILES:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        service = document["services"]["agent"]
        targets = {_volume_target(item) for item in service["volumes"]}
        assert REQUIRED_TARGETS <= targets, path.name
        declared = set(document["volumes"])
        mounted_named = {
            item.split(":", 1)[0]
            for item in service["volumes"]
            if isinstance(item, str) and not item.startswith(".")
        }
        assert mounted_named <= declared, path.name


def test_supported_profiles_use_named_volumes_not_container_layers() -> None:
    for path in PROFILES:
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        service = document["services"]["agent"]
        state_mounts = [
            item
            for item in service["volumes"]
            if _volume_target(item) in REQUIRED_TARGETS
        ]
        assert len(state_mounts) == len(REQUIRED_TARGETS)
        assert all(
            isinstance(item, str) and not item.startswith(("./", "../", "/", "~"))
            for item in state_mounts
        )


def test_image_family_declares_the_same_persistent_program_roots() -> None:
    family = yaml.safe_load(
        (ROOT / "docker" / "image-family.yaml").read_text(encoding="utf-8")
    )
    linux_images = [
        image for image in family["images"] if image["platform"].startswith("linux/")
    ]
    assert linux_images
    for image in linux_images:
        assert REQUIRED_TARGETS <= set(image["persisted_paths"]), image["id"]


def _require_disposable_volume_name(value: str) -> str:
    if not value.startswith("wright-program-persistence-test-"):
        raise ValueError("refusing non-disposable Docker volume")
    return value


def test_live_harness_refuses_any_non_disposable_volume_name() -> None:
    for unsafe in ("wright_data", "wright_mcp_data", "production", ""):
        with pytest.raises(ValueError, match="refusing"):
            _require_disposable_volume_name(unsafe)


def _docker_daemon_available(docker: str) -> bool:
    try:
        daemon = subprocess.run(
            [docker, "version", "--format", "{{.Server.Version}}"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        return False
    return daemon.returncode == 0


def test_nonresponsive_docker_daemon_is_unavailable_host_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def time_out(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", time_out)

    assert not _docker_daemon_available("docker")


def test_responsive_docker_daemon_remains_available_host_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: list[tuple[object, dict[str, object]]] = []

    def succeed(command: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        observed.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, stdout="28.3.3\n", stderr="")

    monkeypatch.setattr(subprocess, "run", succeed)

    assert _docker_daemon_available("docker")
    assert observed == [
        (
            ["docker", "version", "--format", "{{.Server.Version}}"],
            {
                "capture_output": True,
                "text": True,
                "check": False,
                "timeout": 10,
            },
        )
    ]


def test_available_local_wright_image_preserves_data_across_container_replacement() -> (
    None
):
    docker = shutil.which("docker")
    if docker is None:
        pytest.skip("Docker CLI unavailable; no supporting host evidence")
    if not _docker_daemon_available(docker):
        pytest.skip("Docker daemon unavailable; no supporting host evidence")
    image = os.environ.get(
        "WRIGHT_DOCKER_PERSISTENCE_IMAGE", "wright:standard-linux-amd64"
    )
    available = subprocess.run(
        [docker, "image", "inspect", image],
        capture_output=True,
        check=False,
        timeout=10,
    )
    if available.returncode:
        pytest.skip(
            f"Exact local candidate {image} unavailable; contract evidence only"
        )

    volume = _require_disposable_volume_name(
        f"wright-program-persistence-test-{uuid.uuid4().hex}"
    )
    subprocess.run([docker, "volume", "create", volume], check=True, timeout=20)
    try:
        common = [
            docker,
            "run",
            "--rm",
            "--network",
            "none",
            "-v",
            f"{volume}:/home/agent/.local/share/wright",
            "--entrypoint",
            "sh",
            image,
            "-c",
        ]
        subprocess.run(
            [*common, "printf program-state > /home/agent/.local/share/wright/probe"],
            check=True,
            timeout=30,
        )
        restored = subprocess.run(
            [*common, "cat /home/agent/.local/share/wright/probe"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert restored.stdout == "program-state"
    finally:
        _require_disposable_volume_name(volume)
        subprocess.run([docker, "volume", "rm", volume], check=True, timeout=20)
