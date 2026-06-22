import os
import yaml
from typing import List, Optional
from .schemas import CatalogEntry


class CatalogLoader:
    """Manages loading, parsing, searching, and filtering of catalog entries."""

    def __init__(self, catalog_path: Optional[str] = None):
        """Initializes the loader. Loads catalog from path or default location."""
        if catalog_path is None:
            catalog_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "catalog.yaml"
            )

        self.catalog_path = catalog_path
        self.entries: List[CatalogEntry] = []
        self._load()

    def _load(self):
        """Loads and validates the catalog file."""
        if not os.path.exists(self.catalog_path):
            raise FileNotFoundError(f"Catalog file not found: {self.catalog_path}")

        with open(self.catalog_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        servers_data = data.get("servers", [])
        seen_ids = set()

        for entry_dict in servers_data:
            entry = CatalogEntry.model_validate(entry_dict)
            if entry.id in seen_ids:
                raise ValueError(f"Duplicate catalog entry ID found: {entry.id}")
            seen_ids.add(entry.id)
            self.entries.append(entry)

    def get_all(self) -> List[CatalogEntry]:
        """Returns all loaded catalog entries."""
        return self.entries

    def get_by_domain(self, domain: str) -> List[CatalogEntry]:
        """Filters catalog entries by domain taxonomy tag (case-insensitive)."""
        normalized_domain = domain.strip().lower()
        return [
            entry for entry in self.entries
            if any(d.lower() == normalized_domain for d in entry.domains)
        ]

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

            if name_match or desc_match or tag_match:
                results.append(entry)
        return results
