"""Provider-neutral contracts for Wright's built-in engineering templates."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Mapping


_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")


class EngineeringWorkflowTemplateError(ValueError):
    """Stable validation or selection failure for an engineering template."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


class TemplateReadinessState(StrEnum):
    REFERENCE = "reference"
    SETUP_REQUIRED = "setup_required"
    READY = "ready"
    VERIFIED = "verified"


class TemplateDefinitionStatus(StrEnum):
    REVIEWED = "reviewed"
    DEPRECATED = "deprecated"
    WITHDRAWN = "withdrawn"


@dataclass(frozen=True, slots=True)
class TemplateReadinessFact:
    code: str
    label: str
    satisfied: bool
    evidence: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not _SLUG.fullmatch(self.code) or not self.label.strip():
            raise EngineeringWorkflowTemplateError(
                "template_readiness_fact_invalid", "Template readiness fact is invalid"
            )


@dataclass(frozen=True, slots=True)
class TemplateReadiness:
    state: TemplateReadinessState
    definition_valid: bool
    configured: bool
    qualified: bool
    available: bool
    verified_run: bool
    facts: tuple[TemplateReadinessFact, ...]
    blocking_reasons: tuple[str, ...]

    def __post_init__(self) -> None:
        runnable_evidence = (
            self.definition_valid,
            self.configured,
            self.qualified,
            self.available,
        )
        if self.state in {
            TemplateReadinessState.READY,
            TemplateReadinessState.VERIFIED,
        } and not all(runnable_evidence):
            raise EngineeringWorkflowTemplateError(
                "template_readiness_overstated",
                "Runnable readiness requires definition, setup, qualification, and current availability",
            )
        if self.state is TemplateReadinessState.VERIFIED and not self.verified_run:
            raise EngineeringWorkflowTemplateError(
                "template_readiness_overstated",
                "Verified readiness requires definition, setup, qualification, availability, and a verified run",
            )


@dataclass(frozen=True, slots=True)
class EngineeringWorkflowTemplate:
    template_id: str
    version: str
    title: str
    summary: str
    discipline: str
    source_resource: str
    layout_resource: str
    preview_asset: str
    preview_alt: str
    source_digest: str
    layout_digest: str
    provided_inputs: tuple[Mapping[str, Any], ...]
    requested_inputs: tuple[Mapping[str, Any], ...]
    expected_outputs: tuple[Mapping[str, Any], ...]
    capability_requirements: tuple[Mapping[str, Any], ...]
    external_effects: tuple[str, ...]
    acceptance_profile: str
    definition_status: TemplateDefinitionStatus
    rights: Mapping[str, Any]
    readiness: TemplateReadiness

    def __post_init__(self) -> None:
        if not _SLUG.fullmatch(self.template_id):
            raise EngineeringWorkflowTemplateError(
                "template_id_invalid", "Template identity is invalid"
            )
        if not _VERSION.fullmatch(self.version):
            raise EngineeringWorkflowTemplateError(
                "template_version_invalid", "Template version is invalid"
            )
        if not all(
            value.strip() for value in (self.title, self.summary, self.discipline)
        ):
            raise EngineeringWorkflowTemplateError(
                "template_metadata_invalid", "Template display metadata is incomplete"
            )
        if not _DIGEST.fullmatch(self.source_digest) or not _DIGEST.fullmatch(
            self.layout_digest
        ):
            raise EngineeringWorkflowTemplateError(
                "template_digest_invalid", "Template resource digest is invalid"
            )
        if (
            self.definition_status is TemplateDefinitionStatus.REVIEWED
            and not self.rights
        ):
            raise EngineeringWorkflowTemplateError(
                "template_rights_missing",
                "Reviewed templates require input rights metadata",
            )

    def summary_document(self) -> dict[str, Any]:
        return {
            "template_id": self.template_id,
            "version": self.version,
            "title": self.title,
            "summary": self.summary,
            "discipline": self.discipline,
            "preview": {"asset": self.preview_asset, "alt": self.preview_alt},
            "provided_inputs": list(self.provided_inputs),
            "requested_inputs": list(self.requested_inputs),
            "expected_outputs": list(self.expected_outputs),
            "external_effects": list(self.external_effects),
            "source_digest": self.source_digest,
            "readiness": {
                "state": self.readiness.state,
                "definition_valid": self.readiness.definition_valid,
                "configured": self.readiness.configured,
                "qualified": self.readiness.qualified,
                "available": self.readiness.available,
                "verified_run": self.readiness.verified_run,
                "facts": [
                    {
                        "code": fact.code,
                        "label": fact.label,
                        "satisfied": fact.satisfied,
                        "evidence": list(fact.evidence),
                    }
                    for fact in self.readiness.facts
                ],
                "blocking_reasons": list(self.readiness.blocking_reasons),
            },
        }
