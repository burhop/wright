import io
import base64
import hashlib
import json
import re
import zipfile

import pytest

from workspace_service.workflow_trace.export import (
    TraceExportResource,
    build_trace_export,
)


INSPECTION = {
    "run": {
        "run_id": "run-1",
        "workflow_id": "workflow-1",
        "revision": 2,
        "state": "succeeded",
    },
    "final_outputs": [
        {
            "result_id": "artifact:a",
            "name": "same.step",
            "preview": "STEP",
            "artifact": {"artifact_id": "a"},
        },
        {
            "result_id": "artifact:b",
            "name": "same.step",
            "preview": "STEP",
            "artifact": {"artifact_id": "b"},
        },
    ],
    "steps": [],
    "run_inputs": [],
}


def package(mode="full_data", resources=()):
    return build_trace_export(
        inspection=INSPECTION,
        evidence={"run_id": "run-1", "artifacts": []},
        mode=mode,
        resources=resources,
    )


def test_full_export_disambiguates_repeated_names_and_uses_relative_links() -> None:
    resources = (
        TraceExportResource("a", "same.step", "model/step", b"first", None),
        TraceExportResource("b", "same.step", "model/step", b"second", None),
    )
    with zipfile.ZipFile(io.BytesIO(package(resources=resources))) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        paths = [entry["package_path"] for entry in manifest["entries"]]
        assert len(set(paths)) == 2
        assert all(path and not path.startswith("/") for path in paths)
        html = archive.read("index.html").decode()
        assert "connect-src 'none'" in html
        assert "file-origin" not in html


def test_report_only_marks_originals_omitted_without_broken_links() -> None:
    resource = TraceExportResource("a", "part.stl", "model/stl", b"mesh", None)
    with zipfile.ZipFile(io.BytesIO(package("report_only", (resource,)))) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["entries"][0]["availability"] == "omitted_from_export"
        assert manifest["entries"][0]["package_path"] is None
        assert archive.namelist() == [
            "index.html",
            "manifest.json",
            "report/report.json",
            "evidence/run-evidence.json",
            "assets/licenses/DOCUMENT-LICENSES.txt",
        ]
        assert archive.read("index.html").decode().count("WrightSTLViewer") == 2


def test_report_only_includes_self_contained_visual_assets() -> None:
    resource = TraceExportResource(
        "a",
        "preview.png",
        "image/png",
        b"retained-preview",
        None,
        report_asset=True,
    )
    with zipfile.ZipFile(io.BytesIO(package("report_only", (resource,)))) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        entry = manifest["entries"][0]
        assert entry["availability"] == "included"
        assert entry["package_path"] == "assets/previews/preview.png"
        assert archive.read(entry["package_path"]) == b"retained-preview"
        html = archive.read("index.html").decode()
        assert 'class="image-frame"' in html
        assert 'src="${esc(localPath(item))}"' in html


@pytest.mark.parametrize("mode", ["full_data", "report_only"])
def test_cfd_review_visualization_is_promoted_and_attached_to_its_activity(
    mode,
) -> None:
    inspection = {
        **INSPECTION,
        "run": {**INSPECTION["run"], "workflow_id": "raspberry-pi-enclosure-01"},
        "graph": {
            "name": "Raspberry Pi Enclosure 01",
            "nodes": [{"node_id": "collect_cfd_results"}],
            "connections": [],
        },
        "final_outputs": [],
        "steps": [
            {
                "node_id": "collect_cfd_results",
                "label": "Collect CFD results",
                "state": "succeeded",
                "attempt": 1,
                "outputs": [
                    {
                        "artifact": {"artifact_id": "comparison"},
                    },
                    {
                        "artifact": {"artifact_id": "fields"},
                    },
                ],
            }
        ],
        "review_supplements": [
            {
                "name": "velocity-comparison.png",
                "node_id": "collect_cfd_results",
                "title": "Airflow comparison",
                "caption": "Shared air-speed scale for both variants.",
                "provenance": "Derived from retained VTK fields.",
                "engineering_summary": "Actual computed fields; exploratory run.",
                "visualization_parameters": {
                    "field": "Air speed",
                    "slice_plane": "z = 22 mm",
                },
                "source_artifact_ids": ["comparison", "fields"],
                "artifact": {
                    "artifact_id": "velocity-visual",
                    "role": "review_visualization",
                },
            }
        ],
    }
    resources = (
        TraceExportResource(
            "comparison",
            "cfd-comparison.json",
            "application/json",
            b"{}",
            None,
        ),
        TraceExportResource(
            "fields", "cfd-fields.zip", "application/zip", b"fields", None
        ),
        TraceExportResource(
            "velocity-visual",
            "velocity-comparison.png",
            "image/png",
            b"png",
            None,
            role="review_visualization",
            report_asset=True,
        ),
    )

    with zipfile.ZipFile(
        io.BytesIO(
            build_trace_export(
                inspection=inspection,
                evidence={},
                mode=mode,
                resources=resources,
            )
        )
    ) as archive:
        review = _review(archive)
        visual = next(
            item
            for item in review["documents"]
            if item["subject_id"] == "velocity-visual"
        )
        assert visual["title"] == "Airflow comparison"
        assert visual["review_visualization"] is True
        assert visual["source_document_ids"] == ["document-1", "document-2"]
        assert visual["id"] in review["previews"]
        assert visual["id"] in review["steps"][0]["documents"]
        assert archive.read("evidence/visualizations/velocity-comparison.png") == b"png"
        html = archive.read("index.html").decode()
        assert "Engineering visualizations" in html
        assert "visualization-provenance" in html


def test_export_preserves_external_unavailability_and_rejects_integrity_mismatch() -> (
    None
):
    external = TraceExportResource(
        "external-1",
        "cloud-result",
        "application/octet-stream",
        None,
        None,
        availability="external",
    )
    with zipfile.ZipFile(io.BytesIO(package(resources=(external,)))) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["entries"][0]["availability"] == "external"
    with pytest.raises(ValueError, match="digest mismatch"):
        package(
            resources=(
                TraceExportResource("a", "part.stl", "model/stl", b"mesh", "0" * 64),
            )
        )


def _model(archive):
    html = archive.read("index.html").decode()
    model = re.search(
        r'<script id="wright-trace-data" type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    return json.loads(model.group(1))


def _review(archive):
    return _model(archive)["review"]


@pytest.mark.parametrize("mode", ["full_data", "report_only"])
def test_pdf_viewer_embeds_only_included_originals_with_offline_licenses(mode):
    content = b"%PDF-1.4\nretained drawing bytes"
    resource = TraceExportResource(
        "pdf", "drawing.pdf", "application/pdf", content, None
    )
    with zipfile.ZipFile(io.BytesIO(package(mode, (resource,)))) as archive:
        model = _model(archive)
        manifest = json.loads(archive.read("manifest.json"))
        assert len(manifest["entries"]) == 1
        if mode == "full_data":
            payload = model["viewerDocuments"]["document-1"]
            assert base64.b64decode(payload["base64"]) == content
            assert payload["digest"] == hashlib.sha256(content).hexdigest()
            assert archive.read(manifest["entries"][0]["package_path"]) == content
            assert (
                manifest["viewer_capabilities"]["pdf"] == "interactive-offline-viewer"
            )
            assert "assets/licenses/PDFJS-LICENSE.txt" in archive.namelist()
        else:
            assert not model["viewerDocuments"]
            assert (
                "not included"
                in model["review"]["documents"][0]["viewer_unavailable_reason"]
            )
            assert "assets/licenses/PDFJS-LICENSE.txt" not in archive.namelist()
        for license in manifest["viewer_licenses"]:
            assert (
                hashlib.sha256(archive.read(license["package_path"])).hexdigest()
                == license["digest"]
            )


def test_pdf_viewer_bounds_size_but_preserves_the_download():
    content = b"%PDF-1.4" + b" " * (16 * 1024 * 1024)
    resource = TraceExportResource("pdf", "large.pdf", "application/pdf", content, None)
    with zipfile.ZipFile(io.BytesIO(package(resources=(resource,)))) as archive:
        model = _model(archive)
        assert not model["viewerDocuments"]
        assert (
            "size limit" in model["review"]["documents"][0]["viewer_unavailable_reason"]
        )
        assert archive.read("outputs/output/large.pdf") == content


def test_retrieved_document_provenance_requires_matching_bytes_and_keeps_research_text():
    content = b"%PDF-1.4 retained drawing"
    digest = hashlib.sha256(content).hexdigest()
    evidence = json.dumps(
        {
            "operation": "retrieve_manufacturer_sources",
            "sources": [
                {
                    "path": "drawing.pdf",
                    "sha256": digest,
                    "url": "https://example.com/drawing.pdf",
                    "retrieved_at": "2026-09-13T13:20:00Z",
                }
            ],
        }
    ).encode()
    resources = (
        TraceExportResource("pdf", "drawing.pdf", "application/pdf", content, digest),
        TraceExportResource(
            "wrong",
            "drawing.pdf",
            "application/pdf",
            b"other revision",
            hashlib.sha256(b"other revision").hexdigest(),
        ),
        TraceExportResource(
            "research",
            "research.md",
            "text/markdown",
            b"# Design basis\n\nBoard width: 85 mm.",
            None,
        ),
        TraceExportResource(
            "source", "sources.json", "application/json", evidence, None
        ),
    )
    payload = build_trace_export(
        inspection={
            **INSPECTION,
            "steps": [
                {
                    "node_id": "research",
                    "label": "Source dimensions",
                    "state": "succeeded",
                    "attempt": 1,
                    "outputs": [{"artifact": {"artifact_id": "source"}}],
                }
            ],
        },
        evidence={},
        mode="full_data",
        resources=resources,
        source_record={"usage": {"models": ["retained-model"], "request_count": 4}},
    )
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        review = _review(archive)
        documents = review["documents"]
        assert documents[0]["origin"] == "Retrieved reference"
        assert documents[0]["source_url"] == "https://example.com/drawing.pdf"
        assert documents[0]["source_manifest_id"] == documents[3]["id"]
        assert "source_url" not in documents[1]
        assert "Board width: 85 mm." in documents[2]["source_text"]
        assert review["ai_usage"]["request_count"] == 4
        assert review["ai_usage"]["models"] == ["retained-model"]
        assert review["steps"][0]["attempts"][0]["research_actions"][0][
            "documents"
        ] == [documents[0]["id"]]


def test_report_embeds_visual_input_and_only_principal_enclosure_geometry() -> None:
    inspection = {
        **INSPECTION,
        "run": {
            **INSPECTION["run"],
            "workflow_id": "raspberry-pi-enclosure-01",
            "state": "succeeded",
        },
        "graph": {"name": "Raspberry Pi Enclosure 01", "nodes": []},
        "run_inputs": [
            {
                "name": "concept.png",
                "kind": "artifact",
                "value": "inputs/concept.png",
                "origin": "campaign_input_pack",
                "artifact": {"artifact_id": "concept"},
            }
        ],
    }
    resources = (
        TraceExportResource(
            "concept",
            "concept.png",
            "image/png",
            b"sketch",
            None,
            role="input",
            report_asset=True,
        ),
        TraceExportResource(
            "enclosure-a", "enclosure-a.stl", "model/stl", b"solid a", None
        ),
        TraceExportResource(
            "enclosure-b", "enclosure-b.stl", "model/stl", b"solid b", None
        ),
        TraceExportResource(
            "fluid-domain", "fluid-domain-a.stl", "model/stl", b"solid fluid", None
        ),
        TraceExportResource(
            "cad-inspection",
            "cad-export-inspection.json",
            "application/json",
            json.dumps(
                {
                    "summary": (
                        "No mismatch was found. Unresolved lineage remains for "
                        "feet-a.step because it was outside the authorized inspection set."
                    ),
                    "observations": [
                        {
                            "path": "enclosure-a.step",
                            "bytes": 460403,
                            "sha256": "a" * 64,
                        },
                        {
                            "path": "enclosure-a.stl",
                            "bytes": 641084,
                            "sha256": "b" * 64,
                        },
                        {
                            "path": "cfd-contract-a.json",
                            "bytes": 4123,
                            "sha256": "c" * 64,
                        },
                    ],
                }
            ).encode(),
            None,
        ),
    )
    encoded = build_trace_export(
        inspection=inspection,
        evidence={},
        mode="report_only",
        resources=resources,
    )
    with zipfile.ZipFile(io.BytesIO(encoded)) as archive:
        model = _model(archive)
        review = model["review"]
        titles = {document["id"]: document["title"] for document in review["documents"]}
        assert [titles[item] for item in review["interactive_models"]] == [
            "Enclosure concept A",
            "Enclosure concept B",
        ]
        assert set(model["viewerModels"]) == set(review["interactive_models"])
        assert archive.read("index.html").decode().count("WrightSTLViewer") == 3
        assert all(
            titles[item] != "Fluid domain a" for item in review["interactive_models"]
        )
        assert review["inputs"][0]["document_id"] is not None
        inspection_record = next(
            document
            for document in review["documents"]
            if document["name"] == "cad-export-inspection.json"
        )
        assert inspection_record["tables"][0]["title"] == "CAD export verification"
        assert inspection_record["tables"][1]["collapsed"] is True
        assert not any(
            "Bytes" in cell
            for table in inspection_record["tables"]
            for row in table["rows"]
            for cell in row
        )
        assert archive.read("assets/previews/concept.png") == b"sketch"
        assert model["manifest"]["viewer_capabilities"] == {
            "stl": "interactive-offline-viewer",
            "step": "recorded-preview-and-original-when-available",
            "3mf": "recorded-preview-and-original-when-available",
            "interactive_viewer_bundled": True,
            "pdf": "original-file-when-available",
        }


def test_geometry_is_available_per_occurrence_without_promoting_all_models_to_results():
    resources = (
        TraceExportResource(
            "source-a", "source_mesh.stl", "model/stl", b"first mesh", None
        ),
        TraceExportResource(
            "source-b", "source_mesh.stl", "model/stl", b"second mesh", None
        ),
        TraceExportResource(
            "domain", "fluid-domain-a.stl", "model/stl", b"domain", None
        ),
    )
    inspection = {
        **INSPECTION,
        "steps": [
            {
                "node_id": "geometry",
                "state": "succeeded",
                "attempt": index + 1,
                "outputs": [{"artifact": {"artifact_id": name}}],
            }
            for index, name in enumerate(["source-a", "source-b", "domain"])
        ],
    }
    with zipfile.ZipFile(
        io.BytesIO(
            build_trace_export(
                inspection=inspection,
                evidence={},
                mode="full_data",
                resources=resources,
            )
        )
    ) as archive:
        model = _model(archive)
        review = model["review"]
        assert not review["interactive_models"]
        assert len(model["viewerModels"]) == 3
        assert [
            [value["document_id"] for value in attempt["geometry"]]
            for attempt in review["steps"][0]["attempts"]
        ] == [["document-1"], ["document-2"], ["document-3"]]
        assert all(
            value["relation"] == "produced"
            for attempt in review["steps"][0]["attempts"]
            for value in attempt["geometry"]
        )


@pytest.mark.parametrize("authoring_passes", [1, 2])
def test_authoring_geometry_is_later_context_not_a_fabricated_stage_output(
    authoring_passes,
):
    mesh = b"retained mesh"
    digest = hashlib.sha256(mesh).hexdigest()
    resources = (
        TraceExportResource(
            "source",
            "enclosure-source.py",
            "text/x-python",
            b"never execute this",
            None,
        ),
        TraceExportResource(
            "author",
            "cad-authoring.json",
            "application/json",
            b'{"summary":"Source was authored; not executed by this step."}',
            None,
        ),
        TraceExportResource("model", "enclosure-a.stl", "model/stl", mesh, digest),
        TraceExportResource(
            "inspection",
            "cad-export-inspection.json",
            "application/json",
            json.dumps(
                {"observations": [{"path": "enclosure-a.stl", "sha256": digest}]}
            ).encode(),
            None,
        ),
    )

    def activity(node, outputs, attempt=1):
        return {
            "node_id": node,
            "label": node,
            "state": "succeeded",
            "attempt": attempt,
            "outputs": [{"artifact": {"artifact_id": item}} for item in outputs],
        }

    inspection = {
        **INSPECTION,
        "steps": [
            *[
                activity("author_cad", ["source", "author"], index + 1)
                for index in range(authoring_passes)
            ],
            activity("agentcad", ["model"]),
            activity("inspect_cad", ["inspection"]),
        ],
        "graph": {
            "nodes": [
                {"node_id": name, "lane": "CAD engineering"}
                for name in ["author_cad", "agentcad", "inspect_cad"]
            ]
        },
    }
    with zipfile.ZipFile(
        io.BytesIO(
            build_trace_export(
                inspection=inspection,
                evidence={},
                mode="full_data",
                resources=resources,
            )
        )
    ) as archive:
        review = _review(archive)
        author, producer, inspection = review["steps"]
        assert author["documents"] == ["document-1", "document-2"]
        if authoring_passes == 1:
            geometry = author["attempts"][0]["geometry"][0]
            assert geometry["relation"] == "later_run_result"
            assert geometry["step_id"] == producer["id"]
            assert geometry["document_id"] == "document-3"
            assert (
                "not captured during source authoring"
                in author["attempts"][0]["geometry_note"]
            )
        else:
            assert not any(attempt["geometry"] for attempt in author["attempts"])
        assert inspection["attempts"][0]["geometry"][0]["relation"] == "inspected"
        assert inspection["attempts"][0]["geometry"][0]["source_id"] == "document-4"


@pytest.mark.parametrize("mode", ["report_only", "full_data"])
def test_campaign_original_prompt_is_exported_and_linked_to_consuming_activity(mode):
    import hashlib
    from workspace_service.workflow_trace.canonical import (
        build_canonical_trace,
        canonical_artifact_paths,
    )

    prompt = b"Create a six-scallop wheel with a 6 mm D shaft."
    reference = "campaign/example-01/attempt-003/inputs/prompt.txt"
    record = {
        "schema_version": 1,
        "scenario_id": "example-01",
        "attempt_id": "attempt-003",
        "dataset_digest": "d" * 64,
        "status": "completed",
        "run_id": "run-1",
        "required_step_ids": ["create_mesh"],
        "step_events": [{"kind": "step_completed", "task_id": "create_mesh"}],
        "produced_files": [
            {"path": "design.json", "artifact_id": "design", "task_id": "create_mesh"}
        ],
        "trace_input_pack": {
            "dataset_digest": "d" * 64,
            "input_hashes": {"prompt.txt": hashlib.sha256(prompt).hexdigest()},
            "files": [
                {
                    "path": "prompt.txt",
                    "reference": reference,
                    "artifact_id": "original-prompt",
                    "sha256": hashlib.sha256(prompt).hexdigest(),
                    "size_bytes": len(prompt),
                }
            ],
        },
    }
    inspection = build_canonical_trace(
        record,
        workspace_id="w",
        session_id="s",
        path="runs/example-01/attempt-003.json",
    )
    artifact = next(
        a for a in canonical_artifact_paths(inspection) if a["role"] == "input"
    )
    assert artifact["workspace_path"] == "runs/example-01/inputs/attempt-003/prompt.txt"
    assert inspection["graph"]["nodes"][0]["prompt"] is None
    encoded = build_trace_export(
        inspection=inspection,
        evidence={},
        mode=mode,
        resources=[
            TraceExportResource(
                "original-prompt",
                "prompt.txt",
                "text/plain",
                prompt,
                hashlib.sha256(prompt).hexdigest(),
                role="input",
            ),
            TraceExportResource(
                "design",
                "design.json",
                "application/json",
                json.dumps({"input_references": [reference]}).encode(),
                None,
            ),
        ],
    )
    with zipfile.ZipFile(io.BytesIO(encoded)) as archive:
        review = _review(archive)
        assert len(review["inputs"]) == 1
        assert review["inputs"][0]["text"] == prompt.decode()
        assert "verified against" in review["inputs"][0]["provenance"]
        assert review["steps"][0]["input_ids"] == [review["inputs"][0]["id"]]
        assert review["documents"][0]["input_only"] is True
        if mode == "full_data":
            assert archive.read("inputs/prompt.txt") == prompt
        else:
            assert "inputs/prompt.txt" not in archive.namelist()
    record["trace_input_pack"]["dataset_digest"] = "f" * 64
    assert not build_canonical_trace(
        record,
        workspace_id="w",
        session_id="s",
        path="runs/example-01/attempt-003.json",
    )["run_inputs"]


def test_report_only_projects_json_into_readable_tables_without_raw_code() -> None:
    resource = TraceExportResource(
        "record",
        "measurement.json",
        "application/json",
        json.dumps(
            {
                "diameter_mm": 38,
                "boundary_edges": 0,
                "machine_start_gcode": "M400 U1",
                "artifact_id": "opaque-identity",
            }
        ).encode(),
        None,
    )
    with zipfile.ZipFile(io.BytesIO(package("report_only", (resource,)))) as archive:
        review = _review(archive)
        rows = review["documents"][0]["tables"][0]["rows"]
        assert ["Diameter mm", "38"] in rows
        assert ["Boundary edges", "0"] in rows
        assert not any("gcode" in row[0] or "identity" in row[1] for row in rows)
        assert "data" not in review["documents"][0]
        assert not any(name.startswith("outputs/") for name in archive.namelist())


def test_mcp_report_is_unwrapped_and_interpreted_bytes_are_integrity_checked() -> None:
    payload = json.dumps(
        {"content": [{"type": "text", "text": json.dumps({"volume_mm3": 15862.6})}]}
    ).encode()
    resource = TraceExportResource(
        "record", "measurements.json", "application/json", payload, None
    )
    with zipfile.ZipFile(io.BytesIO(package("report_only", (resource,)))) as archive:
        assert _review(archive)["documents"][0]["tables"][0]["rows"] == [
            ["Volume mm3", "15,862.6"]
        ]
    with pytest.raises(ValueError, match="digest mismatch"):
        package(
            "report_only",
            (
                TraceExportResource(
                    "record", "measurements.json", "application/json", payload, "0" * 64
                ),
            ),
        )


def test_repeated_activities_retain_each_iterations_own_outputs() -> None:
    inspection = {
        **INSPECTION,
        "steps": [
            {
                "node_id": "repair",
                "label": "Repair mesh",
                "attempt": 1,
                "state": "failed",
                "outputs": [{"artifact": {"artifact_id": "a"}}],
            },
            {
                "node_id": "repair",
                "label": "Repair mesh",
                "attempt": 2,
                "state": "succeeded",
                "outputs": [{"artifact": {"artifact_id": "b"}}],
            },
        ],
    }
    data = build_trace_export(
        inspection=inspection,
        evidence={},
        mode="full_data",
        resources=(
            TraceExportResource("a", "mesh.stl", "model/stl", b"first", None),
            TraceExportResource("b", "mesh.stl", "model/stl", b"second", None),
        ),
    )
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        review = _review(archive)
        assert len(review["steps"]) == 1
        first, second = review["steps"][0]["attempts"]
        assert first["state"] == "failed"
        assert first["documents"] == ["document-1"]
        assert second["state"] == "succeeded"
        assert second["documents"] == ["document-2"]


def test_untrusted_text_cannot_escape_embedded_model_or_archive_paths() -> None:
    inspection = {**INSPECTION, "graph": {"name": "</script><script>alert(1)</script>"}}
    data = build_trace_export(
        inspection=inspection,
        evidence={},
        mode="full_data",
        resources=(
            TraceExportResource(
                "a", "../../part.stl", "model/stl", b"mesh", None, role="../elsewhere"
            ),
        ),
    )
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        assert (
            "</script><script>alert(1)</script>"
            not in archive.read("index.html").decode()
        )
        assert "outputs/elsewhere/part.stl" in archive.namelist()


def test_input_overview_retains_prompt_parameters_and_large_input_sets() -> None:
    inspection = {
        **INSPECTION,
        "run_inputs": [
            {
                "name": "user_prompt",
                "kind": "text",
                "value": "Design a bracket for a 20 N load.",
            },
            {
                "name": "design_limits",
                "kind": "structured",
                "value": {"load_N": 20, "clearance_mm": 0.2},
            },
            *[
                {
                    "name": f"reference-{index}.pdf",
                    "kind": "link",
                    "value": f"inputs/reference-{index}.pdf",
                }
                for index in range(24)
            ],
        ],
    }
    for mode in ("report_only", "full_data"):
        encoded = build_trace_export(inspection=inspection, evidence={}, mode=mode)
        with zipfile.ZipFile(io.BytesIO(encoded)) as archive:
            inputs = _review(archive)["inputs"]
        assert len(inputs) == 26
        assert inputs[0]["group"] == "Prompts"
        assert inputs[0]["text"] == "Design a bracket for a 20 N load."
        assert inputs[1]["group"] == "Parameters"
        assert ["Load n", "20"] in inputs[1]["tables"][0]["rows"]
        assert all(item["document_id"] is None for item in inputs[2:])


def test_producer_input_references_are_not_confused_with_same_named_outputs() -> None:
    reference = "campaign/inputs/concept.png"
    resources = (
        TraceExportResource(
            "record",
            "source-model-report.json",
            "application/json",
            json.dumps(
                {
                    "input_references": [
                        reference,
                        "campaign/inputs/prompt.txt",
                        reference,
                    ],
                }
            ).encode(),
            None,
        ),
        TraceExportResource(
            "output-image", "concept.png", "image/png", b"output-image", None
        ),
    )
    with zipfile.ZipFile(io.BytesIO(package(resources=resources))) as archive:
        inputs = _review(archive)["inputs"]
        assert len(inputs) == 2
        assert inputs[0]["title"] == "Design sketch (PNG)"
        assert inputs[0]["document_id"] is None
        assert inputs[0]["source_document_id"] == "document-1"
        assert inputs[1]["group"] == "Prompts"
        assert inputs[1]["text"] is None


def test_input_files_use_exact_artifact_identity_and_are_not_output_deliverables() -> (
    None
):
    inspection = {
        **INSPECTION,
        "run_inputs": [
            {
                "name": "source.step",
                "kind": "artifact",
                "value": "inputs/source.step",
                "artifact": {"artifact_id": "input-model"},
            },
        ],
    }
    encoded = build_trace_export(
        inspection=inspection,
        evidence={},
        mode="full_data",
        resources=(
            TraceExportResource(
                "input-model", "source.step", "model/step", b"source-model", None
            ),
            TraceExportResource(
                "prompt",
                "prompt.txt",
                "text/plain",
                b"Make a replacement part.",
                None,
                role="input",
            ),
        ),
    )
    with zipfile.ZipFile(io.BytesIO(encoded)) as archive:
        review = _review(archive)
        assert review["inputs"][0]["document_id"] == "document-1"
        assert review["inputs"][1]["text"] == "Make a replacement part."
        assert review["documents"][0]["input_only"] is True
        assert review["deliverables"] == []


def test_input_identity_and_partial_text_do_not_imply_complete_original_prompt() -> (
    None
):
    inspection = {
        **INSPECTION,
        "run_inputs": [
            {"name": "prompt", "kind": "text", "value": "a" * 64},
            {
                "name": "instructions",
                "kind": "text",
                "value": "Retained excerpt",
                "complete": False,
                "redaction_count": 1,
            },
        ],
    }
    encoded = build_trace_export(inspection=inspection, evidence={}, mode="report_only")
    with zipfile.ZipFile(io.BytesIO(encoded)) as archive:
        inputs = _review(archive)["inputs"]
        assert inputs[0]["identity_only"] is True
        assert inputs[0]["text"] is None
        assert inputs[1]["text"] == "Retained excerpt"
        assert inputs[1]["complete"] is False
        assert inputs[1]["redacted"] is True


def test_retained_prompt_file_is_presented_as_text_not_a_missing_reference() -> None:
    inspection = {
        **INSPECTION,
        "run_inputs": [
            {
                "name": "prompt.txt",
                "kind": "artifact",
                "value": "inputs/prompt.txt",
                "artifact": {"artifact_id": "prompt-file"},
            }
        ],
    }
    encoded = build_trace_export(
        inspection=inspection,
        evidence={},
        mode="full_data",
        resources=(
            TraceExportResource(
                "prompt-file",
                "prompt.txt",
                "text/plain",
                b"Create a replacement handwheel.",
                None,
            ),
        ),
    )
    with zipfile.ZipFile(io.BytesIO(encoded)) as archive:
        item = _review(archive)["inputs"][0]
        assert item["text"] == "Create a replacement handwheel."
        assert item["reference"] == "inputs/prompt.txt"
        assert item["document_id"] == "document-1"


@pytest.mark.parametrize("mode", ["report_only", "full_data"])
def test_assumptions_keep_exact_source_and_iteration_without_inventing_input_lineage(
    mode,
):
    resources = [
        TraceExportResource(
            "design-first",
            "source-model-report.json",
            "application/json",
            json.dumps(
                {
                    "unresolved_assumptions": [
                        "Initial scallop interpretation.",
                        None,
                        "First grip-dot assumption.",
                    ],
                    "input_references": ["inputs/original/prompt.txt"],
                }
            ).encode(),
            None,
        ),
        TraceExportResource(
            "design-second",
            "source-model-report.json",
            "application/json",
            json.dumps(
                {"unresolved_assumptions": ["Revised scallop interpretation."]}
            ).encode(),
            None,
        ),
        TraceExportResource(
            "request",
            "prompt.txt",
            "text/plain",
            b"Original request",
            None,
            role="input",
        ),
        TraceExportResource(
            "other-request",
            "prompt.txt",
            "text/plain",
            b"Unrelated request",
            None,
            role="input",
        ),
    ]
    inspection = {
        **INSPECTION,
        "final_outputs": [],
        "steps": [
            {
                "node_id": "geometry",
                "attempt": number,
                "state": "succeeded",
                "outputs": [{"artifact": {"artifact_id": subject}}],
            }
            for number, subject in enumerate(["design-first", "design-second"], start=1)
        ],
        "run_inputs": [
            {
                "name": "prompt.txt",
                "kind": "artifact",
                "value": path,
                "artifact": {"artifact_id": subject},
            }
            for path, subject in [
                ("inputs/original/prompt.txt", "request"),
                ("inputs/other/prompt.txt", "other-request"),
            ]
        ],
    }
    encoded = build_trace_export(
        inspection=inspection, evidence={}, mode=mode, resources=resources
    )
    with zipfile.ZipFile(io.BytesIO(encoded)) as archive:
        review = _review(archive)
        first, second = review["steps"][0]["attempts"]
        assert [item["text"] for item in first["assumptions"]] == [
            "Initial scallop interpretation.",
            "First grip-dot assumption.",
        ]
        assert [item["source_pointer"] for item in first["assumptions"]] == [
            "/unresolved_assumptions/0",
            "/unresolved_assumptions/2",
        ]
        assert {item["source_document_id"] for item in first["assumptions"]} == {
            "document-1"
        }
        assert second["assumptions"][0]["text"] == "Revised scallop interpretation."
        assert second["assumptions"][0]["source_document_id"] == "document-2"
        assert review["documents"][0]["assumptions"] == first["assumptions"]
        assert review["documents"][0]["input_ids"] == [review["inputs"][0]["id"]]
        assert review["documents"][1]["input_ids"] == []
        assert "assumptions" not in review["steps"][0]
        assert first["input_ids"] == [review["inputs"][0]["id"]]
        assert second["input_ids"] == []


@pytest.mark.parametrize("mode", ["full_data", "report_only"])
def test_3mf_producer_metadata_is_read_without_loading_geometry(mode):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as package:
        package.writestr(
            "3D/3dmodel.model",
            '<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><metadata name="Application">BambuStudio-02.08.02.61</metadata></model>',
        )
        package.writestr(
            "3D/Objects/object_1.model", b"Geometry is not parsed by the review"
        )
    resource = TraceExportResource(
        "package", "manufacturing.3mf", "model/3mf", output.getvalue(), None
    )
    with zipfile.ZipFile(
        io.BytesIO(
            build_trace_export(
                inspection=INSPECTION, evidence={}, mode=mode, resources=[resource]
            )
        )
    ) as archive:
        assert (
            _review(archive)["documents"][0]["application"] == "BambuStudio-02.08.02.61"
        )
        assert "Geometry is not parsed" not in archive.read("index.html").decode()
        assert bool(
            json.loads(archive.read("manifest.json"))["entries"][0]["package_path"]
        ) == (mode == "full_data")


@pytest.mark.parametrize(
    "xml",
    [
        b"<malformed",
        b"x" * 65537,
        b'<!DOCTYPE model [<!ENTITY x "untrusted">]><model>&x;</model>',
    ],
)
def test_unusable_package_metadata_does_not_become_a_software_version(xml):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as package:
        package.writestr("3D/3dmodel.model", xml)
    resource = TraceExportResource(
        "package", "part.3mf", "model/3mf", output.getvalue(), None
    )
    with zipfile.ZipFile(
        io.BytesIO(
            build_trace_export(
                inspection=INSPECTION,
                evidence={},
                mode="report_only",
                resources=[resource],
            )
        )
    ) as archive:
        assert _review(archive)["documents"][0]["application"] is None


def test_completed_activity_events_and_artifact_origin_are_not_conflated():
    inspection = {
        **INSPECTION,
        "final_outputs": [],
        "run_inputs": [
            {
                "name": "source_mesh.stl",
                "kind": "artifact",
                "value": "inputs/source_mesh.stl",
                "artifact": {"artifact_id": "supplied"},
            }
        ],
        "steps": [
            {"node_id": "geometry", "attempt": 1, "state": "failed", "outputs": []},
            {
                "node_id": "geometry",
                "attempt": 2,
                "state": "succeeded",
                "outputs": [{"artifact": {"artifact_id": "generated"}}],
            },
        ],
        "events": [
            {"task_id": "geometry", "kind": kind, "at": f"2026-09-14T20:00:0{index}Z"}
            for index, kind in enumerate(
                ["step_started", "step_failed", "step_started", "step_completed"]
            )
        ],
    }
    encoded = build_trace_export(
        inspection=inspection,
        evidence={},
        mode="full_data",
        resources=[
            TraceExportResource(
                "supplied",
                "source_mesh.stl",
                "model/stl",
                b"input mesh",
                None,
                role="input",
            ),
            TraceExportResource(
                "generated", "source_mesh.stl", "model/stl", b"generated mesh", None
            ),
        ],
    )
    with zipfile.ZipFile(io.BytesIO(encoded)) as archive:
        review = _review(archive)
        assert [(doc["title"], doc["origin"]) for doc in review["documents"]] == [
            ("Supplied part model", "Supplied input"),
            ("Generated part model", "Generated in this run"),
        ]
        first, second = review["steps"][0]["attempts"]
        assert [event["label"] for event in first["events"]] == [
            "Activity started",
            "Activity failed",
        ]
        assert [event["label"] for event in second["events"]] == [
            "Activity started",
            "Activity completed",
        ]
        assert (
            review["steps"][0]["software_version"]
            == "Version unavailable in this historical run"
        )


@pytest.mark.parametrize("support_moves", [0, 12, None])
@pytest.mark.parametrize("mode", ["report_only", "full_data"])
def test_printing_presentation_distinguishes_design_mesh_and_slicer_evidence(
    support_moves, mode
):
    records = {
        "source-model-report.json": {
            "design_dimensions_mm": {"maximum_diameter": 38},
            "operations": ["constructed six-scallop wheel body"],
        },
        "repair-model-report.json": {
            "before": {"mesh": {"vertices": 20, "degenerate_faces": 1}},
            "after": {"mesh": {"degenerate_faces": 0}},
            "orientation": {
                "action": "preserved_model_axes_and_translated_minimum_z_to_build_plate"
            },
            "repair": {"voxel_remesh_used": False, "decimation_used": True},
        },
        "slice-evidence.json": {
            "supports_enabled": True,
            "support_moves": support_moves,
        },
        "process-profile.json": {
            "layer_height": "0.20",
            "sparse_infill_density": "35%",
            "sparse_infill_pattern": "grid",
            "wall_loops": "4",
            "support_type": "tree(auto)",
            "support_threshold_angle": "30",
        },
        "machine-profile.json": {
            "printer_model": "Bambu Lab P1S",
            "nozzle_diameter": ["0.4"],
        },
        "printer-transfer-receipt.json": {"simulated_handoff": True},
    }
    resources = [
        TraceExportResource(
            name, name, "application/json", json.dumps(value).encode(), None
        )
        for name, value in records.items()
    ]
    resources += [
        TraceExportResource(name, name, media, None, None)
        for name, media in [
            ("mesh-preview.png", "image/png"),
            ("slice-preview.png", "image/png"),
            ("concept.png", "image/png"),
            ("concept.svg", "image/svg+xml"),
        ]
    ]
    projection = b'<svg xmlns="http://www.w3.org/2000/svg"/>'
    resources.append(
        TraceExportResource(
            "projection",
            "support-preview.svg",
            "image/svg+xml",
            projection,
            None,
            report_asset=True,
        )
    )
    inspection = {
        **INSPECTION,
        "run_inputs": [
            {"name": name, "kind": "artifact", "artifact": {"artifact_id": name}}
            for name in ["concept.png", "concept.svg"]
        ],
    }
    with zipfile.ZipFile(
        io.BytesIO(
            build_trace_export(
                inspection=inspection, evidence={}, mode=mode, resources=resources
            )
        )
    ) as archive:
        review = _review(archive)
        documents = {item["name"]: item for item in review["documents"]}
        assert documents["mesh-preview.png"]["title"] == "Replacement part design"
        assert (
            documents["slice-preview.png"]["caption"]
            == "Whole model, not individual layers"
        )
        assert documents["support-preview.svg"]["archive_only"] is True
        assert "projection_id" not in review["printing"]
        retained = next(
            item
            for item in json.loads(archive.read("manifest.json"))["entries"]
            if item["subject_id"] == "projection"
        )
        assert archive.read(retained["package_path"]) == projection
        assert (
            review["printing"]["settings_id"] == documents["process-profile.json"]["id"]
        )
        assert review["printing"]["facts"][0] == [
            "Printer",
            "Bambu Lab P1S / 0.4 mm nozzle",
        ]
        expected = "Not recorded" if support_moves is None else str(support_moves)
        assert (
            review["printing"]["support_summary"]
            == f"Supports enabled; {expected} support toolpath moves reported."
        )
        assert review["previews"] == [documents["mesh-preview.png"]["id"]]
        assert documents["slice-preview.png"]["id"] not in review["previews"]
        assert review["printing"]["support_facts"] == [
            ["Support strategy", "Automatic tree supports"],
            ["Support threshold", "30 degrees"],
        ]
        assert ["Wall loops", "4"] in review["printing"]["facts"]
        assert ["Infill pattern", "Grid"] in review["printing"]["facts"]
        assert review["printing"]["preparation"] == [
            ["Mesh cleanup", "Degenerate faces: 1 to 0"],
            [
                "Build orientation",
                "Model axes kept; lowest point moved to the build plate",
            ],
            ["Voxel remeshing", "Not applied"],
            ["Decimation", "Applied"],
        ]
        assert (
            review["printing"]["preparation_id"]
            == documents["repair-model-report.json"]["id"]
        )
        assert "no physical part was printed or repaired" in review["summary"]
        assert [item["title"] for item in review["inputs"]] == [
            "Design sketch (PNG)",
            "Design sketch (SVG)",
        ]
        assert [item["format_note"] for item in review["inputs"]] == [
            "Raster image",
            "Vector drawing",
        ]


@pytest.mark.parametrize("mode", ["full_data", "report_only"])
def test_review_sources_preserve_input_identities_and_documentary_attribution(mode):
    from workspace_service.workflow_trace.canonical import canonical_artifact_paths

    inputs = [
        {
            "name": name,
            "kind": "artifact",
            "origin": "campaign_input_pack",
            "value": f"campaign/case/attempt/inputs/{name}",
            "artifact": {"artifact_id": name},
        }
        for name in ["concept.png", "concept.svg", "context.md"]
    ]
    supplements = [
        {
            "name": "assembled-context.md",
            "kind": "artifact",
            "origin": "review_supplement",
            "value": "campaign/case/attempt/inputs/assembled-context.md",
            "provenance": "Reassembled, not original runtime bytes.",
            "source_artifact_ids": ["context.md"],
            "artifact": {"artifact_id": "assembled", "role": "input_reconstruction"},
        },
        {
            "name": "checkpoint.md",
            "software": "Blender",
            "node_id": "create_mesh",
            "provenance": "Campaign documentation, not raw calls.",
            "artifact": {"artifact_id": "checkpoint", "role": "source_document"},
        },
    ]
    inspection = {
        **INSPECTION,
        "run_inputs": inputs,
        "review_supplements": supplements,
        "steps": [{"node_id": "create_mesh", "outputs": []}],
    }
    resources = [
        TraceExportResource(
            "concept.png",
            "concept.png",
            "image/png",
            b"image",
            None,
            role="input",
            report_asset=True,
        ),
        TraceExportResource(
            "concept.svg",
            "concept.svg",
            "image/svg+xml",
            b"<svg/>",
            None,
            role="input",
            report_asset=True,
        ),
        TraceExportResource(
            "context.md",
            "context.md",
            "text/markdown",
            b"Original context",
            None,
            role="input",
        ),
        TraceExportResource(
            "assembled",
            "assembled-context.md",
            "text/markdown",
            b"Reassembled context",
            None,
            role="input_reconstruction",
        ),
        TraceExportResource(
            "checkpoint",
            "checkpoint.md",
            "text/markdown",
            b"Campaign checkpoint",
            None,
            role="source_document",
        ),
    ]
    assert {item["artifact_id"] for item in canonical_artifact_paths(inspection)} >= {
        "assembled",
        "checkpoint",
    }
    with zipfile.ZipFile(
        io.BytesIO(
            build_trace_export(
                inspection=inspection, evidence={}, mode=mode, resources=resources
            )
        )
    ) as archive:
        review = _review(archive)
        assert len(review["inputs"]) == 4
        sketch, variant, context, assembled = review["inputs"]
        assert sketch["title"] == "Design sketch"
        assert sketch["variant_ids"] == [variant["id"]]
        assert variant["variant_of"] == sketch["id"]
        assert assembled["reconstructed"] is True
        assert assembled["source_document_ids"] == [context["document_id"]]
        assert assembled["text"] == "Reassembled context"
        assert review["steps"][0]["software"] == "Blender"
        assert (
            review["steps"][0]["software_version"]
            == "Version unavailable in this historical run"
        )
        assert (
            review["steps"][0]["software_note"]
            == "Campaign documentation, not raw calls."
        )
        assert review["documents"][-1]["source_text"] == "Campaign checkpoint"
        if mode == "full_data":
            assert (
                archive.read("inputs/reconstructed/assembled-context.md")
                == b"Reassembled context"
            )
            assert (
                archive.read("evidence/sources/checkpoint.md") == b"Campaign checkpoint"
            )
        else:
            assert "evidence/sources/checkpoint.md" not in archive.namelist()

    inspection["review_supplements"][1]["node_id"] = "different_node"
    with zipfile.ZipFile(
        io.BytesIO(
            build_trace_export(
                inspection=inspection, evidence={}, mode=mode, resources=resources
            )
        )
    ) as archive:
        assert _review(archive)["steps"][0]["software"] == "Wright workflow automation"


def test_review_preserves_recorded_lane_labels_without_inventing_missing_groups():
    inspection = {
        **INSPECTION,
        "steps": [{"node_id": str(index)} for index in range(3)],
        "graph": {
            "nodes": [
                {"node_id": "0", "lane": "Mechanical design"},
                {"node_id": "1", "lane": "Manufacturing"},
                {"node_id": "2", "lane": None},
            ]
        },
    }
    with zipfile.ZipFile(
        io.BytesIO(
            build_trace_export(inspection=inspection, evidence={}, mode="report_only")
        )
    ) as archive:
        review = _review(archive)
        assert review["lanes"] == [
            "Mechanical design",
            "Manufacturing",
            "Workflow execution",
        ]
        assert [step["lane"] for step in review["steps"]] == review["lanes"]
