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
            "sha256": "0e6216a75e586a9966cd961cceb8068e9563dd0c7263c7a31425078080911da0",
        },
        "baseline_ref": {
            "id": "robot-tracking-diagnosis-01-basis",
            "version": "1",
            "sha256": "a1b6db09fddaaf3f80acfa2914daf3e0850160f9b09693879024425fe9020e26",
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
            "sha256": "6787b9682d664e90fd73bece5dcddf31079f23e69bd88cdadcdfe5881643474e",
        },
        "baseline_ref": {
            "id": "robot-tracking-diagnosis-02-basis",
            "version": "1",
            "sha256": "4caf51cc91a953004bce257b90216e83d50b7836a3b83196fbaf5a0a3842a9b1",
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
            "sha256": "11f5ca4b297e60132c541f55bce8720ee987e61924ed340dbff058eb814375cf",
        },
        "baseline_ref": {
            "id": "robot-tracking-diagnosis-03-basis",
            "version": "1",
            "sha256": "c08adf5cd747d36651e57e565fb5a63b4c989b7f25041321eec44ccbaee257ce",
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
        "profile_ref": {"id": "heat-spreader-sizing-02-full", "version": "1", "sha256": "8c4b48a93163b03936315af2060f47ab154553264ecaeeac2d998db6abc57851"},
        "baseline_ref": {"id": "heat-spreader-sizing-02-basis", "version": "1", "sha256": "e8f86603db3713c227be1f311485f150e2cf1fbe4aae35998678429c7822c139"},
        "reader_ids": ["step-bounding-box@1", "structured@1", "thermal-field@1"],
        "scope": "Actual STEP envelopes, coarse/refined fields, analytical agreement, balance, refinement, outcomes, selection, deliverables and required basis review.",
        "limitations": "Required basis review is not yet authenticated; physical thermal qualification and certification remain excluded.",
        "evidence": ["tests/external/process_validation/test_step_box.py", "tests/external/process_validation/test_heat_profiles.py"],
    },
    "heat-spreader-sizing-03": {
        "profile_resource": "heat-spreader-sizing-03-full",
        "profile_ref": {"id": "heat-spreader-sizing-03-full", "version": "1", "sha256": "99bd9a4b009cee5540eb88d0ea6f2c91dba76857fc1a37b3b44a9f8ed14ee9a5"},
        "baseline_ref": {"id": "heat-spreader-sizing-03-basis", "version": "1", "sha256": "c30c4e62e2048071105e830ad347b6d5a9341ce6e4d1b94ad31a50651a4949b7"},
        "reader_ids": ["step-bounding-box@1", "structured@1", "thermal-field@1"],
        "scope": "Actual STEP envelopes, contact-resistance fields, analytical agreement, balance, refinement, outcomes, selection, deliverables and required design review.",
        "limitations": "Required design review is not yet authenticated; physical thermal qualification and certification remain excluded.",
        "evidence": ["tests/external/process_validation/test_step_box.py", "tests/external/process_validation/test_heat_profiles.py"],
    },
}

for _scenario_id, _profile_sha, _baseline_sha in (
    ("sensor-fan-harness-01", "97a33702f0b514d708acc230b9050b4fe008e26b07cfd971bcce319a3c4fa361", "0a17c7a175b00f57d758068762bc76bf294dfe19028b400bedaf893a24c68eb1"),
    ("sensor-fan-harness-02", "c69a16f21c8186de0c9d5d2ae00f1a2b8ef7e8624584be7e61372874eebbd547", "f2d5bbbddc28104471bd5ee9da4434fe18288e082f3f3ed145c0549cef091c6c"),
    ("sensor-fan-harness-03", "f7ecf7d518f54d2269dd9cdbe550c69601d2c310d80911f3af7a8785ab5bb88e", "fa7d92b76771ed1305ef37510c65b4756a16ae6541291d9bdd67aaeb1eec7d87"),
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
    ("water-heater-sizing-01", "d04f0c7cf7a074ee2f5e26141c6673e2a3304ea8c8cc37b03bad1ecc2857d2c1", "83dc0e6d9877a46c9b0c5ba0c84941ffcfff06fa32eadfab4cccf3248bd8bde5"),
    ("water-heater-sizing-02", "5ef2ef688dd957f0e0294ea36ef5926ab8f948bdb2f9ef6089b1e2f8e0a29f54", "4f3aaa8fac7278c69de7fbca166477a151cfd07869d9c37db493c337c8f99f34"),
    ("water-heater-sizing-03", "df62db9766be2c52fb616f620b3917a2087f31c996570030a3496bf0d66e7d28", "c8303d44b3d63733d64cd03270f3b3cd4f1786edf5b187d824227dd476ca863c"),
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
    ("parametric-drill-jig-02", "fd39181e0c3a7d5262b27b17ff837f4cbd86fab7d67a524f101d9cd259bec754", "01ab65b9f751d126beb09c310e17339bd32fbae19581f86b27313b4e443df4b0"),
    ("parametric-drill-jig-03", "381bdca15a9d7e6345290436d1cb9d92dd7f086c47feed64373faeb528c48052", "6c26d73189485eaba89e07ab551c83afa40fae40fda86b43ec8a36ac891f38cc"),
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
    ("raspberry-pi-enclosure-01", "951d04395fec0385859db2fb4cd5b0fec2d9007fe33dfc1899c5fd98e5582115", "5c43d1f40a00764f55c12b4e31b58fdf2f12c5d21e21ec4775be69031f67a07c"),
    ("raspberry-pi-enclosure-02", "af3a77d442abad177fb6779e4860a02e33f2293d31405aa34941eaf8adeacce4", "5947b499daff950b17b32fe8a2fb6c80b2c41e10e05567444ade1aa65a62f979"),
    ("raspberry-pi-enclosure-03", "80a044eff182a73147caabf57e5b4d56c20ff90c246df1052174e0be5f15ab0e", "6c795f2d61468598868c30f50a680742290649fbcf093de7360e721312397297"),
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
    ("sheet-metal-supplier-handoff-01", "68383082bc607ccbe1c34bd2ac99bce51656620391cda4cedc06eb0c9a3a89d2", "efdfe67c2abba893af484c8412163b863fb39b20aef3d2c5be58b17b6e81643a"),
    ("sheet-metal-supplier-handoff-02", "e7ddabb706322ddc35a14bc84ebd83533f9a2a23d4a1a0a5be52050c009ca991", "ef692463cafec8fee996bcd53ec00d0556b1d9d1e77f745316536f0fa7676818"),
    ("sheet-metal-supplier-handoff-03", "6cd2d25ff58fbc103f6816a0ff78cbba17dcf70c61ffc305aee80aa2168407ba", "0b12b72d01a9e54b720b54d5a35f94f9b014eef2a532e16f307352a24175784f"),
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
        "profile_ref": {"id": "heat-spreader-sizing-01-full", "version": "1", "sha256": "3528aa7740b1ab0b7f0ab98ee02904aa37195e11eb8e600d6123ea1371cce1f5"},
        "baseline_ref": {"id": "heat-spreader-sizing-01-basis", "version": "1", "sha256": "648762c15d9461eedc7067bc51272e7fcc5e75e1a785efdfaa47efc123dd4e20"},
        "reader_ids": ["step-bounding-box@1", "structured@1", "thermal-field@1"],
        "scope": "Actual STEP envelopes, coarse/refined fields, analytical agreement, balance, refinement, outcomes, selection, deliverables and required basis review.",
        "limitations": "Required basis review is not yet authenticated; physical thermal qualification and certification remain excluded.",
        "evidence": ["tests/external/process_validation/test_step_box.py", "tests/external/process_validation/test_heat_profiles.py"],
    },
    "parametric-drill-jig-01": {
        "profile_resource": "parametric-drill-jig-01-full",
        "profile_ref": {"id": "parametric-drill-jig-01-full", "version": "1", "sha256": "0d1cbca11861a0fe8b18f47887568b1420a72b553baf413180c70892d5647724"},
        "baseline_ref": {"id": "parametric-drill-jig-01-basis", "version": "1", "sha256": "71f0fad592432ba092f5f2a170012875417044daeeb6306faa9f93446f21f3a4"},
        "reader_ids": ["step-seat-geometry@1", "structured@1"],
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
