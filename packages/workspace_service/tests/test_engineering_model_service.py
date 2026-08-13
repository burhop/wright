from __future__ import annotations

from model_registry import ModelCatalog
from model_registry.policy import HostObservation
from workspace_service.engineering_model_service import EngineeringModelService


def test_model_catalog_service_is_offline_and_composes_host_compatibility(
    monkeypatch,
) -> None:
    def network_must_not_run(*args, **kwargs):
        raise AssertionError("read-only model catalog contacted the network")

    monkeypatch.setattr("urllib.request.urlopen", network_must_not_run)
    service = EngineeringModelService(
        catalog=ModelCatalog.load_bundled(),
        host_observer=HostObservation.reference,
    )

    page = service.list_catalog(task="predict", limit=10)
    detail = service.get_catalog_model("wright-affine-test")

    assert page["total"] == 1
    assert page["models"][0]["model_id"] == "wright-affine-test"
    assert detail["compatibility"]["state"] == "compatible"
    assert detail["snapshot"]["offline"] is True
