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


# Share only the temporary mock storage observations, never guest operations.
from test_synthetic_beta_guest import storage  # noqa: F401, E402


@pytest.mark.parametrize(
    "wrong",
    [None, "parent", "noexec", "small", "nonempty", "guard_owner", "guard_writable"],
)
def test_installer_exact_fresh_scope_and_root_verifier(
    storage,  # noqa: F811 - imported pytest fixture
    tmp_path,
    monkeypatch,
    wrong,
):
    import json
    import os
    from types import SimpleNamespace
    from scripts.synthetic_beta_testing import guest

    profile, _, private, target, rows, calls, prepare = storage
    prepare()
    guard = tmp_path / "root-owned-check.py"
    guard.write_text("# Mock verifier, never executed")
    guard.chmod(0o644)
    if wrong == "nonempty":
        (target / "data" / "retained").write_text("preserve")
    if wrong == "noexec":
        rows[private]["options"] += ",noexec"
    if wrong == "small":
        rows[private]["size"] = 512 * 1024**2
    previous_stat = Path.stat

    def stat(path, *args, **kwargs):
        value = previous_stat(path, *args, **kwargs)
        if path == guard:
            fields = list(value)
            fields[4] = 1000 if wrong == "guard_owner" else 0
            if wrong == "guard_writable":
                fields[0] |= 0o022
            return os.stat_result(fields)
        return value

    monkeypatch.setattr(Path, "stat", stat)
    monkeypatch.setattr(
        installer,
        "Path",
        lambda value: {
            "/run/hermes-beta/wright-home": target,
            "/usr/local/lib/wright-beta/check-runtime-storage.py": guard,
        }.get(str(value), Path(value)),
    )

    def verify(argv, **kwargs):
        assert argv == ["python3", str(guard)]
        return SimpleNamespace(stdout=json.dumps(guest.verify_runtime_storage(profile)))

    monkeypatch.setattr(installer.subprocess, "run", verify)
    if wrong is None:
        assert installer.check_runtime_mount(target)["target"] == str(target)
    else:
        with pytest.raises(RuntimeError):
            installer.check_runtime_mount(profile if wrong == "parent" else target)
    if wrong == "nonempty":
        assert (target / "data" / "retained").read_text() == "preserve"
