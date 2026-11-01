"""Synthetic local bytes are integrity controls, NOT evidence of STEP validity.
Run explicitly with: python -m unittest -v test_prepare_visualization_mesh.py
No real Roadster files, renderer, provider, or network are used.
"""

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

import prepare_visualization_mesh as prep


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "synthetic-integrity-control.step"
        self.source.write_bytes(
            b"Synthetic bytes integrity control; NOT a valid STEP claim."
        )
        self.mesh_path = self.root / "mesh.json"
        self.output = self.root / "new-output"
        self.mesh = {
            "units": "mm",
            "points": [
                [0.0, 0.0, 0.0],
                [1.0, 0.0, 0.0],
                [2.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [99.0, 99.0, 99.0],
            ],
            "triangles": [[0, 0, 1], [0, 1, 2], [0, 1, 3]],
            "tessellation": {
                "linear_deflection_mm": 0.1,
                "angular_deflection_radians": 0.15,
            },
            "source_artifact": {
                "path": str(self.source.resolve()),
                "sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
            },
            "extra_metadata": {"preserve": ["all", 1, None]},
        }

    def write_mesh(self, mesh=None):
        # allow_nan=True intentionally permits constructing the invalid NaN test.
        self.mesh_path.write_text(
            json.dumps(self.mesh if mesh is None else mesh), encoding="utf-8"
        )

    def run_mesh(self, mesh=None, output=None):
        self.write_mesh(mesh)
        return prep.prepare(self.mesh_path, self.output if output is None else output)

    def failure_report(self, output=None):
        directory = self.output if output is None else output
        report = json.loads((directory / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "failed_do_not_use_derivative")
        return report

    def test_duplicate_and_distinct_collinear_removed_positive_retained(self):
        self.write_mesh()
        mesh_before = self.mesh_path.read_bytes()
        source_before = self.source.read_bytes()
        report = prep.prepare(self.mesh_path, self.output)
        prepared_bytes = (self.output / "prepared-mesh.json").read_bytes()
        prepared = json.loads(prepared_bytes)
        expected = copy.deepcopy(self.mesh)
        expected["triangles"] = [[0, 1, 3]]
        self.assertEqual(prepared, expected)
        self.assertEqual(report["counts"]["preserved_vertices"], 5)
        self.assertEqual(report["counts"]["removed_vertices"], 0)
        self.assertEqual(report["counts"]["removed_triangles"], 2)
        self.assertEqual(
            [entry["triangle_index"] for entry in report["removed_triangles"]], [0, 1]
        )
        for entry in report["removed_triangles"]:
            self.assertEqual(
                entry["vertex_indices"], self.mesh["triangles"][entry["triangle_index"]]
            )
            self.assertEqual(
                entry["coordinates"],
                [self.mesh["points"][i] for i in entry["vertex_indices"]],
            )
            self.assertTrue(entry["exact_zero_proof"]["all_components_exactly_zero"])
            self.assertEqual(
                entry["exact_zero_proof"]["cross_components"],
                [{"numerator": "0", "denominator": "1"}] * 3,
            )
        self.assertEqual(
            report["input_mesh_sha256"], hashlib.sha256(mesh_before).hexdigest()
        )
        self.assertEqual(
            report["output_mesh_sha256"], hashlib.sha256(prepared_bytes).hexdigest()
        )
        self.assertEqual(report["source_artifact"], self.mesh["source_artifact"])
        self.assertEqual(self.mesh_path.read_bytes(), mesh_before)
        self.assertEqual(self.source.read_bytes(), source_before)
        self.assertTrue(report["integrity_checks"]["input_step_unchanged"])
        self.assertTrue(report["integrity_checks"]["input_mesh_unchanged"])

    def test_ordinary_positive_only_is_retained(self):
        self.mesh["triangles"] = [[0, 1, 3]]
        report = self.run_mesh()
        self.assertEqual(report["counts"]["removed_triangles"], 0)
        self.assertEqual(
            json.loads((self.output / "prepared-mesh.json").read_bytes()), self.mesh
        )

    def test_tiny_positive_nonzero_is_retained_without_tolerance(self):
        self.mesh["points"] = [[0.0, 0.0, 0.0], [1e-75, 0.0, 0.0], [0.0, 1e-75, 0.0]]
        self.mesh["triangles"] = [[0, 1, 2]]
        report = self.run_mesh()
        self.assertEqual(report["float_zero_candidate_count"], 0)
        self.assertEqual(report["counts"]["preserved_triangles"], 1)

    def test_simulated_floating_underflow_is_explicit_failure(self):
        self.mesh["triangles"] = [[0, 1, 3]]
        self.write_mesh()
        with mock.patch.object(
            prep, "float_cross_magnitudes", return_value=np.array([0.0])
        ):
            with self.assertRaisesRegex(
                prep.MeshError, "Offending original triangle indices: 0"
            ):
                prep.prepare(self.mesh_path, self.output)
        report = self.failure_report()
        offending = report["error"]["details"]["offending_triangles"][0]
        self.assertEqual(offending["vertex_indices"], [0, 1, 3])
        self.assertFalse(offending["exact_zero_proof"]["all_components_exactly_zero"])
        self.assertFalse((self.output / "prepared-mesh.json").exists())

    def test_actual_cross_underflow_is_not_removed(self):
        self.mesh["points"] = [[0.0, 0.0, 0.0], [1e-200, 0.0, 0.0], [0.0, 1e-200, 0.0]]
        self.mesh["triangles"] = [[0, 1, 2]]
        with self.assertRaisesRegex(prep.MeshError, "Floating zero disagrees"):
            self.run_mesh()
        self.failure_report()
        self.assertFalse((self.output / "prepared-mesh.json").exists())

    def test_norm_underflow_with_nonzero_float_cross_is_not_removed(self):
        self.mesh["points"] = [[0.0, 0.0, 0.0], [1e-100, 0.0, 0.0], [0.0, 1e-100, 0.0]]
        self.mesh["triangles"] = [[0, 1, 2]]
        with self.assertRaisesRegex(prep.MeshError, "Floating zero disagrees"):
            self.run_mesh()
        self.failure_report()

    def test_invalid_indices_float_indices_and_boolean_indices(self):
        for number, triangle in enumerate(
            [[-1, 1, 3], [0, 1, 5], [0.0, 1, 3], [False, 1, 3], [0, 1]]
        ):
            with self.subTest(triangle=triangle):
                mesh = copy.deepcopy(self.mesh)
                mesh["triangles"] = [triangle]
                output = self.root / ("invalid-" + str(number))
                with self.assertRaises(prep.MeshError):
                    self.run_mesh(mesh, output)
                self.failure_report(output)

    def test_nan_and_infinity_are_rejected(self):
        for number, value in enumerate([float("nan"), float("inf"), -float("inf")]):
            with self.subTest(value=value):
                mesh = copy.deepcopy(self.mesh)
                mesh["points"][0][0] = value
                output = self.root / ("nonfinite-" + str(number))
                with self.assertRaises(prep.MeshError):
                    self.run_mesh(mesh, output)
                self.failure_report(output)

    def test_allzero_rejected(self):
        self.mesh["triangles"] = [[0, 0, 1], [0, 1, 2]]
        with self.assertRaisesRegex(prep.MeshError, "All triangles would be removed"):
            self.run_mesh()
        self.failure_report()
        self.assertFalse((self.output / "prepared-mesh.json").exists())

    def test_hash_mismatch(self):
        self.mesh["source_artifact"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(prep.MeshError, "does not match"):
            self.run_mesh()
        self.failure_report()

    def test_existing_output_is_untouched(self):
        self.output.mkdir()
        sentinel = self.output / "evidence.txt"
        sentinel.write_bytes(b"preserve failed projection evidence")
        with self.assertRaisesRegex(prep.MeshError, "Output already exists"):
            self.run_mesh()
        self.assertEqual(sentinel.read_bytes(), b"preserve failed projection evidence")
        self.assertEqual(list(self.output.iterdir()), [sentinel])

    def test_missing_source(self):
        self.source.unlink()
        with self.assertRaisesRegex(prep.MeshError, "Source STEP is missing"):
            self.run_mesh()
        self.failure_report()

    def test_units_empty_shape_and_hash_syntax(self):
        variants = []
        for field, value in [("units", "m"), ("points", []), ("triangles", [])]:
            mesh = copy.deepcopy(self.mesh)
            mesh[field] = value
            variants.append(mesh)
        mesh = copy.deepcopy(self.mesh)
        mesh["source_artifact"]["sha256"] = "invalid"
        variants.append(mesh)
        for number, mesh in enumerate(variants):
            with self.subTest(number=number):
                output = self.root / ("schema-" + str(number))
                with self.assertRaises(prep.MeshError):
                    self.run_mesh(mesh, output)
                self.failure_report(output)

    def test_count_limit_guards(self):
        for constant in ["MAX_VERTICES", "MAX_TRIANGLES"]:
            with self.subTest(constant=constant):
                with mock.patch.object(prep, constant, 1):
                    with self.assertRaisesRegex(prep.MeshError, "count limit"):
                        prep.validate_mesh(self.mesh)

    def test_nonfinite_detector_arithmetic_is_explicit_failure(self):
        self.mesh["points"] = [[0.0, 0.0, 0.0], [1e308, 0.0, 0.0], [0.0, 1e308, 0.0]]
        self.mesh["triangles"] = [[0, 1, 2]]
        with self.assertRaisesRegex(prep.MeshError, "detector arithmetic is nonfinite"):
            self.run_mesh()
        self.failure_report()

    def test_postprocessing_integrity_checks_and_partial_evidence(self):
        for target in ["source", "mesh"]:
            with self.subTest(target=target):
                output = self.root / ("changed-" + target)
                self.write_mesh()
                victim = self.source if target == "source" else self.mesh_path
                before = victim.read_bytes()
                real_write = prep.write_exclusive

                def interfering_write(path, data):
                    real_write(path, data)
                    if path.name == "prepared-mesh.json":
                        victim.write_bytes(before + b" ")

                with mock.patch.object(
                    prep, "write_exclusive", side_effect=interfering_write
                ):
                    with self.assertRaisesRegex(
                        prep.MeshError, "changed during processing"
                    ):
                        prep.prepare(self.mesh_path, output)
                self.failure_report(output)
                self.assertTrue((output / "prepared-mesh.json").exists())
                victim.write_bytes(before)

    def test_output_write_exception_retains_partial_evidence_without_success(self):
        self.write_mesh()
        real_write = prep.write_exclusive

        def partial_write(path, data):
            if path.name == "prepared-mesh.json":
                path.write_bytes(data[:20])
                raise OSError("simulated local write failure")
            real_write(path, data)

        with mock.patch.object(prep, "write_exclusive", side_effect=partial_write):
            with self.assertRaises(prep.MeshError):
                prep.prepare(self.mesh_path, self.output)
        self.failure_report()
        self.assertEqual(len((self.output / "prepared-mesh.json").read_bytes()), 20)


if __name__ == "__main__":
    unittest.main()
