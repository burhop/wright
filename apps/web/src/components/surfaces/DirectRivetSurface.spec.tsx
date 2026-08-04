import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { DirectRivetSurface } from "./DirectRivetSurface";

const workflow = {
  workflow_id: "workflow-1",
  slug: "rivet",
  revision: 1,
  etag: "etag-1",
  review_state: null,
  reviewer: null,
  reviewed_at: null,
};

const document = {
  ...workflow,
  project: "version: 4\ndata:\n  graphs: {}\n",
  datasets: {},
};

const mocks = vi.hoisted(() => ({
  listRivetWorkflowOperations: vi.fn(),
  readRivetWorkflow: vi.fn(),
  createBlankRivetWorkflow: vi.fn(),
  saveRivetWorkflow: vi.fn(),
  lintRivetWorkflowGraph: vi.fn(),
  runRivetWorkflow: vi.fn(),
}));

vi.mock("../../services/workspace-service", () => ({
  workspaceService: mocks,
}));

describe("DirectRivetSurface", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("opens and saves Rivet workflows through Wright workspace APIs", async () => {
    const user = userEvent.setup();
    const loaded = vi.fn();
    mocks.listRivetWorkflowOperations.mockResolvedValue([workflow]);
    mocks.readRivetWorkflow.mockResolvedValue(document);
    mocks.saveRivetWorkflow.mockResolvedValue({ ...workflow, revision: 2 });

    render(
      <DirectRivetSurface
        url="http://127.0.0.1:9180/?wrightMinimal=1&workflow=rivet"
        sessionId="session-1"
        initialSlug="rivet"
        onOpenInBrowser={vi.fn()}
        onWorkflowLoaded={loaded}
      />,
    );

    expect(await screen.findByText("rivet.rivet-project")).toBeVisible();
    expect(mocks.readRivetWorkflow).toHaveBeenCalledWith("session-1", "rivet");
    expect(loaded).toHaveBeenCalledWith(expect.objectContaining({ slug: "rivet" }));

    await user.click(screen.getByTestId("direct-rivet-save-workspace"));

    await waitFor(() =>
      expect(mocks.saveRivetWorkflow).toHaveBeenCalledWith(
        "session-1",
        "rivet",
        1,
        document.project,
        {},
      ),
    );
  });

  it("creates a blank Rivet workflow in the active workspace", async () => {
    const user = userEvent.setup();
    const loaded = vi.fn();
    const createdWorkflow = {
      ...workflow,
      workflow_id: "workflow-2",
      slug: "untitled-workflow",
      etag: "etag-2",
    };
    const createdDocument = {
      ...createdWorkflow,
      project: "version: 4\ndata:\n  graphs: {}\n",
      datasets: {},
    };
    mocks.listRivetWorkflowOperations
      .mockResolvedValueOnce([workflow])
      .mockResolvedValueOnce([workflow, createdWorkflow]);
    mocks.readRivetWorkflow
      .mockResolvedValueOnce(document)
      .mockResolvedValueOnce(createdDocument);
    mocks.createBlankRivetWorkflow.mockResolvedValue(createdWorkflow);

    render(
      <DirectRivetSurface
        url="http://127.0.0.1:9180/?wrightMinimal=1&workflow=rivet"
        sessionId="session-1"
        initialSlug="rivet"
        onOpenInBrowser={vi.fn()}
        onWorkflowLoaded={loaded}
      />,
    );

    expect(await screen.findByText("rivet.rivet-project")).toBeVisible();
    await user.click(screen.getByTestId("direct-rivet-new-workspace"));

    await waitFor(() =>
      expect(mocks.createBlankRivetWorkflow).toHaveBeenCalledWith("session-1"),
    );
    expect(mocks.readRivetWorkflow).toHaveBeenLastCalledWith(
      "session-1",
      "untitled-workflow",
    );
    expect(loaded).toHaveBeenLastCalledWith(
      expect.objectContaining({ slug: "untitled-workflow" }),
    );
  });
});
