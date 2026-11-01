"""Unexecuted controls using hand-specified synthetic depth arrays only.

Triangle-shaped sample footprints are fixtures, not a second rasterizer.
All depths are arbitrary numerical test values, not Roadster dimensions.
No automatic test execution or I/O occurs on import.
"""

import unittest
import numpy as np
import owner_visibility


def layer(identifier, depths, color=(255, 255, 255), shade=255):
    depth = np.array(depths, dtype=np.float64)
    return {
        "id": identifier,
        "depth": depth,
        "shade": np.full(depth.shape, shade, dtype=np.uint8),
        "color_rgb": color,
    }


class OwnerVisibilityTests(unittest.TestCase):
    def assertNativeJSON(self, value):
        # Check serializable native types without importing a JSON library.
        if type(value) is dict:
            for key, item in value.items():
                self.assertIs(type(key), str)
                self.assertNativeJSON(item)
        elif type(value) is list:
            for item in value:
                self.assertNativeJSON(item)
        else:
            self.assertIn(type(value), (str, int, float, bool, type(None)))
            if type(value) is float:
                self.assertTrue(np.isfinite(value))

    def assertCounts(self, report, expected):
        actual = {
            r["id"]: (
                r["projected"],
                r["uniquely_visible"],
                r["occluded"],
                r["nearest_tied"],
            )
            for r in report["layers"]
        }
        self.assertEqual(actual, expected)
        for projected, unique, occluded, tied in actual.values():
            self.assertEqual(projected, unique + occluded + tied)
        self.assertNativeJSON(report)

    def triangles(self):
        n = np.nan
        near = layer(
            "near", [[2, n, n, n], [2, 2, n, n], [2, 2, 2, n]], (255, 128, 1), 128
        )
        near["shade"][0, 0] = 0
        far = layer("far", [[8, 8, 8, n], [8, 8, n, n], [8, n, n, n]], (10, 20, 30))
        return [near, far]

    def test_overlapping_triangle_samples_and_partial_occlusion(self):
        owner, depth, rgb, report = owner_visibility.compose(self.triangles())
        np.testing.assert_array_equal(
            owner, [[0, 1, 1, -1], [0, 0, -1, -1], [0, 0, 0, -1]]
        )
        np.testing.assert_allclose(
            depth,
            [[2, 8, 8, np.nan], [2, 2, np.nan, np.nan], [2, 2, 2, np.nan]],
            rtol=0,
            atol=0,
            equal_nan=True,
        )
        np.testing.assert_array_equal(rgb[0, 0], [0, 0, 0])
        self.assertEqual(owner[0, 0], 0)  # black shade is not background
        np.testing.assert_array_equal(rgb[1, 1], [128, 64, 1])
        np.testing.assert_array_equal(rgb[0, 1], [10, 20, 30])
        np.testing.assert_array_equal(rgb[0, 3], [0, 0, 0])
        self.assertEqual(owner.dtype, np.dtype(np.int32))
        self.assertEqual(depth.dtype, np.dtype(np.float64))
        self.assertEqual(rgb.dtype, np.dtype(np.uint8))
        self.assertEqual(report["shape"], [3, 4])
        self.assertEqual(report["array_shapes"]["rgb"], [3, 4, 3])
        self.assertEqual(report["depth_epsilon_mm"], 0.0)
        self.assertCounts(report, {"near": (6, 6, 0, 0), "far": (6, 2, 4, 0)})
        self.assertEqual(
            report["global"],
            {"foreground": 8, "ties": 0, "uniquely_visible": 8, "background": 4},
        )

    def tie_layers(self):
        n = np.nan
        return [
            layer("a", [[4, 4, 8, 4, 4, n]]),
            layer("b", [[4, 4.25, 8, 4.25, 4.25, n]]),
            layer("c", [[9, 9, 2, 4.5, 4.375, n]]),
        ]

    def test_exact_ties_and_third_nearer_layer(self):
        owner, depth, rgb, report = owner_visibility.compose(self.tie_layers())
        np.testing.assert_array_equal(owner, [[-2, 0, 2, 0, 0, -1]])
        np.testing.assert_allclose(
            depth, [[4, 4, 2, 4, 4, np.nan]], rtol=0, atol=0, equal_nan=True
        )
        np.testing.assert_array_equal(rgb[0, 0], [255, 0, 255])
        self.assertCounts(
            report, {"a": (5, 3, 1, 1), "b": (5, 0, 4, 1), "c": (5, 1, 4, 0)}
        )
        self.assertEqual(report["global"]["ties"], 1)

    def test_epsilon_boundary_and_nontransitive_ties(self):
        owner, depth, rgb, report = owner_visibility.compose(self.tie_layers(), 0.25)
        np.testing.assert_array_equal(owner, [[-2, -2, 2, -2, -2, -1]])
        np.testing.assert_allclose(
            depth, [[4, 4, 2, 4, 4, np.nan]], rtol=0, atol=0, equal_nan=True
        )
        for column in (0, 1, 3, 4):
            np.testing.assert_array_equal(rgb[0, column], [255, 0, 255])
        self.assertCounts(
            report, {"a": (5, 0, 1, 4), "b": (5, 0, 1, 4), "c": (5, 1, 4, 0)}
        )
        self.assertEqual(report["global"]["ties"], 4)
        # A new nearer minimum makes b ineligible although a and b are close.
        owner, depth, _, report = owner_visibility.compose(
            [layer("a", [[4]]), layer("b", [[4.25]]), layer("c", [[3.875]])], 0.25
        )
        self.assertEqual(owner[0, 0], -2)
        self.assertEqual(depth[0, 0], 3.875)
        self.assertCounts(
            report, {"a": (1, 0, 0, 1), "b": (1, 0, 1, 0), "c": (1, 0, 0, 1)}
        )

    def test_multiway_tie_and_farther_occludable_layer(self):
        layers = [
            layer("a", [[2]]),
            layer("b", [[2]]),
            layer("c", [[2]]),
            layer("far", [[7]]),
        ]
        owner, depth, rgb, report = owner_visibility.compose(layers)
        self.assertEqual(owner[0, 0], -2)
        self.assertEqual(depth[0, 0], 2)
        np.testing.assert_array_equal(rgb[0, 0], [255, 0, 255])
        self.assertCounts(
            report,
            {
                "a": (1, 0, 0, 1),
                "b": (1, 0, 0, 1),
                "c": (1, 0, 0, 1),
                "far": (1, 0, 1, 0),
            },
        )
        self.assertEqual(report["global"]["foreground"], 1)
        self.assertEqual(report["global"]["ties"], 1)

    def test_all_background_and_extreme_finite_values_without_warnings(self):
        layers = [layer("a", [[np.nan, np.nan]]), layer("b", [[np.nan, np.nan]])]
        with np.errstate(all="raise"):
            owner, depth, rgb, report = owner_visibility.compose(layers)
        np.testing.assert_array_equal(owner, [[-1, -1]])
        self.assertTrue(np.isnan(depth).all())
        self.assertFalse(rgb.any())
        self.assertCounts(report, {"a": (0, 0, 0, 0), "b": (0, 0, 0, 0)})
        self.assertEqual(
            report["global"],
            {"foreground": 0, "ties": 0, "uniquely_visible": 0, "background": 2},
        )
        maximum = np.finfo(np.float64).max
        with np.errstate(all="raise"):
            owner, depth, _, _ = owner_visibility.compose(
                [layer("near", [[1, np.nan]]), layer("far", [[maximum, np.nan]])],
                maximum,
            )
        np.testing.assert_array_equal(owner, [[-2, -1]])
        self.assertEqual(depth[0, 0], 1)

    def owner_ids(self, owner, layers):
        return [
            [layers[int(index)]["id"] if index >= 0 else int(index) for index in row]
            for row in owner
        ]

    def test_order_invariance_by_ids(self):
        for original, epsilon in ((self.triangles(), 0.0), (self.tie_layers(), 0.25)):
            baseline = owner_visibility.compose(original, epsilon)
            expected_ids = self.owner_ids(baseline[0], original)
            expected_counts = {
                r["id"]: (
                    r["projected"],
                    r["uniquely_visible"],
                    r["occluded"],
                    r["nearest_tied"],
                )
                for r in baseline[3]["layers"]
            }
            orders = [list(reversed(original)), original[1:] + original[:1]]
            if len(original) == 3:
                orders.extend(
                    [
                        [original[0], original[2], original[1]],
                        [original[1], original[0], original[2]],
                        [original[2], original[0], original[1]],
                    ]
                )
            for reordered in orders:
                owner, depth, rgb, report = owner_visibility.compose(reordered, epsilon)
                self.assertEqual(self.owner_ids(owner, reordered), expected_ids)
                np.testing.assert_allclose(
                    depth, baseline[1], rtol=0, atol=0, equal_nan=True
                )
                np.testing.assert_array_equal(rgb, baseline[2])
                self.assertCounts(report, expected_counts)

    def test_ownership_does_not_depend_on_color_or_shade(self):
        layers = [
            layer("front", [[1, 2]], (255, 0, 255), 255),
            layer("rear", [[3, 2]], (255, 0, 255), 255),
        ]
        owner, _, rgb, _ = owner_visibility.compose(layers)
        np.testing.assert_array_equal(owner, [[0, -2]])
        np.testing.assert_array_equal(rgb, [[[255, 0, 255], [255, 0, 255]]])
        for item in layers:
            item["color_rgb"] = (0, 0, 0)
            item["shade"][:] = 0
        changed = owner_visibility.compose(layers)
        np.testing.assert_array_equal(changed[0], owner)
        np.testing.assert_array_equal(changed[2], [[[0, 0, 0], [255, 0, 255]]])

    def test_input_immutability_readonly_and_noncontiguous_arrays(self):
        for readonly in (False, True):
            layers = self.triangles()
            for item in layers:
                item["depth"] = item["depth"][:, ::-1]
                item["shade"] = item["shade"][:, ::-1]
                item["color_rgb"] = np.array(item["color_rgb"], dtype=np.int64)
                if readonly:
                    for key in ("depth", "shade", "color_rgb"):
                        item[key].setflags(write=False)
            snapshots = [
                (
                    tuple(item.keys()),
                    item["id"],
                    [
                        (item[key], item[key].tobytes(), item[key].flags.writeable)
                        for key in ("depth", "shade", "color_rgb")
                    ],
                )
                for item in layers
            ]
            outputs = owner_visibility.compose(layers)
            for item, (keys, identifier, arrays) in zip(layers, snapshots):
                self.assertEqual(tuple(item.keys()), keys)
                self.assertEqual(item["id"], identifier)
                for key, (original, contents, writeable) in zip(
                    ("depth", "shade", "color_rgb"), arrays
                ):
                    self.assertIs(item[key], original)
                    self.assertEqual(original.tobytes(), contents)
                    self.assertEqual(original.flags.writeable, writeable)
                    for output in outputs[:3]:
                        self.assertFalse(np.shares_memory(original, output))

    def test_bad_depth_values_including_zero_background(self):
        for bad in (0.0, -0.0, -1.0, np.inf, -np.inf):
            with self.subTest(depth=bad):
                item = layer("bad", [[np.nan, bad]])
                before = item["depth"].tobytes()
                with self.assertRaises(ValueError):
                    owner_visibility.compose([item])
                self.assertEqual(item["depth"].tobytes(), before)
        # A small strictly positive value is foreground, never zero-like background.
        owner, depth, _, _ = owner_visibility.compose([layer("small", [[1e-12]])])
        self.assertEqual(owner[0, 0], 0)
        self.assertEqual(depth[0, 0], 1e-12)

    def test_bad_epsilon(self):
        layers = [layer("a", [[1]])]
        for bad in (-1, np.nan, np.inf, -np.inf, 10**1000):
            with self.subTest(kind="value", epsilon=type(bad).__name__):
                with self.assertRaises(ValueError):
                    owner_visibility.compose(layers, bad)
        for bad in (True, np.bool_(False), "0", None, 1j, [0], np.array(0.0)):
            with self.subTest(kind="type", epsilon=type(bad).__name__):
                with self.assertRaises(TypeError):
                    owner_visibility.compose(layers, bad)
        for good in (0, np.float64(0.0), np.int64(0)):
            self.assertEqual(owner_visibility.compose(layers, good)[0][0, 0], 0)

    def test_bad_ids_layer_containers_and_missing_fields(self):
        for bad in (None, {}, "layers", iter([])):
            with self.assertRaises(TypeError):
                owner_visibility.compose(bad)
        with self.assertRaises(ValueError):
            owner_visibility.compose([])
        with self.assertRaises(TypeError):
            owner_visibility.compose([None])
        for bad, error in (("", ValueError), (7, TypeError), (None, TypeError)):
            item = layer("a", [[1]])
            item["id"] = bad
            with self.assertRaises(error):
                owner_visibility.compose([item])
        with self.assertRaises(ValueError):
            owner_visibility.compose([layer("same", [[1]]), layer("same", [[2]])])
        for key in ("id", "depth", "shade", "color_rgb"):
            item = layer("a", [[1]])
            del item[key]
            with self.assertRaises(ValueError):
                owner_visibility.compose([item])

    def test_bad_shapes_and_unsupported_array_types(self):
        for shape in ((), (2,), (1, 1, 1), (0, 2), (2, 0)):
            item = layer("a", [[1]])
            item["depth"] = np.ones(shape, dtype=np.float64)
            item["shade"] = np.ones(shape, dtype=np.uint8)
            with self.assertRaises(ValueError):
                owner_visibility.compose([item])
        item = layer("a", [[1, 2]])
        item["shade"] = np.ones((2, 1), dtype=np.uint8)
        with self.assertRaises(ValueError):
            owner_visibility.compose([item])
        with self.assertRaises(ValueError):
            owner_visibility.compose([layer("a", [[1]]), layer("b", [[1, 2]])])
        bad_dtypes = {
            "depth": (np.float32, np.int64, np.uint8, np.bool_, np.complex128, object),
            "shade": (np.float64, np.int8, np.uint16, np.bool_, object),
        }
        for key, dtypes in bad_dtypes.items():
            for dtype in dtypes:
                with self.subTest(key=key, dtype=str(dtype)):
                    item = layer("a", [[1]])
                    item[key] = np.ones((1, 1), dtype=dtype)
                    with self.assertRaises(TypeError):
                        owner_visibility.compose([item])
        for key in ("depth", "shade"):
            for bad in ([[1]], np.ma.array([[1]], mask=[[False]])):
                item = layer("a", [[1]])
                item[key] = bad
                with self.assertRaises(TypeError):
                    owner_visibility.compose([item])

    def test_bad_colors_and_valid_integer_color_containers(self):
        cases = [
            ((0, 0), ValueError),
            ((0, 0, 0, 0), ValueError),
            ((-1, 0, 0), ValueError),
            ((256, 0, 0), ValueError),
            ((True, 0, 0), TypeError),
            ((1.0, 0, 0), TypeError),
            ((np.nan, 0, 0), TypeError),
            ((np.inf, 0, 0), TypeError),
            (("1", 0, 0), TypeError),
            (None, TypeError),
            ("red", TypeError),
            (np.zeros((1, 3), dtype=np.uint8), ValueError),
            (np.array(1), ValueError),
            ([[1], [2], [3]], TypeError),
        ]
        for color, error in cases:
            with self.subTest(color=str(color)):
                item = layer("a", [[1]], color)
                with self.assertRaises(error):
                    owner_visibility.compose([item])
        for color in (
            [0, 128, 255],
            (0, 128, 255),
            np.array([0, 128, 255], dtype=np.uint8),
        ):
            rgb = owner_visibility.compose((layer("a", [[1]], color),))[2]
            np.testing.assert_array_equal(rgb[0, 0], [0, 128, 255])
