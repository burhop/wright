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


def test_oasis_fea_entry_is_searchable():
    loader = CatalogLoader()

    fea_results = loader.get_by_domain("fea")
    assert any(tool.id == "oasis-open-fem-agent" for tool in fea_results)

    oasis = next(tool for tool in loader.search("scikit-fem") if tool.id == "oasis-open-fem-agent")
    assert oasis.installability_tier == "tested"
    assert oasis.validation_result.status == "passed"
    assert oasis.platform_support["linux_x64"].tested is True


def test_freecad_engineering_records_false_success_failure():
    loader = CatalogLoader()

    freecad = next(
        tool
        for tool in loader.get_all()
        if tool.id == "freecad-mcp-sandraschi"
    )
    assert freecad.command == [
        "uv",
        "run",
        "--with",
        "git+https://github.com/sandraschi/freecad-mcp.git",
        "python",
        "-m",
        "freecad_mcp.server",
        "--mode",
        "stdio",
    ]
    assert freecad.installability_tier == "non_working"
    assert freecad.validation_result.status == "failed"
    assert freecad.platform_support["linux_x64"].status == "no"
    assert freecad.platform_support["linux_x64"].tested is True
    assert freecad.env_vars[0].name == "FREECAD_PATH"
    assert "94" in freecad.validation_result.message
    assert "Cannot create a mesh out of a 'Part.Solid'" in freecad.validation_result.message
    assert freecad.follow_up_url == "docs/mcp-catalog/followups/freecad-engineering-sandraschi.md"


def test_caid_entry_records_validated_opencascade_stack():
    loader = CatalogLoader()

    caid = next(
        tool
        for tool in loader.search("opencascade")
        if tool.id == "caid-mcp"
    )
    assert caid.command == ["python", "server.py"]
    assert caid.installability_tier == "tested"
    assert caid.validation_result.status == "passed"
    assert "libgl1" in caid.dependencies.system
    assert caid.platform_support["linux_x64"].tested is True


def test_openscad_renderer_entry_is_tested_and_gateway_validated():
    loader = CatalogLoader()

    openscad = next(
        tool
        for tool in loader.search("openscad")
        if tool.id == "openscad-mcp"
    )
    assert openscad.command[:4] == ["uv", "run", "--with", "git+https://github.com/quellant/openscad-mcp.git"]
    assert openscad.installability_tier == "tested"
    assert openscad.validation_result.status == "passed"
    assert openscad.platform_support["linux_x64"].status == "yes"


def test_openscad_linter_entry_records_failed_source_verification():
    loader = CatalogLoader()

    linter = next(
        tool
        for tool in loader.search("linter")
        if tool.id == "trikos529-openscad"
    )
    assert linter.installability_tier == "non_working"
    assert linter.validation_result.status == "failed"
    assert linter.follow_up_url == "docs/mcp-catalog/followups/openscad-linter-trikos529.md"
    assert "not found" in linter.validation_result.message


def test_autocad_entry_records_headless_ezdxf_validation():
    loader = CatalogLoader()

    autocad = next(
        tool
        for tool in loader.search("autocad")
        if tool.id == "autocad-mcp"
    )
    assert autocad.command == [
        "uv",
        "run",
        "--with",
        "git+https://github.com/hvkshetry/autocad-mcp.git",
        "python",
        "-m",
        "autocad_mcp",
    ]
    assert autocad.installability_tier == "tested"
    assert autocad.validation_result.status == "passed"
    assert autocad.platform_support["linux_x64"].tested is True
    assert autocad.env_vars[0].name == "AUTOCAD_MCP_BACKEND"


def test_easy_autocad_entry_records_windows_com_dependency():
    loader = CatalogLoader()

    easy = next(
        tool
        for tool in loader.get_all()
        if tool.id == "easy-mcp-autocad"
    )
    assert easy.command == ["python", "server.py"]
    assert easy.installability_tier == "might_work"
    assert easy.validation_result.status == "dependency_missing"
    assert easy.platform_support["linux_x64"].status == "no"
    assert easy.platform_support["linux_x64"].tested is True
    assert easy.validation_result.missing_dependencies == [
        "Windows COM",
        "pywin32",
        "AutoCAD 2018+",
    ]
    assert easy.host_software_required == [
        "Windows",
        "AutoCAD 2018+",
        "pywin32",
        "COM interface",
    ]


def test_fusion360_entry_records_mock_pass_and_missing_desktop():
    loader = CatalogLoader()

    fusion = next(
        tool
        for tool in loader.get_all()
        if tool.id == "fusion360-mcp-server"
    )
    assert fusion.command == [
        "uv",
        "run",
        "--with",
        "fusion360-mcp-server",
        "fusion360-mcp-server",
        "--mode",
        "socket",
    ]
    assert fusion.installability_tier == "might_work"
    assert fusion.validation_result.status == "dependency_missing"
    assert fusion.platform_support["linux_x64"].status == "no"
    assert fusion.platform_support["linux_x64"].tested is True
    assert fusion.validation_result.missing_dependencies == [
        "Fusion 360 desktop",
        "Fusion360MCP add-in",
    ]


def test_autodesk_fusion_python_entry_records_auth_helper_failure():
    loader = CatalogLoader()

    fusion = next(
        tool
        for tool in loader.get_all()
        if tool.id == "autodesk-fusion-mcp-python"
    )
    assert fusion.command == ["python", "fusion_mcp.py"]
    assert fusion.installability_tier == "non_working"
    assert fusion.validation_result.status == "failed"
    assert fusion.platform_support["linux_x64"].status == "no"
    assert fusion.platform_support["linux_x64"].tested is True
    assert fusion.validation_result.missing_dependencies == [
        "Fusion 360",
        "APS_CLIENT_ID",
        "APS_CLIENT_SECRET",
        "FUSION_ACTIVITY_ID",
    ]
    assert "BasicAuth" in fusion.validation_result.message
    assert "listed one tool" in fusion.validation_result.message
    assert fusion.follow_up_url == "docs/mcp-catalog/followups/autodesk-fusion-mcp-python.md"


def test_aps_node_entry_records_required_ssa_credentials():
    loader = CatalogLoader()

    aps = next(
        tool
        for tool in loader.get_all()
        if tool.id == "aps-mcp-server-nodejs"
    )
    assert aps.command == ["node", "server.js"]
    assert aps.installability_tier == "might_work"
    assert aps.validation_result.status == "dependency_missing"
    assert aps.platform_support["linux_x64"].tested is True
    assert aps.validation_result.missing_dependencies == [
        "APS_CLIENT_ID",
        "APS_CLIENT_SECRET",
        "SSA_ID",
        "SSA_KEY_ID",
        "SSA_KEY_PATH",
    ]
    assert "AUTH-001" in aps.validation_result.message


def test_aps_community_entry_redirects_to_official_server():
    loader = CatalogLoader()

    aps = next(
        tool
        for tool in loader.get_all()
        if tool.id == "aps-mcp-server-petr"
    )
    assert aps.command == ["node", "build/server.js"]
    assert aps.installability_tier == "blocked"
    assert aps.validation_result.status == "blocked"
    assert aps.platform_support["linux_x64"].tested is True
    assert aps.credentials_required == [
        "APS_CLIENT_ID",
        "APS_CLIENT_SECRET",
        "APS_SA_ID",
        "APS_SA_EMAIL",
        "APS_SA_KEY_ID",
        "APS_SA_PRIVATE_KEY",
    ]
    assert "557556235e806a5d74265fcf556b9dae4206abdd" in aps.validation_result.message
    assert "listed 8 tools" in aps.validation_result.message
    assert "autodesk-platform-services/aps-mcp-server-nodejs" in aps.install_blocked_reason


def test_blender_entry_records_xvfb_backend_validation():
    loader = CatalogLoader()

    blender = next(
        tool
        for tool in loader.get_all()
        if tool.id == "blender-mcp"
    )
    assert blender.command == ["uvx", "--python", "3.11", "blender-mcp"]
    assert blender.installability_tier == "tested"
    assert blender.validation_result.status == "passed"
    assert blender.platform_support["linux_x64"].status == "yes"
    assert blender.platform_support["linux_x64"].tested is True
    assert blender.host_software_required == ["Blender", "BlenderMCP addon"]
    assert "listed 22 tools" in blender.validation_result.message
    assert "WrightValidationCube" in blender.validation_result.message
    assert blender.validation_result.missing_dependencies == []


def test_cad_mcp_universal_records_windows_com_dependency():
    loader = CatalogLoader()

    cad = next(
        tool
        for tool in loader.get_all()
        if tool.id == "cad-mcp-daobataotie"
    )
    assert cad.command == ["python", "src/server.py"]
    assert cad.installability_tier == "might_work"
    assert cad.validation_result.status == "dependency_missing"
    assert cad.platform_support["linux_x64"].status == "no"
    assert cad.platform_support["linux_x64"].tested is True
    assert cad.host_software_required == [
        "Windows",
        "pywin32",
        "AutoCAD",
        "GstarCAD",
        "ZWCAD",
    ]
    assert "No module named 'win32com'" in cad.validation_result.message


def test_creo_mcp_records_cadquery_pass_and_missing_host_dependencies():
    loader = CatalogLoader()

    creo = next(
        tool
        for tool in loader.get_all()
        if tool.id == "creo-mcp"
    )
    assert creo.command == [
        "uvx",
        "creo-mcp",
        "--authorization",
        "${VOLCENGINE_AUTHORIZATION}",
        "--service-resource-id",
        "${VOLCENGINE_SERVICE_RESOURCE_ID}",
    ]
    assert creo.installability_tier == "might_work"
    assert creo.validation_result.status == "dependency_missing"
    assert creo.platform_support["linux_x64"].status == "host-dependent"
    assert creo.platform_support["linux_x64"].tested is True
    assert creo.validation_result.missing_dependencies == [
        "Creo",
        "CREOSON",
        "VOLCENGINE_AUTHORIZATION",
        "VOLCENGINE_SERVICE_RESOURCE_ID",
    ]
    assert "15418 bytes" in creo.validation_result.message
    assert "localhost:9056" in creo.validation_result.message
    assert "HTTP 400" in creo.validation_result.message


def test_revit_mcp_records_node_server_and_plugin_boundary():
    loader = CatalogLoader()

    revit = next(
        tool
        for tool in loader.get_all()
        if tool.id == "revit-mcp"
    )
    assert revit.command == ["node", "build/index.js"]
    assert revit.installability_tier == "might_work"
    assert revit.validation_result.status == "dependency_missing"
    assert revit.platform_support["linux_x64"].status == "no"
    assert revit.platform_support["linux_x64"].tested is True
    assert revit.host_software_required == ["Revit", "revit-mcp-plugin", "Windows"]
    assert revit.validation_result.missing_dependencies == [
        "Revit",
        "revit-mcp-plugin",
    ]
    assert "c9ef49e4c397298d291304f822b89ba3a102e6bf" in revit.validation_result.message
    assert "listed 25 tools" in revit.validation_result.message
    assert "connect to revit client failed" in revit.validation_result.message


def test_siemens_element_records_project_install_and_token_boundary():
    loader = CatalogLoader()

    element = next(
        tool
        for tool in loader.get_all()
        if tool.id == "siemens-element-mcp"
    )
    assert element.transport == "stdio"
    assert element.command == ["npx", "@siemens/element-mcp"]
    assert element.verification_state == "verified_docs_mcp"
    assert element.installability_tier == "might_work"
    assert element.risk_level == "read-only"
    assert element.platform_support["linux_x64"].status == "yes"
    assert element.platform_support["linux_x64"].tested is True
    assert element.credentials_required == ["OPENAI_API_KEY"]
    assert element.validation_result.status == "dependency_missing"
    assert element.validation_result.missing_dependencies == ["OPENAI_API_KEY"]
    assert "@siemens/element-mcp@49.12.0-v.1.11.1" in element.dependencies.node
    assert "listed 2 tools" in element.validation_result.message
    assert "Embedding API error: 403 Forbidden" in element.validation_result.message
    assert "element-mcp: not found" in element.validation_result.message


def test_wincc_unified_records_login_gated_official_artifact():
    loader = CatalogLoader()

    wincc = next(
        tool
        for tool in loader.get_all()
        if tool.id == "wincc-unified-mcp"
    )
    assert wincc.command == ["wincc-unified-mcp.exe"]
    assert wincc.installability_tier == "blocked"
    assert wincc.risk_level == "safety-critical"
    assert wincc.validation_result.status == "blocked"
    assert wincc.platform_support["linux_x64"].status == "no"
    assert wincc.platform_support["linux_x64"].tested is True
    assert wincc.follow_up_url == "docs/mcp-catalog/followups/wincc-unified-mcp.md"
    assert "HTTP 403" in wincc.validation_result.message
    assert "npm view wincc-unified-mcp" in wincc.validation_result.message
    assert "No MCP stdio calls could be made" in wincc.validation_result.message
    assert "110002407_MCPServerPCRuntime_READMEOSS.zip" in (
        wincc.validation_result.missing_dependencies
    )


def test_thingworx_records_product_hosted_mcp_endpoint():
    loader = CatalogLoader()

    thingworx = next(
        tool
        for tool in loader.get_all()
        if tool.id == "thingworx-mcp"
    )
    assert thingworx.transport == "sse"
    assert thingworx.command == "${THINGWORX_BASE_URL}/mcp"
    assert thingworx.installability_tier == "might_work"
    assert thingworx.risk_level == "safety-critical"
    assert thingworx.validation_result.status == "dependency_missing"
    assert thingworx.platform_support["linux_x64"].status == "host-dependent"
    assert thingworx.platform_support["linux_x64"].tested is True
    assert thingworx.credentials_required == [
        "THINGWORX_BASE_URL",
        "THINGWORX_APP_KEY or THINGWORX_OAUTH_TOKEN",
    ]
    assert "ptc-thingworx-mcp` command was not present" in (
        thingworx.validation_result.message
    )
    assert "7e22ef9be1af495acf1a46101ebb17380eed86ae" in (
        thingworx.validation_result.message
    )
    assert "No MCP calls could be made" in thingworx.validation_result.message


def test_creoson_records_backend_alias_not_mcp_server():
    loader = CatalogLoader()

    creoson = next(
        tool
        for tool in loader.get_all()
        if tool.id == "creoson-mcp-bridge"
    )
    assert creoson.verification_state == "capability_alias"
    assert creoson.installability_tier == "blocked"
    assert creoson.validation_result.status == "blocked"
    assert creoson.platform_support["linux_x64"].status == "no"
    assert creoson.platform_support["linux_x64"].tested is True
    assert creoson.follow_up_url == "docs/mcp-catalog/followups/creoson-mcp-bridge.md"
    assert "CreosonServer-3.0.1-win64.zip" in creoson.validation_result.message
    assert "no main manifest attribute" in creoson.validation_result.message
    assert "NoClassDefFoundError: com/ptc/cipjava/jxthrowable" in (
        creoson.validation_result.message
    )
    assert "does not implement MCP stdio/SSE" in creoson.validation_result.message


def test_solidworks_python_records_dependency_api_break():
    loader = CatalogLoader()

    solidworks = next(
        tool
        for tool in loader.get_all()
        if tool.id == "solidworks-mcp-python"
    )
    assert solidworks.command == ["python", "-m", "solidworks_mcp.server"]
    assert solidworks.installability_tier == "non_working"
    assert solidworks.validation_result.status == "failed"
    assert solidworks.platform_support["linux_x64"].status == "no"
    assert solidworks.platform_support["linux_x64"].tested is True
    assert solidworks.follow_up_url == "docs/mcp-catalog/followups/solidworks-mcp-python.md"
    assert "f0858a7b9cf8cb9a7838ddfaa91a706ef6439cab" in (
        solidworks.validation_result.message
    )
    assert "pydantic-ai` 2.0.0" in solidworks.validation_result.message
    assert "ModuleNotFoundError: No module named 'pydantic_ai.toolsets.fastmcp'" in (
        solidworks.validation_result.message
    )
    assert solidworks.validation_result.missing_dependencies == [
        "compatible pydantic-ai API",
        "Windows",
        "SolidWorks",
        "Windows COM",
    ]


def test_solidworks_ts_records_windows_com_dependency_boundary():
    loader = CatalogLoader()

    solidworks = next(
        tool
        for tool in loader.get_all()
        if tool.id == "solidworks-mcp-ts"
    )
    assert solidworks.command == ["node", "dist/index.js"]
    assert solidworks.installability_tier == "might_work"
    assert solidworks.validation_result.status == "dependency_missing"
    assert solidworks.platform_support["linux_x64"].status == "host-dependent"
    assert solidworks.platform_support["linux_x64"].tested is True
    assert "c50ba5867f1d1632a5f6857a2b4aa5ad9b1838b7" in (
        solidworks.validation_result.message
    )
    assert "Upstream tests passed with 52 tests" in solidworks.validation_result.message
    assert "listed 86 tools" in solidworks.validation_result.message
    assert "The winax native module is not available" in (
        solidworks.validation_result.message
    )
    assert solidworks.validation_result.missing_dependencies == [
        "Windows",
        "SolidWorks",
        "Windows COM",
        "working winax native module",
    ]


def test_solidworks_alisamsam_records_broken_requirements():
    loader = CatalogLoader()

    solidworks = next(
        tool
        for tool in loader.get_all()
        if tool.id == "solidworks-mcp-alisamsam"
    )
    assert solidworks.command == ["python", "solidworks_mcp_server.py"]
    assert solidworks.installability_tier == "non_working"
    assert solidworks.validation_result.status == "failed"
    assert solidworks.platform_support["linux_x64"].status == "no"
    assert solidworks.platform_support["linux_x64"].tested is True
    assert solidworks.follow_up_url == (
        "docs/mcp-catalog/followups/solidworks-mcp-alisamsam.md"
    )
    assert "ee8f42a1a919af5e0fa8d1dcd24270c9983ce027" in (
        solidworks.validation_result.message
    )
    assert "asyncio-compat>=0.1.0" in solidworks.validation_result.message
    assert "ModuleNotFoundError: No module named 'win32com'" in (
        solidworks.validation_result.message
    )
    assert solidworks.validation_result.missing_dependencies == [
        "published asyncio-compat package or removed requirement",
        "pywin32",
        "win32com",
        "Windows",
        "SolidWorks",
    ]


def test_freecad_contextform_records_backend_timeout():
    loader = CatalogLoader()

    freecad = next(
        tool
        for tool in loader.get_all()
        if tool.id == "freecad-mcp-contextform"
    )
    assert freecad.command == ["python3", "working_bridge.py"]
    assert "freecad-copilot-contextform" in freecad.aliases
    assert freecad.installability_tier == "non_working"
    assert freecad.validation_result.status == "failed"
    assert freecad.platform_support["linux_x64"].status == "no"
    assert freecad.platform_support["linux_x64"].tested is True
    assert freecad.follow_up_url == (
        "docs/mcp-catalog/followups/freecad-copilot-contextform.md"
    )
    assert "de4fed2a7a4352fcb0de60d2b784063c54eeb812" in (
        freecad.validation_result.message
    )
    assert "serverInfo `freecad` version 2.0.0" in freecad.validation_result.message
    assert "listed 7 tools" in freecad.validation_result.message
    assert "part_operations" in freecad.validation_result.message
    assert "timed out after 30 seconds" in freecad.validation_result.message
    assert "QObject::startTimer" in freecad.validation_result.message


def test_freecad_robust_records_headless_xmlrpc_backend_pass():
    loader = CatalogLoader()

    freecad = next(
        tool
        for tool in loader.get_all()
        if tool.id == "freecad-addon-robust"
    )
    assert freecad.command == [
        "uv",
        "tool",
        "run",
        "--from",
        "freecad-robust-mcp",
        "freecad-mcp",
    ]
    assert "freecad-robust-spkane" in freecad.aliases
    assert freecad.installability_tier == "tested"
    assert freecad.validation_result.status == "passed"
    assert freecad.platform_support["linux_x64"].status == "yes"
    assert freecad.platform_support["linux_x64"].tested is True
    assert "d9a37118a8331e8739ad45fd97d027437984296f" in (
        freecad.validation_result.message
    )
    assert "420 tests" in freecad.validation_result.message
    assert "FreeCAD 1.1.1 revision 20260414" in freecad.validation_result.message
    assert "listed 152 tools" in freecad.validation_result.message
    assert "get_connection_status" in freecad.validation_result.message
    assert "WrightBox" in freecad.validation_result.message
    assert freecad.validation_result.missing_dependencies == []


def test_freecad_nekanat_records_xvfb_backend_pass():
    loader = CatalogLoader()

    freecad = next(
        tool
        for tool in loader.get_all()
        if tool.id == "freecad-mcp-nekanat"
    )
    assert freecad.command == ["uvx", "freecad-mcp", "--only-text-feedback"]
    assert "freecad-core-nekanat" in freecad.aliases
    assert freecad.installability_tier == "tested"
    assert freecad.validation_result.status == "passed"
    assert freecad.platform_support["linux_x64"].status == "yes"
    assert freecad.platform_support["linux_x64"].tested is True
    assert "63acb305573194a011641ab13ccfb391fe95769f" in (
        freecad.validation_result.message
    )
    assert "version 0.1.18" in freecad.validation_result.message
    assert "no upstream tests were present" in freecad.validation_result.message
    assert "listed 14 tools" in freecad.validation_result.message
    assert "list_documents" in freecad.validation_result.message
    assert "WrightBox" in freecad.validation_result.message
    assert freecad.validation_result.missing_dependencies == []


def test_multicad_records_windows_com_dependency_boundary():
    loader = CatalogLoader()

    multicad = next(
        tool
        for tool in loader.get_all()
        if tool.id == "multicad-mcp"
    )
    assert multicad.command == ["python", "src/server.py"]
    assert "multicad-mcp-ancode666" in multicad.aliases
    assert multicad.installability_tier == "might_work"
    assert multicad.validation_result.status == "dependency_missing"
    assert multicad.platform_support["linux_x64"].status == "no"
    assert multicad.platform_support["linux_x64"].tested is True
    assert "360ec77c970ec95a962bd4d0a3238715ee78dd7c" in (
        multicad.validation_result.message
    )
    assert "version 0.2.0" in multicad.validation_result.message
    assert "pywin32>=300" in multicad.validation_result.message
    assert "AutoCAD adapter requires Windows OS with COM support" in (
        multicad.validation_result.message
    )
    assert "no MCP `initialize` or `tools/list` calls were possible" in (
        multicad.validation_result.message
    )
    assert multicad.validation_result.missing_dependencies == [
        "Windows",
        "Windows COM",
        "pywin32",
        "AutoCAD 2018+ or ZWCAD 2020+ or GstarCAD 2020+ or BricsCAD 21+",
    ]


def test_rhino_records_missing_bridge_boundary():
    loader = CatalogLoader()

    rhino = next(
        tool
        for tool in loader.get_all()
        if tool.id == "rhino-mcp"
    )
    assert rhino.command == ["uvx", "rhinomcp"]
    assert "rhino-mcp-mcneel" in rhino.aliases
    assert rhino.installability_tier == "might_work"
    assert rhino.validation_result.status == "dependency_missing"
    assert rhino.platform_support["linux_x64"].status == "host-dependent"
    assert rhino.platform_support["linux_x64"].tested is True
    assert "RHINO_MCP_HOST" == rhino.env_vars[0].name
    assert "b56338a9da733d17555744ab895facdc84a80542" in (
        rhino.validation_result.message
    )
    assert "version 0.3.1" in rhino.validation_result.message
    assert "192/192" in rhino.validation_result.message
    assert "listed 66 tools" in rhino.validation_result.message
    assert "Could not connect to Rhino at 127.0.0.1:1999" in (
        rhino.validation_result.message
    )
    assert rhino.validation_result.missing_dependencies == [
        "Rhino 8",
        "RhinoMCP plugin",
        "mcpstart bridge on 127.0.0.1:1999",
    ]


def test_sketchup_records_missing_extension_boundary():
    loader = CatalogLoader()

    sketchup = next(
        tool
        for tool in loader.get_all()
        if tool.id == "sketchup-mcp"
    )
    assert sketchup.command == ["uvx", "sketchup-mcp"]
    assert "sketchup-mcp-mhyrr" in sketchup.aliases
    assert sketchup.installability_tier == "might_work"
    assert sketchup.validation_result.status == "dependency_missing"
    assert sketchup.platform_support["linux_x64"].status == "host-dependent"
    assert sketchup.platform_support["linux_x64"].tested is True
    assert "aa096f04d3d7b22a70860368f2b576343feac405" in (
        sketchup.validation_result.message
    )
    assert "version 0.1.17" in sketchup.validation_result.message
    assert "listed 10 tools" in sketchup.validation_result.message
    assert "get_scene_info" in sketchup.validation_result.message
    assert "Could not connect to Sketchup" in sketchup.validation_result.message
    assert sketchup.validation_result.missing_dependencies == [
        "SketchUp",
        "SketchupMCP extension server on port 9876",
    ]


def test_webmcp_openscad_records_browser_bridge_boundary():
    loader = CatalogLoader()

    webmcp = next(
        tool
        for tool in loader.get_all()
        if tool.id == "webmcp-openscad"
    )
    assert webmcp.command == ["npx", "-y", "@mcp-b/webmcp-local-relay@latest"]
    assert "webmcp-openscad-jherr" in webmcp.aliases
    assert "scad-webmcp" in webmcp.aliases
    assert webmcp.installability_tier == "might_work"
    assert webmcp.validation_result.status == "dependency_missing"
    assert webmcp.platform_support["linux_x64"].status == "host-dependent"
    assert webmcp.platform_support["linux_x64"].tested is True
    assert "a3acb68578701001f0251459c75716a55aadfa10" in (
        webmcp.validation_result.message
    )
    assert "Node 22.23.1" in webmcp.validation_result.message
    assert "pnpm build" in webmcp.validation_result.message
    assert "serverInfo `webmcp-local-relay` version 0.0.0" in (
        webmcp.validation_result.message
    )
    assert "listed 4 relay tools" in webmcp.validation_result.message
    assert "zero sources/tools" in webmcp.validation_result.message
    assert webmcp.validation_result.missing_dependencies == [
        "browser tab running scad-webmcp",
        "MCP-B extension or native WebMCP bridge",
    ]


def test_web3d_records_verified_source_build_and_mcp_codegen():
    loader = CatalogLoader()

    web3d = next(
        tool
        for tool in loader.get_all()
        if tool.id == "web3d-mcp"
    )
    assert web3d.vendor == "dev261004"
    assert web3d.command == ["node", "dist/server.js"]
    assert web3d.source_url == "https://github.com/dev261004/web3d-mcp-server"
    assert "web3d-mcp-server" in web3d.aliases
    assert web3d.installability_tier == "tested"
    assert web3d.validation_result.status == "passed"
    assert web3d.platform_support["linux_x64"].status == "yes"
    assert web3d.platform_support["linux_x64"].tested is True
    assert "b6e3cb59ba243ab53be2e1b1a674e5199bfc0c6a" in (
        web3d.validation_result.message
    )
    assert "Node 22.23.1" in web3d.validation_result.message
    assert "10 suites and 65 tests" in web3d.validation_result.message
    assert "serverInfo `3d-scene-mcp` version 1.0.0" in (
        web3d.validation_result.message
    )
    assert "listed 12 tools" in web3d.validation_result.message
    assert "validate_scene` returned `is_valid:true`" in (
        web3d.validation_result.message
    )
    assert "generate_r3f_code` returned `SUCCESS`" in (
        web3d.validation_result.message
    )
    assert web3d.validation_result.missing_dependencies == []


def test_solidworks_api_docs_entry_is_tested_read_only():
    loader = CatalogLoader()

    docs_entry = next(
        tool
        for tool in loader.search("solidworks")
        if tool.id == "solidworks-api-mcp"
    )
    assert docs_entry.installability_tier == "tested"
    assert docs_entry.risk_level == "read-only"
    assert docs_entry.validation_result.status == "passed"
    assert docs_entry.platform_support["linux_x64"].status == "yes"


def test_onshape_entry_records_missing_credentials():
    loader = CatalogLoader()

    onshape = next(
        tool
        for tool in loader.search("onshape")
        if tool.id == "onshape-mcp-hedless"
    )
    assert onshape.installability_tier == "might_work"
    assert onshape.validation_result.status == "dependency_missing"
    assert onshape.validation_result.missing_dependencies == [
        "ONSHAPE_ACCESS_KEY",
        "ONSHAPE_SECRET_KEY",
    ]


def test_jarvis_onshape_entry_records_git_source_and_credentials_boundary():
    loader = CatalogLoader()

    jarvis = next(
        tool
        for tool in loader.get_all()
        if tool.id == "jarvis-onshape-mcp"
    )
    assert jarvis.command == [
        "uv",
        "run",
        "--with",
        "git+https://github.com/ReshefElisha/jarvis-onshape-mcp.git",
        "onshape-mcp",
    ]
    assert jarvis.installability_tier == "might_work"
    assert jarvis.validation_result.status == "dependency_missing"
    assert jarvis.platform_support["linux_x64"].status == "yes"
    assert jarvis.platform_support["linux_x64"].tested is True
    assert jarvis.validation_result.missing_dependencies == [
        "ONSHAPE_API_KEY",
        "ONSHAPE_API_SECRET",
    ]
    assert "698/698" in jarvis.validation_result.message
    assert "listed 69 tools" in jarvis.validation_result.message
    assert "Unauthenticated API request" in jarvis.validation_result.message


def test_zoo_entry_records_python_stdio_and_token_requirement():
    loader = CatalogLoader()

    zoo = next(
        tool
        for tool in loader.search("zoo")
        if tool.id == "zoo-mcp"
    )
    assert zoo.transport == "stdio"
    assert zoo.command == ["uvx", "zoo-mcp"]
    assert zoo.installability_tier == "might_work"
    assert zoo.validation_result.status == "dependency_missing"
    assert zoo.validation_result.missing_dependencies == ["ZOO_API_TOKEN"]
    assert zoo.platform_support["linux_x64"].tested is True


def test_catalog_sorted_by_installability_tier(tmp_path):
    catalog_file = tmp_path / "catalog.yaml"
    catalog_file.write_text(
        """
servers:
  - id: blocked
    name: Blocked Tool
    vendor: Test
    description: Test
    domains: [cad]
    transport: stdio
    command: test
    locality: local
    weight: light
    installability_tier: blocked
  - id: tested
    name: Tested Tool
    vendor: Test
    description: Test
    domains: [cad]
    transport: stdio
    command: test
    locality: local
    weight: light
    installability_tier: tested
""",
        encoding="utf-8",
    )

    loader = CatalogLoader(str(catalog_file))
    assert [entry.id for entry in loader.get_all()] == ["tested", "blocked"]


def test_search_matches_risk_and_dependencies(tmp_path):
    catalog_file = tmp_path / "catalog.yaml"
    catalog_file.write_text(
        """
servers:
  - id: risky
    name: Risky Tool
    vendor: Test
    description: Test
    domains: [cad]
    transport: stdio
    command: test
    locality: local
    weight: light
    risk_level: high
    host_software_required: [FreeCAD]
""",
        encoding="utf-8",
    )

    loader = CatalogLoader(str(catalog_file))
    assert loader.search("high")[0].id == "risky"
    assert loader.search("freecad")[0].id == "risky"


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
