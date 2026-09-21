"""Plot readability and data-integrity checks; optional selected robot dependencies.

Also runnable with standard-library unittest in the selected offline container.
"""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "robot_plot_operations", ROOT / "scripts/robot_tracking_operations.py"
)
operations = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(operations)
PLOT_AVAILABLE = importlib.util.find_spec("matplotlib") is not None
BAG_AVAILABLE = importlib.util.find_spec("rosbags") is not None
DATA = ROOT / "tests/datasets/engineering-workflows/scenarios/robot-tracking-diagnosis"


class TrackingPlotSegmentsTests(unittest.TestCase):
    def test_missing_measurements_split_lines_not_fill_them(self):
        samples = [{"time_s": t} for t in [0, 0.5, 1, 3, 3.5]]
        self.assertEqual(operations.plot_segments(samples, 0.5), [samples[:3], samples[3:]])

    def test_float_roundoff_is_not_a_false_gap(self):
        samples = [{"time_s": 0.9999999999999999}, {"time_s": 1.5}]
        self.assertEqual(operations.plot_segments(samples, 0.5), [samples])

    def test_empty_series(self):
        self.assertEqual(operations.plot_segments([], 0.5), [])


@unittest.skipUnless(PLOT_AVAILABLE, "Use the selected robot environment for real rendering")
class TrackingPlotRenderingTests(unittest.TestCase):
    def test_labels_units_gaps_and_actual_series(self):
        import matplotlib.pyplot as plt

        planned = [{"time_s": t, "x_m": t, "y_m": 0} for t in [0, 0.5, 1, 1.5, 2]]
        external = [{"time_s": t, "raw_x_m": t, "raw_y_m": y,
                     "aligned_x_m": t, "aligned_y_m": y, "lateral_error_m": y}
                    for t, y in [(0, 0), (0.5, 0.045), (1.5, -0.025), (2, 0)]]
        wheel = [{**row, "y_m": 0.095, "lateral_error_m": 0.095} for row in planned]
        alignment = {"map_frame": "map", "external_frame": "map", "translation_x_m": 0,
                     "translation_y_m": 0, "rotation_rad": 0, "header_offset_s": 0,
                     "max_interpolation_gap_s": 0.5, "event_tolerance_s": 0.5}
        metrics = {"alignment": alignment, "external_gaps_not_interpolated": [[0.5, 1.5]],
                   "lateral_rmse_m": 0.026, "events": [{"bag_elapsed_s": 1,
                   "operator_note": "Tracker obscured by tote"}]}
        figures = []
        original_save = plt.Figure.savefig

        def save(figure, filename, **kwargs):
            if Path(filename).name == "trajectory-overlay.svg":
                figures.append(figure)
            return original_save(figure, filename, **kwargs)

        with tempfile.TemporaryDirectory() as temp, patch.object(plt.Figure, "savefig", save):
            operations.render_tracking_plots(temp, external, planned, wheel, metrics)
            output = Path(temp)
            for name in ["trajectory-overlay", "alignment-comparison"]:
                ET.fromstring((output / (name + ".svg")).read_text())
                self.assertTrue((output / (name + ".png")).read_bytes().startswith(b"\x89PNG"))
            svg = (output / "trajectory-overlay.svg").read_text()
            for text in ["External position measurement", "Wheel-based estimate (odometry)",
                         "Intended route", "45.0 mm", "95.0 mm", "Sideways error (mm)",
                         "Elapsed time from run start (s)", "not a scale drawing",
                         "Tracker obscured by tote", "no comparable external", "No acceptance limit"]:
                self.assertIn(text, svg)
            guide = (output / "plot-guide.md").read_text()
            self.assertIn("not assumed ground truth", guide)
            self.assertIn("does not prove a cause or wheel slip", guide)
            self.assertIn("not a maximum or a confidence bound", guide)

        path_axis, error_axis = figures[0].axes
        self.assertEqual(path_axis.get_aspect(), "auto")
        measured_lines = [line for line in error_axis.lines if line.get_color() == "#0072B2"]
        self.assertEqual(len(measured_lines), 2)
        self.assertEqual(list(measured_lines[0].get_xdata()), [0, 0.5])
        self.assertEqual(list(measured_lines[1].get_xdata()), [1.5, 2])
        self.assertEqual(list(measured_lines[0].get_ydata()), [0, 45])
        self.assertEqual(list(measured_lines[1].get_ydata()), [-25, 0])
        wheel_lines = [line for line in error_axis.lines if line.get_color() == "#D55E00"]
        self.assertEqual(len(wheel_lines), 1)
        self.assertEqual(list(wheel_lines[0].get_ydata()), [95] * 5)


@unittest.skipUnless(PLOT_AVAILABLE and BAG_AVAILABLE,
                     "Use the selected offline robot environment for bag/plot checks")
class TrackingPlotBagTests(unittest.TestCase):
    def test_all_existing_robot_cases_and_source_preservation(self):
        settings = json.loads((DATA.parent.parent / "bindings/robot-tracking-diagnosis.json").read_text())
        for source in sorted(DATA.iterdir()):
            with self.subTest(case=source.name), tempfile.TemporaryDirectory() as temp:
                before = {path: operations.sha(path) for path in source.iterdir() if path.is_file()}
                root = Path(temp)
                operations.convert_csv_to_bag(source, root / "converted")
                scenario = json.loads((source / "scenario.json").read_text())
                alignment = root / "alignment.json"
                alignment.write_text(json.dumps(settings["scenarios"][scenario["scenario_id"]]))
                metrics = operations.analyze_tracking_bag(root / "converted/recording", alignment, root / "analysis")
                expected_count = 56 if scenario["scenario_id"].endswith("03") else 61
                self.assertEqual(metrics["retained_samples"], expected_count)
                timeline = operations.rows(root / "analysis/timeline.csv")
                self.assertAlmostEqual(metrics["lateral_rmse_m"], math.sqrt(
                    sum(float(row["lateral_error_m"]) ** 2 for row in timeline) / expected_count))
                for name in metrics["plot_files"]:
                    self.assertTrue((root / "analysis" / name).is_file())
                if scenario["scenario_id"].endswith("02"):
                    self.assertAlmostEqual(float(timeline[0]["aligned_x_m"]), 0)
                    self.assertAlmostEqual(float(timeline[0]["aligned_y_m"]), 0)
                    self.assertAlmostEqual(float(timeline[0]["original_header_time_s"]), 0.15)
                    self.assertIn("subtract 150 ms", (root / "analysis/plot-guide.md").read_text())
                if scenario["scenario_id"].endswith("03"):
                    self.assertFalse(any(14 <= float(row["time_s"]) <= 16 for row in timeline))
                    self.assertEqual(metrics["external_gaps_not_interpolated"], [[13.5, 16.5]])
                self.assertEqual(before, {path: operations.sha(path) for path in before})
                with self.assertRaisesRegex(ValueError, "already exists"):
                    operations.analyze_tracking_bag(root / "converted/recording", alignment, root / "analysis")

    def test_wheel_residual_uses_intended_heading_and_rejects_unknown_frame(self):
        source = DATA / "02-corner-time-alignment"
        config = json.loads((DATA.parent.parent / "bindings/robot-tracking-diagnosis.json").read_text())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            operations.convert_csv_to_bag(source, root / "converted")
            bag = root / "converted/recording"
            alignment = root / "alignment.json"
            alignment.write_text(json.dumps(config["scenarios"]["robot-tracking-diagnosis-02"]))
            data = operations.load_bag(bag)
            with patch.object(operations, "render_tracking_plots") as render:
                operations.analyze_tracking_bag(bag, alignment, root / "analysis")
                actual = render.call_args.args[3]
                expected = operations.rows(source / "odometry.csv")
                planned = operations.rows(source / "planned-path.csv")
                for result, wheel, target in zip(actual, expected, planned):
                    yaw = float(target["yaw_rad"])
                    dx = float(wheel["x_m"]) - float(target["x_m"])
                    dy = float(wheel["y_m"]) - float(target["y_m"])
                    self.assertAlmostEqual(result["lateral_error_m"], -math.sin(yaw)*dx + math.cos(yaw)*dy)
            data["/wright_test/odom"][0][1].header.frame_id = "unmapped_wheel_frame"
            with patch.object(operations, "load_bag", return_value=data):
                with self.assertRaisesRegex(ValueError, "odometry frame"):
                    operations.analyze_tracking_bag(bag, alignment, root / "wrong-frame")


if __name__ == "__main__":
    unittest.main(verbosity=2)
