import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { PlotlyRenderer, type PlotlyModule } from "./plotly-renderer";

const representation = {
  mediaType: "application/vnd.plotly.v1+json" as const,
  encoding: "json" as const,
  data: {
    data: [{ x: [0, 1], y: [10, 12], type: "scatter" }],
    layout: { title: "Loads" },
  },
};

describe("PlotlyRenderer", () => {
  it("loads bundled Plotly lazily, renders, and updates the same host", async () => {
    const react = vi.fn().mockResolvedValue(undefined);
    const purge = vi.fn();
    const loadPlotly = vi.fn().mockResolvedValue({ react, purge } satisfies PlotlyModule);
    const { rerender } = render(
      <PlotlyRenderer
        representation={representation}
        description="Load rises from 10 N to 12 N."
        fallback={<table aria-label="Load data"><tbody><tr><td>10</td></tr></tbody></table>}
        loadPlotly={loadPlotly}
      />,
    );
    expect(screen.getByRole("table", { name: "Load data" })).toBeVisible();
    await waitFor(() => expect(react).toHaveBeenCalledTimes(1));
    const host = screen.getByRole("img", { name: "Load rises from 10 N to 12 N." });
    expect(react.mock.calls[0][0]).toBe(host);
    expect(host).toHaveStyle({ width: "100%", minHeight: "320px" });

    rerender(
      <PlotlyRenderer
        representation={{
          ...representation,
          data: { ...representation.data, data: [{ x: [0, 1], y: [11, 15] }] },
        }}
        description="Updated loads"
        fallback={<span>Updated fallback</span>}
        loadPlotly={loadPlotly}
      />,
    );
    await waitFor(() => expect(react).toHaveBeenCalledTimes(2));
    expect(loadPlotly).toHaveBeenCalledTimes(1);
    expect(react.mock.calls[1][0]).toBe(host);
  });

  it("keeps an accessible fallback when Plotly fails", async () => {
    const loadPlotly = vi.fn().mockRejectedValue(new Error("renderer failed"));
    render(
      <PlotlyRenderer
        representation={representation}
        description="Loads"
        fallback={<p>Load values: 10, 12</p>}
        loadPlotly={loadPlotly}
      />,
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(/could not render/i);
    expect(screen.getByText("Load values: 10, 12")).toBeVisible();
  });

  it("rejects malformed or non-finite plot data before loading Plotly", () => {
    const loadPlotly = vi.fn();
    render(
      <PlotlyRenderer
        representation={{
          ...representation,
          data: { data: [{ y: [Number.NaN] }] },
        }}
        description="Invalid"
        fallback={<p>Invalid plot data</p>}
        loadPlotly={loadPlotly}
      />,
    );
    expect(screen.getByRole("alert")).toHaveTextContent(/invalid/i);
    expect(loadPlotly).not.toHaveBeenCalled();
  });
});
