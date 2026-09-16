"""Input acceptance rejects incomplete or invented provenance before dispatch."""

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from scripts import engineering_dataset_input_bindings as bindings
from scripts import run_engineering_dataset_campaign as runner

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def mapping(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "binding_test_helpers", ROOT / "scripts/prepare-printed-dataset-campaign.py"
    )
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    raw = (
        ROOT
        / "tests/datasets/engineering-workflows/scenarios/heat-spreader-sizing/01-eink-sign-controller-strap"
    )
    manifest = json.loads((raw / "scenario.json").read_text(encoding="utf-8"))
    workspace = tmp_path / "workspace"
    inputs = workspace / "inputs"
    inputs.mkdir(parents=True)
    staged = []
    for name in bindings.declared(manifest):
        data = (raw / name).read_bytes()
        (inputs / name).write_bytes(data)
        staged.append({"path": "inputs/" + name, "sha256": bindings.digest(data)})
    names = [
        manifest["files"]["user_profile"],
        manifest["files"]["prompt"],
        *manifest["files"]["context"],
    ]
    context = "\n\n".join(
        (raw / name).read_text(encoding="utf-8") for name in names
    ).encode()
    (inputs / "assembled.md").write_bytes(context)
    staged.append({"path": "inputs/assembled.md", "sha256": bindings.digest(context)})
    sections = []
    text = helpers.add_file_input(sections, "test", "text", "inputs/assembled.md")
    image = helpers.add_file_input(sections, "test", "image", "inputs/concept.png")
    task = {
        "kind": "task",
        "id": "engineering",
        "fields": {"name": "Engineering", "inputs": [], "outputs": []},
    }
    sections.append(task)
    helpers.add_reference(sections, text, task, "requirements")
    helpers.add_reference(sections, image, task, "drawing", "reference_images")
    source = workspace / "test.workflow.wflow"
    source.write_bytes(helpers.render(sections).encode())
    report = {
        "workspace_root": str(workspace),
        "source": str(source),
        "source_sha256": bindings.digest(source.read_bytes()),
        "attempt_id": "attempt-acceptance",
        "input_manifest": staged,
    }
    # Stable fixture receipt tests validation structure. The separate real
    # Chromium replay supplies actual production conversion qualification.
    receipt_root = tmp_path / "lineage"
    receipt_dir = receipt_root / manifest["scenario_id"]
    receipt_dir.mkdir(parents=True)
    svg_hash = bindings.digest((inputs / "concept.svg").read_bytes())
    png_hash = bindings.digest((inputs / "concept.png").read_bytes())
    receipt = {
        "schema_version": 1,
        "operation": "wright.svg-rasterization.v1",
        "scenario_id": manifest["scenario_id"],
        "source": "concept.svg",
        "output": "concept.png",
        "source_sha256": svg_hash,
        "output_sha256": png_hash,
        "reproduced_sha256": png_hash,
        "matches": True,
        "historical_execution_claim": False,
        "observation_kind": "reproduced_now_compared_existing",
        "observed_at": "2026-09-12T00:00:00Z",
        "operation_sha256": bindings.digest(
            (ROOT / "scripts/render-engineering-dataset-images.mjs").read_bytes()
        ),
        "renderer": {
            "network": "http_https_blocked",
            "version": "test-contract-fixture",
        },
    }
    (receipt_dir / (svg_hash + "-" + png_hash + ".json")).write_text(
        json.dumps(receipt), encoding="utf-8"
    )
    document = bindings.build_bindings(
        report, manifest=manifest, raw_directory=raw, lineage_root=receipt_root
    )
    return document, report, raw, receipt_root


def test_every_raw_document_and_retained_svg_has_actual_canonical_consumers(mapping):
    document, report, _, _ = mapping
    assert document["complete"]
    bindings.validate_bindings(
        document, workspace_root=report["workspace_root"], source_path=report["source"]
    )
    svg = next(
        item for item in document["bindings"] if item["raw_file"] == "concept.svg"
    )
    relation = svg["relationships"][0]
    assert relation["kind"] == "retained_editable_original"
    assert relation["consumers"][0]["consumer_port"].endswith("drawing")
    assert relation["image_conversion"]["historical_execution_claim"] is False
    for name in ("context.md", "alternatives.csv", "user-profile.md", "prompt.txt"):
        row = next(item for item in document["bindings"] if item["raw_file"] == name)
        assert row["relationships"][0]["kind"] == "utf8_text_embedding"


@pytest.mark.parametrize(
    "corruption",
    [
        "missing_file",
        "consumer",
        "span",
        "image_hash",
        "operation",
        "retained_original",
        "staged_hash",
        "complete_claim",
    ],
)
def test_missing_or_corrupted_mapping_is_rejected(mapping, corruption):
    original, report, _, _ = mapping
    document = copy.deepcopy(original)
    svg = next(
        item for item in document["bindings"] if item["raw_file"].endswith(".svg")
    )
    text = next(
        item for item in document["bindings"] if item["raw_file"] == "context.md"
    )
    if corruption == "missing_file":
        document["bindings"].pop(0)
    elif corruption == "consumer":
        text["relationships"][0]["consumers"][0]["consumer_port"] = "invented"
    elif corruption == "span":
        text["relationships"][0]["byte_end"] += 1
    elif corruption == "image_hash":
        svg["relationships"][0]["image_conversion"]["output_sha256"] = "a" * 64
    elif corruption == "operation":
        svg["relationships"][0]["image_conversion"]["operation_sha256"] = "a" * 64
    elif corruption == "retained_original":
        svg["relationships"] = []
    elif corruption == "staged_hash":
        document["input_manifest"][0]["sha256"] = "a" * 64
    elif corruption == "complete_claim":
        document["complete"] = False
    with pytest.raises(ValueError):
        bindings.validate_bindings(
            document,
            workspace_root=report["workspace_root"],
            source_path=report["source"],
        )


def test_mojibake_is_not_an_embedding_and_cannot_be_accepted(mapping):
    original, report, raw, lineage = mapping
    workspace = Path(report["workspace_root"])
    original_context = (raw / "context.md").read_bytes()
    # Include explicit engineering Unicode even if this fixture becomes ASCII.
    appended = (
        original_context + b"\nDesign at 45\xc2\xb0C; tolerance \xc2\xb10.1 mm.\n"
    )
    (workspace / "inputs/context.md").write_bytes(appended)
    manifest = copy.deepcopy(original["raw_manifest"])
    for item in report["input_manifest"]:
        if item["path"] == "inputs/context.md":
            item["sha256"] = bindings.digest(appended)
    assembled = workspace / "inputs/assembled.md"
    altered = assembled.read_bytes().replace(
        original_context, appended.decode("cp1252").encode("utf-8")
    )
    assembled.write_bytes(altered)
    next(
        item
        for item in report["input_manifest"]
        if item["path"] == "inputs/assembled.md"
    )["sha256"] = bindings.digest(altered)
    observed = bindings.build_bindings(report, manifest=manifest, lineage_root=lineage)
    assert not observed["complete"]
    assert (
        next(item for item in observed["bindings"] if item["raw_file"] == "context.md")[
            "status"
        ]
        == "unresolved"
    )
    with pytest.raises(ValueError, match="unconsumed"):
        bindings.validate_bindings(
            observed,
            workspace_root=report["workspace_root"],
            source_path=report["source"],
        )


@pytest.mark.parametrize(
    "corruption",
    ["missing_evidence", "missing_binding", "changed_image", "other_attempt"],
)
def test_runner_refuses_input_acceptance_failure_before_any_http_call(
    mapping, tmp_path, corruption
):
    document, report, _, _ = mapping
    evidence = tmp_path / "input-bindings.json"
    case = {
        "scenario_id": document["scenario_id"],
        "attempt_id": document["attempt_id"],
        "workspace_root": report["workspace_root"],
        "source_path": "test.workflow.wflow",
        "source_digest": document["source_sha256"],
        "dataset_digest": document["dataset_digest"],
        "input_binding_contract": "wright.input-bindings.v1",
    }
    if corruption == "missing_binding":
        document["bindings"].pop()
    if corruption == "changed_image":
        (Path(report["workspace_root"]) / "inputs/concept.png").write_bytes(b"changed")
    if corruption == "other_attempt":
        case["attempt_id"] = "attempt-other"
    data = json.dumps(document).encode()
    evidence.write_bytes(data)
    if corruption != "missing_evidence":
        case["input_binding_evidence"] = {
            "path": str(evidence),
            "sha256": bindings.digest(data),
        }

    class Transport:
        calls = 0

        def request(self, *args, **kwargs):
            self.calls += 1
            raise AssertionError("Input rejection must precede HTTP")

    transport = Transport()
    instance = runner.Runner(
        state_root=tmp_path / "state",
        export_root=tmp_path / "exports",
        transport=transport,
    )
    with pytest.raises(ValueError):
        instance.run_case(case)
    assert transport.calls == 0
    assert not (tmp_path / "state" / case["scenario_id"]).exists()
