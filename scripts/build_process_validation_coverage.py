"""Rebuild the source inventory; this does not evaluate any generated output."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


CAPABILITIES = {
    "printed-replacement-part": ["geometry", "manufacturing.slice"],
    "raspberry-pi-enclosure": ["geometry", "source.authority", "thermal.cfd"],
    "sheet-metal-supplier-handoff": ["geometry", "manufacturing.sheet_metal", "bundle"],
    "lightweight-equipment-bracket": ["geometry", "structural.fields"],
    "parametric-drill-jig": ["geometry", "fit.datum"],
    "robot-tracking-diagnosis": ["structured", "timeseries.frames"],
    "heat-spreader-sizing": ["thermal.conduction", "numerical.refinement"],
    "sensor-fan-harness": ["structured", "electrical.network"],
    "sensor-interface-pcb": ["electrical.netlist", "manufacturing.ecad"],
    "water-heater-sizing": ["numerical.timeseries", "modelica.model"],
}

SUPPORT_DEFINITIONS = {
    "qualified": "A frozen scenario profile and reader scope passed independent controls and a retained canonical process demonstration.",
    "implemented": "A reusable runtime capability and frozen profile exist, but the scenario has not passed every required qualification and retained demonstration.",
    "planned": "The extension is defined, but its scenario-specific profile or reader is not implemented and qualified.",
    "unavailable": "No bounded trustworthy runtime reader is currently available for this capability.",
}

EXTENSION_RECIPES = {
    "geometry": {
        "prerequisites": ["authoritative geometry requirements", "actual candidate files"],
        "steps": [
            "freeze semantic feature selectors, datum, units and tolerances",
            "implement actual-file readback for every mandatory feature",
            "qualify good, alternate, targeted-defect and boundary controls",
        ],
    },
    "fit.datum": {
        "prerequisites": ["source-backed mating dimensions", "declared datum frame"],
        "steps": [
            "separate radial and diametral clearances",
            "measure mating features in the declared frame",
            "qualify transformed-datum and unit-error controls",
        ],
    },
    "manufacturing.slice": {
        "prerequisites": ["qualified slicer or format reader", "material and process limits"],
        "steps": [
            "bind model revision to slicer inputs and settings",
            "read layer/toolpath and material facts independently",
            "qualify orientation, clearance and correspondence defects",
        ],
    },
    "source.authority": {
        "prerequisites": ["versioned manufacturer source", "approved authority policy"],
        "steps": [
            "pin source identity and retrieval date",
            "map each interface requirement to an exact locator",
            "block stale, conflicting or unavailable authority",
        ],
    },
    "thermal.cfd": {
        "prerequisites": ["qualified field reader", "boundary-condition lineage"],
        "steps": [
            "bind mesh, loads, materials and solver output revisions",
            "measure balance, convergence and requirement quantities",
            "qualify wrong-load, mesh and fabricated-summary defects",
        ],
    },
    "manufacturing.sheet_metal": {
        "prerequisites": ["qualified native flat-pattern reader", "bend and material rules"],
        "steps": [
            "bind formed and flat revisions",
            "inspect bends, reliefs, thickness and true flat geometry",
            "qualify correspondence and multipart completeness defects",
        ],
    },
    "bundle": {
        "prerequisites": ["declared deliverable inventory", "cross-format identity rules"],
        "steps": [
            "freeze required files, quantities and revision relationships",
            "inspect bounded archive contents and cross-file identifiers",
            "qualify missing, duplicate, stale and mismatched members",
        ],
    },
    "structural.fields": {
        "prerequisites": ["qualified FEA field reader", "load/restraint lineage"],
        "steps": [
            "bind geometry, loads, restraints, materials and mesh",
            "read reactions, stress and displacement fields",
            "qualify equilibrium, convergence and wrong-boundary defects",
        ],
    },
    "structured": {
        "prerequisites": ["frozen field/table schema", "source-backed limits"],
        "steps": [
            "map every mandatory requirement to exact JSON/CSV selectors",
            "freeze units, missing-value and identity rules",
            "qualify duplicate, malformed, boundary and stale controls",
        ],
    },
    "timeseries.frames": {
        "prerequisites": ["clock and frame definitions", "qualified time-series reader"],
        "steps": [
            "bind timestamps, masks and transforms",
            "derive metrics from raw samples rather than summaries",
            "qualify offset, frame, dropout and windowing defects",
        ],
    },
    "electrical.network": {
        "prerequisites": ["frozen connectivity graph", "wire and load properties"],
        "steps": [
            "read endpoint and splice topology",
            "compute shared currents, voltage drop and cut length",
            "qualify swapped-net, missing-return and unit defects",
        ],
    },
    "electrical.netlist": {
        "prerequisites": ["qualified native netlist reader", "frozen component/net rules"],
        "steps": [
            "read exact nets, values, footprints and coordinates",
            "bind electrical rules to source requirements",
            "qualify wrong-net, value, placement and power defects",
        ],
    },
    "manufacturing.ecad": {
        "prerequisites": ["qualified PCB/fabrication readers", "fab-output lineage"],
        "steps": [
            "bind native design to Gerber, drill and BOM revisions",
            "inspect stackup, clearances and output correspondence",
            "qualify DRC-success-with-wrong-content and stale-output defects",
        ],
    },
    "thermal.conduction": {
        "prerequisites": ["candidate and refined fields", "source-backed thermal constants"],
        "steps": [
            "freeze geometry, loads, conductivity and boundary conditions",
            "read actual fields and independently compute balance/reference rise",
            "qualify load, unit, lineage and threshold defects",
        ],
    },
    "numerical.refinement": {
        "prerequisites": ["paired coarse/fine outputs", "declared comparison metric"],
        "steps": [
            "bind both outputs to one candidate revision",
            "derive sensitivity from the actual fields",
            "qualify missing, swapped and nonconverged pairs",
        ],
    },
    "numerical.timeseries": {
        "prerequisites": ["qualified trajectory reader", "source-backed event criteria"],
        "steps": [
            "bind parameters, initial conditions and time grid",
            "integrate energy and locate threshold crossings independently",
            "qualify truncation, timestep, unit and candidate-grid defects",
        ],
    },
    "modelica.model": {
        "prerequisites": ["qualified Modelica parser/runtime", "approved model semantics"],
        "steps": [
            "inspect equations, parameters and derivative semantics",
            "bind compiled simulation to the exact model revision",
            "qualify altered thermostat, energy and initialization behavior",
        ],
    },
}

GENERIC_IMPLEMENTED = {
    ("robot-tracking-diagnosis", "structured"),
    ("sensor-fan-harness", "structured"),
}

UNAVAILABLE = {
    "manufacturing.slice",
    "source.authority",
    "thermal.cfd",
    "manufacturing.sheet_metal",
    "structural.fields",
    "electrical.network",
    "electrical.netlist",
    "manufacturing.ecad",
    "modelica.model",
}

QUALIFIED = {
    "parametric-drill-jig-01": {
        "profile_resource": "parametric-drill-jig-01",
        "profile_ref": {
            "id": "parametric-drill-jig-01-seat-geometry",
            "version": "1",
            "sha256": "5488f377adfa5eaea61ce4b8e299654bb74709ed313b67e8f04494bd2e4a3884",
        },
        "baseline_ref": {
            "id": "parametric-drill-jig-01-seat-basis",
            "version": "1",
            "sha256": "5fb63ff5fca47d189665efe2d22424743205a0c12812f193cd79b49fe4ebf2d8",
        },
        "reader_ids": ["step-seat-geometry@1"],
        "scope": "H1/H2 seat centers and diameters in the frozen workpiece datum only.",
        "limitations": "Clamp, keys, stock, full fit/manufacturing and physical qualification remain excluded.",
        "evidence": [
            "tests/external/process_validation/test_geometry.py",
            "artifacts/process-validation/engineering/20260916T213859Z/jig/evidence.json",
        ],
    },
    "heat-spreader-sizing-01": {
        "profile_resource": "heat-spreader-sizing-01",
        "profile_ref": {
            "id": "heat-spreader-sizing-01-fields",
            "version": "1",
            "sha256": "28c7cbd9811fe2423715b7c485195a5cafd53cbc7118a66492fa0995036bdc82",
        },
        "baseline_ref": {
            "id": "heat-spreader-sizing-01-basis",
            "version": "1",
            "sha256": "3f6464140ae741a0ef9ecd8dabcde8bcbbe3cc1f9755955d7ec12b1cac89e564",
        },
        "reader_ids": ["thermal-field@1"],
        "scope": "40/60 mm conduction fields, analytical rise, heat balance, refinement and 45 degC selection.",
        "limitations": "Interface resistance, CAD/manufacturing and physical thermal qualification remain excluded.",
        "evidence": [
            "tests/external/process_validation/test_thermal.py",
            "artifacts/process-validation/engineering/20260916T213859Z/heat/evidence.json",
        ],
    },
}

IMPLEMENTED_PROFILES = {
    "robot-tracking-diagnosis-01": {
        "profile_resource": "robot-tracking-diagnosis-01",
        "profile_ref": {
            "id": "robot-tracking-diagnosis-01-full",
            "version": "1",
            "sha256": "0d3704713b050507ce0cdc1d54288eadac617fd54601362fdd4bd281144c582c",
        },
        "baseline_ref": {
            "id": "robot-tracking-diagnosis-01-basis",
            "version": "1",
            "sha256": "17d6451a1e12dad10f74c8b095c996bad312ba27fa9763c69c7e6ad82491227b",
        },
        "reader_ids": ["structured@1", "tracking-timeline@1"],
        "scope": "Traceable conversion, alignment, retained timeline metrics, event correspondence, deliverable presence and required plot/diagnosis reviews.",
        "limitations": "Required human reviews are not yet authenticated; physical operation and causal proof remain excluded.",
        "evidence": [
            "tests/external/process_validation/test_tracking.py",
            "tests/external/process_validation/test_tracking_profiles.py",
        ],
    },
    "robot-tracking-diagnosis-02": {
        "profile_resource": "robot-tracking-diagnosis-02",
        "profile_ref": {
            "id": "robot-tracking-diagnosis-02-full",
            "version": "1",
            "sha256": "6c7f0759d057cd6389c933d74bfbed1341e6df8cd5a2e3803dbe98e109c83db8",
        },
        "baseline_ref": {
            "id": "robot-tracking-diagnosis-02-basis",
            "version": "1",
            "sha256": "d2855eaa739e67fe4a8df94c50d47abc4b538ff7753a5230f3a314ebbfb388a2",
        },
        "reader_ids": ["structured@1", "tracking-timeline@1"],
        "scope": "Traceable conversion, spatial/time alignment, retained timeline metrics, event correspondence, deliverable presence and required plot/diagnosis reviews.",
        "limitations": "The retained output contains false gap records and required human reviews are not yet authenticated; physical operation and causal proof remain excluded.",
        "evidence": [
            "tests/external/process_validation/test_tracking.py",
            "tests/external/process_validation/test_tracking_profiles.py",
        ],
    },
    "robot-tracking-diagnosis-03": {
        "profile_resource": "robot-tracking-diagnosis-03",
        "profile_ref": {
            "id": "robot-tracking-diagnosis-03-full",
            "version": "1",
            "sha256": "19f58fd4bb6351737ae733c5610b0db9107594386dfa3caf8ed76cefa61628cc",
        },
        "baseline_ref": {
            "id": "robot-tracking-diagnosis-03-basis",
            "version": "1",
            "sha256": "200605741a81745b82408656a1d12bdae388e74b5e3a86dbfbe0beb457976656",
        },
        "reader_ids": ["structured@1", "tracking-timeline@1"],
        "scope": "Traceable conversion, missing-sample preservation, retained timeline metrics, wrapped yaw, event correspondence, deliverable presence and required plot/diagnosis reviews.",
        "limitations": "Required human reviews are not yet authenticated; physical operation and causal proof remain excluded.",
        "evidence": [
            "tests/external/process_validation/test_tracking.py",
            "tests/external/process_validation/test_tracking_profiles.py",
        ],
    },
    "heat-spreader-sizing-02": {
        "profile_resource": "heat-spreader-sizing-02-full",
        "profile_ref": {"id": "heat-spreader-sizing-02-full", "version": "1", "sha256": "42daf6deb97644e39d119240559e54d21e0ee6cd5a062fe86ed4b5060ef2ae66"},
        "baseline_ref": {"id": "heat-spreader-sizing-02-basis", "version": "1", "sha256": "c135eb38bdb6df7de1059cba125b4d9ffa857f9646c026afb6f30d8caf366021"},
        "reader_ids": ["step-bounding-box@1", "structured@1", "thermal-field@1"],
        "scope": "Actual STEP envelopes, coarse/refined fields, analytical agreement, balance, refinement, outcomes, selection, deliverables and required basis review.",
        "limitations": "Required basis review is not yet authenticated; physical thermal qualification and certification remain excluded.",
        "evidence": ["tests/external/process_validation/test_step_box.py", "tests/external/process_validation/test_heat_profiles.py"],
    },
    "heat-spreader-sizing-03": {
        "profile_resource": "heat-spreader-sizing-03-full",
        "profile_ref": {"id": "heat-spreader-sizing-03-full", "version": "1", "sha256": "9802f76c9413ba9bc8ce312a5c90f0b78b2927ad7bf090396459d04a4bf620d8"},
        "baseline_ref": {"id": "heat-spreader-sizing-03-basis", "version": "1", "sha256": "b7aa6aff79adc8b3f6782495c73cc9bbb17dbfa4df763cc92281693ae6add6f7"},
        "reader_ids": ["step-bounding-box@1", "structured@1", "thermal-field@1"],
        "scope": "Actual STEP envelopes, contact-resistance fields, analytical agreement, balance, refinement, outcomes, selection, deliverables and required design review.",
        "limitations": "Required design review is not yet authenticated; physical thermal qualification and certification remain excluded.",
        "evidence": ["tests/external/process_validation/test_step_box.py", "tests/external/process_validation/test_heat_profiles.py"],
    },
}

for _scenario_id, _profile_sha, _baseline_sha in (
    ("sensor-fan-harness-01", "585eb8e5b0d72bce2f82de8a515354548e8e23eb821ef0fd80f120f5ec821621", "2bb18ff7bab8624f21dea88b8df297ea42a9fe7e144a75373d5f46903cc8efed"),
    ("sensor-fan-harness-02", "6108bfcac945ff3018c19a581e72aef2dcf615dba62295a5b5d2ebc6ffb26578", "81b536a099781344aef35d76d34c9b3128c44f8f88ea508809af0aafefdbce9e"),
    ("sensor-fan-harness-03", "08a75a770bf113319b42c3190930877285758762cf068f4c51b25e2975e46ff9", "b1083fac47ba76119e11185808a18c5ceb552950de3260f341d6566ed81e7648"),
):
    IMPLEMENTED_PROFILES[_scenario_id] = {
        "profile_resource": _scenario_id,
        "profile_ref": {"id": _scenario_id + "-full", "version": "1", "sha256": _profile_sha},
        "baseline_ref": {"id": _scenario_id + "-basis", "version": "1", "sha256": _baseline_sha},
        "reader_ids": ["harness@1", "structured@1"],
        "scope": "Source-schedule topology, reserve pins, unique cut arithmetic, contact-inclusive voltage drop, deliverables and required engineering reviews.",
        "limitations": "Retained voltage evidence omits total contact/splice drop and required reviews are not yet authenticated; physical production remains excluded.",
        "evidence": ["tests/external/process_validation/test_harness.py", "tests/external/process_validation/test_harness_profiles.py"],
    }

for _scenario_id, _profile_sha, _baseline_sha in (
    ("water-heater-sizing-01", "50cbd44da2968007256b4826d4aa4b4f7ca0783f001ac6372c58143ef4e2705c", "6f83a7235a75361b4fc8168f288d6d4277601dce31d88949bf8c7294c8b1f741"),
    ("water-heater-sizing-02", "bb1998684bf64f76a576fb101a434e3297caeab6f881a9386d7e48317b667cc5", "5e2ab52fe2ca956a0e207e7f1d93601a9ed0ab88a03d8759955d791dbedd9e66"),
    ("water-heater-sizing-03", "e4ea406d1eb765a967c5405f075e2f670ba39586f7f353fca2057b3715e4785a", "84ba8e72f5de5df5f687a9bbb112da23b89fd71f2aeb037fa784d00d1495eae0"),
):
    IMPLEMENTED_PROFILES[_scenario_id] = {
        "profile_resource": _scenario_id,
        "profile_ref": {"id": _scenario_id + "-full", "version": "1", "sha256": _profile_sha},
        "baseline_ref": {"id": _scenario_id + "-basis", "version": "1", "sha256": _baseline_sha},
        "reader_ids": ["structured@1", "water-heater-timeline@1"],
        "scope": "Exact candidate/loss grid, initial state, electrical/thermal power, complete one-second baseline grid, independent target crossings, selection, deliverables and required reviews.",
        "limitations": "Retained parameter summaries omit required kit identity/version and required reviews are not authenticated; physical heater qualification remains excluded.",
        "evidence": ["tests/external/process_validation/test_water_heater.py", "tests/external/process_validation/test_water_heater_profiles.py"],
    }

for _scenario_id, _profile_sha, _baseline_sha in (
    ("parametric-drill-jig-02", "6592d49505d2ecb87ab33ac9fa21a6d436c4852046ad2187efaffe582b8a7448", "77f06f130aeca4dbfaa6085eda8f8a1c7abc9671cb445479891fa087fb58094d"),
    ("parametric-drill-jig-03", "3c0afcf348c3562c09098c158c2bcbe892b0cb3f92c036f9580b9013009c7d03", "d10f4d89c43d6140309c4a19fee7c88d0d83e39dfe2c0474e57cf5f9d8191a4f"),
):
    IMPLEMENTED_PROFILES[_scenario_id] = {
        "profile_resource": _scenario_id,
        "profile_ref": {"id": _scenario_id + "-full", "version": "1", "sha256": _profile_sha},
        "baseline_ref": {"id": _scenario_id + "-basis", "version": "1", "sha256": _baseline_sha},
        "reader_ids": ["step-seat-geometry@1", "structured@1"],
        "scope": "Actual STEP body/flange seat coordinates and diameters, required DXF/report deliverables and authenticated review of remaining geometry/design obligations.",
        "limitations": "Required design reviews are not authenticated; physical fit, machining, drilling and supplier qualification remain excluded.",
        "evidence": ["tests/external/process_validation/test_geometry.py", "tests/external/process_validation/test_jig_profiles.py"],
    }

for _scenario_id, _profile_sha, _baseline_sha in (
    ("sensor-interface-pcb-01", "bb2524c35af414900992f39d3330387316187fa7217c082d68b17bbe719e8007", "e24d15c8f27361632e58b9dcb3e3687e97446d95de21905cef1792dbc59ddb79"),
    ("sensor-interface-pcb-02", "f574687e600949f5b33887ab97ac14b02c7d0e5f251ac494c93d390614009f7a", "e538f38efa35d709ee8c2b53bdf33c0f50ebdd316ecdb68830979cf3bb8260b3"),
    ("sensor-interface-pcb-03", "c0964bd98e92480c3c8e2bc1d258fdf72ff504ee26268355c53d8f4f52b62855", "eac0a5621632de48fd80a2aec4cbf38dd01021f9c48fd95106e4bcc46015bcfe"),
):
    IMPLEMENTED_PROFILES[_scenario_id] = {
        "profile_resource": _scenario_id,
        "profile_ref": {"id": _scenario_id + "-full", "version": "1", "sha256": _profile_sha},
        "baseline_ref": {"id": _scenario_id + "-basis", "version": "1", "sha256": _baseline_sha},
        "reader_ids": ["kicad@1", "structured@1"],
        "scope": "Native PCB pin-to-net mapping, values/footprints, required placements, board outline and holes, BOM, ERC/DRC errors, fabrication inventory and case-03 power widths, plus required engineering review.",
        "limitations": "Warning disposition, source compatibility, full native-to-fabrication correspondence, physical qualification and release authorization require authenticated engineering review.",
        "evidence": ["tests/external/process_validation/test_kicad.py", "tests/external/process_validation/test_pcb_profiles.py"],
    }

FULL_SCOPE_IMPLEMENTED = {
    **IMPLEMENTED_PROFILES,
    "heat-spreader-sizing-01": {
        "profile_resource": "heat-spreader-sizing-01-full",
        "profile_ref": {"id": "heat-spreader-sizing-01-full", "version": "1", "sha256": "41dc00c372147995ef6e68a86052c98d7a5b8e8c0ad9986e5ed624733e678923"},
        "baseline_ref": {"id": "heat-spreader-sizing-01-basis", "version": "1", "sha256": "819635eab37792ce1fee9832e5c085c5803760b61a4350e04b50de818c17c968"},
        "reader_ids": ["step-bounding-box@1", "structured@1", "thermal-field@1"],
        "scope": "Actual STEP envelopes, coarse/refined fields, analytical agreement, balance, refinement, outcomes, selection, deliverables and required basis review.",
        "limitations": "Required basis review is not yet authenticated; physical thermal qualification and certification remain excluded.",
        "evidence": ["tests/external/process_validation/test_step_box.py", "tests/external/process_validation/test_heat_profiles.py"],
    },
    "parametric-drill-jig-01": {
        "profile_resource": "parametric-drill-jig-01-full",
        "profile_ref": {"id": "parametric-drill-jig-01-full", "version": "1", "sha256": "114a3a204e3e208a5bde00da35a5c6ada870bf303784d8ae8ca95d27be639492"},
        "baseline_ref": {"id": "parametric-drill-jig-01-basis", "version": "1", "sha256": "f3018a6f6843cec7d03f2e7b06a86628206e4082ae3b4fd8e9b22521885a6644"},
        "reader_ids": ["step-seat-geometry@1", "structured@1"],
        "scope": "Actual STEP body/flange seat coordinates and diameters, required DXF/report deliverables and authenticated review of remaining geometry/design obligations.",
        "limitations": "Required design reviews are not authenticated; physical fit, machining, drilling and supplier qualification remain excluded.",
        "evidence": ["tests/external/process_validation/test_geometry.py", "tests/external/process_validation/test_jig_profiles.py"],
    },
}


def _capability(family: str, scenario_id: str, capability_id: str) -> dict:
    if scenario_id in QUALIFIED:
        support = "qualified"
        scope = QUALIFIED[scenario_id]["scope"]
        limitation = QUALIFIED[scenario_id]["limitations"]
        evidence = QUALIFIED[scenario_id]["evidence"]
    elif scenario_id in IMPLEMENTED_PROFILES:
        support = "implemented"
        scope = IMPLEMENTED_PROFILES[scenario_id]["scope"]
        limitation = IMPLEMENTED_PROFILES[scenario_id]["limitations"]
        evidence = IMPLEMENTED_PROFILES[scenario_id]["evidence"]
    elif (family, capability_id) in GENERIC_IMPLEMENTED:
        support = "implemented"
        scope = "Generic bounded structured JSON/CSV/text inspection only."
        limitation = "This pack has no frozen profile or qualified domain semantics, so requests remain blocked."
        evidence = ["packages/workspace_service/tests/test_process_validation.py"]
    else:
        support = "unavailable" if capability_id in UNAVAILABLE else "planned"
        scope = None
        limitation = "No frozen scenario profile and qualified reader currently cover this capability."
        evidence = []
    return {
        "id": capability_id,
        "support": support,
        "scope": scope,
        "limitation": limitation,
        "extension_recipe": capability_id,
        "evidence": evidence,
    }


def build(root: Path) -> dict:
    source = root / "tests/datasets/engineering-workflows/scenarios"
    seeds = (
        root
        / "specs/081-engineering-workflow-templates/content-validation/acceptance-cases.md"
    )
    seed_rows = {}
    for line in seeds.read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.split("|")]
        if len(cells) == 5 and cells[1].endswith(("-01", "-02", "-03")):
            seed_rows[cells[1]] = cells[2:4]
    entries = []
    for manifest_path in sorted(source.glob("*/*/scenario.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        family, case_id = manifest["template_id"], manifest["scenario_id"]
        requirements, defect = seed_rows[case_id]
        sources = []
        for path in sorted(manifest_path.parent.rglob("*")):
            if not path.is_file():
                continue
            if path.is_symlink() or not path.resolve().is_relative_to(source.resolve()):
                raise ValueError(f"Source leaves inventory root: {path}")
            if path.stat().st_size > 16 * 1024 * 1024:
                raise ValueError(f"Source exceeds inventory bound: {path}")
            content = path.read_bytes()
            sources.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "sha256": hashlib.sha256(content).hexdigest(),
                    "size_bytes": len(content),
                }
            )
        qualified = QUALIFIED.get(case_id)
        implemented = IMPLEMENTED_PROFILES.get(case_id)
        baseline_path = (
            root
            / "packages/workspace_service/src/workspace_service/process_validation/baselines"
            / f"{case_id}.json"
        )
        if not baseline_path.is_file():
            raise ValueError(f"Missing frozen baseline: {case_id}")
        entries.append(
            {
                "scenario_id": case_id,
                "family": family,
                "source_requirements_seed": requirements,
                "targeted_defect_seed": defect,
                "requirements_frozen": True,
                "sources": sources,
                "support_status": "qualified"
                if qualified
                else "implemented"
                if implemented
                else "unsupported",
                "profile": qualified or implemented,
                "full_profile": FULL_SCOPE_IMPLEMENTED.get(case_id),
                "capabilities": [
                    _capability(family, case_id, item) for item in CAPABILITIES[family]
                ],
                "initial_slice": case_id in QUALIFIED,
            }
        )
    ids = {entry["scenario_id"] for entry in entries}
    if (
        len(entries) != 30
        or len(ids) != 30
        or set(CAPABILITIES) != {entry["family"] for entry in entries}
    ):
        raise ValueError("Expected 30 unique scenarios in the ten known families")
    return {
        "schema_version": "wright.process-validation-coverage/2",
        "kind": "capability_support_map",
        "scope": "Thirty source packs reconciled against current bounded runtime capabilities. Qualification applies only to the declared profile scope and is not a whole-design or physical verdict.",
        "support_definitions": SUPPORT_DEFINITIONS,
        "qualified_scenarios": sorted(QUALIFIED),
        "extension_recipes": EXTENSION_RECIPES,
        "seed_source": {
            "path": seeds.relative_to(root).as_posix(),
            "sha256": hashlib.sha256(seeds.read_bytes()).hexdigest(),
        },
        "scenarios": entries,
    }


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    target = (
        root
        / "packages/workspace_service/src/workspace_service/process_validation/profiles/coverage.json"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(build(root), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote 30 source inventory entries: {target.relative_to(root)}")
