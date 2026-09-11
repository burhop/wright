import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../services/workflow-drafts", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("../../services/workflow-drafts")>();
  return {
    ...actual,
    createWorkflowDraft: vi.fn(),
    readWorkflowDraft: vi.fn(),
  };
});

import fixture from "../../../../../packages/core/tests/fixtures/workflow_drafts/representative-workflow.json";
import {
  createWorkflowDraft,
  decodeWorkflowDraft,
  readWorkflowDraft,
} from "../../services/workflow-drafts";
import WorkflowComposerPage from "./WorkflowComposerPage";

const createDraft = vi.mocked(createWorkflowDraft);
const readDraft = vi.mocked(readWorkflowDraft);

describe("WorkflowComposerPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.history.replaceState({}, "", "/workflow-composer");
  });

  it("creates a separate working draft and enters the authority-labeled composer", async () => {
    const user = userEvent.setup();
    const draft = decodeWorkflowDraft(fixture);
    createDraft.mockResolvedValue({ draft, etag: '"draft-etag"' });
    render(<WorkflowComposerPage />);

    expect(
      screen.getByRole("heading", { name: "Create an empty draft" }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/released Process Definition remains read-only/i),
    ).toBeInTheDocument();
    await user.click(screen.getByTestId("workflow-composer-create"));

    expect(
      await screen.findByTestId("workflow-composer-canvas"),
    ).toBeInTheDocument();
    expect(createDraft).toHaveBeenCalledWith(
      "Product definition draft",
      "Capture, define, review, and release one product definition.",
    );
    expect(screen.getByLabelText("Working draft authority")).toHaveTextContent(
      "Not released · Not executable",
    );
    expect(new URLSearchParams(window.location.search).get("draft")).toBe(
      draft.draft_id,
    );
  });

  it("reopens a draft named in the URL instead of creating another", async () => {
    const draft = decodeWorkflowDraft(fixture);
    readDraft.mockResolvedValue({ draft, etag: '"draft-etag"' });
    window.history.replaceState(
      {},
      "",
      `/workflow-composer?draft=${draft.draft_id}`,
    );

    render(<WorkflowComposerPage />);

    expect(
      await screen.findByTestId("workflow-composer-text"),
    ).toBeInTheDocument();
    expect(readDraft).toHaveBeenCalledWith(draft.draft_id);
    expect(createDraft).not.toHaveBeenCalled();
  });
});
