from __future__ import annotations

from .support import artifact, lifecycle, seed_runtime


def test_reinstall_discovers_preserved_workspace_and_configuration(tmp_path) -> None:
    runtime = lifecycle(tmp_path)
    seed_runtime(runtime, version="0.1.4", runtime_id="old")
    workspace = runtime.layout.workspaces / "preserved"
    workspace.mkdir(parents=True)
    (workspace / "part.step").write_text("geometry", encoding="utf-8")
    config = runtime.layout.data / "settings.json"
    config.write_text('{"theme":"dark"}', encoding="utf-8")
    assert runtime.uninstall().ok

    result = runtime.start(artifact=artifact(tmp_path, "0.1.5"))

    assert result.ok
    assert (workspace / "part.step").read_text(encoding="utf-8") == "geometry"
    assert config.read_text(encoding="utf-8") == '{"theme":"dark"}'
