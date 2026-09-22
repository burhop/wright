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
    "qualified": "A frozen scenario profile and reader scope passed independent valid, alternate, targeted-defect and boundary controls. Candidate outputs still require a current passing assessment.",
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
            "sha256": "a46d4b244494a2f25b5baa5858f19c665301b5ea4aa0914f74180c80d6ba33fd",
        },
        "baseline_ref": {
            "id": "robot-tracking-diagnosis-01-basis",
            "version": "1",
            "sha256": "2b35e75c35ca1b5f6b77962d422e58f19840597a814125fa945f09e0ad61be91",
        },
        "reader_ids": ["step-bounding-box@1", "structured@1", "tracking-timeline@1"],
        "scope": "Traceable conversion, alignment and non-causal diagnosis followed by independently governed corrective CAD, CalculiX verification and bounded commissioning review.",
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
            "sha256": "10bd909a84e6d2815e752863cf47b684a7a298a4ccc391be0740c8255741c7d5",
        },
        "baseline_ref": {
            "id": "robot-tracking-diagnosis-02-basis",
            "version": "1",
            "sha256": "5dfce036c856742d45304ba7574919b0bd8b1cdad6c46044e9b492f7dbc36ecc",
        },
        "reader_ids": ["step-bounding-box@1", "structured@1", "tracking-timeline@1"],
        "scope": "Traceable conversion, spatial/time alignment and non-causal diagnosis followed by independently governed corrective CAD, CalculiX verification and bounded commissioning review.",
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
            "sha256": "83b48192aa2abd72d94ef18ab23df19671ab9eccefaa936cb14ecbe4118558ec",
        },
        "baseline_ref": {
            "id": "robot-tracking-diagnosis-03-basis",
            "version": "1",
            "sha256": "dbfe7ca5291922c53e8d939311cc8de0f637f78c1c8520a152f48c8ef52b4e7d",
        },
        "reader_ids": ["step-bounding-box@1", "structured@1", "tracking-timeline@1"],
        "scope": "Traceable conversion, missing-sample preservation and non-causal diagnosis followed by independently governed corrective CAD, CalculiX verification and bounded commissioning review.",
        "limitations": "Required human reviews are not yet authenticated; physical operation and causal proof remain excluded.",
        "evidence": [
            "tests/external/process_validation/test_tracking.py",
            "tests/external/process_validation/test_tracking_profiles.py",
        ],
    },
    "heat-spreader-sizing-02": {
        "profile_resource": "heat-spreader-sizing-02-full",
        "profile_ref": {"id": "heat-spreader-sizing-02-full", "version": "1", "sha256": "dec64d294490d091abcdf1052ce8affb8d17c038ea907e584787cd517c93a4e6"},
        "baseline_ref": {"id": "heat-spreader-sizing-02-basis", "version": "1", "sha256": "e8f86603db3713c227be1f311485f150e2cf1fbe4aae35998678429c7822c139"},
        "reader_ids": ["step-bounding-box@1", "structured@1", "thermal-field@1"],
        "scope": "Actual STEP envelopes, exact STEP-to-field identity correspondence, coarse/refined fields, analytical agreement, balance, refinement, outcomes, selection, deliverables and required basis review.",
        "limitations": "Required basis review is not yet authenticated; physical thermal qualification and certification remain excluded.",
        "evidence": ["tests/external/process_validation/test_step_box.py", "tests/external/process_validation/test_heat_profiles.py"],
    },
    "heat-spreader-sizing-03": {
        "profile_resource": "heat-spreader-sizing-03-full",
        "profile_ref": {"id": "heat-spreader-sizing-03-full", "version": "1", "sha256": "c23b8537593e1200d1e0a01361d164cf7aec0db6c29ad56b1387fee277098ba7"},
        "baseline_ref": {"id": "heat-spreader-sizing-03-basis", "version": "1", "sha256": "c30c4e62e2048071105e830ad347b6d5a9341ce6e4d1b94ad31a50651a4949b7"},
        "reader_ids": ["step-bounding-box@1", "structured@1", "thermal-field@1"],
        "scope": "Actual STEP envelopes, exact STEP-to-field identity correspondence, contact-resistance fields, analytical agreement, balance, refinement, outcomes, selection, deliverables and required design review.",
        "limitations": "Required design review is not yet authenticated; physical thermal qualification and certification remain excluded.",
        "evidence": ["tests/external/process_validation/test_step_box.py", "tests/external/process_validation/test_heat_profiles.py"],
    },
}

for _scenario_id, _profile_sha, _baseline_sha in (
    ("sensor-fan-harness-01", "0d25644d3770b289a24e42bcd241836d3808c88f752a435063e1fce58a2c9149", "0a90382e419db11f20b5c8d71a2840fa3cee3f9d726d8d5d191298c7d27f4b1b"),
    ("sensor-fan-harness-02", "18f19982e186926fceb25053736fb33e64d966dee3f76bec5aa5db66562b4638", "e2c7a00f6d0f3e6fcf30f642e1f1912f17de5fe71094fa18ac41cc815111b8d6"),
    ("sensor-fan-harness-03", "1d2479bb3acbd5b09823e0719d54cfefa3c92274dd72f80dac35e39b4bdfafa1", "15ae0bc6732aeab953b73b20b6b56d4f088e985fd7159676145cdb0065d4a3a2"),
):
    IMPLEMENTED_PROFILES[_scenario_id] = {
        "profile_resource": _scenario_id,
        "profile_ref": {"id": _scenario_id + "-full", "version": "2", "sha256": _profile_sha},
        "baseline_ref": {"id": _scenario_id + "-basis", "version": "1", "sha256": _baseline_sha},
        "reader_ids": ["harness@1", "structured@1"],
        "scope": "Source-schedule topology, independently read native KiCad XML/ERC correspondence including named splice terminals, reserve pins, unique cut arithmetic, contact-inclusive voltage drop, deliverables and required engineering reviews.",
        "limitations": "Retained voltage evidence omits total contact/splice drop and required reviews are not yet authenticated; physical production remains excluded.",
        "evidence": ["tests/external/process_validation/test_harness.py", "tests/external/process_validation/test_harness_profiles.py", "packages/workspace_service/tests/test_harness_native_correspondence.py"],
    }

for _scenario_id, _profile_sha, _baseline_sha in (
    ("water-heater-sizing-01", "bb5f22e55ccfe857ff60a612a950d80486a9f2cdbb3514854ef9986fc49b4bbd", "b5f8d63ee4f36b3ee3c32ac9f74fc7a0d769fa21ebc62592232d3494b09016d0"),
    ("water-heater-sizing-02", "45a9591cf084719ec081e3b0f30caa9f4caadfc336d6724bf1d67bba6f32f7c3", "258b0675125c6fe50fb0943110e1d9e50b0eab1b5410718baa8e4492ff64fb51"),
    ("water-heater-sizing-03", "9b5d98220c2e2aafb8a1a43865cca2926e19b8897d0e5253a3e69aebf260c988", "ebe3698bbd89b09479ed3a38c87a9fd4c5a1a136881d32e6be0899b6c33b9af1"),
):
    IMPLEMENTED_PROFILES[_scenario_id] = {
        "profile_resource": _scenario_id,
        "profile_ref": {"id": _scenario_id + "-full", "version": "1", "sha256": _profile_sha},
        "baseline_ref": {"id": _scenario_id + "-basis", "version": "1", "sha256": _baseline_sha},
        "reader_ids": ["step-bounding-box@1", "structured@1", "water-heater-timeline@1"],
        "scope": "Exact Modelica candidate/loss grid and selection plus a hash-bound AgentCAD package, independently recomputed one-dimensional carrier/shell fields and fixed numeric limits, native package envelope, deliverables and required reviews.",
        "limitations": "Retained parameter summaries omit required kit identity/version and required reviews are not authenticated; physical heater qualification remains excluded.",
        "evidence": ["tests/external/process_validation/test_water_heater.py", "tests/external/process_validation/test_water_heater_profiles.py", "packages/workspace_service/tests/test_water_package_numeric_validation.py"],
    }
    IMPLEMENTED_PROFILES[_scenario_id]["profile_ref"]["version"] = "2"

for _scenario_id, _profile_sha, _baseline_sha in (
    ("parametric-drill-jig-02", "95ce88043e9fa2c690d888135e648e921214d7928a5a11bc721a47107a0e2350", "895744b1726ba48ef18b9582151d5cde4402afd0b2378957de3d7c884a67c14e"),
    ("parametric-drill-jig-03", "e135566d247a456f3d3df312ca9fcd5ae9c5e64b367bd7ab32651ea5fb556903", "b6d98dc15c5823c3356a4ecbd13bee82851d1d092b6b80a3b7fd456c3cf7318b"),
):
    IMPLEMENTED_PROFILES[_scenario_id] = {
        "profile_resource": _scenario_id,
        "profile_ref": {"id": _scenario_id + "-full", "version": "1", "sha256": _profile_sha},
        "baseline_ref": {"id": _scenario_id + "-basis", "version": "1", "sha256": _baseline_sha},
        "reader_ids": ["printing@1", "step-seat-geometry@1", "structured@1"],
        "scope": "Actual STEP body/flange seat coordinates and diameters, required DXF/report deliverables and authenticated review of remaining geometry/design obligations.",
        "limitations": "Required design reviews are not authenticated; physical fit, machining, drilling and supplier qualification remain excluded.",
        "evidence": ["tests/external/process_validation/test_geometry.py", "tests/external/process_validation/test_jig_profiles.py"],
    }

for _scenario_id, _profile_sha, _baseline_sha in (
    ("sensor-interface-pcb-01", "7feca0634fbfa9b1e80f7b9f3b100d656c4ae06d67c97e565ee1d0a4c1a6f192", "31b433c19c4ce8d394a7e43bf40ee0dcd893f26a5e72e7a9df7b61a4372fd8f8"),
    ("sensor-interface-pcb-02", "fc53c00f53c6e67b4ec0d896311c769859e29291ffafb09bcb33c4bacd3e10d5", "80c90a52422a8b25fccc23d4b430ce3543b8ebf63b92c989fa1a0591d4aea75d"),
    ("sensor-interface-pcb-03", "fecdbda349e2d1c8ba476cb89bf8db0f7b6ff5cc1584af015797c6b5e017c037", "3073a159f73f58b8661f9aca13e40d8acca067636a0c05529854683c0239159b"),
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

for _scenario_id, _profile_sha, _baseline_sha in (
    ("printed-replacement-part-01", "d9b26a909119befd6746e68b448587187104a9d44b46b11081a7ce233e97bfb4", "26392cf7ca2ad1dcec0edd56f29d466aaac53cfc2a6c2111895d16aa3019854e"),
    ("printed-replacement-part-02", "aa6e94d24ecf62de164767d63f7bbd5db59bfc5de1a90d3f1084496dfee64d59", "770e77fb66a49218b75f92d031efc44ac5f5a48b629e4c135a823d87d894eb52"),
    ("printed-replacement-part-03", "881423783fbb3588df6717f4f2eb9f7d1d30305c8849f2fa6bdfa015399f5ce3", "1886624547ee2afd8c852a7cd057371f623f0cab31023fac91180c2d1a232b40"),
):
    IMPLEMENTED_PROFILES[_scenario_id] = {
        "profile_resource": _scenario_id,
        "profile_ref": {"id": _scenario_id + "-full", "version": "1", "sha256": _profile_sha},
        "baseline_ref": {"id": _scenario_id + "-basis", "version": "1", "sha256": _baseline_sha},
        "reader_ids": ["printing@1", "structured@1"],
        "scope": "Binary-STL envelope and manifold integrity, distinct source/repaired lineage, exact P1S/PETG/process settings, safe 3MF inventory, slice hash lineage, simulator-only transfer binding, deliverables and required engineering review.",
        "limitations": "Detailed mating features, grip geometry, orientation/support decisions, tolerance statements, physical fit/load/print performance and release authorization require authenticated engineering review.",
        "evidence": ["tests/external/process_validation/test_printing.py", "tests/external/process_validation/test_printed_profiles.py"],
    }

for _scenario_id, _profile_sha, _baseline_sha in (
    ("raspberry-pi-enclosure-01", "1840e74a6f5f1235bf8a1cf35eed08fe77d84e7dc149db1945cc5d019ed17924", "5c43d1f40a00764f55c12b4e31b58fdf2f12c5d21e21ec4775be69031f67a07c"),
    ("raspberry-pi-enclosure-02", "8c6ecf39eeb3f893d499dccfcd16741fc99e3883e0eb93a5cd278fe2392e361a", "5947b499daff950b17b32fe8a2fb6c80b2c41e10e05567444ade1aa65a62f979"),
    ("raspberry-pi-enclosure-03", "fca3e7bb12904189c8321901fd58cd033c0527d6394900c19f2adb18115112cd", "6c795f2d61468598868c30f50a680742290649fbcf093de7360e721312397297"),
):
    IMPLEMENTED_PROFILES[_scenario_id] = {
        "profile_resource": _scenario_id,
        "profile_ref": {"id": _scenario_id + "-full", "version": "1", "sha256": _profile_sha},
        "baseline_ref": {"id": _scenario_id + "-basis", "version": "1", "sha256": _baseline_sha},
        "reader_ids": ["cfd-evidence@1", "step-bounding-box@1", "structured@1"],
        "scope": "Actual STEP envelopes and fluid domains, exact geometry/load contract bindings, field-archive/hash correspondence, independent binary-VTK source temperatures, mass balance, convergence/heat-balance evidence and required engineering review.",
        "limitations": "Retained fields lack supported convergence and heat-balance evidence; case 02 variant B also exceeds the frozen height. Manufacturer authority, detailed geometry and physical qualification require authenticated review.",
        "evidence": ["tests/external/process_validation/test_cfd.py", "tests/external/process_validation/test_pi_enclosure_profiles.py"],
    }

for _scenario_id, _profile_sha, _baseline_sha in (
    ("lightweight-equipment-bracket-01", "0c2f24e8d8523a45e7c27bb00755b5cc0a2449dd738a1f7c3dea8856bf033a8f", "7f005f16e9831b90df52e57fbb30a8704f2cc390b2120870b29636a74aa5fbfa"),
    ("lightweight-equipment-bracket-02", "af5bcb43353c44cba7c2f321e6d900bfcfe57aad3473fffca6de1f1fa3afca00", "b3afd5c748c5c2b4f2530dde6606abd4fc0fc7174a6c7f0c8548a97db3e62e9b"),
    ("lightweight-equipment-bracket-03", "a90c518ab4f74166733b3d99a5c541a4464f1d0249fe3bdc6c35cb5c737e90d5", "b0ea52ecc61dd3dfb2d6cb9292e41173c117274e9ecc30c613ca6bb042320ac5"),
):
    IMPLEMENTED_PROFILES[_scenario_id] = {
        "profile_resource": _scenario_id,
        "profile_ref": {"id": _scenario_id + "-full", "version": "1", "sha256": _profile_sha},
        "baseline_ref": {"id": _scenario_id + "-basis", "version": "1", "sha256": _baseline_sha},
        "reader_ids": ["step-bounding-box@1", "structural-evidence@1", "structured@1"],
        "scope": "Exact STEP/request lineage, four recorded solve receipts, full field integrity, displacement, reaction force/moment equilibrium, coarse/fine sensitivity, mass reduction, deliverables and required engineering reviews.",
        "limitations": "Retained campaign attempts lack the required CAD and solver outputs; protected topology, machining feasibility, evaluated stress treatment and physical qualification require authenticated engineering review.",
        "evidence": ["tests/external/process_validation/test_structural.py", "tests/external/process_validation/test_bracket_profiles.py"],
    }

for _scenario_id, _profile_sha, _baseline_sha in (
    ("sheet-metal-supplier-handoff-01", "44ff3131eaa32b44a0a097be3ccecc826bd0c5cc336b701de1fa5d85592c59e9", "2e5196ddb55f07c75639de648520cee58e239789778ed344951175243c61a42d"),
    ("sheet-metal-supplier-handoff-02", "bf2744717cad61c440a6e38a0a4fef3025a586b4268a7074f169f5fa0fb92269", "5b8fd20be00fb9f2d5e41223f45ef9669f2c7e785456c02a249af54c4d6fb53b"),
    ("sheet-metal-supplier-handoff-03", "9c95cb1d67a78922e479c835bc2d5aa9b83c48014ab268535980386ff10db927", "8b3cb122f5d030d1b66f34022100222532b33c8d42f1f9d5bf727b927362080d"),
):
    IMPLEMENTED_PROFILES[_scenario_id] = {
        "profile_resource": _scenario_id,
        "profile_ref": {"id": _scenario_id + "-full", "version": "1", "sha256": _profile_sha},
        "baseline_ref": {"id": _scenario_id + "-basis", "version": "1", "sha256": _baseline_sha},
        "reader_ids": ["sheet-metal-evidence@1", "step-bounding-box@1", "structured@1"],
        "scope": "Exact installed material identity, native inspection evidence, folded STEP presence, millimetre developed-DXF structure, source-bound final artifact manifest, local simulated supplier receipts and required engineering reviews.",
        "limitations": "Retained campaign attempts lack native CAD/export/handoff outputs. Proprietary PSM feature history, bend feasibility, detailed cross-format correspondence, supplier acceptance and physical fabrication require authenticated engineering review.",
        "evidence": ["tests/external/process_validation/test_sheet_metal.py", "tests/external/process_validation/test_sheet_metal_profiles.py"],
    }

FULL_SCOPE_IMPLEMENTED = {
    **IMPLEMENTED_PROFILES,
    "heat-spreader-sizing-01": {
        "profile_resource": "heat-spreader-sizing-01-full",
        "profile_ref": {"id": "heat-spreader-sizing-01-full", "version": "1", "sha256": "da8e16b33bd69313b020c0aabc21ce6e0e6fb21bd465941b92ad224a86756252"},
        "baseline_ref": {"id": "heat-spreader-sizing-01-basis", "version": "1", "sha256": "648762c15d9461eedc7067bc51272e7fcc5e75e1a785efdfaa47efc123dd4e20"},
        "reader_ids": ["step-bounding-box@1", "structured@1", "thermal-field@1"],
        "scope": "Actual STEP envelopes, exact STEP-to-field identity correspondence, coarse/refined fields, analytical agreement, balance, refinement, outcomes, selection, deliverables and required basis review.",
        "limitations": "Required basis review is not yet authenticated; physical thermal qualification and certification remain excluded.",
        "evidence": ["tests/external/process_validation/test_step_box.py", "tests/external/process_validation/test_heat_profiles.py"],
    },
    "parametric-drill-jig-01": {
        "profile_resource": "parametric-drill-jig-01-full",
        "profile_ref": {"id": "parametric-drill-jig-01-full", "version": "1", "sha256": "2563e2ae025694cdb029bad8dc67250107f3772351048de7d78150f656a34bb8"},
        "baseline_ref": {"id": "parametric-drill-jig-01-basis", "version": "1", "sha256": "3c360740760a99eb71b63690b3a6a3bf69814e74d26ea1aa90c84a595c544a67"},
        "reader_ids": ["printing@1", "step-seat-geometry@1", "structured@1"],
        "scope": "Actual STEP body/flange seat coordinates and diameters, required DXF/report deliverables and authenticated review of remaining geometry/design obligations.",
        "limitations": "Required design reviews are not authenticated; physical fit, machining, drilling and supplier qualification remain excluded.",
        "evidence": ["tests/external/process_validation/test_geometry.py", "tests/external/process_validation/test_jig_profiles.py"],
    },
}


# These artifacts are bound into the immutable validation request to preserve
# source/design provenance, even when a profile check consumes their reviewed
# derivative rather than reading each file directly.
CAMPAIGN_AUXILIARY_SUBJECT_ROLES = {
    "raspberry-pi-enclosure-01": {
        "board_a", "board_b", "source_primary_a", "source_primary_b",
    },
    "raspberry-pi-enclosure-02": {
        "board_a", "board_b", "source_primary_a", "source_primary_b",
        "source_secondary_a", "source_secondary_b",
    },
    "raspberry-pi-enclosure-03": {
        "board_a", "board_b", "source_primary_a", "source_primary_b",
        "source_secondary_a", "source_secondary_b",
    },
    "sheet-metal-supplier-handoff-01": {
        "supplier_evidence", "wall_dock_native", "wall_dock_screenshot",
    },
    "sheet-metal-supplier-handoff-02": {
        "cable_trough_native", "cable_trough_screenshot", "supplier_evidence",
    },
    "sheet-metal-supplier-handoff-03": {
        "base_tray_native", "base_tray_screenshot", "removable_lid_native",
        "removable_lid_screenshot", "supplier_evidence",
    },
}


def _campaign_credit(root: Path, scenario_id: str, metadata: dict) -> dict:
    profile_path = (
        root
        / "packages/workspace_service/src/workspace_service/process_validation/profiles"
        / f"{metadata['profile_resource']}.json"
    )
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    if (
        profile.get("id") != metadata["profile_ref"]["id"]
        or profile.get("version") != metadata["profile_ref"]["version"]
        or profile.get("baseline", {}).get("id") != metadata["baseline_ref"]["id"]
        or profile.get("baseline", {}).get("version")
        != metadata["baseline_ref"]["version"]
    ):
        raise ValueError(f"Full-profile metadata differs from packaged profile: {scenario_id}")
    mandatory = {
        row["id"]
        for row in profile["baseline"]["requirements"]
        if row.get("mandatory") is True
    }
    assessed = {
        requirement_id
        for check in profile["checks"]
        for requirement_id in check.get("requirement_ids", [])
    }
    if not mandatory or not mandatory.issubset(assessed):
        raise ValueError(f"Full profile misses mandatory requirements: {scenario_id}")
    subject_roles = {check["subject_role"] for check in profile["checks"]}
    # Some independent correspondence checks consume one primary evidence file
    # and hash-bind additional submitted artifacts. Those related artifacts are
    # part of the immutable validation request and therefore part of campaign
    # credit scope even though they do not each need a duplicate check row.
    for check in profile["checks"]:
        related_roles = (check.get("parameters") or {}).get("related_roles", [])
        if not isinstance(related_roles, list) or any(
            not isinstance(role, str) or not role for role in related_roles
        ):
            raise ValueError(
                f"Invalid related subject roles in packaged profile: {scenario_id}"
            )
        subject_roles.update(related_roles)
    subject_roles.update(CAMPAIGN_AUXILIARY_SUBJECT_ROLES.get(scenario_id, set()))
    if not subject_roles:
        raise ValueError(f"Full profile has no campaign subjects: {scenario_id}")
    return {
        "full_scope": True,
        "requirement_ids": sorted(mandatory),
        "subject_roles": sorted(subject_roles),
    }


def _capability(family: str, scenario_id: str, capability_id: str) -> dict:
    if scenario_id in FULL_SCOPE_IMPLEMENTED:
        support = "qualified"
        scope = FULL_SCOPE_IMPLEMENTED[scenario_id]["scope"]
        limitation = FULL_SCOPE_IMPLEMENTED[scenario_id]["limitations"]
        evidence = FULL_SCOPE_IMPLEMENTED[scenario_id]["evidence"]
    elif scenario_id in QUALIFIED:
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
        full_profile = FULL_SCOPE_IMPLEMENTED.get(case_id)
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
                if full_profile or qualified
                else "implemented"
                if implemented
                else "unsupported",
                "profile": full_profile or qualified or implemented,
                "bounded_profile": qualified,
                "full_profile": full_profile,
                "campaign_credit": _campaign_credit(root, case_id, full_profile)
                if full_profile
                else {"full_scope": False},
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
        "scope": "Thirty source packs reconciled against qualified full-scope digital validation profiles. Qualification applies to the declared validator capability; each candidate still requires current exact output, authenticated review and a passing immutable assessment. Physical claims remain excluded unless explicitly assessed.",
        "support_definitions": SUPPORT_DEFINITIONS,
        "qualified_scenarios": sorted(FULL_SCOPE_IMPLEMENTED),
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
