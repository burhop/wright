from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/hermes_plugin_mirror"


def copy_fixture(tmp_path: Path) -> Path:
    mirror = tmp_path / "mirror"
    shutil.copytree(FIXTURE, mirror)
    return mirror


def run_validate(
    mirror: Path, channel: str = "stable"
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            str(ROOT / "scripts/validate-hermes-plugin-mirror.sh"),
            "--mirror-dir",
            str(mirror),
            "--channel",
            channel,
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_valid_mirror_fixture_passes_stable_validation(tmp_path: Path) -> None:
    mirror = copy_fixture(tmp_path)
    result = run_validate(mirror, "stable")

    assert result.returncode == 0, result.stderr
    assert "Mirror validation passed" in result.stdout


def test_validator_rejects_prohibited_monorepo_paths(tmp_path: Path) -> None:
    mirror = copy_fixture(tmp_path)
    (mirror / "apps").mkdir()
    (mirror / "apps/api.py").write_text("bad", encoding="utf-8")

    result = run_validate(mirror, "stable")

    assert result.returncode != 0
    assert "prohibited path present: apps" in result.stderr


def test_validator_rejects_stable_workspace_sources(tmp_path: Path) -> None:
    mirror = copy_fixture(tmp_path)
    pyproject = mirror / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text(encoding="utf-8")
        + "\n[tool.uv.sources]\nwright-tool-registry = { workspace = true }\n",
        encoding="utf-8",
    )

    result = run_validate(mirror, "stable")

    assert result.returncode != 0
    assert "stable mirror pyproject must not contain [tool.uv.sources]" in result.stderr


def test_validator_rejects_missing_readme_links(tmp_path: Path) -> None:
    mirror = copy_fixture(tmp_path)
    (mirror / "README.md").write_text("# Missing content\n", encoding="utf-8")

    result = run_validate(mirror, "stable")

    assert result.returncode != 0
    assert "README missing required content" in result.stderr
