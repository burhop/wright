"""Bounded independent inspection of KiCad PCB and fabrication outputs."""

from __future__ import annotations

import csv
import io
import json
import math
import re
import zipfile

from core.process_validation import Measurement, ReaderIdentity, canonical_digest

from .base import ValidationIssue


TOKEN = re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+')


def _defect(code, message):
    return ValidationIssue(
        code, message, state="fail", category="output_defect", action="revise_output"
    )


def _parse(content, context):
    try:
        text = content.decode("utf-8-sig")
    except UnicodeError as exc:
        raise _defect(
            "kicad.invalid_text", "KiCad file is not valid UTF-8 text."
        ) from exc
    tokens = TOKEN.findall(text)
    context.checkpoint(entities=len(tokens))
    stack, roots = [], []
    for token in tokens:
        if token == "(":
            node = []
            (stack[-1] if stack else roots).append(node)
            stack.append(node)
        elif token == ")":
            if not stack:
                raise _defect(
                    "kicad.invalid_syntax", "KiCad file has unmatched parentheses."
                )
            stack.pop()
        else:
            if not stack:
                raise _defect(
                    "kicad.invalid_syntax", "KiCad file has text outside its root."
                )
            if token.startswith('"'):
                token = json.loads(token)
            stack[-1].append(token)
    if stack or len(roots) != 1 or not roots[0]:
        raise _defect(
            "kicad.invalid_syntax", "KiCad file has an invalid root expression."
        )
    return roots[0]


def _children(node, name):
    return [
        item for item in node[1:] if isinstance(item, list) and item and item[0] == name
    ]


def _child(node, name):
    items = _children(node, name)
    return items[0] if items else None


def _number(value, label):
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise _defect(
            "kicad.invalid_number", f"KiCad {label} must be numeric."
        ) from exc
    if not math.isfinite(result):
        raise _defect("kicad.invalid_number", f"KiCad {label} must be finite.")
    return result


def _property(node, name):
    for item in _children(node, "property"):
        if len(item) >= 3 and item[1] == name:
            return item[2]
    return None


def _at(node):
    item = _child(node, "at")
    if item is None or len(item) < 3:
        raise _defect("kicad.missing_position", "KiCad object has no usable position.")
    return (
        _number(item[1], "x"),
        _number(item[2], "y"),
        _number(item[3], "rotation") if len(item) > 3 else 0.0,
    )


def _board(content, context):
    root = _parse(content, context)
    if root[0] != "kicad_pcb":
        raise _defect("kicad.wrong_document", "Expected a native KiCad PCB document.")
    net_names = {
        int(item[1]): item[2] for item in _children(root, "net") if len(item) >= 3
    }
    footprints = {}
    for node in _children(root, "footprint"):
        ref = _property(node, "Reference")
        if not ref or ref in footprints:
            raise _defect(
                "kicad.duplicate_reference", "PCB has a missing or duplicate reference."
            )
        x, y, rotation = _at(node)
        pads = {}
        absolute = []
        # KiCad board angles are clockwise in its screen-coordinate convention.
        angle = math.radians(-rotation)
        for pad in _children(node, "pad"):
            if len(pad) < 2:
                continue
            pin = str(pad[1])
            net = _child(pad, "net")
            if net is not None and len(net) >= 2:
                net_id = int(net[1])
                pads[pin] = net[2] if len(net) >= 3 else net_names.get(net_id, "")
            local_x, local_y, _ = _at(pad)
            absolute.append(
                (
                    x + local_x * math.cos(angle) - local_y * math.sin(angle),
                    y + local_x * math.sin(angle) + local_y * math.cos(angle),
                )
            )
        centroid = (
            (
                sum(point[0] for point in absolute) / len(absolute),
                sum(point[1] for point in absolute) / len(absolute),
            )
            if absolute
            else (x, y)
        )
        footprints[ref] = {
            "name": str(node[1]) if len(node) > 1 else "",
            "value": _property(node, "Value"),
            "at": (x, y, rotation),
            "centroid": centroid,
            "pads": pads,
            "node": node,
        }
    return root, net_names, footprints


def _expected_components(parameters):
    expected = parameters.get("expected_components")
    if not isinstance(expected, dict) or not expected:
        raise ValidationIssue(
            "profile.kicad_components",
            "Expected KiCad components are required.",
            category="source_conflict",
        )
    return expected


class KiCadReader:
    identity = ReaderIdentity(
        id="kicad",
        version="1",
        config_digest=canonical_digest(
            {
                "checks": [
                    "netlist",
                    "components",
                    "placement",
                    "board_geometry",
                    "track_widths",
                    "report",
                    "bom",
                    "fabrication_bundle",
                ],
                "version": 1,
            }
        ),
        method="independent_measurement",
        tool_identity="wright bounded KiCad and fabrication reader v1",
        formats=("kicad_pcb", "csv", "json", "zip"),
    )

    def measure(self, snapshot, check, context):
        operation = check.parameters.get("operation")
        if operation in {
            "netlist",
            "components",
            "placement",
            "board_geometry",
            "track_widths",
        }:
            root, nets, footprints = _board(snapshot.content, context)
            value = getattr(self, "_" + operation)(
                root, nets, footprints, check.parameters
            )
        elif operation == "report":
            value = self._report(snapshot.content, check.parameters, context)
        elif operation == "bom":
            value = self._bom(snapshot.content, check.parameters, context)
        elif operation == "fabrication_bundle":
            value = self._fabrication_bundle(
                snapshot.content, check.parameters, context
            )
        else:
            raise ValidationIssue(
                "profile.kicad_operation",
                "KiCad check requests an unsupported operation.",
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
            unit="1",
            frame=check.frame,
            uncertainty=0.0,
            reader=self.identity,
            evidence_refs=(
                f"subject:{snapshot.subject.id}@{snapshot.subject.sha256}#{operation}",
            ),
        )

    @staticmethod
    def _netlist(_root, _nets, footprints, parameters):
        expected = parameters.get("expected_connections")
        if not isinstance(expected, list) or not expected:
            raise ValidationIssue(
                "profile.kicad_netlist",
                "Expected connections are required.",
                category="source_conflict",
            )
        wanted = {
            (str(row["reference"]), str(row["pin"])): row["net"] for row in expected
        }
        if len(wanted) != len(expected):
            raise ValidationIssue(
                "profile.kicad_netlist",
                "Expected connections repeat a component pin.",
                category="source_conflict",
            )
        actual = {
            (reference, pin): net
            for reference, component in footprints.items()
            if reference in {item[0] for item in wanted}
            for pin, net in component["pads"].items()
        }
        if actual != wanted:
            missing = sorted(set(wanted) - set(actual))
            wrong = sorted(
                key
                for key in wanted.keys() & actual.keys()
                if wanted[key] != actual[key]
            )
            extra = sorted(set(actual) - set(wanted))
            raise _defect(
                "kicad.netlist_mismatch",
                f"PCB pin-to-net mapping differs from the frozen source (missing={missing}, wrong={wrong}, extra={extra}).",
            )
        return len(wanted)

    @staticmethod
    def _components(_root, _nets, footprints, parameters):
        expected = _expected_components(parameters)
        for reference, rule in expected.items():
            actual = footprints.get(reference)
            if actual is None:
                raise _defect(
                    "kicad.component_missing", f"PCB component {reference} is missing."
                )
            if (
                actual["value"] != rule["value"]
                or rule["footprint_contains"] not in actual["name"]
            ):
                raise _defect(
                    "kicad.component_mismatch",
                    f"PCB component {reference} has the wrong value or footprint.",
                )
        return len(expected)

    @staticmethod
    def _placement(_root, _nets, footprints, parameters):
        expected = parameters.get("expected_placements")
        tolerance = float(parameters.get("tolerance_mm", 0.01))
        if not isinstance(expected, dict) or not expected:
            raise ValidationIssue(
                "profile.kicad_placement",
                "Expected placements are required.",
                category="source_conflict",
            )
        for reference, rule in expected.items():
            actual = footprints.get(reference)
            if actual is None:
                raise _defect(
                    "kicad.component_missing", f"PCB component {reference} is missing."
                )
            point = (
                actual["centroid"]
                if rule.get("point") == "pad_centroid"
                else actual["at"][:2]
            )
            target = rule["xy_mm"]
            if math.dist(point, target) > tolerance:
                raise _defect(
                    "kicad.placement_mismatch",
                    f"PCB component {reference} is at {point}, expected {target} mm.",
                )
            if (
                "rotation_deg" in rule
                and abs((actual["at"][2] - rule["rotation_deg"] + 180) % 360 - 180)
                > 0.01
            ):
                raise _defect(
                    "kicad.rotation_mismatch",
                    f"PCB component {reference} has the wrong rotation.",
                )
        return len(expected)

    @staticmethod
    def _board_geometry(root, _nets, footprints, parameters):
        points = []
        for line in _children(root, "gr_line"):
            layer = _child(line, "layer")
            if layer is None or len(layer) < 2 or layer[1] != "Edge.Cuts":
                continue
            for key in ("start", "end"):
                item = _child(line, key)
                if item is not None and len(item) >= 3:
                    points.append(
                        (_number(item[1], key + " x"), _number(item[2], key + " y"))
                    )
        if not points:
            raise _defect(
                "kicad.edge_missing", "PCB has no readable Edge.Cuts outline."
            )
        width = max(x for x, _ in points) - min(x for x, _ in points)
        height = max(y for _, y in points) - min(y for _, y in points)
        expected = parameters["size_mm"]
        tolerance = float(parameters.get("tolerance_mm", 0.01))
        if (
            abs(width - expected[0]) > tolerance
            or abs(height - expected[1]) > tolerance
        ):
            raise _defect(
                "kicad.board_size",
                f"PCB outline is {width:g} by {height:g} mm, expected {expected} mm.",
            )
        for reference, target in parameters.get("holes", {}).items():
            actual = footprints.get(reference)
            if actual is None or math.dist(actual["at"][:2], target) > tolerance:
                raise _defect(
                    "kicad.hole_position",
                    f"Mounting hole {reference} is absent or misplaced.",
                )
        return 1

    @staticmethod
    def _track_widths(root, nets, _footprints, parameters):
        widths = {}
        for segment in _children(root, "segment"):
            width, net = _child(segment, "width"), _child(segment, "net")
            if width is None or net is None or len(width) < 2 or len(net) < 2:
                continue
            name = nets.get(int(net[1]))
            if name:
                widths.setdefault(name, []).append(_number(width[1], "track width"))
        for name, minimum in parameters.get("minimum_by_net_mm", {}).items():
            if not widths.get(name) or min(widths[name]) + 1e-9 < float(minimum):
                raise _defect(
                    "kicad.track_width",
                    f"PCB net {name} has a route narrower than {minimum} mm or is unrouted.",
                )
        return len(parameters.get("minimum_by_net_mm", {}))

    @staticmethod
    def _report(content, parameters, context):
        try:
            document = json.loads(content)
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise _defect(
                "kicad.invalid_report", "KiCad check report is invalid JSON."
            ) from exc
        violations = document.get("violations", [])
        if "sheets" in document:
            violations = [
                item
                for sheet in document["sheets"]
                for item in sheet.get("violations", [])
            ]
        context.checkpoint(entities=len(violations))
        errors = [item for item in violations if item.get("severity") == "error"]
        unconnected = document.get("unconnected_items", [])
        parity = document.get("schematic_parity", [])
        if errors or unconnected or parity:
            raise _defect(
                "kicad.check_errors",
                "KiCad report contains errors, unconnected items, or schematic parity defects.",
            )
        return 0

    @staticmethod
    def _bom(content, parameters, context):
        try:
            rows = list(
                csv.DictReader(io.StringIO(content.decode("utf-8-sig")), strict=True)
            )
        except (UnicodeError, csv.Error) as exc:
            raise _defect(
                "kicad.invalid_bom", "KiCad BOM is not a valid CSV table."
            ) from exc
        context.checkpoint(entities=len(rows) * 5)
        expected = _expected_components(parameters)
        actual = {}
        for row in rows:
            refs = [
                ref.strip() for ref in row.get("Refs", "").split(",") if ref.strip()
            ]
            for ref in refs:
                if ref in actual:
                    raise _defect(
                        "kicad.duplicate_bom", f"BOM repeats reference {ref}."
                    )
                actual[ref] = row
        if set(actual) != set(expected):
            raise _defect(
                "kicad.bom_references",
                "BOM references do not match the frozen component set.",
            )
        for reference, rule in expected.items():
            row = actual[reference]
            if (
                row.get("Value") != rule["value"]
                or rule["footprint_contains"] not in row.get("Footprint", "")
                or row.get("Qty") != "1"
            ):
                raise _defect(
                    "kicad.bom_mismatch",
                    f"BOM row {reference} has the wrong value, footprint, or quantity.",
                )
        return len(expected)

    @staticmethod
    def _fabrication_bundle(content, parameters, context):
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                members = archive.infolist()
                context.checkpoint(entities=len(members))
                if (
                    sum(item.file_size for item in members)
                    > context.budget.memory_limit_mb * 1024 * 1024
                ):
                    raise ValidationIssue(
                        "reader.memory_limit",
                        "Fabrication archive exceeds the reader budget.",
                        category="capability_unavailable",
                        action="restore_capability",
                    )
                names = {item.filename for item in members if not item.is_dir()}
                required = set(parameters.get("required_members", []))
                if not required <= names:
                    raise _defect(
                        "kicad.fabrication_missing",
                        f"Fabrication bundle is missing {sorted(required - names)}.",
                    )
                for name in required:
                    if not archive.read(name):
                        raise _defect(
                            "kicad.fabrication_empty",
                            f"Fabrication member {name} is empty.",
                        )
        except zipfile.BadZipFile as exc:
            raise _defect(
                "kicad.invalid_archive",
                "Fabrication bundle is not a valid ZIP archive.",
            ) from exc
        return len(required)
