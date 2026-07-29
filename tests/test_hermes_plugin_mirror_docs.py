from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_release_runbook_documents_production_adapter_and_identity() -> None:
    doc = (ROOT / "docs/release/hermes-plugin-mirror.md").read_text(encoding="utf-8")
    squashed = " ".join(doc.split())

    for expected in [
        "Hermes Git Adapter Mirror Release Runbook",
        "production thin adapter",
        "migration",
        "cannot replace PyPI",
        "Development",
        "Stable",
        "wright-core",
        "wright-tool-registry",
        "Trusted Publishing",
        "testpypi",
        "pypi",
        "scripts/sync-hermes-plugin-mirror.sh",
        "scripts/validate-hermes-plugin-mirror.sh",
        "Migration Guidance",
        "provenance.json",
        "installed `.git` `HEAD`",
        "hermes plugins install",
        "/wright uninstall",
    ]:
        assert expected in squashed


def test_mkdocs_links_release_runbook() -> None:
    mkdocs = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")

    assert "Hermes Plugin Mirror Release: release/hermes-plugin-mirror.md" in mkdocs
