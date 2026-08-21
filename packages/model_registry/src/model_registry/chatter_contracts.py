"""Strict public contracts for Wright's local Chatter screening adapter."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping, Sequence
from enum import StrEnum
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .models import canonical_digest

CHATTER_FORMAT = "wright-chatter-forest-npz-1.0"
CHATTER_ADAPTER_ID = "wright-chatter-forest-numpy"
CHATTER_ADAPTER_VERSION = "1.0.0"
CHATTER_TASK_ID = "screen_chatter_candidates"
MAX_CANDIDATES = 100
MAX_REQUEST_BYTES = 512 * 1024
MAX_OUTPUT_BYTES = 1024 * 1024
MAX_TREES = 500
MAX_NODES = 1_000_000

FEATURE_ORDER = (
    "fntx",
    "ktx",
    "zetatx",
    "fnty",
    "kty",
    "zetaty",
    "fnwx",
    "kwx",
    "zetawx",
    "fnwy",
    "kwy",
    "zetawy",
    "ktc",
    "knc",
    "kte",
    "kne",
    "Cn",
    "d",
    "m",
    "beta_mean",
    "et",
    "ud",
    "a",
    "ft_mean",
    "omega",
    "b",
    "tooth_passing_freq",
    "frf_ratio_xy",
    "stiffness_ratio_tw",
    "radial_immersion",
    "chip_load",
    "speed_ratio_to_nat",
    "has_process_damping",
    "has_runout",
    "has_edge_coeffs",
    "n_modes",
    "tooth_spacing_std",
)
FEATURE_UNITS = (
    "Hz",
    "N/m",
    "1",
    "Hz",
    "N/m",
    "1",
    "Hz",
    "N/m",
    "1",
    "Hz",
    "N/m",
    "1",
    "N/m^2",
    "N/m^2",
    "N/m",
    "N/m",
    "N/m",
    "m",
    "1",
    "deg",
    "1",
    "1",
    "m",
    "m",
    "rpm",
    "m",
    "Hz",
    "1",
    "1",
    "1",
    "m^2",
    "1",
    "1",
    "1",
    "1",
    "1",
    "deg",
)
LOG_FEATURES = ("ktx", "kty", "kwx", "kwy", "ktc", "knc")
BINARY_FEATURES = ("has_process_damping", "has_runout", "has_edge_coeffs", "et", "ud")
PREPROCESSING_ORDER = (
    LOG_FEATURES
    + tuple(
        item
        for item in FEATURE_ORDER
        if item not in LOG_FEATURES and item not in BINARY_FEATURES
    )
    + BINARY_FEATURES
)
ALLOWED_ORIGINS = frozenset({"simulated", "identified", "measured", "assumed"})
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


class ChatterFailure(StrEnum):
    CONTRACT_INVALID = "chatter_contract_invalid"
    ARTIFACT_INVALID = "chatter_artifact_invalid"
    ARTIFACT_MISSING = "chatter_artifact_missing"
    PARITY_STALE = "chatter_parity_stale"
    RUNTIME_MISSING = "chatter_runtime_missing"
    RUNTIME_INCOMPATIBLE = "chatter_runtime_incompatible"
    APPLICABILITY_REVIEW = "chatter_applicability_review"
    RESOURCE_REJECTED = "chatter_resource_rejected"
    CANCELLED = "chatter_cancelled"
    CLEANUP_RESIDUE = "chatter_cleanup_residue"


class ChatterContractError(ValueError):
    def __init__(self, category: ChatterFailure, message: str) -> None:
        super().__init__(message)
        self.category = category.value


def _schema(name: str) -> Mapping[str, Any]:
    value = json.loads(
        files("model_registry.schemas").joinpath(name).read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(value)
    return value


def validate_schema(document: Mapping[str, Any], schema_name: str) -> None:
    errors = sorted(
        Draft202012Validator(
            _schema(schema_name), format_checker=FormatChecker()
        ).iter_errors(document),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if errors:
        raise ChatterContractError(
            ChatterFailure.CONTRACT_INVALID,
            f"Chatter contract is invalid at {list(errors[0].absolute_path)}",
        )


def validate_serving_metadata(document: Mapping[str, Any]) -> dict[str, Any]:
    value = dict(document)
    validate_schema(value, "chatter-serving-metadata.schema.json")
    material = dict(value)
    claimed = str(material.pop("metadata_digest"))
    if canonical_digest(material) != claimed:
        raise ChatterContractError(
            ChatterFailure.ARTIFACT_INVALID, "Serving metadata digest changed"
        )
    features = value["input_contract"]
    names = tuple(item["name"] for item in features)
    units = tuple(item["unit"] for item in features)
    preprocessing = value["preprocessing"]
    if (
        names != FEATURE_ORDER
        or units != FEATURE_UNITS
        or tuple(preprocessing["input_order"]) != FEATURE_ORDER
        or tuple(preprocessing["output_order"]) != PREPROCESSING_ORDER
        or tuple(preprocessing["log_features"]) != LOG_FEATURES
        or tuple(preprocessing["binary_features"]) != BINARY_FEATURES
    ):
        raise ChatterContractError(
            ChatterFailure.CONTRACT_INVALID, "Chatter feature contract changed"
        )
    for feature in features:
        if (
            feature["contract_min"] > feature["population_min"]
            or feature["population_min"] > feature["population_max"]
            or feature["population_max"] > feature["contract_max"]
            or not set(feature["allowed_origins"]) <= ALLOWED_ORIGINS
        ):
            raise ChatterContractError(
                ChatterFailure.CONTRACT_INVALID, "Chatter feature bounds are invalid"
            )
    return value


def validate_candidate_batch(
    document: Mapping[str, Any], metadata: Mapping[str, Any]
) -> dict[str, Any]:
    try:
        encoded = json.dumps(
            document, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ChatterContractError(
            ChatterFailure.CONTRACT_INVALID, "Candidate batch is not finite JSON"
        ) from error
    if len(encoded) > MAX_REQUEST_BYTES:
        raise ChatterContractError(
            ChatterFailure.RESOURCE_REJECTED, "Candidate batch exceeds its byte limit"
        )
    value = dict(document)
    validate_schema(value, "chatter-candidate-batch.schema.json")
    serving = validate_serving_metadata(metadata)
    if (
        tuple(value["feature_order"]) != FEATURE_ORDER
        or tuple(value["units"]) != FEATURE_UNITS
    ):
        raise ChatterContractError(
            ChatterFailure.CONTRACT_INVALID, "Candidate feature order or units changed"
        )
    candidates = value["candidates"]
    identities = [str(item["candidate_id"]) for item in candidates]
    if len(identities) != len(set(identities)) or any(
        not _ID.fullmatch(item) for item in identities
    ):
        raise ChatterContractError(
            ChatterFailure.CONTRACT_INVALID,
            "Candidate identity is invalid or duplicated",
        )
    contracts = serving["input_contract"]
    for candidate in candidates:
        for index, raw in enumerate(candidate["values"]):
            if (
                isinstance(raw, bool)
                or not isinstance(raw, (int, float))
                or not math.isfinite(float(raw))
            ):
                raise ChatterContractError(
                    ChatterFailure.CONTRACT_INVALID,
                    "Candidate value must be finite numeric data",
                )
            contract = contracts[index]
            if not contract["contract_min"] <= float(raw) <= contract["contract_max"]:
                raise ChatterContractError(
                    ChatterFailure.CONTRACT_INVALID,
                    "Candidate value is outside the contract range",
                )
            if candidate["origins"][index] not in contract["allowed_origins"]:
                raise ChatterContractError(
                    ChatterFailure.CONTRACT_INVALID,
                    "Candidate value origin is not permitted",
                )
    return value


def result_material(
    *,
    results: Sequence[Mapping[str, Any]],
    model_evidence: Mapping[str, Any],
    input_digest: str,
) -> dict[str, Any]:
    body = {
        "schema_version": "1.0",
        "results": [dict(item) for item in results],
        "model_evidence": dict(model_evidence),
        "input_digest": input_digest,
    }
    output_digest = canonical_digest(body["results"])
    material_digest = canonical_digest({**body, "output_digest": output_digest})
    return {**body, "output_digest": output_digest, "material_digest": material_digest}


__all__ = [
    "ALLOWED_ORIGINS",
    "BINARY_FEATURES",
    "CHATTER_ADAPTER_ID",
    "CHATTER_ADAPTER_VERSION",
    "CHATTER_FORMAT",
    "CHATTER_TASK_ID",
    "ChatterContractError",
    "ChatterFailure",
    "FEATURE_ORDER",
    "FEATURE_UNITS",
    "LOG_FEATURES",
    "MAX_CANDIDATES",
    "MAX_NODES",
    "MAX_OUTPUT_BYTES",
    "MAX_REQUEST_BYTES",
    "MAX_TREES",
    "PREPROCESSING_ORDER",
    "result_material",
    "validate_candidate_batch",
    "validate_schema",
    "validate_serving_metadata",
]
