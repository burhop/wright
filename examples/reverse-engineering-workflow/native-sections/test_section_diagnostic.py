"""Synthetic analytic controls only; no artifact acceptance criteria.
These controls are supplied for execution in the target environment, not run here.
assertAlmostEqual's seven decimal places apply only to these analytic controls.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import cadquery as cq
import section_diagnostic as diagnostic


def plane(x):
    return {
        "id": "plane",
        "origin_mm": [x, 0, 0],
        "normal": [1, 0, 0],
        "plot_axes": [1, 2],
    }


class SectionControls(unittest.TestCase):
    def test_box_native_edges_and_serialized_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            result = diagnostic.measure(
                cq.Solid.makeBox(10, 20, 30), plane(5), 33, directory, "box"
            )
            self.assertEqual(result["status"], "completed", result)
            self.assertTrue(result["raw_section_is_valid"])
            self.assertEqual(len(result["edges"]), 4)
            self.assertEqual([e["geom_type"] for e in result["edges"]], ["LINE"] * 4)
            for actual, expected in zip(
                sorted(e["length_mm"] for e in result["edges"]), [20, 20, 30, 30]
            ):
                self.assertAlmostEqual(actual, expected)
            for edge in result["edges"]:
                payload = (directory / edge["brep"]["file"]).read_bytes()
                self.assertGreater(len(payload), 0)
                self.assertEqual(diagnostic.digest(payload), edge["brep"]["sha256"])
                self.assertEqual(len(edge["samples"]), 33)
                points = [p["xyz_mm"] for p in edge["samples"]]
                for point in edge["samples"]:
                    self.assertAlmostEqual(point["xyz_mm"][0], 5)
                    self.assertAlmostEqual(point["plane_residual_mm"], 0)
                for first, second in zip(points, points[1:]):
                    distance = sum((b - a) ** 2 for a, b in zip(first, second)) ** 0.5
                    self.assertAlmostEqual(distance, edge["length_mm"] / 32)

    def test_outside_plane_is_explicitly_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = diagnostic.measure(
                cq.Solid.makeBox(10, 20, 30), plane(20), 33, Path(tmp), "outside"
            )
            self.assertEqual(result["status"], "empty", result)
            self.assertEqual(result["edges"], [])
            self.assertIn("raw_section_is_valid", result)
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_open_face_has_one_uncapped_line(self):
        corners = [
            cq.Vector(*p) for p in [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)]
        ]
        face = cq.Face.makeFromWires(cq.Wire.makePolygon(corners, close=True))
        with tempfile.TemporaryDirectory() as tmp:
            result = diagnostic.measure(face, plane(5), 33, Path(tmp), "face")
            self.assertEqual(result["status"], "completed", result)
            self.assertEqual(len(result["edges"]), 1)
            edge = result["edges"][0]
            self.assertEqual(edge["geom_type"], "LINE")
            self.assertAlmostEqual(edge["length_mm"], 10)
            for point in edge["samples"]:
                self.assertAlmostEqual(point["xyz_mm"][0], 5)
                self.assertAlmostEqual(point["xyz_mm"][2], 0)
                self.assertAlmostEqual(point["plane_residual_mm"], 0)

    def test_wrong_hash_precedes_import_and_output_is_exclusive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.step"
            manifest = root / "manifest.json"
            source.write_bytes(b"synthetic invalid STEP payload")
            manifest.write_text(
                json.dumps(
                    {
                        "artifacts": [
                            {
                                "id": "artifact",
                                "path": source.name,
                                "sha256": diagnostic.digest(
                                    b"different synthetic payload"
                                ),
                            }
                        ],
                        "sections": [plane(5)],
                        "samples_per_edge": 33,
                    }
                ),
                encoding="utf-8",
            )
            output = root / "diagnostic"
            with patch.object(diagnostic.cq.importers, "importStep") as importer:
                report = diagnostic.run(manifest, output)
                importer.assert_not_called()
                self.assertEqual(report["status"], "incomplete")
                artifact = report["artifacts"][0]
                self.assertIn("mismatch before import", " ".join(artifact["errors"]))
                self.assertEqual(
                    artifact["sha256_before"], diagnostic.digest(source.read_bytes())
                )
                self.assertEqual(artifact["sha256_before"], artifact["sha256_after"])
                before = {p.name: p.read_bytes() for p in output.iterdir()}
                with self.assertRaises(FileExistsError):
                    diagnostic.run(manifest, output)
                importer.assert_not_called()
                self.assertEqual(
                    before, {p.name: p.read_bytes() for p in output.iterdir()}
                )


if __name__ == "__main__":
    unittest.main()
