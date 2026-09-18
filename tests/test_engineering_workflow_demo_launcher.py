from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_demo_api_binds_before_workspace_mcp_servers_are_started_lazily():
    launcher = (
        ROOT / "scripts/windows/start-engineering-workflow-demo.ps1"
    ).read_text(encoding="utf-8")

    disable = '$env:WRIGHT_API_MCP_AUTOSTART = "0"'
    api_start = 'Start-HiddenProcess -Name "wright-api"'
    assert disable in launcher
    assert launcher.index(disable) < launcher.index(api_start)


def test_demo_uses_the_wright_profile_for_auth_model_and_gateway_startup():
    launcher = (
        ROOT / "scripts/windows/start-engineering-workflow-demo.ps1"
    ).read_text(encoding="utf-8")

    assert '$env:HERMES_PROFILE = "wright"' in launcher
    assert '$env:WRIGHT_HERMES_PROFILE = "wright"' in launcher
    assert '"API_SERVER_ENABLED"' in launcher
    assert '"API_SERVER_KEY"' in launcher
    assert (
        'ArgumentList @("-p", "wright", "gateway", "run")'
        in launcher
    )
