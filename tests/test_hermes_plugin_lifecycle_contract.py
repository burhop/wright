from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_lifecycle_common_supports_root_mirror_install_identifiers() -> None:
    common = read_text("scripts/hermes-plugin-lifecycle-common.sh")

    assert "PLUGIN_SOURCE_MODE" in common
    assert "--mirror-root" in common
    assert "tree/${PLUGIN_REF}" in common
    assert "tree/${PLUGIN_REF}/${PLUGIN_SUBDIR}" in common
    assert "WRIGHT_PLUGIN_SOURCE_MODE" in common


def test_lifecycle_scripts_document_root_mirror_usage() -> None:
    readme = read_text("scripts/README.md")
    makefile = read_text("Makefile")

    assert "--mirror-root" in readme
    assert "https://github.com/burhop/hermes-plugin-wright/tree/dev" in readme
    assert "hermes-plugin-root-lifecycle-test:" in makefile
