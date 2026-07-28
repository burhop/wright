from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from wright_engineering.runtime.artifacts import (
    ArtifactError,
    ArtifactResolver,
    RuntimeArtifact,
)
from wright_engineering.runtime.installer import RuntimeInstaller
from wright_engineering.runtime.layout import NativeLayout
from wright_engineering.runtime.models import SourceChannel


def _wheel(tmp_path: Path, version: str = "0.1.5") -> Path:
    wheel = tmp_path / f"wright_engineering-{version}-py3-none-any.whl"
    wheel.write_bytes(b"candidate-wheel")
    return wheel


def test_local_candidate_requires_exact_matching_version_and_hash(
    tmp_path: Path,
) -> None:
    wheel = _wheel(tmp_path)
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    resolved = ArtifactResolver().resolve_local(
        wheel,
        version="0.1.5",
        expected_sha256=digest,
        channel=SourceChannel.LOCAL_CANDIDATE,
    )
    assert resolved.version == "0.1.5"
    assert resolved.sha256 == digest

    with pytest.raises(ArtifactError, match="artifact_version_mismatch"):
        ArtifactResolver().resolve_local(
            wheel, version="0.1.6", channel=SourceChannel.TEST
        )
    with pytest.raises(ArtifactError, match="artifact_hash_mismatch"):
        ArtifactResolver().resolve_local(
            wheel, version="0.1.5", expected_sha256="0" * 64, channel=SourceChannel.TEST
        )


def test_channel_policy_rejects_mutable_or_unapproved_sources(tmp_path: Path) -> None:
    wheel = _wheel(tmp_path)
    with pytest.raises((ArtifactError, ValueError)):
        ArtifactResolver().resolve_local(wheel, version="latest", channel="nightly")  # type: ignore[arg-type]


def test_install_command_uses_exact_runtime_extra_and_no_source_tools(
    tmp_path: Path,
) -> None:
    wheel = _wheel(tmp_path)
    artifact = RuntimeArtifact.from_local(wheel, "0.1.5", SourceChannel.LOCAL_CANDIDATE)
    layout = NativeLayout.from_hermes_home(tmp_path / "hermes")
    installer = RuntimeInstaller(layout, python_executable=Path("python"))
    command = installer.install_command(artifact, layout.runtime_path("runtime-id"))
    rendered = " ".join(str(part) for part in command).lower()
    assert "wright-engineering[runtime] @ file:" in rendered
    assert "wright_engineering-0.1.5-py3-none-any.whl" in rendered
    assert str(wheel.parent.resolve()) in command
    assert not any(tool in rendered for tool in ("git ", "docker", "npm", "node"))
    assert "--no-deps" not in command
