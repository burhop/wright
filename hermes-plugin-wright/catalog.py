import os
from typing import List, Optional
from tool_registry.catalog_loader import load_catalog_entries, sort_catalog_entries

from .schemas import CatalogEntry


class CatalogLoader:
    """Manages loading, parsing, searching, and filtering of catalog entries."""

    def __init__(self, catalog_path: Optional[str] = None):
        """Initializes the loader. Loads catalog from path or default location."""
        if catalog_path is None:
            package_catalog_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "catalog.yaml"
            )
            workspace_catalog_path = os.path.join(
                os.getcwd(), "hermes-plugin-wright", "catalog.yaml"
            )
            catalog_path = (
                workspace_catalog_path
                if os.path.exists(workspace_catalog_path)
                else package_catalog_path
            )

        self.catalog_path = catalog_path
        self.entries: List[CatalogEntry] = []
        self._load()

    def _load(self):
        """Loads and validates the catalog file."""
        shared_entries = load_catalog_entries(self.catalog_path)
        self.entries = [
            CatalogEntry.model_validate(entry.model_dump(mode="json"))
            for entry in shared_entries
        ]

    def get_all(self) -> List[CatalogEntry]:
        """Returns all loaded catalog entries sorted by practical readiness."""
        return self.sorted_entries(self.entries)

    def sorted_entries(self, entries: List[CatalogEntry]) -> List[CatalogEntry]:
        """Sort entries as tested, maybe, blocked, non-working, then by name."""
        return sort_catalog_entries(entries)

    def get_by_domain(self, domain: str) -> List[CatalogEntry]:
        """Filters catalog entries by domain taxonomy tag (case-insensitive)."""
        normalized_domain = domain.strip().lower()
        return self.sorted_entries([
            entry for entry in self.entries
            if any(d.lower() == normalized_domain for d in entry.domains)
        ])

    def search(self, query: str) -> List[CatalogEntry]:
        """Performs case-insensitive free-text search across name, description, and tags."""
        normalized_query = query.strip().lower()
        if not normalized_query:
            return self.entries

        results = []
        for entry in self.entries:
            name_match = normalized_query in entry.name.lower()
            desc_match = normalized_query in entry.description.lower()
            tag_match = any(normalized_query in tag.lower() for tag in entry.tags)
            state_match = normalized_query in entry.verification_state.lower()
            tier_match = normalized_query in entry.installability_tier.lower()
            risk_match = normalized_query in entry.risk_level.lower()
            dependency_match = any(
                normalized_query in dep.lower()
                for dep in (
                    entry.dependencies.system
                    + entry.dependencies.python
                    + entry.dependencies.node
                    + entry.host_software_required
                    + entry.credentials_required
                )
            )

            if (
                name_match
                or desc_match
                or tag_match
                or state_match
                or tier_match
                or risk_match
                or dependency_match
            ):
                results.append(entry)
        return self.sorted_entries(results)
