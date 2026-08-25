import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { EngineeringWorkflowVisualSlice } from "./EngineeringWorkflowVisualSlice";

describe("Reference Images CP3A editor", () => {
  it("selects, reorders, removes, undoes, redoes, and discloses local-only state", async () => {
    const user = userEvent.setup();
    render(<EngineeringWorkflowVisualSlice />);

    await user.click(
      screen.getByRole("button", { name: "Input A. Reference Images" }),
    );

    const editor = screen.getByRole("region", { name: "Reference images" });
    expect(within(editor).getByText("No images selected")).toBeVisible();
    expect(within(editor).getByRole("button", { name: "Undo" })).toBeDisabled();

    await user.click(
      within(editor).getByRole("button", {
        name: "Add Angled drill index tray",
      }),
    );
    await user.click(
      within(editor).getByRole("button", {
        name: "Add Wall-mounted bit rack",
      }),
    );

    expect(within(editor).getByText("2 images selected")).toBeVisible();
    expect(screen.getByLabelText("2 selected reference images")).toBeVisible();
    expect(screen.getByText("2 selected · session only")).toBeVisible();

    await user.click(
      within(editor).getByRole("button", {
        name: "Move Wall-mounted bit rack earlier",
      }),
    );
    const selectedList = within(editor).getByRole("list", {
      name: "Selected reference images",
    });
    expect(
      within(selectedList)
        .getAllByRole("img")
        .map((image) => image.getAttribute("alt")),
    ).toEqual([
      "Schematic of a wall-mounted drill-bit rack",
      "Schematic of an angled sheet-metal drill index tray",
    ]);

    await user.click(
      within(editor).getByRole("button", {
        name: "Remove Angled drill index tray",
      }),
    );
    expect(within(editor).getByText("1 image selected")).toBeVisible();

    await user.click(within(editor).getByRole("button", { name: "Undo" }));
    expect(within(editor).getByText("2 images selected")).toBeVisible();
    await user.click(within(editor).getByRole("button", { name: "Redo" }));
    expect(within(editor).getByText("1 image selected")).toBeVisible();

    await user.click(screen.getByRole("tab", { name: "Evidence" }));
    const evidencePanel = screen.getByRole("tabpanel", { name: "Evidence" });
    expect(
      within(evidencePanel).getByText("Local CP3A draft · session only"),
    ).toBeVisible();
    expect(
      within(evidencePanel).getByText("1 image selected · not persisted"),
    ).toBeVisible();
  });
});
