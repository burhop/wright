from __future__ import annotations

import math

import pytest

from wright.adapters import AdapterLimits, adapt_display_value
from wright.models import NativeGraph


pytestmark = pytest.mark.workspace_surfaces


class MatplotlibLike:
    def savefig(self, stream, *, format, **_kwargs):
        assert format == "png"
        stream.write(b"\x89PNG\r\n\x1a\nfigure")


class PlotlyLike:
    def to_plotly_json(self):
        return {"data": [{"x": [1, 2], "y": [3, 4]}], "layout": {"title": "Loads"}}


class PandasLike:
    columns = ["time", "load"]

    def to_dict(self, orient):
        assert orient == "split"
        return {"columns": self.columns, "index": [0, 1], "data": [[0, 10], [1, 12]]}


class PilLike:
    mode = "RGB"
    size = (2, 2)

    def save(self, stream, *, format):
        assert format == "PNG"
        stream.write(b"\x89PNG\r\n\x1a\nimage")


class MimeBundleLike:
    def _repr_mimebundle_(self, include=None, exclude=None):
        del include, exclude
        return {
            "text/html": "<strong>safe</strong><script>bad()</script>",
            "text/plain": "safe fallback",
            "application/javascript": "bad()",
        }


@pytest.mark.parametrize(
    "value,media_type,encoding",
    [
        (MatplotlibLike(), "image/png", "base64"),
        (PlotlyLike(), "application/vnd.plotly.v1+json", "json"),
        (PandasLike(), "application/vnd.wright.table+json", "json"),
        (PilLike(), "image/png", "base64"),
        ("<svg role='img'></svg>", "image/svg+xml", "utf-8"),
    ],
)
def test_bounded_optional_value_adapters_are_duck_typed_and_lazy(
    value, media_type: str, encoding: str
) -> None:
    representations = adapt_display_value(value)
    assert representations[0].media_type == media_type
    assert representations[0].encoding == encoding


def test_native_graph_precedes_generic_mime_and_text_fallbacks() -> None:
    graph = NativeGraph(
        kind="line",
        x=(0.0, 1.0),
        y=(2.0, 3.0),
        title="Loads",
        x_label="Time",
        y_label="Load",
        description="Load rises.",
    )
    representations = adapt_display_value(graph)
    assert representations[0].media_type == "application/vnd.plotly.v1+json"
    assert representations[-1].media_type == "text/plain"


def test_repr_mimebundle_is_allowlisted_and_html_requires_explicit_active_mode() -> None:
    passive = adapt_display_value(MimeBundleLike())
    assert [item.media_type for item in passive] == ["text/html", "text/plain"]
    assert all(item.active_html is False for item in passive)
    assert "application/javascript" not in {item.media_type for item in passive}
    active = adapt_display_value(MimeBundleLike(), active_html=True)
    assert active[0].media_type == "text/html"
    assert active[0].active_html is True


def test_non_finite_and_oversized_adapter_results_fail_before_transport() -> None:
    class NonFinite:
        def to_plotly_json(self):
            return {"data": [{"y": [math.inf]}]}

    with pytest.raises(ValueError, match="finite"):
        adapt_display_value(NonFinite())
    with pytest.raises(ValueError, match="points"):
        adapt_display_value(
            NativeGraph(
                kind="line",
                x=(0.0, 1.0),
                y=(2.0, 3.0),
                title="Loads",
                x_label="Time",
                y_label="Load",
                description="Load rises.",
            ),
            limits=AdapterLimits(maximum_graph_points=1),
        )
    with pytest.raises(ValueError, match="bytes"):
        adapt_display_value("too large", limits=AdapterLimits(maximum_encoded_bytes=2))


def test_scalar_fallback_does_not_require_optional_dependencies() -> None:
    representation = adapt_display_value({"status": "ok"})[0]
    assert representation.media_type == "text/plain"
    assert "ok" in representation.data
