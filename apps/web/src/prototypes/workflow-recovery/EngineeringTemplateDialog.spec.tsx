import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  workspaceService,
  type EngineeringWorkflowTemplate,
} from "../../services/workspace-service";
import { EngineeringTemplateDialog } from "./EngineeringTemplateDialog";

const digest = "d".repeat(64);
const templates: EngineeringWorkflowTemplate[] = Array.from(
  { length: 10 },
  (_, index) => ({
    template_id: index === 0 ? "printed-replacement-part" : `template-${index}`,
    version: "1.0.0",
    title:
      index === 0
        ? "3D Printed Replacement Part"
        : `Engineering Example ${index + 1}`,
    summary: "A measurable engineering workflow with explicit outputs.",
    discipline: "Engineering",
    preview: { asset: `previews/${index}.svg`, alt: `Preview ${index}` },
    provided_inputs: [{ name: "Fixture" }],
    requested_inputs: [{ name: "Requirements" }],
    expected_outputs: [{ name: "Verified artifact" }],
    external_effects: index === 0 ? ["printer_transfer"] : [],
    source_digest: digest,
    readiness: {
      state: index === 0 ? "setup_required" : "reference",
      definition_valid: true,
      configured: false,
      qualified: false,
      available: false,
      verified_run: false,
      facts: [],
      blocking_reasons: ["Qualification required."],
    },
  }),
);

describe("EngineeringTemplateDialog", () => {
  afterEach(() => vi.restoreAllMocks());

  it("shows ten keyboard-selectable options and truthful details", async () => {
    vi.spyOn(
      workspaceService,
      "getEngineeringWorkflowTemplates",
    ).mockResolvedValue(templates);
    render(
      <EngineeringTemplateDialog
        open
        sessionId="session"
        workspaceId="workspace"
        workspaceName="Demo"
        onClose={vi.fn()}
        onCreated={vi.fn()}
      />,
    );
    expect(await screen.findAllByRole("option")).toHaveLength(10);
    expect(screen.getByTestId("workflow-template-readiness")).toHaveTextContent(
      "Setup required",
    );
    expect(screen.getByTestId("workflow-template-details")).toHaveTextContent(
      "printer transfer",
    );
    const options = screen.getAllByRole("option");
    options[0].focus();
    await userEvent.keyboard("{ArrowDown}");
    expect(options[1]).toHaveFocus();
    expect(options[1]).toHaveAttribute("aria-selected", "true");
  });

  it("creates an editable copy and returns its canonical workspace path", async () => {
    vi.spyOn(
      workspaceService,
      "getEngineeringWorkflowTemplates",
    ).mockResolvedValue(templates);
    const instantiate = vi
      .spyOn(workspaceService, "instantiateEngineeringWorkflowTemplate")
      .mockResolvedValue({
        workspace_id: "workspace",
        path: "workflows/my-part.workflow.wflow",
      } as never);
    const onCreated = vi.fn();
    const onClose = vi.fn();
    render(
      <EngineeringTemplateDialog
        open
        sessionId="session"
        workspaceId="workspace"
        workspaceName="Demo"
        onClose={onClose}
        onCreated={onCreated}
      />,
    );
    await screen.findAllByRole("option");
    const name = screen.getByTestId("workflow-template-name");
    await userEvent.clear(name);
    await userEvent.type(name, "My Part");
    await userEvent.click(screen.getByTestId("workflow-template-create"));
    await waitFor(() =>
      expect(onCreated).toHaveBeenCalledWith(
        "workflows/my-part.workflow.wflow",
      ),
    );
    expect(onClose).toHaveBeenCalled();
    expect(instantiate).toHaveBeenCalledWith(
      "session",
      templates[0],
      "workflows/my-part.workflow.wflow",
      expect.any(String),
    );
  });

  it("cancels without creating anything", async () => {
    vi.spyOn(
      workspaceService,
      "getEngineeringWorkflowTemplates",
    ).mockResolvedValue(templates);
    const instantiate = vi.spyOn(
      workspaceService,
      "instantiateEngineeringWorkflowTemplate",
    );
    const onClose = vi.fn();
    render(
      <EngineeringTemplateDialog
        open
        sessionId="session"
        workspaceId="workspace"
        workspaceName="Demo"
        onClose={onClose}
        onCreated={vi.fn()}
      />,
    );
    await screen.findAllByRole("option");
    await userEvent.click(screen.getByTestId("workflow-template-cancel"));
    expect(onClose).toHaveBeenCalled();
    expect(instantiate).not.toHaveBeenCalled();
  });

  it("keeps invalid names and storage collisions inside the dialog", async () => {
    vi.spyOn(
      workspaceService,
      "getEngineeringWorkflowTemplates",
    ).mockResolvedValue(templates);
    const instantiate = vi
      .spyOn(workspaceService, "instantiateEngineeringWorkflowTemplate")
      .mockRejectedValue(
        new Error("A workflow already exists with that name."),
      );
    render(
      <EngineeringTemplateDialog
        open
        sessionId="session"
        workspaceId="workspace"
        workspaceName="Demo"
        onClose={vi.fn()}
        onCreated={vi.fn()}
      />,
    );
    await screen.findAllByRole("option");
    const name = screen.getByTestId("workflow-template-name");
    await userEvent.clear(name);
    await userEvent.type(name, "!!!");
    await userEvent.click(screen.getByTestId("workflow-template-create"));
    expect(screen.getByRole("alert")).toHaveTextContent("short workflow name");
    expect(instantiate).not.toHaveBeenCalled();

    await userEvent.clear(name);
    await userEvent.type(name, "Existing Part");
    await userEvent.click(screen.getByTestId("workflow-template-create"));
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent("already exists"),
    );
    expect(screen.getByTestId("workflow-template-details")).toBeVisible();
  });
});
