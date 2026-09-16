"""Fast contracts only; no native mesh, solver, network or reference fixtures."""

import importlib.util
import json
from pathlib import Path
import sys
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[3]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


operation = load("pi_cfd_operations", "pi_cfd_operations.py")
sys.modules["pi_cfd_operations"] = operation
reference = load("pi_reference_test", "pi_reference_mcp.py")
fixed_mcp = load("pi_cfd_mcp_test", "pi_cfd_mcp.py")


@pytest.fixture
def contract(tmp_path):
    # This placeholder tests metadata rejection only; it is never passed to Gmsh.
    path = tmp_path / "source.step"
    path.write_text("unit contract placeholder, not geometry")
    value = {
        "schema_version": 1,
        "units": "mm",
        "ambient_k": 298.15,
        "gravity_m_s2": [0, 0, -9.81],
        "mesh_size_mm": 2,
        "duration_s": 0.02,
        "delta_t_s": 0.001,
        "boundaries": [],
        "assumptions": ["Unit metadata test"],
        "regions": [
            {
                "name": name,
                "kind": kind,
                "step": "source.step",
                "sha256": operation.sha(path),
                "material": {"rho": 1, "cp": 1000, "kappa": 0.2},
                "heat_w": 0,
            }
            for name, kind in (("air", "fluid"), ("shell", "solid"))
        ],
    }
    return value, tmp_path


@pytest.mark.parametrize(
    "field,value",
    [
        ("units", "m"),
        ("mesh_size_mm", float("nan")),
        ("script", "arbitrary"),
        ("regions", []),
    ],
)
def test_compiler_rejects_unsupported_or_nonfinite_contract(contract, field, value):
    document, root = contract
    document[field] = value
    with pytest.raises(ValueError):
        operation.validate(document, root)


def test_compiler_rejects_changed_actual_cad_bytes(contract):
    document, root = contract
    (root / "source.step").write_text("changed")
    with pytest.raises(ValueError, match="CAD STEP bytes"):
        operation.validate(document, root)


def test_compiler_requires_a_real_named_fan_boundary(contract):
    document, root = contract
    document["fan_curve"] = {
        "points": [[0, 45], [0.001, 0]],
        "provenance": "synthetic_customer_curve",
    }
    with pytest.raises(ValueError, match="actual fan face"):
        operation.validate(document, root)


def test_unresolved_solver_dispatch_is_never_replayed(tmp_path, monkeypatch):
    (tmp_path / "contract.json").write_text("{}")
    (tmp_path / "solver-dispatch.json").write_text(json.dumps({"status": "dispatched"}))
    monkeypatch.setattr(
        operation,
        "foam_command",
        lambda *_: pytest.fail("Unknown mutation was replayed"),
    )
    with pytest.raises(ValueError, match="do not replay"):
        operation.solve_and_extract(tmp_path)


def steady_contract(document):
    document.pop("duration_s")
    document.pop("delta_t_s")
    document.update(
        schema_version=2,
        numerics={"mode": "steady", "iterations": 300, "write_interval": 50},
        mesh_grading={"far_size_mm": 10, "distance_min_mm": 2, "distance_max_mm": 25},
    )
    return document


def test_steady_profile_is_explicit_and_preserves_geometry_thermal_inputs(contract):
    document, root = contract
    original = json.loads(json.dumps(document))
    operation.validate(steady_contract(document), root)
    assert operation.numerical_profile(document) == {
        "mode": "steady",
        "end": 300,
        "delta": 1,
        "write_interval": 50,
    }
    for key in ("regions", "boundaries", "ambient_k", "gravity_m_s2"):
        assert document[key] == original[key]
    assert operation.numerical_profile(original)["mode"] == "transient"


def test_steady_dictionaries_add_bounded_under_relaxation():
    template = """solvers
{
    p_rgh
    {
        solver           GAMG;
        smoother         symGaussSeidel;
        tolerance        1e-7;
        relTol           0.01;
    }
}
relaxationFactors
{
    equations
    {
        h               1;
        U               1;
    }
}
"""
    fluid = operation.steady_solution_controls(template, True)
    assert "solver           PCG;" in fluid
    assert "preconditioner   DIC;" in fluid
    assert "p_rgh           0.7;" in fluid
    assert "h               0.1;" in fluid
    assert "U               0.2;" in fluid
    solid = operation.steady_solution_controls("solvers {}\n", False)
    assert "e               0.1;" in solid


def test_same_region_fragment_splits_are_grouped_but_cross_region_overlap_is_exposed():
    assert operation.MAX_CLOSED_SOLIDS_PER_REGION == 64
    assert operation.MAX_IMPORTED_SOLIDS == 128
    grouped, cross, owners = operation.classify_fragment_owners(
        ["air", "shell", "shell"],
        [[(3, 1)], [(3, 2), (3, 3)], [(3, 3), (3, 4)]],
    )
    assert grouped == {"air": [1], "shell": [2, 3, 4]}
    assert cross == {}
    assert owners[3] == ["shell", "shell"]

    grouped, cross, _ = operation.classify_fragment_owners(
        ["air", "shell"], [[(3, 1), (3, 5)], [(3, 5), (3, 6)]]
    )
    assert grouped == {"air": [1], "shell": [6]}
    assert cross == {5: ["air", "shell"]}


def test_mesh_progress_never_writes_to_mcp_stdout(tmp_path, capsys):
    operation.record_mesh_progress(tmp_path, [], 0.0, "fragment_started")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert '"stage": "fragment_started"' in captured.err
    assert (
        json.loads((tmp_path / "mesh-progress.json").read_text())["stages"][0]["stage"]
        == "fragment_started"
    )


def test_split_region_validation_accepts_only_declared_material_identities(tmp_path):
    document = {"regions": [{"name": "air"}, {"name": "shell"}, {"name": "inserts"}]}
    boundaries = {
        "air": "sampleRegion shell;\nsampleRegion inserts;\n",
        "shell": "sampleRegion air;\n",
        "inserts": "sampleRegion air;\n",
    }
    for identity, text in boundaries.items():
        path = tmp_path / "constant" / identity / "polyMesh/boundary"
        path.parent.mkdir(parents=True)
        path.write_text(text)
    assert operation.validate_split_regions(tmp_path, document) == {
        "actual_regions": ["air", "inserts", "shell"],
        "sampled_regions": ["air", "inserts", "shell"],
    }


@pytest.mark.parametrize(
    "extra_region,bad_sample",
    [("region2", None), (None, "region2")],
)
def test_split_region_validation_rejects_anonymous_or_dangling_regions(
    tmp_path, extra_region, bad_sample
):
    document = {"regions": [{"name": "air"}, {"name": "shell"}]}
    for identity in ("air", "shell"):
        path = tmp_path / "constant" / identity / "polyMesh/boundary"
        path.parent.mkdir(parents=True)
        path.write_text(
            f"sampleRegion {bad_sample or ('shell' if identity == 'air' else 'air')};\n"
        )
    if extra_region:
        path = tmp_path / "constant" / extra_region / "polyMesh/boundary"
        path.parent.mkdir(parents=True)
        path.write_text("sampleRegion air;\n")
    with pytest.raises(ValueError, match="material identities"):
        operation.validate_split_regions(tmp_path, document)
    diagnostic = json.loads((tmp_path / "split-region-diagnostic.json").read_text())
    assert (
        extra_region in diagnostic["actual_regions"]
        if extra_region
        else bad_sample in diagnostic["sampled_regions"]
    )


@pytest.mark.parametrize(
    "replacement",
    [
        {"mode": "steady", "iterations": True, "write_interval": 1},
        {"mode": "steady", "iterations": 300.5, "write_interval": 50},
        {"mode": "steady", "iterations": 301, "write_interval": 50},
        {"mode": "transient", "iterations": 300, "write_interval": 50},
        {
            "mode": "steady",
            "iterations": 300,
            "write_interval": 50,
            "script": "ignored?",
        },
    ],
)
def test_invalid_steady_profile_never_reaches_native_work(contract, replacement):
    document, root = contract
    steady_contract(document)["numerics"] = replacement
    with pytest.raises(ValueError):
        operation.validate(document, root)


def test_steady_schema_rejects_ambiguous_transient_keys_and_grading(contract):
    document, root = contract
    steady_contract(document)["duration_s"] = 1200
    with pytest.raises(ValueError, match="Unsupported"):
        operation.validate(document, root)
    document.pop("duration_s")
    document["mesh_grading"]["distance_max_mm"] = 1
    with pytest.raises(ValueError):
        operation.validate(document, root)


def test_native_timeout_preserves_partial_solver_log_and_prevents_overwrite(
    tmp_path, monkeypatch
):
    def timeout(command, **kwargs):
        kwargs["stdout"].write("Time = 4\nreal native partial diagnostic\n")
        kwargs["stdout"].flush()
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(operation.subprocess, "run", timeout)
    with pytest.raises(subprocess.TimeoutExpired):
        operation.foam_command(tmp_path, ["chtMultiRegionFoam"])
    logfile = tmp_path / "log.chtMultiRegionFoam"
    assert "Time = 4" in logfile.read_text()
    assert (
        json.loads((tmp_path / "log.chtMultiRegionFoam.receipt.json").read_text())[
            "status"
        ]
        == "timed_out"
    )
    with pytest.raises(FileExistsError):
        operation.foam_command(tmp_path, ["chtMultiRegionFoam"])
    assert "Time = 4" in logfile.read_text()


@pytest.mark.parametrize(
    "url",
    [
        "http://pip-assets.raspberrypi.com/a",
        "https://127.0.0.1/a",
        "https://www.raspberrypi.com@evil.example/a",
        "https://www.raspberrypi.com:8443/a",
    ],
)
def test_reference_redirect_cannot_leave_public_fixed_origins(url):
    with pytest.raises(ValueError):
        reference.checked_url(url)


@pytest.mark.parametrize(
    "path",
    ["../outside", "/etc/passwd", "C:/outside", "inputs/../../outside", ".hidden/file"],
)
def test_fixed_operation_path_confinement(tmp_path, path):
    with pytest.raises(ValueError):
        operation.path_under(tmp_path, path)
    with pytest.raises(ValueError):
        reference.confined(tmp_path, path)


def test_reference_page_observations_are_bounded_and_keep_exact_offsets(tmp_path):
    inputs = tmp_path / "case/inputs"
    research = tmp_path / "case/artifacts/research"
    inputs.mkdir(parents=True)
    research.mkdir(parents=True)
    source = Path(reference.__file__).read_bytes()
    (inputs / "pi_reference_mcp.py").write_bytes(source)
    # Metadata-only unit input; no actual PDF retrieval/extraction is claimed.
    data = b"unit reference bytes"
    filename = "manufacturer-drawing.pdf"
    (research / filename).write_bytes(data)
    manifest = {
        "operation_sha256": reference.digest(source),
        "sources": [
            {
                "path": filename,
                "sha256": reference.digest(data),
                "url": "https://pip-assets.raspberrypi.com/unit",
                "pages": [{"text": "x" * 8501}],
            }
        ],
        "limits": ["unit metadata only"],
    }
    (research / "manufacturer-evidence.json").write_text(json.dumps(manifest))
    first = reference.read_page(
        tmp_path,
        "case/inputs/pi_reference_mcp.py",
        "case/artifacts/research",
        filename,
        1,
    )
    second = reference.read_page(
        tmp_path,
        "case/inputs/pi_reference_mcp.py",
        "case/artifacts/research",
        filename,
        1,
        first["next_offset"],
    )
    assert len(first["text"]) == len(second["text"]) == 4000
    assert first["next_offset"] == 4000 and second["next_offset"] == 8000
    assert first["sha256"] == reference.digest(data)


def test_one_variant_preparation_has_its_own_case_receipt_and_allrun(
    tmp_path, monkeypatch
):
    workspace = tmp_path / "workspace"
    inputs = workspace / "campaign/case/attempt/inputs"
    output = workspace / "campaign/case/attempt/artifacts"
    foam = tmp_path / "foam"
    inputs.mkdir(parents=True)
    output.mkdir()
    foam.mkdir()
    for name in ("pi_cfd_operations.py", "pi_cfd_mcp.py"):
        (inputs / name).write_bytes((ROOT / "scripts" / name).read_bytes())
    (inputs / "wrightPrghFanPressure.C").write_bytes(
        (ROOT / "scripts/pi_foam_boundary/wrightPrghFanPressure.C").read_bytes()
    )
    geometry = output / "air.step"
    geometry.write_text("metadata-only placeholder")
    document = {
        "schema_version": 1,
        "units": "mm",
        "ambient_k": 298.15,
        "gravity_m_s2": [0, 0, -9.81],
        "mesh_size_mm": 2,
        "duration_s": 0.02,
        "delta_t_s": 0.001,
        "boundaries": [],
        "assumptions": ["Unit metadata test"],
        "regions": [
            {
                "name": name,
                "kind": kind,
                "step": geometry.relative_to(workspace).as_posix(),
                "sha256": operation.sha(geometry),
                "material": {"rho": 1, "cp": 1000, "kappa": 0.2},
                "heat_w": 0,
            }
            for name, kind in (("air", "fluid"), ("shell", "solid"))
        ],
    }
    contract_path = output / "contract-a.json"
    contract_path.write_text(json.dumps(document))

    def fake_prepare(root, contract, case):
        case_path = operation.path_under(root, case)
        case_path.mkdir(parents=True)
        operation.write(case_path / "preparation.json", "{}")
        return {"solver_executed": False}

    monkeypatch.setattr(operation, "prepare", fake_prepare)
    receipt = fixed_mcp.prepare_variant(
        workspace,
        foam,
        "campaign/case/attempt/inputs/pi_cfd_operations.py",
        "campaign/case/attempt/artifacts",
        "campaign/case/attempt/artifacts/contract-a.json",
        "a",
    )
    assert receipt["variant"] == "variant-a"
    assert receipt["foam_case_dir"].endswith("/pi-cfd/variant-a")
    allrun = (
        operation.path_under(foam, receipt["staging_relative_to_foam_root"]) / "Allrun"
    )
    assert allrun.read_text().count(" solve ") == 1
    assert (output / "cfd-preparation-a.json").is_file()
    with pytest.raises(ValueError, match="exists"):
        fixed_mcp.prepare_variant(
            workspace,
            foam,
            "campaign/case/attempt/inputs/pi_cfd_operations.py",
            "campaign/case/attempt/artifacts",
            "campaign/case/attempt/artifacts/contract-a.json",
            "a",
        )
