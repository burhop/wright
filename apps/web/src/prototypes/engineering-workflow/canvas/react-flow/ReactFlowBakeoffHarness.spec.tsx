import { fireEvent, render, screen } from "@testing-library/react";
import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";

import { ReactFlowBakeoffHarness } from "./ReactFlowBakeoffHarness";

describe("ReactFlowBakeoffHarness", () => {
  const originalGetBoundingClientRect =
    HTMLElement.prototype.getBoundingClientRect;

  beforeAll(() => {
    class ResizeObserverMock {
      private readonly callback: ResizeObserverCallback;

      constructor(callback: ResizeObserverCallback) {
        this.callback = callback;
      }

      observe(target: Element) {
        this.callback(
          [
            {
              target,
              contentRect: target.getBoundingClientRect(),
            } as ResizeObserverEntry,
          ],
          this as unknown as ResizeObserver,
        );
      }

      unobserve() {}
      disconnect() {}
    }

    vi.stubGlobal("ResizeObserver", ResizeObserverMock);
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
    render(<ReactFlowBakeoffHarness />);

    expect(
      screen.getByRole("heading", {
        name: "Drill-Bit Holder — Design to Fabrication",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("CP1B · React Flow")).toBeInTheDocument();
    expect(screen.getByTestId("react-flow-bakeoff-canvas")).toBeInTheDocument();
    const referenceImages = await screen.findByRole("button", {
      name: /Reference Images/,
    });
    expect(referenceImages).toBeInTheDocument();

    fireEvent.click(referenceImages);
    expect(
      await screen.findByText("Source material supplied by the designer."),
    ).toBeInTheDocument();
  });
});
