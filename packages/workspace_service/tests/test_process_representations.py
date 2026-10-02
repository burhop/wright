"""Passive readers never invent topology, support classification, or acceptance."""

from __future__ import annotations

import hashlib
import io
import math
import zipfile

import pytest

from workspace_service.process_interfaces import representations as readers


def digest(content):
    return hashlib.sha256(content).hexdigest()


def gcode(body="G1 X10 Y0 E1", feature="Inner wall", header="G90\nG21\nM83"):
    return (
        header
        + "\nG1 X0 Y0 Z0.2\n; CHANGE_LAYER\n; Z_HEIGHT: 0.2\n; FEATURE: "
        + feature
        + "\n"
        + body
        + "\n"
    ).encode()


def parse(content):
    return readers.read_gcode_toolpaths(content, digest(content))


def archive(entries):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as output:
        for name, content in entries:
            entry = zipfile.ZipInfo(name)
            # Windows ZipInfo normally normalizes backslashes while writing;
            # retain the untrusted incoming archive name in this negative fixture.
            entry.filename = name
            output.writestr(entry, content, compress_type=zipfile.ZIP_DEFLATED)
    return buffer.getvalue()


def test_long_inert_metadata_comments_do_not_become_motion():
    content = gcode(
        header="; retained_metadata = " + "G1 X999 E99\\n" * 500 + "\nG90\nM83"
    )
    data = parse(content)
    assert data["layers"][0]["model"] == [[0, 0, 10, 0]]


@pytest.mark.parametrize(
    "line",
    ["G1 " + " " * 4096, ";" + "x" * 65_536, ";FEATURE: " + "x" * 257],
    ids=["command", "comment", "feature"],
)
def test_commands_comments_and_feature_labels_have_separate_bounds(line):
    with pytest.raises(readers.RepresentationUnavailable, match="bound"):
        parse(gcode() + line.encode())


def test_feature_evidence_count_has_a_separate_bound():
    with pytest.raises(readers.RepresentationUnavailable, match="feature evidence"):
        parse(
            gcode()
            + "\n".join(";FEATURE: custom " + str(i) for i in range(257)).encode()
        )


def test_actual_planar_coordinates_layers_and_unknown_features():
    content = gcode(
        "G1 X10 Y0 E1\n; FEATURE: Support interface\nG1 X10 Y10 E1\n; CHANGE_LAYER\n; Z_HEIGHT: 0.4\nG1 Z0.4\n; FEATURE: Mystery structure\nG1 X0 Y10 E1"
    )
    data = parse(content)
    assert data["package_sha256"] == digest(content)
    assert [(layer["index"], layer["z"]) for layer in data["layers"]] == [
        (0, 0.2),
        (1, 0.4),
    ]
    assert data["layers"][0]["model"] == [[0, 0, 10, 0]]
    assert data["layers"][0]["support"] == [[10, 0, 10, 10]]
    assert data["layers"][1]["unclassified"] == [[10, 10, 0, 10]]
    assert data["provenance"]["unclassified_features"] == ["mystery structure"]
    assert data["provenance"]["engineering_acceptance"] is False


def test_missing_feature_comments_do_not_infer_model_or_support():
    data = parse(gcode(feature="Unrecognized"))
    assert data["classification_source"] == "unknown"
    assert data["layers"][0]["model"] == data["layers"][0]["support"] == []
    assert len(data["layers"][0]["unclassified"]) == 1


def test_absolute_extrusion_retraction_reset_and_tool_state():
    data = parse(
        gcode(
            "G1 X10 E1\nG1 X20 E0.5\nG92 E0\nG1 X30 E1\nT1\nG1 X40 E1\nT0\nG1 X50 E1",
            header="G90\nG21\nM82",
        )
    )
    assert data["layers"][0]["model"] == [[0, 0, 10, 0], [20, 0, 30, 0], [30, 0, 40, 0]]


def test_relative_axes_and_inch_units():
    data = parse(gcode("G91\nM83\nG1 X1 E0.1", header="G90\nG20\nM83"))
    assert data["layers"][0]["model"] == [[0, 0, 25.4, 0]]
    assert data["layers"][0]["z"] == pytest.approx(5.08)


@pytest.mark.parametrize(
    "code",
    [
        "G3 X10 Y10 I0 J10 E1",
        "G2 X10 Y-10 I0 J-10 E1",
        "G3 X10 Y10 R10 E1",
        "G3 X10 Y10 R-10 E1",
    ],
)
def test_planar_arcs_have_actual_endpoints_and_bounded_chord_error(code):
    data = parse(gcode(code))
    segments = data["layers"][0]["model"]
    assert segments[0][:2] == [0, 0]
    assert segments[-1][2:] == [10, -10 if "Y-10" in code else 10]
    assert len(segments) > 1
    assert data["provenance"]["extruding_arcs"] == 1
    assert data["provenance"]["arc_maximum_chord_error_mm"] == 0.02
    radius = 10
    maximum_angle = max(
        2 * math.asin(min(1, math.hypot(s[2] - s[0], s[3] - s[1]) / (2 * radius)))
        for s in segments
    )
    assert radius * (1 - math.cos(maximum_angle / 2)) <= 0.020001


def test_full_circle_and_nonextruding_helical_travel():
    data = parse(gcode("G3 I0 J10 E1\nG3 Z0.6 I1 J0 P1\nG1 Z0.2\nG1 X10 E1"))
    assert data["layers"][0]["model"][0][:2] == data["layers"][0]["model"][-2][2:]
    assert data["layers"][0]["model"][-1] == [0, 0, 10, 0]


def test_cura_negative_layer_indices_are_retained_and_not_used_as_fake_z():
    content = b"G90\nM83\nG1 X0 Y0 Z0.1\n;LAYER:-1\n;TYPE:SUPPORT\nG1 X2 E1\n;LAYER:0\nG1 Z0.3\nG1 X4 E1\n"
    data = parse(content)
    assert [
        (layer["index"], layer["source_index"], layer["z"]) for layer in data["layers"]
    ] == [(0, -1, 0.1), (1, 0, 0.3)]


@pytest.mark.parametrize(
    "body",
    [
        "G1 Xnan E1",
        "G1 X1 X2 E1",
        "G1 X2 A1 E1",
        "G54\nG1 X2 E1",
        "G2 X10 Y10 R1 E1",
        "G2 X10 Y10 I0 J2 E1",
        "G3 I0 J10 P2 E1",
        "G3 I0 J10 Z0.4 E1",
        "G18\nG2 I0 J10 E1",
        "M200 D1\nG1 X2 E1",
        "G1 X2 Z0.4 E1",
        "G28\nG1 X2 E1",
        "G1 X1000001 E1",
        "UNKNOWN_MACRO\nG1 X2 E1",
    ],
)
def test_unsupported_semantics_fail_whole_view_instead_of_silently_dropping_paths(body):
    with pytest.raises(readers.RepresentationUnavailable):
        parse(gcode(body))


def test_missing_layer_comments_and_wrong_digest_are_explicit():
    with pytest.raises(readers.RepresentationUnavailable, match="layer"):
        parse(b"G90\nM83\nG1 X0 Y0 Z0.2\nG1 X10 E1\n")
    with pytest.raises(readers.RepresentationUnavailable, match="exact recorded"):
        readers.read_gcode_toolpaths(gcode(), "0" * 64)


def test_segment_layer_and_source_limits(monkeypatch):
    monkeypatch.setattr(readers, "MAX_SEGMENTS", 1)
    with pytest.raises(readers.RepresentationUnavailable, match="segment bound"):
        parse(gcode("G1 X2 E1\nG1 X3 E1"))
    monkeypatch.setattr(readers, "MAX_LAYERS", 1)
    with pytest.raises(readers.RepresentationUnavailable, match="layer count"):
        parse(gcode("G1 X2 E1\n;CHANGE_LAYER\n;Z_HEIGHT:0.4"))
    monkeypatch.setattr(readers, "MAX_GCODE_BYTES", 2)
    with pytest.raises(readers.RepresentationUnavailable, match="reader bound"):
        parse(gcode())


def test_exact_single_plate_package_and_entry_provenance():
    raw = gcode()
    content = archive([("Metadata/plate_1.gcode", raw), ("3D/model.model", b"inert")])
    data = readers.read_3mf_toolpaths(content, digest(content))
    assert data["package_sha256"] == digest(content)
    assert data["provenance"]["source_sha256"] == digest(raw)
    assert data["provenance"]["archive_entry"] == "Metadata/plate_1.gcode"


def test_multiple_plates_require_exact_selection():
    content = archive([("one.gcode", gcode()), ("two.gcode", gcode("G1 X20 E1"))])
    with pytest.raises(readers.RepresentationUnavailable, match="exact G-code plate"):
        readers.read_3mf_toolpaths(content, digest(content))
    selected = readers.read_3mf_toolpaths(content, digest(content), entry="two.gcode")
    assert selected["layers"][0]["model"] == [[0, 0, 20, 0]]
    with pytest.raises(readers.RepresentationUnavailable, match="exact package entry"):
        readers.read_3mf_toolpaths(content, digest(content), entry="absent.gcode")


@pytest.mark.parametrize(
    "entry", ["../model.gcode", "/model.gcode", "C:/model.gcode", "a\\model.gcode"]
)
def test_archive_paths_are_never_extracted_or_followed(entry):
    content = archive([(entry, gcode())])
    with pytest.raises(readers.RepresentationUnavailable, match="entry names"):
        readers.read_3mf_toolpaths(content, digest(content))


def test_duplicate_corrupt_and_oversized_archives_are_refused(monkeypatch):
    with pytest.warns(UserWarning, match="Duplicate"):
        content = archive([("one.gcode", gcode()), ("one.gcode", gcode())])
    with pytest.raises(readers.RepresentationUnavailable, match="duplicate"):
        readers.read_3mf_toolpaths(content, digest(content))
    with pytest.raises(readers.RepresentationUnavailable, match="could not be read"):
        readers.read_3mf_toolpaths(b"not a zip archive", digest(b"not a zip archive"))
    content = archive([("one.gcode", gcode())])
    monkeypatch.setattr(readers, "MAX_GCODE_BYTES", 2)
    with pytest.raises(readers.RepresentationUnavailable, match="G-code exceeds"):
        readers.read_3mf_toolpaths(content, digest(content))


def field(content):
    return readers.read_scalar_csv(
        content, digest(content), x="x_m", y="y_m", z="z_m", value="temperature_c"
    )


def test_scalar_csv_preserves_actual_samples_and_declared_columns():
    content = b'\xef\xbb\xbfx_m,y_m,z_m,temperature_c,note\r\n0,0,0,20,"quoted, note"\r\n.05,.03,.002,25.55555555558,tip\r\n'
    data = field(content)
    assert data["points"] == [[0, 0, 0, 20], [0.05, 0.03, 0.002, 25.55555555558]]
    assert data["source_sha256"] == digest(content)
    assert data["provenance"]["interpolated_geometry"] is False
    assert data["provenance"]["engineering_acceptance"] is False


@pytest.mark.parametrize(
    "content",
    [
        b"x_m,y_m,z_m,temperature_c\n0,0,0,nan\n",
        b"x_m,y_m,z_m,temperature_c\n0,0,0,inf\n",
        b"x_m,y_m,z_m,temperature_c\n0,0,0\n",
        b"x_m,y_m,z_m,temperature_c,temperature_c\n0,0,0,20,20\n",
        b"x_m,y_m,z_m,other\n0,0,0,20\n",
        b"x_m,y_m,z_m,temperature_c\n",
    ],
)
def test_scalar_csv_missing_ambiguous_or_nonfinite_fields_are_explicit(content):
    with pytest.raises(readers.RepresentationUnavailable):
        field(content)
