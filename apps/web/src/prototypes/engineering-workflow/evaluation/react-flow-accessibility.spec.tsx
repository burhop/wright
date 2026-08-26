import axe from "axe-core";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterAll, beforeAll, describe, expect, it, vi } from "vitest";

import { EngineeringWorkflowPrototype } from "../EngineeringWorkflowPrototype";

describe("React Flow workflow accessibility", () => {
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

  it("exposes phases and blocks through semantic names and keyboard selection", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter>
        <EngineeringWorkflowPrototype />
      </MemoryRouter>,
    );

    const phaseSummary = await screen.findByRole("region", {
      name: "Workflow phase summary",
    });
    expect(
      within(phaseSummary).getByText(
        /Turn needs and context into an accepted design\./,
      ),
    ).toBeInTheDocument();

    const analysisResults = await screen.findByRole("button", {
      name: "Artifact L. Analysis Results",
    });
    analysisResults.focus();
    expect(analysisResults).toHaveFocus();
    await user.keyboard("{Enter}");

    expect(
      within(screen.getByLabelText("Block properties")).getByText(
        "L. Analysis Results",
      ),
    ).toBeVisible();
  });

  it("has no axe violations detectable in the component-test environment", async () => {
    const { container } = render(
      <MemoryRouter>
        <EngineeringWorkflowPrototype />
      </MemoryRouter>,
    );

    await screen.findByRole("button", {
      name: "Input A. Reference Images",
    });
    const result = await axe.run(container, {
      rules: {
        "color-contrast": { enabled: false },
      },
    });

    expect(
      result.violations.map(({ id, impact, nodes }) => ({
        id,
        impact,
        targets: nodes.map(({ target }) => target),
      })),
    ).toEqual([]);
  });
});
