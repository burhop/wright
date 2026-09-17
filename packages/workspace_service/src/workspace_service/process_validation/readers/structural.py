"""Bounded independent checks over recorded CalculiX structural evidence."""

from __future__ import annotations

import csv
import io
import json
import math

from core.process_validation import Measurement, ReaderIdentity, canonical_digest

from .base import ValidationIssue


def _defect(code: str, message: str) -> ValidationIssue:
    return ValidationIssue(
        code,
        message,
        state="fail",
        category="output_defect",
        action="revise_output",
    )


def _number(value, name: str) -> float:
    if isinstance(value, bool):
        raise _defect("structural.invalid_value", f"Structural {name} must be numeric.")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise _defect("structural.invalid_value", f"Structural {name} must be numeric.") from exc
    if not math.isfinite(result):
        raise _defect("structural.nonfinite", f"Structural {name} must be finite.")
    return result


def _json(snapshot):
    try:
        value = json.loads(snapshot.content)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise _defect("structural.invalid_json", "Structural evidence must be valid JSON.") from exc
    if not isinstance(value, dict):
        raise _defect("structural.invalid_json", "Structural evidence must be a JSON object.")
    return value


def _csv(snapshot, headers):
    try:
        reader = csv.DictReader(io.StringIO(snapshot.content.decode("utf-8-sig")), strict=True)
        if reader.fieldnames != list(headers):
            raise ValueError("columns")
        rows = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError("row")
            rows.append(row)
    except (UnicodeError, csv.Error, ValueError) as exc:
        raise _defect(
            "structural.invalid_csv",
            "Structural field data has an unexpected or inconsistent CSV schema.",
        ) from exc
    if not rows:
        raise _defect("structural.empty_field", "Structural field data is empty.")
    return rows


def _related(context):
    return {item.subject.role: item for item in context.related_snapshots}


def _vector(value, name, length=3):
    if not isinstance(value, list) or len(value) != length:
        raise _defect("structural.invalid_vector", f"Structural {name} must contain {length} values.")
    return tuple(_number(item, name) for item in value)


def _displacements(snapshot):
    rows = _csv(snapshot, ("node_id", "ux_mm", "uy_mm", "uz_mm"))
    seen, magnitudes = set(), []
    for row in rows:
        try:
            node = int(row["node_id"])
        except ValueError as exc:
            raise _defect("structural.invalid_node", "Displacement node IDs must be integers.") from exc
        if node <= 0 or node in seen:
            raise _defect("structural.duplicate_node", "Displacement node IDs must be unique and positive.")
        seen.add(node)
        vector = tuple(_number(row[key], key) for key in ("ux_mm", "uy_mm", "uz_mm"))
        magnitudes.append(math.sqrt(sum(item * item for item in vector)))
    return len(rows), max(magnitudes)


def _stresses(snapshot):
    headers = (
        "element_id",
        "integration_point",
        "sxx_mpa",
        "syy_mpa",
        "szz_mpa",
        "sxy_mpa",
        "sxz_mpa",
        "syz_mpa",
    )
    rows = _csv(snapshot, headers)
    seen, maxima = set(), []
    for row in rows:
        try:
            key = (int(row["element_id"]), int(row["integration_point"]))
        except ValueError as exc:
            raise _defect("structural.invalid_element", "Stress element identities must be integers.") from exc
        if min(key) <= 0 or key in seen:
            raise _defect("structural.duplicate_element", "Stress integration-point identities must be unique and positive.")
        seen.add(key)
        sxx, syy, szz, sxy, sxz, syz = (
            _number(row[name], name) for name in headers[2:]
        )
        von_mises = math.sqrt(
            0.5 * ((sxx - syy) ** 2 + (syy - szz) ** 2 + (szz - sxx) ** 2)
            + 3.0 * (sxy * sxy + sxz * sxz + syz * syz)
        )
        maxima.append(von_mises)
    return len(rows), max(maxima)


class StructuralEvidenceReader:
    identity = ReaderIdentity(
        id="structural-evidence",
        version="1",
        config_digest=canonical_digest(
            {
                "formats": "recorded CalculiX request/receipt/reaction and field CSV",
                "operations": [
                    "request_contract",
                    "receipt_binding",
                    "displacement_maximum",
                    "stress_maximum",
                    "refinement",
                    "reaction_equilibrium",
                    "mass_reduction",
                ],
                "version": 1,
            }
        ),
        method="independent_measurement",
        tool_identity="wright bounded structural evidence reader v1",
        formats=("json", "csv"),
    )

    def measure(self, snapshot, check, context):
        operation = check.parameters.get("operation")
        related = _related(context)
        evidence = [f"subject:{snapshot.subject.id}@{snapshot.subject.sha256}#{check.selector}"]
        unit = check.unit
        if operation == "request_contract":
            observed = self._request_contract(snapshot, check, related, evidence)
        elif operation == "receipt_binding":
            observed = self._receipt_binding(snapshot, check, related, evidence)
        elif operation == "displacement_maximum":
            _, observed = _displacements(snapshot)
        elif operation == "stress_maximum":
            _, observed = _stresses(snapshot)
        elif operation == "refinement":
            observed = self._refinement(snapshot, check, related, evidence)
        elif operation == "reaction_equilibrium":
            observed = self._reaction_equilibrium(snapshot, check)
        elif operation == "mass_reduction":
            observed = self._mass_reduction(snapshot, check, related, evidence)
        else:
            raise ValidationIssue(
                "profile.structural_operation",
                "Structural check requests an unsupported operation.",
                category="source_conflict",
            )
        identity = canonical_digest(
            {
                "subject": snapshot.subject,
                "check": check,
                "reader": self.identity,
                "related": tuple(item.subject for item in context.related_snapshots),
            }
        )
        return Measurement(
            id="m-" + identity,
            subject_id=snapshot.subject.id,
            subject_sha256=snapshot.subject.sha256,
            selector=check.selector,
            value=observed,
            unit=unit,
            frame=check.frame,
            uncertainty=0.0,
            reader=self.identity,
            evidence_refs=tuple(evidence),
        )

    @staticmethod
    def _request_contract(snapshot, check, related, evidence):
        value = _json(snapshot)
        runs = value.get("runs")
        if not isinstance(runs, list) or len(runs) != 4:
            raise _defect("structural.request_inventory", "FEA requests must contain exactly four labeled runs.")
        expected_force = _vector(check.parameters.get("force_n"), "load force")
        expected = {
            (variant, mesh): size
            for variant in ("baseline", "revised")
            for mesh, size in (("coarse", 3.0), ("fine", 2.0))
        }
        seen = set()
        for item in runs:
            if not isinstance(item, dict) or not isinstance(item.get("arguments"), dict):
                raise _defect("structural.request_schema", "Each FEA request needs variant, mesh and arguments.")
            key = (item.get("variant"), item.get("mesh"))
            if key not in expected or key in seen:
                raise _defect("structural.request_inventory", "FEA run labels must be unique baseline/revised coarse/fine pairs.")
            seen.add(key)
            arguments = item["arguments"]
            role = f"{key[0]}_step"
            geometry = related.get(role)
            if geometry is None:
                raise ValidationIssue("subject.related_role_missing", f"Bind the required related output role '{role}'.")
            evidence.append(f"subject:{geometry.subject.id}@{geometry.subject.sha256}#geometry")
            material = arguments.get("material")
            if (
                arguments.get("expected_step_sha256") != geometry.subject.sha256
                or _number(arguments.get("mesh_size_mm"), "mesh size") != expected[key]
                or arguments.get("element_order") != 2
                or not isinstance(material, dict)
                or _number(material.get("e_mpa"), "elastic modulus") != 69000.0
                or _number(material.get("nu"), "Poisson ratio") != 0.33
            ):
                raise _defect("structural.request_contract", "FEA request differs from the frozen geometry, mesh or material contract.")
            loads = arguments.get("loads")
            fixed = arguments.get("fixed")
            selections = arguments.get("selections")
            if (
                not isinstance(loads, list)
                or not loads
                or not isinstance(fixed, list)
                or not fixed
                or not isinstance(selections, list)
                or not selections
                or any(_vector(load.get("force_n"), "applied force") != expected_force for load in loads)
            ):
                raise _defect("structural.load_contract", "FEA request does not preserve the exact distributed load and nonempty selections.")
        return True

    @staticmethod
    def _receipt_binding(snapshot, check, related, evidence):
        value = _json(snapshot)
        geometry_role = check.parameters.get("geometry_role")
        geometry = related.get(geometry_role)
        if geometry is None:
            raise ValidationIssue("subject.related_role_missing", f"Bind the required related output role '{geometry_role}'.")
        if (
            value.get("status") != "completed"
            or value.get("expected_step_sha256") != geometry.subject.sha256
            or value.get("physics_deck_changed") is not False
            or value.get("expansion_kind") != "explicit_separate_native_solve_output_requests_only"
            or not isinstance(value.get("original_run_id"), str)
            or not value["original_run_id"].startswith("r-")
            or int(value.get("nodal_displacement_rows", 0)) <= 0
            or int(value.get("stress_integration_point_rows", 0)) <= 0
        ):
            raise _defect("structural.receipt_contract", "Field expansion receipt does not preserve the completed geometry-bound output-only solve contract.")
        files = value.get("files")
        if not isinstance(files, list):
            raise _defect("structural.receipt_files", "Field expansion receipt omits its file inventory.")
        indexed = {item.get("path"): item for item in files if isinstance(item, dict)}
        expected_paths = check.parameters.get("expected_paths")
        if not isinstance(expected_paths, dict) or not expected_paths:
            raise ValidationIssue("profile.structural_paths", "Receipt binding requires role-to-path mappings.", category="source_conflict")
        for role, path in expected_paths.items():
            bound, item = related.get(role), indexed.get(path)
            if bound is None:
                raise ValidationIssue("subject.related_role_missing", f"Bind the required related output role '{role}'.")
            if (
                not isinstance(item, dict)
                or item.get("sha256") != bound.subject.sha256
                or item.get("bytes") != len(bound.content)
            ):
                raise _defect("structural.receipt_file_mismatch", f"Receipt does not bind the exact '{path}' output.")
            evidence.append(f"subject:{bound.subject.id}@{bound.subject.sha256}#{path}")
        evidence.append(f"subject:{geometry.subject.id}@{geometry.subject.sha256}#geometry")
        return True

    @staticmethod
    def _refinement(snapshot, check, related, evidence):
        coarse_role = check.parameters.get("coarse_role")
        coarse = related.get(coarse_role)
        if coarse is None:
            raise ValidationIssue("subject.related_role_missing", f"Bind the required related output role '{coarse_role}'.")
        kind = check.parameters.get("field")
        parser = _displacements if kind == "displacement" else _stresses if kind == "stress" else None
        if parser is None:
            raise ValidationIssue("profile.structural_field", "Refinement field must be displacement or stress.", category="source_conflict")
        fine_count, fine_max = parser(snapshot)
        coarse_count, coarse_max = parser(coarse)
        if fine_count <= coarse_count:
            raise _defect("structural.refinement_lineage", "Fine field must contain more observations than its bound coarse field.")
        denominator = max(abs(fine_max), 1e-12)
        evidence.append(f"subject:{coarse.subject.id}@{coarse.subject.sha256}#field")
        return abs(fine_max - coarse_max) / denominator

    @staticmethod
    def _reaction_equilibrium(snapshot, check):
        value = _json(snapshot)
        reaction_force = _vector(value.get("reaction_force_n"), "reaction force")
        reaction_moment = _vector(value.get("reaction_moment_about_global_origin_nmm"), "reaction moment")
        applied = _vector(check.parameters.get("force_n"), "applied force")
        centroid = _vector(check.parameters.get("load_centroid_mm"), "load centroid")
        applied_moment = (
            centroid[1] * applied[2] - centroid[2] * applied[1],
            centroid[2] * applied[0] - centroid[0] * applied[2],
            centroid[0] * applied[1] - centroid[1] * applied[0],
        )
        force_scale = max(math.sqrt(sum(item * item for item in applied)), 1e-12)
        moment_scale = max(math.sqrt(sum(item * item for item in applied_moment)), force_scale)
        force_error = math.sqrt(sum((a + b) ** 2 for a, b in zip(reaction_force, applied, strict=True))) / force_scale
        moment_error = math.sqrt(sum((a + b) ** 2 for a, b in zip(reaction_moment, applied_moment, strict=True))) / moment_scale
        return max(force_error, moment_error)

    @staticmethod
    def _mass_reduction(snapshot, check, related, evidence):
        headers = ("variant", "volume_mm3", "mass_g", "step_sha256")
        rows = _csv(snapshot, headers)
        if len(rows) != 2 or {row["variant"] for row in rows} != {"baseline", "revised"}:
            raise _defect("structural.mass_inventory", "Mass comparison must contain exactly baseline and revised rows.")
        values = {}
        density = _number(check.parameters.get("density_kg_m3"), "density")
        for row in rows:
            variant = row["variant"]
            geometry = related.get(f"{variant}_step")
            if geometry is None:
                raise ValidationIssue("subject.related_role_missing", f"Bind the required related output role '{variant}_step'.")
            volume = _number(row["volume_mm3"], "volume")
            mass = _number(row["mass_g"], "mass")
            calculated = volume * density * 1e-6
            if volume <= 0 or mass <= 0 or abs(mass - calculated) > max(1e-6, calculated * 0.001):
                raise _defect("structural.mass_calculation", "Reported mass does not match volume and frozen density.")
            if row["step_sha256"] != geometry.subject.sha256:
                raise _defect("structural.mass_geometry", "Mass comparison does not bind the exact STEP revision.")
            values[variant] = mass
            evidence.append(f"subject:{geometry.subject.id}@{geometry.subject.sha256}#geometry")
        if values["revised"] >= values["baseline"]:
            return 0.0
        return 1.0 - values["revised"] / values["baseline"]
