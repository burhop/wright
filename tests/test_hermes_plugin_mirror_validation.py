from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/hermes_plugin_mirror"


def copy_fixture(tmp_path: Path) -> Path:
    mirror = tmp_path / "mirror"
    shutil.copytree(
        FIXTURE,
        mirror,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    return mirror


def run_validate(
    mirror: Path, channel: str = "stable"
) -> subprocess.CompletedProcess[str]:
    script = ROOT / "scripts/validate-hermes-plugin-mirror.sh"
    command = [str(script)]
    if sys.platform == "win32":
        command = ["bash", str(script)]

    return subprocess.run(
        command
        + [
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


def test_validator_rejects_development_unpinned_git_dependencies(
    tmp_path: Path,
) -> None:
    mirror = copy_fixture(tmp_path)
    pyproject = mirror / "pyproject.toml"
    pyproject.write_text(
        pyproject.read_text(encoding="utf-8").replace(
            '"wright-tool-registry>=0.1.0,<0.2.0",',
            '"wright-tool-registry @ git+https://github.com/burhop/wright.git@dev#subdirectory=packages/tool_registry",',
        ),
        encoding="utf-8",
    )

    result = run_validate(mirror, "development")

    assert result.returncode != 0
    assert "development pyproject must pin wright-core" in result.stderr
    assert "development pyproject must pin wright-tool-registry" in result.stderr
