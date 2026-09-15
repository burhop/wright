from __future__ import annotations

import pytest

from core.engineering_workflow_templates import (
    EngineeringWorkflowTemplateError,
    TemplateReadiness,
    TemplateReadinessState,
)


@pytest.mark.parametrize(
    "missing",
    ["definition_valid", "configured", "qualified", "available"],
)
def test_discovery_or_partial_evidence_cannot_promote_template_to_ready(missing):
    evidence = {
        "definition_valid": True,
        "configured": True,
        "qualified": True,
        "available": True,
    }
    evidence[missing] = False
    with pytest.raises(EngineeringWorkflowTemplateError) as error:
        TemplateReadiness(
            state=TemplateReadinessState.READY,
            verified_run=False,
            facts=(),
            blocking_reasons=("Qualification is incomplete.",),
            **evidence,
        )
    assert error.value.code == "template_readiness_overstated"


def test_verified_requires_a_real_verified_run_in_addition_to_ready_evidence():
    with pytest.raises(EngineeringWorkflowTemplateError) as error:
        TemplateReadiness(
            state=TemplateReadinessState.VERIFIED,
            definition_valid=True,
            configured=True,
            qualified=True,
            available=True,
            verified_run=False,
            facts=(),
            blocking_reasons=("No verified run evidence exists.",),
        )
    assert error.value.code == "template_readiness_overstated"


def test_reference_state_can_truthfully_retain_partial_discovery_evidence():
    readiness = TemplateReadiness(
        state=TemplateReadinessState.REFERENCE,
        definition_valid=True,
        configured=False,
        qualified=False,
        available=False,
        verified_run=False,
        facts=(),
        blocking_reasons=("The candidate adapter is unqualified.",),
    )
    assert readiness.state is TemplateReadinessState.REFERENCE
