"""Execute the documented Python entrypoint seam, without importing CAD."""
import ast
from enum import Enum, auto
import inspect
import hashlib
import os
from pathlib import Path
from typing import Any

import pytest

from scripts.agentcad_source_contract import entrypoint_probe, runner_context

EXCERPT = Path(__file__).parent/"fixtures/agentcad-entrypoint-context.txt"


def test_real_runner_context_reproduces_main_guard_skip_and_module_scope_capture():
    context = runner_context(EXCERPT.read_text(encoding="utf-8"))
    old = entrypoint_probe(context,entrypoint="if __name__ == '__main__':\n    main()\n")
    assert old == {"captured_count":0,"original_marker_captured":False}
    fixed = entrypoint_probe(context)
    assert fixed == {"captured_count":1,"original_marker_captured":True}


def test_module_scope_requires_real_injected_capture_instead_of_stub():
    context = runner_context(EXCERPT.read_text(encoding="utf-8"))
    with pytest.raises(RuntimeError,match="injected show_object is required"):
        entrypoint_probe(context,include_capture=False)


def test_guidance_requires_validator_visible_direct_capture_call():
    from scripts.agentcad_source_contract import GUIDANCE

    assert "show_object(actual_shape)" in GUIDANCE
    assert "do not assign it to an alias" in GUIDANCE
    assert "never call the abstract Shape.cast" in GUIDANCE
    assert "Compound.cast" in GUIDANCE
    assert "Solid.cast" in GUIDANCE


def test_rotation_guidance_binds_selected_native_signature_without_running_cad():
    from scripts.agentcad_source_contract import GUIDANCE, ROTATION_EXAMPLE

    source = EXCERPT.with_name("build123d-shape-rotate-context.txt").read_text(encoding="utf-8")
    method = ast.parse(source).body[0]
    # Preserve the selected native method's positional requirements, without
    # importing build123d or substituting a fake geometric implementation.
    signature = inspect.Signature([
        inspect.Parameter(argument.arg, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        for argument in method.args.args
    ])
    failed_call = ast.parse("shape.rotate((0, 0, 58))", mode="eval").body
    with pytest.raises(TypeError, match="angle"):
        signature.bind(object(), *failed_call.args)
    call = ast.parse(ROTATION_EXAMPLE, mode="eval").body
    bound = signature.bind(object(), *call.args)
    axis = bound.arguments["axis"]
    assert isinstance(axis, ast.Attribute) and axis.value.id == "Axis" and axis.attr == "Z"
    assert isinstance(bound.arguments["angle"], ast.Constant)
    assert "degrees" in ast.get_docstring(method)
    assert ROTATION_EXAMPLE in GUIDANCE and "import Axis" in GUIDANCE


def test_alignment_guidance_uses_selected_enum_and_tuple_normalization_without_cad():
    from scripts.agentcad_source_contract import ALIGNMENT_EXAMPLE, GUIDANCE

    source = EXCERPT.with_name("build123d-align-context.txt").read_text(encoding="utf-8")
    namespace = {"Enum": Enum, "auto": auto, "Any": Any}
    # Execute only the exact standard-library enum and normalization excerpts,
    # not build123d imports, constructors or any substitute geometry.
    exec(compile(source, "<build123d-alignment-contract>", "exec"), namespace)
    align, tuplify = namespace["Align"], namespace["tuplify"]
    for invalid in ("center", ("center", "center", "min"), (align.CENTER, "min", align.MAX)):
        with pytest.raises(ValueError, match="not a valid Align"):
            tuple(map(align, tuplify(invalid, 3)))
    for expression, dimensions in (("Align.CENTER", 3), ("(Align.CENTER, Align.CENTER)", 2), (ALIGNMENT_EXAMPLE, 3)):
        value = eval(compile(ast.parse(expression, mode="eval"), "<documented-alignment>", "eval"), {"Align": align})
        normalized = tuple(map(align, tuplify(value, dimensions)))
        assert len(normalized) == dimensions and all(isinstance(member, align) for member in normalized)
        assert expression in GUIDANCE
    assert normalized == (align.CENTER, align.CENTER, align.MIN)


def test_disconnected_shape_guidance_normalizes_with_positional_compound():
    from scripts.agentcad_source_contract import (
        COMPOUND_NORMALIZATION_EXAMPLE,
        GUIDANCE,
        VALIDITY_EXAMPLE,
    )

    assignment = ast.parse(COMPOUND_NORMALIZATION_EXAMPLE).body[0]
    assert isinstance(assignment, ast.Assign)
    expression = assignment.value
    assert isinstance(expression, ast.IfExp)
    assert isinstance(expression.body, ast.Call)
    assert expression.body.func.id == "Compound"
    assert len(expression.body.args) == 1 and not expression.body.keywords
    validity = ast.parse(VALIDITY_EXAMPLE, mode="eval").body
    assert isinstance(validity, ast.Attribute) and validity.attr == "is_valid"
    assert COMPOUND_NORMALIZATION_EXAMPLE in GUIDANCE
    assert "Compound([*base.solids(), *lid.solids()])" in GUIDANCE
    assert "never call shape.is_valid()" in GUIDANCE


def test_rounded_rectangle_guidance_uses_pinned_build123d_symbol():
    from scripts.agentcad_source_contract import GUIDANCE, ROUNDED_RECTANGLE_EXAMPLE

    assignment = ast.parse(ROUNDED_RECTANGLE_EXAMPLE).body[0]
    assert isinstance(assignment, ast.Assign)
    call = assignment.value
    assert isinstance(call, ast.Call) and call.func.id == "RectangleRounded"
    assert [argument.id for argument in call.args] == ["width", "depth", "radius"]
    assert len(call.keywords) == 1 and call.keywords[0].arg == "align"
    assert "RoundedRectangle is unavailable" in GUIDANCE
    assert "Import RectangleRounded" in GUIDANCE
    assert ROUNDED_RECTANGLE_EXAMPLE in GUIDANCE


def test_selected_runner_placeholder_cannot_supply_source_hash_but_explicit_path_can(tmp_path, monkeypatch):
    from scripts.agentcad_source_contract import GUIDANCE

    tree = ast.parse(EXCERPT.with_name("agentcad-script-filename-context.txt").read_text(encoding="utf-8"))
    function, invocation = tree.body
    defaults = [inspect.Parameter.empty, *[ast.literal_eval(node) for node in function.args.defaults]]
    signature = inspect.Signature([
        inspect.Parameter(arg.arg, inspect.Parameter.POSITIONAL_OR_KEYWORD, default=default)
        for arg, default in zip(function.args.args, defaults)
    ])
    bound = signature.bind(*invocation.value.args)
    bound.apply_defaults()
    assert bound.arguments["filename"] == "<script>"
    declaration = function.body[0].value
    assert declaration.keys[0].value == "__file__" and declaration.values[0].id == "filename"
    project = tmp_path / "agentcad-project"
    project.mkdir()
    staged_source = tmp_path / "jig-source.py"
    staged_source.write_bytes(b"# immutable staged source for a path-contract unit test\n")
    monkeypatch.chdir(project)
    environment = {"__file__": bound.arguments["filename"], "os": os}
    # Exact failing generated statement; no geometry or source body is run.
    exec("source_path = os.path.abspath(__file__)", environment)
    bad_path = Path(environment["source_path"])
    assert bad_path == project / "<script>"
    with pytest.raises(OSError):
        bad_path.read_bytes()
    exec(f"SOURCE_PATH = {str(staged_source)!r}", environment)
    assert Path(environment["SOURCE_PATH"]).read_bytes() == staged_source.read_bytes()
    assert hashlib.sha256(Path(environment["SOURCE_PATH"]).read_bytes()).hexdigest() == hashlib.sha256(staged_source.read_bytes()).hexdigest()
    assert "__file__='<script>'" in GUIDANCE and "SOURCE_PATH literal" in GUIDANCE


@pytest.mark.parametrize("change",["capture","execution_globals"])
def test_unknown_runner_contract_is_rejected_before_source_guidance_is_claimed(change):
    source = EXCERPT.read_text(encoding="utf-8")
    if change == "capture":
        source = source.replace('"show_object": show_object','"show_object": unsupported_capture')
    else:
        source = source.replace('exec(code, script_globals)','exec(code, other_globals)')
    with pytest.raises(ValueError):
        runner_context(source)
