import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  workspaceService,
  type EngineeringWorkflowTemplate,
  type EngineeringWorkflowTemplateDetail,
} from "../../services/workspace-service";
import { EngineeringTemplateDialog } from "./EngineeringTemplateDialog";
import { initialLayout } from "./model";

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

const handle: EngineeringWorkflowTemplate = {
  ...templates[0],
  template_id: "replacement-drawer-handle",
  title: "Replace a drawer handle",
  external_effects: [],
  exploration: {
    preview_kind: "supplied_sketch",
    preview_caption: "Original fictional sample; the bolt spacing is 96 mm.",
    outcome_status: "pending",
    outcome_summary: "A measured handle result has not been recorded yet.",
    stages: [
      {
        title: "Prepare the print package",
        tool: "Independent slicer",
        contribution: "Compare orientations and support contacts.",
        input: "Measured handle mesh",
        output: "3MF package and support preview",
      },
    ],
    limitations: ["Physical fit has not been demonstrated."],
  },
};

function detailFor(
  template: EngineeringWorkflowTemplate,
  title: string,
): EngineeringWorkflowTemplateDetail {
  return {
    ...template,
    source: "workflow test\nend\n",
    layout: initialLayout,
    layout_digest: digest,
    acceptance_profile: "test/v1",
    definition_status: "reviewed",
    rights: { fixture: "test-only" },
    capability_requirements: [
      { title, operation: "slice_with_supports", qualification: "required" },
    ],
  };
}

function renderDialog() {
  return render(
    <EngineeringTemplateDialog
      open
      sessionId="session"
      workspaceId="workspace"
      workspaceName="Demo"
      onClose={vi.fn()}
      onCreated={vi.fn()}
    />,
  );
}

describe("EngineeringTemplateDialog", () => {
  afterEach(() => vi.restoreAllMocks());

  it("explores the supplied handle and pending outcome without setup or execution", async () => {
    vi.spyOn(
      workspaceService,
      "getEngineeringWorkflowTemplates",
    ).mockResolvedValue([...templates, handle]);
    const getDetail = vi.spyOn(
      workspaceService,
      "getEngineeringWorkflowTemplate",
    );
    const instantiate = vi.spyOn(
      workspaceService,
      "instantiateEngineeringWorkflowTemplate",
    );
    const readiness = vi.spyOn(
      workspaceService,
      "refreshEngineeringWorkflowTemplateReadiness",
    );
    renderDialog();

    expect(await screen.findAllByRole("option")).toHaveLength(11);
    expect(
      screen.getByRole("option", { name: /Replace a drawer handle/ }),
    ).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("Supplied sketch")).toBeVisible();
    expect(screen.getByTestId("workflow-template-outcome")).toHaveTextContent(
      "Recorded outcome pending",
    );
    expect(
      screen.getByRole("region", { name: "Engineering tool handoffs" }),
    ).toHaveTextContent("Measured handle mesh");
    expect(
      screen.getByRole("region", { name: "Example limitations" }),
    ).toHaveTextContent("Physical fit has not been demonstrated");
    expect(getDetail).not.toHaveBeenCalled();
    expect(instantiate).not.toHaveBeenCalled();
    expect(readiness).not.toHaveBeenCalled();
  });

  it("shows only this job's packaged requirements on request and explains the actual readiness step", async () => {
    vi.spyOn(
      workspaceService,
      "getEngineeringWorkflowTemplates",
    ).mockResolvedValue([handle, ...templates]);
    const getDetail = vi
      .spyOn(workspaceService, "getEngineeringWorkflowTemplate")
      .mockResolvedValue(detailFor(handle, "Handle slicing"));
    const readiness = vi.spyOn(
      workspaceService,
      "refreshEngineeringWorkflowTemplateReadiness",
    );
    renderDialog();
    await screen.findAllByRole("option");
    await userEvent.click(screen.getByTestId("workflow-template-setup"));

    expect(await screen.findByText("Handle slicing")).toBeVisible();
    expect(getDetail).toHaveBeenCalledWith(handle.template_id, handle.version);
    expect(
      screen.getByRole("region", { name: "Setup requirements" }),
    ).toHaveTextContent("Prepare and check inputs");
    expect(screen.getByTestId("workflow-template-readiness")).toHaveTextContent(
      "Packaged starter status",
    );
    expect(readiness).not.toHaveBeenCalled();
  });

  it("keeps recorded result provenance distinct from a live run", async () => {
    const recorded: EngineeringWorkflowTemplate = {
      ...handle,
      version: "1.0.1",
      preview: {
        asset: "previews/replacement-drawer-handle.svg",
        alt: "Supplied sketch beside the actual recorded repaired handle; no live execution.",
      },
      exploration: {
        ...handle.exploration!,
        preview_kind: "recorded_result",
        preview_caption:
          "Supplied intent and actual recorded geometry are separately labelled.",
        outcome_status: "recorded",
        outcome_summary: "A retained digital preparation example.",
        recorded_result: {
          run_id: "recorded-run",
          source_digest: digest,
          artifact_digest: "a".repeat(64),
          evidence_reference: "retained/handle-evidence.json",
          scope: "Digital preparation only; physical fit remains unverified.",
        },
      },
    };
    vi.spyOn(
      workspaceService,
      "getEngineeringWorkflowTemplates",
    ).mockResolvedValue([recorded]);
    const instantiate = vi.spyOn(
      workspaceService,
      "instantiateEngineeringWorkflowTemplate",
    );
    const readiness = vi.spyOn(
      workspaceService,
      "refreshEngineeringWorkflowTemplateReadiness",
    );
    const setup = vi.spyOn(workspaceService, "getEngineeringWorkflowTemplate");
    renderDialog();
    await screen.findAllByRole("option");
    await userEvent.click(
      screen.getByTestId("workflow-template-recorded-evidence"),
    );

    expect(
      screen.getByRole("img", { name: recorded.preview.alt }),
    ).toBeVisible();
    expect(
      screen.getByRole("img", { name: recorded.preview.alt }),
    ).toHaveAttribute("src", expect.stringContaining("version=1.0.1"));
    expect(screen.getByTestId("workflow-template-readiness")).toHaveTextContent(
      "Setup required",
    );
    expect(screen.getByText("recorded-run")).toBeVisible();
    expect(screen.getByText("retained/handle-evidence.json")).toBeVisible();
    expect(screen.getByTestId("workflow-template-outcome")).toHaveTextContent(
      "Live results appear in the working view after you start your own run",
    );
    expect(instantiate).not.toHaveBeenCalled();
    expect(readiness).not.toHaveBeenCalled();
    expect(setup).not.toHaveBeenCalled();
  });

  it("ignores requirements that arrive after the user chooses another example", async () => {
    vi.spyOn(
      workspaceService,
      "getEngineeringWorkflowTemplates",
    ).mockResolvedValue([handle, ...templates]);
    let finishHandle!: (detail: EngineeringWorkflowTemplateDetail) => void;
    vi.spyOn(
      workspaceService,
      "getEngineeringWorkflowTemplate",
    ).mockImplementation((templateId) =>
      templateId === handle.template_id
        ? new Promise((resolve) => {
            finishHandle = resolve;
          })
        : Promise.resolve(detailFor(templates[0], "Generic image modeling")),
    );
    renderDialog();
    await screen.findAllByRole("option");
    await userEvent.click(screen.getByTestId("workflow-template-setup"));
    await userEvent.click(
      screen.getByTestId("workflow-template-option-printed-replacement-part"),
    );
    await userEvent.click(screen.getByTestId("workflow-template-setup"));
    expect(await screen.findByText("Generic image modeling")).toBeVisible();
    await act(async () => finishHandle(detailFor(handle, "Handle slicing")));

    expect(screen.queryByText("Handle slicing")).not.toBeInTheDocument();
    expect(screen.getByText("Generic image modeling")).toBeVisible();
  });

  it("rejects requirements from a different source revision", async () => {
    vi.spyOn(
      workspaceService,
      "getEngineeringWorkflowTemplates",
    ).mockResolvedValue([handle]);
    vi.spyOn(
      workspaceService,
      "getEngineeringWorkflowTemplate",
    ).mockResolvedValue({
      ...detailFor(handle, "Changed requirements"),
      source_digest: "e".repeat(64),
    });
    renderDialog();
    await screen.findAllByRole("option");
    await userEvent.click(screen.getByTestId("workflow-template-setup"));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "starter changed",
    );
    expect(screen.queryByText("Changed requirements")).not.toBeInTheDocument();
  });

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
