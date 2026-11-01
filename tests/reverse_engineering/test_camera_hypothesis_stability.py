import pytest
from core.image_coordinates import ImageCoordinateFrame
from camera_hypothesis_stability import prediction_spread

FRAME = ImageCoordinateFrame(
    image_sha256="a" * 64,
    width_px=100,
    height_px=100,
    axes="x-right-y-down",
    origin="top-left",
    pixel_reference="centers",
)


def hypothesis(identity, point, maximum=1):
    return dict(
        id=identity,
        frame_id=FRAME.identifier(),
        artifact_sha256="b" * 64,
        calibration_maximum_px=maximum,
        predictions={"body-outline": point},
    )


def test_good_calibration_residuals_do_not_establish_stable_body_prediction():
    result = prediction_spread(
        [hypothesis("a", [20, 30]), hypothesis("b", [20, 50])],
        frame=FRAME,
        artifact_sha256="b" * 64,
        calibration_band_px=3,
    )
    assert result["feasible_hypothesis_ids"] == ["a", "b"]
    assert result["maximum_prediction_diameter_px"] == 20
    assert result["observations"][0]["diameter_witness_ids"] == ["a", "b"]


def test_one_feasible_pose_does_not_imply_zero_uncertainty():
    result = prediction_spread(
        [hypothesis("a", [20, 30]), hypothesis("b", [20, 50], 4)],
        frame=FRAME,
        artifact_sha256="b" * 64,
        calibration_band_px=3,
    )
    assert result["maximum_prediction_diameter_px"] is None
    assert result["excluded_hypotheses"] == [{"id": "b", "calibration_maximum_px": 4}]


@pytest.mark.parametrize(
    "field,value", [("artifact_sha256", "c" * 64), ("frame_id", "different-frame")]
)
def test_changed_geometry_or_raster_is_not_camera_uncertainty(field, value):
    second = hypothesis("b", [20, 50])
    second[field] = value
    with pytest.raises(ValueError, match="same exact"):
        prediction_spread(
            [hypothesis("a", [20, 30]), second],
            frame=FRAME,
            artifact_sha256="b" * 64,
            calibration_band_px=3,
        )
