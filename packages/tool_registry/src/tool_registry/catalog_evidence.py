from __future__ import annotations

from .catalog_models import CatalogEntry, EvidenceClass, conservative_evidence_class

OFFICIAL_EVIDENCE_CLASSES = frozenset({"official_production", "official_preview"})
AUTHORITATIVE_SOURCE_KINDS = frozenset({"vendor_docs", "release"})
AUTHORITATIVE_SOURCE_AUTHORITIES = frozenset({"vendor", "publisher"})


class CatalogEvidenceError(ValueError):
    """Raised when a catalog entry makes an unsupported evidence claim."""


def derive_evidence_class(entry: CatalogEntry) -> EvidenceClass:
    """Return an explicit claim or a deliberately non-official legacy mapping."""
    return entry.evidence_class or conservative_evidence_class(entry)


def validate_catalog_evidence(entry: CatalogEntry) -> None:
    """Validate evidence claims without inferring authority from branding or URLs."""
    evidence_class = derive_evidence_class(entry)
    if evidence_class not in OFFICIAL_EVIDENCE_CLASSES:
        return

    authoritative = [
        source
        for source in entry.source_records
        if source.primary
        and source.kind in AUTHORITATIVE_SOURCE_KINDS
        and source.authority in AUTHORITATIVE_SOURCE_AUTHORITIES
    ]
    if not authoritative:
        raise CatalogEvidenceError(
            f"Catalog entry '{entry.id}' claims {evidence_class} without a primary "
            "vendor or publisher source record"
        )

    if entry.maturity != "official":
        raise CatalogEvidenceError(
            f"Catalog entry '{entry.id}' claims {evidence_class} but maturity is "
            f"'{entry.maturity}'"
        )

    if evidence_class == "official_preview" and entry.default_enabled:
        raise CatalogEvidenceError(
            f"Catalog entry '{entry.id}' is an official preview and must default disabled"
        )
