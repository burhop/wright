from workspace_service.workflow_additive_manufacturing import verify_print_package
from workspace_service.workflow_enclosure_cfd import verify_enclosure_cfd
from workspace_service.workflow_engineering_assertions import all_pass
from workspace_service.workflow_supplier_handoff import verify_supplier_preview


DIGEST = "a" * 64
EVIDENCE = ["artifacts/result.json#sha256=" + DIGEST]


def test_print_package_checks_actual_scale_topology_volume_and_slice():
    passing = verify_print_package(
        {
            "reference_dimension_mm": 40,
            "scale_applied": True,
            "manifold": True,
            "watertight": True,
            "dimensions_mm": [80, 70, 60],
            "build_volume_mm": [256, 256, 256],
            "supports_generated": True,
            "toolpath_valid": True,
            "profile_compatible": True,
            "evidence": EVIDENCE,
        }
    )
    assert all_pass(passing)
    oversized = verify_print_package(
        {
            "reference_dimension_mm": 40,
            "scale_applied": True,
            "manifold": True,
            "watertight": True,
            "dimensions_mm": [300, 70, 60],
            "build_volume_mm": [256, 256, 256],
            "supports_generated": True,
            "toolpath_valid": True,
            "profile_compatible": True,
            "evidence": EVIDENCE,
        }
    )
    assert (
        next(
            item for item in oversized if item.assertion_id == "additive.build-volume"
        ).state
        == "fail"
    )


def test_cfd_rejects_substituted_geometry_and_theoretical_only_results():
    common = {
        "reference_authority": "manufacturer",
        "reference_document_id": "rpi5-mechanical-drawing",
        "cad_geometry_digest": DIGEST,
        "domain_geometry_digest": DIGEST,
        "boundary_names": ["inlet", "outlet", "walls"],
        "field_derived": True,
        "converged": True,
        "mass_imbalance_percent": 0.4,
        "mesh_change_percent": 1.2,
        "evidence": EVIDENCE,
    }
    assert all_pass(verify_enclosure_cfd(common))
    substituted = verify_enclosure_cfd({**common, "domain_geometry_digest": "b" * 64})
    assert substituted[1].state == "fail"
    theoretical = verify_enclosure_cfd({**common, "field_derived": False})
    assert theoretical[3].state == "fail"


def test_supplier_preview_requires_exact_files_quote_and_no_order_or_payment():
    common = {
        "design_check": "pass",
        "revision_count": 2,
        "files": {"psm": DIGEST, "step": DIGEST, "dxf": DIGEST},
        "dxf_verified": True,
        "uploaded_digest": DIGEST,
        "dxf_digest": DIGEST,
        "price": "42.50",
        "currency": "USD",
        "quantity": 1,
        "material": "5052-H32",
        "thickness": "0.063 in",
        "timestamp": "2026-09-11T00:00:00Z",
        "units_verified": True,
        "bends_verified": True,
        "order": False,
        "payment": False,
        "evidence": EVIDENCE,
    }
    assert all_pass(verify_supplier_preview(common))
    stale = verify_supplier_preview({**common, "uploaded_digest": "b" * 64})
    assert stale[2].state == "fail"
    unsafe = verify_supplier_preview({**common, "order": True})
    assert unsafe[3].state == "fail"


def test_missing_artifact_evidence_is_inconclusive_never_pass():
    results = verify_print_package(
        {
            "reference_dimension_mm": 40,
            "scale_applied": True,
            "manifold": True,
            "watertight": True,
            "dimensions_mm": [80, 70, 60],
            "build_volume_mm": [256, 256, 256],
            "supports_generated": True,
            "toolpath_valid": True,
            "profile_compatible": True,
            "evidence": [],
        }
    )
    assert {item.state for item in results} == {"inconclusive"}
