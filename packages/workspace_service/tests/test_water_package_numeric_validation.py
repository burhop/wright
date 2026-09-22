"""Synthetic field/measurement tests, not native CAD or solver qualification."""

import copy
import hashlib
import json
import math
from dataclasses import replace

import pytest

from core.process_validation import (
    CheckDefinition,
    Constraint,
    ProducerIdentity,
    ResourceBudget,
    SubjectBinding,
)
from workspace_service.process_validation.readers.base import (
    ReaderContext,
    SubjectSnapshot,
    ValidationIssue,
)
from workspace_service.process_validation.readers.water_heater import (
    WaterHeaterTimelineReader,
)


FIXED = {
    "maximum_envelope_mm": [120, 120, 155],
    "maximum_heater_contact_diameter_mm": 70,
    "carrier_thermal_conductivity_w_mk": 167,
    "insulation_thickness_range_mm": [8, 15],
    "insulation_thermal_conductivity_w_mk": 0.04,
    "external_film_coefficient_w_m2k": 12,
    "maximum_carrier_temperature_c": 180,
    "maximum_accessible_shell_temperature_c": 60,
    "maximum_dry_package_mass_kg": 0.75,
}


def snapshot(role, content, fmt):
    subject = SubjectBinding(
        id=role,
        role=role,
        result_id="run:step:" + role,
        producer=ProducerIdentity(
            run_id="run", step_id="step", attempt=1, output_port=role
        ),
        kind="file",
        locator=role + "." + fmt,
        format=fmt,
        encoding="raw-bytes",
        sha256=hashlib.sha256(content).hexdigest(),
    )
    return SubjectSnapshot(subject, content)


def fixture():
    measurements = {
        "step_sha256": hashlib.sha256(b"identity-only STEP fixture").hexdigest(),
        "heater_contact_diameter_mm": 70,
        "carrier_thickness_mm": 5,
        "insulation_thickness_mm": 10,
        "envelope_mm": [112, 112, 140],
        "dry_mass_kg": 0.6,
    }
    carrier = 90 + 700 * 0.92 / (math.pi * 0.07**2 / 4) * 0.005 / 167
    shell = (0.04 / 0.01 * 90 + 12 * 20) / (0.04 / 0.01 + 12)
    field = f"model,x_m,temperature_c\ncarrier,0,90\ncarrier,0.0025,{(90 + carrier) / 2}\ncarrier,0.005,{carrier}\ninsulation,0,90\ninsulation,0.005,{(90 + shell) / 2}\ninsulation,0.01,{shell}\n"
    document = {
        "schema": "wright-water-thermal-package-verification-v1",
        "status": "pass",
        "selected_electrical_power_w": 700,
        "heater_efficiency": 0.92,
        "thermal_power_w": 644,
        "checks": {
            "carrier_temperature": {
                "observed_c": carrier,
                "limit_c": 180,
                "pass": True,
            },
            "accessible_shell_temperature": {
                "observed_c": shell,
                "limit_c": 60,
                "pass": True,
            },
            "envelope": {
                "observed_mm": [112, 112, 140],
                "limit_mm": [120, 120, 155],
                "pass": True,
            },
            "dry_mass": {"observed_kg": 0.6, "limit_kg": 0.75, "pass": True},
        },
    }
    return measurements, field, document


def evaluate(measurements, field, document):
    geometry = snapshot("package_step", b"identity-only STEP fixture", "step")
    measured = snapshot(
        "package_measurements", json.dumps(measurements).encode(), "json"
    )
    thermal = snapshot("package_field", field.encode(), "csv")
    comparison = snapshot(
        "comparison", b"identity-only retained comparison fixture", "csv"
    )
    document = copy.deepcopy(document)
    document.update(
        geometry={
            "sha256": geometry.subject.sha256,
            "measurements_sha256": measured.subject.sha256,
        },
        field={"sha256": thermal.subject.sha256},
        modelica_selection_sha256=comparison.subject.sha256,
    )
    subject = snapshot("package_verification", json.dumps(document).encode(), "json")
    check = CheckDefinition(
        id="package",
        requirement_ids=("REQ",),
        subject_role="package_verification",
        reader="water-heater-timeline",
        selector="package/verified",
        constraint=Constraint(operator="equals", expected=True),
        evidence_method="independent_measurement",
        parameters={
            "operation": "package_verification",
            "selected_power_w": 700,
            "heater_efficiency": 0.92,
            "target_temperature_c": 90,
            "ambient_temperature_c": 20,
            "fixed_requirements": FIXED,
            "geometry_role": "package_step",
            "measurements_role": "package_measurements",
            "field_role": "package_field",
            "comparison_role": "comparison",
        },
    )
    context = replace(
        ReaderContext.create(ResourceBudget(), "synthetic-package"),
        related_snapshots=(geometry, measured, thermal, comparison),
    )
    return WaterHeaterTimelineReader().measure(subject, check, context)


def test_independently_checks_both_fields_and_fixed_numeric_limits():
    assert evaluate(*fixture()).value is True


@pytest.mark.parametrize(
    "defect",
    [
        "mass_above_limit",
        "relaxed_limit",
        "missing_observation",
        "false_observation",
        "negative_mass",
        "nan_mass",
        "short_envelope",
        "oversize_envelope",
        "missing_insulation_field",
        "wrong_temperature_field",
        "wrong_field_thickness",
        "outside_insulation_range",
        "oversize_contact",
        "wrong_efficiency",
        "wrong_heat_input",
        "missing_numeric_report",
        "measurement_geometry_mismatch",
    ],
)
def test_pass_flags_cannot_hide_wrong_or_missing_numbers(defect):
    measurements, field, report = fixture()
    if defect == "mass_above_limit":
        measurements["dry_mass_kg"] = report["checks"]["dry_mass"]["observed_kg"] = 0.76
    elif defect == "relaxed_limit":
        report["checks"]["carrier_temperature"]["limit_c"] = 1000
    elif defect == "missing_observation":
        del report["checks"]["carrier_temperature"]["observed_c"]
    elif defect == "false_observation":
        report["checks"]["carrier_temperature"]["observed_c"] = 91
    elif defect in {"negative_mass", "nan_mass"}:
        measurements["dry_mass_kg"] = (
            -0.1 if defect == "negative_mass" else float("nan")
        )
    elif defect == "short_envelope":
        measurements["envelope_mm"] = [100]
    elif defect == "oversize_envelope":
        measurements["envelope_mm"] = [125, 112, 140]
    elif defect == "missing_insulation_field":
        field = (
            "\n".join(
                line for line in field.splitlines() if not line.startswith("insulation")
            )
            + "\n"
        )
    elif defect == "wrong_temperature_field":
        field = field.replace("carrier,0,90", "carrier,0,89")
    elif defect == "wrong_field_thickness":
        field = field.replace("carrier,0.005,", "carrier,0.006,")
    elif defect == "outside_insulation_range":
        measurements["insulation_thickness_mm"] = 16
    elif defect == "oversize_contact":
        measurements["heater_contact_diameter_mm"] = 71
    elif defect == "wrong_efficiency":
        report["heater_efficiency"] = 0.9
    elif defect == "wrong_heat_input":
        report["thermal_power_w"] = 700
    elif defect == "missing_numeric_report":
        report["checks"] = {name: {"pass": True} for name in report["checks"]}
    else:
        measurements["step_sha256"] = "0" * 64
    with pytest.raises(ValidationIssue):
        evaluate(measurements, field, report)
