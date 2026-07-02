from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_runbook_documents_channels_publication_and_migration() -> None:
    doc = (ROOT / "docs/release/hermes-plugin-mirror.md").read_text(encoding="utf-8")
    squashed = " ".join(doc.split())

    for expected in [
        "Hermes Plugin Mirror Release Runbook",
        "Development",
        "Stable",
        "wright-core",
        "wright-tool-registry",
        "Trusted Publishing",
        "testpypi",
        "pypi",
        "scripts/sync-hermes-plugin-mirror.sh",
        "scripts/validate-hermes-plugin-mirror.sh",
        "--mirror-root",
        "Migration Guidance",
    ]:
        assert expected in squashed


def test_mkdocs_links_release_runbook() -> None:
    mkdocs = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")

    assert "Hermes Plugin Mirror Release: release/hermes-plugin-mirror.md" in mkdocs
