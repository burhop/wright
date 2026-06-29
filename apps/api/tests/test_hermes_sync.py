import yaml

from api.services import hermes_sync


def test_static_hermes_config_uses_runtime_repo_dir(tmp_path, monkeypatch):
    hermes_root = tmp_path / ".hermes"

    def fake_expanduser(path: str) -> str:
        return path.replace("~/.hermes", str(hermes_root))

    monkeypatch.setenv("WRIGHT_REPO_DIR", "/workspace")
    monkeypatch.setattr(hermes_sync.os.path, "expanduser", fake_expanduser)

    changed = hermes_sync._write_static_hermes_config()

    assert changed is True

    config_path = hermes_root / "profiles" / "wright" / "config.yaml"
    config = yaml.safe_load(config_path.read_text())
    gateway = config["mcp_servers"]["wrightgateway"]

    assert gateway["args"] == [
        "run",
        "--project",
        "/workspace",
        "python",
        "-m",
        "tool_registry.gateway",
    ]
    assert config["terminal"]["cwd"] == "/workspace"
