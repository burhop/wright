from __future__ import annotations

import json
import subprocess
import sys

import pytest

import wright
from wright.models import DisplayHandle, NativeGraph


pytestmark = pytest.mark.workspace_surfaces


@pytest.mark.parametrize("helper,kind", [("line", "line"), ("bar", "bar"), ("scatter", "scatter")])
def test_xy_graph_helpers_normalize_inputs_and_accessibility(
    monkeypatch: pytest.MonkeyPatch, helper: str, kind: str
) -> None:
    captured = {}
    expected = DisplayHandle(
        surface_id="surface-1", display_id="loads", revision=1, title="Loads"
    )

    def fake_display(value, **options):
        captured.update(value=value, options=options)
        return expected

    monkeypatch.setattr("wright.graphs.display", fake_display)
    result = getattr(wright, helper)(
        x=(0, 1, 2),
        y=[10, 12, 15],
        title="Measured load",
        x_label="Time (s)",
        y_label="Load (N)",
        description="Load increases from 10 N to 15 N over two seconds.",
        display_id="loads",
    )

    assert result is expected
    graph = captured["value"]
    assert isinstance(graph, NativeGraph)
    assert graph.kind == kind
    assert graph.x == (0.0, 1.0, 2.0)
    assert graph.y == (10.0, 12.0, 15.0)
    assert graph.title == "Measured load"
    assert graph.x_label == "Time (s)"
    assert graph.y_label == "Load (N)"
    assert captured["options"] == {
        "title": "Measured load",
        "description": "Load increases from 10 N to 15 N over two seconds.",
        "display_id": "loads",
        "durability": "durable",
    }


def test_histogram_computes_bounded_deterministic_bins(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = {}
    monkeypatch.setattr(
        "wright.graphs.display",
        lambda value, **options: captured.update(value=value, options=options),
    )
    wright.histogram(
        values=[0, 1, 1, 2, 3, 5],
        bins=3,
        title="Distribution",
        x_label="Value",
        y_label="Count",
        description="Six values distributed across three bins.",
    )
    graph = captured["value"]
    assert graph.kind == "histogram"
    assert graph.values == (0.0, 1.0, 1.0, 2.0, 3.0, 5.0)
    assert graph.bins == 3


@pytest.mark.parametrize(
    "call,match",
    [
        (
            lambda: wright.line(
                x=[1], y=[1, 2], title="x", x_label="x", y_label="y", description="d"
            ),
            "same length",
        ),
        (
            lambda: wright.scatter(
                x=[1], y=[float("nan")], title="x", x_label="x", y_label="y", description="d"
            ),
            "finite",
        ),
        (
            lambda: wright.bar(
                x=[], y=[], title="x", x_label="x", y_label="y", description="d"
            ),
            "at least one",
        ),
        (
            lambda: wright.histogram(
                values=[1], bins=0, title="x", x_label="x", y_label="y", description="d"
            ),
            "bins",
        ),
    ],
)
def test_graph_helpers_reject_ambiguous_or_unsafe_inputs(call, match: str) -> None:
    with pytest.raises((TypeError, ValueError), match=match):
        call()


def test_import_is_side_effect_free_and_does_not_load_optional_graph_packages() -> None:
    code = """
import json, sys
before = set(sys.modules)
import wright
after = set(sys.modules)
blocked = ['matplotlib', 'plotly', 'pandas', 'PIL', 'requests', 'httpx']
print(json.dumps({name: name in (after-before) for name in blocked}))
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(completed.stdout) == {
        "matplotlib": False,
        "plotly": False,
        "pandas": False,
        "PIL": False,
        "requests": False,
        "httpx": False,
    }
