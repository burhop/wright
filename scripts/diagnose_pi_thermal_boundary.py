"""Read-only native case audit: boundary coverage and thermal coupling controls."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re


def diagnose(case: Path) -> dict:
    contract_path = case / "contract.json"
    contract = json.loads(contract_path.read_text())
    regions = []
    for region in contract["regions"]:
        boundary = case / "constant" / region["name"] / "polyMesh/boundary"
        patches = re.findall(r"\n\s*([a-zA-Z][a-zA-Z0-9_]*)\s*\n\s*\{([^}]+)\}", boundary.read_text())
        exterior = []
        for name, body in patches:
            if name == "FoamFile" or "sampleRegion" in body:
                continue
            count = re.search(r"nFaces\s+(\d+)\s*;", body)
            exterior.append({"name": name, "faces": int(count[1]) if count else None})
        regions.append({"name": region["name"], "kind": region["kind"], "heat_w": region.get("heat_w", 0), "exterior_patches": exterior})
    return {
        "case": str(case),
        "contract_sha256": hashlib.sha256(contract_path.read_bytes()).hexdigest(),
        "global_solution_controls": (case / "system/fvSolution").read_text(),
        "regions": regions,
        "solid_exterior_faces_not_covered_by_fluid_only_heat_integral": sum(patch["faces"] or 0 for region in regions if region["kind"] == "solid" for patch in region["exterior_patches"]),
        "solver_executed": False,
        "campaign_credit": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", type=Path)
    print(json.dumps(diagnose(parser.parse_args().case), indent=2))
