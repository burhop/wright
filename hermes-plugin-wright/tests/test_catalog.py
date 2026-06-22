import pytest
import os
import tempfile
import yaml
from hermes_plugin_wright.catalog import CatalogLoader
from hermes_plugin_wright.schemas import CatalogEntry


def test_default_catalog_loads():
    loader = CatalogLoader()
    entries = loader.get_all()
    assert len(entries) >= 30
    
    # Check that FreeCAD and OnShape are in there
    ids = [entry.id for entry in entries]
    assert "freecad-mcp-sandraschi" in ids
    assert "jarvis-onshape-mcp" in ids


def test_domain_filtering():
    loader = CatalogLoader()
    cad_tools = loader.get_by_domain("cad")
    assert len(cad_tools) > 0
    for tool in cad_tools:
        assert any(d.lower() == "cad" for d in tool.domains)

    # Case insensitivity test
    cad_tools_upper = loader.get_by_domain("CAD")
    assert len(cad_tools_upper) == len(cad_tools)


def test_keyword_search():
    loader = CatalogLoader()

    # Search by partial name
    freecad_results = loader.search("freecad")
    assert len(freecad_results) > 0
    assert any("FreeCAD" in tool.name for tool in freecad_results)

    # Search by description content
    fea_results = loader.search("CalculiX")
    assert len(fea_results) > 0
    assert any("freecad" in tool.id for tool in fea_results)

    # Search by tag
    rest_results = loader.search("rest-api")
    assert len(rest_results) > 0
    assert any(tool.id == "jarvis-onshape-mcp" for tool in rest_results)


def test_validation_errors():
    invalid_data = {
        "servers": [
            {
                "id": "invalid-transport",
                "name": "Invalid Tool",
                "vendor": "Test",
                "description": "Test",
                "domains": ["cad"],
                "transport": "invalid-value",  # Should fail literal stdio/sse/webmcp
                "command": "python test.py",
                "locality": "local",
                "weight": "light"
            }
        ]
    }

    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w+", delete=False) as f:
        yaml.dump(invalid_data, f)
        temp_name = f.name

    try:
        with pytest.raises(Exception):
            CatalogLoader(temp_name)
    finally:
        os.remove(temp_name)


def test_duplicate_ids():
    duplicate_data = {
        "servers": [
            {
                "id": "dup-id",
                "name": "Tool 1",
                "vendor": "Test",
                "description": "Test",
                "domains": ["cad"],
                "transport": "stdio",
                "command": "test",
                "locality": "local",
                "weight": "light"
            },
            {
                "id": "dup-id",
                "name": "Tool 2",
                "vendor": "Test",
                "description": "Test",
                "domains": ["fea"],
                "transport": "stdio",
                "command": "test",
                "locality": "local",
                "weight": "light"
            }
        ]
    }

    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w+", delete=False) as f:
        yaml.dump(duplicate_data, f)
        temp_name = f.name

    try:
        with pytest.raises(ValueError) as excinfo:
            CatalogLoader(temp_name)
        assert "Duplicate catalog entry ID" in str(excinfo.value)
    finally:
        os.remove(temp_name)
