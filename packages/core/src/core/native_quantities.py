"""Small exact quantity vocabulary for the native process language."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, Inexact, InvalidOperation, Overflow, Rounded, localcontext

Dimension = tuple[int, int, int]  # length, mass, time


@dataclass(frozen=True, slots=True)
class Unit:
    dimension: Dimension
    factor: Decimal


UNITS: dict[str, Unit] = {
    "1": Unit((0, 0, 0), Decimal("1")),
    "mm": Unit((1, 0, 0), Decimal("0.001")),
    "cm": Unit((1, 0, 0), Decimal("0.01")),
    "m": Unit((1, 0, 0), Decimal("1")),
    "mm2": Unit((2, 0, 0), Decimal("0.000001")),
    "cm2": Unit((2, 0, 0), Decimal("0.0001")),
    "m2": Unit((2, 0, 0), Decimal("1")),
    "mm3": Unit((3, 0, 0), Decimal("0.000000001")),
    "cm3": Unit((3, 0, 0), Decimal("0.000001")),
    "m3": Unit((3, 0, 0), Decimal("1")),
    "g": Unit((0, 1, 0), Decimal("0.001")),
    "kg": Unit((0, 1, 0), Decimal("1")),
    "kg/m3": Unit((-3, 1, 0), Decimal("1")),
    "g/cm3": Unit((-3, 1, 0), Decimal("1000")),
    "N": Unit((1, 1, -2), Decimal("1")),
    "Pa": Unit((-1, 1, -2), Decimal("1")),
    "MPa": Unit((-1, 1, -2), Decimal("1000000")),
}
_DECIMAL = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]*[1-9])?\Z")


def decimal_value(value: str) -> Decimal:
    if not isinstance(value, str) or len(value) > 39 or not _DECIMAL.fullmatch(value):
        raise ValueError("quantity requires a canonical decimal string")
    if value == "-0":
        raise ValueError("negative zero is not permitted")
    result = Decimal(value)
    digits = result.as_tuple()
    if (
        result.copy_abs() > Decimal("1e18")
        or digits.exponent < -18
        or len(digits.digits) > 34
    ):
        raise ValueError(
            "quantity exceeds its exact magnitude, scale or precision bound"
        )
    return result


def decimal_text(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if value == 0:
        text = "0"
    decimal_value(text)
    return text


@dataclass(frozen=True, slots=True)
class Quantity:
    value: str
    unit: str

    def __post_init__(self) -> None:
        decimal_value(self.value)
        if self.unit not in UNITS:
            raise ValueError("unsupported native unit")

    @property
    def dimension(self) -> Dimension:
        return UNITS[self.unit].dimension

    def as_dict(self) -> dict[str, str]:
        return {"value": self.value, "unit": self.unit}

    def convert(self, unit: str) -> Quantity:
        if unit not in UNITS or self.dimension != UNITS[unit].dimension:
            raise ValueError("incompatible quantity conversion")
        with localcontext() as context:
            _exact_context(context)
            value = (
                decimal_value(self.value) * UNITS[self.unit].factor / UNITS[unit].factor
            )
            return Quantity(decimal_text(value), unit)

    def multiply(self, other: Quantity, unit: str) -> Quantity:
        dimension = tuple(a + b for a, b in zip(self.dimension, other.dimension))
        if unit not in UNITS or dimension != UNITS[unit].dimension:
            raise ValueError("multiplication target has incompatible dimensions")
        with localcontext() as context:
            _exact_context(context)
            value = (
                decimal_value(self.value)
                * UNITS[self.unit].factor
                * decimal_value(other.value)
                * UNITS[other.unit].factor
                / UNITS[unit].factor
            )
            return Quantity(decimal_text(value), unit)

    def compare(self, other: Quantity) -> int:
        if self.dimension != other.dimension:
            raise ValueError("cannot compare incompatible quantities")
        # Compare base values directly: an intermediate conversion need not fit
        # the public value bound when each original operand is valid.
        with localcontext() as context:
            _exact_context(context)
            left = decimal_value(self.value) * UNITS[self.unit].factor
            right = decimal_value(other.value) * UNITS[other.unit].factor
            return (left > right) - (left < right)


def _exact_context(context) -> None:
    context.prec = 68
    for signal in (Inexact, Rounded, Overflow, InvalidOperation):
        context.traps[signal] = True
