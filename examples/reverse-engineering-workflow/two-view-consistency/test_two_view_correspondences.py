import copy
import json
from pathlib import Path
import tempfile
import unittest
import cv2
import numpy as np
import audit_two_view_correspondences as audit


def scene(planar=False, n=14):
    rng = np.random.default_rng(731)
    xyz = rng.uniform([-1.4, -1.0, 4.0], [1.4, 1.0, 8.0], (n, 3))
    if planar:
        xyz[:, 2] = 6.0
    angle = 0.17
    r = np.array(
        [
            [np.cos(angle), 0, np.sin(angle)],
            [0, 1, 0],
            [-np.sin(angle), 0, np.cos(angle)],
        ]
    )
    t = np.array([0.7, 0.12, 0.08])
    k1 = np.array([[400.0, 0, 320], [0, 450, 240], [0, 0, 1]])
    k2 = np.array([[850.0, 0, 600], [0, 900, 400], [0, 0, 1]])
    p1 = k1 @ np.column_stack((np.eye(3), np.zeros(3)))
    p2 = k2 @ np.column_stack((r, t))
    world = np.column_stack((xyz, np.ones(n)))
    u, v = world @ p1.T, world @ p2.T
    skew = np.array([[0, -t[2], t[1]], [t[2], 0, -t[0]], [-t[1], t[0], 0]])
    known = np.linalg.inv(k2).T @ skew @ r @ np.linalg.inv(k1)
    return u[:, :2] / u[:, 2:], v[:, :2] / v[:, 2:], known


def tracks(a, b):
    return {
        str(i): {
            "a": {"uv_px": x.tolist(), "uncertainty_px": 2.0},
            "b": {"uv_px": y.tolist(), "uncertainty_px": 5.0},
        }
        for i, (x, y) in enumerate(zip(a, b))
    }


class NumericalControls(unittest.TestCase):
    def test_known_nonplanar_and_leaveout(self):
        a, b, known = scene(n=10)
        result = audit.audit_pair(["a", "b"], tracks(a, b))
        f = result["models"]["F"]
        matrix = np.array(f["fit"]["matrix"])
        known /= np.linalg.norm(known)
        self.assertLess(
            min(np.linalg.norm(matrix - known), np.linalg.norm(matrix + known)), 1e-8
        )
        self.assertEqual(f["fit"]["design_before_enforcement"]["rank"], 8)
        self.assertLess(f["leave_out_summary"]["metrics"]["to_image_b_px"]["max"], 1e-6)
        self.assertGreater(
            result["models"]["H"]["within_summary"]["metrics"]["forward_to_b_px"][
                "max"
            ],
            0.1,
        )
        for row in f["leave_one_out"]:
            self.assertNotIn(row["held_out_id"], row["training_ids"])
            self.assertEqual(len(row["training_ids"]), 9)

    def test_independent_directional_formula_and_uncertainty(self):
        # Rectified cameras: f_a=400, f_b=900; positive horizontal baseline.
        # Their independently derived constraint is y_a/400 - y_b/900 = 0.
        f = [[0.0, 0.0, 0.0], [0.0, 0.0, -1 / 900], [0.0, 1 / 400, 0.0]]
        model = {"status": "fitted_image_model", "matrix": f}
        row = audit.evaluate(
            "F",
            model,
            "probe",
            np.array([80.0, 80.0]),
            np.array([270.0, 189.0]),
            2.0,
            5.0,
        )
        m = row["metrics"]
        self.assertAlmostEqual(m["to_image_a_px"], 4.0, places=10)
        self.assertAlmostEqual(m["to_image_b_px"], 9.0, places=10)
        expected = 0.01 / np.sqrt((2 / 400) ** 2 + (5 / 900) ** 2)
        self.assertAlmostEqual(m["constraint_normalized"], expected, places=10)
        self.assertAlmostEqual(
            m["to_image_a_px"] / m["constraint_scale_over_line_a_px"], expected
        )
        self.assertAlmostEqual(
            m["to_image_b_px"] / m["constraint_scale_over_line_b_px"], expected
        )

    def test_planar_nearplanar_and_shift(self):
        a, b, _ = scene(planar=True)
        p = audit.audit_pair(["a", "b"], tracks(a, b))
        self.assertEqual(p["models"]["F"]["fit"]["status"], "non_identifiable")
        self.assertLess(
            p["models"]["H"]["leave_out_summary"]["metrics"]["forward_to_b_px"]["max"],
            1e-6,
        )
        noisy = b + np.random.default_rng(19).normal(0, 1e-7, b.shape)
        diagnostic = audit.fit("F", a, noisy)["design_before_enforcement"]
        self.assertTrue(diagnostic["weak_eight_row_support_warning"])
        shifted = b.copy()
        shifted[0] += [60.0, 120.0]
        h = audit.audit_pair(["a", "b"], tracks(a, shifted))["models"]["H"][
            "leave_one_out"
        ][0]
        self.assertAlmostEqual(
            h["evaluation"]["metrics"]["forward_to_b_px"], np.hypot(60, 120), places=5
        )
        a, b, known = scene()
        b[0] += [60.0, 120.0]
        row = audit.audit_pair(["a", "b"], tracks(a, b))["models"]["F"][
            "leave_one_out"
        ][0]
        oracle = audit.evaluate(
            "F",
            {"status": "fitted_image_model", "matrix": known.tolist()},
            "0",
            a[0],
            b[0],
            2.0,
            5.0,
        )
        self.assertGreater(row["evaluation"]["metrics"]["to_image_b_px"], 20.0)
        self.assertAlmostEqual(
            row["evaluation"]["metrics"]["to_image_b_px"],
            oracle["metrics"]["to_image_b_px"],
            places=5,
        )

    def test_minimum_counts_collinearity_and_nulls(self):
        for n in (7, 8):
            a, b, _ = scene(n=n)
            f = audit.audit_pair(["a", "b"], tracks(a, b))["models"]["F"]
            self.assertEqual(
                f["fit"]["status"], "unavailable" if n == 7 else "fitted_image_model"
            )
            self.assertTrue(
                all(r["fit"]["status"] == "unavailable" for r in f["leave_one_out"])
            )
        a = np.column_stack((np.arange(10.0), 2 * np.arange(10.0) + 3))
        for kind in ("F", "H"):
            self.assertEqual(
                audit.fit(kind, a, 3 * a + 7)["status"], "non_identifiable"
            )
        a, b, _ = scene(planar=True, n=4)
        h = audit.audit_pair(["a", "b"], tracks(a, b))["models"]["H"]
        self.assertEqual(h["fit"]["status"], "fitted_image_model")
        self.assertTrue(
            all(r["fit"]["status"] == "unavailable" for r in h["leave_one_out"])
        )
        data = tracks(a, b)
        data["0"]["a"]["uv_px"] = None
        result = audit.audit_pair(["a", "b"], data)
        self.assertEqual(
            result["omitted"], [{"id": "0", "missing_or_null_images": ["a"]}]
        )
        self.assertEqual(result["models"]["H"]["fit"]["status"], "unavailable")


class FileControls(unittest.TestCase):
    def test_offline_integrity_validation_and_preservation(self):
        with tempfile.TemporaryDirectory(prefix="two-view-qualification-") as directory:
            root = Path(directory)
            ok, encoded = cv2.imencode(".png", np.zeros((1000, 1600, 3), np.uint8))
            self.assertTrue(ok)
            raw = encoded.tobytes()
            (root / "image.png").write_bytes(raw)
            a, b, _ = scene()
            data = {
                "schema": "wright.two-view-correspondences/1",
                "images": [
                    {
                        "id": k,
                        "path": "image.png",
                        "sha256": audit.sha(raw),
                        "width_px": 1600,
                        "height_px": 1000,
                    }
                    for k in ("a", "b")
                ],
                "tracks": [
                    {
                        "id": k,
                        "observations": [dict(v, image_id=i) for i, v in obs.items()],
                    }
                    for k, obs in tracks(a, b).items()
                ],
                "pairs": [["a", "b"]],
            }
            serial = 0

            def invoke(value=None, text=None, expected=None):
                nonlocal serial
                serial += 1
                payload = (text if text is not None else json.dumps(value)).encode()
                source = root / "input.json"
                source.write_bytes(payload)
                output = root / ("out" + str(serial))
                code = audit.run(source, expected or audit.sha(payload), output)
                report = json.loads(
                    (output / "report.json").read_text(),
                    parse_constant=audit.reject_constant,
                )
                audit.finite(report)
                return code, report, source, output

            code, report, source, output = invoke(data)
            self.assertEqual(code, 0)
            self.assertEqual(report["supplied_input"], data)
            self.assertEqual(report["runtime"]["opencv"], cv2.__version__)
            before = (output / "report.json").read_bytes()
            (output / "sentinel").write_text("retain")
            with self.assertRaises(FileExistsError):
                audit.run(source, audit.sha(source.read_bytes()), output)
            self.assertEqual((output / "report.json").read_bytes(), before)
            self.assertEqual((output / "sentinel").read_text(), "retain")
            self.assertEqual(invoke(data, expected="0" * 64)[0], 2)
            for problem in (
                "image_hash",
                "dimensions",
                "track",
                "observation",
                "image",
                "pair",
                "nonfinite",
                "malformed",
            ):
                bad = copy.deepcopy(data)
                if problem == "image_hash":
                    bad["images"][0]["sha256"] = "0" * 64
                elif problem == "dimensions":
                    bad["images"][0]["width_px"] += 1
                elif problem == "track":
                    bad["tracks"].append(copy.deepcopy(bad["tracks"][0]))
                elif problem == "observation":
                    bad["tracks"][0]["observations"].append(
                        copy.deepcopy(bad["tracks"][0]["observations"][0])
                    )
                elif problem == "image":
                    bad["images"].append(copy.deepcopy(bad["images"][0]))
                elif problem == "pair":
                    bad["pairs"].append(["a", "b"])
                elif problem == "nonfinite":
                    bad["tracks"][0]["observations"][0]["uv_px"][0] = float("inf")
                else:
                    bad["tracks"][0]["observations"][0]["uv_px"] = [1]
                with self.subTest(problem=problem):
                    code, report, _, _ = invoke(bad)
                    self.assertEqual(code, 2)
                    self.assertIn("error", report)
            for text in ('{"x":1,"x":2}', '{"x":1e400}', '{"x":NaN}'):
                self.assertEqual(invoke(text=text)[0], 2)


if __name__ == "__main__":
    unittest.main()
