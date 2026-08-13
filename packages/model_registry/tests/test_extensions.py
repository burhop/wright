from __future__ import annotations

from pathlib import Path
from datetime import UTC, datetime

import pytest
from data_vault import ModelArtifactStore, ModelRepository, upgrade_database
from fixture_factory import generate_affine_fixture
from fakes import FakeDiskReservation
from model_registry import ModelPackage, canonical_digest
from model_registry.conformance import run_package_conformance
from model_registry.extensions import ExtensionError, built_in_extension_registries
from model_registry.lifecycle import MappingArtifactSource, ModelInstallLifecycle
from model_registry.planning import confirm_effect_plan, create_effect_plan
from model_registry.policy import HostObservation
from model_registry.runtime import AdapterRegistration


def _package(fixture, **changes) -> ModelPackage:
    document = fixture.package.model_dump(mode="json")
    document.update(changes)
    return ModelPackage.model_validate(document)


def test_test_only_extension_uses_public_registries_without_service_edits(
    tmp_path,
) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    document = fixture.package.model_dump(mode="json")
    document["model_id"] = "test-extension-affine"
    document["display_name"] = "Test Extension Affine"
    document["variants"][0]["runtime"]["adapter_id"] = "test-extension-adapter"
    package = ModelPackage.model_validate(document)
    registries = built_in_extension_registries()
    registries.adapters.register(
        AdapterRegistration(
            adapter_id="test-extension-adapter",
            adapter_version="1.0.0",
            contract_version="1.0",
            command=("generated-fixture-adapter",),
            formats=frozenset({"wright-affine-json"}),
            tasks=frozenset({"predict"}),
            platforms=frozenset({"windows"}),
            architectures=frozenset({"x86_64"}),
            execution_providers=frozenset({"cpu"}),
        )
    )

    report = run_package_conformance(package, fixture.artifacts, registries)
    registered = registries.packages.register(package, registries=registries)

    assert report.passed is True
    assert registered.model_id == "test-extension-affine"
    assert (
        registries.packages.get(package.model_id, package.package_revision) is package
    )
    service_source = Path(
        "packages/workspace_service/src/workspace_service/engineering_model_service.py"
    ).read_text(encoding="utf-8")
    assert package.model_id not in service_source

    now = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    host = HostObservation(
        platform="windows",
        architecture="x86_64",
        available_disk_bytes=1_000_000_000,
        available_ram_bytes=1_000_000_000,
        accelerators=frozenset({"cpu"}),
        runtime_adapters={"test-extension-adapter": "1.0.0"},
    )
    plan = create_effect_plan(
        package,
        variant_id="json-cpu-f64",
        snapshot_id="extension-snapshot",
        principal_id="extension-author",
        host=host,
        now=now,
    )
    confirmed = confirm_effect_plan(
        plan,
        principal_id="extension-author",
        plan_digest=plan.plan_digest,
        now=now,
        current_plan=plan,
    )
    database = tmp_path / "state.db"
    upgrade_database(database)
    lifecycle = ModelInstallLifecycle(
        repository=ModelRepository(str(database)),
        store=ModelArtifactStore(tmp_path / "data"),
        disk=FakeDiskReservation(10_000_000),
        clock=lambda: now,
    )
    operation = lifecycle.install(
        confirmed, package, MappingArtifactSource(fixture.artifacts)
    )
    assert operation["state"] == "succeeded"


def test_duplicate_and_unknown_adapter_version_fail_before_acquisition(
    tmp_path,
) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    registries = built_in_extension_registries()
    registries.packages.register(fixture.package, registries=registries)
    with pytest.raises(ExtensionError) as duplicate:
        registries.packages.register(fixture.package, registries=registries)
    assert duplicate.value.category == "extension_duplicate"

    document = fixture.package.model_dump(mode="json")
    document["package_revision"] = 2
    document["variants"][0]["runtime"]["version_specifier"] = "==9.0.0"
    incompatible = ModelPackage.model_validate(document)
    with pytest.raises(ExtensionError) as unknown:
        registries.packages.register(incompatible, registries=registries)
    assert unknown.value.category == "runtime_incompatible"


@pytest.mark.parametrize(
    ("mutation", "category"),
    [
        (
            lambda document: document["variants"][0].update(
                {"format": "unsafe-pickle"}
            ),
            "unsafe_format",
        ),
        (
            lambda document: document["license"]["evidence"][0].update(
                {"location": "MISSING-LICENSE"}
            ),
            "license_unapproved",
        ),
        (
            lambda document: document["variants"][0]["test_vectors"][0].update(
                {"input_schema_sha256": "f" * 64}
            ),
            "schema_mismatch",
        ),
    ],
)
def test_unsafe_incomplete_and_schema_incompatible_extensions_fail_closed(
    tmp_path, mutation, category
) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    document = fixture.package.model_dump(mode="json")
    mutation(document)
    candidate = ModelPackage.model_validate(document)
    registries = built_in_extension_registries()
    with pytest.raises(ExtensionError) as failure:
        registries.packages.register(candidate, registries=registries)
    assert failure.value.category == category


def test_conformance_rejects_undeclared_or_digest_changed_generated_bytes(
    tmp_path,
) -> None:
    fixture = generate_affine_fixture(tmp_path / "fixture")
    registries = built_in_extension_registries()
    undeclared = {**fixture.artifacts, "extra.json": b"{}"}
    report = run_package_conformance(fixture.package, undeclared, registries)
    assert report.passed is False
    assert report.findings[0].category == "undeclared_file"

    changed = dict(fixture.artifacts)
    changed["model/coefficients.json"] = b"{}"
    report = run_package_conformance(fixture.package, changed, registries)
    assert report.passed is False
    assert {item.category for item in report.findings} >= {
        "digest_mismatch",
        "size_mismatch",
    }
    assert report.report_digest == canonical_digest(report.material())
