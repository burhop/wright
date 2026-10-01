import { StrictMode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import {
  ProcessClientError,
  type FollowUpdate,
  type InputSnapshot,
  type InteractionSnapshot,
  type ProcessClient,
  type Readiness,
  type StartReceipt,
} from "@wright/process-client";
import { CommonProcessView } from "./CommonProcessView";
import {
  createProcessViewRecoveryStore,
  compactInput,
  processViewRequestId,
  type ProcessViewRecovery,
  type ProcessViewRecoveryStore,
} from "../../services/process-view-recovery";

const hash = "a".repeat(64);
const process = {
  workspace_id: "workspace",
  source_path: "workflows/example.wflow",
  source_digest: hash,
};
const input: InputSnapshot = {
  process,
  snapshot_id: "inputs-one",
  digest: hash,
  created_at: "2026-09-30T12:00:00Z",
  bindings: [],
};
const readiness: Readiness = {
  process,
  assessment_id: "ready-one",
  assessed_at: input.created_at,
  input_digest: hash,
  state: "ready",
};
const receipt: StartReceipt = {
  process,
  request_id: "request-one",
  run_id: "run-one",
  input_snapshot_id: input.snapshot_id,
  input_digest: hash,
  payload_digest: hash,
  principal_id: "native-actor",
  created_at: input.created_at,
};
const initial: InteractionSnapshot = {
  context: { process, generated_at: input.created_at, cursor: 0 },
  state: "preparing",
  inputs: [
    {
      input_id: "prompt",
      block_id: "intent",
      port_id: "out",
      title: "Design request",
      value_schema: { type: "string" },
      required: true,
    },
  ],
  actions: [
    {
      action_id: "start",
      operation: "start",
      title: "Start process",
      enabled: false,
    },
  ],
};
const prepared: InteractionSnapshot = {
  ...initial,
  state: "ready",
  readiness,
  context: {
    ...initial.context,
    input_snapshot_id: input.snapshot_id,
    input_digest: hash,
  },
  actions: [
    {
      action_id: "start",
      operation: "start",
      title: "Start process",
      enabled: true,
      subject_digest: hash,
    },
  ],
};
const running: InteractionSnapshot = {
  ...prepared,
  state: "running",
  context: { ...prepared.context, run_id: "run-one" },
  actions: [
    {
      action_id: "cancel",
      operation: "cancel",
      title: "Cancel this run",
      enabled: true,
    },
  ],
};
function fixture() {
  const client: ProcessClient = {
    process,
    getSnapshot: vi.fn(async (options) =>
      options?.inputSnapshotId ? prepared : initial,
    ),
    setInputs: vi.fn(async (bindings) => ({ ...input, bindings })),
    checkReadiness: vi.fn(async () => readiness),
    start: vi.fn(async (_input, requestId) => ({
      ...receipt,
      request_id: requestId,
    })),
    attach: vi.fn(async () => running),
    follow: vi.fn(async function* ({ signal }): AsyncGenerator<FollowUpdate> {
      yield { type: "snapshot", snapshot: running };
      yield { type: "connection", state: "connected", attempt: 0 };
      if (signal?.aborted) return;
      await new Promise<void>((resolve) =>
        signal?.addEventListener("abort", () => resolve(), { once: true }),
      );
    }),
    respond: vi.fn(async () => {
      throw new Error("not enabled");
    }),
    decide: vi.fn(async () => {
      throw new Error("not enabled");
    }),
    requestAction: vi.fn(async () => {
      throw new Error("not enabled");
    }),
    cancel: vi.fn(async (runId, requestId) => ({
      run_id: runId,
      request_id: requestId,
      state: "cancellation_requested" as const,
    })),
    getRepresentation: vi.fn(
      async () => new Blob(["exact output"], { type: "text/plain" }),
    ),
    navigate: vi.fn(async () => undefined),
  };
  let saved: ProcessViewRecovery | null = null;
  const store: ProcessViewRecoveryStore = {
    read: vi.fn(() => saved),
    write: vi.fn((value) => {
      saved = value;
    }),
    clear: vi.fn(() => {
      saved = null;
    }),
  };
  return { client, store, saved: () => saved };
}
async function prepareView(
  client: ProcessClient,
  store: ProcessViewRecoveryStore,
) {
  const view = render(
    <CommonProcessView
      client={client}
      sessionId="session"
      recoveryStore={store}
    />,
  );
  await screen.findByLabelText("Design request (required)");
  fireEvent.change(screen.getByLabelText("Design request (required)"), {
    target: { value: "Create a small fixture" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Prepare and check inputs" }),
  );
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Start process" })).toBeEnabled(),
  );
  return view;
}
function deferred<T>() {
  let resolve!: (value: T) => void, reject!: (reason: unknown) => void;
  const promise = new Promise<T>((yes, no) => {
    resolve = yes;
    reject = no;
  });
  return { promise, resolve, reject };
}
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe("common process preparation and authority", () => {
  it("reads on mount without preparing, starting, reviewing or cancelling", async () => {
    const { client, store } = fixture();
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
      />,
    );
    await screen.findByLabelText("Design request (required)");
    expect(client.getSnapshot).toHaveBeenCalledTimes(1);
    for (const mutation of [
      client.setInputs,
      client.start,
      client.cancel,
      client.respond,
      client.decide,
      client.requestAction,
    ])
      expect(mutation).not.toHaveBeenCalled();
    expect(
      screen.getByRole("button", { name: "Start process" }),
    ).toBeDisabled();
  });
  it("checks the saved input overlay before the explicit start and records recovery before submission", async () => {
    const { client, store, saved } = fixture();
    await prepareView(client, store);
    expect(client.setInputs).toHaveBeenCalledWith([
      {
        kind: "value",
        input_id: "prompt",
        provenance: "supplied",
        value: "Create a small fixture",
      },
    ]);
    expect(client.checkReadiness).toHaveBeenCalledTimes(1);
    expect(saved()?.input.bindings).toBeUndefined();
    vi.mocked(client.start).mockImplementationOnce(
      async (_input, requestId) => {
        expect(saved()?.start?.requestId).toBe(requestId);
        return { ...receipt, request_id: requestId };
      },
    );
    fireEvent.click(screen.getByRole("button", { name: "Start process" }));
    await screen.findByRole("button", { name: "Cancel this run" });
    expect(saved()?.start?.receipt?.run_id).toBe("run-one");
    expect(client.start).toHaveBeenCalledTimes(1);
    expect(client.follow).toHaveBeenCalledWith(
      expect.objectContaining({ runId: "run-one" }),
    );
    expect(screen.getByLabelText("Design request (required)")).toBeDisabled();
  });
  it("invalidates readiness as soon as a prepared value is edited, without changing accepted source", async () => {
    const { client, store } = fixture();
    await prepareView(client, store);
    fireEvent.change(screen.getByLabelText("Design request (required)"), {
      target: { value: "A different size" },
    });
    expect(
      screen.getByRole("button", { name: "Start process" }),
    ).toBeDisabled();
    expect(screen.getByText("Readiness has not been checked")).toBeVisible();
    expect(store.clear).toHaveBeenCalled();
    expect(client.start).not.toHaveBeenCalled();
  });
  it("preserves a supplied false value and explicitly reports downstream unresolved input", async () => {
    const { client, store } = fixture();
    const withFalse = {
      ...initial,
      inputs: [
        {
          ...initial.inputs![0],
          title: "Cooling enabled",
          value_schema: { type: "boolean" },
          current_value: { kind: "value", input_id: "prompt", value: false },
        },
      ],
    } satisfies InteractionSnapshot;
    const blocked = {
      ...readiness,
      state: "blocked",
      reasons: [
        {
          code: "INPUT_REQUIRED",
          message: "A later step needs a destination.",
          correction: "Configure the destination before starting.",
        },
      ],
    } satisfies Readiness;
    vi.mocked(client.checkReadiness).mockResolvedValue(blocked);
    vi.mocked(client.getSnapshot).mockImplementation(async (options) =>
      options?.inputSnapshotId
        ? {
            ...withFalse,
            context: prepared.context,
            readiness: blocked,
          }
        : withFalse,
    );
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
      />,
    );
    await screen.findByLabelText("Cooling enabled (required)");
    fireEvent.click(
      screen.getByRole("button", { name: "Prepare and check inputs" }),
    );
    await waitFor(() => expect(client.checkReadiness).toHaveBeenCalledTimes(1));
    expect(client.setInputs).toHaveBeenCalledWith([
      { kind: "value", input_id: "prompt", value: false },
    ]);
    await screen.findByText("A later step needs a destination.");
    expect(
      screen.getByRole("button", { name: "Start process" }),
    ).toBeDisabled();
    expect(client.start).not.toHaveBeenCalled();
  });
  it("expires readiness while idle and requires a fresh assessment", async () => {
    vi.useFakeTimers({ toFake: ["Date", "setInterval", "clearInterval"] });
    vi.setSystemTime(new Date("2026-09-30T12:00:00Z"));
    try {
      const { client, store } = fixture();
      const ready = { ...readiness, expires_at: "2026-09-30T12:00:02Z" };
      vi.mocked(client.checkReadiness).mockResolvedValue(ready);
      vi.mocked(client.getSnapshot).mockImplementation(async (options) =>
        options?.inputSnapshotId ? { ...prepared, readiness: ready } : initial,
      );
      await prepareView(client, store);
      act(() => {
        vi.advanceTimersByTime(3000);
      });
      expect(
        screen.getByRole("button", { name: "Start process" }),
      ).toBeDisabled();
      expect(
        screen.getByText("The readiness check has expired."),
      ).toBeVisible();
      expect(screen.getByText("Readiness needs refreshing")).toBeVisible();
    } finally {
      vi.useRealTimers();
    }
  });
  it("does not start when backend permission or exact input subject is absent", async () => {
    const { client, store } = fixture();
    vi.mocked(client.getSnapshot).mockImplementation(async (options) =>
      options?.inputSnapshotId
        ? {
            ...prepared,
            actions: [
              { ...prepared.actions![0], subject_digest: "b".repeat(64) },
            ],
          }
        : initial,
    );
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
      />,
    );
    await screen.findByLabelText("Design request (required)");
    fireEvent.click(
      screen.getByRole("button", { name: "Prepare and check inputs" }),
    );
    await screen.findByText("Ready to start");
    expect(
      screen.getByRole("button", { name: "Start process" }),
    ).toBeDisabled();
    expect(client.start).not.toHaveBeenCalled();
  });
  it("contains late preparation replies when another process is opened", async () => {
    const { client, store } = fixture(),
      pending = deferred<InputSnapshot>();
    vi.mocked(client.setInputs).mockReturnValue(pending.promise);
    const view = render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
      />,
    );
    await screen.findByLabelText("Design request (required)");
    fireEvent.click(
      screen.getByRole("button", { name: "Prepare and check inputs" }),
    );
    const second = fixture();
    second.client = {
      ...second.client,
      process: { ...process, source_path: "workflows/second.wflow" },
    };
    vi.mocked(second.client.getSnapshot).mockResolvedValue({
      ...initial,
      inputs: [{ ...initial.inputs![0], title: "Second process input" }],
    });
    view.rerender(
      <CommonProcessView
        client={second.client}
        sessionId="session"
        recoveryStore={second.store}
      />,
    );
    await screen.findByLabelText("Second process input (required)");
    await act(async () => {
      pending.resolve(input);
    });
    expect(store.write).not.toHaveBeenCalled();
    expect(client.checkReadiness).not.toHaveBeenCalled();
    expect(
      screen.queryByLabelText("Design request (required)"),
    ).not.toBeInTheDocument();
  });
  it("shows uploading progress and prevents preparation until selected files are ready", async () => {
    const { client, store } = fixture();
    const upload = deferred<{ artifact_ref: string; sha256: string }>();
    vi.mocked(client.getSnapshot).mockResolvedValue({
      ...initial,
      inputs: [
        {
          ...initial.inputs![0],
          title: "Reference image",
          binding_kind: "file",
        },
      ],
    });
    const create = vi
      .spyOn(URL, "createObjectURL")
      .mockReturnValue("blob:reference");
    vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
        onUpload={() => upload.promise}
      />,
    );
    await screen.findByLabelText("Reference image (required)");
    fireEvent.change(screen.getByLabelText("Reference image (required)"), {
      target: {
        files: [new File(["image"], "reference.png", { type: "image/png" })],
      },
    });
    expect(
      screen.getByRole("button", { name: "Prepare and check inputs" }),
    ).toBeDisabled();
    expect(
      screen.getByAltText("Selected reference: reference.png"),
    ).toBeVisible();
    expect(create).toHaveBeenCalled();
    await act(async () => {
      upload.resolve({ artifact_ref: "inputs/reference.png", sha256: hash });
    });
    expect(
      screen.getByRole("button", { name: "Prepare and check inputs" }),
    ).toBeEnabled();
    fireEvent.click(
      screen.getByRole("button", { name: "Prepare and check inputs" }),
    );
    await waitFor(() => expect(client.setInputs).toHaveBeenCalled());
    expect(vi.mocked(client.setInputs).mock.calls[0][0][0]).toMatchObject({
      kind: "file",
      reference: { sha256: hash },
    });
  });
  it("preserves usable read-only and missing-capability fallback", async () => {
    const { client, store } = fixture();
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
        readOnly
      />,
    );
    await screen.findByLabelText("Design request (required)");
    expect(screen.getByLabelText("Design request (required)")).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Prepare and check inputs" }),
    ).toBeDisabled();
    expect(screen.getByRole("button", { name: "Open process" })).toBeDisabled();
    expect(
      screen.getByText(/Representation previews are unavailable/),
    ).toBeVisible();
    expect(client.start).not.toHaveBeenCalled();
  });
});

describe("common process request recovery and observer lifetime", () => {
  it("keeps exact-request recovery available even when the source read fails", async () => {
    const { client, store } = fixture();
    store.write({
      version: "1",
      input: compactInput(input),
      start: { requestId: receipt.request_id },
    });
    vi.mocked(client.getSnapshot).mockRejectedValue(
      new ProcessClientError({
        code: "SOURCE_CHANGED",
        message: "The source has changed.",
        correction: "Open the accepted source.",
      }),
    );
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
      />,
    );
    await screen.findByText("The source has changed.");
    fireEvent.click(
      screen.getByRole("button", { name: "Reconcile start request" }),
    );
    await screen.findByRole("button", { name: "Cancel this run" });
    expect(client.start).toHaveBeenCalledWith(
      compactInput(input),
      receipt.request_id,
    );
  });
  it("blocks preparation rather than overwriting an unreadable recovery record", async () => {
    const { client, store } = fixture();
    vi.mocked(store.read).mockImplementation(() => {
      throw new ProcessClientError({
        code: "UI_INCOMPATIBLE",
        message: "The recovery record is unreadable.",
        correction: "Reconcile the saved run.",
      });
    });
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
      />,
    );
    await screen.findByLabelText("Design request (required)");
    expect(screen.getByLabelText("Design request (required)")).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Prepare and check inputs" }),
    ).toBeDisabled();
    expect(client.setInputs).not.toHaveBeenCalled();
    expect(store.write).not.toHaveBeenCalled();
  });
  it("preserves another view's pending start when an older view edits its draft", async () => {
    const { client, store, saved } = fixture();
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
      />,
    );
    await screen.findByLabelText("Design request (required)");
    store.write({
      version: "1",
      input: compactInput(input),
      start: { requestId: "another-view-start" },
    });
    fireEvent.change(screen.getByLabelText("Design request (required)"), {
      target: { value: "Changed draft" },
    });
    await screen.findByRole("button", { name: "Reconcile start request" });
    expect(saved()?.start?.requestId).toBe("another-view-start");
    expect(store.clear).not.toHaveBeenCalled();
    expect(client.start).not.toHaveBeenCalled();
  });
  it("does not overwrite a start that arrives while input preparation is in flight", async () => {
    const { client, store, saved } = fixture(),
      pending = deferred<InputSnapshot>();
    vi.mocked(client.setInputs).mockReturnValue(pending.promise);
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
      />,
    );
    await screen.findByLabelText("Design request (required)");
    fireEvent.click(
      screen.getByRole("button", { name: "Prepare and check inputs" }),
    );
    store.write({
      version: "1",
      input: compactInput(input),
      start: { requestId: "other-pending-start" },
    });
    await act(async () => {
      pending.resolve({ ...input, snapshot_id: "later-input" });
    });
    expect(saved()?.start?.requestId).toBe("other-pending-start");
    expect(client.checkReadiness).not.toHaveBeenCalled();
    expect(
      screen.getByRole("button", { name: "Reconcile start request" }),
    ).toBeEnabled();
  });
  it("cancels the explicit recorded run with a stable ID even when browser recovery is unavailable", async () => {
    const { client, store } = fixture();
    vi.mocked(store.read).mockImplementation(() => {
      throw new Error("storage unavailable");
    });
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
      />,
    );
    fireEvent.click(
      await screen.findByRole("button", { name: "Cancel this run" }),
    );
    await screen.findByText("Cancellation was requested.");
    expect(client.cancel).toHaveBeenCalledWith(
      "run-one",
      await processViewRequestId("cancel", "run-one"),
    );
  });
  it("does not adopt a cached receipt when an explicit different run is opened", async () => {
    const { client, store } = fixture();
    store.write({
      version: "1",
      input: compactInput(input),
      start: {
        requestId: receipt.request_id,
        receipt: { ...receipt, run_id: "other-run" },
      },
    });
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
      />,
    );
    await screen.findByRole("button", { name: "Cancel this run" });
    expect(client.follow).toHaveBeenCalledWith(
      expect.objectContaining({ runId: "run-one" }),
    );
    expect(client.start).not.toHaveBeenCalled();
  });
  it("blocks submission if the request identity cannot be preserved", async () => {
    const { client, store } = fixture();
    await prepareView(client, store);
    vi.mocked(store.write).mockImplementation(() => {
      throw new Error("storage unavailable");
    });
    fireEvent.click(screen.getByRole("button", { name: "Start process" }));
    await screen.findByRole("alert");
    expect(client.start).not.toHaveBeenCalled();
  });
  it("retains the same start request through lost acknowledgement, close and explicit recovery", async () => {
    const { client, store, saved } = fixture();
    vi.mocked(client.start).mockRejectedValueOnce(
      new ProcessClientError({
        code: "OUTCOME_UNKNOWN",
        message: "The acknowledgement was lost.",
        correction: "Reconcile the exact request.",
      }),
    );
    const view = await prepareView(client, store);
    fireEvent.click(screen.getByRole("button", { name: "Start process" }));
    await screen.findByRole("button", { name: "Reconcile start request" });
    const identity = saved()?.start?.requestId;
    expect(identity).toBeTruthy();
    expect(screen.getByLabelText("Design request (required)")).toBeDisabled();
    view.unmount();
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
      />,
    );
    await screen.findByRole("button", { name: "Reconcile start request" });
    expect(client.start).toHaveBeenCalledTimes(1);
    fireEvent.click(
      screen.getByRole("button", { name: "Reconcile start request" }),
    );
    await screen.findByRole("button", { name: "Cancel this run" });
    expect(vi.mocked(client.start).mock.calls[1][1]).toBe(identity);
    expect(saved()?.start?.receipt?.run_id).toBe("run-one");
  });
  it("does not replay a start on double click or StrictMode attachment", async () => {
    const { client, store } = fixture(),
      accepted = deferred<StartReceipt>();
    vi.mocked(client.start).mockImplementation((_input, requestId) =>
      accepted.promise.then((value) => ({ ...value, request_id: requestId })),
    );
    const view = await prepareView(client, store);
    const button = screen.getByRole("button", { name: "Start process" });
    fireEvent.click(button);
    fireEvent.click(button);
    await waitFor(() => expect(client.start).toHaveBeenCalledTimes(1));
    await act(async () => {
      accepted.resolve(receipt);
    });
    view.unmount();
    render(
      <StrictMode>
        <CommonProcessView
          client={client}
          sessionId="session"
          recoveryStore={store}
        />
      </StrictMode>,
    );
    await screen.findByRole("button", { name: "Cancel this run" });
    expect(client.start).toHaveBeenCalledTimes(1);
    expect(client.cancel).not.toHaveBeenCalled();
  });
  it("persists an accepted receipt after closing while start is in flight", async () => {
    const { client, store, saved } = fixture(),
      accepted = deferred<StartReceipt>();
    vi.mocked(client.start).mockImplementation((_input, requestId) =>
      accepted.promise.then((value) => ({ ...value, request_id: requestId })),
    );
    const view = await prepareView(client, store);
    fireEvent.click(screen.getByRole("button", { name: "Start process" }));
    await waitFor(() => expect(client.start).toHaveBeenCalledTimes(1));
    view.unmount();
    await act(async () => {
      accepted.resolve(receipt);
    });
    expect(saved()?.start?.receipt?.run_id).toBe("run-one");
    expect(client.cancel).not.toHaveBeenCalled();
  });
  it("releases only the observer on close and reopens the exact existing run", async () => {
    const { client, store } = fixture();
    store.write({
      version: "1",
      input: compactInput(input),
      start: { requestId: receipt.request_id, receipt },
    });
    const view = render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
      />,
    );
    await screen.findByRole("button", { name: "Cancel this run" });
    const signal = vi.mocked(client.follow).mock.calls[0][0].signal;
    view.unmount();
    expect(signal?.aborted).toBe(true);
    expect(client.cancel).not.toHaveBeenCalled();
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
      />,
    );
    await screen.findByRole("button", { name: "Cancel this run" });
    expect(client.start).not.toHaveBeenCalled();
    expect(client.setInputs).not.toHaveBeenCalled();
  });
  it("shows cancellation as a request and preserves its identity on a repeat", async () => {
    const { client, store } = fixture();
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
      />,
    );
    fireEvent.click(
      await screen.findByRole("button", { name: "Cancel this run" }),
    );
    await screen.findByText("Cancellation was requested.");
    expect(screen.queryByText("Process cancelled")).not.toBeInTheDocument();
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Cancel this run" }),
      ).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Cancel this run" }));
    await waitFor(() => expect(client.cancel).toHaveBeenCalledTimes(2));
    expect(vi.mocked(client.cancel).mock.calls[0][1]).toBe(
      vi.mocked(client.cancel).mock.calls[1][1],
    );
    expect(client.start).not.toHaveBeenCalled();
  });
  it("reports a disconnected observer without guessing completion or restarting work", async () => {
    const { client, store } = fixture();
    vi.mocked(client.follow).mockImplementation(async function* () {
      yield { type: "snapshot", snapshot: running };
      yield { type: "connection", state: "reconnecting", attempt: 1 };
      throw new ProcessClientError({
        code: "CAPABILITY_UNAVAILABLE",
        message: "The stream is disconnected.",
        correction: "Refresh the saved run.",
      });
    });
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
      />,
    );
    await screen.findByText("The stream is disconnected.");
    expect(screen.getByText(/Live updates are not attached/)).toBeVisible();
    expect(screen.queryByText("Process completed")).not.toBeInTheDocument();
    expect(client.start).not.toHaveBeenCalled();
  });
  it("retains exact result, assessment, evidence and producer navigation", async () => {
    const { client, store } = fixture();
    const artifact = {
      artifact_ref: "outputs/geometry.csv",
      sha256: hash,
      result_id: "result-one",
    };
    vi.mocked(client.follow).mockImplementation(async function* () {
      yield {
        type: "snapshot",
        snapshot: {
          ...running,
          state: "completed",
          actions: [],
          outputs: [
            {
              result_id: "result-one",
              step_id: "geometry",
              port_id: "out",
              role: "geometry",
              title: "Measured geometry",
              representations: [artifact],
              assessments: [
                {
                  assessment_id: "check-one",
                  subject_digest: hash,
                  outcome: "fail",
                  currentness: "current",
                },
              ],
            },
          ],
        },
      };
    });
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
        canNavigate
        canReadRepresentations
      />,
    );
    await screen.findByText("Measured geometry");
    fireEvent.click(screen.getByRole("button", { name: "Open assessment" }));
    expect(client.navigate).toHaveBeenCalledWith({
      kind: "assessment",
      assessment_id: "check-one",
      result_id: "result-one",
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Open producing step" }),
    );
    expect(client.navigate).toHaveBeenCalledWith({
      kind: "block",
      block_id: "geometry",
      result_id: "result-one",
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Open representation" }),
    );
    await screen.findByText("exact output");
    expect(
      screen.getByRole("link", { name: "Download exact file" }),
    ).toHaveAttribute("download", "geometry.csv");
    expect(client.getRepresentation).toHaveBeenCalledWith(artifact);
    expect(screen.getByText("Failed")).toBeVisible();
  });
  it("shows only declared interactions and never submits an invented response", async () => {
    const { client, store } = fixture();
    vi.mocked(client.follow).mockImplementation(async function* () {
      yield {
        type: "snapshot",
        snapshot: {
          ...running,
          state: "waiting_human",
          interactions: [
            {
              checkpoint_id: "checkpoint-one",
              step_id: "review",
              subject_digest: hash,
              kind: "review",
              instructions: "Inspect the measured result.",
            },
          ],
          actions: [
            {
              action_id: "review",
              operation: "review",
              title: "Accept measured result",
              enabled: true,
              checkpoint_id: "checkpoint-one",
              subject_digest: hash,
            },
          ],
        },
      };
    });
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
      />,
    );
    await screen.findByText("Inspect the measured result.");
    expect(
      screen.getByRole("button", { name: "Accept measured result" }),
    ).toBeDisabled();
    expect(client.decide).not.toHaveBeenCalled();
  });
  it("pages exact outputs and rejects a page from a changed snapshot", async () => {
    const { client, store } = fixture();
    vi.mocked(client.getSnapshot).mockResolvedValueOnce({
      ...initial,
      next_page: "page-two",
    });
    vi.mocked(client.getSnapshot).mockResolvedValueOnce({
      ...initial,
      context: { ...initial.context, cursor: 1 },
    });
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
      />,
    );
    fireEvent.click(
      await screen.findByRole("button", {
        name: "Load more process information",
      }),
    );
    await screen.findByText("The results changed while this page was loading.");
    expect(client.start).not.toHaveBeenCalled();
  });
});

describe("native recovery locator storage", () => {
  function storage() {
    const values = new Map<string, string>();
    return {
      getItem: vi.fn((key: string) => values.get(key) ?? null),
      setItem: vi.fn((key: string, value: string) => {
        values.set(key, value);
      }),
      removeItem: vi.fn((key: string) => {
        values.delete(key);
      }),
    };
  }
  it("round-trips compact identities without user input values or credentials", () => {
    const data = storage(),
      store = createProcessViewRecoveryStore(process, "session", data);
    const compact = compactInput({
      ...input,
      bindings: [
        { kind: "value", input_id: "secret", value: "private user data" },
      ],
    });
    store.write({
      version: "1",
      input: compact,
      start: { requestId: receipt.request_id, receipt },
    });
    expect(store.read()?.start?.receipt?.run_id).toBe("run-one");
    expect(data.setItem.mock.calls[0][1]).not.toContain("private user data");
    store.clear();
    expect(store.read()).toBeNull();
  });
  it("isolates sessions, workspaces, source paths and accepted revisions", () => {
    const data = storage();
    createProcessViewRecoveryStore(process, "session", data).write({
      version: "1",
      input: compactInput(input),
    });
    expect(
      createProcessViewRecoveryStore(process, "another-session", data).read(),
    ).toBeNull();
    for (const modified of [
      { ...process, workspace_id: "other" },
      { ...process, source_path: "other.wflow" },
      { ...process, source_digest: "b".repeat(64) },
    ])
      expect(
        createProcessViewRecoveryStore(modified, "session", data).read(),
      ).toBeNull();
  });
  it("rejects malformed, oversized, changed-subject and foreign-run records", () => {
    const data = storage(),
      store = createProcessViewRecoveryStore(process, "session", data);
    const valid: ProcessViewRecovery = {
      version: "1",
      input: compactInput(input),
      start: { requestId: receipt.request_id, receipt },
    };
    store.write(valid);
    const key = data.setItem.mock.calls[0][0];
    for (const value of [
      "bad JSON",
      "x".repeat(16385),
      JSON.stringify({ ...valid, admin: true }),
      JSON.stringify({
        ...valid,
        input: {
          ...input,
          bindings: [
            { kind: "value", input_id: "prompt", value: "inline data" },
          ],
        },
      }),
      JSON.stringify({
        ...valid,
        start: { requestId: "different-request", receipt },
      }),
      JSON.stringify({
        ...valid,
        cancellation: { requestId: "cancel-one", runId: "other-run" },
      }),
    ]) {
      data.setItem(key, value);
      expect(() => store.read()).toThrow(ProcessClientError);
    }
  });
  it("returns a visible failure if storage is unavailable or silently drops the record", () => {
    const data = storage(),
      store = createProcessViewRecoveryStore(process, "session", data);
    data.setItem.mockImplementation(() => {
      throw new Error("quota");
    });
    expect(() =>
      store.write({ version: "1", input: compactInput(input) }),
    ).toThrow(ProcessClientError);
    data.setItem.mockImplementation(() => undefined);
    expect(() =>
      store.write({ version: "1", input: compactInput(input) }),
    ).toThrow(ProcessClientError);
  });
  it("derives stable distinct identities for an immutable preparation and cancellation", async () => {
    const first = await processViewRequestId(
      "start",
      `${input.snapshot_id}:${hash}`,
    );
    expect(
      await processViewRequestId("start", `${input.snapshot_id}:${hash}`),
    ).toBe(first);
    expect(await processViewRequestId("start", `new-input:${hash}`)).not.toBe(
      first,
    );
    expect(await processViewRequestId("cancel", "run-one")).not.toBe(first);
  });
});
