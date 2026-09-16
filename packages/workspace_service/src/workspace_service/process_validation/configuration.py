"""Closed, non-executable validator configuration in canonical process source."""

from typing import Annotated, Literal
import re

from pydantic import Field, model_validator

from core.process_validation import (
    Contract,
    Identifier,
    ResourceBudget,
    VersionReference,
)
from .profiles import load_profile


class ProfileLocation(Contract):
    source: Literal["packaged", "workspace"]
    name: Annotated[str, Field(min_length=1, max_length=256)]
    reference: VersionReference

    @model_validator(mode="after")
    def safe_location(self):
        if self.source == "packaged":
            if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,127}", self.name):
                raise ValueError("Use a packaged profile name")
        else:
            from ..workflow_source_execution import _safe_path

            _safe_path(self.name)
            if not self.name.endswith(".json"):
                raise ValueError("Workspace profiles must be JSON files")
        return self


class ValidatorConfiguration(Contract):
    profile: ProfileLocation
    baseline: VersionReference
    subjects: Annotated[
        dict[Identifier, Identifier], Field(min_length=1, max_length=32)
    ]
    budget: ResourceBudget = Field(default_factory=ResourceBudget)

    @model_validator(mode="after")
    def unique_ports(self):
        if len(set(self.subjects.values())) != len(self.subjects):
            raise ValueError("Each subject role needs a distinct input port")
        return self

    def load(self, workspace_root: str):
        profile = load_profile(
            self.profile.name,
            expected=self.profile.reference,
            workspace_root=workspace_root
            if self.profile.source == "workspace"
            else None,
        )
        if profile.baseline.reference() != self.baseline:
            raise ValueError("Requirement baseline differs from the pinned baseline")
        if {check.subject_role for check in profile.checks} != set(self.subjects):
            raise ValueError("Bind exactly the subject roles declared in this profile")
        return profile


def compile_validator(block_id, fields, incoming, blocks):
    """Compile an ordinary task; no separate graph, provider or execution engine."""
    from ..workflow_source_execution import PromptStep, _invalid

    settings = fields["settings"]
    try:
        config = ValidatorConfiguration.model_validate(settings.get("validation"))
    except ValueError as exc:
        raise _invalid(
            f"{fields['name']}: invalid validator configuration.", str(exc)
        ) from exc
    if (
        fields.get("step_type") != "work"
        or fields.get("performed_by") != "configured_tool"
        or fields.get("tool") is not None
        or fields.get("reusable_step") is not None
        or fields.get("prompt", "").strip()
        or set(settings)
        - {"authoring_template", "validation", "max_revisions", "output_format"}
        or settings.get("output_format", "json") != "json"
    ):
        raise _invalid(
            "Use a configured validator with a profile and subject bindings; it does not run prompts or tools."
        )
    limit = settings.get("max_revisions", 0)
    if type(limit) is not int or not 0 <= limit <= 3:
        raise _invalid("Set a validator revision limit from zero to three.")
    inputs, outputs = fields.get("inputs", []), fields.get("outputs", [])
    if (
        {port["key"] for port in inputs} != set(config.subjects.values())
        or any(port.get("quantity", "one") != "one" for port in inputs)
        or len(outputs) != 1
        or outputs[0].get("kind") != "engineering_document"
        or outputs[0].get("quantity", "one") != "one"
    ):
        raise _invalid(
            "Bind every validator input to one subject role and declare one assessment document output."
        )
    bindings = []
    for role, port_key in config.subjects.items():
        sources = incoming.get(f"{block_id}.{port_key}", [])
        if len(sources) != 1 or blocks[sources[0].split(".")[0]]["kind"] != "task":
            raise _invalid(
                "Connect each validator subject to exactly one producing task output."
            )
        bindings.append((role, sources[0]))
    return PromptStep(
        block_id,
        fields["name"],
        "",
        None,
        (),
        "json",
        "",
        False,
        "indexed",
        output_ports=((outputs[0]["key"], "engineering_document"),),
        design_check=True,
        max_revisions=limit,
        validation=config.model_dump(mode="json"),
        validation_sources=tuple(bindings),
    )
