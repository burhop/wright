import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import cadquery as cq
from OCP.BRep import BRep_Builder
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.BRepTools import BRepTools
from OCP.Geom import Geom_BezierSurface
from OCP.gp import gp_Pnt
from OCP.TColgp import TColgp_Array2OfPnt
from OCP.TopoDS import TopoDS_Shape

import compare_native_faces as audit


class NativeFaceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        value = os.environ.get("NATIVE_FACE_AUDIT_TEMP")
        if not value:
            raise RuntimeError("Host must supply explicit local NATIVE_FACE_AUDIT_TEMP")
        cls.temp_parent = Path(value)
        if not cls.temp_parent.is_absolute() or not cls.temp_parent.is_dir():
            raise RuntimeError(
                "NATIVE_FACE_AUDIT_TEMP must be an existing absolute local directory"
            )

    def setUp(self):
        # Intentionally retain all fixtures and audit evidence, including failures.
        self.root = Path(
            tempfile.mkdtemp(prefix="native-face-test-", dir=self.temp_parent)
        )

    def face(self):
        return cq.Workplane("XY").box(2, 3, 4).val().Faces()[0]

    def records(self, faces, side):
        return audit.inventory(faces, side, self.root, [])

    def run_audit(self, arguments):
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            return audit.main(arguments)

    def step_arguments(self, before, after, output, before_sha=None):
        return [
            "--before",
            str(before),
            "--before-sha",
            before_sha or audit.sha256(before.read_bytes()),
            "--after",
            str(after),
            "--after-sha",
            audit.sha256(after.read_bytes()),
            "--output",
            str(output),
        ]

    def test_native_roundtrip_determinism(self):
        original = self.face()
        data = audit.serialize_face(original)
        self.assertEqual(data, audit.serialize_face(original))
        restored = TopoDS_Shape()
        # Unsupported reader overloads are failures, never skipped or replaced.
        BRepTools.Read_s(restored, io.BytesIO(data), BRep_Builder())
        self.assertFalse(restored.IsNull())
        self.assertEqual(data, audit.serialize_face(cq.Shape.cast(restored)))

    def test_identical_step_imports_and_evidence(self):
        before = self.root / "source.step"
        after = self.root / "same.step"
        cq.exporters.export(cq.Workplane("XY").box(2, 3, 4).val(), str(before))
        original_bytes = before.read_bytes()
        after.write_bytes(original_bytes)
        output = self.root / "audit"
        self.assertEqual(0, self.run_audit(self.step_arguments(before, after, output)))
        report = json.loads((output / "report.json").read_text())
        self.assertTrue(report["before_faces_fully_preserved"])
        self.assertTrue(report["comparison"]["multiset_bijection"])
        self.assertEqual(original_bytes, before.read_bytes())
        self.assertEqual(original_bytes, after.read_bytes())
        indexed = {}
        for side in ("before", "after"):
            item = report["inputs"][side]
            self.assertEqual(item["expected_sha256"], item["pre_import_sha256"])
            self.assertEqual(item["pre_import_sha256"], item["post_audit_sha256"])
            self.assertEqual(
                item["pre_import_sha256"], item["snapshot_post_audit_sha256"]
            )
            for record in report["faces"][side]:
                data = (output / record["file"]).read_bytes()
                self.assertEqual(record["sha256"], audit.sha256(data))
                indexed[record["id"]] = data
        for pair in report["comparison"]["matches"]:
            self.assertEqual(indexed[pair["before_id"]], indexed[pair["after_id"]])
        self.assertEqual(
            audit.sha256(Path(audit.__file__).read_bytes()),
            report["audit_source_sha256"],
        )

    def test_reordered_faces_preserve_multiset(self):
        faces = cq.Workplane("XY").box(2, 3, 4).val().Faces()
        before = self.records(faces, "before")
        after = self.records(list(reversed(faces)), "after")
        result = audit.compare_records(before, after)
        self.assertTrue(result["multiset_bijection"])
        self.assertEqual(len(faces), len(result["matches"]))
        self.assertEqual(len(faces), len({p["after_id"] for p in result["matches"]}))

    def test_duplicate_multiplicity_cannot_reuse_counterpart(self):
        face = self.face()
        before = self.records([face, face], "before")
        after = self.records([face], "after")
        result = audit.compare_records(before, after)
        self.assertFalse(result["before_faces_all_matched"])
        self.assertFalse(result["multiset_bijection"])
        self.assertEqual(1, len(result["matches"]))
        self.assertEqual(1, len(result["unmatched_before"]))
        reverse = audit.compare_records(after, before)
        self.assertTrue(reverse["before_faces_all_matched"])
        self.assertFalse(reverse["multiset_bijection"])
        self.assertEqual(1, len(reverse["unmatched_after"]))

    def test_hash_collision_is_not_identity(self):
        before = [{"id": "before_F1", "sha256": "synthetic-collision", "data": b"A"}]
        after = [{"id": "after_F1", "sha256": "synthetic-collision", "data": b"B"}]
        result = audit.compare_records(before, after)
        self.assertFalse(result["before_faces_all_matched"])
        self.assertEqual([], result["matches"])

    def test_location_and_orientation_are_not_discarded(self):
        face = self.face()
        data = audit.serialize_face(face)
        translated = face.moved(cq.Location(cq.Vector(7, 0, 0)))
        reversed_face = cq.Shape.cast(face.wrapped.Reversed())
        self.assertNotEqual(data, audit.serialize_face(translated))
        self.assertNotEqual(data, audit.serialize_face(reversed_face))

    def synthetic_bezier(self, center_height):
        # Synthetic fixture, not an engineering tolerance or target CAD model.
        poles = TColgp_Array2OfPnt(1, 3, 1, 3)
        for i in range(1, 4):
            for j in range(1, 4):
                z = center_height if (i, j) == (2, 2) else 0.0
                poles.SetValue(i, j, gp_Pnt(float(i - 1), float(j - 1), z))
        surface = Geom_BezierSurface(poles)
        # Required OCCT construction precision only; never an identity threshold.
        builder = BRepBuilderAPI_MakeFace(surface, 1e-7)
        self.assertTrue(builder.IsDone())
        return surface, cq.Shape.cast(builder.Face())

    def test_synthetic_interior_change_with_identical_boundary_poles(self):
        flat_surface, flat_face = self.synthetic_bezier(0.0)
        raised_surface, raised_face = self.synthetic_bezier(1.0)
        # For this non-rational Bezier patch, equal boundary control polygons
        # imply identical complete boundary curves, not merely sampled agreement.
        for i in range(1, 4):
            for j in range(1, 4):
                if i in (1, 3) or j in (1, 3):
                    p = flat_surface.Pole(i, j)
                    q = raised_surface.Pole(i, j)
                    self.assertEqual((p.X(), p.Y(), p.Z()), (q.X(), q.Y(), q.Z()))
        self.assertNotEqual(
            flat_surface.Value(0.5, 0.5).Z(), raised_surface.Value(0.5, 0.5).Z()
        )
        before = self.records([flat_face], "before")
        after = self.records([raised_face], "after")
        self.assertNotEqual(before[0]["data"], after[0]["data"])
        self.assertFalse(
            audit.compare_records(before, after)["before_faces_all_matched"]
        )

    def test_input_hash_failure_retains_evidence_without_import(self):
        before = self.root / "before.step"
        after = self.root / "after.step"
        before.write_bytes(b"not parsed: hash validation must precede import")
        after.write_bytes(b"also not parsed")
        output = self.root / "failed-audit"
        arguments = self.step_arguments(before, after, output, "0" * 64)
        with mock.patch.object(audit.cq.importers, "importStep") as importer:
            self.assertEqual(2, self.run_audit(arguments))
            importer.assert_not_called()
        report = json.loads((output / "report.json").read_text())
        self.assertEqual("NOT_PROVEN", report["preservation_claim"])
        self.assertIsNone(report["before_faces_fully_preserved"])
        self.assertIn("SHA256 mismatch", report["errors"][0]["message"])
        for side, source in [("before", before), ("after", after)]:
            item = report["inputs"][side]
            self.assertEqual(
                source.read_bytes(), (output / item["snapshot"]).read_bytes()
            )
            self.assertEqual(item["pre_import_sha256"], item["post_audit_sha256"])
            self.assertEqual(
                item["pre_import_sha256"], item["snapshot_post_audit_sha256"]
            )

    def test_existing_output_refused_before_input_access(self):
        output = self.root / "existing"
        output.mkdir()
        marker = output / "keep.bin"
        marker.write_bytes(b"unchanged")
        arguments = [
            "--before",
            str(self.root / "missing-before.step"),
            "--before-sha",
            "0" * 64,
            "--after",
            str(self.root / "missing-after.step"),
            "--after-sha",
            "0" * 64,
            "--output",
            str(output),
        ]
        with mock.patch.object(audit.cq.importers, "importStep") as importer:
            self.assertEqual(2, self.run_audit(arguments))
            importer.assert_not_called()
        self.assertEqual(b"unchanged", marker.read_bytes())
        self.assertEqual(["keep.bin"], sorted(p.name for p in output.iterdir()))


if __name__ == "__main__":
    unittest.main()
