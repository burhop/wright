from __future__ import annotations

from types import SimpleNamespace

import pytest

from workspace_service.brep_panel import (
    BrepPanelError,
    panel_environment,
    parse_brep_status_result,
    select_brep_application_server,
)


def _server(**changes):
    values = {
        "name": "BREP MCP",
        "source_url": "https://github.com/mmiscool/BREP-MCP",
        "is_installed": True,
    }
    values.update(changes)
    return SimpleNamespace(**values)


def test_panel_environment_moves_brep_off_wright_port_and_suppresses_browser():
    environment = panel_environment({"BREP_MCP_COMMAND_TIMEOUT_MS": "295000"})

    assert environment == {
        "BREP_MCP_COMMAND_TIMEOUT_MS": "295000",
        "BREP_CAD_MODULE_URL": "http://127.0.0.1:5190/src/CAD.ts",
        "BREP_MCP_APP_PORT": "0",
        "BREP_MCP_AUTO_OPEN": "0",
    }


def test_panel_environment_rejects_wright_development_port():
    with pytest.raises(BrepPanelError, match="must not use Wright"):
        panel_environment({}, module_url="http://127.0.0.1:5173/src/CAD.ts")


def test_status_parser_accepts_tokenized_loopback_control_page():
    status = parse_brep_status_result(
        {
            "content": [
                {
                    "type": "text",
                    "text": """{
                      "connected": false,
                      "controlUrl": "http://127.0.0.1:61234/?token=abcdefghijklmnopqrstuvwxyz012345",
                      "moduleUrl": "http://127.0.0.1:5190/src/CAD.ts"
                    }""",
                }
            ]
        }
    )

    assert status.control_url.startswith("http://127.0.0.1:61234/")
    assert status.module_url.endswith(":5190/src/CAD.ts")
    assert status.connected is False


@pytest.mark.parametrize(
    "control_url",
    [
        "https://127.0.0.1:61234/?token=abcdefghijklmnopqrstuvwxyz012345",
        "http://example.com:61234/?token=abcdefghijklmnopqrstuvwxyz012345",
        "http://127.0.0.1:61234/",
    ],
)
def test_status_parser_rejects_untrusted_control_urls(control_url: str):
    with pytest.raises(BrepPanelError):
        parse_brep_status_result(
            {
                "structuredContent": {
                    "controlUrl": control_url,
                    "moduleUrl": "http://127.0.0.1:5190/src/CAD.ts",
                }
            }
        )


def test_server_selection_excludes_uninstalled_and_unrelated_brep_servers():
    selected = _server()
    assert (
        select_brep_application_server(
            [
                _server(is_installed=False),
                _server(
                    name="BREP.js CAD",
                    source_url="https://github.com/valerypopoff/brepjs-cad",
                ),
                selected,
            ]
        )
        is selected
    )
