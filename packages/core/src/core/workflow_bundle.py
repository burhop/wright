"""Portable definition data, deliberately excluding run and permission records."""

from __future__ import annotations

import base64
import binascii
import hashlib
import re
from typing import Annotated, Literal

from pydantic import Field, StrictStr, field_validator, model_validator

from .process_interfaces import InterfaceManifest, SourceEnvelope
from .process_validation import Contract, Digest, Identifier, canonical_json

BUNDLE_MAX_BYTES = 20 * 1024 * 1024
ASSET_MAX_BYTES = 8 * 1024 * 1024


def portable_path(value: str) -> str:
    """One unambiguous cross-platform spelling, never an authority location."""
    if not isinstance(value, str) or not 1 <= len(value) <= 256:
        raise ValueError("Bundle path must be a bounded relative path")
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_./ -]*", value):
        raise ValueError("Bundle path contains unsupported characters")
    parts = value.split("/")
    if value.casefold().endswith((".pem", ".key", ".p12", ".pfx")):
        raise ValueError("Credential/key files cannot be transferred")
    for part in parts:
        stem = part.split(".")[0].casefold()
        if (
            not part
            or part in {".", ".."}
            or part.startswith(".")
            or part.endswith((".", " "))
            or stem
            in {
                "con",
                "prn",
                "aux",
                "nul",
                *(f"com{i}" for i in range(1, 10)),
                *(f"lpt{i}" for i in range(1, 10)),
            }
            or stem in {"credentials", "secrets", "id_rsa", "id_ed25519"}
        ):
            raise ValueError(
                "Bundle paths cannot contain hidden, reserved or credential locations"
            )
    if parts[0].casefold() in {"runs", "node_modules", "workflows"}:
        raise ValueError(
            "Assets cannot overwrite workflows, runs or executable dependency trees"
        )
    return value


class BundleAsset(Contract):
    path: StrictStr
    sha256: Digest
    data_base64: Annotated[StrictStr, Field(max_length=11_184_812)]

    _path = field_validator("path")(portable_path)

    def decoded(self) -> bytes:
        try:
            return base64.b64decode(self.data_base64, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ValueError("Bundle asset is not valid base64") from exc

    @model_validator(mode="after")
    def exact_bytes(self):
        content = self.decoded()
        if (
            len(content) > ASSET_MAX_BYTES
            or hashlib.sha256(content).hexdigest() != self.sha256
        ):
            raise ValueError("Bundle asset is oversized or differs from its digest")
        return self


class BundleDependency(Contract):
    category: Literal[
        "reference", "validation_profile", "provider", "model", "instructions", "ui"
    ]
    identity: Annotated[StrictStr, Field(min_length=1, max_length=1024)]
    disposition: Literal["embedded", "external"]
    sha256: Digest | None = None
    details: dict = Field(default_factory=dict)


class PortableInterface(Contract):
    """An editable candidate, never a transferable trusted build or approval."""

    manifest: InterfaceManifest
    source: SourceEnvelope
    source_digest: Digest

    @model_validator(mode="after")
    def exact_source(self):
        from .process_validation import canonical_digest

        if canonical_digest(self.source) != self.source_digest:
            raise ValueError("Interface source differs from its saved digest")
        return self


class ImportedInterfaceReference(Contract):
    """A selected local candidate's bytes, without transferred build authority."""

    ui_id: Identifier
    sha256: Digest


class WorkflowBundle(Contract):
    schema_version: Literal["wright.workflow-bundle/1"] = "wright.workflow-bundle/1"
    mode: Literal["source", "bundle"]
    source: Annotated[StrictStr, Field(max_length=1_048_576)]
    source_digest: Digest
    layout: dict | None = None
    assets: tuple[BundleAsset, ...] = Field(default=(), max_length=64)
    dependencies: tuple[BundleDependency, ...] = Field(default=(), max_length=256)
    interfaces: tuple[PortableInterface, ...] = Field(default=(), max_length=16)

    @model_validator(mode="after")
    def integrity(self):
        if len(self.source.encode("utf-8")) > 1_048_576:
            raise ValueError("Source exceeds the 1 MiB UTF-8 bound")
        if (
            hashlib.sha256(self.source.encode("utf-8")).hexdigest()
            != self.source_digest
        ):
            raise ValueError("Bundle source differs from its digest")
        paths = [asset.path.casefold() for asset in self.assets]
        if len(set(paths)) != len(paths) or any(
            left.startswith(right + "/")
            for left in paths
            for right in paths
            if left != right
        ):
            raise ValueError(
                "Bundle paths are duplicated or conflict as files/directories"
            )
        identities = [(d.category, d.identity) for d in self.dependencies]
        if len(set(identities)) != len(identities):
            raise ValueError("Bundle dependency identities are duplicated")
        ui_ids = [ui.manifest.ui_id for ui in self.interfaces]
        if len(set(ui_ids)) != len(ui_ids):
            raise ValueError("Bundle interfaces are duplicated")
        if self.mode == "source" and (self.assets or self.interfaces):
            raise ValueError("Source export cannot contain assets or interface source")
        if len(canonical_json(self).encode("utf-8")) > BUNDLE_MAX_BYTES:
            raise ValueError("Bundle exceeds the 20 MiB serialized bound")
        return self


class BundleDiagnostic(Contract):
    code: StrictStr
    severity: Literal["error", "warning"]
    message: StrictStr
    dependency: StrictStr | None = None


class BundleInspection(Contract):
    bundle_digest: Digest
    can_import: bool
    can_run: Literal[False] = False
    diagnostics: tuple[BundleDiagnostic, ...]
    external_dependencies: tuple[BundleDependency, ...]
    requirements: tuple[BundleDependency, ...]
