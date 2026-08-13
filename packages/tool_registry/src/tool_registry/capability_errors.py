from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CapabilityErrorDetail:
    code: str
    message: str
    recovery: str
    status_code: int = 400


class CapabilityError(RuntimeError):
    def __init__(self, detail: CapabilityErrorDetail) -> None:
        self.detail = detail
        super().__init__(detail.message)


CATALOG_SIGNATURE_INVALID = CapabilityErrorDetail(
    "catalog_signature_invalid",
    "Catalog update signature could not be verified.",
    "Keep the current catalog and verify the configured update source.",
)
CATALOG_STALE = CapabilityErrorDetail(
    "catalog_stale",
    "Catalog update is expired or does not advance the channel sequence.",
    "Keep the current catalog and request a newer signed snapshot.",
)
IMPORT_INVALID = CapabilityErrorDetail(
    "mcp_import_invalid",
    "MCP configuration could not be normalized safely.",
    "Correct the reported fields and preview the configuration again.",
    422,
)
INSTALL_PLAN_INVALIDATED = CapabilityErrorDetail(
    "install_plan_invalidated",
    "The capability or machine state changed after review.",
    "Generate and review a new install plan.",
    409,
)
EXTERNAL_LICENSE_REQUIRED = CapabilityErrorDetail(
    "external_license_acceptance_required",
    "External license or terms must be completed independently.",
    "Review the authoritative vendor source and return after completing it yourself.",
    409,
)
