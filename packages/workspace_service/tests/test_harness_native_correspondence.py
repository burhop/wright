"""Synthetic reader tests; these are not native KiCad qualification evidence."""
import copy
import hashlib
import json
import importlib.util
from dataclasses import replace
from pathlib import Path
from threading import Event
from time import monotonic
from xml.etree import ElementTree as ET

import pytest

from core.process_validation import CheckDefinition, Constraint, ProducerIdentity, ResourceBudget, SubjectBinding
from workspace_service.process_validation.readers.base import ReaderContext, SubjectSnapshot, ValidationIssue
from workspace_service.process_validation.readers.harness import HarnessReader
from workspace_service.process_validation.readers.harness_interconnect import _native_xml


CONNECTIONS = [
    {"from": "J0:1", "to": "B1:POWER", "net": "24V"},
    {"from": "B1:POWER", "to": "JF:1", "net": "24V"},
    {"from": "J0:2", "to": "JF:2", "net": "RETURN"},
]
PIN_MAP = {"J0:1": "J0:1", "J0:2": "J0:2", "JF:1": "JF:1", "JF:2": "JF:2", "JF:3": "JF:3", "B1:POWER": "B1:1"}
PIN_COLUMNS = "wire_id,cable_id,conductor,from_connector,from_pin,to_connector,to_pin,net,view,color_requirement"


def snapshot(role, content, fmt):
    subject = SubjectBinding(id=role, role=role, result_id="run:step:" + role,
        producer=ProducerIdentity(run_id="run", step_id="step", attempt=1, output_port=role),
        kind="file", locator=role + "." + fmt, format=fmt, encoding="raw-bytes",
        sha256=hashlib.sha256(content).hexdigest())
    return SubjectSnapshot(subject, content)


def fixture():
    root = ET.Element("export", version="E")
    parts, libraries, nets = (ET.SubElement(root, key) for key in ("components", "libparts", "nets"))
    for reference, count in (("J0", 2), ("JF", 3), ("B1", 1)):
        component = ET.SubElement(parts, "comp", ref=reference)
        ET.SubElement(component, "libsource", lib="Test", part=reference)
        library = ET.SubElement(libraries, "libpart", lib="Test", part=reference)
        pins = ET.SubElement(library, "pins")
        for number in range(1, count + 1):
            ET.SubElement(pins, "pin", num=str(number))
    for code, name, endpoints in (("1", "/24V", ["J0:1", "JF:1", "B1:1"]), ("2", "/RETURN", ["J0:2", "JF:2"]), ("3", "unconnected", ["JF:3"])):
        net = ET.SubElement(nets, "net", code=code, name=name)
        for endpoint in endpoints:
            reference, pin = endpoint.split(":")
            ET.SubElement(net, "node", ref=reference, pin=pin)
    pins = PIN_COLUMNS + "\n"
    wireviz = "from_endpoint,to_endpoint,cable,conductor\n"
    for index, row in enumerate(CONNECTIONS, 1):
        pins += f"W{index},W{index},1,{row['from'].replace(':',',')},{row['to'].replace(':',',')},{row['net']},mating face,red\n"
        wireviz += f"{row['from']},{row['to']},W{index},1\n"
    erc = {"$schema":"https://schemas.kicad.org/erc.v1.json", "sheets":[{"violations":[{"severity":"warning","description":"retained library warning"}]}]}
    return root, pins, wireviz, erc


def evaluate(root, pins, wireviz, erc, *, defect=None, parameters=None):
    content = ET.tostring(root) if root is not None else b'<export/>'
    if defect == "external_entities":
        content = b'<!DOCTYPE export [<!ENTITY test "expanded">]>' + content
    if defect == "malformed_xml":
        content = b'<export><components></export>'
    subjects = [snapshot("kicad_schematic", b"identity-only schematic fixture", "kicad_sch"),
        snapshot("pin_schedule", pins.encode(), "csv"), snapshot("netlist", wireviz.encode(), "csv"),
        snapshot("kicad_erc", json.dumps(erc).encode(), "json"),
        snapshot("kicad_native_netlist", content, "xml")]
    hashes = {item.subject.role:item.subject.sha256 for item in subjects}
    proof = {"schema":"wright-native-kicad-interconnect-v1", "engine":"kicad-cli", "status":"exported_not_design_approval",
        "source_sha256":hashes["kicad_schematic"], "netlist_sha256":hashes["kicad_native_netlist"], "erc_sha256":hashes["kicad_erc"],
        "erc_error_count":0, "erc_warning_count":1}
    if defect in {"wrong_source_hash", "wrong_xml_hash", "wrong_erc_hash"}:
        proof[{"wrong_source_hash":"source_sha256", "wrong_xml_hash":"netlist_sha256", "wrong_erc_hash":"erc_sha256"}[defect]] = "0"*64
    if defect == "false_warning_count":
        proof["erc_warning_count"] = 0
    if defect != "missing_native_proof":
        subjects.append(snapshot("kicad_native_inspection", json.dumps(proof).encode(), "json"))
    report = {"schema":"wright-harness-kicad-correspondence-v1", "status":"pass",
        "schematic_sha256":hashes["kicad_schematic"],"pin_schedule_sha256":hashes["pin_schedule"],
        "netlist_sha256":hashes["netlist"],"erc_sha256":hashes["kicad_erc"],
        "missing_rows":[],"extra_rows":[],"mismatched_rows":[],"erc_error_count":0}
    check = CheckDefinition(id="native", requirement_ids=("REQ",), subject_role="net_correspondence", reader="harness",
        selector="harness/kicad-correspondence", constraint=Constraint(operator="equals",expected=True),
        evidence_method="independent_measurement", parameters={"operation":"kicad_correspondence",
        "expected_connections":CONNECTIONS, "native_pin_map":PIN_MAP,"reserved_endpoints":["JF:3"],**(parameters or {})})
    context = replace(ReaderContext.create(ResourceBudget(), "synthetic-native"), related_snapshots=tuple(subjects))
    return HarnessReader().measure(snapshot("net_correspondence", json.dumps(report).encode(), "json"), check, context)


def test_native_pins_nets_splice_reserve_and_real_erc_are_independently_compared():
    assert evaluate(*fixture()).value is True


@pytest.mark.parametrize("defect", ["missing_splice", "missing_net", "swapped_pins", "merged_returns", "extra_component",
    "wrong_pin_count", "reserve_connected", "duplicate_pin", "duplicate_net", "wrong_net_name", "fake_erc", "erc_error",
    "unknown_erc_severity", "false_warning_count", "wrong_source_hash", "wrong_xml_hash", "wrong_erc_hash",
    "missing_native_proof", "invalid_xml", "malformed_xml", "external_entities", "schedule_changed", "wireviz_changed", "extra_wire", "invalid_mapping"])
def test_pass_flags_cannot_hide_native_or_source_defects(defect):
    root, pins, wireviz, erc = fixture()
    nets = root.find("nets")
    params = None
    if defect == "missing_splice":
        root.find("components").remove(root.find("components/comp[@ref='B1']"))
        nets[0].remove(nets[0].find("node[@ref='B1']"))
    elif defect == "missing_net":
        nets.remove(nets[1])
    elif defect == "swapped_pins":
        nets[0].find("node[@ref='JF']").set("pin", "2")
        nets[1].find("node[@ref='JF']").set("pin", "1")
    elif defect == "merged_returns":
        nets[0].extend(list(nets[1]))
        nets.remove(nets[1])
    elif defect == "extra_component":
        duplicate = copy.deepcopy(root.find("components")[0])
        duplicate.set("ref","JX")
        root.find("components").append(duplicate)
    elif defect == "wrong_pin_count":
        ET.SubElement(root.find("libparts/libpart[@part='JF']/pins"), "pin", num="4")
    elif defect == "reserve_connected":
        nets[0].append(list(nets[2])[0])
        nets.remove(nets[2])
    elif defect == "duplicate_pin":
        nets[0].append(copy.deepcopy(nets[0][0]))
    elif defect == "duplicate_net":
        nets.append(copy.deepcopy(nets[0]))
    elif defect == "wrong_net_name":
        nets[0].set("name", "/INCORRECT")
    elif defect == "fake_erc":
        erc = {"errors":[], "warnings":[]}
    elif defect in {"erc_error", "unknown_erc_severity"}:
        erc["sheets"][0]["violations"][0]["severity"] = "error" if defect == "erc_error" else "hidden"
    elif defect == "invalid_xml":
        root = None
    elif defect == "schedule_changed":
        pins = pins.replace("J0,2,JF,2,RETURN", "J0,2,JF,1,RETURN")
    elif defect == "wireviz_changed":
        wireviz = wireviz.replace("J0:2,JF:2", "J0:2,JF:1")
    elif defect == "extra_wire":
        wireviz += "J0:1,JX:1,EXTRA,1\n"
    elif defect == "invalid_mapping":
        params = {"native_pin_map":{**PIN_MAP,"B1:POWER":"JF:1"}}
    with pytest.raises(ValidationIssue):
        evaluate(root, pins, wireviz, erc, defect=defect, parameters=params)


def test_equivalent_native_order_and_net_codes_do_not_change_connectivity():
    root, pins, wireviz, erc = fixture()
    nets = root.find("nets")
    nets.remove(nets[2])  # An unused reserve need not appear as a singleton net.
    for code, net in enumerate(nets, 40):
        net.set("code", str(code))
        net.set("name", net.attrib["name"].removeprefix("/"))
        net[:] = list(reversed(net))
    nets[:] = list(reversed(nets))
    root.find("components")[:] = list(reversed(root.find("components")))
    root.find("libparts")[:] = list(reversed(root.find("libparts")))
    assert evaluate(root, pins, wireviz, erc).value is True


@pytest.mark.parametrize("limit,code", [
    ("entities", "reader.entity_limit"),
    ("cancelled", "validation.cancelled"),
    ("timeout", "reader.timeout"),
])
def test_native_xml_preserves_resource_limit_and_cancellation_findings(limit, code):
    context = ReaderContext.create(ResourceBudget(max_entities=5), "native-limits")
    if limit == "cancelled":
        cancelled = Event()
        cancelled.set()
        context = replace(context, cancelled=cancelled)
    if limit == "timeout":
        context = replace(context, deadline=monotonic() - 1)
    with pytest.raises(ValidationIssue) as caught:
        _native_xml(ET.tostring(fixture()[0]), context)
    assert caught.value.code == code


def test_native_xml_respects_the_invocation_byte_budget():
    context = ReaderContext.create(ResourceBudget(max_bytes=32), "native-byte-limit")
    with pytest.raises(ValueError, match="oversized"):
        _native_xml(ET.tostring(fixture()[0]), context)


@pytest.mark.parametrize("ordinal,edge_count", [(1, 8), (2, 11), (3, 26)])
def test_profile_freezes_released_physical_schedule_and_named_splices(ordinal, edge_count):
    path = Path(__file__).parents[3] / "scripts/build_harness_validation_profiles.py"
    spec = importlib.util.spec_from_file_location("native_harness_profile", path)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    identity = f"sensor-fan-harness-{ordinal:02d}"
    profile = builder.build(identity, builder.SOURCES[identity])
    check = next(item for item in profile.checks if item.id == "kicad-correspondence")
    assert profile.version == "2" and check.version == "2"
    assert len(check.parameters["expected_connections"]) == edge_count
    assert {"kicad_native_netlist", "kicad_native_inspection"} <= set(check.parameters["related_roles"])
    mapping = check.parameters["native_pin_map"]
    if ordinal == 1:
        assert mapping["B1:POWER"] == "B1:1"
    else:
        assert mapping["B0:PLUS"] == "B0:1" and mapping["B0:RETURN"] == "B0:2"
    if ordinal == 3:
        assert check.parameters["reserved_endpoints"] == ["ZX:6", "ZY:6"]
        assert mapping["S_ZX:POWER"] == "S_ZX:1"
        assert mapping["S_ZY:POWER"] == "S_ZY:1"
        assert {"from": "ZX:1", "to": "S_ZX:POWER", "net": "24V"} in check.parameters["expected_connections"]
    for original, native in mapping.items():
        reference, number = original.split(":")
        if number.isdigit():
            assert native == f"{reference}:{number}"
