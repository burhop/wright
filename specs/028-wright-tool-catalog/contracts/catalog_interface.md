# Interface Contracts: Engineering Tool Catalog

This document defines the interface contracts for loading, filtering, and searching catalog entries.

## 1. CatalogLoader Interface

The `CatalogLoader` class manages loading the catalog entries from `catalog.yaml` and providing query APIs.

### Methods

#### Initialization
```python
def __init__(self, catalog_path: Optional[str] = None):
    """
    Initializes loader. Loads catalog from catalog_path or default path.
    Raises YAML compilation/validation errors if the catalog is malformed.
    """
```

#### Get All Entries
```python
def get_all(self) -> list[CatalogEntry]:
    """Returns all loaded catalog entries."""
```

#### Filter by Domain
```python
def get_by_domain(self, domain: str) -> list[CatalogEntry]:
    """
    Returns entries matching a domain in the taxonomy.
    Matches must be case-insensitive.
    """
```

#### Keyword Search
```python
def search(self, query: str) -> list[CatalogEntry]:
    """
    Performs case-insensitive free-text search across name, description,
    and tags. Returns list of matches.
    """
```
