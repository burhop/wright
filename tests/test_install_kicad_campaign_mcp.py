import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "install_kicad_campaign_mcp",
    ROOT / "scripts/install-kicad-campaign-mcp.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_harness_runtime_uses_separate_exact_attempt_mounts(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    mounts = MODULE.campaign_mount_specs(
        workspace, "sensor-fan-harness", "attempt-907"
    )

    assert len(mounts) == 6
    assert {mount["read_only"] for mount in mounts} == {True, False}
    assert all(
        "sensor-fan-harness" in mount["container"]
        and "attempt-907" in mount["container"]
        for mount in mounts
    )
    assert all(
        mount["host"].is_relative_to(workspace.resolve()) for mount in mounts
    )
    assert (
        MODULE.RUNTIMES["sensor-fan-harness"]["container"]
        != MODULE.RUNTIMES["sensor-interface-pcb"]["container"]
    )


def test_pcb_runtime_keeps_original_family_mount_contract(tmp_path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    mounts = MODULE.campaign_mount_specs(
        workspace, "sensor-interface-pcb", "attempt-001"
    )

    destinations = {mount["container"] for mount in mounts}
    assert "/work/campaign/sensor-interface-pcb-01/attempt-001/inputs" in destinations
    assert "/work/campaign/sensor-interface-pcb-03/attempt-001/artifacts" in destinations


def test_harness_qualification_replays_all_released_nets():
    spec = importlib.util.spec_from_file_location(
        "qualify_harness_kicad_runtime",
        ROOT / "scripts/qualify-harness-kicad-runtime.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert {row[-1] for row in module.NET_CALLS} == {
        "24V",
        "FAN_GND",
        "PWM",
        "TACH",
        "TEMP_SIGNAL",
        "SIGNAL_RETURN",
    }
    assert {row["reference"] for row in module.CONNECTOR_CALLS} == {"J0", "JF", "JS"}
