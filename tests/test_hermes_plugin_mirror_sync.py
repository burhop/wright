from pathlib import Path
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def run_script(script_name: str, *args: str) -> subprocess.CompletedProcess[str]:
    script = ROOT / "scripts" / script_name
    command = [str(script)]
    if sys.platform == "win32":
        command = ["bash", str(script)]

    return subprocess.run(
        command + list(args),
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_sync_exports_allowlisted_root_plugin_files_and_provenance(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "mirror"

    run_script(
        "sync-hermes-plugin-mirror.sh",
        "--source",
        "hermes-plugin-wright",
        "--mirror-url",
        "https://github.com/burhop/hermes-plugin-wright",
        "--branch",
        "dev",
        "--channel",
        "development",
        "--output-dir",
        str(output_dir),
    )

    for path in [
        "plugin.yaml",
        "__init__.py",
        "bridge.py",
        "catalog.py",
        "catalog.yaml",
        "commands.py",
        "schemas.py",
        "pyproject.toml",
        "README.md",
        "LICENSE",
        "verify_plugin.py",
        "tests/test_plugin_metadata.py",
        "provenance.json",
    ]:
        assert (output_dir / path).exists(), path

    assert not (output_dir / "apps").exists()
    assert not (output_dir / "packages").exists()
    pyproject_text = (output_dir / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.uv.sources]" not in pyproject_text
    assert re.search(
        r"wright-core @ git\+https://github\.com/burhop/wright\.git@[0-9a-f]{40}#subdirectory=packages/core",
        pyproject_text,
    )
    assert re.search(
        r"wright-tool-registry @ git\+https://github\.com/burhop/wright\.git@[0-9a-f]{40}#subdirectory=packages/tool_registry",
        pyproject_text,
    )

    provenance = json.loads(
        (output_dir / "provenance.json").read_text(encoding="utf-8")
    )
    assert provenance["main_repo_url"] == "https://github.com/burhop/wright"
    assert (
        provenance["mirror_repo_url"]
        == "https://github.com/burhop/hermes-plugin-wright"
    )
    assert re.fullmatch(r"[0-9a-f]{40}", provenance["commit_sha"])
    assert provenance["source_paths"] == ["hermes-plugin-wright"]


def test_sync_dry_run_lists_mirror_files_without_writing(tmp_path: Path) -> None:
    output_dir = tmp_path / "not-created"
    result = run_script(
        "sync-hermes-plugin-mirror.sh",
        "--source",
        "hermes-plugin-wright",
        "--mirror-url",
        "https://github.com/burhop/hermes-plugin-wright",
        "--branch",
        "dev",
        "--dry-run",
    )

    assert "plugin.yaml" in result.stdout
    assert "provenance.json" in result.stdout
    assert not output_dir.exists()


def test_sync_stable_mirror_keeps_pypi_dependencies(tmp_path: Path) -> None:
    output_dir = tmp_path / "mirror"

    run_script(
        "sync-hermes-plugin-mirror.sh",
        "--source",
        "hermes-plugin-wright",
        "--mirror-url",
        "https://github.com/burhop/hermes-plugin-wright",
        "--branch",
        "main",
        "--channel",
        "stable",
        "--output-dir",
        str(output_dir),
    )

    pyproject_text = (output_dir / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.uv.sources]" not in pyproject_text
    assert "git+https://github.com/burhop/wright.git" not in pyproject_text
    assert "wright-tool-registry>=0.1.0,<0.2.0" in pyproject_text
