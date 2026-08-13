"""Small deterministic generated artifacts used by Wright's normal model gates."""

from __future__ import annotations

import hashlib

from .models import ModelPackage, canonical_json


def affine_artifacts(package: ModelPackage) -> dict[str, bytes]:
    """Regenerate the reviewed affine fixture and verify every declared identity."""

    if package.model_id != "wright-affine-test":
        raise ValueError("The package has no built-in deterministic generator")
    coefficients = {"offset": 1.0, "scale": 2.0}
    values = {
        "LICENSE": b"MIT License\n\nCopyright Wright Project contributors.\n",
        "model/coefficients.json": canonical_json(coefficients).encode("utf-8"),
        "tests/predict-two-input.json": canonical_json({"x": 2.0}).encode("utf-8"),
        "tests/predict-two-expected.json": canonical_json({"y": 5.0}).encode("utf-8"),
    }
    declarations = {
        item.path: item for variant in package.variants for item in variant.artifacts
    }
    if set(values) != set(declarations):
        raise ValueError("Generated artifact declarations changed")
    for path, value in values.items():
        declaration = declarations[path]
        if (
            len(value) != declaration.size
            or hashlib.sha256(value).hexdigest() != declaration.sha256
        ):
            raise ValueError("Generated artifact identity changed")
    return values


__all__ = ["affine_artifacts"]
