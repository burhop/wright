import { useState } from "react";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeAll, beforeEach, describe, expect, it, vi } from "vitest";

import type { WorkspaceWorkflowSourceDocument } from "../../services/workspace-service";
import { WorkflowRecoveryPage } from "./WorkflowRecoveryPage";

const mocks = vi.hoisted(() => ({
  get: vi.fn(),
  files: vi.fn(),
  update: vi.fn(),
  run: vi.fn(),
}));
vi.mock("../../services/workspace-service", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("../../services/workspace-service")>();
  return {
    ...actual,
    workspaceService: {
      ...actual.workspaceService,
      getWorkspaceWorkflowSource: mocks.get,
      getWorkspaceWorkflowInputFiles: mocks.files,
      updateWorkspaceWorkflowSource: mocks.update,
      runWorkspaceWorkflowSource: mocks.run,
      getWorkspaceWorkflowReviews: vi.fn().mockResolvedValue([]),
      getWorkspaceWorkflowRuns: vi.fn().mockResolvedValue([]),
    },
  };
});

const source = `workflow prompt_to_html
  name: "Prompt to HTML"
  purpose: "Create a report."
  discipline: "mechanical.design"
  reviewed_ai_suggestions: true
end
task document_1
  name: "Original report"
  purpose: "Create report.html."
  step_type: work
  group: null
  performed_by: ai_assisted
  inputs: []
  outputs: [{"description":"Report","item":null,"key":"document_1_document_out","kind":"engineering_document","name":"HTML report","quantity":"one","required":true}]
  prompt: "Create a report about a bracket."
  settings: {"authoring_template":"document","binding_state":"unbound","output_filename":"report.html","output_format":"html"}
  tool: null
  reusable_step: null
end`;
const original: WorkspaceWorkflowSourceDocument = {
  workspace_id: "workspace-1",
  path: "workflows/report.workflow.wflow",
  storage_revision: 1,
  storage_digest: "a".repeat(64),
  definition_revision: 1,
  metadata_authority: "wright_host",
  size_bytes: source.length,
  source,
};
const changed = {
  ...original,
  source: source.replace("Original report", "Stored report"),
  storage_revision: 2,
  storage_digest: "b".repeat(64),
  definition_revision: 2,
};

function Page() {
  const [reopenRequest, setReopenRequest] = useState(0);
  return (
    <WorkflowRecoveryPage
      workspaceId="workspace-1"
      sessionId="session-1"
      workspaceName="Test workspace"
      workflowFilePath={`/${original.path}`}
      reopenRequest={reopenRequest}
      onOpenWorkflow={(path) => {
        expect(path).toBe(original.path);
        setReopenRequest((value) => value + 1);
      }}
    />
  );
}

async function openSameFile() {
  await userEvent.click(screen.getByTestId("workflow-file-open"));
  await userEvent.click(
    await screen.findByTestId(`workflow-file-choice-${original.path}`),
  );
}

beforeAll(() => {
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe() {}
      unobserve() {}
      disconnect() {}
    },
  );
});
beforeEach(() => {
  vi.clearAllMocks();
  mocks.get.mockReset();
  mocks.get.mockResolvedValueOnce(original).mockResolvedValue(changed);
  mocks.files.mockResolvedValue([
    { name: "report.workflow.wflow", path: original.path },
  ]);
  mocks.run.mockResolvedValue({
    workspace_id: "workspace-1",
    workflow_path: original.path,
    output_path: "report.html",
    output_bytes: 100,
    task_title: "Stored report",
    workflow_title: "Prompt to HTML",
  });
});

describe("reopening a retained workspace workflow", () => {
  it("loads the new saved revision through the normal Open modal and runs that exact digest", async () => {
    render(<Page />);
    expect(
      await screen.findByTestId("workflow-recovery-block-block.document-1"),
    ).toHaveTextContent("Original report");
    await openSameFile();
    await waitFor(() =>
      expect(
        screen.getByTestId("workflow-recovery-block-block.document-1"),
      ).toHaveTextContent("Stored report"),
    );
    expect(mocks.get).toHaveBeenCalledTimes(2);
    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    await waitFor(() =>
      expect(mocks.run).toHaveBeenCalledWith(
        "session-1",
        original.path,
        changed.storage_digest,
        expect.any(Function),
        expect.any(AbortSignal),
      ),
    );
    expect(mocks.update).not.toHaveBeenCalled();
  });

  it.each(["source", "diagram"])(
    "keeps unsaved %s edits and the old CAS identity, exposing existing comparison controls",
    async (kind) => {
      render(<Page />);
      await screen.findByTestId("workflow-recovery-block-block.document-1");
      if (kind === "source") {
        await userEvent.click(screen.getByRole("tab", { name: "Source" }));
        fireEvent.change(
          screen.getByTestId("workflow-recovery-source-editor"),
          { target: { value: "Unapplied local source" } },
        );
      } else {
        fireEvent.doubleClick(
          screen
            .getByTestId("workflow-recovery-block-block.document-1")
            .querySelector("h3")!,
        );
        fireEvent.change(
          screen.getByTestId("workflow-recovery-rename-block.document-1"),
          { target: { value: "Local report" } },
        );
        fireEvent.keyDown(
          screen.getByTestId("workflow-recovery-rename-block.document-1"),
          { key: "Enter" },
        );
      }
      const localRevision = screen
        .getByTestId("workflow-recovery-concept")
        .getAttribute("data-revision");
      await openSameFile();
      expect(
        await screen.findByTestId("workflow-recovery-conflict-actions"),
      ).toBeVisible();
      expect(screen.getByTestId("workflow-recovery-concept")).toHaveAttribute(
        "data-revision",
        localRevision,
      );
      if (kind === "source") {
        expect(
          screen.getByTestId("workflow-recovery-source-editor"),
        ).toHaveValue("Unapplied local source");
      } else {
        expect(
          screen.getByTestId("workflow-recovery-block-block.document-1"),
        ).toHaveTextContent("Local report");
      }
      await userEvent.click(
        screen.getByTestId("workflow-recovery-conflict-compare"),
      );
      expect(
        await screen.findByRole("dialog", { name: "Compare workflow sources" }),
      ).toBeVisible();
      expect(
        screen.getByTestId("workflow-recovery-source-comparison-stored"),
      ).toHaveValue(changed.source);
      expect(mocks.update).not.toHaveBeenCalled();
      expect(mocks.run).not.toHaveBeenCalled();
    },
  );

  it("protects edits made while the fresh file read is pending", async () => {
    let finish!: (value: WorkspaceWorkflowSourceDocument) => void;
    mocks.get
      .mockReset()
      .mockResolvedValueOnce(original)
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            finish = resolve;
          }),
      );
    render(<Page />);
    await screen.findByTestId("workflow-recovery-block-block.document-1");
    await openSameFile();
    await userEvent.click(screen.getByRole("tab", { name: "Source" }));
    fireEvent.change(screen.getByTestId("workflow-recovery-source-editor"), {
      target: { value: "Local edit during read" },
    });
    await act(async () => finish(changed));
    expect(screen.getByTestId("workflow-recovery-source-editor")).toHaveValue(
      "Local edit during read",
    );
    expect(
      screen.getByTestId("workflow-recovery-conflict-actions"),
    ).toBeVisible();
  });

  it("keeps a running workflow instead of remounting and cancelling it", async () => {
    mocks.run.mockImplementationOnce(() => new Promise(() => undefined));
    render(<Page />);
    await screen.findByTestId("workflow-recovery-block-block.document-1");
    await userEvent.click(screen.getByTestId("workflow-recovery-run-start"));
    await waitFor(() => expect(mocks.run).toHaveBeenCalledOnce());
    const signal = mocks.run.mock.calls[0][4] as AbortSignal;
    await openSameFile();
    await waitFor(() => expect(mocks.get).toHaveBeenCalledTimes(2));
    expect(
      screen.getByTestId("workflow-recovery-block-block.document-1"),
    ).toHaveTextContent("Original report");
    expect(screen.getByTestId("workflow-recovery-run-start")).toHaveTextContent(
      "Running",
    );
    expect(signal.aborted).toBe(false);
  });

  it("keeps the current editor when the refresh fails", async () => {
    mocks.get
      .mockReset()
      .mockResolvedValueOnce(original)
      .mockRejectedValueOnce(new Error("Workspace read failed"));
    render(<Page />);
    await screen.findByTestId("workflow-recovery-block-block.document-1");
    await openSameFile();
    await waitFor(() =>
      expect(
        screen.getByTestId("workflow-recovery-save-status"),
      ).toHaveTextContent("Workspace read failed"),
    );
    expect(
      screen.getByTestId("workflow-recovery-block-block.document-1"),
    ).toHaveTextContent("Original report");
    expect(mocks.update).not.toHaveBeenCalled();
  });
});
