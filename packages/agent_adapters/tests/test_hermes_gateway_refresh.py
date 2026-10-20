import asyncio
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent_adapters.hermes_gateway_refresh import ManualHermesGatewayRefresh


@pytest.fixture
def pilot(tmp_path, monkeypatch):
    home = tmp_path / "hermes"
    config = home / "profiles" / "pilot" / "config.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("model: test\n")
    runtime = SimpleNamespace(python=tmp_path / "python", runtime_root=tmp_path)
    monkeypatch.setattr(
        "agent_adapters.hermes_gateway_refresh.HermesRoleTransport.from_host",
        lambda: runtime,
    )
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_PROFILE", "pilot")
    monkeypatch.delenv("WRIGHT_HERMES_PROFILE", raising=False)
    monkeypatch.delenv("_HERMES_GATEWAY", raising=False)
    monkeypatch.setenv("HERMES_CONFIG_PATH", str(config))
    monkeypatch.setenv("HERMES_API_BASE_URL", "http://127.0.0.1:28642")
    monkeypatch.setenv("HERMES_API_DISABLE_DEFAULT_CANDIDATES", "1")
    monkeypatch.setattr(
        "agent_adapters.hermes_gateway_refresh.resolve_hermes_api_settings",
        lambda: SimpleNamespace(
            base_url="http://127.0.0.1:28642", api_key="private-test-value"
        ),
    )
    launches = []
    child = SimpleNamespace(poll=lambda: None)

    def launch(command, **options):
        launches.append((command, options))
        return child

    monkeypatch.setattr(
        "agent_adapters.hermes_gateway_refresh.subprocess.Popen", launch
    )
    refresh = ManualHermesGatewayRefresh()
    state = {"pid": 10, "digest": "a" * 64, "busy": False, "active": 0}
    monkeypatch.setattr(
        refresh,
        "_observe",
        lambda: {
            "pid": state["pid"],
            "config_digest": state["digest"],
            "home": str(config.parent),
        },
    )

    async def health():
        return {
            "pid": state["pid"],
            "gateway_state": "running",
            "gateway_busy": state["busy"],
            "active_agents": 0,
            "readiness": {
                "checks": {
                    "background_queues": {
                        "active_api_runs": state["active"],
                        "process_completions": 0,
                        "active_delegations": 0,
                    }
                }
            },
        }

    monkeypatch.setattr(refresh, "_health", health)
    return refresh, state, launches, child


@pytest.mark.parametrize(
    "key,value",
    [
        ("HERMES_API_BASE_URL", "http://example.org:8642"),
        ("HERMES_API_BASE_URL", "http://127.0.0.1:8642/p/shared"),
        ("HERMES_API_BASE_URL", "http://127.0.0.1"),
        ("HERMES_API_DISABLE_DEFAULT_CANDIDATES", "0"),
        ("HERMES_PROFILE", "default"),
        ("HERMES_PROFILE", "../shared"),
        ("HERMES_CONFIG_PATH", ""),
        ("_HERMES_GATEWAY", "1"),
    ],
)
def test_manual_refresh_refuses_ambiguous_scope_before_launch(
    pilot, monkeypatch, key, value
):
    monkeypatch.setenv(key, value)
    with pytest.raises(RuntimeError, match="explicit isolated"):
        ManualHermesGatewayRefresh()
    assert pilot[2] == []


def test_manual_refresh_rejects_invalid_port_before_any_operation(pilot, monkeypatch):
    monkeypatch.setenv("HERMES_API_BASE_URL", "http://127.0.0.1:invalid")
    with pytest.raises(RuntimeError, match="valid local endpoint"):
        ManualHermesGatewayRefresh()
    assert pilot[2] == []


@pytest.mark.asyncio
async def test_manual_refresh_replaces_only_selected_profile_without_install(pilot):
    refresh, state, launches, _ = pilot
    await refresh.start()
    command, options = launches[0]
    assert command[1:] == [
        "-m",
        "hermes_cli.main",
        "-p",
        "pilot",
        "gateway",
        "run",
        "--replace",
    ]
    assert options["env"]["API_SERVER_PORT"] == "28642"
    assert options["env"]["API_SERVER_KEY"] == "private-test-value"
    assert "private-test-value" not in str(command)
    assert options["env"]["HERMES_GATEWAY_DETACHED"] == "1"
    state["pid"] = 11
    await refresh.wait_ready()
    assert refresh.confirmed is True
    assert len(launches) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["profile", "busy", "active"])
async def test_manual_refresh_requires_matching_idle_connected_process(
    pilot, monkeypatch, change
):
    refresh, state, launches, _ = pilot
    if change == "profile":
        monkeypatch.setattr(refresh, "_observe", lambda: {"pid": 99})
    else:
        state[change] = True if change == "busy" else 1
    with pytest.raises(RuntimeError):
        await refresh.start()
    assert launches == []


@pytest.mark.asyncio
async def test_slow_replacement_preserves_child_and_does_not_accept_old_health(
    pilot, monkeypatch
):
    refresh, state, launches, _ = pilot
    await refresh.start()
    clock = iter([0, 0, 121])
    monkeypatch.setattr(
        "agent_adapters.hermes_gateway_refresh.time",
        SimpleNamespace(monotonic=lambda: next(clock)),
    )
    with pytest.raises(TimeoutError, match="same operation"):
        await refresh.wait_ready()
    assert not refresh.confirmed
    await refresh.start()
    assert len(launches) == 1
    state["pid"] = 11
    monkeypatch.setattr(
        "agent_adapters.hermes_gateway_refresh.time",
        SimpleNamespace(monotonic=lambda: 0),
    )
    await refresh.wait_ready()
    assert refresh.confirmed
    assert len(launches) == 1


@pytest.mark.asyncio
async def test_cancelled_observation_can_resume_same_child(pilot, monkeypatch):
    refresh, state, launches, _ = pilot
    await refresh.start()
    original = refresh._health

    async def cancelled():
        raise asyncio.CancelledError

    monkeypatch.setattr(refresh, "_health", cancelled)
    with pytest.raises(asyncio.CancelledError):
        await refresh.wait_ready()
    state["pid"] = 11
    monkeypatch.setattr(refresh, "_health", original)
    await refresh.wait_ready()
    assert len(launches) == 1


@pytest.mark.asyncio
async def test_api_restart_reconciles_retained_operation_without_replacement(
    pilot, monkeypatch
):
    refresh, state, launches, _ = pilot
    await refresh.start()
    restored = ManualHermesGatewayRefresh()
    assert restored.pending
    assert restored.child is None
    monkeypatch.setattr(restored, "_health", refresh._health)
    monkeypatch.setattr(restored, "_observe", refresh._observe)
    await restored.start()
    assert len(launches) == 1
    state["pid"] = 11
    await restored.wait_ready()
    reopened = ManualHermesGatewayRefresh()
    assert reopened.confirmed
    assert not reopened.pending
    assert len(launches) == 1


def test_corrupt_pending_receipt_is_not_treated_as_permission_to_restart(pilot):
    refresh, _, launches, _ = pilot
    refresh.receipt_path.write_text("unexpected: state\n")
    with pytest.raises(RuntimeError, match="receipt is invalid"):
        ManualHermesGatewayRefresh()
    assert launches == []


@pytest.mark.asyncio
async def test_failed_child_and_configuration_drift_never_trigger_another_launch(pilot):
    refresh, state, launches, child = pilot
    await refresh.start()
    state["pid"] = 11
    state["digest"] = "b" * 64
    with pytest.raises(RuntimeError, match="configuration changed"):
        await refresh.wait_ready()
    child.poll = lambda: 1
    with pytest.raises(RuntimeError, match="replacement exited"):
        await refresh.wait_ready()
    assert len(launches) == 1


@pytest.mark.parametrize("mismatch", ["home", "pid", "digest", "error"])
def test_observer_receipt_must_identify_exact_local_profile(
    pilot, monkeypatch, mismatch
):
    refresh = pilot[0]
    import json

    receipt = {"home": str(refresh.config.parent), "pid": 10, "config_digest": "a" * 64}
    if mismatch == "home":
        receipt["home"] = str(Path("/different-profile"))
    elif mismatch == "pid":
        receipt["pid"] = None
    elif mismatch == "digest":
        receipt["config_digest"] = ""
    else:
        receipt = {"error": "unavailable"}
    monkeypatch.setattr(
        "agent_adapters.hermes_gateway_refresh.subprocess.run",
        lambda *_, **__: SimpleNamespace(
            returncode=0, stdout=json.dumps(receipt).encode()
        ),
    )
    with pytest.raises(RuntimeError, match="no verified"):
        ManualHermesGatewayRefresh._observe(refresh)
