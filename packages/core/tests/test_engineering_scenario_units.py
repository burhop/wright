from __future__ import annotations

from decimal import Decimal

import pytest

from core.engineering_scenarios import EngineeringScenarioError, convert_unit


@pytest.mark.parametrize(
    ("value", "source", "target", "expected"),
    [
        (1000, "mm", "m", Decimal("1")),
        (1_000_000, "mm2", "m2", Decimal("1")),
        (1_000_000_000, "mm3", "m3", Decimal("1")),
        (1000, "g", "kg", Decimal("1")),
        (1000, "ms", "s", Decimal("1")),
        (0, "degC", "K", Decimal("273.15")),
        (1, "delta_degC", "delta_K", Decimal("1")),
        (180, "deg", "rad", Decimal("3.141592653589792999999999999")),
        (1, "kN", "N", Decimal("1000")),
        (1, "MPa", "Pa", Decimal("1000000")),
        (1000, "mm/s", "m/s", Decimal("1")),
        (1, "kW", "W", Decimal("1000")),
        (1, "kJ", "J", Decimal("1000")),
        (50, "%", "1", Decimal("0.50")),
    ],
)
def test_unit_conversion(value, source, target, expected) -> None:
    actual = convert_unit(value, source, target)
    assert actual == expected


def test_unit_dimension_mismatch_fails_closed() -> None:
    with pytest.raises(EngineeringScenarioError) as error:
        convert_unit(1, "mm", "MPa")
    assert error.value.code == "unit_dimension_mismatch"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), "NaN"])
def test_non_finite_values_are_rejected(value) -> None:
    with pytest.raises(EngineeringScenarioError) as error:
        convert_unit(value, "m", "mm")
    assert error.value.code == "non_finite_value"
