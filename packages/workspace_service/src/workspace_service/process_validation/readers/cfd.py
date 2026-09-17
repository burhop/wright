"""Bounded readback of archived CFD fields, contracts and comparison evidence."""

from __future__ import annotations

import hashlib
import io
import json
import math
import re
import struct
from zipfile import BadZipFile, ZipFile

from core.process_validation import Measurement, ReaderIdentity, canonical_digest

from .base import ValidationIssue


_MAX_MEMBERS = 256
_MAX_EXPANDED_BYTES = 192 * 1024 * 1024
_FIELD_HEADER = re.compile(rb"FIELD attributes [0-9]+\n")
_TYPE_SIZE = {"float": 4, "double": 8, "int": 4, "unsigned_int": 4}


def _defect(code, message):
    return ValidationIssue(
        code, message, state="fail", category="output_defect", action="revise_output"
    )


def _missing(code, message):
    return ValidationIssue(
        code,
        message,
        state="blocked",
        category="missing_evidence",
        action="supply_input",
    )


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate member")
        result[key] = value
    return result


def _constant(_):
    raise ValueError("nonfinite number")


def _json(content, name):
    try:
        value = json.loads(
            content.decode("utf-8-sig"),
            object_pairs_hook=_pairs,
            parse_constant=_constant,
        )
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise _defect("cfd.invalid_json", f"{name} must be finite unambiguous JSON.") from exc
    if not isinstance(value, dict):
        raise _defect("cfd.invalid_json", f"{name} must be a JSON object.")
    return value


def _archive(content, context):
    try:
        archive = ZipFile(io.BytesIO(content))
        entries = archive.infolist()
        if not entries or len(entries) > _MAX_MEMBERS:
            raise _defect("cfd.archive_entries", "CFD archive member count is unsupported.")
        context.checkpoint(entities=len(entries))
        names = [entry.filename.replace("\\", "/") for entry in entries]
        if len(names) != len(set(names)):
            raise _defect("cfd.archive_duplicates", "CFD archive has duplicate members.")
        total = 0
        for entry, name in zip(entries, names, strict=True):
            total += entry.file_size
            if (
                not name
                or name.startswith("/")
                or re.match(r"^[A-Za-z]:", name)
                or ".." in name.split("/")
                or entry.flag_bits & 0x1
            ):
                raise _defect(
                    "cfd.archive_member", "CFD archive has an unsafe or encrypted member."
                )
        if total > _MAX_EXPANDED_BYTES:
            raise _defect("cfd.archive_size", "Expanded CFD archive exceeds the reader limit.")
        return archive, set(names)
    except ValidationIssue:
        raise
    except (BadZipFile, OSError, RuntimeError) as exc:
        raise _defect("cfd.invalid_archive", "CFD fields must be a valid ZIP archive.") from exc


def _field_values(content, field_name):
    if not content.startswith(b"# vtk DataFile") or b"\nBINARY\n" not in content[:256]:
        raise _defect("cfd.invalid_vtk", "CFD field must be legacy binary VTK.")
    match = _FIELD_HEADER.search(content)
    while match:
        count = int(match.group(0).split()[2])
        position = match.end()
        for _ in range(count):
            line_end = content.find(b"\n", position)
            if line_end < 0:
                raise _defect("cfd.invalid_vtk", "VTK field header is truncated.")
            try:
                name, components, tuples, data_type = content[position:line_end].decode(
                    "ascii"
                ).split()
                components, tuples = int(components), int(tuples)
                size = _TYPE_SIZE[data_type]
            except (UnicodeError, ValueError, KeyError) as exc:
                raise _defect("cfd.invalid_vtk", "VTK field declaration is unsupported.") from exc
            start = line_end + 1
            end = start + components * tuples * size
            if end > len(content):
                raise _defect("cfd.invalid_vtk", "VTK binary field is truncated.")
            if name == field_name:
                if components != 1 or data_type not in {"float", "double"}:
                    raise _defect("cfd.invalid_vtk", "Temperature field has invalid type.")
                code = ">f" if data_type == "float" else ">d"
                values = tuple(item[0] for item in struct.iter_unpack(code, content[start:end]))
                if not values or any(not math.isfinite(item) for item in values):
                    raise _defect("cfd.nonfinite_field", "Temperature field is empty or nonfinite.")
                return values
            position = end + (content[end : end + 1] == b"\n")
        match = _FIELD_HEADER.search(content, position)
    raise _defect("cfd.temperature_missing", "VTK output has no temperature field.")


def _variant(comparison, name):
    variants = comparison.get("variants")
    if not isinstance(variants, list):
        raise _defect("cfd.comparison_variants", "CFD comparison has no variant records.")
    matches = [item for item in variants if isinstance(item, dict) and item.get("variant") == name]
    if len(matches) != 1:
        raise _defect("cfd.comparison_variants", f"CFD comparison must contain one {name} record.")
    return matches[0]


class CfdEvidenceReader:
    identity = ReaderIdentity(
        id="cfd-evidence",
        version="1",
        config_digest=canonical_digest(
            {
                "formats": ["contract-json", "comparison-json", "legacy-binary-vtk-zip"],
                "checks": [
                    "contract-geometry-and-load-binding",
                    "archive-summary-and-field-hashes",
                    "temperature-field-readback",
                    "mass-balance",
                    "convergence-and-heat-balance-evidence",
                ],
                "version": 1,
            }
        ),
        method="independent_measurement",
        tool_identity="wright bounded CFD evidence reader v1",
        formats=("json", "zip"),
    )

    def measure(self, snapshot, check, context):
        operation = check.parameters.get("operation")
        related = {item.subject.role: item for item in context.related_snapshots}
        evidence = [f"subject:{snapshot.subject.id}@{snapshot.subject.sha256}#{check.selector}"]
        unit = None
        if operation == "contract":
            value = _json(snapshot.content, "CFD contract")
            self._contract(value, check.parameters, related, evidence)
            observed = True
        elif operation == "archive_binding":
            comparison = _json(snapshot.content, "CFD comparison")
            archive_snapshot = related.get("field_archive")
            if archive_snapshot is None:
                raise ValidationIssue(
                    "subject.related_role_missing", "Bind the required field_archive output role."
                )
            if comparison.get("field_archive_sha256") != archive_snapshot.subject.sha256:
                raise _defect(
                    "cfd.archive_binding", "Comparison does not bind the exact CFD archive bytes."
                )
            archive, names = _archive(archive_snapshot.content, context)
            observed = self._verify_archive(comparison, archive, names, context)
            archive.close()
            unit = "1"
            evidence.append(
                f"subject:{archive_snapshot.subject.id}@{archive_snapshot.subject.sha256}#fields"
            )
        elif operation == "maximum_temperature":
            archive, names = _archive(snapshot.content, context)
            member = check.parameters.get("member")
            if not isinstance(member, str) or member not in names:
                archive.close()
                raise _defect("cfd.field_missing", "Required CFD temperature field is absent.")
            content = archive.read(member)
            archive.close()
            values = _field_values(content, "T")
            observed = max(values) - 273.15
            unit = "degC"
        elif operation == "mass_balance_relative":
            comparison = _json(snapshot.content, "CFD comparison")
            variant = _variant(comparison, check.parameters.get("variant"))
            boundaries = variant.get("actual_boundaries")
            if not isinstance(boundaries, list) or len(boundaries) < 2:
                raise _missing(
                    "cfd.mass_balance_missing", "Mass-balance evidence needs at least two boundaries."
                )
            try:
                fluxes = [float(item["net_outward_volume_flux_m3_s"]) for item in boundaries]
            except (KeyError, TypeError, ValueError) as exc:
                raise _missing(
                    "cfd.mass_balance_missing", "Boundary volume-flux evidence is incomplete."
                ) from exc
            if any(not math.isfinite(item) for item in fluxes) or sum(map(abs, fluxes)) == 0:
                raise _defect("cfd.mass_balance_invalid", "Boundary fluxes are invalid.")
            observed = abs(sum(fluxes)) / sum(map(abs, fluxes))
            unit = "1"
        elif operation == "convergence":
            comparison = _json(snapshot.content, "CFD comparison")
            variants = [_variant(comparison, name) for name in ("variant-a", "variant-b")]
            if not all(item.get("steady_state_convergence_claimed") is True for item in variants):
                raise _missing(
                    "cfd.convergence_unproven",
                    "Both CFD alternatives need explicit, supported steady-state convergence evidence.",
                )
            observed = True
        elif operation == "heat_balance":
            comparison = _json(snapshot.content, "CFD comparison")
            variants = [_variant(comparison, name) for name in ("variant-a", "variant-b")]
            try:
                balances = [float(item["heat_balance_relative"]) for item in variants]
            except (KeyError, TypeError, ValueError) as exc:
                raise _missing(
                    "cfd.heat_balance_missing",
                    "Both alternatives need field-derived heat-balance evidence.",
                ) from exc
            if any(not math.isfinite(item) or item < 0 for item in balances):
                raise _defect("cfd.heat_balance_invalid", "Heat-balance evidence is invalid.")
            observed = max(balances)
            unit = "1"
        else:
            raise ValidationIssue(
                "profile.cfd_operation",
                "CFD check requests an unsupported operation.",
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
    def _contract(value, parameters, related, evidence):
        expected = parameters.get("expected")
        region_roles = parameters.get("region_roles")
        if not isinstance(expected, dict) or not isinstance(region_roles, dict):
            raise ValidationIssue(
                "profile.cfd_contract", "CFD contract expectations are missing.", category="source_conflict"
            )
        if value.get("ambient_k") != expected.get("ambient_k") or value.get(
            "gravity_m_s2"
        ) != expected.get("gravity_m_s2"):
            raise _defect("cfd.contract_conditions", "CFD ambient or gravity differs from the frozen basis.")
        regions = value.get("regions")
        if not isinstance(regions, list):
            raise _defect("cfd.contract_regions", "CFD contract has no region inventory.")
        by_name = {item.get("name"): item for item in regions if isinstance(item, dict)}
        for name, required in expected.get("regions", {}).items():
            actual = by_name.get(name)
            if not actual:
                raise _defect("cfd.contract_region_missing", f"CFD contract lacks region {name}.")
            material = actual.get("material") if isinstance(actual.get("material"), dict) else {}
            if actual.get("heat_w") != required.get("heat_w") or material.get(
                "kappa"
            ) != required.get("kappa"):
                raise _defect("cfd.contract_region_value", f"CFD region {name} has wrong load/material data.")
        for name, role in region_roles.items():
            actual, bound = by_name.get(name), related.get(role)
            if actual is None or bound is None:
                raise ValidationIssue(
                    "subject.related_role_missing", f"Bind the required related output role '{role}'."
                )
            if actual.get("sha256") != bound.subject.sha256:
                raise _defect("cfd.contract_geometry_binding", f"CFD region {name} is not bound to the exact geometry bytes.")
            evidence.append(f"subject:{bound.subject.id}@{bound.subject.sha256}#cfd-region:{name}")

    @staticmethod
    def _verify_archive(comparison, archive, names, context):
        count = 0
        for variant_name in ("variant-a", "variant-b"):
            variant = _variant(comparison, variant_name)
            summary_name = f"{variant_name}/computed-fields.json"
            log_name = f"{variant_name}/solver.log"
            if summary_name not in names or log_name not in names:
                raise _defect("cfd.archive_missing", "CFD archive lacks a field summary or solver log.")
            summary = _json(archive.read(summary_name), "Archived field summary")
            for key in ("actual_regions", "actual_boundaries", "contract_sha256"):
                if summary.get(key) != variant.get(key):
                    raise _defect("cfd.summary_mismatch", "Archived fields and comparison JSON disagree.")
            records = summary.get("actual_regions", []) + summary.get("actual_boundaries", [])
            for record in records:
                member = f"{variant_name}/{record.get('field', '')}"
                if member not in names:
                    raise _defect("cfd.field_missing", f"CFD archive lacks {member}.")
                digest = hashlib.sha256(archive.read(member)).hexdigest()
                if digest != record.get("sha256"):
                    raise _defect("cfd.field_hash", f"CFD field digest does not match {member}.")
                count += 1
                context.checkpoint(entities=count)
        return count
