"""Analytic open-format controls for the exact STEP observer."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import cadquery as cq
from OCP.IFSelect import IFSelect_RetDone
from OCP.STEPControl import STEPControl_AsIs, STEPControl_Writer

from inspect_step_rays import digest, inspect


class StepRayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        value = os.environ.get("STEP_RAY_AUDIT_TEMP")
        if not value or not Path(value).is_absolute() or not Path(value).is_dir():
            raise RuntimeError(
                "Host must supply existing absolute local STEP_RAY_AUDIT_TEMP"
            )
        # Keep generated control artifacts and failed evidence on the local disk.
        cls.root = Path(tempfile.mkdtemp(prefix="step-ray-test-", dir=value))
        cls.step = cls.root / "box.step"
        cq.exporters.export(
            cq.Workplane("XY").box(10, 12, 14, centered=(True, True, False)),
            str(cls.step),
        )
        cls.sha = digest(cls.step)
        cls.camera = dict(
            projection="perspective",
            R_world_to_camera=[[1, 0, 0], [0, -1, 0], [0, 0, -1]],
            t_world_to_camera_mm=[0, 0, 30],
            fx=100,
            fy=100,
            cx_px=50,
            cy_px=50,
            width_px=100,
            height_px=100,
            near_mm=1,
            distortion="none_assumed",
            provenance="Analytic box z0..14 in synthetic common frame, camera z30; no fit.",
        )

    def measure(self, **changed):
        kwargs = dict(
            step=self.step,
            expected_sha256=self.sha,
            camera=self.camera,
            pixels=[[60, 50]],
            unit_label="mm",
            unit_basis="Synthetic analytic CAD control only.",
        )
        kwargs.update(changed)
        return inspect(**kwargs)

    def test_perspective_oblique_ray_hits_analytic_planes(self):
        row = self.measure()["rows"][0]
        self.assertEqual(len(row["hits"]), 2)
        first, last = row["hits"]
        self.assertAlmostEqual(first["point"][0], 1.6, places=8)
        self.assertAlmostEqual(first["point"][2], 14.0, places=8)
        self.assertAlmostEqual(first["camera_depth"], 16.0, places=8)
        self.assertAlmostEqual(last["point"][0], 3.0, places=8)
        self.assertAlmostEqual(last["point"][2], 0.0, places=8)
        self.assertEqual(len(row["nearest_face_indices"]), 1)

    def test_orthographic_rays_do_not_use_perspective_division(self):
        row = self.measure(
            camera=dict(self.camera, projection="orthographic", fx=10, fy=10)
        )["rows"][0]
        self.assertEqual(len(row["hits"]), 2)
        for hit in row["hits"]:
            self.assertAlmostEqual(hit["point"][0], 1.0, places=8)

    def test_multiple_STEP_roots_are_all_inspected(self):
        path = self.root / "two-independent-roots.step"
        writer = STEPControl_Writer()
        for x in [-10, 10]:
            box = (
                cq.Workplane("XY")
                .box(4, 4, 4, centered=(True, True, False))
                .val()
                .translate((x, 0, 0))
            )
            self.assertEqual(
                writer.Transfer(box.wrapped, STEPControl_AsIs), IFSelect_RetDone
            )
        self.assertEqual(writer.Write(str(path)), IFSelect_RetDone)
        self.assertEqual(len(cq.importers.importStep(str(path)).vals()), 2)
        report = self.measure(
            step=path,
            expected_sha256=digest(path),
            camera=dict(self.camera, projection="orthographic", fx=2, fy=2),
            pixels=[[30, 50], [70, 50]],
        )
        self.assertEqual(report["step"]["imported_roots"], 2)
        self.assertEqual(report["step"]["solids"], 2)
        self.assertEqual(report["step"]["faces"], 12)
        for row, x in zip(report["rows"], [-10, 10]):
            self.assertAlmostEqual(row["hits"][0]["point"][0], x, places=8)
            self.assertAlmostEqual(row["hits"][0]["point"][2], 4.0, places=8)

    def test_no_hit_and_near_far_clipping(self):
        self.assertFalse(self.measure(pixels=[[99, 99]])["rows"][0]["hits"])
        self.assertFalse(
            self.measure(camera=dict(self.camera, near_mm=31))["rows"][0]["hits"]
        )
        self.assertFalse(self.measure(far_depth=15)["rows"][0]["hits"])

    def test_reject_stale_hash_and_reflected_camera(self):
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            self.measure(expected_sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "det \\+1"):
            self.measure(
                camera=dict(
                    self.camera, R_world_to_camera=[[1, 0, 0], [0, 1, 0], [0, 0, -1]]
                )
            )
        for pixels in [[[float("nan"), 50]], [[100, 50]], [[True, False]]]:
            with self.assertRaises(ValueError):
                self.measure(pixels=pixels)

    def test_cli_binds_dependencies_and_refuses_overwrite(self):
        camera = self.root / "camera.json"
        pixels = self.root / "pixels.json"
        output = self.root / "report.json"
        camera.write_text(json.dumps(self.camera))
        pixels.write_text("[[60,50]]")
        command = [
            sys.executable,
            str(Path(__file__).with_name("inspect_step_rays.py")),
            "--step",
            str(self.step),
            "--expected-step-sha256",
            self.sha,
            "--camera",
            str(camera),
            "--pixels",
            str(pixels),
            "--unit-label",
            "mm",
            "--unit-basis",
            "Synthetic analytic control",
            "--output",
            str(output),
        ]
        first = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        report = json.loads(output.read_text())
        self.assertEqual(report["step"]["sha256"], self.sha)
        self.assertEqual(report["input_files"]["camera"]["sha256"], digest(camera))
        self.assertEqual(
            set(report["dependency_sha256"]),
            {"project_mesh_to_photo.py", "compare_native_faces.py"},
        )
        original = output.read_bytes()
        second = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("output already exists", second.stderr)
        self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
