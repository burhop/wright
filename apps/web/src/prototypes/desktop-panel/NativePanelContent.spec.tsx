// Presentation routing checks with stub surfaces; not native desktop acceptance.
import { useState } from "react";
import type { ComponentProps } from "react";
import { afterEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import type { WorkspaceWorkflowSourceDocument } from "../../services/workspace-service";
import type { NativeWorkflowPanel } from "./NativeWorkflowPanel";
import type { NativeProcessPanel } from "./NativeProcessPanel";
import { NativePanelContent } from "./NativePanelContent";
import { NativeSourceClient } from "./native-source-client";
import type { NativeProcessCall } from "./native-process-client";
import type { NativeTransferCall } from "./native-transfer-client";

const original: WorkspaceWorkflowSourceDocument = {
  workspace_id: "workspace",
  path: "workflows/test.wflow",
  source: "accepted",
  storage_digest: "a".repeat(64),
  storage_revision: 1,
  definition_revision: 1,
  metadata_authority: "wright_host",
  size_bytes: 8,
};
const saved = {
  ...original,
  storage_digest: "b".repeat(64),
  storage_revision: 2,
  source: "new accepted",
};
vi.mock("./NativeWorkflowPanel", () => ({
  NativeWorkflowPanel: (props: ComponentProps<typeof NativeWorkflowPanel>) => {
    const [draft, setDraft] = useState("");
    return (
      <section aria-label="Editor">
        {props.onOpenTransfer && (
          <button
            onClick={props.onOpenTransfer}
            disabled={props.transferDisabled}
          >
            Export / import workflow
          </button>
        )}
        <input
          aria-label="Retained editor state"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
        />
        <button onClick={() => props.onDirty?.(true)}>Unsaved source</button>
        <button
          onClick={() => {
            props.onAccepted?.(saved);
            props.onDirty?.(false);
          }}
        >
          Accepted save
        </button>
        <button
          onClick={props.onOpenWorkingView}
          disabled={!props.onOpenWorkingView}
        >
          Run and results
        </button>
      </section>
    );
  },
}));
vi.mock("./NativeProcessPanel", () => ({
  NativeProcessPanel: (props: ComponentProps<typeof NativeProcessPanel>) => (
    <section aria-label="Working view">
      <button onClick={() => props.onDirty?.(true)}>Uncertain change</button>
      <button onClick={() => props.onDirty?.(false)}>Reconciled</button>
      <button onClick={props.onOpenWorkflow}>Open workflow</button>
      <button onClick={() => props.onRunAttached?.("retained-run")}>
        Attach run
      </button>
      <button
        onClick={() => void props.client.getSnapshot({ runId: props.runId })}
      >
        Read exact run
      </button>
      <span>{props.runId ?? "New preparation"}</span>
    </section>
  ),
}));
afterEach(() => cleanup());

it("opens transfer only for a saved source and keeps editor drafts and run controls guarded", async () => {
  const transferCall = vi.fn<NativeTransferCall>();
  const { read, call, onDirty } = setup({
    transferCall,
    onOpenTransferred: vi.fn(),
  });
  fireEvent.click(screen.getByRole("button", { name: "Unsaved source" }));
  expect(
    screen.getByRole("button", { name: "Export / import workflow" }),
  ).toBeDisabled();
  expect(read).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Accepted save" }));
  read.mockResolvedValue({ content: [], structuredContent: saved });
  fireEvent.click(
    screen.getByRole("button", { name: "Export / import workflow" }),
  );
  await screen.findByRole("dialog", { name: "Export or import a workflow" });
  expect(onDirty).toHaveBeenLastCalledWith(true);
  fireEvent.click(screen.getByRole("button", { name: "Run and results" }));
  expect(screen.queryByRole("region", { name: "Working view" })).toBeNull();
  expect(call).not.toHaveBeenCalled();
  expect(transferCall).not.toHaveBeenCalled();
  fireEvent.click(
    screen.getByRole("button", { name: "Close workflow transfer" }),
  );
  expect(onDirty).toHaveBeenLastCalledWith(false);
});

it("rejects stale transfer source before opening the dialog", async () => {
  const transferCall = vi.fn<NativeTransferCall>();
  const { read, onDirty } = setup({ transferCall, onOpenTransferred: vi.fn() });
  read.mockResolvedValue({ content: [], structuredContent: saved });
  fireEvent.click(
    screen.getByRole("button", { name: "Export / import workflow" }),
  );
  await screen.findByText(/Reload it before transferring/);
  expect(screen.queryByRole("dialog")).toBeNull();
  expect(transferCall).not.toHaveBeenCalled();
  expect(onDirty).toHaveBeenLastCalledWith(false);
});
function setup(extra: Partial<ComponentProps<typeof NativePanelContent>> = {}) {
  const read = vi
    .fn()
    .mockResolvedValue({ content: [], structuredContent: original });
  const sourceClient = new NativeSourceClient(
    {
      workspaceId: original.workspace_id,
      sessionId: "session",
      path: original.path,
    },
    read,
  );
  const call = vi.fn<NativeProcessCall>().mockResolvedValue({
    content: [],
    structuredContent: {
      ok: true,
      document: {
        context: {
          process: {
            workspace_id: original.workspace_id,
            source_path: original.path,
            source_digest: saved.storage_digest,
          },
          generated_at: "2026-10-12T12:00:00Z",
        },
        state: "preparing",
      },
    },
  });
  const onDirty = vi.fn();
  const view = render(
    <NativePanelContent
      initial={original}
      sourceClient={sourceClient}
      call={call}
      sessionId="session"
      workspaceName="Prototype"
      workingViewEnabled
      onDirty={onDirty}
      {...extra}
    />,
  );
  return { read, call, onDirty, ...view };
}
it("preserves editor state and attaches the same run after switching views", async () => {
  const { call } = setup();
  fireEvent.change(screen.getByLabelText("Retained editor state"), {
    target: { value: "undo history marker" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Run and results" }));
  await screen.findByRole("region", { name: "Working view" });
  fireEvent.click(screen.getByRole("button", { name: "Attach run" }));
  fireEvent.click(screen.getByRole("button", { name: "Open workflow" }));
  expect(screen.getByLabelText("Retained editor state")).toHaveValue(
    "undo history marker",
  );
  fireEvent.click(screen.getByRole("button", { name: "Run and results" }));
  await screen.findByText("retained-run");
  expect(call).not.toHaveBeenCalled();
});
it("keeps drafts and uncertain effects in their current surface", async () => {
  const { read, call, onDirty } = setup();
  fireEvent.click(screen.getByRole("button", { name: "Unsaved source" }));
  fireEvent.click(screen.getByRole("button", { name: "Run and results" }));
  expect(read).not.toHaveBeenCalled();
  expect(onDirty).toHaveBeenLastCalledWith(true);
  fireEvent.click(screen.getByRole("button", { name: "Accepted save" }));
  read.mockResolvedValue({ content: [], structuredContent: saved });
  fireEvent.click(screen.getByRole("button", { name: "Run and results" }));
  await screen.findByRole("region", { name: "Working view" });
  fireEvent.click(screen.getByRole("button", { name: "Uncertain change" }));
  fireEvent.click(screen.getByRole("button", { name: "Open workflow" }));
  expect(screen.getByText(/Finish or reconcile/)).toBeVisible();
  expect(screen.getByRole("region", { name: "Working view" })).toBeVisible();
  expect(call).not.toHaveBeenCalled();
});
it("refuses a changed source without rebasing the editor or preparing a run", async () => {
  const { read, call } = setup();
  read.mockResolvedValue({ content: [], structuredContent: saved });
  fireEvent.click(screen.getByRole("button", { name: "Run and results" }));
  await screen.findByText(/saved workflow changed/);
  expect(screen.queryByRole("region", { name: "Working view" })).toBeNull();
  expect(call).not.toHaveBeenCalled();
});
it("binds a fresh preparation to the explicitly saved revision", async () => {
  const { read, call } = setup();
  read.mockResolvedValue({ content: [], structuredContent: saved });
  fireEvent.click(screen.getByRole("button", { name: "Accepted save" }));
  fireEvent.click(screen.getByRole("button", { name: "Run and results" }));
  await screen.findByText("New preparation");
  fireEvent.click(screen.getByRole("button", { name: "Read exact run" }));
  await waitFor(() => expect(call).toHaveBeenCalledTimes(1));
  expect(call.mock.calls[0][1]).toMatchObject({
    operation: "snapshot",
    expected_storage_digest: saved.storage_digest,
    session_id: "session",
    path: original.path,
  });
});
it("does not enable a working view when its runtime capability is absent", () => {
  const { call, read } = setup({ workingViewEnabled: false });
  expect(
    screen.getByRole("button", { name: "Run and results" }),
  ).toBeDisabled();
  expect(call).not.toHaveBeenCalled();
  expect(read).not.toHaveBeenCalled();
});
