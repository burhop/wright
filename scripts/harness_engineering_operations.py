"""Source-bound harness synthesis and independent inspection using real WireViz.

Consumes customer schedules, never fixture geometry. Component facts retain
primary evidence and unresolved application ratings; no energizing/purchasing.
"""
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
import csv
import gzip
import hashlib
import html
import importlib.metadata
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+"\n", encoding="utf-8")


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def csv_file(path, records):
    with Path(path).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


def fresh(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=False)
    return path


def provenance(output, inputs):
    shutil.copyfile(__file__, output / "engineering-operation.py")
    return {"operation_sha256": sha(__file__), "inputs": [{"path": str(p), "sha256": sha(p)} for p in inputs],
            "created_at": datetime.now(UTC).isoformat(), "implementation": "WireViz/Graphviz selected implementation; not Splice", "physical_action": False}


def retrieve_records(source_document, output_directory):
    from pypdf import PdfReader
    specification, output = load(source_document), fresh(output_directory)
    allowed = {"www.amphenol-sine.com", "www.alphawire.com", "catalog.belden.com", "www.wago.com"}
    def fetch(item):
        uri = urllib.parse.urlparse(item["url"])
        if uri.scheme != "https" or uri.hostname not in allowed or uri.username or uri.password:
            raise ValueError("Only reviewed primary manufacturer HTTPS documents are permitted")
        request = urllib.request.Request(item["url"], headers={"User-Agent": "Wright-offline-harness-research/1.0"})
        with urllib.request.urlopen(request, timeout=45) as response:
            if urllib.parse.urlparse(response.url).hostname not in allowed:
                raise ValueError("Manufacturer redirected outside reviewed hosts")
            raw = response.read(12*1024*1024+1)
            final_url = response.url
        wire_sha256 = hashlib.sha256(raw).hexdigest()
        compressed = raw.startswith(b"\x1f\x8b")
        if compressed:
            raw = gzip.decompress(raw)
        if len(raw) > 12*1024*1024 or not raw:
            raise ValueError("Unexpected empty/oversized manufacturer document")
        pdf = raw.startswith(b"%PDF")
        suffix = ".pdf" if pdf else ".html"
        path = output / (item["id"]+suffix)
        path.write_bytes(raw)
        if pdf:
            reader = PdfReader(io.BytesIO(raw))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            text = html.unescape(re.sub("<[^>]+>", " ", raw.decode("utf-8", errors="replace")))
        normalized = re.sub(r"\s+", " ", text)
        missing = [token for token in item["tokens"] if token not in normalized]
        if missing:
            raise ValueError("Retrieved primary document does not expose expected record tokens: "+item["id"]+" "+str(missing))
        (output/(item["id"]+".txt")).write_text(text, encoding="utf-8")
        return {"id": item["id"], "url": item["url"], "final_url": final_url, "path": path.name, "sha256": sha(path),
                "http_body_sha256": wire_sha256, "http_gzip_decoded": compressed,
                "bytes": len(raw), "token_checks": item["tokens"], "retrieved_at": datetime.now(UTC).isoformat()}
    with ThreadPoolExecutor(max_workers=4) as pool:
        documents = list(pool.map(fetch, specification["documents"]))
    result = {**provenance(output, [Path(source_document)]), "documents": documents, "component_basis": specification["component_basis"],
              "fact_status": "Source-indexed candidate facts; token checks establish record identity, not independent engineering certification",
              "unresolved": ["Loaded-contact derating at scenario ambient", "Contact and splice resistance", "Exact fan/transmitter electrical interfaces", "Customer chassis termination geometry and environmental enclosure for splices"]}
    save(output/"component-records.json", result)
    return result


def verify_evidence(research):
    research = Path(research)
    result = load(research/"component-records.json")
    for document in result["documents"]:
        path = (research/document["path"]).resolve()
        if not path.is_relative_to(research.resolve()) or sha(path) != document["sha256"]:
            raise ValueError("Primary component evidence has changed")
    return result


def requirements(path):
    result = {}
    for row in read_csv(path):
        row = dict(row)
        for canonical, alias in (("min_power_contact_A", "min_contact_current_A"), ("min_voltage_V", "min_operating_voltage_V"), ("min_operating_temperature_C", "min_ambient_C")):
            if canonical not in row:
                row[canonical] = row[alias]
        for connector in row["connector"].split(";"):
            splice = connector.endswith("_power_splices")
            result[connector.removesuffix("_power_splices")] = {**row, "is_splice": splice}
    return result


def logical_edges(schedule):
    return [{"id": f"W{i+1:03d}", "from": row["from_connector"]+":"+row["from_pin"], "to": row["to_connector"]+":"+row["to_pin"],
             "net": row["net"], "route_mm": float(row["route_mm"]), "continuous_a": float(row["current_cont_A"]),
             "startup_a": float(row["current_start_A"]), "color": row["color_requirement"], "original_row": i+2}
            for i, row in enumerate(schedule)]


def synthesize(input_directory, design_document, research_directory, output_directory):
    import yaml
    source, output = Path(input_directory), fresh(output_directory)
    design = load(design_document)
    evidence = verify_evidence(research_directory)
    basis = evidence["component_basis"]
    customer = read_csv(source/"wiring-schedule.csv")
    connector_reqs = requirements(source/"connector-requirements.csv")
    if basis["wire_awg"] not in {int(row["awg"]) for row in read_csv(source/"allowed-wire.csv")}:
        raise ValueError("Selected wire gauge is outside supplied stock capability")
    edges = logical_edges(customer)
    original = json.loads(json.dumps(edges))
    # Replace each load-side power fork at a zone contact with a separate physical
    # splice/pigtail. Installed root-to-load route lengths are conserved.
    for node in sorted({edge["from"] for edge in edges}):
        outgoing = [edge for edge in edges if edge["from"] == node and edge["net"] == "24V"]
        incoming = [edge for edge in edges if edge["to"] == node and edge["net"] == "24V"]
        connector = node.split(":")[0]
        if connector not in connector_reqs or connector_reqs[connector]["is_splice"] or len(outgoing) < 2 or not incoming:
            continue
        length = float(design["zone_pigtail_route_mm"])
        splice = "S_"+connector+":POWER"
        for edge in outgoing:
            if edge["route_mm"] <= length:
                raise ValueError("Specified pigtail exceeds installed branch route")
            edge["from"] = splice
            edge["route_mm"] -= length
        edges.append({"id": "P_"+connector, "from": node, "to": splice, "net": "24V", "route_mm": length,
                      "continuous_a": sum(edge["continuous_a"] for edge in outgoing), "startup_a": sum(edge["startup_a"] for edge in outgoing),
                      "color": "red", "original_row": "derived physical one-wire-per-crimp fork"})
    connectors, pins, labels = {}, defaultdict(set), defaultdict(dict)
    for edge in edges:
        for endpoint in (edge["from"], edge["to"]):
            name, pin = endpoint.split(":")
            pins[name].add(pin)
            if pin in labels[name] and labels[name][pin] != edge["net"]:
                raise ValueError("Input schedule shorts two named nets at a pin")
            labels[name][pin] = edge["net"]
    for name, req in connector_reqs.items():
        if req["is_splice"]:
            continue
        for pin in range(1, int(req["pins"])+1):
            pins[name].add(str(pin))
            labels[name].setdefault(str(pin), "RESERVE / UNCONNECTED")
    bom = []
    for name in sorted(pins):
        ordered = sorted(pins[name], key=lambda pin: (not pin.isdigit(), int(pin) if pin.isdigit() else pin))
        physical = name in connector_reqs and not connector_reqs[name]["is_splice"]
        count = int(connector_reqs[name]["pins"]) if physical else len(ordered)
        code = "08SA" if count == 8 else f"{count}S"
        mpn = "AT06-"+code if physical else basis["splice_mpn"]
        connectors[name] = {"pins": [int(pin) if pin.isdigit() else pin for pin in ordered], "pinlabels": [labels[name][pin] for pin in ordered], "type": "mated connector pair" if physical else "separate splice per labeled potential",
                            "manufacturer": "Amphenol Sine" if physical else "WAGO", "mpn": mpn,
                            "notes": "Logical numbered cavities; mating-face drawings supplied separately. One wire per physical terminal." if physical else "One 221-413 per named potential; mount in protected enclosure; no IP rating claimed."}
        if physical:
            mate = "AT04-"+("08PA" if count == 8 else f"{count}P")
            for part, qty, purpose in [(mpn,1,"harness socket housing"),(mate,1,"mating pin housing; customer interface selection must be confirmed"),
                                       (f"AW{count}S",1,"socket wedgelock"),(f"AW{count}P",1,"pin wedgelock")]:
                bom.append(dict(mpn=part, quantity=qty, unit="each", use=name+": "+purpose, evidence="plug"+str(count)+"/socket"+str(count)))
            used = sum(1 for pin in ordered if not labels[name][pin].startswith("RESERVE"))
            for part in (basis["socket_terminal"], basis["pin_terminal"]):
                bom.append(dict(mpn=part, quantity=used, unit="each", use=name+": single conductor contacts (both mating halves)", evidence="contacts"))
            if count-used:
                bom.append(dict(mpn=basis["reserved_cavity_seal"], quantity=2*(count-used), unit="each", use=name+": unused cavities on both halves; no circuit connection", evidence="contacts"))
        else:
            bom.append(dict(mpn=mpn, quantity=len(ordered), unit="each", use=name+": one separate three-port splice per net", evidence="splice"))
    cables, connections, cuts, pin_table = {}, [], [], []
    paired = set()
    pair_groups = {}
    for pair in design["shield_pairs"]:
        candidates = [edge for edge in edges if edge["net"] in pair]
        for edge in candidates:
            key = tuple(sorted([edge["from"].split(":")[0], edge["to"].split(":")[0]]))
            pair_groups.setdefault((tuple(pair), key), []).append(edge)
    colors = {"red":"RD", "black":"BK", "white":"WH", "gray":"GY", "yellow":"YE", "blue":"BU"}
    def termination(endpoint):
        name = endpoint.split(":")[0]
        return (design["service_mm"]+basis["design_strip_mm"]) if name in connector_reqs and not connector_reqs[name]["is_splice"] else basis["splice_strip_mm"]
    def add_cable(name, members, shield=False):
        lengths = [edge["route_mm"]+termination(edge["from"])+termination(edge["to"]) for edge in members]
        if max(lengths)-min(lengths) > 1e-8:
            raise ValueError("Requested twisted-pair conductors have different installed/service lengths")
        length = lengths[0]
        cables[name] = {"wirecount": len(members), "gauge": "16 AWG", "length": length/1000, "colors": [colors[edge["color"]] for edge in members],
                        "manufacturer": "Belden" if shield else "Alpha Wire", "mpn": "8719" if shield else "3057", "shield": shield,
                        "wirelabels": [edge["net"] for edge in members], "notes": "Belden clear/black conductors: apply requested white/gray circuit markers. Drain never a return; controller chassis bond only, insulated removable service link at each zone." if shield else "Requested conductor color; final put-up suffix confirmed at procurement"}
        for index, edge in enumerate(members, 1):
            left, lp = edge["from"].split(":")
            right, rp = edge["to"].split(":")
            connections.append([{left: [int(lp) if lp.isdigit() else lp]}, {name: [index]}, {right: [int(rp) if rp.isdigit() else rp]}])
            pin_table.append(dict(wire_id=edge["id"], cable_id=name, conductor=index, from_connector=left, from_pin=lp, to_connector=right, to_pin=rp, net=edge["net"], view="numbered mating-face cavities; source drawing controls position", color_requirement=edge["color"]))
            edge.update(cable_id=name, conductor=index, cut_mm=length, awg=16, shielded_pair=shield,
                        r20_ohm_per_m=basis["pair_nominal_r20_ohm_m"] if shield else basis["wire_nominal_r20_ohm_m"])
        cuts.append(dict(cable_id=name, mpn=cables[name]["mpn"], conductors=len(members), installed_route_mm=members[0]["route_mm"], cut_mm=length,
                         service_plus_strip_mm=length-members[0]["route_mm"], quantity=1, note="Length is physical cable cut, not multiplied by pair conductor count"))
        bom.append(dict(mpn=cables[name]["mpn"], quantity=length/1000, unit="m", use=name, evidence="shielded_pair" if shield else "wire"))
    for index, group in enumerate(pair_groups.values(), 1):
        if len(group) != 2 or len({edge["net"] for edge in group}) != 2:
            raise ValueError("Shield pair requires exact signal/return route pairing")
        add_cable(f"PAIR{index:02d}", group, True)
        paired.update(edge["id"] for edge in group)
    for edge in edges:
        if edge["id"] not in paired:
            add_cable(edge["id"], [edge])
    bom.append(dict(mpn=basis["tool"], quantity=1, unit="tooling only", use="manufacturer-specified machined-contact hand crimp tool; setup and pull checks per retrieved manual", evidence="crimp_tool/contacts"))
    if design["shield_pairs"]:
        bom.append(dict(mpn=basis["splice_mpn"], quantity=len(design["shield_pairs"]), unit="each", use="insulated shield-drain service link at removable zones; two positions used; never pin6 or signal return", evidence="splice"))
    native = {"metadata": {"title":"Sensor and fan harness — engineering prototype", "notes":"WireViz alternative implementation; logical mating-face cavity IDs; no production electrical approval"},
              "connectors": connectors, "cables": cables, "connections": connections}
    yaml_path = output/"harness-source.yml"
    yaml_path.write_text(yaml.safe_dump(native, sort_keys=False), encoding="utf-8")
    command = [str(Path(sys.executable).with_name("wireviz")), "-f", "gspt", "-o", str(output), "-O", "harness-plan", str(yaml_path)]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=120)
    if completed.returncode:
        (output/"wireviz-error.txt").write_text(completed.stdout+"\n"+completed.stderr,encoding="utf-8")
        raise ValueError("Native WireViz failed: "+completed.stderr[-2000:])
    if not (output/"harness-plan.svg").exists() or not (output/"harness-plan.bom.tsv").exists():
        raise ValueError("Native WireViz did not generate its diagram and BOM")
    views = []
    for count in sorted({int(row["pins"]) for row in connector_reqs.values() if not row["is_splice"]}):
        for side in ("plug", "socket"):
            path = Path(research_directory)/f"{side}{count}.pdf"
            prefix = output/f"manufacturer-mating-view-{side}{count}"
            subprocess.run(["pdftoppm","-f","1","-singlefile","-scale-to","1400","-png",str(path),str(prefix)], check=True, capture_output=True, timeout=30)
            views.append(prefix.name+".png")
    csv_file(output/"pin-schedule.csv", pin_table)
    csv_file(output/"cut-list.csv", cuts)
    csv_file(output/"bom.csv", bom)
    shields = []
    for cable_id,cable in cables.items():
        if not cable.get("shield"):
            continue
        endpoints = sorted({endpoint.split(":")[0] for edge in edges if edge["cable_id"]==cable_id for endpoint in (edge["from"],edge["to"])})
        for endpoint in endpoints:
            method = "controller chassis bond; hardware geometry unresolved" if endpoint=="J0" else "separate insulated WAGO221-413 drain service link" if endpoint.startswith("Z") else "insulated unconnected load-end drain"
            shields.append(dict(cable_id=cable_id,endpoint=endpoint,termination=method,load_return=False,reserved_pin_used=False))
    save(output/"shield-termination.json",{"shield_ends":shields,"chassis_termination_hardware_selected":False,"physical_test_performed":False})
    package = {**provenance(output, [source/"wiring-schedule.csv", source/"connector-requirements.csv", source/"allowed-wire.csv", Path(design_document), Path(research_directory)/"component-records.json"]),
               "original_logical_edges": original, "physical_edges": edges, "connector_requirements": connector_reqs, "design": design,
               "generated_source_sha256": sha(yaml_path), "wireviz_version": importlib.metadata.version("wireviz"), "graphviz_version": subprocess.run(["dot","-V"],capture_output=True,text=True).stderr.strip(),
               "native_command": command, "native_stdout": completed.stdout, "native_stderr": completed.stderr, "mating_views": views, "shield_schedule":shields,
               "release_status":"HOLD: application derating, contact/splice resistance, exact interfaces and installation details require evidence"}
    save(output/"harness-plan.json", package)
    assembly = "# Prototype harness assembly\n\nWireViz/Graphviz generated this package from the original uploaded schedule. This is an explicit Splice alternative, not Splice output.\n\n"
    assembly += "Preserve logical pin IDs and use the attached manufacturer mating-face drawings; the wire-entry view is mirrored and must not be substituted. Confirm the customer devices accept the selected mating housings before fabrication.\n\n"
    assembly += "Use the exact housing pair/wedgelocks and single-wire machined terminals in bom.csv. Strip contact ends to the 7.0 mm design nominal inside the sourced 6.35–7.92 mm range; use AUTK-16 per its retrieved instructions. Strip WAGO ends 11 mm. Inspect strands and retention, perform representative crimp pull checks before assembly. No performed test is claimed.\n\n"
    assembly += f"Cut once per cut-list row, retaining the original one-way routes plus {design['service_mm']} mm service length at each connector termination and sourced termination allowance. P_ zone pigtails are {design['zone_pigtail_route_mm']} mm installed segments deducted from each downstream original route, preserving root-to-load length. No two conductors share one crimp. WAGO branch splices need protected retained enclosures; no sealed splice assembly is claimed.\n\n"
    assembly += f"Maintain at least {design['minimum_bend_radius_mm']} mm route bend radius and any larger cable manufacturer requirement. Retain all supplied hot-wall, irrigation/motor separation, sleeve, clip and label requirements. {design['physical_cross_connection_control']}.\n\n"
    if design["shield_pairs"]:
        assembly += "Use Belden 8719 twisted pairs for pressure/sensor return. Clear conductor gets white signal markers; black gets gray return markers. Join each zone's cable drain segments through its separate insulated WAGO service link, leave load-end shield/drain insulated, and bond only at the controller chassis. Shield drain never uses reserved pin6, signal return, fan ground or protective-earth function. Customer chassis stud/termination and cable-end breakout hardware remain unselected; do not fabricate that termination until resolved.\n\n"
    assembly += "Keep fan return and each sensor return separate throughout; only the external controller implements the documented star point. Seal reserved cavities and leave them electrically open. With power isolated, continuity-check every pin row, all disconnected reserves, cross-net isolation and shield-to-chassis/signal isolation; review against independent verification.json. No energizing, purchasing or controller changes authorized.\n\nRelease HOLD: ambient loaded-contact current derating, contact/splice resistance and exact fan/transmitter PWM/tach/analog compatibility remain unresolved. See voltage-drop.json for copper-only budgets, never claim total loaded drop was verified.\n\n## Manufacturer mating-face views\n\n"
    assembly += "\n".join(f"![Unmodified manufacturer drawing {name}]({name})" for name in views)
    (output/"assembly.md").write_text(assembly, encoding="utf-8")
    return package


def independent_verify(input_directory, research_directory, generated_directory, output_directory):
    import yaml
    source, generated, output = Path(input_directory), Path(generated_directory), fresh(output_directory)
    package = load(generated/"harness-plan.json")
    basis = verify_evidence(research_directory)["component_basis"]
    native = yaml.safe_load((generated/"harness-source.yml").read_text())
    expected = logical_edges(read_csv(source/"wiring-schedule.csv"))
    physical = package["physical_edges"]
    observed = []
    for connection in native["connections"]:
        left, center, right = [next(iter(item.items())) for item in connection]
        observed.append((left[0]+":"+str(left[1][0]),right[0]+":"+str(right[1][0]),center[0],int(center[1][0])))
    wanted = [(edge["from"],edge["to"],edge["cable_id"],edge["conductor"]) for edge in physical]
    failures = []
    shield_record = load(generated/"shield-termination.json")
    if shield_record["shield_ends"] != package["shield_schedule"] or any(row["load_return"] or row["reserved_pin_used"] for row in shield_record["shield_ends"]):
        failures.append("Shield schedule uses a load return or reserved contact")
    for cable_id,cable in native["cables"].items():
        if cable["mpn"]=="8719" and (not cable.get("shield") or cable["wirecount"]!=2):
            failures.append("Requested shielded twisted pair missing from native source: "+cable_id)
    if any(connector.get("loops") for connector in native["connectors"].values()):
        failures.append("Unexpected native connector loop creates a short")
    if sorted(observed) != sorted(wanted):
        failures.append("Native emitted netlist differs from the physical pin schedule")
    if [(e["from"],e["to"],e["net"],e["route_mm"]) for e in expected] != [(e["from"],e["to"],e["net"],e["route_mm"]) for e in package["original_logical_edges"]]:
        failures.append("Original customer netlist was changed")
    by_node = defaultdict(set)
    for edge in physical:
        by_node[edge["from"]].add(edge["net"])
        by_node[edge["to"]].add(edge["net"])
    if any(len(nets)>1 for nets in by_node.values()):
        failures.append("Unexpected short between named nets")
    for connector, req in requirements(source/"connector-requirements.csv").items():
        if req.get("reserved_pins", "none") != "none":
            pin = req["reserved_pins"].split("_")[0]
            if connector+":"+pin in by_node:
                failures.append("Reserved pin is connected: "+connector+":"+pin)
    adjacency = defaultdict(list)
    for index, edge in enumerate(physical):
        adjacency[edge["from"]].append((edge["to"],index))
        adjacency[edge["to"]].append((edge["from"],index))
    def route(start, finish, net):
        queue = deque([(start,[])])
        visited = {start}
        while queue:
            node, path = queue.popleft()
            if node == finish:
                return path
            for target,index in adjacency[node]:
                if target not in visited and physical[index]["net"] == net:
                    visited.add(target)
                    queue.append((target,path+[index]))
        raise ValueError("Open circuit: "+start+" -> "+finish+" net "+net)
    for edge in expected:
        path = route(edge["from"],edge["to"],edge["net"])
        if abs(sum(physical[i]["route_mm"] for i in path)-edge["route_mm"]) > 1e-6:
            failures.append("Installed route length changed: "+edge["id"])
    # Solve segment currents from leaf loads and compare every shared trunk.
    loads = [edge for edge in expected if edge["net"] == "24V" and not any(other["from"] == edge["to"] and other["net"] == "24V" for other in expected)]
    currents = {"continuous_a":defaultdict(float),"startup_a":defaultdict(float)}
    branches = []
    supply_root = next(edge["from"] for edge in expected if edge["net"] == "24V" and edge["from"].startswith("J0:"))
    for leaf in loads:
        connector = leaf["to"].split(":")[0]
        return_node = connector+":2"
        return_net = next(iter(by_node[return_node]))
        root = next(node for node,nets in by_node.items() if node.startswith("J0:") and return_net in nets)
        path = route(supply_root,leaf["to"],"24V") + route(root,return_node,return_net)
        for mode in currents:
            for index in path:
                currents[mode][index] += leaf[mode]
        branches.append((connector,path,leaf))
    drops = []
    alpha = 0.00393
    initial_wire = {int(row["awg"]): float(row["resistance_ohm_per_m_at_20C"]) for row in read_csv(source/"allowed-wire.csv")}
    for edge in physical:
        cable = native["cables"][edge["cable_id"]]
        expected_part = "8719" if edge["shielded_pair"] else "3057"
        reference_resistance = basis["pair_nominal_r20_ohm_m"] if edge["shielded_pair"] else basis["wire_nominal_r20_ohm_m"]
        if cable["mpn"] != expected_part or cable["gauge"] != "16 AWG" or abs(edge["r20_ohm_per_m"]-reference_resistance) > 1e-12:
            failures.append("Generated conductor differs from sourced selected gauge/part/resistance: "+edge["id"])
    for mode, solved in currents.items():
        for index,current in solved.items():
            if abs(current-physical[index][mode]) > 1e-9:
                failures.append("Shared segment current mismatch: "+physical[index]["id"]+" "+mode)
        for connector,path,leaf in branches:
            terms = []
            for index in path:
                edge = physical[index]
                length = native["cables"][edge["cable_id"]]["length"]
                resistance = length*edge["r20_ohm_per_m"]*(1+alpha*(package["design"]["ambient_c"]-20))
                terms.append(dict(wire_id=edge["id"], current_a=solved[index], resistance_ohm=resistance, drop_v=solved[index]*resistance))
            copper = sum(item["drop_v"] for item in terms)
            initial_design_drop = sum(solved[index] * native["cables"][physical[index]["cable_id"]]["length"] * initial_wire[16] * (1+alpha*(package["design"]["ambient_c"]-20)) for index in path)
            limit = package["design"]["drop_limit_v"]
            if copper > limit:
                failures.append("Copper-only voltage budget exceeded: "+connector+" "+mode)
            drops.append(dict(load=connector,case=mode,copper_only_drop_v=copper,limit_v=limit,remaining_contact_budget_v=limit-copper,
                              supplied_initial_design_copper_drop_v=initial_design_drop,contact_and_splice_drop_v=None,total_drop_v=None,status="total_unverified_contact_resistance_unknown",terms=terms))
    ratings = []
    for connector, req in requirements(source/"connector-requirements.csv").items():
        if req["is_splice"]:
            nominal_ok = float(req["min_power_contact_A"]) <= basis["splice_nominal_current_a"] and float(req["min_voltage_V"]) <= basis["splice_nominal_voltage_v"]
            if not nominal_ok:
                failures.append("Nominal splice rating below customer requirement: "+connector)
            ratings.append(dict(connector=connector,nominal_limits_meet_customer_minimum=nominal_ok,application_current_derating_verified=False,source="splice document: nominal32A/450V; loaded ambient qualification unresolved",release="hold"))
            continue
        nominal_ok = float(req["min_power_contact_A"]) <= basis["nominal_contact_current_a"] and float(req["min_voltage_V"]) <= basis["nominal_voltage_v"] and float(req["min_operating_temperature_C"]) <= basis["temperature_max_c"]
        if not nominal_ok:
            failures.append("Nominal component rating below supplied requirement: "+connector)
        ratings.append(dict(connector=connector,nominal_limits_meet_customer_minimum=nominal_ok,application_current_derating_verified=False,source="component-records.json source_mapping; exact housing drawings and contacts",release="hold"))
    result = {**provenance(output,[source/"wiring-schedule.csv",generated/"harness-source.yml",generated/"harness-plan.json",Path(research_directory)/"component-records.json"]),
              "netlist_and_numeric_failures": failures, "observed_native_connections": len(observed), "customer_edges":len(expected), "physical_wires":len(physical),
              "ratings":ratings,"voltage_drop":drops,"release":"rejected" if failures else "hold_for_missing_application_evidence",
              "engineering_validation_complete":False,"physical_continuity_test_performed":False,
              "limitations":["Nominal source ratings do not prove derating at loaded-contact ambient","Contact/splice resistances remain unknown; computed drop is copper-only","Fan/transmitter interface datasheets absent","Chassis shield termination and installation reach/environment need confirmation"]}
    save(output/"verification.json",result)
    save(output/"voltage-drop.json",{"branches":drops,"contact_resistance_not_assumed_zero":True})
    csv_file(output/"independent-netlist.csv",[dict(from_endpoint=a,to_endpoint=b,cable=c,conductor=d) for a,b,c,d in observed])
    return result
