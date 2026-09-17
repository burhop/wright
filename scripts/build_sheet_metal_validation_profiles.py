"""Build full-scope sheet-metal supplier-handoff validation profiles."""

from __future__ import annotations

from pathlib import Path

from core.process_validation import ValidationProfile, canonical_json
from workspace_service.process_validation.baselines import load_baseline


ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "packages/workspace_service/src/workspace_service/process_validation/profiles"
CASES = {
    "sheet-metal-supplier-handoff-01": {
        "parts": ["wall-dock"],
        "material_pointer": "/materialsQuery/materials/0/name",
        "material": "Aluminum Alloy:3.3523 , AlMg2.5, EN-AW 5052 ",
    },
    "sheet-metal-supplier-handoff-02": {
        "parts": ["cable-trough"],
        "material_pointer": "/required_native_mapping/name",
        "material": "Steel - Unalloyed:1.0301 , C10",
    },
    "sheet-metal-supplier-handoff-03": {
        "parts": ["base-tray", "removable-lid"],
        "material_pointer": "/materials/0/name",
        "material": "Aluminum Alloy:3.3523 , AlMg2.5, EN-AW 5052 ",
    },
}


def check(
    identifier,
    requirements,
    role,
    *,
    constraint=None,
    reader="sheet-metal-evidence",
    method="independent_measurement",
    selector="",
    parameters=None,
    unit=None,
    frame=None,
):
    return {
        "id": identifier,
        "version": "1",
        "requirement_ids": requirements,
        "subject_role": role,
        "reader": reader,
        "selector": selector,
        "constraint": constraint or {"operator": "exists"},
        "unit": unit,
        "frame": frame,
        "evidence_method": method,
        "parameters": parameters or {},
        "applicability_reason": None,
    }


def build(scenario_id: str, values: dict) -> ValidationProfile:
    prefix = "SHEET" + scenario_id[-2:]
    baseline = load_baseline(scenario_id).model_dump(mode="json")
    known = {item["id"] for item in baseline["requirements"]}

    def ids(*suffixes):
        result = [prefix + "-" + suffix for suffix in suffixes]
        if not set(result) <= known:
            raise ValueError(set(result) - known)
        return result

    for requirement in baseline["requirements"]:
        requirement["review_required"] = True
    design_ids = sorted(
        known - set(ids("CORRESPONDENCE", "HANDOFF", "SCOPE"))
    )
    checks = [
        check(
            "installed-material-label",
            ids("MATERIAL"),
            "installed_materials",
            reader="structured",
            method="structured_value",
            selector=values["material_pointer"],
            constraint={"operator": "equals", "expected": values["material"]},
        )
    ]
    manifest_roles = {
        "installed_materials": "installed-materials.json",
        "manufacturing_intent": "manufacturing-intent.md",
        "supplier_evidence": "supplier-evidence.json",
        "preview_receipt": "supplier-preview.json",
        "cart_receipt": "cart-quote-handoff.json",
    }
    for part in values["parts"]:
        token = part.replace("-", "_")
        role_map = {
            f"{token}_native": f"{part}.psm",
            f"{token}_step": f"{part}.step",
            f"{token}_dxf": f"{part}.dxf",
            f"{token}_screenshot": f"{part}.jpg",
            f"{token}_check": f"{part}-measured-check.json",
        }
        manifest_roles.update(role_map)
        checks.extend(
            [
                check(
                    f"{part}-native-check",
                    ids("NATIVE"),
                    f"{token}_check",
                    constraint={"operator": "equals", "expected": True},
                    selector=f"sheet-metal/{part}/native-check",
                    parameters={
                        "operation": "design_check",
                        "required_requirement_ids": ids("NATIVE"),
                    },
                ),
                check(
                    f"{part}-step-present",
                    ids("NATIVE", "CORRESPONDENCE"),
                    f"{token}_step",
                    reader="step-bounding-box",
                    method="native_inspection",
                    selector="box/x_span_mm",
                    constraint={"operator": "range", "minimum": 0.001},
                    unit="mm",
                    frame="model_axes",
                ),
                check(
                    f"{part}-developed-dxf",
                    ids("CORRESPONDENCE"),
                    f"{token}_dxf",
                    selector=f"sheet-metal/{part}/dxf-entity-count",
                    constraint={"operator": "range", "minimum": 1},
                    parameters={"operation": "dxf_contract"},
                    unit="1",
                    frame="flat_pattern_mm",
                ),
                check(
                    f"{part}-native-review",
                    [item for item in design_ids],
                    f"{token}_check",
                    constraint={"operator": "review"},
                    reader="structured",
                    method="human_review",
                ),
            ]
        )
    manifest_related = sorted(manifest_roles)
    checks.extend(
        [
            check(
                "final-manifest-binding",
                ids("CORRESPONDENCE", "HANDOFF"),
                "final_manifest",
                selector="sheet-metal/final-manifest",
                constraint={"operator": "range", "minimum": len(manifest_roles)},
                parameters={
                    "operation": "manifest_binding",
                    "related_roles": manifest_related,
                    "expected_basenames": manifest_roles,
                },
                unit="1",
            ),
            check(
                "supplier-preview-simulation",
                ids("HANDOFF"),
                "preview_receipt",
                constraint={"operator": "equals", "expected": True},
                selector="sheet-metal/supplier-preview",
                parameters={
                    "operation": "simulated_handoff",
                    "action_kind": "supplier_upload_preview",
                    "scenario_id": scenario_id,
                    "destination": f"test://081-engineering-datasets-v1/supplier/{scenario_id}",
                },
            ),
            check(
                "cart-handoff-simulation",
                ids("HANDOFF"),
                "cart_receipt",
                constraint={"operator": "equals", "expected": True},
                selector="sheet-metal/cart-handoff",
                parameters={
                    "operation": "simulated_handoff",
                    "action_kind": "cart_quote_handoff",
                    "scenario_id": scenario_id,
                    "destination": f"test://081-engineering-datasets-v1/supplier/{scenario_id}",
                },
            ),
            check(
                "manufacturing-intent-review",
                design_ids + ids("SCOPE"),
                "manufacturing_intent",
                constraint={"operator": "review"},
                reader="structured",
                method="human_review",
            ),
            check(
                "correspondence-and-handoff-review",
                ids("CORRESPONDENCE", "HANDOFF", "SCOPE"),
                "engineering_handoff",
                constraint={"operator": "review"},
                reader="structured",
                method="human_review",
            ),
        ]
    )
    return ValidationProfile.model_validate(
        {
            "id": scenario_id + "-full",
            "version": "1",
            "baseline": baseline,
            "checks": checks,
            "excluded_scope": [],
            "limitations": [
                "The reader validates native-inspection evidence, developed-DXF structure, exact artifact lineage and simulated handoff safety; it does not parse proprietary PSM feature history.",
                "Bend feasibility, reliefs, detailed feature correspondence, supplier acceptance and physical fabrication remain behind authenticated engineering review and the declared HOLD boundary.",
            ],
            "supported_kinds": ["file", "value"],
        }
    )


def render():
    return {
        DESTINATION / f"{scenario_id}.json": (
            canonical_json(build(scenario_id, values)) + "\n"
        ).encode("utf-8")
        for scenario_id, values in CASES.items()
    }


def main():
    for path, content in render().items():
        path.write_bytes(content)
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
