"""Explicit engineering assertions over adapter readbacks, never AI narration."""

import math


def _finite_number(value):
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _analysis_quantity(step, assertion):
    resource = step.get("engineering_result", {})
    read = step.get("resource_readback", {})
    if (
        resource.get("kind") != "analysis"
        or not read
        or read not in step.get("tool_calls", [])
    ):
        raise ValueError("No final analysis provider inspection was recorded.")
    if read.get("status") != "succeeded" or read.get("tool") != assertion.get("tool"):
        raise ValueError(
            "The analysis inspection tool differs from the reviewed oracle."
        )
    value = read.get("result", {})
    reps = [
        rep
        for rep in resource.get("representations", [])
        if rep.get("kind") in {"cloud_resource", "application_document"}
    ]
    if (
        not reps
        or not value.get("resource_id")
        or value.get("revision") is None
        or not all(
            rep.get("resource_id") == value["resource_id"]
            and rep.get("revision") == value["revision"]
            and rep.get("provider_id") == assertion.get("provider_id")
            for rep in reps
        )
    ):
        raise ValueError(
            "Analysis quantities do not identify the resulting resource and revision."
        )
    path = assertion.get("path")
    if (
        not isinstance(path, list)
        or not 1 <= len(path) <= 12
        or not all(isinstance(key, str) and key for key in path)
    ):
        raise ValueError("Specify the reviewed analysis quantity field path.")
    for key in path:
        if not isinstance(value, dict) or key not in value:
            raise ValueError(
                "The provider did not return the asserted analysis quantity."
            )
        value = value[key]
    expected = assertion.get("expected")
    tolerance = assertion.get("tolerance", 0)
    actual = value.get("value") if isinstance(value, dict) else None
    if not _finite_number(expected) or not _finite_number(tolerance) or tolerance < 0:
        raise ValueError("Use a finite expected quantity and nonnegative tolerance.")
    if (
        not isinstance(value, dict)
        or not assertion.get("unit")
        or value.get("unit") != assertion["unit"]
    ):
        raise ValueError("Analysis quantity unit differs from the asserted unit.")
    if not _finite_number(actual) or abs(actual - expected) > tolerance:
        raise ValueError(
            "Analysis quantity differs from the expected value and tolerance."
        )
    return {
        "check": "analysis_quantity",
        "task_id": step["task_id"],
        "path": path,
        "resource_id": reps[0]["resource_id"],
        "revision": reps[0]["revision"],
        "actual": actual,
        "expected": expected,
        "unit": assertion["unit"],
        "tolerance": tolerance,
        "passed": True,
    }


def attach_oracles(manifest, definitions):
    cases = {case["id"]: case for case in manifest["cases"]}
    for identity, spec in definitions.items():
        if identity not in cases:
            raise ValueError(f"Oracle refers to unknown workflow {identity}.")
        case = cases[identity]
        if spec.get("source_sha256") != case["source_sha256"]:
            raise ValueError(
                f"Review engineering assertions after source changes: {identity}."
            )
        assertions = spec.get("assertions", [])
        if not isinstance(assertions, list) or not 1 <= len(assertions) <= 50:
            raise ValueError("Each oracle needs 1–50 explicit assertions.")
        case["engineering_assertions"] = assertions
    return manifest


def verify_engineering_assertions(result, assertions):
    steps = {step["task_id"]: step for step in result.get("steps", [])}
    checks = []
    for assertion in assertions:
        step = steps.get(assertion.get("task_id"))
        if step is None:
            raise ValueError("The asserted engineering step did not return evidence.")
        kind = assertion.get("kind")
        if kind == "analysis_quantity":
            checks.append(_analysis_quantity(step, assertion))
        elif kind == "cad_variable":
            calls = step.get("tool_calls", [])
            reads = [
                (i, c)
                for i, c in enumerate(calls)
                if c.get("tool", "").endswith("__cad.list_variables")
                and c.get("status") == "succeeded"
            ]
            if not reads:
                raise ValueError("No CAD variable readback was recorded.")
            index, read = reads[-1]
            doc = step.get("cad_document", {})
            if read.get("arguments", {}).get("documentId") != doc.get(
                "documentId"
            ) or not doc.get("documentId"):
                raise ValueError("CAD variable evidence belongs to a different model.")
            geometry_calls = (
                "__cad.set_variable",
                "__cad.rebuild",
                "__cad.create_part_from_recipe",
                "__cad.create_sheet_metal_from_recipe",
            )
            if any(
                c.get("tool", "").endswith(geometry_calls) for c in calls[index + 1 :]
            ):
                raise ValueError(
                    "CAD geometry changed after the last variable readback."
                )
            values = read.get("result", {}).get("result", [])
            values = [
                item["value"]
                for item in values
                if item.get("name") == assertion["name"]
            ]
            if not values:
                raise ValueError(f"CAD variable not found: {assertion['name']}.")
            expected = assertion["expected"]
            tolerance = assertion.get("tolerance", 0)
            if (
                not isinstance(expected, (int, float))
                or not math.isfinite(expected)
                or not isinstance(tolerance, (int, float))
                or not math.isfinite(tolerance)
                or tolerance < 0
            ):
                raise ValueError(
                    "Use a finite expected value and nonnegative tolerance."
                )
            for value in values:
                actual = value.get("decimalValue")
                if value.get("unit") != assertion["unit"]:
                    raise ValueError(
                        "CAD variable unit differs from the asserted unit."
                    )
                if (
                    not isinstance(actual, (int, float))
                    or not math.isfinite(actual)
                    or abs(actual - expected) > tolerance
                ):
                    raise ValueError(
                        f"CAD variable {assertion['name']} differs from {expected} {assertion['unit']}."
                    )
            checks.append(
                {
                    "check": "cad_variable",
                    "task_id": step["task_id"],
                    "name": assertion["name"],
                    "actual": values[0]["decimalValue"],
                    "expected": expected,
                    "unit": assertion["unit"],
                    "tolerance": tolerance,
                    "passed": True,
                }
            )
        elif kind == "resource_revision":
            resource = step.get("engineering_result", {})
            reps = [
                rep
                for rep in resource.get("representations", [])
                if rep.get("kind") in {"cloud_resource", "application_document"}
            ]
            if not reps or any(
                not rep.get("provider_id")
                or not rep.get("resource_id")
                or rep.get("revision") is None
                for rep in reps
            ):
                raise ValueError(
                    "The application did not provide a verifiable resource revision."
                )
            if "expected" in assertion and not any(
                rep["revision"] == assertion["expected"] for rep in reps
            ):
                raise ValueError(
                    "The resulting resource revision differs from the expected revision."
                )
            if assertion.get("changed"):
                before = step.get("input_resource", {}).get("revision")
                if before is None or any(rep["revision"] == before for rep in reps):
                    raise ValueError("A changed resource revision was not verified.")
            checks.append(
                {
                    "check": "resource_revision",
                    "task_id": step["task_id"],
                    "revisions": [rep["revision"] for rep in reps],
                    "passed": True,
                }
            )
        else:
            raise ValueError(f"No engineering oracle registered for {kind}.")
    return checks
