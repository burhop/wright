import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { EngineeringWorkflowVisualSlice } from "./EngineeringWorkflowVisualSlice";

describe("Design Input CP3B editor", () => {
  it("applies a prompt and attaches, removes, undoes, and redoes documents", async () => {
    const user = userEvent.setup();
    render(<EngineeringWorkflowVisualSlice />);

    await user.click(
      screen.getByRole("button", { name: "Input B. Design Input" }),
    );

    const editor = screen.getByRole("region", { name: "Design input" });
    const prompt = within(editor).getByLabelText("Design prompt");
    const promptText =
      "Create a compact device that is safe to handle and easy to manufacture.";
    await user.type(prompt, promptText);
    expect(within(editor).getByText(/changes not applied/)).toBeVisible();

    await user.click(
      within(editor).getByRole("button", { name: "Apply prompt" }),
    );
    expect(within(editor).getByText(/characters · applied/)).toBeVisible();
    expect(screen.getByText("Draft · session only")).toBeVisible();

    const fileInput = within(editor).getByLabelText("Attach design documents");
    expect(fileInput).toHaveAttribute(
      "accept",
      ".txt,.md,.markdown,.csv,.json,.yaml,.yml,.xml,.rtf,.pdf,.doc,.docx",
    );
    expect(fileInput).toHaveAttribute("multiple");

    const brief = new File(
      ["Use corrosion-resistant material.\nKeep assembly steps low."],
      "design-brief.md",
      { type: "text/markdown" },
    );
    const requirements = new File(["pdf"], "requirements.pdf", {
      type: "application/pdf",
    });
    await user.upload(fileInput, [brief, requirements]);

    expect(await within(editor).findByText("2 documents")).toBeVisible();
    expect(within(editor).getByText("design-brief.md")).toBeVisible();
    expect(within(editor).getByText("requirements.pdf")).toBeVisible();
    expect(
      within(editor).getByText("Use corrosion-resistant material.", {
        exact: false,
      }),
    ).toBeVisible();
    expect(
      within(editor).getByText(
        "Attached · parser required in a later checkpoint",
      ),
    ).toBeVisible();

    await user.click(
      within(editor).getByRole("button", {
        name: "Remove requirements.pdf",
      }),
    );
    expect(within(editor).getByText("1 document")).toBeVisible();
    await user.click(within(editor).getByRole("button", { name: "Undo" }));
    expect(within(editor).getByText("2 documents")).toBeVisible();
    await user.click(within(editor).getByRole("button", { name: "Redo" }));
    expect(within(editor).getByText("1 document")).toBeVisible();

    await user.click(screen.getByRole("tab", { name: "Evidence" }));
    const evidencePanel = screen.getByRole("tabpanel", { name: "Evidence" });
    expect(
      within(evidencePanel).getByText("Local CP3B draft · session only"),
    ).toBeVisible();
    expect(
      within(evidencePanel).getByText(
        `${promptText.length} prompt characters · 1 document attached · not persisted`,
      ),
    ).toBeVisible();
  });

  it("keeps extraction, reuse, downstream AI, and persistence boundaries explicit", async () => {
    const user = userEvent.setup();
    render(<EngineeringWorkflowVisualSlice />);

    await user.click(
      screen.getByRole("button", { name: "Input B. Design Input" }),
    );

    const editor = screen.getByRole("region", { name: "Design input" });
    expect(
      within(editor).getByText(
        "Text formats show a bounded local preview. PDF and Word extraction, reusable workspace sources, and downstream AI use come later.",
      ),
    ).toBeVisible();
    expect(
      within(editor).getByText(
        "No documents attached. A prompt, documents, or both can feed later workflow steps.",
      ),
    ).toBeVisible();
    expect(screen.getByText("No design input")).toBeVisible();
  });
});
