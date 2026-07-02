from pathlib import Path
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def test_sync_exports_allowlisted_root_plugin_files_and_provenance(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "mirror"

    subprocess.run(
        [
            str(ROOT / "scripts/sync-hermes-plugin-mirror.sh"),
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
        ],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
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
    assert "[tool.uv.sources]" not in (output_dir / "pyproject.toml").read_text(
        encoding="utf-8"
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
    result = subprocess.run(
        [
            str(ROOT / "scripts/sync-hermes-plugin-mirror.sh"),
            "--source",
            "hermes-plugin-wright",
            "--mirror-url",
            "https://github.com/burhop/hermes-plugin-wright",
            "--branch",
            "dev",
            "--dry-run",
        ],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    assert "plugin.yaml" in result.stdout
    assert "provenance.json" in result.stdout
    assert not output_dir.exists()
