import yaml

from agent_adapters.config_merge import atomic_merge_yaml


def test_atomic_merge_preserves_unknown_entries(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "unknown": {"keep": True},
                "mcp_servers": {"other": {"command": "other-server"}},
            }
        ),
        encoding="utf-8",
    )

    def update(config):
        config.setdefault("mcp_servers", {})["wright"] = {"command": "wright"}

    assert atomic_merge_yaml(path, update) is True
    result = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert result["unknown"] == {"keep": True}
    assert result["mcp_servers"]["other"] == {"command": "other-server"}
    assert result["mcp_servers"]["wright"] == {"command": "wright"}


def test_atomic_merge_noop_keeps_file_unchanged(tmp_path):
    path = tmp_path / "config.yaml"
    original = "unknown: true\n"
    path.write_text(original, encoding="utf-8")

    assert atomic_merge_yaml(path, lambda config: None) is False
    assert path.read_text(encoding="utf-8") == original
