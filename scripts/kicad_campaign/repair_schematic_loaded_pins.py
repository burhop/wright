"""Hydrate library pins after kicad-sch-api loads a saved schematic.

The pinned kicad-sch-api parser preserves instance pin UUIDs but leaves the
component ``pins`` collection empty.  Editing operations then reject valid pin
numbers after a save/load boundary.  The public ``update_from_library`` method
restores the same library-backed pin definitions used when a component is first
added.
"""
from __future__ import annotations

from pathlib import Path
import sys


OLD = '''            _sch_mod._current_schematic = ksa.load_schematic(schematic_path)
            comp_count = len(list(_sch_mod._current_schematic.components))
            logger.info("Loaded schematic: %s (%d components)", schematic_path, comp_count)
            return {"status": "ok", "file_path": schematic_path, "components": comp_count}
'''

NEW = '''            _sch_mod._current_schematic = ksa.load_schematic(schematic_path)
            components = list(_sch_mod._current_schematic.components)
            hydrated_references = []
            unresolved_references = []
            for component in components:
                if component.pins:
                    continue
                if component.update_from_library():
                    hydrated_references.append(component.reference)
                else:
                    unresolved_references.append(component.reference)
            comp_count = len(components)
            logger.info(
                "Loaded schematic: %s (%d components, %d pin sets hydrated)",
                schematic_path,
                comp_count,
                len(hydrated_references),
            )
            return {
                "status": "ok",
                "file_path": schematic_path,
                "components": comp_count,
                "pin_sets_hydrated": len(hydrated_references),
                "hydrated_references": hydrated_references,
                "unresolved_pin_references": unresolved_references,
            }
'''


def repair(root: Path) -> Path:
    target = root / "src/kicad_mcp/tools/schematic.py"
    source = target.read_text(encoding="utf-8")
    if NEW in source:
        return target
    if source.count(OLD) != 1:
        raise ValueError("Pinned schematic load implementation did not match the reviewed source")
    target.write_text(source.replace(OLD, NEW), encoding="utf-8")
    return target


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: repair_schematic_loaded_pins.py KICAD_MCP_ROOT")
    print(repair(Path(sys.argv[1]).resolve()))
