from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "hermes-plugin-wright/README.md"


def test_mirror_readme_has_customer_lifecycle_sections_and_links() -> None:
    text = README.read_text(encoding="utf-8")
    squashed = " ".join(text.split())

    for expected in [
        "official thin Wright Hermes plugin mirror",
        "Stable Install",
        "Development Install",
        "hermes plugins install https://github.com/burhop/hermes-plugin-wright/tree/main --enable",
        "hermes plugins install https://github.com/burhop/hermes-plugin-wright/tree/dev --enable",
        "hermes plugins update wright",
        "hermes plugins remove wright",
        "Migration From the Monorepo Subdirectory",
        "https://github.com/burhop/wright",
        "https://github.com/burhop/wright/issues",
        "https://github.com/burhop/wright/releases",
        "https://pypi.org/project/wright-core/",
        "https://pypi.org/project/wright-tool-registry/",
        "PROVENANCE.md",
    ]:
        assert expected in squashed


def test_mirror_readme_explains_update_requires_git_metadata() -> None:
    text = README.read_text(encoding="utf-8")

    assert "plugin.yaml" in text
    assert ".git" in text
    assert "standard update command" in text
