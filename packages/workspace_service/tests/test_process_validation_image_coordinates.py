"""Pixel measurements cannot borrow physical units or an expected image frame."""

from copy import deepcopy
from decimal import Decimal
import hashlib
import io

import pytest
from pydantic import ValidationError
from PIL import Image

from core.engineering_scenarios import EngineeringScenarioError, convert_unit
from core.image_coordinates import ImageCoordinateFrame
from core.process_validation import ValidationProfile, SubjectBinding, ProducerIdentity
from packages.workspace_service.tests.test_process_validation import (
    evaluate as evaluate_base,
    numeric_profile,
)


_image = io.BytesIO()
Image.new("RGB", (16, 12), "white").save(_image, format="PNG")
IMAGE_BYTES = _image.getvalue()
FRAME = {
    "image_sha256": hashlib.sha256(IMAGE_BYTES).hexdigest(),
    "width_px": 16,
    "height_px": 12,
    "axes": "x-right-y-down",
    "origin": "top-left",
    "pixel_reference": "centers",
}


def evaluate(tmp_path, value, *, profile):
    (tmp_path / "reference.png").write_bytes(IMAGE_BYTES)
    image = SubjectBinding(
        id="reference-image",
        role="reference_image",
        kind="file",
        format="png",
        locator="reference.png",
        encoding="raw-bytes",
        sha256=FRAME["image_sha256"],
        result_id="run:reference:image",
        producer=ProducerIdentity(
            run_id="run", step_id="reference", attempt=1, output_port="image"
        ),
    )
    return evaluate_base(tmp_path, value, profile=profile, related_subjects=(image,))


def image_profile():
    raw = numeric_profile().model_dump()
    raw["id"] = "image-residual-control"
    raw["version"] = "1"
    check = raw["checks"][0]
    check.update(
        selector="/residual",
        unit="px",
        frame=ImageCoordinateFrame(**FRAME).identifier(),
        constraint={"operator": "within", "target": 0.0, "tolerance": 2.0},
        parameters={
            "unit_pointer": "/unit",
            "image_frame_pointer": "/coordinates",
            "image_frame": FRAME,
            "image_subject_role": "reference_image",
            "related_roles": ["reference_image"],
        },
    )
    raw["checks"] = [check]
    raw["baseline"]["requirements"] = [
        item
        for item in raw["baseline"]["requirements"]
        if item["id"] in check["requirement_ids"]
    ]
    for requirement in raw["baseline"]["requirements"]:
        if requirement["id"] in check["requirement_ids"]:
            requirement["text"] = (
                "Synthetic residual at most 2 pixels in the pinned image coordinate frame."
            )
    return ValidationProfile.model_validate(raw)


def observation(value=0.5):
    return {"residual": value, "unit": "px", "coordinates": deepcopy(FRAME)}


@pytest.mark.parametrize("value,state", [(0.5, "pass"), (2.0, "pass"), (2.5, "fail")])
def test_image_residual_is_measured_in_exact_frame(tmp_path, value, state):
    result, _, _ = evaluate(tmp_path, observation(value), profile=image_profile())
    assert result.assessment.checks[0].state == state
    assert result.release_eligible is (state == "pass")
    assert result.assessment.measurements[0].value == value
    assert result.assessment.measurements[0].unit == "px"


@pytest.mark.parametrize(
    "key,value",
    [
        ("image_sha256", "b" * 64),
        ("width_px", 1500),
        ("height_px", 1000),
        ("axes", "x-right-y-up"),
        ("origin", "bottom-left"),
        ("pixel_reference", "edges"),
    ],
)
def test_changed_image_crop_resolution_or_convention_cannot_pass(tmp_path, key, value):
    measured = observation()
    measured["coordinates"][key] = value
    result, _, _ = evaluate(tmp_path, measured, profile=image_profile())
    assert not result.release_eligible
    assert result.assessment.findings[0].code == "measurement.frame"
    assert result.assessment.checks[0].state == "inconclusive"


@pytest.mark.parametrize("unit", ["mm", "1", "%"])
def test_other_units_cannot_masquerade_as_pixels(tmp_path, unit):
    measured = observation()
    measured["unit"] = unit
    result, _, _ = evaluate(tmp_path, measured, profile=image_profile())
    assert not result.release_eligible
    assert result.assessment.findings[0].code == "measurement.unit"


@pytest.mark.parametrize("removed", ["unit_pointer", "image_frame_pointer"])
def test_missing_observation_binding_does_not_inherit_expected_values(
    tmp_path, removed
):
    raw = image_profile().model_dump()
    del raw["checks"][0]["parameters"][removed]
    result, _, _ = evaluate(
        tmp_path, observation(), profile=ValidationProfile.model_validate(raw)
    )
    assert not result.release_eligible
    assert result.assessment.findings[0].code == "measurement.image_frame"


@pytest.mark.parametrize("frame", [None, {}, {**FRAME, "width_px": True}])
def test_absent_or_invalid_observed_frame_is_not_manufactured(tmp_path, frame):
    measured = observation()
    measured["coordinates"] = frame
    result, _, _ = evaluate(tmp_path, measured, profile=image_profile())
    assert not result.release_eligible
    assert result.assessment.findings[0].code == "measurement.image_frame"


def test_expected_frame_must_match_its_declared_image_metadata(tmp_path):
    raw = image_profile().model_dump()
    raw["checks"][0]["parameters"]["image_frame"] = {**FRAME, "width_px": 1500}
    result, _, _ = evaluate(
        tmp_path, observation(), profile=ValidationProfile.model_validate(raw)
    )
    assert not result.release_eligible
    assert result.assessment.findings[0].code == "profile.image_frame"


def test_frame_is_part_of_profile_revision():
    original = image_profile()
    raw = original.model_dump()
    frame = ImageCoordinateFrame(**{**FRAME, "image_sha256": "b" * 64})
    raw["checks"][0]["frame"] = frame.identifier()
    raw["checks"][0]["parameters"]["image_frame"] = frame.model_dump(mode="json")
    assert original.reference() != ValidationProfile.model_validate(raw).reference()


def test_changed_reference_image_invalidates_prior_assessment(tmp_path):
    result, service, _ = evaluate(tmp_path, observation(), profile=image_profile())
    assert result.release_eligible
    (tmp_path / "reference.png").write_bytes(IMAGE_BYTES + b"changed")
    assert not service.get_result(result.assessment.id).currentness.is_current


def test_pixel_check_requires_the_related_image(tmp_path):
    result, _, _ = evaluate_base(tmp_path, observation(), profile=image_profile())
    assert not result.release_eligible
    assert result.assessment.findings[0].code == "subject.related_role_missing"


@pytest.mark.parametrize(
    "source,target", [("px", "mm"), ("mm", "px"), ("px", "1"), ("1", "px")]
)
def test_unit_conversion_cannot_invent_a_calibration(source, target):
    with pytest.raises(EngineeringScenarioError) as caught:
        convert_unit(1, source, target)
    assert caught.value.code == "unit_dimension_mismatch"


def test_pixel_conversion_and_frame_contract_preserve_precision():
    assert convert_unit("0.125", "px", "px") == Decimal("0.125")
    with pytest.raises(ValidationError):
        ImageCoordinateFrame(**{**FRAME, "image_sha256": "not-a-digest"})
