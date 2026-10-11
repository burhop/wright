"""Bounded sheet-metal inspection, flat-pattern and handoff evidence checks."""

from __future__ import annotations

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


def _json(snapshot):
    try:
        value = json.loads(snapshot.content)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise _defect(
            "sheet_metal.invalid_json", "Sheet-metal evidence must be valid JSON."
        ) from exc
    if not isinstance(value, dict):
        raise _defect(
            "sheet_metal.invalid_json", "Sheet-metal evidence must be a JSON object."
        )
    return value


def _related(context):
    return {item.subject.role: item for item in context.related_snapshots}


class SheetMetalEvidenceReader:
    identity = ReaderIdentity(
        id="sheet-metal-evidence",
        version="1",
        config_digest=canonical_digest(
            {
                "formats": "native inspection JSON, ASCII DXF, artifact manifest and test handoff receipt",
                "operations": [
                    "design_check",
                    "dxf_contract",
                    "manifest_binding",
                    "simulated_handoff",
                    "dxf_review_binding",
                ],
                "version": 2,
            }
        ),
        method="independent_measurement",
        tool_identity="wright bounded sheet-metal evidence reader v1",
        formats=("json", "dxf"),
    )

    def measure(self, snapshot, check, context):
        operation = check.parameters.get("operation")
        related = _related(context)
        evidence = [
            f"subject:{snapshot.subject.id}@{snapshot.subject.sha256}#{check.selector}"
        ]
        if operation == "design_check":
            observed = self._design_check(snapshot, check)
        elif operation == "dxf_contract":
            observed = self._dxf_contract(snapshot, context)
        elif operation == "manifest_binding":
            observed = self._manifest_binding(snapshot, check, related, evidence)
        elif operation == "simulated_handoff":
            observed = self._simulated_handoff(snapshot, check, related, evidence)
        elif operation == "dxf_review_binding":
            value = _json(snapshot)
            source = related.get(check.parameters.get("source_role"))
            reviewed = related.get(check.parameters.get("reviewed_role"))
            if source is None or reviewed is None:
                raise ValidationIssue(
                    "subject.related_role_missing",
                    "DXF review requires the source and independently reopened copy.",
                )
            if (
                value.get("schema") != "wright-headless-dxf-review-v1"
                or value.get("status") != "pass"
                or value.get("source_sha256") != source.subject.sha256
                or value.get("reviewed_sha256") != reviewed.subject.sha256
                or value.get("inventories_equal") is not True
                or value.get("differences") not in ([], {})
            ):
                raise _defect(
                    "sheet_metal.dxf_review_mismatch",
                    "Independent DXF reopen evidence does not bind equal source and reviewed flat-pattern content.",
                )
            observed = True
            evidence.extend(
                (
                    f"subject:{source.subject.id}@{source.subject.sha256}#source-dxf",
                    f"subject:{reviewed.subject.id}@{reviewed.subject.sha256}#reviewed-dxf",
                )
            )
        else:
            raise ValidationIssue(
                "profile.sheet_metal_operation",
                "Sheet-metal check requests an unsupported operation.",
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
            unit=check.unit,
            frame=check.frame,
            uncertainty=0.0,
            reader=self.identity,
            evidence_refs=tuple(evidence),
        )

    @staticmethod
    def _design_check(snapshot, check):
        value = _json(snapshot)
        checks = value.get("checks")
        if value.get("verdict") != "pass" or value.get("corrections") != []:
            raise _defect(
                "sheet_metal.native_check_failed",
                "Native inspection did not produce an unqualified pass with no corrections.",
            )
        if not isinstance(checks, list) or not checks:
            raise _defect(
                "sheet_metal.native_check_empty",
                "Native inspection must retain a nonempty criterion table.",
            )
        requirements = []
        for item in checks:
            if not isinstance(item, dict):
                raise _defect(
                    "sheet_metal.native_check_schema",
                    "Native inspection criteria must be objects.",
                )
            requirement = item.get("requirement")
            evidence = item.get("evidence")
            if (
                not isinstance(requirement, str)
                or not requirement.strip()
                or item.get("status") != "pass"
                or item.get("expected") in (None, "")
                or item.get("observed") in (None, "", "unknown", "unavailable")
                or not isinstance(evidence, list)
                or not evidence
                or any(type(index) is not int or index < 1 for index in evidence)
            ):
                raise _defect(
                    "sheet_metal.native_check_schema",
                    "Every native criterion needs expected and observed evidence, pass status and positive tool-call indices.",
                )
            requirements.append(requirement)
        required_ids = check.parameters.get("required_requirement_ids")
        if not isinstance(required_ids, list) or any(
            not isinstance(item, str) for item in required_ids
        ):
            raise ValidationIssue(
                "profile.sheet_metal_requirements",
                "Native inspection check requires source requirement IDs.",
                category="source_conflict",
            )
        missing = [
            requirement_id
            for requirement_id in required_ids
            if not any(requirement_id in requirement for requirement in requirements)
        ]
        if missing:
            raise _defect(
                "sheet_metal.native_check_coverage",
                "Native inspection omits source requirement IDs: " + ", ".join(missing),
            )
        return True

    @staticmethod
    def _dxf_contract(snapshot, context):
        try:
            lines = snapshot.content.decode("utf-8-sig").splitlines()
        except UnicodeError as exc:
            raise _defect(
                "sheet_metal.dxf_encoding", "Developed DXF must be bounded UTF-8 text."
            ) from exc
        if len(lines) % 2 or not lines:
            raise _defect(
                "sheet_metal.dxf_structure",
                "Developed DXF must contain complete group-code pairs.",
            )
        pairs = []
        for index in range(0, len(lines), 2):
            context.checkpoint(entities=index // 2 + 1)
            try:
                code = int(lines[index].strip())
            except ValueError as exc:
                raise _defect(
                    "sheet_metal.dxf_structure", "DXF group codes must be integers."
                ) from exc
            value = lines[index + 1].strip()
            if code in {10, 20, 11, 21, 40, 41, 42}:
                try:
                    numeric = float(value)
                except ValueError as exc:
                    raise _defect(
                        "sheet_metal.dxf_numeric",
                        "DXF geometry contains a nonnumeric coordinate.",
                    ) from exc
                if not math.isfinite(numeric):
                    raise _defect(
                        "sheet_metal.dxf_numeric",
                        "DXF geometry contains a nonfinite coordinate.",
                    )
            pairs.append((code, value))
        if pairs[-1] != (0, "EOF"):
            raise _defect(
                "sheet_metal.dxf_structure", "Developed DXF is missing its EOF marker."
            )
        units = None
        for index, pair in enumerate(pairs[:-1]):
            if pair == (9, "$INSUNITS") and pairs[index + 1][0] == 70:
                units = pairs[index + 1][1]
        if units != "4":
            raise _defect(
                "sheet_metal.dxf_units",
                "Developed DXF must declare millimetres with $INSUNITS=4.",
            )
        in_entities, entity_count = False, 0
        supported = {"LINE", "ARC", "CIRCLE", "LWPOLYLINE", "POLYLINE", "SPLINE"}
        forbidden = {"IMAGE", "INSERT", "3DSOLID", "BODY", "VIEWPORT"}
        for index, pair in enumerate(pairs):
            if (
                pair == (0, "SECTION")
                and index + 1 < len(pairs)
                and pairs[index + 1] == (2, "ENTITIES")
            ):
                in_entities = True
                continue
            if in_entities and pair == (0, "ENDSEC"):
                in_entities = False
                continue
            if in_entities and pair[0] == 0:
                if pair[1] in forbidden:
                    raise _defect(
                        "sheet_metal.dxf_substitute",
                        "DXF contains a non-flat embedded or solid representation.",
                    )
                if pair[1] in supported:
                    entity_count += 1
        if entity_count == 0:
            raise _defect(
                "sheet_metal.dxf_empty",
                "Developed DXF contains no supported flat geometry entities.",
            )
        return entity_count

    @staticmethod
    def _manifest_binding(snapshot, check, related, evidence):
        value = _json(snapshot)
        files = value.get("files")
        if (
            value.get("operation") != "collect_artifact_manifest"
            or value.get("content_validation") != "not_measured"
            or not isinstance(files, list)
            or not files
        ):
            raise _defect(
                "sheet_metal.manifest_contract",
                "Final handoff manifest has an invalid source-bound contract.",
            )
        indexed = {}
        for item in files:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                raise _defect(
                    "sheet_metal.manifest_schema",
                    "Final handoff manifest file entries are invalid.",
                )
            if item["path"] in indexed:
                raise _defect(
                    "sheet_metal.manifest_duplicate",
                    "Final handoff manifest contains duplicate paths.",
                )
            indexed[item["path"]] = item
        expected = check.parameters.get("expected_basenames")
        if not isinstance(expected, dict) or not expected:
            raise ValidationIssue(
                "profile.sheet_metal_manifest",
                "Manifest binding requires role-to-basename mappings.",
                category="source_conflict",
            )
        for role, basename in expected.items():
            bound = related.get(role)
            matches = [
                item
                for path, item in indexed.items()
                if path.replace("\\", "/").endswith("/" + basename) or path == basename
            ]
            if bound is None:
                raise ValidationIssue(
                    "subject.related_role_missing",
                    f"Bind the required related output role '{role}'.",
                )
            if len(matches) != 1:
                raise _defect(
                    "sheet_metal.manifest_inventory",
                    f"Final handoff manifest must contain exactly one '{basename}'.",
                )
            item = matches[0]
            if item.get("sha256") != bound.subject.sha256 or item.get("bytes") != len(
                bound.content
            ):
                raise _defect(
                    "sheet_metal.manifest_mismatch",
                    f"Final handoff manifest does not bind the exact '{basename}' bytes.",
                )
            evidence.append(
                f"subject:{bound.subject.id}@{bound.subject.sha256}#{basename}"
            )
        return len(expected)

    @staticmethod
    def _simulated_handoff(snapshot, check, related, evidence):
        value = _json(snapshot)
        expected_destination = check.parameters.get("destination")
        destination = value.get("destination")
        if (
            value.get("schema_version") != 1
            or value.get("integration_test") is not True
            or value.get("simulated_handoff") is not True
            or value.get("network_dispatch") is not False
            or value.get("action_kind") != check.parameters.get("action_kind")
            or not isinstance(destination, dict)
            or destination.get("kind") != "integration_test"
            or destination.get("id") != expected_destination
            or value.get("dataset_id") != check.parameters.get("scenario_id")
        ):
            raise _defect(
                "sheet_metal.handoff_contract",
                "Supplier handoff is not the exact local integration-test action for this scenario.",
            )
        digests = value.get("artifact_digests")
        if (
            not isinstance(digests, list)
            or not digests
            or any(not isinstance(item, str) for item in digests)
        ):
            raise _defect(
                "sheet_metal.handoff_artifacts",
                "Supplier handoff omits its exact artifact digest list.",
            )
        for role, bound in related.items():
            if bound.subject.sha256 not in digests:
                raise _defect(
                    "sheet_metal.handoff_artifacts",
                    f"Supplier handoff does not bind the exact '{role}' artifact.",
                )
            evidence.append(
                f"subject:{bound.subject.id}@{bound.subject.sha256}#handoff"
            )
        return True
