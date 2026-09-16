"""Selected AgentCAD source-entrypoint contract; never runs CAD."""
import ast

ENTRYPOINT = "main()\n"
CAPTURE_GUARD = "if not callable(globals().get('show_object')):\n    raise RuntimeError('AgentCAD injected show_object is required')\n"
ROTATION_EXAMPLE = "shape.rotate(Axis.Z, 58.0)"
ALIGNMENT_EXAMPLE = "(Align.CENTER, Align.CENTER, Align.MIN)"
COMPOUND_NORMALIZATION_EXAMPLE = (
    "shape = Compound(shape) if isinstance(shape, list) else shape"
)
VALIDITY_EXAMPLE = "shape.is_valid"
ROUNDED_RECTANGLE_EXAMPLE = (
    "profile = RectangleRounded(width, depth, radius, "
    "align=(Align.CENTER, Align.CENTER))"
)
GUIDANCE = (
    "The pinned AgentCAD 0.6.0 build123d runner executes the source with __name__='__agentcad_script__', not '__main__'. "
    "If generation/inspection is in main(), invoke main() unconditionally at module scope after its definition; do not place all work behind if __name__ == '__main__'. "
    "Use the actual callable show_object injected by AgentCAD to capture real model results. Never redefine, import over, stub or suppress that callback; fail explicitly if the injected callback is missing. "
    "Call it directly with the literal form show_object(actual_shape); do not assign it to an alias such as injected_show_object because AgentCAD's source validator requires a direct show_object(...) call. "
    "In pinned build123d 0.10.0, never call the abstract Shape.cast class method: its abstract body returns None. For BRepFeat_SplitShape.Shape(), which returns a compound, import Compound and use Compound.cast(raw_result); use Solid.cast only for a known TopAbs_SOLID, or pass a valid raw TopoDS_Shape directly to show_object. Validate the concrete result before calling show_object(actual_shape). "
    "The source must actually execute exports/inspection and invoke the injected callback, not silently skip its body. "
    "AgentCAD's run command executes source text with __file__='<script>'; this is a diagnostic placeholder, not the staged script pathname. "
    "Never derive source, project, input or output paths from __file__, Path(__file__), os.path.abspath(__file__) or inspect.getfile; do not open or hash that placeholder. "
    "For source provenance, use the exact staged absolute script path supplied to AgentCAD run(script=...), stored as an explicit SOURCE_PATH literal, and hash those actual bytes without rewriting the source. "
    "Use the exact supplied absolute input/output paths. Path.cwd() refers to the explicit run(cwd=...) project directory, not the script's parent or workspace root; use project-relative paths only when resolved against that confirmed project directory. "
    "Do not guess alternate paths, substitute a source string's hash for a file hash, or suppress a missing-file error in lineage evidence. "
    "For the pinned build123d 0.10.0 Shape API, import Axis and call shape.rotate(axis, angle) with an explicit Axis and angle in degrees. "
    f"For example, {ROTATION_EXAMPLE} returns a rotated copy; assign or use that returned shape. "
    "Use Axis.X, Axis.Y or Axis.Z for origin-centered principal-axis rotations. Apply separate axis-and-angle rotations in the intended order when multiple rotations are needed. "
    "Never pass only an Euler tuple to Shape.rotate: shape.rotate((0, 0, 58)) is missing the required angle argument. "
    "Import Align from build123d and supply Align.MIN, Align.CENTER or Align.MAX enum members for alignment, never strings such as 'center', 'min' or 'max'. "
    f"For 3D primitives such as Box and Cylinder, use align={ALIGNMENT_EXAMPLE} for the X/Y/Z axes; "
    "for 2D sketch primitives use an X/Y pair such as align=(Align.CENTER, Align.CENTER). "
    "A single align=Align.CENTER is also valid where the primitive accepts uniform alignment. Preserve the reviewed datum placement when choosing these enum values. "
    "In the pinned build123d 0.10.0 runtime, the rounded 2D rectangle class is named RectangleRounded; RoundedRectangle is unavailable and must never be imported or called. "
    f"Import RectangleRounded from build123d and construct the profile with `{ROUNDED_RECTANGLE_EXAMPLE}`, then extrude that profile for a rounded prism. "
    "Boolean operations on disconnected build123d bodies can return a ShapeList, which is a list rather than one topology object. "
    f"Normalize every such result before validation, export or composition with `{COMPOUND_NORMALIZATION_EXAMPLE}`; Compound must receive the ShapeList as its positional object argument. "
    "When combining several possibly disconnected results, normalize each result first and compose their solids with a positional call such as Compound([*base.solids(), *lid.solids()]). "
    "Do not pass a ShapeList as one item in Compound(children=[...]); the children keyword is the anytree hierarchy and requires individual NodeMixin nodes. "
    f"In build123d 0.10.0 validity is the boolean property `{VALIDITY_EXAMPLE}`, not a method; never call shape.is_valid(). "
)


def runner_context(source):
    """Extract and verify the actual source-global/exec seam without imports."""
    tree = ast.parse(source)
    declarations = [node for node in ast.walk(tree) if isinstance(node,ast.AnnAssign)
        and isinstance(node.target,ast.Name) and node.target.id == "script_globals" and isinstance(node.value,ast.Dict)]
    if len(declarations) != 1:
        raise ValueError("Selected runner has an unknown script-global declaration")
    values = {key.value:value for key,value in zip(declarations[0].value.keys,declarations[0].value.values) if isinstance(key,ast.Constant)}
    if not isinstance(values.get("__name__"),ast.Constant) or not isinstance(values.get("show_object"),ast.Name) or values["show_object"].id != "show_object":
        raise ValueError("Selected runner does not expose the expected capture context")
    if not any(isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id == "exec"
        and len(node.args) == 2 and isinstance(node.args[1],ast.Name) and node.args[1].id == "script_globals" for node in ast.walk(tree)):
        raise ValueError("Selected runner does not execute with the declared globals")
    return {"__name__":values["__name__"].value,"capture_name":"show_object","declaration_line":declarations[0].lineno}


def entrypoint_probe(context, *, entrypoint=ENTRYPOINT, include_capture=True):
    """Pure Python observation: marker callbacks, no geometry/imports/files."""
    captured = []
    environment = {"__name__":context["__name__"]}
    marker = object()
    if include_capture:
        environment["show_object"] = captured.append
    environment["build_geometry"] = lambda: marker
    source = CAPTURE_GUARD+"def main():\n    show_object(build_geometry())\n"+entrypoint
    exec(compile(source,"<agentcad-entrypoint-contract>","exec"),environment)
    return {"captured_count":len(captured),"original_marker_captured":captured == [marker]}
