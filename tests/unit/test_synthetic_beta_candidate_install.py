"""Candidate preparation archive fixtures; no Hermes, guest or provider use."""

import importlib.util
import io
from pathlib import Path
import tarfile

import pytest


PATH = (
    Path(__file__).resolve().parents[2]
    / "scripts/synthetic_beta_testing/assets/install-native-candidate.py"
)
SPEC = importlib.util.spec_from_file_location("beta_candidate_fixture", PATH)
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


@pytest.mark.parametrize(
    "name,link",
    [
        ("../outside", False),
        ("wrong-prefix/file", False),
        ("wright-candidate/link", True),
    ],
)
def test_archive_escape_and_links_are_rejected(tmp_path, name, link):
    bundle = tmp_path / "fixture.tar.gz"
    with tarfile.open(bundle, "w:gz") as archive:
        member = tarfile.TarInfo(name)
        if link:
            member.type = tarfile.SYMTYPE
            member.linkname = "/tmp/unowned"
            archive.addfile(member)
        else:
            member.size = 1
            archive.addfile(member, io.BytesIO(b"x"))
    with pytest.raises(RuntimeError, match="archive boundary"):
        installer.extract_candidate(bundle, tmp_path / "extracted")
    assert not (tmp_path / "outside").exists()


def test_fixed_candidate_prefix_extracts_without_installing(tmp_path):
    bundle = tmp_path / "fixture.tar.gz"
    with tarfile.open(bundle, "w:gz") as archive:
        member = tarfile.TarInfo("wright-candidate/wheelhouse/fixture.whl")
        member.size = 7
        archive.addfile(member, io.BytesIO(b"fixture"))
    installer.extract_candidate(bundle, tmp_path / "extracted")
    assert (
        tmp_path / "extracted/wright-candidate/wheelhouse/fixture.whl"
    ).read_bytes() == b"fixture"


def test_install_guard_precedes_all_host_mutation(tmp_path, monkeypatch):
    monkeypatch.setattr(installer.os, "getuid", lambda: 1001)
    monkeypatch.setattr(
        installer.subprocess,
        "run",
        lambda *_a, **_k: pytest.fail("host subprocess reached"),
    )
    with pytest.raises(RuntimeError, match="fresh disposable customer guest"):
        installer.install(tmp_path / "missing.tar.gz", "a" * 64, "b" * 64)


@pytest.mark.parametrize("kind", ["valid", "parent", "noexec", "small", "nonempty"])
def test_installer_allows_only_empty_dedicated_executable_mount(
    tmp_path, monkeypatch, kind
):
    import json

    if kind == "nonempty":
        (tmp_path / "existing-state").write_text("preserve")
    description = {
        "target": str(tmp_path) if kind != "parent" else str(tmp_path.parent),
        "fstype": "tmpfs",
        "size": 4 * 1024**3 if kind != "small" else 800 * 1024**2,
        "options": "rw,nosuid,nodev" + (",noexec" if kind == "noexec" else ""),
    }
    monkeypatch.setattr(
        installer.subprocess,
        "check_output",
        lambda *_a, **_k: json.dumps({"filesystems": [description]}),
    )
    if kind == "valid":
        installer.check_runtime_mount(tmp_path)
    else:
        with pytest.raises(RuntimeError, match="mount"):
            installer.check_runtime_mount(tmp_path)
