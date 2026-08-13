from __future__ import annotations

from hashlib import sha256

import pytest

from core.engineering_scenarios import (
    ArtifactProducer,
    AssertionCategory,
    AssertionResult,
    AssertionState,
    EngineeringScenarioError,
    NormalizedArtifact,
)


DIGEST = sha256(b"artifact").hexdigest()


def producer() -> ArtifactProducer:
    return ArtifactProducer("run-1", "node-cad", "call-1", "cad__build")


def test_artifact_requires_exactly_one_storage_form() -> None:
    with pytest.raises(EngineeringScenarioError, match="exactly one"):
        NormalizedArtifact(
            artifact_id="cad-mesh",
            domain="cad",
            kind="mesh",
            source_schema={"name": "wright-mesh", "version": "1.0"},
            producer=producer(),
            upstream_digests=(),
            content_digest=DIGEST,
            validation_state="valid",
        )


def test_artifact_rejects_secret_like_content() -> None:
    with pytest.raises(ValueError, match="secret-like"):
        NormalizedArtifact(
            artifact_id="cad-mesh",
            domain="cad",
            kind="mesh",
            source_schema={"name": "wright-mesh", "version": "1.0"},
            producer=producer(),
            upstream_digests=(),
            content_digest=DIGEST,
            validation_state="valid",
            content={"api_key": "not-permitted"},
        )


def test_failed_assertion_requires_actionable_diagnostic() -> None:
    with pytest.raises(EngineeringScenarioError, match="message and recovery"):
        AssertionResult(
            assertion_id="stress-limit",
            plugin="numeric",
            plugin_version="1.0",
            state=AssertionState.FAIL,
            category=AssertionCategory.NUMERIC,
            reason_code="range_exceeded",
            artifact_digests=(DIGEST,),
            producer={"node_id": "node-fea", "capability": "fea__solve"},
        )


def test_assertion_digest_is_deterministic() -> None:
    result = AssertionResult(
        assertion_id="stress-limit",
        plugin="numeric",
        plugin_version="1.0",
        state=AssertionState.PASS,
        category=AssertionCategory.NUMERIC,
        reason_code="within_range",
        artifact_digests=(DIGEST,),
        producer={"node_id": "node-fea", "capability": "fea__solve"},
        expected={"maximum": 100, "unit": "MPa"},
        observed={"value": 80, "unit": "MPa"},
    )

    assert result.digest == result.digest
    assert len(result.digest) == 64
