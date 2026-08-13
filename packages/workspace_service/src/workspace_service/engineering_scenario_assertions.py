"""Versioned engineering assertion plugin registry."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable, Mapping, Sequence

from core.engineering_scenarios import (
    AssertionCategory,
    AssertionResult,
    AssertionState,
    EngineeringScenarioError,
    NormalizedArtifact,
    convert_unit,
)


Plugin = Callable[
    [Mapping[str, Any], Sequence[NormalizedArtifact]], tuple[bool, Any, str]
]
_CAM_ACTUATION = re.compile(
    r"(?im)^\s*(?:N\d+\s+)?(?:G0?0|G0?1|G0?2|G0?3|G28|G38|M0?3|M0?4|M0?5|M0?6|M0?7|M0?8|M0?9|M30)\b"
)
_CATEGORIES = {
    "numeric": AssertionCategory.NUMERIC,
    "table": AssertionCategory.NUMERIC,
    "geometry": AssertionCategory.GEOMETRY,
    "ecad": AssertionCategory.ECAD,
    "fea": AssertionCategory.CONVERGENCE,
    "cfd": AssertionCategory.CONVERGENCE,
    "data_tree": AssertionCategory.TOPOLOGY,
    "additive": AssertionCategory.ADDITIVE,
    "slicer": AssertionCategory.ADDITIVE,
    "cam": AssertionCategory.CAM_SAFETY,
    "chatter_advisory": AssertionCategory.CAM_SAFETY,
}


def _content(artifact: NormalizedArtifact) -> Mapping[str, Any]:
    if not isinstance(artifact.content, Mapping):
        raise EngineeringScenarioError(
            "artifact_content_invalid", "Assertion requires structured artifact content"
        )
    return artifact.content


def _path(value: Any, path: str) -> Any:
    current = value
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            raise EngineeringScenarioError(
                "assertion_observation_missing", f"Observation path is missing: {path}"
            )
        current = current[part]
    return current


def _finite_number(value: Any) -> Decimal:
    try:
        number = Decimal(str(value))
    except Exception as exc:
        raise EngineeringScenarioError(
            "assertion_value_invalid", "Observed value is not numeric"
        ) from exc
    if not number.is_finite():
        raise EngineeringScenarioError(
            "non_finite_value", "Observed value must be finite"
        )
    return number


def _numeric(
    rule: Mapping[str, Any], artifacts: Sequence[NormalizedArtifact]
) -> tuple[bool, Any, str]:
    artifact = artifacts[0]
    content = _content(artifact)
    path = str(rule.get("path", "value"))
    observed = _path(content, path)
    kind = str(rule.get("kind", "range"))
    if kind == "membership":
        passed = observed in rule.get("values", ())
        return passed, observed, "member" if passed else "not_member"
    source_unit = str(artifact.units.get(path, rule.get("unit", "1")))
    target_unit = str(rule.get("unit", source_unit))
    if kind == "monotonic":
        if not isinstance(observed, Sequence) or isinstance(
            observed, (str, bytes, bytearray)
        ):
            raise EngineeringScenarioError(
                "assertion_value_invalid", "Monotonic rule requires a sequence"
            )
        values = tuple(
            convert_unit(_finite_number(value), source_unit, target_unit)
            for value in observed
        )
        direction = str(rule.get("direction", "nondecreasing"))
        comparisons = {
            "increasing": lambda left, right: left < right,
            "nondecreasing": lambda left, right: left <= right,
            "decreasing": lambda left, right: left > right,
            "nonincreasing": lambda left, right: left >= right,
        }
        try:
            compare = comparisons[direction]
        except KeyError as exc:
            raise EngineeringScenarioError(
                "assertion_rule_unsupported",
                f"Unsupported monotonic direction: {direction}",
            ) from exc
        passed = all(compare(left, right) for left, right in zip(values, values[1:]))
        return (
            passed,
            {"values": [str(value) for value in values], "unit": target_unit},
            "monotonic" if passed else "monotonicity_violated",
        )
    if kind == "relational":
        right_index = int(
            rule.get("right_artifact_index", 1 if len(artifacts) > 1 else 0)
        )
        if right_index < 0 or right_index >= len(artifacts):
            raise EngineeringScenarioError(
                "assertion_artifact_missing", "Relational right artifact is missing"
            )
        right_artifact = artifacts[right_index]
        right_path = str(rule.get("right_path", path))
        right_observed = _path(_content(right_artifact), right_path)
        right_source = str(right_artifact.units.get(right_path, target_unit))
        left_value = convert_unit(_finite_number(observed), source_unit, target_unit)
        right_value = convert_unit(
            _finite_number(right_observed), right_source, target_unit
        )
        operator = str(rule.get("operator", "<="))
        operators = {
            "<": lambda left, right: left < right,
            "<=": lambda left, right: left <= right,
            "==": lambda left, right: left == right,
            ">=": lambda left, right: left >= right,
            ">": lambda left, right: left > right,
        }
        try:
            passed = operators[operator](left_value, right_value)
        except KeyError as exc:
            raise EngineeringScenarioError(
                "assertion_rule_unsupported",
                f"Unsupported relational operator: {operator}",
            ) from exc
        return (
            passed,
            {
                "left": str(left_value),
                "operator": operator,
                "right": str(right_value),
                "unit": target_unit,
            },
            "relation_satisfied" if passed else "relation_violated",
        )
    value = convert_unit(_finite_number(observed), source_unit, target_unit)
    if kind == "range":
        minimum = _finite_number(rule["minimum"]) if "minimum" in rule else None
        maximum = _finite_number(rule["maximum"]) if "maximum" in rule else None
        passed = (minimum is None or value >= minimum) and (
            maximum is None or value <= maximum
        )
        return (
            passed,
            {"value": str(value), "unit": target_unit},
            "within_range" if passed else "range_exceeded",
        )
    if kind == "exact":
        expected = _finite_number(rule["value"])
        passed = value == expected
        return (
            passed,
            {"value": str(value), "unit": target_unit},
            "exact_match" if passed else "exact_mismatch",
        )
    if kind in {"absolute_tolerance", "relative_tolerance"}:
        expected = _finite_number(rule["value"])
        tolerance = _finite_number(rule["tolerance"])
        difference = abs(value - expected)
        limit = tolerance if kind == "absolute_tolerance" else abs(expected) * tolerance
        passed = difference <= limit
        return (
            passed,
            {"value": str(value), "difference": str(difference), "unit": target_unit},
            "within_tolerance" if passed else "tolerance_exceeded",
        )
    raise EngineeringScenarioError(
        "assertion_rule_unsupported", f"Unsupported numeric rule: {kind}"
    )


def _table(
    rule: Mapping[str, Any], artifacts: Sequence[NormalizedArtifact]
) -> tuple[bool, Any, str]:
    content = _content(artifacts[0])
    rows = content.get(str(rule.get("path", "rows")))
    if not isinstance(rows, list) or not all(isinstance(row, Mapping) for row in rows):
        raise EngineeringScenarioError(
            "assertion_value_invalid", "Table rule requires a list of row objects"
        )
    required_columns = tuple(str(value) for value in rule.get("columns", ()))
    columns_present = all(
        all(column in row for column in required_columns) for row in rows
    )
    minimum_rows = int(rule.get("minimum_rows", 0))
    maximum_rows = int(rule.get("maximum_rows", len(rows)))
    finite_columns = tuple(str(value) for value in rule.get("finite_columns", ()))
    finite = True
    try:
        for row in rows:
            for column in finite_columns:
                _finite_number(row[column])
    except (KeyError, EngineeringScenarioError):
        finite = False
    passed = columns_present and minimum_rows <= len(rows) <= maximum_rows and finite
    return (
        passed,
        {
            "row_count": len(rows),
            "required_columns": required_columns,
            "columns_present": columns_present,
            "finite": finite,
        },
        "table_valid" if passed else "table_invalid",
    )


def _geometry(
    rule: Mapping[str, Any], artifacts: Sequence[NormalizedArtifact]
) -> tuple[bool, Any, str]:
    if rule.get("kind") == "mass_properties":
        if len(artifacts) < 2:
            raise EngineeringScenarioError(
                "assertion_artifact_missing",
                "Mass-property relationship requires geometry and mass artifacts",
            )
        geometry, mass_properties = artifacts[:2]
        geometry_content = _content(geometry)
        mass_content = _content(mass_properties)
        volume = convert_unit(
            _finite_number(geometry_content.get("volume")),
            str(geometry.units.get("volume", "")),
            "m3",
        )
        mass = convert_unit(
            _finite_number(mass_content.get("mass")),
            str(mass_properties.units.get("mass", "")),
            "kg",
        )
        if volume <= 0:
            raise EngineeringScenarioError(
                "assertion_value_invalid", "Geometry volume must be positive"
            )
        density = mass / volume
        expected = _finite_number(rule["density"])
        tolerance = _finite_number(rule.get("relative_tolerance", "0"))
        difference = abs(density - expected)
        correlated = geometry.content_digest in mass_properties.upstream_digests
        passed = difference <= abs(expected) * tolerance and correlated
        return (
            passed,
            {
                "mass": str(mass),
                "mass_unit": "kg",
                "volume": str(volume),
                "volume_unit": "m3",
                "density": str(density),
                "density_unit": "kg/m3",
                "input_correlated": correlated,
            },
            "mass_properties_valid" if passed else "mass_properties_invalid",
        )
    content = _content(artifacts[0])
    bounds = content.get("bounds", ())
    finite_bounds = len(bounds) == 6 and all(
        math.isfinite(float(value)) for value in bounds
    )
    ordered_bounds = finite_bounds and all(
        float(bounds[index]) <= float(bounds[index + 1]) for index in (0, 2, 4)
    )
    declared_frame = bool(
        artifacts[0].coordinate_system
        and artifacts[0].coordinate_system.get("length_unit")
        and artifacts[0].units.get("bounds")
        and artifacts[0].units.get("volume")
    )
    passed = (
        int(content.get("vertex_count", 0)) >= 4
        and int(content.get("face_count", 0)) >= 4
        and finite_bounds
        and ordered_bounds
        and declared_frame
        and int(content.get("degenerate_faces", 1)) == 0
        and bool(content.get("manifold", False))
        and float(content.get("volume", 0)) > 0
    )
    return (
        passed,
        {
            "vertex_count": content.get("vertex_count"),
            "face_count": content.get("face_count"),
            "degenerate_faces": content.get("degenerate_faces"),
            "manifold": content.get("manifold"),
            "volume": content.get("volume"),
            "bounds_ordered": ordered_bounds,
            "coordinate_and_units_declared": declared_frame,
        },
        "geometry_valid" if passed else "geometry_invalid",
    )


def _ecad(
    rule: Mapping[str, Any], artifacts: Sequence[NormalizedArtifact]
) -> tuple[bool, Any, str]:
    kind = str(rule.get("kind"))
    board = _content(artifacts[0])
    if kind == "board_valid":
        passed = (
            board.get("root") == "kicad_pcb"
            and board.get("unit") == "mm"
            and float(board.get("thickness", 0)) > 0
            and len(board.get("layers", ())) >= 2
            and len(board.get("nets", ())) >= 1
            and all(float(value) > 0 for value in board.get("dimensions", ()))
            and bool(artifacts[0].coordinate_system)
        )
        return (
            passed,
            {
                key: board.get(key)
                for key in ("root", "unit", "thickness", "layers", "nets", "dimensions")
            },
            "board_valid" if passed else "board_invalid",
        )
    if kind == "minimum_clearance":
        enclosure = _content(artifacts[1]) if len(artifacts) > 1 else {}
        observed = _finite_number(
            enclosure.get("minimum_clearance", board.get("minimum_clearance", 0))
        )
        source = str(artifacts[-1].units.get("minimum_clearance", "mm"))
        target = str(rule.get("unit", "mm"))
        converted = convert_unit(observed, source, target)
        minimum = _finite_number(rule["minimum"])
        passed = converted >= minimum
        coordinate_match = (
            artifacts[0].coordinate_system == artifacts[-1].coordinate_system
        )
        correlated = artifacts[0].content_digest in artifacts[-1].upstream_digests
        if rule.get("require_coordinate_match"):
            passed = passed and coordinate_match
        if len(artifacts) > 1:
            passed = passed and correlated
        return (
            passed,
            {
                "value": str(converted),
                "unit": target,
                "coordinate_match": coordinate_match,
                "input_correlated": correlated,
            },
            "clearance_valid" if passed else "clearance_too_small",
        )
    raise EngineeringScenarioError(
        "assertion_rule_unsupported", f"Unsupported ECAD rule: {kind}"
    )


def _solver(
    rule: Mapping[str, Any], artifacts: Sequence[NormalizedArtifact]
) -> tuple[bool, Any, str]:
    if rule.get("kind") in {"range", "relational"}:
        return _numeric(rule, artifacts)
    content = _content(artifacts[0])
    if rule.get("kind") == "conservation":
        input_value = _finite_number(_path(content, str(rule["input_path"])))
        output_value = _finite_number(_path(content, str(rule["output_path"])))
        tolerance = _finite_number(rule["absolute_tolerance"])
        difference = abs(input_value - output_value)
        passed = difference <= tolerance
        return (
            passed,
            {
                "input": str(input_value),
                "output": str(output_value),
                "difference": str(difference),
            },
            "conservation_satisfied" if passed else "conservation_violated",
        )
    residual = _finite_number(content.get("residual", "Infinity"))
    maximum = _finite_number(
        rule.get("maximum_residual", content.get("residual_limit", "0.001"))
    )
    correlated = content.get("input_digest") in artifacts[0].upstream_digests
    passed = (
        bool(content.get("completed"))
        and bool(content.get("converged"))
        and residual <= maximum
        and correlated
    )
    return (
        passed,
        {
            "completed": content.get("completed"),
            "converged": content.get("converged"),
            "residual": str(residual),
            "input_correlated": correlated,
        },
        "solver_converged" if passed else "solver_not_converged",
    )


def _data_tree(
    rule: Mapping[str, Any], artifacts: Sequence[NormalizedArtifact]
) -> tuple[bool, Any, str]:
    content = _content(artifacts[0])
    branches = content.get("branches", ())
    observed_paths = [
        str(branch.get("path")) for branch in branches if isinstance(branch, Mapping)
    ]
    expected_paths = [str(value) for value in rule.get("paths", ())]
    typed = all(
        isinstance(branch, Mapping)
        and isinstance(branch.get("items"), list)
        and all(
            isinstance(item, Mapping) and "type" in item and "value" in item
            for item in branch["items"]
        )
        for branch in branches
    )
    passed = observed_paths == expected_paths and typed
    return (
        passed,
        {"paths": observed_paths, "typed": typed},
        "tree_topology_valid" if passed else "tree_topology_mismatch",
    )


def _additive(
    rule: Mapping[str, Any], artifacts: Sequence[NormalizedArtifact]
) -> tuple[bool, Any, str]:
    content = _content(artifacts[0])
    passed = (
        content.get("package_type") == "3mf"
        and content.get("unit")
        in {"micron", "millimeter", "centimeter", "inch", "foot", "meter"}
        and int(content.get("mesh_count", 0)) >= 1
        and int(content.get("build_item_count", 0)) >= 1
        and int(content.get("invalid_triangle_count", 1)) == 0
        and bool(content.get("relationships_valid", False))
    )
    return (
        passed,
        {
            key: content.get(key)
            for key in (
                "package_type",
                "unit",
                "mesh_count",
                "build_item_count",
                "invalid_triangle_count",
                "relationships_valid",
            )
        },
        "package_valid" if passed else "package_invalid",
    )


def _cam(
    rule: Mapping[str, Any], artifacts: Sequence[NormalizedArtifact]
) -> tuple[bool, Any, str]:
    content = _content(artifacts[0])
    program = str(content.get("program", ""))
    dialect = str(content.get("dialect", ""))
    unit_mode = str(content.get("unit_mode", ""))
    forbidden = sorted(
        set(match.group(0).strip() for match in _CAM_ACTUATION.finditer(program))
    )
    passed = (
        dialect == "rs274ngc-static"
        and unit_mode in {"mm", "inch"}
        and bool(content.get("static_only"))
        and bool(program.strip())
        and not forbidden
    )
    return (
        passed,
        {"dialect": dialect, "unit_mode": unit_mode, "forbidden_commands": forbidden},
        "cam_static_safe" if passed else "cam_actuation_forbidden",
    )


def _chatter_advisory(
    rule: Mapping[str, Any], artifacts: Sequence[NormalizedArtifact]
) -> tuple[bool, Any, str]:
    del rule
    contents = {artifact.kind: _content(artifact) for artifact in artifacts}
    candidates = contents.get("candidate-batch")
    results = contents.get("model-result-batch")
    report = contents.get("chatter-advisory-report")
    if candidates is None or results is None or report is None:
        raise EngineeringScenarioError(
            "chatter_advisory_artifact_missing",
            "Candidate, model-result, and advisory artifacts are required",
        )
    candidate_ids = [str(item["candidate_id"]) for item in candidates["candidates"]]
    result_ids = [str(item["candidate_id"]) for item in results["results"]]
    outcomes = list(report["candidate_outcomes"])
    outcome_ids = [str(item.get("candidate_id", "")) for item in outcomes]
    selected = str(report["selected_candidate_id"])
    selected_rows = [
        item
        for item in outcomes
        if item.get("candidate_id") == selected
        and item.get("review_status") == "selected_for_review"
    ]
    invariant_failures = [
        item["candidate_id"]
        for item in candidates["candidates"]
        if any(value["state"] != "pass" for value in item["engineering_invariants"])
    ]
    passed = bool(
        candidate_ids == result_ids == outcome_ids
        and selected in candidate_ids
        and len(selected_rows) == 1
        and selected not in invariant_failures
        and report["simulation_only"] is True
        and report["machine_authority"] is False
        and report["score_semantics"] == "uncalibrated_screening_score"
    )
    return (
        passed,
        {
            "candidate_ids": candidate_ids,
            "selected_candidate_id": selected,
            "invariant_failures": invariant_failures,
            "simulation_only": report["simulation_only"],
            "machine_authority": report["machine_authority"],
        },
        "chatter_advisory_valid" if passed else "chatter_advisory_invalid",
    )


@dataclass(frozen=True, slots=True)
class _RegisteredPlugin:
    name: str
    version: str
    function: Plugin


class EngineeringAssertionRegistry:
    def __init__(self) -> None:
        self._plugins: dict[tuple[str, str], _RegisteredPlugin] = {}
        for name, function in {
            "numeric": _numeric,
            "table": _table,
            "geometry": _geometry,
            "ecad": _ecad,
            "fea": _solver,
            "cfd": _solver,
            "data_tree": _data_tree,
            "additive": _additive,
            "slicer": _numeric,
            "cam": _cam,
            "chatter_advisory": _chatter_advisory,
        }.items():
            self.register(name, "1.0", function)

    def register(self, name: str, version: str, function: Plugin) -> None:
        key = (name, version)
        if key in self._plugins:
            raise EngineeringScenarioError(
                "scenario_plugin_conflict",
                f"Assertion plugin already exists: {name}@{version}",
            )
        self._plugins[key] = _RegisteredPlugin(name, version, function)

    def evaluate(
        self,
        definition: Mapping[str, Any],
        artifacts: Mapping[str, NormalizedArtifact],
    ) -> AssertionResult:
        name = str(definition.get("plugin", ""))
        version = str(definition.get("plugin_version", ""))
        try:
            plugin = self._plugins[(name, version)]
        except KeyError as exc:
            raise EngineeringScenarioError(
                "scenario_plugin_unsupported",
                f"Unsupported assertion plugin: {name}@{version}",
            ) from exc
        artifact_ids = tuple(str(value) for value in definition.get("artifact_ids", ()))
        try:
            selected = tuple(artifacts[value] for value in artifact_ids)
        except KeyError as exc:
            raise EngineeringScenarioError(
                "assertion_artifact_missing",
                f"Assertion artifact is missing: {exc.args[0]}",
            ) from exc
        if not selected:
            raise EngineeringScenarioError(
                "assertion_artifact_missing", "Assertion has no artifacts"
            )
        try:
            passed, observed, reason = plugin.function(
                definition.get("rule", {}), selected
            )
            state = AssertionState.PASS if passed else AssertionState.FAIL
            message = (
                None if passed else f"{definition['assertion_id']} violated {reason}"
            )
            recovery = (
                None
                if passed
                else str(
                    definition.get(
                        "guidance", "Inspect the producing node and artifact."
                    )
                )
            )
        except EngineeringScenarioError as error:
            passed = False
            observed = {"error": str(error)}
            reason = error.code
            state = AssertionState.ERROR
            message = str(error)
            recovery = str(
                definition.get("guidance", "Inspect the producing node and artifact.")
            )
        producer = selected[0].producer
        return AssertionResult(
            assertion_id=str(definition["assertion_id"]),
            plugin=name,
            plugin_version=version,
            state=state,
            category=_CATEGORIES.get(name, AssertionCategory.INTERNAL),
            reason_code=reason,
            expected=dict(definition.get("rule", {})),
            observed=observed,
            units={"declared": dict(selected[0].units)},
            artifact_digests=tuple(value.content_digest for value in selected),
            producer={
                "node_id": producer.node_id,
                "capability": producer.capability,
                "call_id": producer.call_id,
            },
            message=message,
            recovery=recovery,
        )

    def evaluate_manifest(
        self,
        definitions: Sequence[Mapping[str, Any]],
        artifacts: Mapping[str, NormalizedArtifact],
    ) -> tuple[AssertionResult, ...]:
        return tuple(self.evaluate(definition, artifacts) for definition in definitions)
