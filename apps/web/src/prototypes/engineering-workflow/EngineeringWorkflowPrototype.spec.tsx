import { fireEvent, render, screen } from "@testing-library/react";
import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";

import { EngineeringWorkflowPrototype } from "./EngineeringWorkflowPrototype";

describe("EngineeringWorkflowPrototype", () => {
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
    render(<EngineeringWorkflowPrototype />);

    expect(
      screen.getByRole("heading", {
        name: "Drill-Bit Holder — Design to Fabrication",
      }),
    ).toBeInTheDocument();
    expect(screen.getByText("CP3A · Image upload")).toBeInTheDocument();
    expect(
      screen.getByTestId("react-flow-workflow-canvas"),
    ).toBeInTheDocument();
    const visualSlice = screen.getByTestId("engineering-workflow-visual-slice");
    expect(visualSlice).toHaveAttribute("data-visual-contract", "cp2a-1");
    expect(visualSlice).toHaveStyle({
      "--ewp-blue": "#159cff",
      "--ewp-purple": "#9b4dff",
      "--ewp-cyan": "#16c8c1",
      "--ewp-green": "#12c881",
      "--ewp-amber": "#ffb20b",
      "--ewp-red": "#ff4058",
    });
    const referenceImages = await screen.findByRole("button", {
      name: /Reference Images/,
    });
    expect(referenceImages).toBeInTheDocument();

    fireEvent.click(referenceImages);
    expect(
      await screen.findByText("Source material supplied by the designer."),
    ).toBeInTheDocument();
    const upload = screen.getByLabelText("Upload reference images");
    expect(upload).toHaveAttribute("accept", "image/*");
    expect(upload).toHaveAttribute("multiple");
    expect(
      screen.queryByRole("button", { name: /drill index tray/i }),
    ).not.toBeInTheDocument();
  });
});
