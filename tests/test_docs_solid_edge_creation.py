from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_solid_edge_operator_docs_are_linked_and_scoped() -> None:
    mkdocs = read_text("mkdocs.yml")
    creation = read_text("docs/integrations/solid-edge-creation.md")
    diagnostics = read_text("docs/operations/solid-edge-diagnostics.md")
    audit = read_text(
        "specs/048-solid-edge-creation-visibility/checklists/completion-audit.md"
    )

    assert "Solid Edge Creation: integrations/solid-edge-creation.md" in mkdocs
    assert "Solid Edge Diagnostics: operations/solid-edge-diagnostics.md" in mkdocs
    assert "WRIGHT_API_MCP_AUTOSTART=0" in creation
    assert "cad.create_part_from_recipe" in creation
    assert "CADMCP_SOLID_EDGE_ALLOWED_ROOTS" in diagnostics
    assert "Not claimed" in audit
    assert "20 redacted Windows trials" in audit
