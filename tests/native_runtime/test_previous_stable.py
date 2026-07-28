from __future__ import annotations

import json
from pathlib import Path

from .support import lifecycle, seed_runtime


def test_previous_stable_fixture_contains_representative_retained_data(
    tmp_path: Path,
) -> None:
    runtime = lifecycle(tmp_path)
    seed_runtime(runtime, version="0.1.4", runtime_id="previous")
    workspace = runtime.layout.workspaces / "project"
    workspace.mkdir(parents=True)
    (workspace / "design.step").write_text("user-data", encoding="utf-8")
    config = runtime.layout.data / "settings.json"
    config.write_text(json.dumps({"catalog_choice": "cad.demo"}), encoding="utf-8")

    assert (workspace / "design.step").read_text(encoding="utf-8") == "user-data"
    assert (
        json.loads(config.read_text(encoding="utf-8"))["catalog_choice"] == "cad.demo"
    )
