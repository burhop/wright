import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { EngineeringWorkflowVisualSlice } from "./EngineeringWorkflowVisualSlice";

describe("Knowledge Lookup CP3C editor", () => {
  it("configures a lookup prompt and generic source scopes with history", async () => {
    const user = userEvent.setup();
    render(<EngineeringWorkflowVisualSlice />);

    await user.click(
      screen.getByRole("button", { name: "Input C. Knowledge Lookup" }),
    );

    const editor = screen.getByRole("region", { name: "Knowledge lookup" });
    expect(
      within(editor).getByText(
        "Add a lookup prompt and choose where Wright may search.",
      ),
    ).toBeVisible();

    const query = within(editor).getByLabelText("Knowledge lookup prompt");
    const queryText =
      "Find applicable company standards, preferred bolt sizes, and relevant prior designs.";
    await user.type(query, queryText);
    expect(within(editor).getByText(/changes not applied/)).toBeVisible();
    await user.click(
      within(editor).getByRole("button", { name: "Apply lookup prompt" }),
    );
    expect(
      within(editor).getByText("Choose at least one source scope."),
    ).toBeVisible();

    await user.click(
      within(editor).getByRole("checkbox", { name: /Workspace documents/ }),
    );
    await user.click(
      within(editor).getByRole("checkbox", { name: /Connected knowledge/ }),
    );

    expect(within(editor).getByText("2 sources")).toBeVisible();
    expect(
      within(editor).getByText(
        "Lookup draft configured. Retrieval has not run.",
      ),
    ).toBeVisible();
    expect(screen.getByText("Draft · retrieval not run")).toBeVisible();
    expect(screen.getByText("QUERY + 2 SOURCES")).toBeVisible();

    await user.click(within(editor).getByRole("button", { name: "Undo" }));
    expect(within(editor).getByText("1 source")).toBeVisible();
    await user.click(within(editor).getByRole("button", { name: "Redo" }));
    expect(within(editor).getByText("2 sources")).toBeVisible();

    await user.click(screen.getByRole("tab", { name: "Evidence" }));
    const evidencePanel = screen.getByRole("tabpanel", { name: "Evidence" });
    expect(
      within(evidencePanel).getByText("Local CP3C draft · session only"),
    ).toBeVisible();
    expect(
      within(evidencePanel).getByText(
        `${queryText.length} prompt characters · 2 sources selected · not persisted`,
      ),
    ).toBeVisible();
    expect(within(evidencePanel).getByText("Not executed")).toBeVisible();
  });

  it("uses user-facing retrieval language without choosing a RAG implementation", async () => {
    const user = userEvent.setup();
    render(<EngineeringWorkflowVisualSlice />);

    expect(screen.getByText("Knowledge lookup")).toBeVisible();
    expect(screen.queryByText("Company context")).not.toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: "Input C. Knowledge Lookup" }),
    );
    const editor = screen.getByRole("region", { name: "Knowledge lookup" });
    expect(within(editor).getByText("Retrieved context")).toBeVisible();
    expect(
      within(editor).getByText(
        "No lookup has run. A later retrieval checkpoint should return reviewable passages, source citations, and retrieval evidence here.",
      ),
    ).toBeVisible();
    expect(
      within(editor).getByText(
        "Retrieval execution, provider selection, permissions, citations, and persistence come later. Source labels never select runtime code.",
      ),
    ).toBeVisible();
    expect(within(editor).queryByText(/RAG/)).not.toBeInTheDocument();
  });
});
