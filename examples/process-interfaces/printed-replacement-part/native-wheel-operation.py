"""Accepted example task payload for the independent FreeCAD MCP.

The authoring helper replaces the single configuration expression before pinning
this recipe. Wright sends its code argument to the selected provider; this file
is never imported or executed by Wright's runtime or a local campaign executor.
Engineering acceptance belongs to the separate exact-output validation stages.
"""
import FreeCAD as App
import FreeCADGui as Gui
import MeshPart
import Part
import Sketcher
import hashlib
import json
import math
from pathlib import Path
from PySide import QtCore, QtGui, QtWidgets

CONFIG = __WRIGHT_NATIVE_WHEEL_CONFIG__  # noqa: F821 -- filled in the pinned provider argument before execution
output = Path(CONFIG["output_directory"])
output.mkdir(parents=True, exist_ok=True)
filenames = ("native-design.FCStd", "native-design.step", "native-design.png", "source_mesh.stl", "native-measurements.json")
assert not any((output / name).exists() for name in filenames), "Preserve existing run artifacts; do not overwrite"
name = "FocusWheel_" + hashlib.sha256(str(output).encode()).hexdigest()[:12]
assert name not in App.listDocuments(), "Owned document already exists; inspect before replay"
doc = App.newDocument(name)
body = doc.addObject("PartDesign::Body", "FocusWheel")
p = CONFIG["geometry"]


def checked(feature):
    doc.recompute()
    assert not feature.Shape.isNull() and feature.Shape.isValid(), "Invalid native feature: " + feature.Name + ": " + feature.getStatusString()
    assert len(feature.Shape.Solids) == 1, "Native wheel must remain one solid: " + feature.Name
    return feature


base = body.newObject("PartDesign::AdditiveCylinder", "BodyCylinder")
base.Label = "Wheel body — diameter 38, height 16 mm"
base.Radius = p["outer_radius_mm"]
base.Height = p["body_height_mm"]
checked(base)
last = base
for index in range(p["scallop_count"]):
    angle = math.radians(p["scallop_phase_degrees"] + 360 * index / p["scallop_count"])
    cut = body.newObject("PartDesign::SubtractiveCylinder", "Scallop" + str(index + 1))
    cut.Radius = p["scallop_cutter_radius_mm"]
    cut.Height = p["body_height_mm"]
    cut.Placement.Base = App.Vector(p["scallop_center_radius_mm"] * math.cos(angle), p["scallop_center_radius_mm"] * math.sin(angle), 0)
    last = checked(cut)

rounds = body.newObject("PartDesign::Fillet", "ExposedBodyRounds")
rounds.Base = (last, ["Edge" + str(i + 1) for i in range(len(last.Shape.Edges))])
rounds.Radius = p["exposed_radius_mm"]
last = checked(rounds)
# Construct the same nominal hub and its two circular rounds as a native
# revolved meridian. At height=2*R the rounds meet tangentially; an edge-fillet
# feature failed for that boundary case in the retained second native attempt.
# This profile retains the requested height/radius rather than reducing rounds.
hub_radius = p["hub_radius_mm"]
hub_height = p["hub_height_mm"]
round_radius = p["exposed_radius_mm"]
assert hub_height >= 2 * round_radius and hub_radius > round_radius
hub_profile = body.newObject("Sketcher::SketchObject", "RoundedHubMeridian")
hub_profile.Label = f"Hub meridian — nominal diameter {2 * hub_radius:g}, height {hub_height:g}, root/rim R{round_radius:g}"
hub_profile.Placement = App.Placement(
    App.Vector(0, 0, p["body_height_mm"]), App.Rotation(App.Vector(1, 0, 0), 90)
)
hub_profile.setExpression("Placement.Base.z", "BodyCylinder.Height")
def point(x, y):
    return App.Vector(x, y, 0)


q = round_radius / math.sqrt(2)
meridian = [
    Part.LineSegment(point(0, 0), point(hub_radius + round_radius, 0)),
    Part.Arc(
        point(hub_radius + round_radius, 0),
        point(hub_radius + round_radius - q, round_radius - q),
        point(hub_radius, round_radius),
    ),
]
if hub_height > 2 * round_radius:
    meridian.append(Part.LineSegment(point(hub_radius, round_radius), point(hub_radius, hub_height - round_radius)))
meridian.extend([
    Part.Arc(
        point(hub_radius, hub_height - round_radius),
        point(hub_radius - round_radius + q, hub_height - round_radius + q),
        point(hub_radius - round_radius, hub_height),
    ),
    Part.LineSegment(point(hub_radius - round_radius, hub_height), point(0, hub_height)),
    Part.LineSegment(point(0, hub_height), point(0, 0)),
])
for geometry in meridian:
    index = hub_profile.addGeometry(geometry, False)
    hub_profile.addConstraint(Sketcher.Constraint("Block", index))
doc.recompute()
body.Tip = last
hub = body.newObject("PartDesign::Revolution", "RoundedFrontHub")
hub.Profile = hub_profile
hub.ReferenceAxis = (hub_profile, ["V_Axis"])
hub.Angle = 360
last = checked(hub)
hub_profile.Visibility = False

cap_radius = ((p["dot_diameter_mm"] / 2) ** 2 + p["dot_height_mm"] ** 2) / (2 * p["dot_height_mm"])
assert p["dot_count"] == 12, "This baseline recipe declares two dots per lobe"
for index in range(p["dot_count"]):
    angle = math.radians(30 + 60 * (index // 2) + (-8 if index % 2 == 0 else 8))
    dot = body.newObject("PartDesign::AdditiveSphere", "GripDot" + str(index + 1))
    dot.Radius = cap_radius
    dot.Placement.Base = App.Vector(p["dot_center_radius_mm"] * math.cos(angle), p["dot_center_radius_mm"] * math.sin(angle), p["body_height_mm"] - cap_radius + p["dot_height_mm"])
    dot.setExpression("Placement.Base.z", "BodyCylinder.Height - " + repr(cap_radius) + " mm + " + repr(p["dot_height_mm"]) + " mm")
    last = checked(dot)

socket = body.newObject("Sketcher::SketchObject", "DSocketProfile")
radius = p["socket_round_radius_mm"]
flat = p["socket_flat_x_mm"]
half_chord = math.sqrt(radius ** 2 - flat ** 2)
bottom = App.Vector(flat, -half_chord, 0)
top = App.Vector(flat, half_chord, 0)
socket.addGeometry(Part.Arc(bottom, App.Vector(radius, 0, 0), top), False)
socket.addGeometry(Part.LineSegment(top, bottom), False)
socket.addConstraint(Sketcher.Constraint("Block", 0))
socket.addConstraint(Sketcher.Constraint("Block", 1))
body.Tip = last
pocket = body.newObject("PartDesign::Pocket", "BlindDSocket")
pocket.Profile = socket
pocket.Length = p["socket_depth_mm"]
pocket.Reversed = True
last = checked(pocket)
body.Tip = last
socket.Visibility = False
for feature in body.Group:
    if hasattr(feature, "Shape"):
        feature.Visibility = feature == last
body.Visibility = True

shape = last.Shape
# Cached display triangulation can under-estimate bounds; the default optimal
# box can also include triangulation deflection. Measure the native surfaces.
bounds = shape.optimalBoundingBox(False, False)
assert max(bounds.XLength, bounds.YLength) <= 2 * p["outer_radius_mm"] + 1e-5, "Native geometry exceeds the maximum diameter"
assert abs(max(bounds.XLength, bounds.YLength) - 2 * p["outer_radius_mm"]) < 1e-5, "Native geometry does not retain the nominal maximum diameter"
assert abs(bounds.ZLength - p["body_height_mm"] - p["hub_height_mm"]) < 1e-5, "Native geometry does not retain the overall height"
section = shape.section(Part.makePlane(100, 100, App.Vector(-50, -50, p["socket_depth_mm"] / 2)))
socket_edges = [edge for edge in section.Edges if all(abs(v.Point.x) < 4 and abs(v.Point.y) < 4 for v in edge.Vertexes)]
assert len(socket_edges) == 2, "Mid-depth section must retain circular wall and flat, not a circular bore"
assert any(isinstance(edge.Curve, Part.Circle) and abs(edge.Curve.Radius - radius) < 1e-6 for edge in socket_edges)
assert any(all(abs(v.Point.x - flat) < 1e-6 for v in edge.Vertexes) for edge in socket_edges)

doc.saveAs(str(output / "native-design.FCStd"))
Part.export([body], str(output / "native-design.step"))
mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=CONFIG["mesh_linear_deflection_mm"], AngularDeflection=math.radians(CONFIG["mesh_angular_deflection_degrees"]), Relative=False)
assert 0 < mesh.CountFacets <= 80000, "Preserve original triangle bound"
mesh.write(str(output / "source_mesh.stl"))
def capture_native_preview(document, destination):
    """Capture this document after display updates; retain failed candidates.

    The pixel check detects the observed empty white frame only. It does not
    verify geometric correspondence, features, dimensions or engineering quality.
    Only the view is retried; CAD construction is never replayed here.
    """
    assert not destination.exists(), "Preserve the existing native preview"
    view = Gui.getDocument(document.Name).activeView()
    view.viewAxonometric()
    view.fitAll()
    samples = []
    for attempt in range(1, 4):
        candidate = destination.with_name(destination.stem + "-attempt-" + str(attempt) + ".png")
        assert not candidate.exists(), "Preserve prior capture diagnostics"
        Gui.updateGui()
        QtWidgets.QApplication.processEvents()
        view.redraw()
        # Native view updates are queued by FreeCAD. Yield to its event loop for
        # a bounded display-only interval before taking the same document's view.
        loop = QtCore.QEventLoop()
        QtCore.QTimer.singleShot(100, loop.quit)
        loop.exec_()
        view.saveImage(str(candidate), 1200, 900, "White")
        image = QtGui.QImage(str(candidate))
        assert not image.isNull() and image.width() == 1200 and image.height() == 900, "Native screenshot could not be decoded at the declared size"
        points = [(x, y) for y in range(5, 900, 10) for x in range(5, 1200, 10)]
        foreground = sum(min(image.pixelColor(x, y).red(), image.pixelColor(x, y).green(), image.pixelColor(x, y).blue()) < 245 for x, y in points)
        fraction = foreground / len(points)
        samples.append({"candidate": candidate.name, "sampled_nonwhite_fraction": fraction})
        if fraction >= 0.01:
            candidate.rename(destination)
            return {"document": document.Name, "method": "Exact document native view after bounded display update; 10px grid, RGB min below245", "minimum_fraction": 0.01, "attempts": samples, "scope": "Nonblank capture only; independent geometry and visual review remain required"}
    raise RuntimeError("Native CAD preview remained blank after three display-only captures; inspect retained candidates")


preview_check = capture_native_preview(doc, output / "native-design.png")
report = {
    "scope": "Actual native CAD producer observations; downstream independent validation and human/physical acceptance remain required",
    "document": name, "units": "mm", "model_frame": "Socket opens at rear z=0; front hub extends to z=18",
    "supplied_geometry": p, "measured": {"valid": shape.isValid(), "solid_count": len(shape.Solids),
        "volume_mm3": shape.Volume, "bounds_mm": [bounds.XMin, bounds.YMin, bounds.ZMin, bounds.XMax, bounds.YMax, bounds.ZMax],
        "bounds_method": "Native shape.optimalBoundingBox(False, False); no display triangulation; original 1e-5 mm numerical assertion tolerance",
        "mid_depth_socket_section_edges": len(socket_edges), "socket_section_round_radius_mm": next(edge.Curve.Radius for edge in socket_edges if isinstance(edge.Curve, Part.Circle)),
        "socket_section_flat_x_mm": next(edge.Vertexes[0].Point.x for edge in socket_edges if not isinstance(edge.Curve, Part.Circle)),
        "mesh_facets": mesh.CountFacets},
    "hub_definition": {
        "native_feature": "RoundedFrontHub", "profile": "RoundedHubMeridian",
        "nominal_virtual_sharp_radius_mm": hub_radius, "height_mm": hub_height,
        "root_and_rim_radius_mm": round_radius,
        "root_foot_radius_mm": hub_radius + round_radius,
        "top_face_radius_mm": hub_radius - round_radius,
        "scope": "Producer construction parameters; independent geometry verification still required",
    },
    "features": [{"name": feature.Name, "type": feature.TypeId} for feature in body.Group],
    "mesh_conversion": {"linear_deflection_mm": CONFIG["mesh_linear_deflection_mm"], "angular_deflection_degrees": CONFIG["mesh_angular_deflection_degrees"], "coordinate_units": "mm; STL carries no unit metadata"},
    "engineering_acceptance": False, "physical_acceptance": False,
    "preview_check": preview_check,
    "files": {filename: {"bytes": (output / filename).stat().st_size, "sha256": hashlib.sha256((output / filename).read_bytes()).hexdigest()} for filename in filenames[:-1]},
}
(output / "native-measurements.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report))
