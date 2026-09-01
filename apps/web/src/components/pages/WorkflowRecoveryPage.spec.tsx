import { StrictMode } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ get: vi.fn(), create: vi.fn(), update: vi.fn() }));

vi.mock("../../services/workspace-service", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../services/workspace-service")>();
  return {
    ...actual,
    workspaceService: {
      getWorkspaceWorkflowSource: mocks.get,
      createWorkspaceWorkflowSource: mocks.create,
      updateWorkspaceWorkflowSource: mocks.update,
    },
  };
});

vi.mock("../../prototypes/workflow-recovery/WorkflowRecoveryConcept", async () => {
  const { useState } = await import("react");
  function MockWorkflowRecoveryConcept(props: {
    surfaceState?: string;
    workflowSource?: string;
    definitionRevision?: number;
    storageDigest?: string;
    workflowFilePath?: string;
    onSave?: (source: string) => Promise<unknown>;
    onReadStoredSource?: () => Promise<{ source: string }>;
    onReloadStoredSource?: () => Promise<void>;
  }) {
    const [initialSource] = useState(props.workflowSource);
    const [readSource, setReadSource] = useState("");
    return <div data-testid="workflow-editor-fixture" data-state={props.surfaceState ?? "ready"} data-source={initialSource} data-current-source={props.workflowSource} data-read-source={readSource} data-definition-revision={props.definitionRevision} data-storage-digest={props.storageDigest} data-path={props.workflowFilePath}>
      {props.onSave && <button type="button" data-testid="fixture-save" onClick={() => void props.onSave?.("updated workflow source")}>Save fixture</button>}
      {props.onReadStoredSource && <button type="button" data-testid="fixture-read" onClick={() => void props.onReadStoredSource?.().then((stored) => setReadSource(stored.source))}>Read stored fixture</button>}
      {props.onReloadStoredSource && <button type="button" data-testid="fixture-reload" onClick={() => void props.onReloadStoredSource?.()}>Reload stored fixture</button>}
    </div>;
  }
  return {
    default: MockWorkflowRecoveryConcept,
  };
});

import {
  WorkspaceWorkflowSourceNotFoundError,
  type WorkspaceWorkflowSourceDocument,
} from "../../services/workspace-service";
import { initialWorkflow } from "../../prototypes/workflow-recovery/model";
import { formatRecoveryAuthoringSource } from "../../prototypes/workflow-recovery/recovery-authoring";
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

function renderPage({ strict = false }: { strict?: boolean } = {}) {
  const page = <WorkflowRecoveryPage workspaceId="workspace-1" sessionId="session-1" workspaceName="Bracket Program" workflowFilePath="/workflows/mounting-bracket.workflow.wflow" />;
  return render(strict ? <StrictMode>{page}</StrictMode> : page);
}

describe("workspace workflow page", () => {
  beforeEach(() => {
    mocks.get.mockReset();
    mocks.create.mockReset();
    mocks.update.mockReset();
  });

  it("loads the exact workspace file and passes host metadata to the editor", async () => {
    mocks.get.mockResolvedValue(document);
    renderPage();
    expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute("data-state", "loading");
    await waitFor(() => expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute("data-state", "ready"));
    expect(mocks.get).toHaveBeenCalledWith("session-1", document.path);
    expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute("data-source", document.source);
    expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute("data-definition-revision", "2");
    expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute("data-storage-digest", document.storage_digest);
    expect(screen.getByTestId("workflow-workspace-context")).toHaveTextContent(/Bracket Program\s*\/\s*Workflows\s*\/\s*mounting-bracket\.workflow\.wflow/);
  });

  it("automatically creates the default workflow once when the file is missing, including in StrictMode", async () => {
    mocks.get.mockRejectedValue(new WorkspaceWorkflowSourceNotFoundError());
    mocks.create.mockResolvedValue(document);
    renderPage({ strict: true });

    expect(await screen.findByTestId("fixture-save")).toBeVisible();
    await waitFor(() => expect(mocks.create).toHaveBeenCalledOnce());
    expect(mocks.create).toHaveBeenCalledWith(
      "session-1",
      document.path,
      formatRecoveryAuthoringSource(initialWorkflow).text,
    );
    expect(mocks.get).toHaveBeenCalledOnce();
  });

  it("opens the stored workflow when automatic creation loses a race", async () => {
    mocks.get
      .mockRejectedValueOnce(new WorkspaceWorkflowSourceNotFoundError())
      .mockResolvedValueOnce(document);
    mocks.create.mockRejectedValue(new Error("Unable to create this workflow file in the workspace."));

    renderPage();

    expect(await screen.findByTestId("fixture-save")).toBeVisible();
    expect(mocks.create).toHaveBeenCalledOnce();
    expect(mocks.get).toHaveBeenCalledTimes(2);
    expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute("data-source", document.source);
  });

  it("fails closed after a real create failure and retries the complete bootstrap", async () => {
    mocks.get
      .mockRejectedValueOnce(new WorkspaceWorkflowSourceNotFoundError())
      .mockRejectedValueOnce(new WorkspaceWorkflowSourceNotFoundError())
      .mockRejectedValueOnce(new WorkspaceWorkflowSourceNotFoundError());
    mocks.create
      .mockRejectedValueOnce(new Error("The path cannot be written."))
      .mockResolvedValueOnce(document);

    renderPage();

    expect(await screen.findByTestId("workflow-source-load-error")).toHaveTextContent(
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
    mocks.get.mockResolvedValue({ ...document, workspace_id: "workspace-elsewhere" });
    renderPage();

    expect(await screen.findByTestId("workflow-source-load-error")).toHaveTextContent(
      "different workspace or path",
    );
    expect(screen.queryByTestId("fixture-save")).not.toBeInTheDocument();
    expect(mocks.create).not.toHaveBeenCalled();
  });

  it("saves through compare-and-swap and rebases the next save to the returned stored identity", async () => {
    mocks.get.mockResolvedValue(document);
    mocks.update
      .mockResolvedValueOnce({ ...document, storage_revision: 5, storage_digest: "b".repeat(64), definition_revision: 3, source: "updated workflow source" })
      .mockResolvedValueOnce({ ...document, storage_revision: 6, storage_digest: "c".repeat(64), definition_revision: 4, source: "updated workflow source" });
    renderPage();
    await userEvent.click(await screen.findByTestId("fixture-save"));
    await waitFor(() => expect(mocks.update).toHaveBeenCalledWith("session-1", document.path, "updated workflow source", 4, document.storage_digest, true));
    await userEvent.click(screen.getByTestId("fixture-save"));
    await waitFor(() => expect(mocks.update).toHaveBeenCalledTimes(2));
    expect(mocks.update).toHaveBeenLastCalledWith("session-1", document.path, "updated workflow source", 5, "b".repeat(64), true);
  });

  it("reads for comparison without changing the editor and remounts only after explicit reload", async () => {
    const stored = { ...document, storage_revision: 9, storage_digest: "d".repeat(64), definition_revision: 7, source: "workflow stored_version\nend\n" };
    mocks.get
      .mockResolvedValueOnce(document)
      .mockResolvedValueOnce(stored)
      .mockResolvedValueOnce(stored);
    renderPage();

    await screen.findByTestId("workflow-editor-fixture");
    await waitFor(() => expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute("data-state", "ready"));
    const editor = screen.getByTestId("workflow-editor-fixture");
    expect(editor).toHaveAttribute("data-source", document.source);
    await userEvent.click(screen.getByTestId("fixture-read"));
    await waitFor(() => expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute("data-read-source", stored.source));
    expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute("data-source", document.source);

    await userEvent.click(screen.getByTestId("fixture-reload"));
    await waitFor(() => expect(screen.getByTestId("workflow-editor-fixture")).toHaveAttribute("data-source", stored.source));
    expect(mocks.get).toHaveBeenNthCalledWith(2, "session-1", document.path);
    expect(mocks.get).toHaveBeenNthCalledWith(3, "session-1", document.path);
  });
});
