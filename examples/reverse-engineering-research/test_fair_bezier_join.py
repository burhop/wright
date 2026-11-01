"""Independent finite-difference geometry checks for polynomial join construction."""

import math
import numpy as np
import pytest
from fair_bezier_join import fair_join


def point(net, u, v):
    n, m = np.asarray(net.shape[:2]) - 1
    return sum(
        math.comb(n, i)
        * u**i
        * (1 - u) ** (n - i)
        * math.comb(m, j)
        * v**j
        * (1 - v) ** (m - j)
        * net[i, j]
        for i in range(n + 1)
        for j in range(m + 1)
    )


def fixture():
    center = np.array([[[x, y, 0.0] for y in [0.0, 1.0]] for x in [0.0, 0.5, 1.0]])
    wing = np.array(
        [
            [[x, 1.0, 0.0], [x, 1.2, 0.5], [x, 1.8, 0.7], [x, 2.0, 1.0]]
            for x in [0.0, 0.5, 1.0]
        ]
    )
    return center, wing


def test_fairing_removes_crease_and_preserves_outer_curve():
    center, wing = fixture()
    result = fair_join(
        center,
        wing,
        [1.0, 1.2, 1.0],
        [0.0, 0.1, 0.0],
        side="positive",
        numerical_guard=1e-10,
    )
    h = 1e-7
    for u in np.linspace(0.05, 0.95, 19):
        np.testing.assert_allclose(
            point(result, u, 0.0), point(center, u, 1.0), atol=1e-12
        )
        np.testing.assert_allclose(
            point(result, u, 1.0), point(wing, u, 1.0), atol=1e-12
        )
        # Independent numerical tangent-plane observation; the defective input
        # has a large nonzero Z derivative, while the repaired join is planar.
        before = (point(wing, u, h) - point(wing, u, 0.0)) / h
        after = (point(result, u, h) - point(result, u, 0.0)) / h
        assert before[2] > 1.0
        assert abs(after[2]) < 1e-6 and after[1] > 0


def test_disconnected_surfaces_and_nonpositive_lambda_are_rejected():
    center, wing = fixture()
    disconnected = wing.copy()
    disconnected[:, 0, 2] += 0.01
    with pytest.raises(ValueError, match="common boundary"):
        fair_join(
            center, disconnected, [1.0], [0.0], side="positive", numerical_guard=1e-8
        )
    with pytest.raises(ValueError, match="positive lambda"):
        fair_join(center, wing, [-1.0], [0.0], side="positive", numerical_guard=1e-8)
