import { StrictMode } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  get: vi.fn(),
  readiness: vi.fn(),
  create: vi.fn(),
  copy: vi.fn(),
  update: vi.fn(),
  files: vi.fn(),
  history: vi.fn(),
  templates: vi.fn(),
  setup: vi.fn(),
}));

vi.mock("../../prototypes/workflow-recovery/PrintedHandleSetupDialog", () => ({
  PrintedHandleSetupDialog: (props: {
    document: import("../../services/workspace-service").WorkspaceWorkflowSourceDocument;
    onAccepted: (
      document: import("../../services/workspace-service").WorkspaceWorkflowSourceDocument,
    ) => void;
  }) => {
    mocks.setup(props);
    return (
      <button
        data-testid="fixture-accept-setup"
        onClick={() =>
          props.onAccepted({
            ...props.document,
            source: "prepared exact source",
            storage_digest: "c".repeat(64),
            storage_revision: props.document.storage_revision + 1,
            definition_revision: props.document.definition_revision + 1,
          })
        }
      >
        Accept setup fixture
      </button>
    );
  },
}));

vi.mock("../../services/workflow-source-copy", () => ({
  copyWorkspaceWorkflowSource: mocks.copy,
}));

vi.mock("../process-interfaces/HistoricalResultView", () => ({
  HistoricalResultView: (props: {
    workflowPath: string;
    runLogPath: string;
    onClose: () => void;
  }) => {
    mocks.history(props);
    return (
      <button data-testid="historical-result-fixture" onClick={props.onClose}>
        Back to workflow
      </button>
    );
  },
}));

vi.mock("../../services/workspace-service", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("../../services/workspace-service")>();
  return {
    ...actual,
    workspaceService: {
      getWorkspaceWorkflowSource: mocks.get,
      getWorkspaceWorkflowRuns: vi.fn().mockResolvedValue([]),
      getWorkspaceWorkflowSourceReadiness: mocks.readiness,
      createWorkspaceWorkflowSource: mocks.create,
      updateWorkspaceWorkflowSource: mocks.update,
      getWorkspaceWorkflowInputFiles: mocks.files,
      getWorkspaceWorkflowReviews: vi.fn().mockResolvedValue([]),
      getEngineeringWorkflowTemplates: mocks.templates,
    },
  };
});

vi.mock(
  "../../prototypes/workflow-recovery/WorkflowRecoveryConcept",
  async () => {
    const { useState } = await import("react");
    function MockWorkflowRecoveryConcept(props: {
      surfaceState?: string;
      fileActions?: import("react").ReactNode;
      workflowSource?: string;
      definitionRevision?: number;
      storageDigest?: string;
      workflowFilePath?: string;
      workflowLayout?: import("../../prototypes/workflow-recovery/model").RecoveryLayout;
      onSave?: (
        source: string,
        layout?: import("../../prototypes/workflow-recovery/model").RecoveryLayout,
      ) => Promise<unknown>;
      onListWorkspaceFiles?: () => Promise<
        Array<{ path: string; name: string }>
      >;
      onReadStoredSource?: () => Promise<{ source: string }>;
      onReloadStoredSource?: () => Promise<void>;
      templateReadiness?: { state: string } | null;
      onRefreshTemplateReadiness?: () => void;
      onUnsavedChange?: (unsaved: boolean) => void;
      onOpenRunWorkingView?: (runId: string, sourceDigest: string) => void;
    }) {
      const [initialSource] = useState(props.workflowSource);
      const [readSource, setReadSource] = useState("");
      const [files, setFiles] = useState("");
      return (
        <div
          data-testid="workflow-editor-fixture"
          data-state={props.surfaceState ?? "ready"}
          data-source={initialSource}
          data-current-source={props.workflowSource}
          data-read-source={readSource}
          data-definition-revision={props.definitionRevision}
          data-storage-digest={props.storageDigest}
          data-path={props.workflowFilePath}
          data-layout={JSON.stringify(props.workflowLayout)}
          data-files={files}
        >
          <output data-testid="fixture-readiness">
            {props.templateReadiness?.state ?? "none"}
          </output>
          {props.onRefreshTemplateReadiness && (
            <button
              type="button"
              data-testid="fixture-readiness-refresh"
              onClick={() => void props.onRefreshTemplateReadiness?.()}
            >
              Refresh readiness fixture
            </button>
          )}
          {props.fileActions}
          {props.onOpenRunWorkingView && (
            <button
              data-testid="fixture-answer-input"
              onClick={() =>
                props.onOpenRunWorkingView?.("waiting-run", "b".repeat(64))
              }
            >
              Answer input fixture
            </button>
          )}
          <button
            data-testid="fixture-edit"
            onClick={() => props.onUnsavedChange?.(true)}
          >
            Edit fixture
          </button>
          <button
            data-testid="fixture-clean"
            onClick={() => props.onUnsavedChange?.(false)}
          >
            Clean fixture
          </button>
          {props.onSave && (
            <button
              type="button"
              data-testid="fixture-save"
              onClick={() =>
                void props
                  .onSave?.("updated workflow source", props.workflowLayout)
                  ?.catch(() => {})
              }
            >
              Save fixture
            </button>
          )}
          {props.onListWorkspaceFiles && (
            <button
              type="button"
              data-testid="fixture-files"
              onClick={() =>
                void props
                  .onListWorkspaceFiles?.()
                  .then((values) => setFiles(JSON.stringify(values)))
              }
            >
              List files fixture
            </button>
          )}
          {props.onReadStoredSource && (
            <button
              type="button"
              data-testid="fixture-read"
              onClick={() =>
                void props
                  .onReadStoredSource?.()
                  .then((stored) => setReadSource(stored.source))
              }
            >
              Read stored fixture
            </button>
          )}
          {props.onReloadStoredSource && (
            <button
              type="button"
              data-testid="fixture-reload"
              onClick={() => void props.onReloadStoredSource?.()}
            >
              Reload stored fixture
            </button>
          )}
        </div>
      );
    }
    return {
      default: MockWorkflowRecoveryConcept,
    };
  },
);

import {
  WorkspaceWorkflowSourceNotFoundError,
  type WorkspaceWorkflowSourceDocument,
} from "../../services/workspace-service";
import { initialLayout } from "../../prototypes/workflow-recovery/model";
import { WorkflowRecoveryPage } from "./WorkflowRecoveryPage";

const document: WorkspaceWorkflowSourceDocument = {
  workspace_id: "workspace-1",
  path: "workflows/mounting-bracket.workflow.wflow",
  storage_revision: 4,
  storage_digest: "a".repeat(64),
  definition_revision: 2,
  metadata_authority: "wright_host",
  size_bytes: 200,
  source: "workflow mounting_bracket\nend\n",
};

function renderPage({
  strict = false,
  onOpenWorkflow,
  onUnsavedChange,
  onSavingChange,
  onOpenProcess,
  createIfMissing,
}: {
  strict?: boolean;
  onOpenWorkflow?: (path: string) => void;
  onUnsavedChange?: (path: string, unsaved: boolean) => void;
  onSavingChange?: (path: string, saving: boolean) => void;
  onOpenProcess?: (
    process: import("@wright/process-client").ProcessRef,
  ) => void;
  createIfMissing?: boolean;
} = {}) {
  const page = (
    <WorkflowRecoveryPage
      workspaceId="workspace-1"
      sessionId="session-1"
      workspaceName="Bracket Program"
      workflowFilePath="/workflows/mounting-bracket.workflow.wflow"
      onOpenWorkflow={onOpenWorkflow}
      onUnsavedChange={onUnsavedChange}
      onSavingChange={onSavingChange}
      onOpenProcess={onOpenProcess}
      createIfMissing={createIfMissing}
    />
  );
  return render(strict ? <StrictMode>{page}</StrictMode> : page);
}

describe("workspace workflow page", () => {
  beforeEach(() => {
    window.history.replaceState({}, "", "/");
    mocks.history.mockReset();
    mocks.get.mockReset();
    mocks.readiness.mockReset();
    mocks.readiness.mockResolvedValue({ state: "not_template" });
    mocks.create.mockReset();
    mocks.copy.mockReset();
    mocks.update.mockReset();
    mocks.files.mockReset();
    mocks.templates.mockReset().mockResolvedValue([]);
    mocks.setup.mockReset();
  });

  it("opens example exploration without replacing the current source or clearing edits", async () => {
    mocks.get.mockResolvedValue(document);
    const onOpenWorkflow = vi.fn();
    renderPage({ onOpenWorkflow });
    await screen.findByTestId("fixture-edit");
    await userEvent.click(screen.getByTestId("fixture-edit"));
    await userEvent.click(screen.getByTestId("workflow-explore-example"));

    expect(
      await screen.findByRole("dialog", {
        name: "Start from an engineering workflow",
      }),
    ).toBeVisible();
    await waitFor(() => expect(mocks.templates).toHaveBeenCalledTimes(1));
    await userEvent.click(screen.getByTestId("workflow-template-cancel"));
    expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute(
      "data-current-source",
      document.source,
    );
    expect(
      screen.getByRole("button", { name: "Export / import workflow" }),
    ).toBeDisabled();
    expect(mocks.create).not.toHaveBeenCalled();
    expect(mocks.update).not.toHaveBeenCalled();
    expect(onOpenWorkflow).not.toHaveBeenCalled();
    expect(mocks.setup).not.toHaveBeenCalled();
  });

  it("opens handle setup only on request, protects dirty edits, and returns the accepted revision to the same editor without starting", async () => {
    mocks.get.mockResolvedValue(document);
    mocks.readiness.mockResolvedValue({
      state: "setup_required",
      template_id: "replacement-drawer-handle",
    });
    const onOpenProcess = vi.fn();
    renderPage({ onOpenProcess });
    const setup = await screen.findByTestId("workflow-handle-setup-open");
    expect(mocks.setup).not.toHaveBeenCalled();
    await userEvent.click(screen.getByTestId("fixture-edit"));
    expect(setup).toBeDisabled();
    expect(setup).toHaveAttribute(
      "title",
      "Setup requires an unchanged starter. Preserve your edits or create a fresh starter.",
    );
    await userEvent.click(setup);
    expect(mocks.setup).not.toHaveBeenCalled();
    await userEvent.click(screen.getByTestId("fixture-clean"));
    await userEvent.click(setup);
    expect(mocks.setup.mock.calls.at(-1)?.[0].document).toEqual(document);
    await userEvent.click(screen.getByTestId("fixture-accept-setup"));
    expect(screen.queryByTestId("fixture-accept-setup")).toBeNull();
    expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute(
      "data-current-source",
      "prepared exact source",
    );
    expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute(
      "data-path",
      document.path,
    );
    expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute(
      "data-storage-digest",
      "c".repeat(64),
    );
    expect(screen.getByText(/^Prepared revision saved\./)).toBeVisible();
    expect(onOpenProcess).not.toHaveBeenCalled();
    expect(mocks.update).not.toHaveBeenCalled();
    await waitFor(() => expect(mocks.readiness).toHaveBeenCalledTimes(2));
  });

  it("keeps revised handle processes on ordinary readiness without offering starter replacement", async () => {
    mocks.get.mockResolvedValue(document);
    mocks.readiness.mockResolvedValue({
      state: "revised",
      template_id: "replacement-drawer-handle",
    });
    const onOpenProcess = vi.fn();
    renderPage({ onOpenProcess });
    await waitFor(() => expect(mocks.readiness).toHaveBeenCalledTimes(1));
    expect(screen.queryByTestId("workflow-handle-setup-open")).toBeNull();
    await userEvent.click(screen.getByTestId("workflow-working-view-open"));
    expect(onOpenProcess).toHaveBeenCalledExactlyOnceWith({
      workspace_id: document.workspace_id,
      source_path: document.path,
      source_digest: document.storage_digest,
    });
    expect(mocks.setup).not.toHaveBeenCalled();
  });

  it("reports edit and clean state to the workspace with the exact tab path", async () => {
    mocks.get.mockResolvedValue(document);
    const onUnsavedChange = vi.fn();
    renderPage({ onUnsavedChange, onOpenProcess: vi.fn() });
    await waitFor(() =>
      expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute(
        "data-state",
        "ready",
      ),
    );
    await userEvent.click(await screen.findByTestId("fixture-edit"));
    expect(onUnsavedChange).toHaveBeenLastCalledWith(
      "/workflows/mounting-bracket.workflow.wflow",
      true,
    );
    expect(
      screen.getByRole("button", { name: "Open working view" }),
    ).toBeDisabled();
    await userEvent.click(screen.getByTestId("fixture-clean"));
    expect(onUnsavedChange).toHaveBeenLastCalledWith(
      "/workflows/mounting-bracket.workflow.wflow",
      false,
    );
    expect(
      screen.getByRole("button", { name: "Open working view" }),
    ).toBeEnabled();
  });

  it.each(["success", "failure"])(
    "reports the exact pending save until %s",
    async (outcome) => {
      mocks.get.mockResolvedValue(document);
      let resolveSave!: (value: typeof document) => void;
      let rejectSave!: (error: Error) => void;
      mocks.update.mockImplementation(
        () =>
          new Promise((resolve, reject) => {
            resolveSave = resolve;
            rejectSave = reject;
          }),
      );
      const onSavingChange = vi.fn();
      renderPage({ onSavingChange });
      await waitFor(() =>
        expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute(
          "data-state",
          "ready",
        ),
      );
      await userEvent.click(screen.getByTestId("fixture-save"));
      expect(onSavingChange.mock.calls).toEqual([
        ["/workflows/mounting-bracket.workflow.wflow", true],
      ]);
      if (outcome === "success")
        resolveSave({ ...document, source: "updated workflow source" });
      else rejectSave(new Error("Fixture save failed"));
      await waitFor(() =>
        expect(onSavingChange.mock.calls).toEqual([
          ["/workflows/mounting-bracket.workflow.wflow", true],
          ["/workflows/mounting-bracket.workflow.wflow", false],
        ]),
      );
    },
  );

  it("offers shared process entry without the retired active demo", async () => {
    mocks.get.mockResolvedValue(document);
    renderPage({ onOpenProcess: vi.fn() });
    await screen.findByTestId("workflow-editor-fixture");
    expect(
      screen.getByRole("button", { name: "Open working view" }),
    ).toBeVisible();
    expect(
      screen.queryByRole("button", { name: "Print a part demo" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("workflow-print-demo-open"),
    ).not.toBeInTheDocument();
    expect(mocks.history).not.toHaveBeenCalled();
  });
  it("opens the exact paused run and captured source rather than a new preparation", async () => {
    mocks.get.mockResolvedValue(document);
    const onOpenProcess = vi.fn();
    renderPage({ onOpenProcess });
    await userEvent.click(await screen.findByTestId("fixture-answer-input"));
    expect(onOpenProcess).toHaveBeenCalledExactlyOnceWith(
      {
        workspace_id: document.workspace_id,
        source_path: document.path,
        source_digest: "b".repeat(64),
      },
      "waiting-run",
    );
  });

  it("preserves the historical result query as a read-only view and returns to its editor", async () => {
    window.history.replaceState(
      {},
      "",
      "/?workflowPath=workflows%2Fmounting-bracket.workflow.wflow&printDemoRun=runs%2Fmounting-bracket%2Fold.json",
    );
    mocks.get.mockResolvedValue(document);
    renderPage();
    await screen.findByTestId("historical-result-fixture");
    expect(mocks.history.mock.calls.at(-1)![0]).toMatchObject({
      workflowPath: document.path,
      runLogPath: "runs/mounting-bracket/old.json",
    });
    expect(
      screen.queryByTestId("workflow-editor-fixture"),
    ).not.toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("button", { name: "Back to workflow" }),
    );
    await screen.findByTestId("workflow-editor-fixture");
    expect(
      screen.getByRole("button", { name: "View saved result" }),
    ).toBeVisible();
    expect(mocks.update).not.toHaveBeenCalled();
    expect(mocks.create).not.toHaveBeenCalled();
  });

  it("does not attach another workflow's historical query to a restored tab", async () => {
    window.history.replaceState(
      {},
      "",
      "/?workflowPath=workflows%2Fother.workflow.wflow&printDemoRun=runs%2Fother%2Fold.json",
    );
    mocks.get.mockResolvedValue(document);
    renderPage();
    await screen.findByTestId("workflow-editor-fixture");
    expect(mocks.history).not.toHaveBeenCalled();
    expect(
      screen.queryByRole("button", { name: "View saved result" }),
    ).not.toBeInTheDocument();
  });

  it("opens the accepted saved process without saving, executing or opening another window", async () => {
    mocks.get.mockResolvedValue(document);
    const onOpenProcess = vi.fn();
    renderPage({ onOpenProcess });
    expect(screen.getByTestId("workflow-working-view-open")).toBeDisabled();
    await waitFor(() =>
      expect(screen.getByTestId("workflow-working-view-open")).toBeEnabled(),
    );
    await userEvent.click(screen.getByTestId("workflow-working-view-open"));
    expect(onOpenProcess).toHaveBeenCalledExactlyOnceWith({
      workspace_id: document.workspace_id,
      source_path: document.path,
      source_digest: document.storage_digest,
    });
    expect(mocks.create).not.toHaveBeenCalled();
    expect(mocks.update).not.toHaveBeenCalled();
  });

  it("does not offer a working view for a failed source read", async () => {
    mocks.get.mockRejectedValue(new Error("read failed"));
    const onOpenProcess = vi.fn();
    renderPage({ onOpenProcess });
    await screen.findByTestId("workflow-source-load-error");
    expect(screen.getByTestId("workflow-working-view-open")).toBeDisabled();
    expect(onOpenProcess).not.toHaveBeenCalled();
  });

  it("requires unsaved edits to be saved before opening the working view", async () => {
    mocks.get.mockResolvedValue(document);
    const onOpenProcess = vi.fn();
    renderPage({ onOpenProcess });
    await screen.findByTestId("workflow-editor-fixture");
    await userEvent.click(screen.getByTestId("fixture-edit"));
    expect(
      screen.getByRole("button", { name: "Open working view" }),
    ).toBeDisabled();
    expect(
      screen.getByText("Save your changes to open the working view."),
    ).toBeVisible();
    await userEvent.click(screen.getByTestId("workflow-working-view-open"));
    expect(onOpenProcess).not.toHaveBeenCalled();
    await userEvent.click(screen.getByTestId("fixture-clean"));
    await userEvent.click(
      screen.getByRole("button", { name: "Open working view" }),
    );
    expect(onOpenProcess).toHaveBeenCalledExactlyOnceWith({
      workspace_id: document.workspace_id,
      source_path: document.path,
      source_digest: document.storage_digest,
    });
  });

  it("does not create a missing workflow on passive process navigation or restoration", async () => {
    mocks.get.mockRejectedValue(new WorkspaceWorkflowSourceNotFoundError());
    renderPage({ createIfMissing: false, onOpenProcess: vi.fn() });
    const error = await screen.findByTestId("workflow-source-load-error");
    expect(error).toHaveTextContent(
      "saved workflow file is no longer available",
    );
    expect(mocks.create).not.toHaveBeenCalled();
    expect(mocks.update).not.toHaveBeenCalled();
    await userEvent.click(screen.getByTestId("workflow-source-load-retry"));
    await waitFor(() => expect(mocks.get).toHaveBeenCalledTimes(2));
    expect(mocks.create).not.toHaveBeenCalled();
  });

  it("loads the exact workspace file and passes host metadata to the editor", async () => {
    mocks.get.mockResolvedValue(document);
    renderPage();
    expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute(
      "data-state",
      "loading",
    );
    await waitFor(() =>
      expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute(
        "data-state",
        "ready",
      ),
    );
    expect(mocks.get).toHaveBeenCalledWith("session-1", document.path);
    expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute(
      "data-source",
      document.source,
    );
    expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute(
      "data-definition-revision",
      "2",
    );
    expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute(
      "data-storage-digest",
      document.storage_digest,
    );
    expect(
      screen.queryByTestId("workflow-workspace-context"),
    ).not.toBeInTheDocument();
    expect(screen.getByTestId("page-workflow-recovery")).toHaveStyle({
      width: "100%",
      minWidth: "0",
    });
  });

  it("keeps an older readiness refresh from overwriting a newer result", async () => {
    mocks.get.mockResolvedValue(document);
    let resolveOlder!: (value: { state: string }) => void;
    const older = new Promise<{ state: string }>((resolve) => {
      resolveOlder = resolve;
    });
    mocks.readiness
      .mockResolvedValueOnce({ state: "not_template" })
      .mockImplementationOnce(() => older)
      .mockResolvedValueOnce({ state: "verified" });
    renderPage();
    await screen.findByTestId("fixture-readiness-refresh");
    await userEvent.click(screen.getByTestId("fixture-readiness-refresh"));
    await userEvent.click(screen.getByTestId("fixture-readiness-refresh"));
    await waitFor(() =>
      expect(screen.getByTestId("fixture-readiness")).toHaveTextContent(
        "verified",
      ),
    );
    resolveOlder({ state: "unavailable" });
    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(screen.getByTestId("fixture-readiness")).toHaveTextContent(
      "verified",
    );
  });

  it("passes persisted layout and loads real file choices on demand in the current workspace", async () => {
    const layout = { ...initialLayout, semanticRevision: 2, layoutRevision: 3 };
    mocks.get.mockResolvedValue({
      ...document,
      layout,
      layout_revision: 3,
      layout_status: "current",
    });
    mocks.files.mockResolvedValue([
      { path: "requirements.txt", name: "requirements.txt" },
    ]);
    mocks.update.mockResolvedValue({ ...document, layout, layout_revision: 4 });
    renderPage();
    await screen.findByTestId("fixture-files");
    expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute(
      "data-layout",
      JSON.stringify(layout),
    );
    expect(mocks.files).not.toHaveBeenCalled();
    await userEvent.click(screen.getByTestId("fixture-files"));
    await waitFor(() =>
      expect(mocks.files).toHaveBeenCalledWith("session-1", "workspace-1"),
    );
    expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute(
      "data-files",
      JSON.stringify([{ path: "requirements.txt", name: "requirements.txt" }]),
    );
    await userEvent.click(screen.getByTestId("fixture-save"));
    expect(mocks.update).toHaveBeenCalledWith(
      "session-1",
      document.path,
      "updated workflow source",
      4,
      document.storage_digest,
      true,
      layout,
      3,
    );
  });

  it("creates a separately named file exclusively and then opens it without updating the original", async () => {
    const onOpen = vi.fn();
    mocks.get.mockResolvedValue(document);
    mocks.create.mockResolvedValue({
      ...document,
      path: "workflows/inspection-checks.workflow.wflow",
      storage_revision: 1,
    });
    renderPage({ onOpenWorkflow: onOpen });
    await screen.findByTestId("fixture-save");
    await userEvent.click(screen.getByTestId("workflow-file-menu"));
    await userEvent.click(screen.getByRole("button", { name: "New workflow" }));
    expect(screen.getByText(/Starts with a blank workflow/)).toBeVisible();
    expect(
      screen.queryByText(/editable engineering example/),
    ).not.toBeInTheDocument();
    await userEvent.type(
      screen.getByLabelText("Workflow name"),
      "Inspection checks",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Create workflow" }),
    );
    await waitFor(() =>
      expect(onOpen).toHaveBeenCalledWith(
        "workflows/inspection-checks.workflow.wflow",
      ),
    );
    expect(mocks.create).toHaveBeenCalledWith(
      "session-1",
      "workflows/inspection-checks.workflow.wflow",
      expect.stringContaining("Inspection checks"),
    );
    const createdSource = mocks.create.mock.calls[0]![2] as string;
    expect(createdSource).not.toMatch(/^(?:task|input|connection|item) /m);
    expect(createdSource).not.toContain("bracket");
    expect(mocks.update).not.toHaveBeenCalled();
    expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute(
      "data-source",
      document.source,
    );
  });

  it("leaves both files untouched when the chosen new name already exists", async () => {
    mocks.get.mockResolvedValue(document);
    mocks.create.mockRejectedValue(
      new Error("A workflow already exists with that name."),
    );
    const onOpen = vi.fn();
    renderPage({ onOpenWorkflow: onOpen });
    await screen.findByTestId("fixture-save");
    await userEvent.click(screen.getByRole("button", { name: "New workflow" }));
    await userEvent.type(screen.getByLabelText("Workflow name"), "Existing");
    await userEvent.click(
      screen.getByRole("button", { name: "Create workflow" }),
    );
    expect(await screen.findByTestId("workflow-files-error")).toHaveTextContent(
      "already exists",
    );
    expect(onOpen).not.toHaveBeenCalled();
    expect(mocks.update).not.toHaveBeenCalled();
  });

  it("gives separately created files distinct public workflow identities", async () => {
    mocks.get.mockResolvedValue(document);
    mocks.create.mockImplementation(async (_session, path, source) => ({
      ...document,
      path,
      source,
    }));
    renderPage({ onOpenWorkflow: vi.fn() });
    await screen.findByTestId("fixture-save");
    for (const name of ["One design", "Another design"]) {
      await userEvent.click(
        screen.getByRole("button", { name: "New workflow" }),
      );
      await userEvent.type(screen.getByLabelText("Workflow name"), name);
      await userEvent.click(
        screen.getByRole("button", { name: "Create workflow" }),
      );
      await waitFor(() =>
        expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
      );
    }
    const firstSource = mocks.create.mock.calls[0][2] as string;
    const secondSource = mocks.create.mock.calls[1][2] as string;
    const firstHeader = firstSource.match(
      /^workflow authored_[a-z0-9_]+$/m,
    )?.[0];
    const secondHeader = secondSource.match(
      /^workflow authored_[a-z0-9_]+$/m,
    )?.[0];
    expect(firstHeader).toBeTruthy();
    expect(secondHeader).toBeTruthy();
    expect(firstHeader).not.toBe(secondHeader);
    expect(mocks.update).not.toHaveBeenCalled();
  });

  it("opens an existing workflow from a fresh workspace file list without creating or saving", async () => {
    const onOpen = vi.fn();
    mocks.get.mockResolvedValue(document);
    mocks.files.mockResolvedValue([
      {
        path: "workflows/inspection.workflow.wflow",
        name: "inspection.workflow.wflow",
      },
      { path: "notes.md", name: "notes.md" },
    ]);
    renderPage({ onOpenWorkflow: onOpen });
    await screen.findByTestId("fixture-save");
    await userEvent.click(
      screen.getByRole("button", { name: "Open workflow" }),
    );
    await userEvent.click(
      await screen.findByRole("button", { name: "inspection.workflow.wflow" }),
    );
    expect(onOpen).toHaveBeenCalledWith("workflows/inspection.workflow.wflow");
    expect(mocks.create).not.toHaveBeenCalled();
    expect(mocks.update).not.toHaveBeenCalled();
  });

  it("does not create a missing workflow when an existing file is opened, including in StrictMode", async () => {
    mocks.get.mockRejectedValue(new WorkspaceWorkflowSourceNotFoundError());
    mocks.create.mockResolvedValue(document);
    renderPage({ strict: true });

    expect(
      await screen.findByTestId("workflow-source-load-error"),
    ).toHaveTextContent("create a new one explicitly");
    expect(mocks.create).not.toHaveBeenCalled();
    expect(mocks.get).toHaveBeenCalledOnce();
    expect(mocks.update).not.toHaveBeenCalled();
  });

  it("opens the stored workflow when explicit empty-file creation loses a race", async () => {
    mocks.get
      .mockRejectedValueOnce(new WorkspaceWorkflowSourceNotFoundError())
      .mockResolvedValueOnce(document);
    mocks.create.mockRejectedValue(
      new Error("Unable to create this workflow file in the workspace."),
    );

    renderPage({ createIfMissing: true });

    expect(await screen.findByTestId("fixture-save")).toBeVisible();
    expect(mocks.create).toHaveBeenCalledOnce();
    expect(mocks.get).toHaveBeenCalledTimes(2);
    expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute(
      "data-source",
      document.source,
    );
  });

  it("fails closed after an explicitly requested create failure and retries that request", async () => {
    mocks.get
      .mockRejectedValueOnce(new WorkspaceWorkflowSourceNotFoundError())
      .mockRejectedValueOnce(new WorkspaceWorkflowSourceNotFoundError())
      .mockRejectedValueOnce(new WorkspaceWorkflowSourceNotFoundError());
    mocks.create
      .mockRejectedValueOnce(new Error("The path cannot be written."))
      .mockResolvedValueOnce(document);

    renderPage({ createIfMissing: true });

    expect(
      await screen.findByTestId("workflow-source-load-error"),
    ).toHaveTextContent(
      "The default workflow could not be created in Bracket Program",
    );
    expect(screen.getByTestId("workflow-source-load-error")).toHaveTextContent(
      "Check that the workspace is writable, then retry",
    );
    expect(screen.queryByTestId("fixture-save")).not.toBeInTheDocument();

    await userEvent.click(screen.getByTestId("workflow-source-load-retry"));
    expect(await screen.findByTestId("fixture-save")).toBeVisible();
    expect(mocks.create).toHaveBeenCalledTimes(2);
    expect(mocks.get).toHaveBeenCalledTimes(3);
  });

  it("fails closed when the host response belongs to another workspace or path and never creates", async () => {
    mocks.get.mockResolvedValue({
      ...document,
      workspace_id: "workspace-elsewhere",
    });
    renderPage();

    expect(
      await screen.findByTestId("workflow-source-load-error"),
    ).toHaveTextContent("different workspace or path");
    expect(screen.queryByTestId("fixture-save")).not.toBeInTheDocument();
    expect(mocks.create).not.toHaveBeenCalled();
  });

  it("saves through compare-and-swap and rebases the next save to the returned stored identity", async () => {
    mocks.get.mockResolvedValue(document);
    mocks.update
      .mockResolvedValueOnce({
        ...document,
        storage_revision: 5,
        storage_digest: "b".repeat(64),
        definition_revision: 3,
        source: "updated workflow source",
      })
      .mockResolvedValueOnce({
        ...document,
        storage_revision: 6,
        storage_digest: "c".repeat(64),
        definition_revision: 4,
        source: "updated workflow source",
      });
    renderPage();
    await userEvent.click(await screen.findByTestId("fixture-save"));
    await waitFor(() =>
      expect(mocks.update).toHaveBeenCalledWith(
        "session-1",
        document.path,
        "updated workflow source",
        4,
        document.storage_digest,
        true,
      ),
    );
    await userEvent.click(screen.getByTestId("fixture-save"));
    await waitFor(() => expect(mocks.update).toHaveBeenCalledTimes(2));
    expect(mocks.update).toHaveBeenLastCalledWith(
      "session-1",
      document.path,
      "updated workflow source",
      5,
      "b".repeat(64),
      true,
    );
  });

  it("reads for comparison without changing the editor and remounts only after explicit reload", async () => {
    const stored = {
      ...document,
      storage_revision: 9,
      storage_digest: "d".repeat(64),
      definition_revision: 7,
      source: "workflow stored_version\nend\n",
    };
    mocks.get
      .mockResolvedValueOnce(document)
      .mockResolvedValueOnce(stored)
      .mockResolvedValueOnce(stored);
    renderPage();

    await screen.findByTestId("workflow-editor-fixture");
    await waitFor(() =>
      expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute(
        "data-state",
        "ready",
      ),
    );
    const editor = screen.getByTestId("workflow-editor-fixture");
    expect(editor).toHaveAttribute("data-source", document.source);
    await userEvent.click(screen.getByTestId("fixture-read"));
    await waitFor(() =>
      expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute(
        "data-read-source",
        stored.source,
      ),
    );
    expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute(
      "data-source",
      document.source,
    );

    await userEvent.click(screen.getByTestId("fixture-reload"));
    await waitFor(() =>
      expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute(
        "data-source",
        stored.source,
      ),
    );
    expect(mocks.get).toHaveBeenNthCalledWith(2, "session-1", document.path);
    expect(mocks.get).toHaveBeenNthCalledWith(3, "session-1", document.path);
  });
});

describe("accepted workflow copies", () => {
  beforeEach(() => {
    window.history.replaceState({}, "", "/");
    mocks.get.mockReset();
    mocks.copy.mockReset();
    mocks.create.mockReset();
    mocks.readiness.mockReset();
    mocks.readiness.mockResolvedValue({ state: "not_template" });
  });
  it.each(["save-as", "clone"])(
    "copies the accepted definition through %s without creating a blank source",
    async (action) => {
      mocks.get.mockResolvedValue(document);
      mocks.readiness.mockResolvedValue({ state: "not_template" });
      mocks.copy.mockResolvedValue({
        ...document,
        path: "workflows/new-copy.workflow.wflow",
        storage_revision: 1,
        definition_revision: 1,
      });
      const open = vi.fn();
      const user = userEvent.setup();
      renderPage({ onOpenWorkflow: open });
      await screen.findByTestId("workflow-file-menu");
      await user.click(screen.getByTestId("workflow-file-menu"));
      await user.click(screen.getByTestId(`workflow-file-${action}`));
      await user.type(screen.getByLabelText("Workflow name"), "New copy");
      await user.click(screen.getByTestId("workflow-file-create"));
      await waitFor(() =>
        expect(open).toHaveBeenCalledWith("workflows/new-copy.workflow.wflow"),
      );
      expect(mocks.copy).toHaveBeenCalledExactlyOnceWith(
        "session-1",
        document.path,
        "workflows/new-copy.workflow.wflow",
        document.storage_digest,
      );
      expect(mocks.create).not.toHaveBeenCalled();
    },
  );
  it("requires saving local edits before offering a definition copy", async () => {
    mocks.get.mockResolvedValue(document);
    renderPage({ onOpenWorkflow: vi.fn() });
    await screen.findByTestId("workflow-file-menu");
    await userEvent.click(screen.getByTestId("fixture-edit"));
    expect(screen.getByTestId("workflow-file-save-as")).toBeDisabled();
    expect(screen.getByTestId("workflow-file-clone")).toBeDisabled();
    expect(mocks.copy).not.toHaveBeenCalled();
  });
});
