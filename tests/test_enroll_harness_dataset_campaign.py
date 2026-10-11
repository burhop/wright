from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_harness_enroller_is_explicitly_non_dispatching() -> None:
    path = ROOT / "scripts/enroll-harness-dataset-campaign.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert "never dispatch execution" in ast.get_docstring(tree).lower()
    assert "run_engineering_dataset_campaign.py" not in source
    assert "prepare-harness-dataset-campaign.py" in source
    assert "enroll_engineering_dataset_case.py" in source
    assert "/api/workspace/workflow-source-templates/sensor-fan-harness/instances" in source
