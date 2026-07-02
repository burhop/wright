from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_provenance_template_lists_source_and_dependency_versions() -> None:
    text = (ROOT / "hermes-plugin-wright/PROVENANCE.md").read_text(encoding="utf-8")

    for expected in [
        "Main repository: https://github.com/burhop/wright",
        "Source branch:",
        "Source commit:",
        "Plugin version:",
        "wright-core version:",
        "wright-tool-registry version:",
        "provenance.json",
        "40-character main repository commit SHA",
    ]:
        assert expected in text


def test_sync_workflow_reports_readme_and_provenance_validation() -> None:
    workflow = (ROOT / ".github/workflows/sync-hermes-plugin-mirror.yml").read_text(
        encoding="utf-8"
    )

    assert "README/provenance validation summary" in workflow
    assert "scripts/validate-hermes-plugin-mirror.sh" in workflow
    assert "provenance.json" in workflow
