import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { EngineeringWorkflowVisualSlice } from "./EngineeringWorkflowVisualSlice";

describe("EngineeringWorkflowVisualSlice", () => {
  it("renders the reference workflow with engineer-readable phases and roles", () => {
    render(<EngineeringWorkflowVisualSlice />);

    expect(screen.getByRole("heading", { name: "Define" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Verify" })).toBeVisible();
    expect(screen.getByRole("heading", { name: "Manufacture" })).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Input I. FEA Test Definition" }),
    ).toBeVisible();
    expect(
      screen.getByRole("button", {
        name: "MCP action K. Run Bound MCP Tool",
      }),
    ).toBeVisible();
    expect(
      screen.getByText("Fail · revise geometry / thickness"),
    ).toBeVisible();
  });

  it("updates the properties inspector when a workflow block is selected", async () => {
    const user = userEvent.setup();
    render(<EngineeringWorkflowVisualSlice />);

    await user.click(
      screen.getByRole("button", { name: "Artifact L. Analysis Results" }),
    );

    const inspector = screen.getByLabelText("Block properties");
    expect(within(inspector).getByText("L. Analysis Results")).toBeVisible();
    expect(
      within(inspector).getAllByText(
        "Stress, deflection, safety factor, and evidence.",
      ),
    ).toHaveLength(2);
  });

  it("opens a searchable capability library instead of a long fixed tool list", async () => {
    const user = userEvent.setup();
    render(<EngineeringWorkflowVisualSlice />);

    await user.click(
      screen.getByRole("button", { name: /browse capability library/i }),
    );

    const dialog = screen.getByRole("dialog", {
      name: "Engineering capability library",
    });
    expect(
      within(dialog).getByText("19", { selector: "strong" }),
    ).toBeVisible();
    await user.type(
      within(dialog).getByRole("textbox", { name: "Search capabilities" }),
      "CFD",
    );
    expect(
      within(dialog).getByRole("heading", {
        name: "Computational fluid dynamics",
      }),
    ).toBeVisible();
    expect(
      within(dialog).getByText("Generic MCP action template"),
    ).toBeVisible();
    expect(
      within(dialog).getByText("Discovery labels do not select runtime code"),
    ).toBeVisible();
  });
});
