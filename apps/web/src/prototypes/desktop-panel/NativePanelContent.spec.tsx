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
  within,
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
        {props.readOnlyRun && (
          <span>Attached evidence: {props.readOnlyRun.run_id}</span>
        )}
        {props.navigation && (
          <span>
            Focused {props.navigation.resolution.target.block_id ?? "process"}
          </span>
        )}
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
          Run workflow
        </button>
      </section>
    );
  },
}));
vi.mock("./NativeProcessPanel", () => ({
  NativeProcessPanel: (props: ComponentProps<typeof NativeProcessPanel>) => (
    <section aria-label="Working view">
      {props.description && <p>{props.description}</p>}
      {props.onToggleHistory && (
        <button
          onClick={props.onToggleHistory}
          disabled={props.historyDisabled}
        >
          Previous runs
        </button>
      )}
      {props.runHistory}
      {props.runDetails}
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
      <button onClick={props.onPrepareAnother}>Prepare new run</button>
      <button
        onClick={() =>
          void props.client.navigate({
            kind: "block",
            run_id: props.runId,
            block_id: "report",
          })
        }
      >
        Open producing step
      </button>
      <button
        onClick={() =>
          void props.client.navigate({ kind: "run", run_id: props.runId })
        }
      >
        Open run details
      </button>
    </section>
  ),
}));
afterEach(() => cleanup());

it.each([false, true])(
  "keeps the accepted title in workflow history only for its exact source (older=%s)",
  async (older) => {
    const named = {
      ...original,
      path: "workflows/untitled-workflow-test.workflow.wflow",
      source:
        'workflow inspection\n  name: "Inspection demo"\n  purpose: "Measure the saved design before release."\nend',
    };
    const readEvidence = vi.fn().mockResolvedValue({
      content: [],
      structuredContent: {
        workspace_id: named.workspace_id,
        session_id: "session",
        workflow_path: named.path,
        runs: [],
      },
    });
    const { call } = setup({
      initial: named,
      initialProcess: {
        workspace_id: named.workspace_id,
        source_path: named.path,
        source_digest: older ? "c".repeat(64) : named.storage_digest,
      },
      initialView: "working",
      readEvidence,
    });
    if (older)
      expect(
        screen.queryByText("Measure the saved design before release."),
      ).toBeNull();
    else
      expect(
        screen.getByText("Measure the saved design before release."),
      ).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Previous runs" }));
    const history = within(screen.getByRole("region", { name: "Recent runs" }));
    await history.findByText("No recorded runs for this workflow.");
    expect(
      history.getByText(older ? "untitled workflow test" : "Inspection demo"),
    ).toBeVisible();
    if (older) expect(history.queryByText("Inspection demo")).toBeNull();
    expect(readEvidence).toHaveBeenCalledExactlyOnceWith(
      "wright_workflow_history",
      {
        workspace_id: named.workspace_id,
        session_id: "session",
        path: named.path,
      },
    );
    expect(call).not.toHaveBeenCalled();
  },
);

it("reads the selected workflow's history and verifies its exact runtime subject before attaching", async () => {
  const recorded = {
    run_id: "historical-run",
    source_digest: original.storage_digest,
    path: "runs/example/historical-run.json",
    status: "failed",
    started_at: null,
  };
  const readEvidence = vi.fn().mockResolvedValue({
    content: [],
    structuredContent: {
      workspace_id: original.workspace_id,
      session_id: "session",
      workflow_path: original.path,
      runs: [recorded],
    },
  });
  const onLocationChange = vi.fn();
  const { call } = setup({ readEvidence, onLocationChange });
  fireEvent.click(screen.getByRole("button", { name: "Run workflow" }));
  fireEvent.click(await screen.findByRole("button", { name: "Previous runs" }));
  await screen.findByText("failed");
  expect(call).not.toHaveBeenCalled();
  call.mockResolvedValueOnce({
    content: [],
    structuredContent: {
      ok: true,
      document: {
        context: {
          process: {
            workspace_id: original.workspace_id,
            source_path: original.path,
            source_digest: original.storage_digest,
          },
          run_id: "another-run",
          generated_at: "2026-10-20T12:00:00Z",
        },
        state: "failed",
      },
    },
  });
  fireEvent.click(screen.getByRole("button", { name: "Open working view" }));
  await screen.findByRole("alert");
  expect(
    onLocationChange.mock.calls.some(([location]) => location.run_id),
  ).toBe(false);
  call.mockResolvedValueOnce({
    content: [],
    structuredContent: {
      ok: true,
      document: {
        context: {
          process: {
            workspace_id: original.workspace_id,
            source_path: original.path,
            source_digest: original.storage_digest,
          },
          run_id: recorded.run_id,
          generated_at: "2026-10-20T12:00:00Z",
        },
        state: "failed",
      },
    },
  });
  fireEvent.click(screen.getByRole("button", { name: "Open working view" }));
  await waitFor(() =>
    expect(onLocationChange).toHaveBeenLastCalledWith({
      path: original.path,
      source_digest: original.storage_digest,
      view: "working",
      run_id: recorded.run_id,
    }),
  );
  expect(
    call.mock.calls.map(([tool, args]) => [tool, args.operation, args.run_id]),
  ).toEqual([
    ["wright_process_ui_read", "snapshot", recorded.run_id],
    ["wright_process_ui_read", "snapshot", recorded.run_id],
  ]);
});

it("reports the exact attached run across views and removes it from changed-source hints", async () => {
  const onLocationChange = vi.fn();
  const { read, call } = setup({ onLocationChange });
  expect(onLocationChange).toHaveBeenLastCalledWith({
    path: original.path,
    source_digest: original.storage_digest,
    view: "editor",
  });
  fireEvent.click(screen.getByRole("button", { name: "Run workflow" }));
  await screen.findByRole("region", { name: "Working view" });
  fireEvent.click(screen.getByRole("button", { name: "Attach run" }));
  expect(onLocationChange).toHaveBeenLastCalledWith({
    path: original.path,
    source_digest: original.storage_digest,
    view: "working",
    run_id: "retained-run",
  });
  fireEvent.click(screen.getByRole("button", { name: "Open workflow" }));
  expect(onLocationChange).toHaveBeenLastCalledWith({
    path: original.path,
    source_digest: original.storage_digest,
    view: "editor",
    run_id: "retained-run",
  });
  fireEvent.click(screen.getByRole("button", { name: "Accepted save" }));
  expect(onLocationChange).toHaveBeenLastCalledWith({
    path: original.path,
    source_digest: saved.storage_digest,
    view: "editor",
  });
  read.mockResolvedValue({ content: [], structuredContent: saved });
  fireEvent.click(screen.getByRole("button", { name: "Run workflow" }));
  await screen.findByText("New preparation");
  await waitFor(() =>
    expect(onLocationChange).toHaveBeenLastCalledWith({
      path: original.path,
      source_digest: saved.storage_digest,
      view: "working",
    }),
  );
  expect(call).not.toHaveBeenCalled();
});

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
  fireEvent.click(screen.getByRole("button", { name: "Run workflow" }));
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
  fireEvent.click(screen.getByRole("button", { name: "Run workflow" }));
  await screen.findByRole("region", { name: "Working view" });
  fireEvent.click(screen.getByRole("button", { name: "Attach run" }));
  fireEvent.click(screen.getByRole("button", { name: "Open workflow" }));
  expect(screen.getByLabelText("Retained editor state")).toHaveValue(
    "undo history marker",
  );
  fireEvent.click(screen.getByRole("button", { name: "Run workflow" }));
  await screen.findByText("retained-run");
  expect(call).not.toHaveBeenCalled();
});
it("opens the owner-resolved producing block while retaining the exact run and editor", async () => {
  const process = {
    workspace_id: original.workspace_id,
    source_path: original.path,
    source_digest: original.storage_digest,
  };
  const { call } = setup({
    initialProcess: process,
    initialRunId: "retained-run",
  });
  call.mockResolvedValueOnce({
    content: [],
    structuredContent: {
      ok: true,
      document: {
        process,
        target: { kind: "block", run_id: "retained-run", block_id: "report" },
      },
    },
  });
  fireEvent.click(screen.getByRole("button", { name: "Open producing step" }));
  await screen.findByText("Focused report");
  expect(screen.getByRole("region", { name: "Editor" })).toBeVisible();
  expect(call).toHaveBeenCalledExactlyOnceWith(
    "wright_process_ui_read",
    expect.objectContaining({
      operation: "navigation",
      expected_storage_digest: original.storage_digest,
      target: { kind: "block", run_id: "retained-run", block_id: "report" },
    }),
    undefined,
  );
  fireEvent.click(screen.getByRole("button", { name: "Run workflow" }));
  await screen.findByText("retained-run");
  expect(call).toHaveBeenCalledOnce();
});
it("opens exact recorded run details using the existing read-only evidence view", async () => {
  const process = {
    workspace_id: original.workspace_id,
    source_path: original.path,
    source_digest: original.storage_digest,
  };
  const readEvidence = vi.fn().mockResolvedValue({
    content: [],
    structuredContent: {
      workspace_id: original.workspace_id,
      session_id: "session",
      workflow_path: original.path,
      record: {
        path: "runs/demo/retained.json",
        run_id: "retained-run",
        source_digest: original.storage_digest,
        source_matches_current: true,
        status: "completed",
        results: [],
      },
    },
  });
  const { call } = setup({
    initialProcess: process,
    initialRunId: "retained-run",
    readEvidence,
  });
  call.mockResolvedValueOnce({
    content: [],
    structuredContent: {
      ok: true,
      document: {
        process,
        target: { kind: "run", run_id: "retained-run" },
      },
    },
  });
  fireEvent.click(screen.getByRole("button", { name: "Open run details" }));
  await screen.findByText("Recorded state: completed.");
  expect(readEvidence).toHaveBeenCalledExactlyOnceWith(
    "wright_recorded_run_read",
    {
      request: {
        workspace_id: original.workspace_id,
        session_id: "session",
        path: original.path,
        run_id: "retained-run",
        source_digest: original.storage_digest,
      },
    },
  );
  fireEvent.click(screen.getByRole("button", { name: "Close run details" }));
  expect(screen.queryByRole("region", { name: "Run details" })).toBeNull();
  expect(call).toHaveBeenCalledOnce();
});
it("keeps drafts and uncertain effects in their current surface", async () => {
  const { read, call, onDirty } = setup();
  fireEvent.click(screen.getByRole("button", { name: "Unsaved source" }));
  fireEvent.click(screen.getByRole("button", { name: "Run workflow" }));
  expect(read).not.toHaveBeenCalled();
  expect(onDirty).toHaveBeenLastCalledWith(true);
  fireEvent.click(screen.getByRole("button", { name: "Accepted save" }));
  read.mockResolvedValue({ content: [], structuredContent: saved });
  fireEvent.click(screen.getByRole("button", { name: "Run workflow" }));
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
  fireEvent.click(screen.getByRole("button", { name: "Run workflow" }));
  await screen.findByText(/saved workflow changed/);
  expect(screen.queryByRole("region", { name: "Working view" })).toBeNull();
  expect(call).not.toHaveBeenCalled();
});
it("binds a fresh preparation to the explicitly saved revision", async () => {
  const { read, call } = setup();
  read.mockResolvedValue({ content: [], structuredContent: saved });
  fireEvent.click(screen.getByRole("button", { name: "Accepted save" }));
  fireEvent.click(screen.getByRole("button", { name: "Run workflow" }));
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
  expect(screen.getByRole("button", { name: "Run workflow" })).toBeDisabled();
  expect(call).not.toHaveBeenCalled();
  expect(read).not.toHaveBeenCalled();
});

it.each([false, true])(
  "attaches only the exact selected recorder identity (foreign=%s), without execution",
  async (foreign) => {
    const readEvidence = vi.fn().mockResolvedValue({
      content: [],
      structuredContent: {
        workspace_id: original.workspace_id,
        session_id: "session",
        workflow_path: original.path,
        record: {
          run_id: foreign ? "other-run" : "retained-run",
          path: "runs/test/retained-run.json",
          source_digest: original.storage_digest,
          source_matches_current: true,
          status: "completed",
          results: [],
        },
      },
    });
    const { call } = setup({
      initialView: "editor",
      initialRunId: "retained-run",
      readEvidence,
    });
    if (foreign) {
      await screen.findByText(/Selected run evidence could not be read/);
      expect(screen.queryByText(/Attached evidence:/)).toBeNull();
    } else await screen.findByText("Attached evidence: retained-run");
    expect(readEvidence).toHaveBeenCalledExactlyOnceWith(
      "wright_recorded_run_read",
      {
        request: {
          workspace_id: original.workspace_id,
          session_id: "session",
          path: original.path,
          run_id: "retained-run",
          source_digest: original.storage_digest,
        },
      },
    );
    expect(call).not.toHaveBeenCalled();
  },
);

it.each(["matching", "changed", "unavailable"] as const)(
  "rereads saved source before new preparation when source is %s",
  async (condition) => {
    const { read, call } = setup({
      initialRunId: "old-run",
      initialView: "working",
    });
    if (condition === "changed")
      read.mockResolvedValue({ content: [], structuredContent: saved });
    if (condition === "unavailable")
      read.mockRejectedValue(new Error("offline"));
    fireEvent.click(screen.getByRole("button", { name: "Prepare new run" }));
    await waitFor(() => expect(read).toHaveBeenCalledTimes(1));
    if (condition === "matching") {
      await screen.findByText("New preparation");
      expect(screen.queryByText("old-run")).toBeNull();
    } else {
      await screen.findByText(
        condition === "changed"
          ? /saved workflow changed/
          : /could not read the accepted workflow/,
      );
      expect(screen.getByText("old-run")).toBeVisible();
    }
    expect(call).not.toHaveBeenCalled();
  },
);
