# Quickstart: Engineering Tool Catalog

This guide details how to load the catalog loader, perform filters, and run unit tests.

## Loading the Catalog

```python
from hermes_plugin_wright.catalog import CatalogLoader

# Initialize loader
loader = CatalogLoader()

# Fetch all tools in 'cad' domain
cad_tools = loader.get_by_domain("cad")
for tool in cad_tools:
    print(f"Tool: {tool.name} (locality: {tool.locality})")

# Free-text keyword search
results = loader.search("CalculiX")
for tool in results:
    print(f"Search Result: {tool.name}")
```

## Running Unit Tests

To run validation and search unit tests:

```bash
pytest hermes-plugin-wright/tests/
```
