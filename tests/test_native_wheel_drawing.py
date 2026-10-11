"""Drawing selection/profile unit checks; actual TechDraw evidence is separate."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from core.process_validation import ValidationProfile

ASSET = Path(__file__).parents[1] / "examples/process-interfaces/printed-replacement-part/wheel-inspection-operation.py"


def helpers():
    tree = ast.parse(ASSET.read_text(encoding="utf-8"))
    body = [node for node in tree.body if isinstance(node, ast.FunctionDef)
            and node.name in {"drawing_edges", "select_drawing_edge", "near", "await_drawing_projection"}]
    namespace = {}
    exec(compile(ast.Module(body=body, type_ignores=[]), str(ASSET), "exec"), namespace)
    return namespace


def projection_clock():
    clock = SimpleNamespace(now=0, delay=0)

    class Timer:
        def start(self):
            self.started = clock.now

        def elapsed(self):
            return clock.now - self.started

    class Loop:
        def quit(self):
            pass

        def exec_(self):
            clock.now += clock.delay

    def single_shot(delay, callback):
        clock.delay = delay

    functions = helpers()
    functions["QtCore"] = SimpleNamespace(QElapsedTimer=Timer, QEventLoop=Loop,
                                          QTimer=SimpleNamespace(singleShot=single_shot))

    def view(name, available_at):
        def edge(index):
            assert index == 0
            if clock.now < available_at:
                raise ValueError("Wrong edge index")
            return object()
        return SimpleNamespace(Name=name, getEdgeByIndex=edge)

    return functions["await_drawing_projection"], view, clock


def test_projection_wait_returns_immediately_when_all_views_are_available():
    wait, view, clock = projection_clock()
    result = wait([view("Front", 0), view("Section", 0)])
    assert result["views"] == ["Front", "Section"]
    assert result["polls"] == 1 and clock.now == 0


def test_projection_wait_services_events_until_the_last_view_is_available():
    wait, view, clock = projection_clock()
    result = wait([view("Front", 100), view("Section", 2700)])
    assert result["elapsed_ms"] == 2700 and clock.now == 2700
    assert result["polls"] == 28


def test_projection_wait_names_only_unavailable_views_and_keeps_its_deadline():
    wait, view, clock = projection_clock()
    with pytest.raises(AssertionError, match="bounded wait: Section$"):
        wait([view("Front", 100), view("Section", 900)], timeout_ms=250)
    assert clock.now == 250


def test_projection_wait_does_not_mask_other_native_errors():
    wait, _, clock = projection_clock()

    def error(index):
        raise RuntimeError("Invalid native shape")

    with pytest.raises(RuntimeError, match="Invalid native shape"):
        wait([SimpleNamespace(Name="Broken", getEdgeByIndex=error)])
    assert clock.now == 0


def test_selection_retains_real_reference_indices_including_hidden_geometry():
    functions = helpers()

    class View:
        def getEdgeByIndex(self, index):
            if index >= 3:
                raise ValueError("Wrong edge index")
            return ("visible", "hidden", "socket")[index]

        def getVisibleEdges(self):
            raise AssertionError("Visible-list positions are not native reference indices")

    edges = functions["drawing_edges"](View())
    assert functions["select_drawing_edge"](edges, lambda edge: edge == "socket", "socket") == (2, "socket")


def test_unavailable_feature_is_a_diagnostic_not_a_guessed_reference():
    functions = helpers()
    with pytest.raises(AssertionError, match="Drawing feature unavailable: socket"):
        functions["select_drawing_edge"]([(7, "another feature")], lambda edge: edge == "socket", "socket")


def test_empty_or_unbounded_projection_fails_explicitly():
    functions = helpers()

    class Empty:
        def getEdgeByIndex(self, index):
            raise ValueError("Wrong edge index")

    class Unbounded:
        def getEdgeByIndex(self, index):
            return object()

    with pytest.raises(AssertionError, match="unavailable"):
        functions["drawing_edges"](Empty())
    with pytest.raises(AssertionError, match="qualified inspection scope"):
        functions["drawing_edges"](Unbounded())


def test_profile_requires_named_functional_dimensions_not_only_a_count():
    value = json.loads(ASSET.with_name("native-inspection-profile.json").read_text())
    profile = ValidationProfile.model_validate(value)
    assert profile.version == "2"
    checks = {check["selector"]: check["constraint"] for check in value["checks"]}
    for name, target in {"Envelope": 38, "OverallHeight": 18, "HubHeight": 2,
                         "SocketRadius": 3.2, "SocketDepth": 10, "SocketAcrossFlat": 5.6,
                         "ExposedRound": 1}.items():
        assert checks["/drawing/dimension_values_mm/" + name] == {
            "operator": "within", "target": target, "tolerance": 1e-5}
    assert checks["/drawing/dimension_values_mm/SocketRoofAtAxis"]["minimum"] == 3
    assert checks["/drawing/dimension_values_mm/GripAtSection"]["minimum"] == 33
    assert checks["/socket_sections/1/flat_x_mm"]["target"] == -2.4
