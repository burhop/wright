"""Independent bounded checks for harness topology, cut lists and voltage drop."""

from __future__ import annotations

import csv
import io
import json
import math

from core.process_validation import Measurement, ReaderIdentity, canonical_digest

from .base import ValidationIssue


def _defect(code, message):
    return ValidationIssue(
        code, message, state="fail", category="output_defect", action="revise_output"
    )


def _csv(snapshot, columns, context):
    try:
        rows = csv.DictReader(
            io.StringIO(snapshot.content.decode("utf-8-sig")), strict=True
        )
        if tuple(rows.fieldnames or ()) != tuple(columns):
            raise ValueError("columns")
        result = []
        for count, row in enumerate(rows, start=1):
            context.checkpoint(entities=count * len(columns))
            if None in row or any(
                value is None or value == "" for value in row.values()
            ):
                raise ValueError("row")
            result.append(row)
        return result
    except (UnicodeError, csv.Error, ValueError) as exc:
        raise _defect(
            "harness.invalid_table", "Harness table has an invalid schema or row."
        ) from exc


def _number(value, name):
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise _defect(
            "harness.invalid_number", f"Harness {name} must be numeric."
        ) from exc
    if not math.isfinite(number):
        raise _defect("harness.invalid_number", f"Harness {name} must be finite.")
    return number


class HarnessReader:
    identity = ReaderIdentity(
        id="harness",
        version="1",
        config_digest=canonical_digest(
            {
                "checks": ["topology", "reserve", "cut-length", "voltage-drop", "kicad-correspondence"],
                "version": 2,
            }
        ),
        method="independent_measurement",
        tool_identity="wright bounded harness reader v1",
        formats=("csv", "json"),
    )

    def measure(self, snapshot, check, context):
        operation = check.parameters.get("operation")
        if operation in {"topology", "reserve_unconnected"}:
            value = self._topology(snapshot, check, context, operation)
            unit = "1"
        elif operation == "cut_lengths":
            rows = _csv(
                snapshot,
                (
                    "cable_id",
                    "mpn",
                    "conductors",
                    "installed_route_mm",
                    "cut_mm",
                    "service_plus_strip_mm",
                    "quantity",
                    "note",
                ),
                context,
            )
            identifiers = [row["cable_id"] for row in rows]
            if len(identifiers) != len(set(identifiers)):
                raise _defect(
                    "harness.duplicate_cut", "Cut list repeats a physical cable."
                )
            for row in rows:
                installed = _number(row["installed_route_mm"], "installed route")
                cut = _number(row["cut_mm"], "cut length")
                allowance = _number(row["service_plus_strip_mm"], "service allowance")
                if abs(cut - installed - allowance) > 1e-6 or int(row["quantity"]) != 1:
                    raise _defect(
                        "harness.cut_length_mismatch",
                        "Each unique cut must equal its installed route plus documented allowance.",
                    )
            value, unit = len(rows), "1"
        elif operation == "voltage_drop":
            try:
                document = json.loads(snapshot.content)
                branches = document["branches"]
            except (UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
                raise _defect(
                    "harness.invalid_drop", "Voltage-drop evidence is invalid JSON."
                ) from exc
            if not isinstance(branches, list) or not branches:
                raise _defect(
                    "harness.invalid_drop", "Voltage-drop evidence has no branches."
                )
            maximum = 0.0
            for branch in branches:
                total = _number(branch.get("total_drop_v"), "total voltage drop")
                limit = _number(branch.get("limit_v"), "voltage-drop limit")
                if total > limit + 1e-12:
                    raise _defect(
                        "harness.drop_exceeded",
                        "A loaded branch exceeds its voltage-drop limit.",
                    )
                maximum = max(maximum, total)
            value, unit = maximum, "V"
        elif operation == "kicad_correspondence":
            try:
                document = json.loads(snapshot.content)
                related = {
                    item.subject.role: item for item in context.related_snapshots
                }
                expected = {
                    "schematic_sha256": related["kicad_schematic"].subject.sha256,
                    "pin_schedule_sha256": related["pin_schedule"].subject.sha256,
                    "netlist_sha256": related["netlist"].subject.sha256,
                    "erc_sha256": related["kicad_erc"].subject.sha256,
                }
                if (
                    document.get("schema")
                    != "wright-harness-kicad-correspondence-v1"
                    or document.get("status") != "pass"
                    or any(document.get(key) != digest for key, digest in expected.items())
                    or any(
                        document.get(key) != []
                        for key in ("missing_rows", "extra_rows", "mismatched_rows")
                    )
                    or int(document.get("erc_error_count", -1)) != 0
                ):
                    raise ValueError("correspondence")
            except (UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                raise _defect(
                    "harness.kicad_correspondence",
                    "KiCad schematic, source tables, ERC and exact pin/net correspondence do not agree.",
                ) from exc
            value, unit = True, None
        else:
            raise ValidationIssue(
                "profile.harness_operation",
                "Harness check requests an unsupported operation.",
                category="source_conflict",
            )
        identity = canonical_digest(
            {"subject": snapshot.subject, "check": check, "reader": self.identity}
        )
        return Measurement(
            id="m-" + identity,
            subject_id=snapshot.subject.id,
            subject_sha256=snapshot.subject.sha256,
            selector=check.selector,
            value=value,
            unit=unit,
            frame=check.frame,
            uncertainty=0.0,
            reader=self.identity,
            evidence_refs=(
                f"subject:{snapshot.subject.id}@{snapshot.subject.sha256}#{operation}",
            ),
        )

    @staticmethod
    def _topology(snapshot, check, context, operation):
        rows = _csv(
            snapshot, ("from_endpoint", "to_endpoint", "cable", "conductor"), context
        )
        graph = {}
        for row in rows:
            left, right = row["from_endpoint"], row["to_endpoint"]
            graph.setdefault(left, set()).add(right)
            graph.setdefault(right, set()).add(left)

        def component(start):
            found, pending = set(), [start]
            while pending:
                node = pending.pop()
                if node in found:
                    continue
                found.add(node)
                pending.extend(graph.get(node, ()))
            return found

        if operation == "reserve_unconnected":
            reserved = check.parameters.get("reserved_endpoints", [])
            if not isinstance(reserved, list) or not reserved:
                raise ValidationIssue(
                    "profile.harness_reserve",
                    "Reserved endpoints are required.",
                    category="source_conflict",
                )
            if any(endpoint in graph for endpoint in reserved):
                raise _defect(
                    "harness.reserve_connected",
                    "A reserved pin is connected in the output netlist.",
                )
            return len(reserved)

        expected = check.parameters.get("expected_connections")
        if not isinstance(expected, list) or not expected:
            raise ValidationIssue(
                "profile.harness_topology",
                "Expected source connections are required.",
                category="source_conflict",
            )
        endpoints_by_net = {}
        for item in expected:
            left, right, net = item["from"], item["to"], item["net"]
            if right not in component(left):
                raise _defect(
                    "harness.connection_missing",
                    f"Required {net} connection is absent.",
                )
            endpoints_by_net.setdefault(net, set()).update((left, right))
        nets = sorted(endpoints_by_net)
        for index, net in enumerate(nets):
            reachable = component(next(iter(endpoints_by_net[net])))
            if any(reachable & endpoints_by_net[other] for other in nets[index + 1 :]):
                raise _defect(
                    "harness.net_short",
                    "Distinct declared nets are connected together.",
                )
        return len(expected)
