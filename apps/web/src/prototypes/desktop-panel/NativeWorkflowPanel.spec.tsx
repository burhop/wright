import { afterEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import type { ComponentProps } from "react";
import { NativeWorkflowPanel } from "./NativeWorkflowPanel";
import { NativeEditorDraftClient } from "./native-editor-draft-client";
import { NativeSourceClient } from "./native-source-client";
import type WorkflowRecoveryConcept from "../workflow-recovery/WorkflowRecoveryConcept";

vi.mock("../workflow-recovery/WorkflowRecoveryConcept", () => ({
  default: (
    props: NonNullable<ComponentProps<typeof WorkflowRecoveryConcept>>,
  ) => (
    <section aria-label="Shared editor">
      {props.fileActions}
      <button onClick={() => props.onUnsavedChange?.(true)}>Edit source</button>
    </section>
  ),
}));
afterEach(cleanup);

const initial = {
  workspace_id: "workspace",
  path: "workflows/inspection.workflow.wflow",
  source: "accepted source",
  storage_digest: "a".repeat(64),
  storage_revision: 1,
  definition_revision: 1,
  size_bytes: 15,
  metadata_authority: "wright_host" as const,
};
const scope = {
  workspaceId: "workspace",
  sessionId: "session",
  path: initial.path,
};
function setup(
  extra: Partial<ComponentProps<typeof NativeWorkflowPanel>> = {},
) {
  const onOpenWorkingView = vi.fn(),
    onOpenTransfer = vi.fn();
  render(
    <NativeWorkflowPanel
      initial={initial}
      client={new NativeSourceClient(scope, vi.fn())}
      workspaceName="Engineering"
      onOpenWorkingView={onOpenWorkingView}
      onOpenTransfer={onOpenTransfer}
      {...extra}
    />,
  );
  return { onOpenWorkingView, onOpenTransfer };
}

it("keeps source identity and transfer accessible on demand, with keyboard return", () => {
  const { onOpenTransfer } = setup();
  expect(screen.getByRole("button", { name: "Run and results" })).toBeVisible();
  expect(screen.getByText(initial.path)).not.toBeVisible();
  fireEvent.click(screen.getByText("Workflow details"));
  expect(screen.getByText(initial.path)).toBeVisible();
  fireEvent.click(
    screen.getByRole("button", { name: "Export / import workflow" }),
  );
  expect(onOpenTransfer).toHaveBeenCalledOnce();
  fireEvent.keyDown(screen.getByText("Workflow details"), { key: "Escape" });
  expect(screen.getByText(initial.path)).not.toBeVisible();
  expect(screen.getByText("Workflow details")).toHaveFocus();
});

it("retains edit guards when transfer is behind a disclosure", () => {
  const { onOpenWorkingView, onOpenTransfer } = setup({
    transferDisabled: true,
  });
  fireEvent.click(screen.getByRole("button", { name: "Edit source" }));
  expect(
    screen.getByRole("button", { name: "Run and results" }),
  ).toBeDisabled();
  fireEvent.click(screen.getByText("Workflow details"));
  expect(
    screen.getByRole("button", { name: "Export / import workflow" }),
  ).toBeDisabled();
  expect(onOpenWorkingView).not.toHaveBeenCalled();
  expect(onOpenTransfer).not.toHaveBeenCalled();
});

it("shows draft-read failures outside the closed disclosure without repeating a write", async () => {
  const call = vi.fn().mockRejectedValue(new Error("Disconnected"));
  setup({ draftClient: new NativeEditorDraftClient(scope, call) });
  const alert = await screen.findByRole("alert");
  expect(alert).toBeVisible();
  expect(alert).toHaveTextContent("Saved drafts could not be read");
  expect(screen.getByText(initial.path)).not.toBeVisible();
  expect(call).toHaveBeenCalledExactlyOnceWith("wright_editor_drafts_read", {
    request: {
      workspace_id: "workspace",
      session_id: "session",
      path: initial.path,
      draft_id: null,
    },
  });
});

it.each([false, true])(
  "returns to the canvas only after confirmed draft recovery (failed=%s)",
  async (failed) => {
    const row = {
      draft_id: "preserved",
      updated_at: 123,
      base_matches_current: true,
      base_storage_digest: initial.storage_digest,
      matches_accepted: false,
      accepted_checkpoint: false,
    };
    const read = failed
      ? vi.fn().mockRejectedValue(new Error("Draft unavailable"))
      : vi.fn().mockResolvedValue({
          ...row,
          source: "preserved draft",
          applied_source: initial.source,
          layout: null,
          view: "code",
        });
    const save = vi.fn(),
      resume = vi.fn();
    const draftClient = {
      list: vi.fn().mockResolvedValue([row]),
      read,
      save,
      resume,
      requiresRead: false,
    } as unknown as NativeEditorDraftClient;
    setup({ draftClient });
    fireEvent.click(screen.getByText("Workflow details"));
    fireEvent.click(await screen.findByText(/Saved drafts checked/));
    fireEvent.click(
      screen.getByRole("button", { name: "Resume draft" }),
    );
    const details = screen.getByText("Workflow details").closest("details");
    if (failed) {
      expect(await screen.findByRole("alert")).toHaveTextContent(
        "Draft unavailable",
      );
      expect(details).toHaveAttribute("open");
      expect(resume).not.toHaveBeenCalled();
    } else {
      await waitFor(() =>
        expect(
          screen.getByText("Workflow details").closest("details"),
        ).not.toHaveAttribute("open"),
      );
      expect(screen.getByText("Workflow details")).toHaveFocus();
      expect(resume).toHaveBeenCalledOnce();
    }
    expect(save).not.toHaveBeenCalled();
  },
);
