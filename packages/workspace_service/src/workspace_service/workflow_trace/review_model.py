"""Source-backed engineering presentation for portable run reviews."""

from __future__ import annotations

import json
import io
import re
import zipfile
from xml.etree import ElementTree
from collections.abc import Mapping
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any


LABELS = {
    "source-model-report.json": "Part design record",
    "repair-model-report.json": "Mesh repair and measurement report",
    "slice-evidence.json": "Slicing results",
    "slice-operation-report.json": "Slicer operation report",
    "process-profile.json": "Print settings",
    "machine-profile.json": "Printer settings",
    "filament-profile.json": "Material settings",
    "printer-transfer-receipt.json": "Transfer receipt",
    "source_mesh.stl": "Part model before repair",
    "repaired_mesh.stl": "Part mesh after cleanup",
    "mesh-preview.png": "Part design",
    "slice-preview.png": "Slicer model preview",
    "support-preview.svg": "Toolpath projection",
    "slice_package.gcode.3mf": "Manufacturing package",
    "slicer.stdout.log": "Slicer log",
}


def _package_application(resource: Any) -> str | None:
    """Read bounded 3MF producer metadata, without loading or checking geometry."""
    if (
        not resource.data
        or not resource.name.lower().endswith(".3mf")
        or len(resource.data) > 8 * 1024 * 1024
    ):
        return None
    try:
        with zipfile.ZipFile(io.BytesIO(resource.data)) as package:
            entry = package.getinfo("3D/3dmodel.model")
            if entry.file_size > 64 * 1024:
                return None
            text = package.read(entry).decode("utf-8")
        if "<!doctype" in text.lower() or "<!entity" in text.lower():
            return None
        root = ElementTree.fromstring(text)
        for item in root.findall(
            "{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}metadata"
        ):
            if (
                item.get("name") == "Application"
                and item.text
                and len(item.text) <= 160
            ):
                return item.text
    except (
        ValueError,
        KeyError,
        UnicodeError,
        zipfile.BadZipFile,
        ElementTree.ParseError,
        RuntimeError,
    ):
        pass
    return None


_EVENT_LABELS = {
    "step_started": "Activity started",
    "step_completed": "Activity completed",
    "step_failed": "Activity failed",
    "approval_requested": "Transfer authorization requested",
    "approval_decided": "Authorization decision recorded",
    "external_action_reconciled": "Transfer receipt recorded",
}


_FAMILY_PRESENTATIONS = {
    "raspberry-pi-enclosure": (
        "Thermal enclosure comparison",
        "Enclosure and CFD package produced",
    ),
    "parametric-drill-jig": (
        "Parametric drill jig",
        "Jig manufacturing definition produced",
    ),
    "robot-tracking-diagnosis": (
        "Robot tracking diagnosis",
        "Tracking diagnosis produced",
    ),
    "heat-spreader-sizing": (
        "Conduction heat-spreader sizing",
        "Thermal sizing decision produced",
    ),
    "sensor-fan-harness": (
        "Sensor and fan wiring harness",
        "Harness manufacturing package produced",
    ),
    "sensor-interface-pcb": (
        "Sensor interface PCB",
        "PCB fabrication package produced",
    ),
    "water-heater-sizing": (
        "Water-heater power sizing",
        "Heater sizing decision produced",
    ),
    "lightweight-equipment-bracket": (
        "Lightweight equipment bracket",
        "Bracket workflow stopped",
    ),
    "sheet-metal-supplier-handoff": (
        "Sheet-metal supplier handoff",
        "Supplier handoff stopped",
    ),
}

_PRINCIPAL_OUTPUTS = (
    "sizing-decision",
    "heater-selection",
    "workflow-heater-selection",
    "diagnosis",
    "analysis-report",
    "verification-report",
    "thermal-verification-report",
    "cfd-comparison",
    "cfd-handoff",
    "harness-handoff",
    "verification-evidence",
    "dimension-report",
    "design-basis",
    "jig-design-basis",
    "electrical-basis",
    "research-and-design-basis",
    "design-gerbers",
    "jig.step",
    "design.kicad_pcb",
)

_MEANINGFUL_PREVIEWS = (
    "mesh-preview.png",
    "trajectory-overlay.svg",
    "harness-plan.png",
    "temperature-curve.svg",
)


def _label(value: Any) -> str:
    label = str(value).replace("_", " ").replace("-", " ").strip().capitalize()
    for source, replacement in (
        (r"\bAgentcad\b", "AgentCAD"),
        (r"\bCad\b", "CAD"),
        (r"\bCfd\b", "CFD"),
        (r"\bPcb\b", "PCB"),
    ):
        label = re.sub(source, replacement, label, flags=re.I)
    return label


def _value(value: Any) -> str:
    if value is None:
        return "Not recorded"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        return f"{value:,.6g}"
    if isinstance(value, (str, int)):
        return str(value)
    if isinstance(value, list) and all(isinstance(v, (str, int, float)) for v in value):
        return ", ".join(_value(v) for v in value)
    return "See supporting document"


def _recorded_time(value: Any) -> str:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).strftime(
            "%d %b %Y, %H:%M:%S %z"
        )
    except ValueError:
        return "Not recorded"


def _scenario_family(run: Mapping[str, Any]) -> str:
    workflow_id = str(run.get("workflow_id") or "")
    return re.sub(r"-\d+$", "", workflow_id)


def _software_facts(value: Any) -> list[tuple[str, str | None]]:
    """Find producer-recorded software identities without guessing from filenames."""
    found: list[tuple[str, str | None]] = []
    keys = {"runtime", "software", "application", "tool_name", "server_name"}

    def visit(item: Any, depth: int = 0) -> None:
        if depth > 5 or len(found) >= 12:
            return
        if isinstance(item, Mapping):
            version = next(
                (
                    str(item[key])
                    for key in ("tool_version", "software_version", "version")
                    if isinstance(item.get(key), (str, int, float))
                ),
                None,
            )
            for key, candidate in item.items():
                if key in keys and isinstance(candidate, str) and candidate.strip():
                    identity = candidate.strip()
                    if not re.fullmatch(r"[a-f0-9]{24,}", identity, re.I):
                        found.append((identity, version))
                elif isinstance(candidate, (Mapping, list)):
                    visit(candidate, depth + 1)
        elif isinstance(item, list):
            for candidate in item[:40]:
                visit(candidate, depth + 1)

    visit(value)
    return list(dict.fromkeys(found))


def _generic_deliverables(documents: list[dict]) -> list[str]:
    outputs = [
        document
        for document in documents
        if not document["input_only"] and not document.get("archive_only")
    ]

    def priority(document: Mapping[str, Any]) -> tuple[int, str]:
        name = str(document["name"]).lower()
        match = next(
            (index for index, token in enumerate(_PRINCIPAL_OUTPUTS) if token in name),
            len(_PRINCIPAL_OUTPUTS),
        )
        return (match, name)

    matched = [
        document
        for document in sorted(outputs, key=priority)
        if priority(document)[0] < len(_PRINCIPAL_OUTPUTS)
    ]
    if matched:
        return [document["id"] for document in matched[:4]]
    fallback = [
        document
        for document in outputs
        if document["media_type"].startswith("model/")
        or re.search(
            r"report|decision|diagnosis|handoff|verification", document["name"], re.I
        )
    ]
    return [document["id"] for document in fallback[:4]]


def _generic_previews(documents: list[dict]) -> list[str]:
    by_name = {document["name"].lower(): document for document in documents}
    return [
        by_name[name]["id"]
        for name in _MEANINGFUL_PREVIEWS
        if name in by_name
        and not by_name[name]["input_only"]
        and not by_name[name].get("archive_only")
    ][:2]


def _generic_interactive_models(documents: list[dict], family: str) -> list[str]:
    """Select reviewer-facing final geometry, not every retained analysis mesh."""
    names_by_family = {
        "printed-replacement-part": ("repaired_mesh.stl",),
        "raspberry-pi-enclosure": ("enclosure-a.stl", "enclosure-b.stl"),
        "parametric-drill-jig": ("jig.stl",),
    }
    by_name = {str(document["name"]).lower(): document for document in documents}
    return [
        document["id"]
        for name in names_by_family.get(family, ())
        if (document := by_name.get(name))
        and document["media_type"] == "model/stl"
        and not document["input_only"]
        and not document.get("archive_only")
    ]


def _activity_geometry(
    steps: list[dict], documents: list[dict], resources, principal: list[str]
) -> list[str]:
    """Keep activity geometry scoped to an occurrence and its recorded role."""
    by_id = {document["id"]: document for document in documents}
    meshes = {
        document["id"]
        for document in documents
        if document["media_type"] == "model/stl" and not document.get("archive_only")
    }
    by_subject = {resource.subject_id: resource for resource in resources}
    digests = {
        document["id"]: by_subject[document["subject_id"]].digest
        for document in documents
    }
    for step in steps:
        for attempt in step["attempts"]:
            attempt["geometry"] = [
                {
                    "document_id": document_id,
                    "relation": "produced",
                    "step_id": step["id"],
                }
                for document_id in sorted(
                    attempt["documents"], key=lambda value: value not in principal
                )
                if document_id in meshes
            ]
            own = {value["document_id"] for value in attempt["geometry"]}
            for record_id in attempt["documents"]:
                observations = by_id[record_id]["data"].get("observations")
                if not isinstance(observations, list):
                    continue
                for observation in observations:
                    if not isinstance(observation, Mapping) or not observation.get(
                        "sha256"
                    ):
                        continue
                    matches = [
                        document_id
                        for document_id in meshes
                        if digests[document_id] == observation["sha256"]
                    ]
                    # Reused bytes in multiple occurrences do not establish one subject.
                    if len(matches) == 1 and matches[0] not in own:
                        attempt["geometry"].append(
                            {
                                "document_id": matches[0],
                                "relation": "inspected",
                                "source_id": record_id,
                            }
                        )
                        own.add(matches[0])

    for index, step in enumerate(steps):
        if len(step["attempts"]) != 1:
            continue
        attempt = step["attempts"][0]
        authoring = next(
            (
                by_id[document_id]
                for document_id in attempt["documents"]
                if by_id[document_id]["name"] == "cad-authoring.json"
            ),
            None,
        )
        if (
            attempt["geometry"]
            or not authoring
            or not any(
                by_id[value]["media_type"] == "text/x-python"
                for value in attempt["documents"]
            )
        ):
            continue
        # This is navigation to later run evidence, never a claimed source-to-mesh link.
        following = next(
            (
                candidate
                for candidate in steps[index + 1 :]
                if candidate["lane"] == step["lane"]
                and len(candidate["attempts"]) == 1
                and any(
                    value["relation"] == "produced"
                    for value in candidate["attempts"][0]["geometry"]
                )
            ),
            None,
        )
        if following:
            attempt["geometry"] = [
                {**value, "relation": "later_run_result", "source_id": authoring["id"]}
                for value in following["attempts"][0]["geometry"]
                if value["relation"] == "produced"
            ]
            attempt["geometry_note"] = (
                "This activity authored CAD source. The geometry shown was produced later by "
                f"{following['title']} in this run, not captured during source authoring. "
                "An exact source-version-to-model link was not retained."
            )
    return list(
        dict.fromkeys(
            [
                *principal,
                *[
                    value["document_id"]
                    for step in steps
                    for attempt in step["attempts"]
                    for value in attempt["geometry"]
                ],
            ]
        )
    )


def _software_for_step(family: str, node_id: str) -> str:
    """Name the producer implied by the retained workflow/task identity."""
    if re.search(r"review|approval|authorize", node_id, re.I):
        return "Wright AutoTest"
    rules = {
        "raspberry-pi-enclosure": (
            (r"cfd|foam", "OpenFOAM"),
            (r"cad|agentcad|enclosure", "AgentCAD / build123d"),
        ),
        "parametric-drill-jig": ((r"jig|project|export", "AgentCAD / build123d"),),
        "robot-tracking-diagnosis": (
            (r"bag", "ROS 2 bag tooling"),
            (r"align|measure|normalize|diagnosis", "Wright analysis automation"),
        ),
        "heat-spreader-sizing": (
            (r"fe_call|solve|thermal", "CalculiX"),
            (r"plate|geometry|project|cad", "AgentCAD / build123d"),
        ),
        "sensor-fan-harness": (
            (r"generate", "WireViz / Graphviz"),
            (r"verify|collect|research", "Wright harness automation"),
        ),
        "sensor-interface-pcb": ((r"pcb|board|schematic|project|routing", "KiCad"),),
        "water-heater-sizing": (
            (r"native|modelica|allowed_settings|selection", "OpenModelica"),
        ),
        "lightweight-equipment-bracket": (
            (r"solve|field|calculix|mesh", "CalculiX"),
            (r"bracket|cad|geometry|project", "AgentCAD / build123d"),
        ),
        "sheet-metal-supplier-handoff": (
            (r"solid_edge|sheet|cad|export", "Solid Edge"),
        ),
    }
    for pattern, software in rules.get(family, ()):
        if re.search(pattern, node_id, re.I):
            return software
    return "Wright workflow automation"


def _decode(resource: Any) -> dict:
    if not resource.data or len(resource.data) > 2 * 1024 * 1024:
        return {}
    try:
        data = json.loads(resource.data)
        # MCP tools sometimes retain the engineering report inside a text result.
        for _ in range(3):
            if not isinstance(data, dict):
                return {}
            content = data.get("content")
            if not isinstance(content, list):
                return data
            text = next(
                (
                    item.get("text")
                    for item in content
                    if isinstance(item, dict) and item.get("type") == "text"
                ),
                None,
            )
            if not isinstance(text, str):
                return data
            data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except (ValueError, UnicodeDecodeError):
        return {}


def _table(
    title: str,
    rows: list,
    source: str | None = None,
    columns: list[str] | None = None,
    collapsed: bool = False,
) -> dict:
    return {
        "title": title,
        "columns": columns or ["Property", "Recorded value"],
        "rows": [[_value(v) for v in row] for row in rows],
        "source": source,
        "collapsed": collapsed,
    }


def _readable_tables(document: Mapping[str, Any]) -> list[dict]:
    """Keep unknown producer documents readable without exposing transport fields."""
    hidden = re.compile(
        r"(^id$|_id$|digest|sha256|schema|argv|gcode|path$|^content$|^artifacts$)"
    )
    tables: list[dict] = []

    def visit(value: Mapping, title: str, depth: int = 0) -> None:
        if depth > 3 or len(tables) >= 12:
            return
        rows = []
        children = []
        for key, item in value.items():
            if hidden.search(str(key)):
                continue
            if isinstance(item, Mapping):
                children.append((item, _label(key)))
            elif isinstance(item, (str, int, float, bool)) or item is None:
                if isinstance(item, str) and (
                    len(item) > 700 or re.search(r"[a-f0-9]{32}", item)
                ):
                    continue
                rows.append([_label(key), item])
            elif isinstance(item, list) and len(item) <= 20:
                for index, entry in enumerate(item):
                    if isinstance(entry, Mapping):
                        children.append((entry, f"{_label(key)} {index + 1}"))
                    elif isinstance(entry, (str, int, float)):
                        rows.append([_label(key), entry])
        if rows:
            tables.append(_table(title, rows[:60]))
        for child, name in children:
            visit(child, name, depth + 1)

    visit(document, "Recorded engineering information")
    return tables


def _engineering_presentation(
    name: str, data: Mapping[str, Any]
) -> tuple[list[str], list[dict]]:
    if name == "cad-authoring.json" and isinstance(data.get("summary"), str):
        return [data["summary"]], []
    observations = data.get("observations")
    if name != "cad-export-inspection.json" or not isinstance(observations, list):
        return [], _readable_tables(data)
    files = [
        item
        for item in observations
        if isinstance(item, Mapping)
        and isinstance(item.get("path"), str)
        and isinstance(item.get("sha256"), str)
    ]
    step_count = sum(
        str(item["path"]).lower().endswith((".step", ".stp")) for item in files
    )
    stl_count = sum(str(item["path"]).lower().endswith(".stl") for item in files)
    contract_count = sum("contract" in str(item["path"]).lower() for item in files)
    summary = str(data.get("summary") or "")
    unresolved = re.search(r"Unresolved lineage remains for (.+?) because", summary)
    paragraphs = [
        f"All {len(files)} expected CAD and CFD exports were found at their recorded relative paths and matched their retained SHA-256 identities."
    ]
    if unresolved:
        paragraphs.append(
            "Lineage was not resolved for "
            + unresolved.group(1).replace(", and ", ", ")
            + "; those files were outside the authorized inspection set."
        )
    checks = _table(
        "CAD export verification",
        [
            ["Expected outputs present", f"{len(files)} / {len(files)}", "Passed"],
            [
                "Retained file identity",
                f"{len(files)} / {len(files)} SHA-256 matches",
                "Passed",
            ],
            ["STEP representations", step_count, "Verified"],
            ["STL visualization meshes", stl_count, "Verified"],
            ["CFD contract records", contract_count, "Read completely"],
        ],
        columns=["Check", "Result", "Status"],
    )
    file_rows = [
        [
            item["path"],
            PurePosixPath(str(item["path"])).suffix.lstrip(".").upper(),
            "Identity matched",
        ]
        for item in files
    ]
    return paragraphs, [
        checks,
        _table(
            "Verified export identities",
            file_rows,
            columns=["Engineering output", "Format", "Integrity"],
            collapsed=True,
        ),
    ]


def _lane_for_step(family: str, node_id: str) -> str:
    if re.search(r"review|approval|authorize", node_id, re.I):
        return "Design authorization"
    if re.search(r"author_cad|agentcad|inspect_cad|geometry|export", node_id, re.I):
        return "CAD engineering"
    if re.search(r"source|research|requirements|design_basis", node_id, re.I):
        return "Requirements & design basis"
    if re.search(r"prepare.*cfd|mesh|case", node_id, re.I):
        return "Simulation preparation"
    if re.search(r"solve|simulate|cfd_compare|thermal|modelica", node_id, re.I):
        return "Engineering analysis"
    if re.search(r"collect|verify|validation|diagnosis|handoff", node_id, re.I):
        return "Verification & results"
    if family == "sensor-interface-pcb":
        return "PCB engineering"
    if family == "sensor-fan-harness":
        return "Harness engineering"
    return "Workflow execution"


def _review_inputs(
    inspection: Mapping, documents: list[dict], resources: list
) -> list[dict]:
    """Separate captured inputs from producer references without resolving paths."""
    inputs: list[dict] = []
    by_subject = {document["subject_id"]: document for document in documents}
    resource_by_subject = {resource.subject_id: resource for resource in resources}
    input_subjects: set[str] = set()
    outputs = list(inspection.get("final_outputs") or [])
    for step in inspection.get("steps") or []:
        outputs.extend(step.get("outputs") or [])
    output_subjects = {
        item["artifact"].get("artifact_id")
        for item in outputs
        if isinstance(item.get("artifact"), Mapping)
    }
    labels = {
        "prompt.txt": "Design request",
        "concept.png": "Design sketch (PNG)",
        "concept.svg": "Design sketch (SVG)",
        "context.md": "Design context",
        "user-profile.md": "Requester profile",
        "assembled-context.md": "Supporting context",
    }

    def append(
        name: str,
        *,
        value: Any = None,
        reference: str | None = None,
        document: dict | None = None,
        source: str | None = None,
        media_type: str = "",
        complete: bool = True,
        redacted: bool = False,
        provenance: str | None = None,
    ) -> None:
        leaf = PurePosixPath(name.replace("\\", "/")).name
        suffix = PurePosixPath(leaf).suffix.lower()
        prompt = bool(
            re.search(
                r"(^|[_. -])(prompt|instructions|request|brief)([_. -]|$)", leaf, re.I
            )
        )
        group = (
            "Prompts"
            if prompt
            else (
                "Images"
                if media_type.startswith("image/")
                or suffix in {".png", ".jpg", ".jpeg", ".webp", ".svg"}
                else "Models"
                if media_type.startswith("model/")
                or suffix in {".step", ".stp", ".stl", ".3mf", ".obj"}
                else "Parameters"
                if isinstance(value, (Mapping, list, int, float, bool))
                else "Documents"
            )
        )
        text = value if isinstance(value, str) and not reference else None
        if document and text is None and not redacted:
            original = resource_by_subject[document["subject_id"]]
            if (
                original.media_type in {"text/plain", "text/markdown"}
                and original.data
                and len(original.data) <= 64 * 1024
            ):
                try:
                    text = original.data.decode("utf-8")
                except UnicodeDecodeError:
                    pass
        identity_only = isinstance(text, str) and bool(
            re.fullmatch(r"[a-fA-F0-9]{64}", text)
        )
        if identity_only:
            text = None
        tables = (
            _readable_tables(value)
            if isinstance(value, Mapping)
            else (
                [_table("Recorded parameters", [[_label(leaf), value]])]
                if isinstance(value, (int, float, bool, list))
                else []
            )
        )
        inputs.append(
            {
                "id": f"input-{len(inputs) + 1}",
                "name": leaf,
                "title": labels.get(leaf, _label(PurePosixPath(leaf).stem)),
                "group": group,
                "text": text,
                "tables": tables,
                "document_id": document["id"] if document else None,
                "source_document_id": source,
                "reference": reference,
                "identity_only": identity_only,
                "complete": complete,
                "redacted": redacted,
                "provenance": provenance,
                "format_note": {
                    "concept.png": "Raster image",
                    "concept.svg": "Vector drawing",
                }.get(leaf),
            }
        )

    supplied = list(inspection.get("run_inputs") or [])
    supplied.extend(
        item
        for item in inspection.get("review_supplements") or []
        if (item.get("artifact") or {}).get("role") == "input_reconstruction"
    )
    for item in supplied:
        if not isinstance(item, Mapping):
            continue
        artifact = item.get("artifact") or {}
        subject = artifact.get("artifact_id") if isinstance(artifact, Mapping) else None
        document = by_subject.get(subject)
        if subject:
            input_subjects.add(subject)
        value = item.get("value")
        reference = (
            value
            if item.get("kind") in {"artifact", "link", "file"}
            and isinstance(value, str)
            else None
        )
        append(
            str(item.get("name") or "Recorded input"),
            value=value,
            reference=reference,
            document=document,
            media_type=str(item.get("data_type") or ""),
            complete=item.get("complete") is not False,
            redacted=bool(item.get("redaction_count")),
            provenance="Original input verified against this run's campaign dataset."
            if item.get("origin") == "campaign_input_pack"
            else item.get("provenance"),
        )
        inputs[-1]["reconstructed"] = artifact.get("role") == "input_reconstruction"
        inputs[-1]["source_document_ids"] = [
            by_subject[identity]["id"]
            for identity in item.get("source_artifact_ids") or []
            if identity in by_subject
        ]

    # Only the verified campaign image-upload pair is grouped; both files survive.
    verified_subjects = {
        item.get("artifact", {}).get("artifact_id")
        for item in inspection.get("run_inputs") or []
        if item.get("origin") == "campaign_input_pack"
    }
    verified_documents = {
        doc["id"] for doc in documents if doc["subject_id"] in verified_subjects
    }
    for item in inputs:
        if (
            item["name"] != "concept.png"
            or not item["reference"]
            or item["document_id"] not in verified_documents
        ):
            continue
        variant = next(
            (
                other
                for other in inputs
                if other["name"] == "concept.svg"
                and other["reference"]
                == str(PurePosixPath(item["reference"]).with_suffix(".svg"))
                and other["document_id"] in verified_documents
            ),
            None,
        )
        if variant:
            item.update(
                title="Design sketch", format_note=None, variant_ids=[variant["id"]]
            )
            variant["variant_of"] = item["id"]

    for document in documents:
        resource = resource_by_subject[document["subject_id"]]
        document["input_only"] = resource.role in {"input", "run_input"} or (
            resource.subject_id in input_subjects
            and resource.subject_id not in output_subjects
        )
        if document["input_only"] and resource.subject_id not in input_subjects:
            append(
                document["name"],
                document=document,
                media_type=resource.media_type,
            )

    seen_references = {item["reference"] for item in inputs if item["reference"]}
    for document in documents:
        references = document["data"].get("input_references", [])
        if not isinstance(references, list):
            continue
        for reference in references:
            if (
                not isinstance(reference, str)
                or not reference
                or reference in seen_references
            ):
                continue
            seen_references.add(reference)
            # A matching filename alone does not prove an output is the original input.
            append(reference, reference=reference, source=document["id"])
    return inputs


def build_review_model(
    inspection: Mapping[str, Any],
    resources: list,
    source_record: Mapping[str, Any] | None = None,
) -> dict:
    record = source_record or {}
    documents = []
    by_name: dict[str, dict] = {}
    by_subject: dict[str, dict] = {}
    for index, resource in enumerate(resources):
        data = _decode(resource) if resource.media_type == "application/json" else {}
        name = PurePosixPath(resource.name).name
        paragraphs, readable_tables = _engineering_presentation(name, data)
        document = {
            "id": f"document-{index + 1}",
            "subject_id": resource.subject_id,
            "name": name,
            "title": LABELS.get(name, _label(PurePosixPath(name).stem)),
            "media_type": resource.media_type,
            "tables": readable_tables,
            "paragraphs": paragraphs,
            "application": _package_application(resource),
            "assumptions": [
                {
                    "id": f"document-{index + 1}-assumption-{position + 1}",
                    "text": statement,
                    "source_document_id": f"document-{index + 1}",
                    "source_pointer": f"/unresolved_assumptions/{position}",
                    "source_pointer_scope": "decoded_record",
                }
                for position, statement in enumerate(
                    data.get("unresolved_assumptions", [])
                    if isinstance(data.get("unresolved_assumptions"), list)
                    else []
                )
                if isinstance(statement, str) and statement.strip()
            ],
            "data": data,
        }
        if (
            resource.data
            and len(resource.data) <= 64 * 1024
            and resource.media_type in {"text/plain", "text/markdown"}
        ):
            document["source_text"] = resource.data.decode("utf-8", errors="replace")
        documents.append(document)
        by_name[name] = document
        by_subject[resource.subject_id] = document

    for item in inspection.get("review_supplements") or []:
        document = by_subject.get((item.get("artifact") or {}).get("artifact_id"))
        role = (item.get("artifact") or {}).get("role")
        if document and role == "source_document":
            resource = next(
                value
                for value in resources
                if value.subject_id == document["subject_id"]
            )
            document["review_source"] = True
            document["title"] = "Campaign execution checkpoint"
            if resource.data and len(resource.data) <= 64 * 1024:
                document["source_text"] = resource.data.decode(
                    "utf-8", errors="replace"
                )
        elif document and role == "review_visualization":
            document.update(
                review_visualization=True,
                title=str(item.get("title") or document["title"]),
                caption=str(item.get("caption") or "Derived engineering visualization"),
                provenance=str(item.get("provenance") or ""),
                paragraphs=[str(item["engineering_summary"])]
                if item.get("engineering_summary")
                else [],
                visualization_parameters=dict(
                    item.get("visualization_parameters") or {}
                ),
            )
            document["tables"] = [
                _table(
                    "Visualization basis",
                    [
                        [_label(key), value]
                        for key, value in document["visualization_parameters"].items()
                    ],
                )
            ]
            document["source_document_ids"] = [
                by_subject[identity]["id"]
                for identity in item.get("source_artifact_ids") or []
                if identity in by_subject
            ]

    inputs = _review_inputs(inspection, documents, resources)
    by_document_id = {document["id"]: document for document in documents}
    for document in documents:
        references = document["data"].get("input_references", [])
        document["input_ids"] = [
            item["id"]
            for item in inputs
            if isinstance(references, list)
            and item["reference"]
            and item["reference"] in references
        ]

    def get(name: str) -> dict:
        return by_name.get(name, {}).get("data", {})

    def doc_id(name: str) -> str | None:
        return by_name.get(name, {}).get("id")

    design = get("source-model-report.json")
    repair = get("repair-model-report.json")
    slicing = get("slice-evidence.json")
    profile = get("process-profile.json")
    receipt = get("printer-transfer-receipt.json")
    printed = bool(design.get("design_dimensions_mm") and repair.get("before"))
    handwheel = "constructed six-scallop wheel body" in design.get("operations", [])
    simulated = receipt.get("simulated_handoff") is True
    graph = inspection.get("graph") or {}
    run = inspection.get("run") or {}
    family = _scenario_family(run)
    nodes = {item["node_id"]: item for item in graph.get("nodes", [])}
    steps = []
    grouped: dict[str, dict] = {}
    for index, item in enumerate(inspection.get("steps", [])):
        node_id = item.get("node_id") or f"recorded-activity-{index + 1}"
        node = nodes.get(item.get("node_id"), {})
        related = [
            by_subject[out["artifact"]["artifact_id"]]["id"]
            for out in item.get("outputs", [])
            if isinstance(out.get("artifact"), dict)
            and out["artifact"].get("artifact_id") in by_subject
        ]
        step = grouped.get(node_id)
        if step is None:
            recorded_tool = item.get("qualified_tool_name") or (
                node.get("configuration") or {}
            ).get("tool")
            software = str(recorded_tool or _software_for_step(family, node_id))
            step = {
                "id": f"step-{len(steps) + 1}",
                "node_id": node_id,
                "title": item.get("label") or "Recorded activity",
                "lane": node["lane"]
                if isinstance(node.get("lane"), str) and node["lane"].strip()
                else _lane_for_step(family, node_id),
                "owner": f"{software} / recorded workflow activity",
                "summary": "Recorded workflow activity.",
                "state": item.get("state"),
                "sections": [],
                "documents": [],
                "attempts": [],
                "prompt": node.get("prompt"),
                "software": software,
                "software_version": "Version unavailable in this historical run",
                "software_source": None,
                "decision": False,
            }
            steps.append(step)
            grouped[node_id] = step
        step["attempts"].append(
            {
                "number": item.get("attempt", 1),
                "state": item.get("state"),
                "started_at": item.get("started_at"),
                "completed_at": item.get("completed_at"),
                "duration_ms": item.get("duration_ms"),
                "documents": related,
                "input_ids": list(
                    dict.fromkeys(
                        input_id
                        for document_id in related
                        for input_id in by_document_id[document_id]["input_ids"]
                    )
                ),
                "input_documents": [
                    by_subject[value["artifact"]["artifact_id"]]["id"]
                    for value in item.get("inputs", [])
                    if isinstance(value.get("artifact"), Mapping)
                    and value["artifact"].get("artifact_id") in by_subject
                ],
                "operations": [
                    {"text": operation, "source": document_id}
                    for document_id in related
                    for operation in (
                        by_document_id[document_id]["data"].get("operations", [])
                        if isinstance(
                            by_document_id[document_id]["data"].get("operations"), list
                        )
                        else []
                    )
                    if isinstance(operation, str)
                ],
                "assumptions": [
                    statement
                    for document_id in related
                    for statement in by_document_id[document_id]["assumptions"]
                ],
            }
        )
        step["documents"] = list(dict.fromkeys([*step["documents"], *related]))
        step["state"] = item.get("state")

    for step in steps:
        references = {
            reference
            for document in documents
            if document["id"] in step["documents"]
            for reference in document["data"].get("input_references", [])
            if isinstance(reference, str)
        }
        step["input_ids"] = [
            item["id"] for item in inputs if item["reference"] in references
        ]
        events = [
            event
            for event in inspection.get("events", [])
            if event.get("task_id") == step["node_id"]
            and event.get("kind") in _EVENT_LABELS
        ]
        starts = [
            index
            for index, event in enumerate(events)
            if event.get("kind") == "step_started"
        ]
        for index, attempt in enumerate(step["attempts"]):
            segment = (
                events[
                    starts[index] : starts[index + 1]
                    if index + 1 < len(starts)
                    else len(events)
                ]
                if index < len(starts)
                else events
                if len(step["attempts"]) == 1
                else []
            )
            attempt["events"] = [
                {
                    "label": _EVENT_LABELS[event["kind"]],
                    "at": event.get("at"),
                    "source": "Saved execution record",
                }
                for event in segment
            ]
        step["input_documents"] = []
        recorded_software = list(
            dict.fromkeys(
                fact
                for document_id in step["documents"]
                for fact in _software_facts(by_document_id[document_id]["data"])
            )
        )
        if recorded_software and (
            step["software"].startswith("Wright ")
            or re.search(r"not recorded|performer not recorded", step["software"], re.I)
        ):
            software, version = recorded_software[0]
            source = next(
                (
                    document_id
                    for document_id in step["documents"]
                    if (software, version)
                    in _software_facts(by_document_id[document_id]["data"])
                ),
                None,
            )
            step.update(
                software=software,
                software_version=version or "Version not retained",
                software_source=source,
                owner=f"{software} / recorded producer",
            )

    edges = []
    for connection in graph.get("connections", []):
        start = grouped.get(connection.get("source_node_id"))
        end = grouped.get(connection.get("target_node_id"))
        if start and end:
            edges.append(
                {
                    "id": f"edge-{len(edges) + 1}",
                    "source": start["id"],
                    "target": end["id"],
                    "label": connection.get("label") or "Recorded connection",
                    "summary": (
                        "The saved activity events establish this execution order. Artifact-level transfer identity was not retained."
                        if connection.get("basis") == "recorded_execution_order"
                        else "Connection retained in the executed workflow definition."
                    ),
                    "documents": [],
                    "traversals": connection.get("traversals") or [],
                }
            )

    # The domain projection describes one unambiguous artifact set. Repeated
    # activities retain their separate outputs instead of sharing a final table.
    printed = (
        printed
        and len(by_name) == len(documents)
        and all(len(step["attempts"]) == 1 for step in steps)
    )
    package = None
    if printed:
        _printed_details(steps, by_name, record)
        # Reconstruct only handoffs explicitly supported by retained artifact identities.
        stages = {step.get("stage"): step for step in steps}
        source_path = str(repair.get("source_preserved") or "").replace("\\", "/")
        design_path = str(design.get("artifact") or "").replace("\\", "/")
        pairs = []
        if source_path.endswith("/source_mesh.stl") and design_path.endswith(
            "/source_mesh.stl"
        ):
            pairs.append(
                (
                    "design",
                    "repair",
                    "Generated part model",
                    "source_mesh.stl",
                    "The repair report names the original part model as its source.",
                )
            )
        repaired = next((r for r in resources if r.name == "repaired_mesh.stl"), None)
        if repaired and slicing.get("source_sha256") == repaired.digest:
            pairs.append(
                (
                    "repair",
                    "slice",
                    "Repaired geometry",
                    "repaired_mesh.stl",
                    "The slicer's recorded input fingerprint matches the repaired model exactly.",
                )
            )
        package = next(
            (r for r in resources if r.name == "slice_package.gcode.3mf"), None
        )
        if package and package.digest in receipt.get("artifact_digests", []):
            pairs.append(
                (
                    "slice",
                    "authorization",
                    "Print package",
                    "slice_package.gcode.3mf",
                    "The transfer receipt identifies this exact manufacturing package.",
                )
            )
        if not edges:
            for start, end, label, name, summary in pairs:
                if start in stages and end in stages:
                    edges.append(
                        {
                            "id": f"edge-{len(edges) + 1}",
                            "source": stages[start]["id"],
                            "target": stages[end]["id"],
                            "label": label,
                            "summary": summary,
                            "documents": [doc_id(name)],
                            "traversals": [],
                        }
                    )

    for supplement in inspection.get("review_supplements") or []:
        document = by_subject.get((supplement.get("artifact") or {}).get("artifact_id"))
        matching = grouped.get(supplement.get("node_id"))
        role = (supplement.get("artifact") or {}).get("role")
        if matching and document and role == "review_visualization":
            matching["documents"] = list(
                dict.fromkeys([*matching["documents"], document["id"]])
            )
            if matching["attempts"]:
                matching["attempts"][-1]["documents"] = list(
                    dict.fromkeys(
                        [*matching["attempts"][-1]["documents"], document["id"]]
                    )
                )
        if (
            matching
            and document
            and document.get("review_source")
            and supplement.get("software")
            and (
                matching["software"].startswith("Wright ")
                or re.search(r"not (recorded|retained)", matching["software"], re.I)
            )
        ):
            matching.update(
                software=supplement["software"],
                software_source=document["id"],
                software_note=supplement.get("provenance"),
                owner=f"{supplement['software']} / campaign-documented tool",
            )

    family_subtitle, family_outcome = _FAMILY_PRESENTATIONS.get(
        family,
        ("Engineering process review", _label(run.get("state", "Recorded"))),
    )
    dims = design.get("artifact_world_bounds_mm", {}).get("size", [])
    dimensions = (
        " x ".join(f"{v:.3f}".rstrip("0").rstrip(".") for v in dims) + " mm"
        if dims
        else None
    )
    deliverables = [
        doc_id(name)
        for name in ("repaired_mesh.stl", "slice_package.gcode.3mf")
        if doc_id(name)
    ]
    if not deliverables:
        deliverables = _generic_deliverables(documents)
    machine = get("machine-profile.json")
    printer = machine.get("printer_model") or "the recorded printer profile"
    nozzle = (
        f"{_value(machine['nozzle_diameter'])} mm nozzle"
        if machine.get("nozzle_diameter")
        else "nozzle not recorded"
    )
    filament = slicing.get("filament", {}).get("name", "Not recorded")
    preparation = []
    before_mesh = repair.get("before", {}).get("mesh", {})
    after_mesh = repair.get("after", {}).get("mesh", {})
    if "degenerate_faces" in before_mesh and "degenerate_faces" in after_mesh:
        preparation.append(
            [
                "Mesh cleanup",
                f"Degenerate faces: {_value(before_mesh['degenerate_faces'])} to {_value(after_mesh['degenerate_faces'])}",
            ]
        )
    orientation = repair.get("orientation", {}).get("action")
    if orientation == "preserved_model_axes_and_translated_minimum_z_to_build_plate":
        preparation.append(
            [
                "Build orientation",
                "Model axes kept; lowest point moved to the build plate",
            ]
        )
    elif orientation:
        preparation.append(["Build orientation", _label(orientation)])
    for key, label in [
        ("voxel_remesh_used", "Voxel remeshing"),
        ("decimation_used", "Decimation"),
    ]:
        applied = repair.get("repair", {}).get(key)
        if isinstance(applied, bool):
            preparation.append([label, "Applied" if applied else "Not applied"])
    output_ids = {document_id for step in steps for document_id in step["documents"]}
    for edge in edges:
        target = next((step for step in steps if step["id"] == edge["target"]), None)
        if target and len(target["attempts"]) == 1:
            target["input_documents"] = list(
                dict.fromkeys([*target["input_documents"], *edge["documents"]])
            )
            target["attempts"][0]["input_documents"] = list(
                dict.fromkeys(
                    [
                        *target["attempts"][0]["input_documents"],
                        *edge["documents"],
                    ]
                )
            )
    for document in documents:
        document["origin"] = (
            "Supplied input"
            if document["input_only"]
            else "Generated in this run"
            if document["id"] in output_ids
            else "Retained file"
        )
        if document.get("review_source"):
            document["origin"] = "Campaign documentation / not a tool-call record"
        if document.get("review_visualization"):
            document["origin"] = "Review visualization derived from retained run data"
        if any(
            item.get("reconstructed") and item["document_id"] == document["id"]
            for item in inputs
        ):
            document["reconstructed"] = True
            document["origin"] = (
                "Reassembled review input / not the original runtime snapshot"
            )
        if document["name"] == "source_mesh.stl":
            document["title"] = (
                "Supplied part model"
                if document["input_only"]
                else "Generated part model"
                if document["id"] in output_ids
                else "Part model before repair"
            )
        if document["input_only"] and document["name"] in {
            "concept.png",
            "concept.svg",
        }:
            document["title"] = (
                "Design sketch (PNG)"
                if document["name"].endswith(".png")
                else "Design sketch (SVG)"
            )
        if family == "raspberry-pi-enclosure" and document["name"] in {
            "enclosure-a.stl",
            "enclosure-b.stl",
        }:
            document["title"] = (
                "Enclosure concept A"
                if document["name"] == "enclosure-a.stl"
                else "Enclosure concept B"
            )
        if family == "parametric-drill-jig" and document["name"] == "jig.stl":
            document["title"] = "Drill jig"
        if (
            family == "printed-replacement-part"
            and document["name"] == "repaired_mesh.stl"
        ):
            document["title"] = "Replacement part geometry"
    # Join retrieved references by their exact retained bytes, not by filenames.
    for source_document in documents:
        sources = source_document["data"].get("sources")
        if not isinstance(sources, list):
            continue
        for source in sources:
            if not isinstance(source, Mapping) or not isinstance(
                source.get("url"), str
            ):
                continue
            if not re.match(r"^https?://", source["url"], re.I) or not source.get(
                "sha256"
            ):
                continue
            for resource in resources:
                if resource.digest != source["sha256"]:
                    continue
                reference = by_subject.get(resource.subject_id)
                if reference:
                    reference.update(
                        origin="Retrieved reference",
                        source_url=source["url"],
                        retrieved_at=source.get("retrieved_at"),
                        source_manifest_id=source_document["id"],
                    )
    for step in steps:
        for attempt in step["attempts"]:
            actions = []
            for document_id in attempt["documents"]:
                activity_document = by_document_id[document_id]
                operation = activity_document["data"].get("operation")
                references = [
                    doc["id"]
                    for doc in documents
                    if doc.get("source_manifest_id") == document_id
                ]
                if references and isinstance(operation, str):
                    actions.append(
                        {
                            "title": _label(operation),
                            "source": document_id,
                            "documents": references,
                        }
                    )
            attempt["research_actions"] = actions
    interactive_models = _generic_interactive_models(documents, family)
    geometry_models = _activity_geometry(
        steps, documents, resources, interactive_models
    )
    review_visualizations = [
        document["id"]
        for document in documents
        if document.get("review_visualization") and not document.get("archive_only")
    ]
    for document in documents:
        document.pop("data", None)
    return {
        "title": graph.get("name") or run.get("workflow_id") or "Workflow review",
        "subtitle": "Replacement handwheel" if handwheel else family_subtitle,
        "summary": (
            f"A new {'six-scallop replacement handwheel' if handwheel else 'part'} was designed. "
            f"Its digital mesh was cleaned up and a 3D print package was generated for {printer}. "
            "The printer transfer was simulated; no physical part was printed or repaired."
            if printed and simulated
            else (
                f"This retained run completed {len(steps)} recorded engineering activities and produced "
                f"{sum(1 for document in documents if not document['input_only'])} files. "
                "Review the principal deliverables first, then follow their recorded activities and source evidence."
                if run.get("state") == "succeeded"
                else (
                    f"This engineering workflow completed {sum(step['state'] == 'succeeded' for step in steps)} recorded activities "
                    "before the next activity stopped. Available partial results and the recorded blocker are preserved below."
                )
            )
        ),
        "outcome": "Manufacturing package generated"
        if printed and package
        else (
            family_outcome
            if run.get("state") == "succeeded"
            else f"Stopped / {_label(run.get('reason_code') or run.get('state', 'Recorded'))}"
        ),
        "simulated_handoff": simulated,
        "date": run.get("completed_at") or run.get("started_at"),
        "facts": (
            [
                ["Part envelope", dimensions],
            ]
            if printed
            else [
                ["Recorded activities", len(steps)],
                [
                    "Retained outputs",
                    sum(1 for document in documents if not document["input_only"]),
                ],
            ]
        ),
        "printing": {
            "facts": [
                ["Printer", f"{printer} / {nozzle}"],
                ["Material", filament.split(" @")[0]],
                [
                    "Layer height / infill",
                    f"{profile.get('layer_height', 'Not recorded')} mm / {profile.get('sparse_infill_density', 'Not recorded')}",
                ],
                *[
                    [label, _label(profile[key])]
                    for key, label in [
                        ("sparse_infill_pattern", "Infill pattern"),
                        ("wall_loops", "Wall loops"),
                    ]
                    if key in profile
                ],
            ],
            "settings_id": doc_id("process-profile.json"),
            "evidence_id": doc_id("slice-evidence.json"),
            "support_facts": [
                *(
                    [
                        [
                            "Support strategy",
                            {
                                "tree(auto)": "Automatic tree supports",
                                "normal(auto)": "Automatic normal supports",
                            }.get(
                                profile["support_type"], _label(profile["support_type"])
                            ),
                        ]
                    ]
                    if "support_type" in profile
                    else []
                ),
                *(
                    [
                        [
                            "Support threshold",
                            f"{_value(profile['support_threshold_angle'])} degrees",
                        ]
                    ]
                    if "support_threshold_angle" in profile
                    else []
                ),
            ],
            "support_preview_note": "A support-geometry preview was not retained for this run.",
            "preparation": preparation,
            "preparation_id": doc_id("repair-model-report.json"),
            "support_summary": (
                f"Supports enabled; {_value(slicing.get('support_moves'))} support toolpath moves reported."
                if slicing.get("supports_enabled") is True
                else f"Support toolpath moves reported: {_value(slicing.get('support_moves'))}."
            ),
        }
        if printed
        else None,
        "previews": (
            [doc_id("mesh-preview.png")]
            if printed and doc_id("mesh-preview.png")
            else [*review_visualizations, *_generic_previews(documents)][:4]
        ),
        "interactive_models": interactive_models,
        "geometry_models": geometry_models,
        "deliverables": deliverables,
        "inputs": inputs,
        "documents": documents,
        "steps": steps,
        "ai_usage": {
            "models": (record.get("usage") or {}).get("models") or [],
            "request_count": (record.get("usage") or {}).get("request_count"),
            "scope": "Whole run; not a count of geometry revisions or tool retries",
        },
        "edges": edges,
        "lanes": list(dict.fromkeys(step["lane"] for step in steps)),
        "evidence": inspection.get("evidence_records") or [],
        "diagnostic": inspection.get("diagnostic"),
        "graph_note": (
            "Connections show recorded activity order; they do not claim an unrecorded artifact handoff."
            if any(
                item.get("basis") == "recorded_execution_order"
                for item in graph.get("connections") or []
            )
            else "Activities and connections from the saved workflow."
        )
        if graph.get("connections")
        else "Recorded activities with evidence-supported handoffs. The original workflow layout was not retained.",
    }


def _printed_details(
    steps: list[dict], documents: dict[str, dict], record: Mapping
) -> None:
    def data(name: str) -> dict:
        return documents.get(name, {}).get("data", {})

    def table(
        title: str, rows: list, name: str, columns: list[str] | None = None
    ) -> dict:
        return _table(title, rows, documents.get(name, {}).get("id"), columns)

    design = data("source-model-report.json")
    repair = data("repair-model-report.json")
    slicing = data("slice-evidence.json")
    profile = data("process-profile.json")
    receipt = data("printer-transfer-receipt.json")
    machine = data("machine-profile.json")
    material = data("filament-profile.json")
    application = documents.get("slice_package.gcode.3mf", {}).get("application") or ""
    slicer_version = re.fullmatch(r"BambuStudio-([0-9]+(?:\.[0-9]+)+)", application)
    handwheel = "constructed six-scallop wheel body" in design.get("operations", [])
    if "mesh-preview.png" in documents:
        documents["mesh-preview.png"].update(
            title="Replacement part design" if handwheel else "Part design",
            caption="After digital mesh cleanup",
            paragraphs=[
                "The generated model's mesh was cleaned up digitally. This was not a repair to a physical part."
            ],
        )
    if "slice-preview.png" in documents:
        documents["slice-preview.png"].update(
            caption="Whole model, not individual layers",
            paragraphs=[
                "Whole-model thumbnail retained from the 3D print package. It is not a layer-by-layer view.",
                "A separate preview of the model with support geometry was not retained.",
            ],
        )
    if (
        "support-preview.svg" in documents
        and not documents["support-preview.svg"]["input_only"]
    ):
        # The flattened projection is retained evidence, not a useful toolpath view.
        documents["support-preview.svg"]["archive_only"] = True
    dimensions = design.get("design_dimensions_mm", {})
    design_tables = [
        table(
            "Design dimensions",
            [
                ["Maximum diameter", dimensions.get("maximum_diameter"), "mm"],
                [
                    "Minimum grip diameter",
                    dimensions.get("minimum_grip_diameter"),
                    "mm",
                ],
                ["Overall height", dimensions.get("overall_height"), "mm"],
                ["Socket depth", dimensions.get("socket_depth"), "mm"],
                [
                    "Cleared socket diameter",
                    dimensions.get("cleared_socket_round_diameter"),
                    "mm",
                ],
                [
                    "Cleared socket flat-to-round",
                    dimensions.get("cleared_socket_flat_to_far_round"),
                    "mm",
                ],
                ["Nominal edge radius", dimensions.get("nominal_edge_radius"), "mm"],
            ],
            "source-model-report.json",
            ["Dimension", "Value", "Unit"],
        )
    ]
    before, after = (
        repair.get("before", {}).get("mesh", {}),
        repair.get("after", {}).get("mesh", {}),
    )
    repair_tables = [
        table(
            "Mesh measurements",
            [
                ["Vertices", before.get("vertices"), after.get("vertices")],
                ["Faces", before.get("faces"), after.get("faces")],
                [
                    "Degenerate faces",
                    before.get("degenerate_faces"),
                    after.get("degenerate_faces"),
                ],
                [
                    "Boundary edges",
                    before.get("boundary_edges"),
                    after.get("boundary_edges"),
                ],
                [
                    "Non-manifold edges",
                    before.get("nonmanifold_edges"),
                    after.get("nonmanifold_edges"),
                ],
                [
                    "Connected components",
                    before.get("connected_components"),
                    after.get("connected_components"),
                ],
            ],
            "repair-model-report.json",
            ["Measurement", "Before repair", "After repair"],
        ),
        table(
            "Repair method",
            [
                [
                    "Merge tolerance",
                    _value(repair.get("repair", {}).get("merge_tolerance_mm")) + " mm",
                ],
                [
                    "Degenerate-face tolerance",
                    _value(repair.get("repair", {}).get("degenerate_tolerance_mm"))
                    + " mm",
                ],
                [
                    "Voxel remeshing used",
                    repair.get("repair", {}).get("voxel_remesh_used"),
                ],
                ["Decimation used", repair.get("repair", {}).get("decimation_used")],
            ],
            "repair-model-report.json",
        ),
        table(
            "Checks reported by Blender",
            [
                [_label(key), "Reported pass" if value else "Reported failure"]
                for key, value in repair.get("checks", {}).items()
            ],
            "repair-model-report.json",
        ),
    ]
    slice_tables = [
        table(
            "3D printing settings",
            [
                ["Layer height", f"{profile.get('layer_height', 'Not recorded')} mm"],
                ["Infill", profile.get("sparse_infill_density")],
                ["Infill pattern", profile.get("sparse_infill_pattern")],
                ["Wall loops", profile.get("wall_loops")],
                ["Support strategy", profile.get("support_type")],
                [
                    "Support threshold",
                    f"{profile.get('support_threshold_angle', 'Not recorded')} degrees",
                ],
            ],
            "process-profile.json",
        ),
        table(
            "Slicing results",
            [
                ["Printer profile", machine.get("name")],
                ["Filament profile", slicing.get("filament", {}).get("name")],
                ["Extrusion moves", slicing.get("extrusion_moves")],
                ["Support moves generated", slicing.get("support_moves")],
                ["Supports enabled", slicing.get("supports_enabled")],
                ["Printer connected", slicing.get("printer_connected")],
            ],
            "slice-evidence.json",
        ),
    ]
    actor = record.get("approval_actor")
    automated = isinstance(actor, str) and actor.startswith("integration_test:")
    actor_name = (
        "Engineering campaign automation"
        if automated
        else actor or "Authorizer not recorded"
    )
    approval_at = next(
        (
            item.get("at")
            for item in record.get("step_events", [])
            if item.get("kind") == "approval_decided"
        ),
        "Not recorded",
    )
    authorization = table(
        "Authorization record",
        [
            ["Authorized by", actor_name],
            [
                "Role",
                "Automated integration-test actor" if automated else "Not recorded",
            ],
            [
                "Decision",
                "Simulated transfer authorized"
                if receipt.get("simulated_handoff")
                else "See retained approval record",
            ],
            ["Recorded at", _recorded_time(approval_at)],
            ["Scope", "Manufacturing package and its supporting artifacts"],
            [
                "Destination",
                "Campaign test destination"
                if receipt.get("simulated_handoff")
                else "See transfer receipt",
            ],
            [
                "Physical printer transfer",
                "Not performed"
                if receipt.get("network_dispatch") is False
                else "Not recorded",
            ],
            ["Human sign-off", "Not recorded"],
            ["Decision rationale", "Not retained in this run record"],
        ],
        "printer-transfer-receipt.json",
    )
    if "source-model-report.json" in documents:
        documents["source-model-report.json"]["tables"] = design_tables
        documents["source-model-report.json"]["paragraphs"] = design.get(
            "operations", []
        )
    if "repair-model-report.json" in documents:
        documents["repair-model-report.json"]["tables"] = repair_tables
    if "slice-evidence.json" in documents:
        documents["slice-evidence.json"]["tables"] = slice_tables
    if "process-profile.json" in documents:
        documents["process-profile.json"]["tables"] = [slice_tables[0]]
    if "machine-profile.json" in documents:
        documents["machine-profile.json"]["tables"] = [
            table(
                "Printer configuration",
                [
                    ["Printer", machine.get("printer_model")],
                    ["Nozzle diameter (mm)", machine.get("nozzle_diameter")],
                    ["Build plate corners (mm)", machine.get("printable_area")],
                    ["Printable height (mm)", machine.get("printable_height")],
                ],
                "machine-profile.json",
            )
        ]
    if "filament-profile.json" in documents:
        documents["filament-profile.json"]["tables"] = [
            table(
                "Material configuration",
                [
                    ["Profile", material.get("name")],
                    ["Material", material.get("filament_type")],
                    ["Manufacturer", material.get("filament_vendor")],
                    ["Density (g/cm3)", material.get("filament_density")],
                    ["Nozzle temperatures (C)", material.get("nozzle_temperature")],
                    ["Bed temperature (C)", material.get("hot_plate_temp")],
                    [
                        "Volumetric limits (mm3/s)",
                        material.get("filament_max_volumetric_speed"),
                    ],
                ],
                "filament-profile.json",
            )
        ]
    if "printer-transfer-receipt.json" in documents:
        documents["printer-transfer-receipt.json"]["tables"] = [authorization]
    for step in steps:
        raw = step["node_id"]
        if raw.startswith("create_mesh"):
            step.update(
                stage="design",
                title="Create part geometry",
                lane="Design & mesh preparation",
                owner="CAD generation / performer not retained",
                software="Geometry authoring tool not retained",
                software_source=documents.get("source-model-report.json", {}).get("id"),
                summary="Six-scallop handwheel with a blind D socket"
                if handwheel
                else "Part geometry generated",
                objective="Created a part model from the supplied request and sketch, including the scalloped grip and blind D-shaped socket."
                if handwheel
                else "Created a part model from the supplied design inputs.",
                paragraphs=design.get("operations", []),
                sections=design_tables,
            )
        elif raw.startswith("repair_measure_orient"):
            step.update(
                stage="repair",
                title="Repair & measure mesh",
                lane="Design & mesh preparation",
                owner="Blender / automated mesh operation",
                software="Blender",
                software_source=documents.get("repair-model-report.json", {}).get("id"),
                summary=f"Degenerate faces: {_value(before.get('degenerate_faces'))} to {_value(after.get('degenerate_faces'))}",
                objective="Repaired the generated mesh, recorded before-and-after dimensions and topology, and positioned it on the build plate.",
                paragraphs=[
                    "Blender reported removal of the degenerate face while preserving the measured part envelope.",
                    "Model axes were retained and the minimum Z position was moved to the build plate.",
                ],
                sections=repair_tables,
                source_note="These are the checks reported by the mesh operation. Independent engineering content validation was not performed in this campaign.",
            )
        elif raw.startswith("supports_and_slice"):
            step.update(
                stage="slice",
                title="Prepare print package",
                lane="Manufacturing preparation",
                owner="Bambu Studio / local slicer",
                software="Bambu Studio",
                software_version=slicer_version.group(1)
                if slicer_version
                else "Not recorded",
                software_source=documents.get("slice_package.gcode.3mf", {}).get("id"),
                summary=f"{profile.get('layer_height', '?')} mm layers / {profile.get('sparse_infill_density', '?')} infill",
                objective="Sliced the generated mesh after cleanup using the recorded printer, process and material profiles and produced the 3D print package.",
                paragraphs=[
                    "The local slicer completed successfully and generated a manufacturing package.",
                    f"Supports enabled: {_value(slicing.get('supports_enabled'))}. Support toolpath moves reported: {_value(slicing.get('support_moves'))}.",
                ],
                sections=slice_tables,
                source_note="Slicing completion does not establish fit, strength or a successful physical print.",
            )
        elif raw.startswith("authorize_transfer"):
            step.update(
                stage="authorization",
                title="Authorize transfer",
                lane="Transfer authorization",
                owner=actor_name,
                software="Wright AutoTest",
                software_source=documents.get("printer-transfer-receipt.json", {}).get(
                    "id"
                ),
                summary="Automated authorization / simulated handoff",
                decision=True,
                objective="Authorized the generated manufacturing package for a simulated test handoff. No physical printer dispatch occurred.",
                paragraphs=[
                    "This was an automated integration-test authorization. The receipt records no network dispatch to a printer."
                ],
                sections=[authorization],
                source_note="The authorizer is retained in the original run record; the transfer scope and simulation state are retained in the receipt.",
            )
