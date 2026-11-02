"""Development mirrors must install one verified package without user overrides."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

import pytest

from test_bootstrap import _load_bootstrap


@pytest.fixture
def development(tmp_path, monkeypatch):
    module = _load_bootstrap("wright_dev_install_test")
    plugin = Path(__file__).parents[1]
    manifest_source = plugin / "dev-runtime.json"
    if not manifest_source.is_file():
        manifest_source = plugin / "runtime-release.json"
    if not manifest_source.is_file():
        pytest.skip("Stable mirror has no development release manifest")
    release = json.loads(manifest_source.read_text())
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr("wright_engineering/dev-release.json", json.dumps({
            "version": release["version"], "source_commit": release["source_commit"],
        }))
    release["sha256"] = hashlib.sha256(data.getvalue()).hexdigest()
    manifest = tmp_path / "runtime-release.json"
    manifest.write_text(json.dumps(release), encoding="utf-8")
    monkeypatch.setattr(module, "RELEASE_MANIFEST", manifest)
    for key in tuple(module.os.environ):
        if key.startswith("WRIGHT_RUNTIME_"):
            monkeypatch.delenv(key)
    root = tmp_path / "wright-home"
    monkeypatch.setattr(module, "wright_home", lambda: root)
    yield module, release, data.getvalue(), root
    sys.modules.pop(module.__name__, None)


def test_dev_selection_avoids_stable_bootstrap_and_supplies_artifact(development):
    module, release, _, root = development
    env = module._child_environment(root)
    assert module.bootstrap_environment(root).name == release["version"]
    assert env["WRIGHT_RUNTIME_CHANNEL"] == "test"
    assert env["WRIGHT_RUNTIME_VERSION"] == release["version"]
    assert env["WRIGHT_RUNTIME_SHA256"] == release["sha256"]
    assert Path(env["WRIGHT_RUNTIME_ARTIFACT"]).parent == Path(env["WRIGHT_RUNTIME_WHEELHOUSE"])


def test_dev_bootstrap_downloads_verifies_and_hands_off_offline(development, monkeypatch):
    module, release, data, root = development
    calls = []
    downloads = []

    def download(url, **kwargs):
        downloads.append(url)
        return io.BytesIO(data)

    def run(command, *, env, **kwargs):
        calls.append((command, env))
        if command[1:4] == ["-m", "venv", "--copies"]:
            python = module._environment_python(Path(command[4]))
            python.parent.mkdir(parents=True)
            python.write_bytes(b"python")

    monkeypatch.setattr(module.urllib.request, "urlopen", download)
    monkeypatch.setattr(module, "_run", run)
    python = module.ensure_bootstrap()
    assert downloads == [release["url"]]
    assert calls[1][0][1:4] == ["-m", "pip", "download"]
    assert "https://pypi.org/simple" in calls[1][0]
    assert "--extra-index-url" not in calls[1][0]
    assert "--no-index" in calls[2][0]
    assert calls[2][1]["WRIGHT_RUNTIME_VERSION"] == release["version"]
    wheel = Path(calls[2][1]["WRIGHT_RUNTIME_ARTIFACT"])
    assert wheel.read_bytes() == data
    assert module.ensure_bootstrap() == python
    assert len(calls) == 3  # Reopen uses the completed, exact-version bootstrap.


def test_tampered_download_never_installs_or_marks_ready(development, monkeypatch):
    module, _, _, root = development
    monkeypatch.setattr(module.urllib.request, "urlopen", lambda *a, **kw: io.BytesIO(b"tampered"))
    monkeypatch.setattr(module, "_run", lambda *a, **kw: pytest.fail("must not install tampered bytes"))
    with pytest.raises(module.BootstrapError, match="hash_mismatch"):
        module._prepare_release(Path("python"), module._child_environment(root))
    assert not list(root.rglob("*.whl"))
    assert not list(root.rglob(".wright-bootstrap-ready"))


@pytest.mark.parametrize("field,value", [
    ("url", "https://evil.example/package.whl"),
    ("version", "latest"), ("channel", "stable"),
    ("source_commit", "dev"), ("sha256", "unknown"),
])
def test_invalid_release_fails_before_network(development, field, value):
    module, release, _, _ = development
    release[field] = value
    module.RELEASE_MANIFEST.write_text(json.dumps(release), encoding="utf-8")
    with pytest.raises(module.BootstrapError, match="runtime_release_invalid"):
        module._runtime_release()


def test_explicit_candidate_override_remains_supported(development, monkeypatch, tmp_path):
    module, _, _, root = development
    wheel = tmp_path / "wright_engineering-0.1.9-py3-none-any.whl"
    wheel.write_bytes(b"candidate")
    monkeypatch.setenv("WRIGHT_RUNTIME_ARTIFACT", str(wheel))
    monkeypatch.setenv("WRIGHT_RUNTIME_VERSION", "0.1.9")
    monkeypatch.setenv("WRIGHT_RUNTIME_CHANNEL", "local_candidate")
    assert module._child_environment(root)["WRIGHT_RUNTIME_ARTIFACT"] == str(wheel)
    assert wheel.as_uri() in module._install_target()[0]


def test_changed_embedded_source_is_rejected(development, monkeypatch):
    module, release, _, root = development
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr("wright_engineering/dev-release.json", json.dumps({
            "version": release["version"], "source_commit": "0" * 40,
        }))
    release["sha256"] = hashlib.sha256(data.getvalue()).hexdigest()
    module.RELEASE_MANIFEST.write_text(json.dumps(release), encoding="utf-8")
    monkeypatch.setattr(module.urllib.request, "urlopen", lambda *a, **kw: io.BytesIO(data.getvalue()))
    monkeypatch.setattr(module, "_run", lambda *a, **kw: pytest.fail("must not install changed source"))
    with pytest.raises(module.BootstrapError, match="provenance_mismatch"):
        module._prepare_release(Path("python"), module._child_environment(root))
