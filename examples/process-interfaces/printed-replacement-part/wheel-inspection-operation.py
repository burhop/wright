"""Authored independent FreeCAD inspection payload, sent through its MCP.

This module is never imported by Wright. Its exact input hashes and inspection
criteria are accepted workflow data. Numeric conversion checks do not establish
manufacturing accuracy, printed fit, strength or human acceptance.
"""
import FreeCAD as App
import FreeCADGui as Gui
import Part
import TechDraw  # noqa: F401 -- loads the native drawing types used by this recipe
import TechDrawGui
from PySide import QtCore, QtGui, QtSvg
import collections
import hashlib
import json
import math
import re
import struct
from pathlib import Path

CONFIG = __WRIGHT_WHEEL_INSPECTION_CONFIG__  # noqa: F821
drawing_number = CONFIG["drawing_number"]
assert isinstance(drawing_number, str) and re.fullmatch(r"[A-Z0-9-]{1,20}", drawing_number), "Declare this drawing's exact revision identity"
output = Path(CONFIG["output_directory"])
output.mkdir(parents=True, exist_ok=True)
files = ("engineering-measurements.json", "inspection-drawing.FCStd", "inspection-drawing.svg", "inspection-drawing.pdf", "inspection-drawing.png", "requirements-matrix.md")
assert not any((output / name).exists() for name in files), "Preserve previous inspection artifacts"
inputs = {}
input_reference_mode = CONFIG.get("input_reference_mode", "pinned")
assert input_reference_mode in ("pinned", "workflow_dependencies"), "Unknown input identity mode"
assert set(CONFIG["inputs"]) == {"native", "step", "mesh"}, "Declare all three exact upstream inputs"
for role, reference in CONFIG["inputs"].items():
    expected_keys = {"path", "sha256"} if input_reference_mode == "pinned" else {"path"}
    assert set(reference) == expected_keys, "Declare the selected input identity contract"
    path = Path(reference["path"])
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if input_reference_mode == "pinned":
        assert digest == reference["sha256"], "Exact upstream input changed: " + role
    # In the same-run mode, the accepted step's declared mcp_file_dependencies
    # are checked by Wright against actual producer bytes before this tool call.
    # Record the independently consumed bytes; this flag grants no authority.
    inputs[role] = {"path": str(path), "sha256": digest, "bytes": len(raw),
                    "reference_mode": input_reference_mode}

native = App.openDocument(CONFIG["inputs"]["native"]["path"])
bodies = [obj for obj in native.Objects if obj.TypeId == "PartDesign::Body"]
assert len(bodies) == 1, "Expected the exact editable wheel body"
body = bodies[0]
native_shape = body.Tip.Shape.copy()
neutral = Part.read(CONFIG["inputs"]["step"]["path"])
assert native_shape.isValid() and neutral.isValid(), "Native or STEP shape invalid"
assert len(native_shape.Solids) == len(neutral.Solids) == 1, "Expected one solid"
bounds = neutral.optimalBoundingBox(False, False)
assert abs(bounds.ZLength - 18.0) < 1e-5 and abs(bounds.YLength - 38.0) < 1e-5
common = native_shape.common(neutral)
conversion_difference = abs(native_shape.Volume + neutral.Volume - 2 * common.Volume)
assert conversion_difference <= 0.001, "Native/STEP symmetric volume disagreement"
features = [{"name": obj.Name, "type": obj.TypeId, "status": obj.getStatusString()} for obj in body.Group]
scallops = [obj for obj in body.Group if obj.TypeId == "PartDesign::SubtractiveCylinder"]
dots = [obj for obj in body.Group if obj.TypeId == "PartDesign::AdditiveSphere"]
assert len(scallops) == 6 and len(dots) == 12
centres = [obj.Placement.Base for obj in scallops]
phases = sorted(math.degrees(math.atan2(v.y, v.x)) % 360 for v in centres)
phase_spacings = [(phases[(i + 1) % 6] - phases[i]) % 360 for i in range(6)]
assert all(abs(delta - 60.0) < 1e-6 for delta in phase_spacings)
grip_section = neutral.section(Part.makePlane(100, 100, App.Vector(-50, -50, 8), App.Vector(0, 0, 1)))
grip_radii = []
for edge in grip_section.Edges:
    for point in edge.discretize(101):
        r = math.hypot(point.x, point.y)
        if r > 10:
            grip_radii.append(r)
sampled_minimum_grip = 2 * min(grip_radii)
assert sampled_minimum_grip >= 33.0, "Minimum sampled grip diameter below 33 mm"
def measure_socket_section(section, z):
    """Return observed dimensions, including out-of-tolerance dimensions.

    The accepted validation profile compares these values with requirements.
    Structural prerequisites still fail explicitly when this reader cannot
    identify a circular wall and planar flat from the exact STEP section.
    """
    edges = [edge for edge in section.Edges if all(abs(v.Point.x) < 4 and abs(v.Point.y) < 4 for v in edge.Vertexes)]
    arcs = [edge for edge in edges if isinstance(edge.Curve, Part.Circle)]
    flats = [edge for edge in edges if not isinstance(edge.Curve, Part.Circle)]
    assert len(arcs) == len(flats) == 1 and len(edges) == 2, "Socket measurement needs one circular wall and one flat"
    flat_vertices = [v.Point.x for v in flats[0].Vertexes]
    assert len(flat_vertices) == 2 and all(math.isfinite(x) for x in flat_vertices), "Socket flat vertices are unavailable"
    assert abs(flat_vertices[0] - flat_vertices[1]) <= 1e-6, "Socket flat is not parallel to the declared YZ plane"
    radius = arcs[0].Curve.Radius
    assert math.isfinite(radius) and radius > 0, "Socket circular-wall radius is unavailable"
    return {"z_mm": z, "round_radius_mm": radius, "flat_x_mm": flat_vertices[0]}


def socket_observation_text(sections):
    return "; ".join(
        f"z={item['z_mm']:g}: R{item['round_radius_mm']:.6g}, x={item['flat_x_mm']:.6g}, span={item['round_radius_mm'] - item['flat_x_mm']:.6g} mm"
        for item in sections
    )


socket_sections = []
for z in (0.1, 5.0, 9.9):
    section = neutral.section(Part.makePlane(100, 100, App.Vector(-50, -50, z), App.Vector(0, 0, 1)))
    socket_sections.append(measure_socket_section(section, z))
measured_socket_radius = socket_sections[1]["round_radius_mm"]
measured_socket_flat = socket_sections[1]["flat_x_mm"]
assert not neutral.isInside(App.Vector(0, 0, 9.999), 1e-7, True)
assert neutral.isInside(App.Vector(0, 0, 10.001), 1e-7, True)
middle_section = neutral.section(Part.makePlane(100, 100, App.Vector(-50, -50, 5), App.Vector(0, 0, 1)))
socket_edges = [edge for edge in middle_section.Edges if all(abs(v.Point.x) < 4 and abs(v.Point.y) < 4 for v in edge.Vertexes)]
socket_face = Part.Face(Part.Wire(socket_edges))
socket_face.translate(App.Vector(0, 0, 5))
roof_probe = socket_face.extrude(App.Vector(0, 0, 3))
roof_uncovered_volume = roof_probe.Volume - roof_probe.common(neutral).Volume
assert abs(roof_uncovered_volume) < 1e-5, "Required 3 mm roof is not solid over the socket"

raw = Path(CONFIG["inputs"]["mesh"]["path"]).read_bytes()
facet_count = struct.unpack_from("<I", raw, 80)[0]
assert 0 < facet_count <= 80000 and len(raw) == 84 + 50 * facet_count
edge_counts = collections.Counter()
vertices = {}
facets = []
signed_volume = 0.0
for index in range(facet_count):
    values = struct.unpack_from("<12fH", raw, 84 + 50 * index)
    points = [tuple(values[3 + j * 3:6 + j * 3]) for j in range(3)]
    assert all(math.isfinite(value) for point in points for value in point)
    keys = [tuple(round(value, 6) for value in point) for point in points]
    a, b, c = [App.Vector(*point) for point in points]
    assert (b - a).cross(c - a).Length > 1e-10, "Degenerate exported facet"
    signed_volume += a.dot(b.cross(c)) / 6
    for point, key in zip(points, keys):
        vertices[key] = point
    for j in range(3):
        edge_counts[tuple(sorted((keys[j], keys[(j + 1) % 3])))] += 1
    facets.append(points)
assert all(count == 2 for count in edge_counts.values()), "STL boundary/non-manifold edges"
assert signed_volume > 0, "STL winding has non-positive signed volume"
sample_distances = []
sample_points = list(vertices.values())
for collection, kind in ((sample_points, "vertex"), (facets, "facet_centroid")):
    for k in range(64):
        index = k * (len(collection) - 1) // 63
        point = collection[index]
        if kind == "facet_centroid":
            point = tuple(sum(p[j] for p in point) / 3 for j in range(3))
        distance = neutral.distToShape(Part.Vertex(App.Vector(*point)))[0]
        sample_distances.append({"kind": kind, "index": index, "distance_mm": distance})
maximum_deviation = max(row["distance_mm"] for row in sample_distances)
assert maximum_deviation <= 0.05, "Sampled STL-to-STEP conversion deviation exceeds 0.05 mm"

name = "WheelInspection_" + hashlib.sha256(str(output).encode()).hexdigest()[:10]
assert name not in App.listDocuments(), "Inspect an existing inspection document before replay"
doc = App.newDocument(name)
model = doc.addObject("Part::Feature", "ExactUpstreamSTEP")
model.Shape = neutral
socket_model = doc.addObject("Part::Feature", "ExactSocketSectionZ5")
socket_model.Shape = Part.Compound(socket_edges)
page = doc.addObject("TechDraw::DrawPage", "WheelInspection")
template = doc.addObject("TechDraw::DrawSVGTemplate", "InstalledA4Template")
template.Template = App.getResourceDir() + "Mod/TechDraw/Templates/ISO/A4_Landscape_TD.svg"
page.Template = template
page.Scale = 2.0
texts = dict(template.EditableTexts)
texts.update({"Designed_by_Name": "Wright study", "Drawing_number": drawing_number, "FC-SC": "2:1 *", "FC-SH": "1 / 1", "FC-Title": "Focus wheel", "Subtitle": "DIGITAL INSPECTION", "Weight": "--", "copyright": "mm / PETG / NOT FOR MANUFACTURE / Physical fit, torque and thermal use unverified"})
template.EditableTexts = texts
views = []
for label, source, direction, x, y in (("FrontFace", model, (0, 0, 1), 65, 148), ("SocketDetail", socket_model, (0, 0, -1), 195, 159)):
    view = doc.addObject("TechDraw::DrawViewPart", label)
    page.addView(view)
    view.Source = [source]
    view.Direction = App.Vector(*direction)
    view.XDirection = App.Vector(1, 0, 0)
    view.ScaleType = "Custom" if label == "SocketDetail" else "Page"
    if label == "SocketDetail":
        view.Scale = 6.0
    view.X, view.Y = x, y
    view.LockPosition = True
    # Explicit annotations below avoid automatic captions colliding with dimensions.
    view.Caption = ""
    views.append(view)
doc.recompute()
section = doc.addObject("TechDraw::DrawViewSection", "SectionAA_Y0")
page.addView(section)
section.BaseView = views[0]
section.Source = [model]
section.SectionOrigin = App.Vector(0, 0, 0)
section.SectionNormal = App.Vector(0, -1, 0)
section.Direction = App.Vector(0, -1, 0)
section.XDirection = App.Vector(1, 0, 0)
section.ScaleType = "Page"
section.X, section.Y = 65, 62
section.LockPosition = True
section.SectionSymbol = "A"
section.Caption = ""
views.append(section)
doc.recompute()


def await_drawing_projection(projected_views, timeout_ms=30000):
    """Wait for actual native edges while servicing TechDraw's GUI callbacks."""
    assert projected_views and 0 < timeout_ms <= 30000
    timer = QtCore.QElapsedTimer()
    timer.start()
    polls = 0
    while True:
        polls += 1
        pending = []
        for view in projected_views:
            try:
                view.getEdgeByIndex(0)
            except ValueError:
                pending.append(view.Name)
        if not pending:
            return {"elapsed_ms": timer.elapsed(), "polls": polls,
                    "views": [view.Name for view in projected_views],
                    "scope": "Native projected edges available; feature and dimension checks still required"}
        remaining = timeout_ms - timer.elapsed()
        assert remaining > 0, "Projected geometry unavailable after bounded wait: " + ", ".join(pending)
        loop = QtCore.QEventLoop()
        QtCore.QTimer.singleShot(min(100, remaining), loop.quit)
        loop.exec_()


projection_readiness = await_drawing_projection(views)


def drawing_edges(view):
    """Read actual indexed projected geometry in model units.

    Visible-edge list positions can differ from reference indices when hidden
    edges exist. Ask TechDraw for each real index instead; never dimension a
    guessed edge number. These APIs return unscaled geometry with Y upwards;
    getVisibleEdges() uses scaled drawing coordinates with Y downwards.
    """
    result = []
    for index in range(2000):
        try:
            edge = view.getEdgeByIndex(index)
        except ValueError:
            break
        result.append((index, edge))
    else:
        raise AssertionError("Projected geometry exceeds the qualified inspection scope")
    assert result, "Projected geometry is unavailable"
    return result


def select_drawing_edge(edges, predicate, feature):
    matches = [(index, edge) for index, edge in edges if predicate(edge)]
    assert matches, "Drawing feature unavailable: " + feature
    # Equivalent occurrences (for example the six identical scallops) are
    # ordered by native reference. Callers constrain the intended feature.
    return matches[0]


def line(edge):
    return isinstance(edge.Curve, Part.Line) and len(edge.Vertexes) == 2


def near(value, expected):
    return abs(value - expected) < 1e-5


front_edges, detail_edges, section_edges = [drawing_edges(view) for view in views]
socket_radius_edge = select_drawing_edge(detail_edges, lambda edge: isinstance(edge.Curve, Part.Circle), "socket circular wall")
socket_floor = select_drawing_edge(section_edges, lambda edge: line(edge) and
    near(edge.Length, measured_socket_radius - measured_socket_flat) and
    near(max(v.Point.x for v in edge.Vertexes), measured_socket_radius) and
    near(min(v.Point.x for v in edge.Vertexes), measured_socket_flat), "socket floor")
socket_wall = select_drawing_edge(section_edges, lambda edge: line(edge) and
    all(near(v.Point.x, measured_socket_radius) for v in edge.Vertexes), "socket round-wall section")
horizontal = [(i, edge) for i, edge in section_edges if line(edge) and near(edge.Vertexes[0].Point.y, edge.Vertexes[1].Point.y)]
hub_top = max(horizontal, key=lambda item: item[1].CenterOfMass.y)
body_top_candidates = [(i, edge) for i, edge in horizontal if abs(edge.CenterOfMass.x) > 7]
assert body_top_candidates, "Body top beside raised hub is unavailable"
body_top = max(body_top_candidates, key=lambda item: item[1].CenterOfMass.y)
outer_right = max([(i, edge) for i, edge in section_edges if line(edge) and near(edge.Vertexes[0].Point.x, edge.Vertexes[1].Point.x)], key=lambda item: item[1].CenterOfMass.x)
outer_left = min([(i, edge) for i, edge in section_edges if line(edge) and near(edge.Vertexes[0].Point.x, edge.Vertexes[1].Point.x)], key=lambda item: item[1].CenterOfMass.x)
scallop_edge = select_drawing_edge(front_edges, lambda edge: isinstance(edge.Curve, Part.Circle) and
    near(edge.Curve.Radius, float(scallops[0].Radius)) and edge.Curve.Center.x > 0 and near(edge.Curve.Center.y, 0), "right-hand scallop")
round_edge = select_drawing_edge(section_edges, lambda edge: isinstance(edge.Curve, Part.Circle) and
    near(edge.Curve.Radius, 1.0) and edge.Curve.Center.x > 10 and edge.Curve.Center.y < 0, "exposed rear edge round")
dimensions = []


def add_dimension(feature, view, kind, references, observed, position, extent=False):
    dim = doc.addObject("TechDraw::DrawViewDimExtent" if extent else "TechDraw::DrawViewDimension", feature)
    dim.Type = kind
    refs = [(view, "Edge" + str(index)) for index in references] if references else [(view, "")]
    dim.References2D = refs
    dim.MeasureType = "Projected"
    if extent:
        dim.Source = refs
        dim.DirExtent = 1 if kind == "DistanceY" else 0
    page.addView(dim)
    dim.X, dim.Y = position
    dim.ViewObject.Fontsize = 3.5
    doc.recompute()
    assert near(dim.getRawValue(), observed), "Linked dimension disagrees with observed geometry: " + feature
    dimensions.append({"feature": feature, "view": view.Name, "references": [ref[1] for ref in refs],
        "kind": kind, "value_mm": dim.getRawValue(), "display": dim.getText(),
        "measurement_basis": "native projected geometry; no overridden value"})
    return dim


add_dimension("Envelope", views[0], "DistanceY", [], bounds.YLength, (-45, 18), extent=True)
add_dimension("ScallopRadius", views[0], "Radius", [scallop_edge[0]], float(scallops[0].Radius), (48, 22))
add_dimension("SocketRadius", views[1], "Radius", [socket_radius_edge[0]], measured_socket_radius, (37, 14))
add_dimension("OverallHeight", section, "DistanceY", [], bounds.ZLength, (-45, 0), extent=True)
add_dimension("SocketDepth", section, "DistanceY", [socket_wall[0]], socket_wall[1].Length, (42, -6))
add_dimension("SocketAcrossFlat", section, "DistanceX", [socket_floor[0]], socket_floor[1].Length, (0, -30))
add_dimension("HubHeight", section, "DistanceY", [hub_top[0], body_top[0]],
    hub_top[1].CenterOfMass.y - body_top[1].CenterOfMass.y, (29, 20))
add_dimension("SocketRoofAtAxis", section, "DistanceY", [hub_top[0], socket_floor[0]],
    abs(hub_top[1].CenterOfMass.y - socket_floor[1].CenterOfMass.y), (-13, 9))
add_dimension("GripAtSection", section, "DistanceX", [outer_left[0], outer_right[0]],
    outer_right[1].CenterOfMass.x - outer_left[1].CenterOfMass.x, (0, -42))
add_dimension("ExposedRound", section, "Radius", [round_edge[0]], round_edge[1].Curve.Radius, (49, -15))
notes = doc.addObject("TechDraw::DrawViewAnnotation", "DimensionalBasis")
page.addView(notes)
notes.Text = ["DESIGN BASIS / mm", "PETG study; no manufacturing release.",
    "6 scallops at 60 deg; 12 raised grip dots.",
    "Rear face: datum A (z=0); socket axis: datum B.",
    "Nominal shaft: round 6.00; across-flat 5.20.",
    "Design clearance: 0.20 radial and at the flat.",
    f"Measured socket flat x={measured_socket_flat:.2f} from axis.",
    "Tolerance / fit trials: see requirements matrix.",
    "All dimensions are CAD observations; review required."]
notes.TextSize = 3.0
notes.X, notes.Y = 213, 90
for label, text, x, y in (("FrontLabel", "FRONT / 2:1", 65, 103),
                           ("DetailLabel", "D SOCKET / Z=5 SECTION / 6:1", 195, 132),
                           ("SectionLabel", "SECTION A-A / 2:1", 65, 87)):
    caption = doc.addObject("TechDraw::DrawViewAnnotation", label)
    page.addView(caption)
    caption.Text = [text]
    caption.TextSize = 3.0
    caption.X, caption.Y = x, y
doc.recompute()
doc.saveAs(str(output / "inspection-drawing.FCStd"))
Gui.activeDocument().getObject(page.Name).show()
Gui.updateGui()
loop = QtCore.QEventLoop()
QtCore.QTimer.singleShot(500, loop.quit)
loop.exec_()
TechDrawGui.exportPageAsSvg(page, str(output / "inspection-drawing.svg"))
TechDrawGui.exportPageAsPdf(page, str(output / "inspection-drawing.pdf"))
# Passive preview from the exact native SVG export, not a separate drawing or
# generated illustration. Keep vector/native originals as the measured evidence.
svg_renderer = QtSvg.QSvgRenderer(str(output / "inspection-drawing.svg"))
assert svg_renderer.isValid(), "Native drawing SVG cannot be rendered"
preview_size = svg_renderer.defaultSize()
assert preview_size.width() > 0 and preview_size.height() > 0
preview = QtGui.QImage(2400, round(2400 * preview_size.height() / preview_size.width()), QtGui.QImage.Format_ARGB32)
preview.fill(QtGui.QColor("white"))
painter = QtGui.QPainter(preview)
svg_renderer.render(painter)
painter.end()
assert preview.save(str(output / "inspection-drawing.png")), "Native drawing preview could not be saved"
report = {"scope": "Independent saved-native/STEP/STL inspection; no engineering release", "input_identity": inputs,
          "projection_readiness": projection_readiness,
          "native_document": native.Name, "native_features": features, "valid_solid": True, "solid_count": 1,
          "native_volume_mm3": native_shape.Volume, "step_volume_mm3": neutral.Volume,
          "native_step_symmetric_volume_difference_mm3": conversion_difference,
          "measured_height_mm": bounds.ZLength, "measured_max_y_envelope_mm": bounds.YLength,
          "sampled_minimum_grip_diameter_mm": sampled_minimum_grip, "scallop_angular_spacings_deg": phase_spacings,
          "socket_sections": socket_sections, "socket_depth_transition_mm": {"empty_at": 9.999, "solid_at": 10.001},
          "roof_required_mm": 3, "roof_uncovered_volume_mm3": roof_uncovered_volume,
          "mesh": {"facets": facet_count, "vertices": len(vertices), "all_edges_two_facets": True, "signed_volume_mm3": signed_volume,
                   "sample_count": len(sample_distances), "maximum_sampled_deviation_mm": maximum_deviation, "samples": sample_distances,
                   "limitation": "64 uniformly indexed vertices and 64 facet centres; not a complete Hausdorff bound; STL units inferred from declared mm frame"},
          "drawing": {"document": name, "number": drawing_number, "views": [view.Name for view in views], "geometry_linked_dimensions": dimensions, "dimension_values_mm": {row["feature"]: row["value_mm"] for row in dimensions}, "linked_dimension_count": len(dimensions), "template": template.Template, "visual_review": "pending", "scope": "Functional digital inspection drawing, not a manufacturing release or standards-conformance claim", "preview": {"source": "inspection-drawing.svg", "source_sha256": hashlib.sha256((output / "inspection-drawing.svg").read_bytes()).hexdigest(), "path": "inspection-drawing.png", "sha256": hashlib.sha256((output / "inspection-drawing.png").read_bytes()).hexdigest(), "method": "FreeCAD QtSvg rasterization of exact native TechDraw export", "width": preview.width(), "height": preview.height()}},
          "engineering_acceptance": False, "physical_acceptance": False}
(output / "engineering-measurements.json").write_text(json.dumps(report, indent=2))
matrix = "# Focus wheel — exact digital inspection\n\nDigital review only; no manufacture release or physical acceptance.\n\n"
matrix += "| Requirement | Actual observation | Method and limit | Remaining scope |\n|---|---|---|---|\n"
matrix += f"| Envelope 38 max / height18 | Y span {bounds.YLength:.6f}; height {bounds.ZLength:.6f} mm | Native surface bounds, 1e-5 mm numeric comparison | Radial-envelope and manufactured accuracy review |\n"
matrix += f"| Six scallops / grip >=33 | 6 native cuts; sampled grip {sampled_minimum_grip:.6f} mm | 101 samples per section edge; angular spacing60 deg | Sampling is not a full extremum proof; glove handling untested |\n"
matrix += f"| Required D socket R3.2 / flat x=-2.4 / depth10 | {socket_observation_text(socket_sections)}; depth transition9.999..10.001 | STEP sections / point containment; accepted profile evaluates actual dimensions | Physical shaft fit untested |\n"
matrix += f"| Roof >=3 | Uncovered probe volume {roof_uncovered_volume:.9g} mm3 | Solid intersection of entire D-face extruded3mm above floor | Physical adhesion/porosity untested |\n"
matrix += f"| Native/STEP consistency | Symmetric volume difference {conversion_difference:.9g} mm3 | <=0.001mm3 numeric conversion criterion | Not a manufacturing tolerance |\n"
matrix += f"| Controlled STL | {facet_count} facets; closed edge adjacency; positive volume; sampled deviation {maximum_deviation:.9g} mm | 128 declared surface-distance samples, <=0.05mm | No complete Hausdorff or printed strength proof |\n"
matrix += "| PETG / supports / physical use | Not evaluated by this inspection step | Separate retained slice/profile/support evidence required | Fit gauge,0.15N.m torque,0..35C use/creep,glove and print tests remain planned |\n"
matrix += "\n## Drawing characteristics\n\nThese values are read from native geometry-linked dimensions. They are observations, not substitutes for the accepted requirement profile or manufacturing tolerances. The dimension text is not overridden.\n\n| Characteristic | Observed mm | Native view | Geometry references |\n|---|---:|---|---|\n"
matrix += "\n".join(f"| {item['feature']} | {item['value_mm']:.6g} | {item['view']} | {', '.join(item['references']) or 'complete projected extent'} |" for item in dimensions) + "\n"
matrix += """
## Physical inspection plan — proposed, not executed

Retain the inspected CAD revision, slice profile, build orientation, material lot,
machine settings and specimen identity. The responsible engineer must approve
sample counts, measurement uncertainty and test procedures before any release.
No physical fabrication or test is authorized by this digital report.

| Characteristic / original basis | Proposed method | Decision still required |
|---|---|---|
| Envelope <=38 mm; total height18 mm; hub rise2 mm | Measure across multiple orientations using calibrated calipers; measure rear datum A to hub top and body top. Record actual values and instrument uncertainty. | Manufacturing tolerances and sampling plan. The proposed +/-0.25 mm applies only to non-mating features and is not approved. |
| D shaft round6.00 / across-flat5.20; design clearance0.20 at round and flat | Inspect socket profile/depth with a suitable optical or sectioned trial specimen measurement and use the actual identified shaft or qualified D gauge. Record insertion force, play and removal. | Fit tolerances, acceptable insertion/removal force, backlash and gauge uncertainty. Do not infer fit from nominal CAD clearance. |
| Blind socket10 mm; roof>=3 mm | Depth gauge from datum A where accessible; section a dedicated trial specimen or use an approved internal-inspection method. | Destructive specimen allowance and suitable measurement method. Digital solid intersection alone cannot prove printed roof integrity. |
| Six scallops, grip>=33 mm, rounded edges, grip dots | Dimensional/visual inspection followed by gloved handling of a trial part; inspect after any support removal. | Glove type, handling protocol and acceptable snag/edge criteria. |
| Operating torque0.15 N.m and environment0..35 C | Instrumented shaft/knob test at the specified torque; inspect for slip, permanent deformation and cracking. Consider sustained loading and representative temperature exposure. | Fixture, hold time, cycles, dwell temperatures and acceptance criteria for creep and slip. No strength claim is supported yet. |
| PETG process and support effects | Review actual toolpaths and material/profile identity; record support contacts, removal access, surface damage and build orientation on the trial specimen. | Printer/process qualification and whether interface finishing is permitted. |

Human drawing review must also check view/section clarity, dimension placement,
datum interpretation and whether the package is sufficient for its intended use.
No ASME/ISO drawing-compliance or manufacturing-release claim is made here.
"""
matrix += "\n## Exact inputs\n\n" + "\n".join(f"- {role}: `{record['sha256']}` — {record['path']}" for role, record in inputs.items()) + "\n"
(output / "requirements-matrix.md").write_text(matrix)
print(json.dumps({"operation_status": "completed_digital_inspection", "measurements": str(output / "engineering-measurements.json"), "drawing": str(output / "inspection-drawing.pdf"), "engineering_acceptance": False}))
