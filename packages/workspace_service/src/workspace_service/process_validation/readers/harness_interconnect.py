"""Bounded native KiCad/WireViz comparison; never trusts a producer pass flag."""
from collections import Counter, defaultdict
import csv
import io
import json
from xml.etree import ElementTree as ET


PIN_COLUMNS = ("wire_id", "cable_id", "conductor", "from_connector", "from_pin",
               "to_connector", "to_pin", "net", "view", "color_requirement")


def _rows(raw, columns, context):
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")), strict=True)
    if tuple(reader.fieldnames or ()) != columns:
        raise ValueError("The released wiring table has an unexpected column layout")
    rows = []
    for count, row in enumerate(reader, 1):
        context.checkpoint(entities=count * len(columns))
        if None in row or any(not value for value in row.values()):
            raise ValueError("The released wiring table has a missing or extra field")
        rows.append(row)
    if not rows:
        raise ValueError("The released wiring table is empty")
    return rows


def _edge(left, right, *identity):
    if left == right:
        raise ValueError("A connection joins a pin to itself")
    return (*sorted((left, right)), *identity)


def _native_xml(raw, context):
    context.checkpoint()
    if not 0 < len(raw) <= min(context.budget.max_bytes, 20 * 1024 * 1024):
        raise ValueError("Native KiCad netlist is empty or oversized")
    decoded = raw.decode("utf-8-sig")
    if "<!DOCTYPE" in decoded.upper() or "<!ENTITY" in decoded.upper():
        raise ValueError("Native netlists cannot contain document types or entities")
    parser = ET.iterparse(io.StringIO(decoded), events=("end",))
    try:
        for count, _ in enumerate(parser, 1):
            context.checkpoint(entities=count)
    except ET.ParseError as exc:
        raise ValueError("The native KiCad XML netlist is malformed") from exc
    root = parser.root
    if root.tag != "export" or any(root.find(key) is None for key in ("components", "libparts", "nets")):
        raise ValueError("The artifact is not a complete native KiCad XML netlist")
    return root


def compare_native(related, parameters, context):
    """Check actual sealed outputs against the profile-frozen physical schedule."""
    native = related["kicad_native_netlist"]
    erc = related["kicad_erc"]
    proof = json.loads(related["kicad_native_inspection"].content)
    if (proof.get("schema") != "wright-native-kicad-interconnect-v1"
            or proof.get("engine") != "kicad-cli"
            or proof.get("status") != "exported_not_design_approval"
            or proof.get("source_sha256") != related["kicad_schematic"].subject.sha256
            or proof.get("netlist_sha256") != native.subject.sha256
            or proof.get("erc_sha256") != erc.subject.sha256):
        raise ValueError("The native inspection does not bind this exact schematic, netlist and ERC")
    report = json.loads(erc.content)
    if report.get("$schema") != "https://schemas.kicad.org/erc.v1.json" or not isinstance(report.get("sheets"), list) or not report["sheets"]:
        raise ValueError("A complete native KiCad ERC report is required")
    issues = []
    for sheet in report["sheets"]:
        if not isinstance(sheet.get("violations"), list):
            raise ValueError("A native ERC sheet is missing its findings")
        issues.extend(sheet["violations"])
        context.checkpoint(entities=len(issues))
    if any(item.get("severity") not in {"error", "warning"} for item in issues):
        raise ValueError("Native ERC has an unrecognized finding severity")
    for severity in ("error", "warning"):
        count = sum(item["severity"] == severity for item in issues)
        if type(proof.get(f"erc_{severity}_count")) is not int or proof[f"erc_{severity}_count"] != count:
            raise ValueError("Native ERC finding counts disagree with the inspection")
        if severity == "error" and count:
            raise ValueError("Native KiCad ERC contains electrical-rule errors")

    expected = parameters["expected_connections"]
    mapping = parameters["native_pin_map"]
    reserved = set(parameters["reserved_endpoints"])
    required_nets = defaultdict(set)
    for row in expected:
        required_nets[row["net"]].update((row["from"], row["to"]))
    connected = set().union(*required_nets.values())
    if not connected or connected & reserved or set(mapping) != connected | reserved or len(set(mapping.values())) != len(mapping):
        raise ValueError("The fixed native pin mapping must cover every connected and reserved pin exactly once")
    expected_components = defaultdict(set)
    for endpoint, native_endpoint in mapping.items():
        reference, pin = endpoint.split(":")
        native_reference, native_pin = native_endpoint.split(":")
        if reference != native_reference or not native_pin.isdigit() or int(native_pin) < 1 or (pin.isdigit() and native_pin != pin):
            raise ValueError("The fixed map must preserve connector references and physical pin numbers")
        expected_components[reference].add(native_pin)

    pins = _rows(related["pin_schedule"].content, PIN_COLUMNS, context)
    schedule = Counter(_edge(f"{r['from_connector']}:{r['from_pin']}", f"{r['to_connector']}:{r['to_pin']}", r["net"]) for r in pins)
    if schedule != Counter(_edge(r["from"], r["to"], r["net"]) for r in expected):
        raise ValueError("The released pin schedule differs from the fixed physical wiring schedule")
    wireviz = _rows(related["netlist"].content, ("from_endpoint", "to_endpoint", "cable", "conductor"), context)
    cables = [(r["cable_id"], r["conductor"]) for r in pins]
    if len(set(cables)) != len(cables):
        raise ValueError("A released cable conductor is assigned more than once")
    if Counter(_edge(r["from_endpoint"], r["to_endpoint"], r["cable"], r["conductor"]) for r in wireviz) != Counter(
            _edge(f"{r['from_connector']}:{r['from_pin']}", f"{r['to_connector']}:{r['to_pin']}", r["cable_id"], r["conductor"]) for r in pins):
        raise ValueError("The actual WireViz netlist differs from the released pin schedule")

    root = _native_xml(native.content, context)
    libraries = {}
    for part in root.find("libparts"):
        key = (part.attrib["lib"], part.attrib["part"])
        numbers = [pin.attrib["num"] for pin in part.findall("pins/pin")]
        if key in libraries or not numbers or len(set(numbers)) != len(numbers):
            raise ValueError("Native KiCad library pin definitions are missing or repeated")
        libraries[key] = set(numbers)
    components = {}
    for part in root.find("components"):
        reference = part.attrib["ref"]
        library = part.find("libsource")
        if reference in components or library is None:
            raise ValueError("Native KiCad component references are repeated or incomplete")
        components[reference] = libraries[(library.attrib["lib"], library.attrib["part"])]
    if components != dict(expected_components):
        raise ValueError("Native KiCad is missing a connector/splice or has the wrong physical pin counts")

    inverse = {value:key for key, value in mapping.items()}
    observed_nets, used_pins, codes = {}, set(), set()
    for net in root.find("nets"):
        code, name = net.attrib["code"], net.attrib["name"].removeprefix("/")
        nodes = [inverse[f"{node.attrib['ref']}:{node.attrib['pin']}"] for node in net.findall("node")]
        if code in codes or not nodes or len(nodes) != len(set(nodes)) or used_pins & set(nodes):
            raise ValueError("Native KiCad repeats a net identifier or assigns a pin more than once")
        codes.add(code)
        used_pins.update(nodes)
        if len(nodes) == 1 and nodes[0] in reserved:
            continue  # Native exports can retain a singleton unconnected reserved pin.
        if name in observed_nets or set(nodes) & reserved:
            raise ValueError("Native KiCad duplicates a net or connects a reserved pin")
        observed_nets[name] = set(nodes)
    if observed_nets != dict(required_nets):
        raise ValueError("Native KiCad pins/nets differ from the approved schedule (missing connection, swapped pin or merged return)")
