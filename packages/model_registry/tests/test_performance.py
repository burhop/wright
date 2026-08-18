from __future__ import annotations

import asyncio
import json
import math
import time
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

import pytest
from model_registry.catalog import (
    ModelCatalog,
    ModelCatalogEntry,
    ModelCatalogFilters,
)
from model_registry.chatter_runtime import load_forest, predict_batch
from model_registry.generated import (
    chatter_fixture_artifacts,
    generated_chatter_package,
)
from model_registry.gateway_provider import EngineeringModelGatewayProvider
from model_registry.generated import affine_artifacts
from model_registry.models import ModelPackage, canonical_digest
from model_registry.planning import create_effect_plan
from model_registry.policy import HostObservation, validate_artifact_path
from model_registry.runtime import (
    RuntimeFailure,
    RuntimeSupervisor,
    built_in_runtime_registry,
    current_runtime_platform,
)
from model_registry.testing import evaluate_test_vector
from tool_registry.gateway_models import GatewaySessionContext


def _p95(samples: list[float]) -> float:
    assert samples
    return sorted(samples)[max(0, math.ceil(len(samples) * 0.95) - 1)]


def _package() -> ModelPackage:
    package = ModelCatalog.load_bundled().get("wright-affine-test").package
    assert package is not None
    return package


def _large_catalog() -> ModelCatalog:
    source = ModelCatalog.load_bundled()
    base = source.get("keras-io-pointnet")
    entries = []
    for index in range(1000):
        document = deepcopy(dict(base.document))
        document["model_id"] = f"performance-model-{index:04d}"
        document["display_name"] = f"Performance engineering model {index:04d}"
        entries.append(
            ModelCatalogEntry(
                document=document,
                package=None,
                digest=canonical_digest(document),
            )
        )
    return ModelCatalog(source.snapshot, tuple(entries))


def test_thousand_entry_discovery_stays_under_500_ms_p95() -> None:
    catalog = _large_catalog()
    samples = []
    for _ in range(8):
        started = time.perf_counter()
        page = catalog.list(
            ModelCatalogFilters(search="performance engineering"),
            host=HostObservation.reference(),
            limit=100,
        )
        samples.append(time.perf_counter() - started)
        assert page.total == 1000
        assert len(page.items) == 100
    assert _p95(samples) < 0.5


def _hundred_artifact_package() -> ModelPackage:
    document = _package().model_dump(mode="json")
    template = document["variants"][0]["artifacts"][0]
    artifacts = []
    for index in range(100):
        artifact = deepcopy(template)
        artifact["path"] = f"data/a{index:03d}.onnx"
        artifact["size"] = 1
        artifact["sha256"] = f"{index:064x}"
        artifact["source_uri"] = f"wright://generated/a{index:03d}.onnx"
        artifacts.append(artifact)
    document["variants"][0]["artifacts"] = artifacts
    document["variants"][0]["format"] = "onnx"
    document["variants"][0]["resources"]["download_bytes"] = 100
    document["variants"][0]["resources"]["installed_bytes"] = 100
    return ModelPackage.model_validate(document)


def test_hundred_file_plan_and_manifest_validation_stay_under_one_second_p95() -> None:
    package = _hundred_artifact_package()
    samples = []
    for _ in range(8):
        started = time.perf_counter()
        validated = ModelPackage.model_validate(package.model_dump(mode="json"))
        plan = create_effect_plan(
            validated,
            variant_id=validated.variants[0].variant_id,
            snapshot_id="performance-snapshot",
            principal_id="performance-engineer",
            host=HostObservation.reference(),
            now=datetime(2026, 8, 13, tzinfo=UTC),
        )
        samples.append(time.perf_counter() - started)
        assert len(plan.effects) == 201
    assert _p95(samples) < 1.0


def test_thousand_artifact_path_and_digest_validation_is_bounded() -> None:
    declarations = [
        {
            "path": f"model/part-{index:04d}.onnx",
            "sha256": f"{index:064x}",
            "size": index,
        }
        for index in range(1000)
    ]
    started = time.perf_counter()
    normalized = [validate_artifact_path(item["path"]) for item in declarations]
    digests = [
        item["sha256"]
        for item in declarations
        if len(item["sha256"]) == 64 and set(item["sha256"]) <= set("0123456789abcdef")
    ]
    elapsed = time.perf_counter() - started
    assert len(set(normalized)) == len(digests) == 1000
    assert elapsed < 1.0


def _runtime_artifacts(root: Path) -> dict[str, Path]:
    package = _package()
    result = {}
    for relative, content in affine_artifacts(package).items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        result[relative] = target
    return result


@pytest.mark.asyncio
async def test_runtime_cancellation_is_observed_within_one_second(tmp_path) -> None:
    supervisor = RuntimeSupervisor(
        built_in_runtime_registry(), scratch_root=tmp_path / "scratch"
    )
    system, architecture = current_runtime_platform()
    session = await supervisor.start_session(
        adapter_id="wright-deterministic",
        installation_id="installation-performance",
        artifacts=_runtime_artifacts(tmp_path / "artifacts"),
        model_format="wright-affine-json",
        task_id="predict",
        platform=system,
        architecture=architecture,
        execution_provider="cpu",
    )
    handle = await session.load()
    inference = asyncio.create_task(
        session.infer(
            handle,
            {"x": 2},
            schema_digest="f" * 64,
            timeout=5,
            maximum_output_bytes=4096,
            fault_profile="slow",
        )
    )
    for _ in range(100):
        if session._current_request_id:
            break
        await asyncio.sleep(0)
    started = time.perf_counter()
    await session.cancel_current(grace_seconds=0.1)
    with pytest.raises(RuntimeFailure) as cancelled:
        await inference
    assert cancelled.value.category == "cancelled"
    assert time.perf_counter() - started < 1.0
    assert await session.shutdown() == "clean"


def _gateway_session() -> GatewaySessionContext:
    return (
        GatewaySessionContext(
            session_id="session-performance",
            principal_id="principal-performance",
            workspace_id="workspace-performance",
            workspace_path="/workspace",
            transport="legacy",
        )
        .initialized(
            protocol_version="2025-11-25",
            client_name="performance-test",
            client_version="1",
            client_capabilities={},
        )
        .activate()
    )


class TimedApplication:
    def __init__(self) -> None:
        self.contract = {
            "model_id": "wright-affine-test",
            "task_id": "predict",
            "description": "Bounded deterministic performance fixture.",
            "input_schema": {
                "type": "object",
                "properties": {"x": {"type": "number"}},
                "required": ["x"],
                "additionalProperties": False,
            },
            "output_schema": {
                "type": "object",
                "properties": {"y": {"type": "number"}},
                "required": ["y"],
                "additionalProperties": False,
            },
            "workspace_id": "workspace-performance",
            "binding_id": "binding-performance",
            "binding_digest": "a" * 64,
            "binding_state": "enabled",
            "installation_id": "installation-performance",
            "installation_digest": "b" * 64,
            "installation_state": "ready",
            "package_revision": 1,
            "manifest_digest": "e" * 64,
            "variant_id": "json-cpu-f64",
            "artifact_set_digest": "f" * 64,
            "adapter_id": "timed-adapter",
            "adapter_version": "1.0.0",
            "runtime_version": "1.0.0",
            "evidence_id": "evidence-performance",
            "evidence_state": "passed",
            "test_material_digest": "1" * 64,
            "input_schema_digest": "2" * 64,
            "output_schema_digest": "3" * 64,
            "resource_digest": "4" * 64,
            "threshold": None,
            "material_digest": "c" * 64,
            "policy_snapshot_digest": "d" * 64,
            "policy_current": True,
        }

    def declared_model_tool_names(self):
        return frozenset({"wright_model__wright_affine_test__predict"})

    def discover_model_capabilities(self, **_values):
        return (self.contract,)

    async def invoke_model_capability(self, **values):
        await asyncio.sleep(0.005)
        return {"structuredContent": {"y": values["arguments"]["x"] * 2 + 1}}

    async def cancel_model_request(self, **_values):
        return None

    async def close_model_session(self, **_values):
        return None

    async def shutdown_model_runtime(self):
        return None


@pytest.mark.asyncio
async def test_gateway_model_tool_overhead_stays_below_ten_percent() -> None:
    application = TimedApplication()
    provider = EngineeringModelGatewayProvider(application)
    session = _gateway_session()
    tool = provider.tools(session)[0]
    direct = []
    mediated = []
    # Average small batches before calculating p95. A single Windows scheduler
    # delay is otherwise larger than the sub-millisecond mediation budget and
    # makes this benchmark report a gateway regression that is not repeatable.
    batch_size = 8
    for index in range(12):
        started = time.perf_counter()
        for _ in range(batch_size):
            await application.invoke_model_capability(arguments={"x": 2})
        direct.append((time.perf_counter() - started) / batch_size)
        started = time.perf_counter()
        for iteration in range(batch_size):
            await provider.call(
                session,
                tool,
                {"x": 2},
                request_id=f"performance-{index}-{iteration}",
                approval_context={},
                progress_callback=None,
            )
        mediated.append((time.perf_counter() - started) / batch_size)
    baseline = _p95(direct)
    overhead = _p95(mediated) - baseline
    assert overhead / baseline < 0.10


def test_validation_evidence_remains_below_one_megabyte() -> None:
    package = _package()
    variant = package.variants[0]
    vector = variant.test_vectors[0]
    evidence = evaluate_test_vector(
        package=package,
        variant=variant,
        vector=vector,
        output={"y": 5.0},
        installation_id="installation-performance",
        installation_digest="a" * 64,
        artifact_set_digest="b" * 64,
        adapter_id="wright-deterministic",
        adapter_version="1.0.0",
        adapter_contract_version="1.0",
        environment_policy_digest="c" * 64,
        timing_ms=1,
        resources={"peak_ram_bytes": 1024},
        trace_id="trace-performance",
    )
    encoded = json.dumps(evidence.projection(), separators=(",", ":")).encode()
    assert len(encoded) < 1024 * 1024


def test_chatter_one_and_hundred_candidate_batches_stay_within_cpu_budget(
    tmp_path,
) -> None:
    package = generated_chatter_package()
    for name, value in chatter_fixture_artifacts(package).items():
        target = tmp_path.joinpath(*name.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value)
    metadata, arrays = load_forest(tmp_path)
    vector = package.variants[0].test_vectors[0]
    evidence = vector.expected.value["model_evidence"]
    samples = {}
    for count in (1, 100):
        batch = deepcopy(vector.input)
        template = batch["candidates"][0]
        batch["candidates"] = [
            {**deepcopy(template), "candidate_id": f"candidate-{index:03d}"}
            for index in range(count)
        ]
        timings = []
        for _ in range(5):
            started = time.perf_counter()
            result = predict_batch(batch, metadata, arrays, evidence)
            timings.append(time.perf_counter() - started)
            assert len(result["results"]) == count
        samples[count] = _p95(timings)
    assert samples[1] < 1.0
    assert samples[100] < 3.0
