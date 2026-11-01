"""Pure polynomial surface-join construction; no vendor, runtime or policy owner.

Inputs are explicit control nets and cross-derivative coefficients. The caller
owns their engineering meaning, units, accepted boundaries and exact CAD checks.
"""

import math
import numpy as np


def elevate(control, degree):
    control = np.asarray(control, dtype=float)
    old = len(control) - 1
    if degree < old:
        raise ValueError("Degree reduction would change the boundary.")
    return np.asarray(
        [
            sum(
                (
                    math.comb(old, j)
                    * math.comb(degree - old, i - j)
                    / math.comb(degree, i)
                )
                * control[j]
                for j in range(max(0, i - (degree - old)), min(old, i) + 1)
            )
            for i in range(degree + 1)
        ]
    )


def multiply(scalar, vector):
    a, b = len(scalar) - 1, len(vector) - 1
    return np.asarray(
        [
            sum(
                (
                    scalar[j]
                    * math.comb(a, j)
                    * math.comb(b, i - j)
                    / math.comb(a + b, i)
                )
                * vector[i - j]
                for j in range(max(0, i - b), min(a, i) + 1)
            )
            for i in range(a + b + 1)
        ]
    )


def fair_join(center, wing, lambda_controls, mu_controls, *, side, numerical_guard):
    """Retain all boundary curves, change the wing's first cross-control column.

    The wing must start on center V=1 (positive) or V=0 (negative). Its new
    outward cross derivative is lambda*center_Dv + mu*shared_Du. Positive
    Bernstein lambda coefficients provide a sufficient positive-function bound.
    Regularity, physical fidelity, other joins and CAD export remain independent.
    """
    c, w = np.asarray(center, dtype=float), np.asarray(wing, dtype=float)
    lam, mu = (
        np.asarray(lambda_controls, dtype=float),
        np.asarray(mu_controls, dtype=float),
    )
    if (
        c.ndim != 3
        or w.ndim != 3
        or c.shape[2] != 3
        or w.shape[2] != 3
        or min(c.shape[:2]) < 2
        or w.shape[1] < 3
        or side not in ("positive", "negative")
        or lam.ndim != 1
        or mu.ndim != 1
        or not len(lam)
        or not len(mu)
        or not all(np.isfinite(x).all() for x in (c, w, lam, mu))
        or not (lam > 0).all()
        or not np.isfinite(numerical_guard)
        or numerical_guard <= 0
    ):
        raise ValueError(
            "Invalid control nets, positive lambda, side or numerical guard."
        )
    shared = c[:, -1] if side == "positive" else c[:, 0]
    normal_derivative = (c.shape[1] - 1) * (
        c[:, -1] - c[:, -2] if side == "positive" else c[:, 0] - c[:, 1]
    )
    along = (len(c) - 1) * np.diff(shared, axis=0)
    first, second = multiply(lam, normal_derivative), multiply(mu, along)
    degree = max(len(first), len(second), len(w), len(shared)) - 1
    common = elevate(shared, degree)
    if (
        np.linalg.norm(common - elevate(w[:, 0], degree), axis=1).max()
        > numerical_guard
    ):
        raise ValueError("The two surfaces do not have the declared common boundary.")
    cross = elevate(first, degree) + elevate(second, degree)
    columns = [common, common + cross / (w.shape[1] - 1)]
    columns.extend(elevate(w[:, j], degree) for j in range(2, w.shape[1]))
    return np.stack(columns, axis=1)
