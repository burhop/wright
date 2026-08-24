import { fireEvent, render, screen } from "@testing-library/react";
import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";

import { ReteBakeoffHarness } from "./ReteBakeoffHarness";

describe("ReteBakeoffHarness", () => {
  const originalGetBoundingClientRect =
    HTMLElement.prototype.getBoundingClientRect;

  beforeAll(() => {
    vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => {
      callback(performance.now());
      return 1;
    });
    vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue({
      x: 0,
      y: 0,
      width: 1200,
      height: 800,
      top: 0,
      right: 1200,
      bottom: 800,
      left: 0,
      toJSON: () => ({}),
    });
  });

  afterAll(() => {
    vi.unstubAllGlobals();
    HTMLElement.prototype.getBoundingClientRect = originalGetBoundingClientRect;
    vi.restoreAllMocks();
  });

  it("reuses the approved shell around a Wright-owned read-only projection", async () => {
    render(<ReteBakeoffHarness />);

    expect(
      screen.getByRole("heading", {
        name: "Drill-Bit Holder — Design to Fabrication",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("CP1B · Rete.js")).toBeInTheDocument();
    expect(screen.getByTestId("rete-bakeoff-canvas")).toBeInTheDocument();
    expect(
      screen.getByRole("region", {
        name: "Define phase: Turn needs and context into an accepted design.",
      }),
    ).toBeInTheDocument();
    expect(
      await screen.findByText(
        "Read-only CP1B candidate · Wright model remains canonical",
      ),
    ).toBeInTheDocument();

    const referenceImages = await screen.findByRole("button", {
      name: /Reference Images/,
    });
    fireEvent.click(referenceImages);
    expect(
      await screen.findByText("Source material supplied by the designer."),
    ).toBeInTheDocument();
  });
});
