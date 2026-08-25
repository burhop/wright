import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { EngineeringWorkflowVisualSlice } from "./EngineeringWorkflowVisualSlice";

describe("Reference Images CP3A editor", () => {
  it("uploads, reorders, removes, undoes, and redoes arbitrary image files", async () => {
    const user = userEvent.setup();
    render(<EngineeringWorkflowVisualSlice />);

    await user.click(
      screen.getByRole("button", { name: "Input A. Reference Images" }),
    );

    const editor = screen.getByRole("region", { name: "Reference images" });
    expect(within(editor).getByText("No images selected")).toBeVisible();
    expect(within(editor).getByRole("button", { name: "Undo" })).toBeDisabled();

    const fileInput = within(editor).getByLabelText("Upload reference images");
    expect(fileInput).toHaveAttribute("accept", "image/*");
    expect(fileInput).toHaveAttribute("multiple");

    const thermalImage = new File(["thermal"], "thermal-camera.png", {
      type: "image/png",
    });
    const sitePhoto = new File(["site"], "site-survey.jpg", {
      type: "image/jpeg",
    });
    await user.upload(fileInput, [thermalImage, sitePhoto]);

    expect(await within(editor).findByText("2 images selected")).toBeVisible();
    expect(screen.getByLabelText("2 selected reference images")).toBeVisible();
    expect(screen.getByText("2 selected · session only")).toBeVisible();

    await user.click(
      within(editor).getByRole("button", {
        name: "Move site-survey.jpg earlier",
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
      "Uploaded reference image site-survey.jpg",
      "Uploaded reference image thermal-camera.png",
    ]);

    await user.click(
      within(editor).getByRole("button", {
        name: "Remove thermal-camera.png",
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

  it("shows a generic upload affordance with no predefined product choices", async () => {
    const user = userEvent.setup();
    render(<EngineeringWorkflowVisualSlice />);

    await user.click(
      screen.getByRole("button", { name: "Input A. Reference Images" }),
    );

    const editor = screen.getByRole("region", { name: "Reference images" });
    expect(
      within(editor).getByText(
        "Upload one or more photos or other image files. They remain in this browser tab and can be used as inputs by later workflow steps.",
      ),
    ).toBeVisible();
    expect(
      within(editor).getByLabelText("Upload reference images"),
    ).toBeInTheDocument();
    expect(within(editor).queryByText(/drill index/i)).not.toBeInTheDocument();
    expect(
      within(editor).queryByText("Available image inputs"),
    ).not.toBeInTheDocument();
  });
});
