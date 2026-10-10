"""Installed, versioned presentation-authoring instructions and fixed resources."""

from dataclasses import dataclass
from importlib.resources import files
import hashlib
import json

from core.process_interfaces import InterfaceManifest, SourceEnvelope
from core.process_validation import Contract

RESOURCE_VERSION = "process-ui-author-2"


class AuthoringOutput(Contract):
    source: SourceEnvelope
    manifest: InterfaceManifest


@dataclass(frozen=True)
class AuthoringResources:
    version: str
    instructions: str
    instructions_digest: str
    template: str
    output_schema: dict
    resource_digest: str


def load_authoring_resources() -> AuthoringResources:
    """No checkout, model call, dependency download or code execution required."""
    resources = files(__package__)
    instructions = resources.joinpath("instructions.md").read_text(encoding="utf-8")
    contract = resources.joinpath("public-api.md").read_text(encoding="utf-8")
    template = resources.joinpath("reference.tsx").read_text(encoding="utf-8")
    effective = instructions + "\n\n" + contract
    schema = AuthoringOutput.model_json_schema()
    digest = hashlib.sha256(
        json.dumps(
            {
                "version": RESOURCE_VERSION,
                "instructions": effective,
                "template": template,
                "output_schema": schema,
            },
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return AuthoringResources(
        RESOURCE_VERSION,
        effective,
        hashlib.sha256(effective.encode("utf-8")).hexdigest(),
        template,
        schema,
        digest,
    )
