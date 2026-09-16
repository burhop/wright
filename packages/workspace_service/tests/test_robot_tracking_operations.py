"""Selected-dependency engineering operation checks; default suite may skip."""

import importlib.util
import json
import math
from pathlib import Path
import sys
import pytest

pytest.importorskip("rosbags")
pytest.importorskip("matplotlib")
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location(
    "robot_tracking_operations", ROOT / "scripts/robot_tracking_operations.py"
)
operation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(operation)
DATA = ROOT / "tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis"


def test_clock_offset_is_preserved_then_corrected_once(tmp_path):
    source = DATA / "02-corner-time-alignment"
    converted = tmp_path / "converted"
    manifest = operation.convert_csv_to_bag(source, converted)
    data = operation.load_bag(converted / "recording")
    stamp, pose = data["/wright_test/external_pose"][0]
    assert (
        pose.header.stamp.sec * 10**9 + pose.header.stamp.nanosec - stamp == 150000000
    )
    assert pose.header.frame_id == "tracker"
    _, odom = data["/wright_test/odom"][0]
    assert all(math.isnan(x) for x in odom.pose.covariance)
    assert manifest["frame_transform_applied"] is False
    config = json.loads(
        (
            ROOT
            / "tests/datasets/engineering-workflows/bindings/robot-tracking-diagnosis.json"
        ).read_text()
    )["scenarios"]["robot-tracking-diagnosis-02"]
    alignment = tmp_path / "alignment.json"
    alignment.write_text(json.dumps(config))
    result = operation.analyze_tracking_bag(
        converted / "recording", alignment, tmp_path / "analysis"
    )
    first = operation.rows(tmp_path / "analysis/timeline.csv")[0]
    assert float(first["aligned_x_m"]) == 0
    assert float(first["aligned_y_m"]) == 0
    assert result["retained_samples"] == 61
    config["header_offset_s"] = 0.3
    alignment.write_text(json.dumps(config))
    with pytest.raises(ValueError, match="double-correct"):
        operation.analyze_tracking_bag(
            converted / "recording", alignment, tmp_path / "bad-analysis"
        )


def test_visual_occlusion_stays_absent_and_prior_outputs_cannot_be_replaced(tmp_path):
    source = DATA / "03-figure-eight-occlusion"
    converted = tmp_path / "converted"
    manifest = operation.convert_csv_to_bag(source, converted)
    assert len(manifest["omitted_rows"]) == 5
    data = operation.load_bag(converted / "recording")
    times = [
        (stamp - operation.EPOCH_NS) / 1e9
        for stamp, _ in data["/wright_test/external_pose"]
    ]
    assert len(times) == 56 and not any(14 <= time <= 16 for time in times)
    with pytest.raises(ValueError, match="already exists"):
        operation.convert_csv_to_bag(source, converted)
    assert len(operation.rows(source / "external-pose.csv")) == 61


def test_selected_tool_refuses_changed_source_and_cross_attempt_paths(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("WRIGHT_ROBOT_WORKSPACE", str(tmp_path))
    module_spec = importlib.util.spec_from_file_location(
        "test_robot_mcp", ROOT / "scripts/robot_tracking_mcp.py"
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    original = tmp_path / "case/attempt/inputs/robot_tracking_operations.py"
    original.parent.mkdir(parents=True)
    original.write_text("different operation")
    with pytest.raises(ValueError, match="differs"):
        module.authorize_source(
            str(original.relative_to(tmp_path)),
            original.parent,
            tmp_path / "case/attempt/artifacts/converted",
        )
    original.write_bytes((ROOT / "scripts/robot_tracking_operations.py").read_bytes())
    with pytest.raises(ValueError, match="same explicit campaign attempt"):
        module.authorize_source(
            str(original.relative_to(tmp_path)),
            original.parent,
            tmp_path / "case/other/artifacts/converted",
        )
    with pytest.raises(ValueError, match="escapes"):
        module.confined("../elsewhere")
    module.authorize_source(
        str(original.relative_to(tmp_path)),
        original.parent,
        tmp_path / "case/attempt/artifacts/converted",
    )
