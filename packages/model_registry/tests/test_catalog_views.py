from __future__ import annotations

import pytest

from model_registry.catalog import ModelCatalog, ModelCatalogError, ModelCatalogFilters
from model_registry.policy import HostObservation


def reference_host() -> HostObservation:
    return HostObservation.reference()


def test_views_explain_readiness_evidence_and_recovery_without_side_effects() -> None:
    catalog = ModelCatalog.load_bundled()
    views = {item["model_id"]: item for item in catalog.views(host=reference_host())}

    generated = views["wright-affine-test"]
    assert generated["readiness"] == "approved"
    assert generated["compatibility"]["state"] == "compatible"
    assert generated["evidence"]["artifact"] == "bundled"
    assert generated["generator"]["artifact_set_digest"]

    pointnet = views["keras-io-pointnet"]
    assert pointnet["readiness"] == "needs_review"
    assert pointnet["evidence"]["test"] == "absent"
    assert {item["category"] for item in pointnet["blockers"]} >= {
        "license_unapproved",
        "runtime_missing",
        "test_evidence_missing",
    }

    assert views["blocked-gated-geometry-model"]["readiness"] == (
        "gated_external_action"
    )
    assert views["blocked-remote-code-model"]["readiness"] == "blocked"
    incompatible = views["incompatible-cuda-mesh-model"]
    assert incompatible["readiness"] == "incompatible"
    assert incompatible["compatibility"]["state"] == "incompatible"


def test_filter_sort_and_cursor_pagination_are_bounded_and_deterministic() -> None:
    catalog = ModelCatalog.load_bundled()
    page = catalog.list(
        ModelCatalogFilters(search="point cloud", source_kind="hugging_face"),
        host=reference_host(),
        limit=10,
    )
    assert [item["model_id"] for item in page.items] == ["keras-io-pointnet"]

    blocked = catalog.list(
        ModelCatalogFilters(readiness=("blocked", "gated_external_action")),
        host=reference_host(),
        limit=10,
    )
    assert [item["model_id"] for item in blocked.items] == [
        "blocked-gated-geometry-model",
        "blocked-remote-code-model",
    ]

    first = catalog.list(ModelCatalogFilters(), host=reference_host(), limit=2)
    second = catalog.list(
        ModelCatalogFilters(),
        host=reference_host(),
        limit=2,
        cursor=first.next_cursor,
    )
    assert first.total == 8
    assert first.next_cursor
    assert not {item["model_id"] for item in first.items}.intersection(
        item["model_id"] for item in second.items
    )
    with pytest.raises(ModelCatalogError, match="cursor"):
        catalog.list(
            ModelCatalogFilters(),
            host=reference_host(),
            limit=2,
            cursor="invalid!",
        )


def test_variant_compatibility_is_independent_and_offline_freshness_is_explicit() -> (
    None
):
    catalog = ModelCatalog.load_bundled()
    pointnet = catalog.get_view("keras-io-pointnet", host=reference_host())

    assert pointnet["snapshot"]["freshness"] == "bundled"
    assert pointnet["snapshot"]["offline"] is True
    assert pointnet["variants"][0]["compatibility"]["state"] in {
        "uncertain",
        "blocked",
    }
    assert pointnet["variants"][0]["evidence"]["test"] == "absent"
