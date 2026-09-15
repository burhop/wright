from pathlib import Path

import pytest

from scripts.kicad_campaign.repair_schematic_loaded_pins import NEW, OLD, repair


def test_repair_hydrates_only_empty_component_pin_sets(tmp_path: Path) -> None:
    root = tmp_path / "kicad-mcp"
    target = root / "src/kicad_mcp/tools/schematic.py"
    target.parent.mkdir(parents=True)
    target.write_text("prefix\n" + OLD + "suffix\n", encoding="utf-8")

    assert repair(root) == target
    repaired = target.read_text(encoding="utf-8")
    assert OLD not in repaired
    assert NEW in repaired
    assert "if component.pins:" in repaired
    assert "component.update_from_library()" in repaired
    assert "unresolved_pin_references" in repaired
    assert repair(root) == target


def test_repair_fails_closed_for_an_unreviewed_upstream_shape(tmp_path: Path) -> None:
    target = tmp_path / "src/kicad_mcp/tools/schematic.py"
    target.parent.mkdir(parents=True)
    target.write_text("different upstream source\n", encoding="utf-8")

    with pytest.raises(ValueError, match="did not match"):
        repair(tmp_path)
