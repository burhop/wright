import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { EngineeringWorkflowVisualSlice } from "./EngineeringWorkflowVisualSlice";

describe("EngineeringWorkflowVisualSlice deterministic review states", () => {
  it.each([
    { viewState: "loading" as const, title: "Preparing workflow preview" },
    { viewState: "empty" as const, title: "No workflow blocks yet" },
    { viewState: "error" as const, title: "Workflow preview unavailable" },
  ])("renders the $viewState state without changing the workflow", ({ viewState, title }) => {
    render(<EngineeringWorkflowVisualSlice viewState={viewState} />);

    const statePanel =
      viewState === "error"
        ? screen.getByRole("alert")
        : screen.getByRole("status");
    expect(within(statePanel).getByRole("heading", { name: title })).toBeVisible();
    expect(
      screen.getByRole("heading", {
        name: "Drill-Bit Holder — Design to Fabrication",
      }),
    ).toBeVisible();
  });

  it("shows deterministic evidence and the generic MCP execution boundary", async () => {
    const user = userEvent.setup();
    render(<EngineeringWorkflowVisualSlice />);

    await user.click(
      screen.getByRole("button", {
        name: "MCP action K. Run Bound MCP Tool",
      }),
    );
    await user.click(screen.getByRole("tab", { name: "Evidence" }));

    const evidencePanel = screen.getByRole("tabpanel", { name: "Evidence" });
    expect(within(evidencePanel).getByText("analysis-tool")).toBeVisible();
    expect(within(evidencePanel).getByText("Not executed")).toBeVisible();
    expect(
      within(evidencePanel).getByText(
        /Capability categories never dispatch runtime services/,
      ),
    ).toBeVisible();
  });
});
