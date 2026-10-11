"""Path/identity checks only; these do not qualify the native thermal solver."""
import hashlib
import importlib.util
from pathlib import Path

import pytest


def load_screen():
    path = Path(__file__).resolve().parents[1] / "scripts/engineering/water_heater_package_skfem.py"
    spec = importlib.util.spec_from_file_location("water_package_handoff_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def handoff(tmp_path):
    relative = "campaign/water-heater-sizing-01/attempt-proof/artifacts/thermal-package.step"
    step = tmp_path / relative
    step.parent.mkdir(parents=True)
    step.write_bytes(b"unit-test identity only, not native STEP")
    config = {"workspace_root": str(tmp_path), "output_root": str(step.parent), "geometry_step": str(step)}
    measurements = {"step_path": relative, "step_sha256": hashlib.sha256(step.read_bytes()).hexdigest()}
    return config, measurements, step


def test_portable_reference_resolves_to_explicit_runtime_geometry(handoff):
    config, measurements, step = handoff
    assert load_screen()._bound_geometry(config, measurements) == step.resolve()


@pytest.mark.parametrize("reference", [
    "C:/campaign/thermal-package.step", "/campaign-workspace/thermal-package.step",
    "campaign\\water-heater-sizing-01\\attempt-proof\\artifacts\\thermal-package.step",
    "campaign/water-heater-sizing-01/attempt-other/artifacts/thermal-package.step",
    "campaign/water-heater-sizing-01/attempt-proof/artifacts/../artifacts/thermal-package.step",
])
def test_rejects_noncanonical_or_other_attempt_reference(handoff, reference):
    config, measurements, _ = handoff
    measurements["step_path"] = reference
    with pytest.raises(ValueError, match="workspace-relative"):
        load_screen()._bound_geometry(config, measurements)


def test_rejects_geometry_outside_same_attempt_output(handoff):
    config, measurements, step = handoff
    config["output_root"] = str(step.parent / "another-attempt")
    with pytest.raises(ValueError, match="same-attempt"):
        load_screen()._bound_geometry(config, measurements)


def test_rejects_changed_geometry(handoff):
    config, measurements, step = handoff
    step.write_bytes(b"different revision")
    with pytest.raises(ValueError, match="identity differs"):
        load_screen()._bound_geometry(config, measurements)
