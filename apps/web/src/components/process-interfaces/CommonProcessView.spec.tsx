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
  type InteractionResponse,
} from "@wright/process-client";
import { CommonProcessView } from "./CommonProcessView";
import { workspaceService } from "../../services/workspace-service";
import {
  createProcessViewRecoveryStore,
  compactInput,
  processViewRequestId,
  type ProcessViewRecovery,
  type ProcessViewRecoveryStore,
  type ProcessViewMutation,
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
const waitingInput: InteractionSnapshot = {
  ...running,
  state: "waiting_human",
  interactions: [
    {
      checkpoint_id: "input-checkpoint",
      step_id: "choose",
      kind: "input",
      subject_digest: hash,
      instructions: "Choose the comparison to carry forward.",
      state: "waiting",
      response_schema: {
        type: "object",
        properties: { selection: { type: "string", enum: ["a", "b"] } },
        required: ["selection"],
        additionalProperties: false,
      },
    },
  ],
  actions: [
    {
      action_id: "respond-input",
      operation: "respond",
      title: "Submit response",
      enabled: true,
      checkpoint_id: "input-checkpoint",
      subject_digest: hash,
    },
  ],
};
const recordedAnswer: InteractionResponse = {
  response_id: "answer-one",
  workspace_id: "workspace",
  run_id: "run-one",
  checkpoint_id: "input-checkpoint",
  subject_digest: hash,
  schema_digest: hash,
  input_digest: hash,
  value: { selection: "b" },
  actor: "server-actor",
  reason: "Response to declared process input",
  request_id: "filled-by-test",
  created_at: input.created_at,
  digest: hash,
};
function fixture() {
  const client: ProcessClient = {
    process,
    getSnapshot: vi.fn(async (options) =>
      options?.inputSnapshotId ? prepared : initial,
    ),
    setInputs: vi.fn(async (bindings) => ({ ...input, bindings })),
    uploadInput: vi.fn(async () => ({
      artifact_ref: "input.txt",
      sha256: hash,
    })),
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
  let interaction: ProcessViewMutation | null = null;
  const store: ProcessViewRecoveryStore = {
    readInteraction: vi.fn((runId) =>
      interaction?.runId === runId ? interaction : null,
    ),
    writeInteraction: vi.fn((value) => {
      interaction = structuredClone(value);
    }),
    clearInteraction: vi.fn((runId, requestId) => {
      if (
        interaction &&
        interaction.runId === runId &&
        interaction.request.requestId === requestId
      )
        interaction = null;
    }),
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

const waitingReview: InteractionSnapshot = {
  ...waitingInput,
  interactions: [
    {
      checkpoint_id: "review-checkpoint",
      step_id: "review",
      kind: "action",
      subject_digest: hash,
      state: "waiting",
      instructions: "Inspect the exact digital action package.",
      decisions: ["approved", "changes_requested"],
    },
  ],
  actions: [
    {
      action_id: "review-action",
      operation: "review",
      title: "Review action",
      enabled: true,
      checkpoint_id: "review-checkpoint",
      subject_digest: hash,
    },
  ],
};
const approvedReview: InteractionSnapshot = {
  ...waitingReview,
  interactions: [
    {
      ...waitingReview.interactions![0],
      decision: {
        decision: "approved",
        actor: "server-actor",
        request_id: "filled-by-test",
        reason: "Checked the package",
        integration_test: false,
      },
    },
  ],
  actions: [
    {
      action_id: "continue-action",
      operation: "action",
      title: "Continue process",
      enabled: true,
      checkpoint_id: "review-checkpoint",
      subject_digest: hash,
    },
  ],
};
const lostInteraction = () =>
  new ProcessClientError(
    {
      code: "OUTCOME_UNKNOWN",
      message: "Interaction acknowledgement was lost.",
      correction: "Reconcile the saved request.",
    },
    { uncertain: true },
  );

describe("declared review and action controls", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });
  it("requires a changes reason and records only the declared exact review", async () => {
    const { client, store } = fixture();
    let current = waitingReview;
    vi.mocked(client.follow).mockImplementation(async function* () {
      yield { type: "snapshot", snapshot: current };
    });
    vi.mocked(client.decide).mockImplementation(async (request) => {
      current = {
        ...waitingReview,
        interactions: [
          {
            ...waitingReview.interactions![0],
            state: "responded",
            decision: {
              decision: "changes_requested",
              actor: "server-actor",
              request_id: request.requestId,
              reason: request.reason,
              integration_test: false,
            },
          },
        ],
        actions: [],
      };
      return current;
    });
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
      />,
    );
    const reason = await screen.findByLabelText("Review reason");
    expect(
      screen.getByRole("button", { name: "Request changes" }),
    ).toBeDisabled();
    expect(screen.getByRole("button", { name: "Approve" })).toBeEnabled();
    fireEvent.change(reason, {
      target: { value: "Correct the documented units" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Request changes" }));
    await screen.findByText("Review recorded: Changes requested");
    expect(
      screen.getByRole("heading", { name: "Recorded review" }),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Questions and decisions" }),
    ).toBeVisible();
    expect(
      screen.queryByRole("heading", { name: "Your next step" }),
    ).toBeNull();
    expect(
      screen.getByText("Paused at a review or response step"),
    ).toBeVisible();
    expect(screen.getByText(/does not itself revise or restart/)).toBeVisible();
    expect(client.decide).toHaveBeenCalledTimes(1);
    expect(client.decide).toHaveBeenCalledWith(
      expect.objectContaining({
        checkpointId: "review-checkpoint",
        subjectDigest: hash,
        decision: "changes_requested",
        reason: "Correct the documented units",
        requestId: expect.any(String),
      }),
    );
    expect(client.requestAction).not.toHaveBeenCalled();
    expect(client.start).not.toHaveBeenCalled();
    expect(store.readInteraction("run-one")).toBeNull();
  });
  it("keeps review approval separate from confirmed action submission and provider observations", async () => {
    const { client, store } = fixture();
    let current = waitingReview;
    vi.mocked(client.follow).mockImplementation(async function* () {
      yield { type: "snapshot", snapshot: current };
    });
    vi.mocked(client.decide).mockImplementation(async (request) => {
      current = {
        ...approvedReview,
        interactions: [
          {
            ...approvedReview.interactions![0],
            decision: {
              ...approvedReview.interactions![0].decision!,
              request_id: request.requestId,
            },
          },
        ],
      };
      return current;
    });
    vi.mocked(client.requestAction).mockImplementation(async (request) => {
      current = {
        ...approvedReview,
        state: "waiting_external",
        actions: [],
        interactions: [
          {
            ...approvedReview.interactions![0],
            state: "consumed",
            action_receipt: {
              request_id: request.requestId,
              submission: "authorized",
              delivery_completed: false,
              cancellation_requested: false,
            },
          },
        ],
      };
      return current;
    });
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
      />,
    );
    fireEvent.click(await screen.findByRole("button", { name: "Approve" }));
    await screen.findByText("Review recorded: Approved");
    expect(client.requestAction).not.toHaveBeenCalled();
    expect(
      screen.getByRole("button", { name: "Continue process" }),
    ).toBeDisabled();
    fireEvent.click(
      screen.getByLabelText("I reviewed this action and its evidence"),
    );
    fireEvent.click(screen.getByRole("button", { name: "Continue process" }));
    await screen.findByText(
      "Action authorized; provider acceptance is not confirmed yet.",
    );
    expect(client.requestAction).toHaveBeenCalledTimes(1);
    expect(client.requestAction).toHaveBeenCalledWith(
      expect.objectContaining({
        actionId: "continue-action",
        subjectDigest: hash,
        requestId: expect.any(String),
      }),
    );
    expect(
      screen.queryByText("Provider accepted the action."),
    ).not.toBeInTheDocument();
    expect(client.start).not.toHaveBeenCalled();
  });
  it.each(["response", "review", "action"] as const)(
    "reopens a lost %s acknowledgement without replay, then explicitly reconciles the same intent",
    async (kind) => {
      const { client, store } = fixture();
      const snapshot =
        kind === "response"
          ? waitingInput
          : kind === "review"
            ? waitingReview
            : approvedReview;
      vi.mocked(client.follow).mockImplementation(async function* () {
        yield { type: "snapshot", snapshot };
      });
      if (kind === "response")
        vi.mocked(client.respond).mockRejectedValue(lostInteraction());
      else if (kind === "review")
        vi.mocked(client.decide).mockRejectedValue(lostInteraction());
      else vi.mocked(client.requestAction).mockRejectedValue(lostInteraction());
      const props = {
        client,
        sessionId: "session",
        runId: "run-one",
        recoveryStore: store,
      };
      const first = render(<CommonProcessView {...props} />);
      if (kind === "response") {
        fireEvent.change(await screen.findByLabelText("selection (required)"), {
          target: { value: "1" },
        });
        fireEvent.click(
          screen.getByRole("button", { name: "Submit response" }),
        );
      } else if (kind === "review") {
        fireEvent.change(await screen.findByLabelText("Review reason"), {
          target: { value: "Checked the package" },
        });
        fireEvent.click(screen.getByRole("button", { name: "Approve" }));
      } else {
        fireEvent.click(
          await screen.findByLabelText(
            "I reviewed this action and its evidence",
          ),
        );
        fireEvent.click(
          screen.getByRole("button", { name: "Continue process" }),
        );
      }
      await screen.findByText("Interaction acknowledgement was lost.");
      const original = store.readInteraction("run-one")!;
      const method =
        kind === "response"
          ? client.respond
          : kind === "review"
            ? client.decide
            : client.requestAction;
      expect(method).toHaveBeenCalledTimes(1);
      first.unmount();
      render(<CommonProcessView {...props} />);
      const reconcile = await screen.findByRole("button", {
        name: `Reconcile ${kind} request`,
      });
      expect(method).toHaveBeenCalledTimes(1);
      expect(client.start).not.toHaveBeenCalled();
      fireEvent.click(reconcile);
      await waitFor(() => expect(method).toHaveBeenCalledTimes(2));
      expect(vi.mocked(method).mock.calls[1][0]).toEqual(original.request);
      expect(store.readInteraction("run-one")).toEqual(original);
    },
  );
  it.each([false, true])(
    "does not dispatch when request preservation is unavailable or the view is read-only (%s)",
    async (readOnly) => {
      const { client, store } = fixture();
      vi.mocked(client.follow).mockImplementation(async function* () {
        yield { type: "snapshot", snapshot: waitingReview };
      });
      vi.mocked(store.writeInteraction).mockImplementation(() => {
        throw new Error("Synthetic storage unavailable");
      });
      render(
        <CommonProcessView
          client={client}
          sessionId="session"
          runId="run-one"
          recoveryStore={store}
          readOnly={readOnly}
        />,
      );
      const approve = await screen.findByRole("button", { name: "Approve" });
      fireEvent.click(approve);
      if (!readOnly)
        await screen.findByText("Wright could not finish this request.");
      else expect(approve).toBeDisabled();
      expect(client.decide).not.toHaveBeenCalled();
      expect(client.requestAction).not.toHaveBeenCalled();
    },
  );
});
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
    expect(
      screen.getByRole("button", { name: "Start workflow" }),
    ).toBeEnabled(),
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

describe("desktop reasoning observation in the common view", () => {
  it("explains a rejected workflow and keeps Start visible without granting an action", async () => {
    const { client, store } = fixture();
    vi.mocked(client.getSnapshot).mockRejectedValue(
      new ProcessClientError({
        code: "WORKFLOW_NOT_READY",
        message:
          "This workflow uses a connection that this execution path does not support.",
        correction:
          "You can inspect and edit this workflow, but cannot start it here. Keep required decisions and reviews.",
      }),
    );
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
        canNavigate
      />,
    );
    expect(
      await screen.findByRole("heading", {
        name: "Cannot start this workflow",
      }),
    ).toBeVisible();
    const start = screen.getByRole("button", { name: "Start workflow" });
    expect(start).toBeVisible();
    expect(start).toBeDisabled();
    expect(
      screen.getByText(/Keep required decisions and reviews/),
    ).toBeVisible();
    fireEvent.click(start);
    fireEvent.click(
      screen.getByRole("button", { name: "View workflow diagram" }),
    );
    await waitFor(() => expect(client.navigate).toHaveBeenCalledOnce());
    expect(client.start).not.toHaveBeenCalled();
    expect(client.setInputs).not.toHaveBeenCalled();
  });

  it("does not invent start authority when the backend has no start action", async () => {
    const { client, store } = fixture();
    vi.mocked(client.getSnapshot).mockResolvedValue({
      ...initial,
      actions: [],
    });
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
      />,
    );
    await screen.findByLabelText("Design request (required)");
    const start = screen.getByRole("button", { name: "Start workflow" });
    expect(start).toBeVisible();
    expect(start).toBeDisabled();
    fireEvent.click(start);
    expect(client.start).not.toHaveBeenCalled();
  });

  it("shows the exact chat wait and detaches only its reader on close", async () => {
    const { client, store } = fixture();
    const read = vi.fn(async (_run: string, _signal: AbortSignal) => ({
      runId: "run-one",
      requestId: "request-chat",
      queuedAt: input.created_at,
      label: "Waiting for desktop chat",
      detail: "Send Continue in the bound desktop conversation.",
    }));
    const view = render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
        readReasoningStatus={read}
      />,
    );
    const notice = await screen.findByTestId("process-desktop-reasoning-wait");
    expect(notice).toHaveTextContent("Waiting for desktop chat");
    expect(notice).toHaveTextContent("request-chat");
    expect(read.mock.calls[0][0]).toBe("run-one");
    expect(client.start).not.toHaveBeenCalled();
    expect(client.respond).not.toHaveBeenCalled();
    expect(client.decide).not.toHaveBeenCalled();
    view.unmount();
    expect(read.mock.calls[0][1].aborted).toBe(true);
    expect(client.cancel).not.toHaveBeenCalled();
  });

  it("reports a mismatched handoff instead of presenting another run's wait", async () => {
    const { client, store } = fixture();
    const read = vi.fn(async () => ({
      runId: "other-run",
      requestId: "other-request",
      queuedAt: input.created_at,
      label: "Wrong run wait",
      detail: "Do not present this.",
    }));
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
        readReasoningStatus={read}
      />,
    );
    const notice = await screen.findByTestId("process-desktop-reasoning-wait");
    expect(notice).toHaveTextContent("AI handoff status unavailable");
    expect(notice).not.toHaveTextContent("other-request");
    expect(client.start).not.toHaveBeenCalled();
    expect(client.respond).not.toHaveBeenCalled();
  });
});

describe("common process preparation and authority", () => {
  it("offers diagnostics for the attached source run without starting or exporting work", async () => {
    const { client, store } = fixture();
    const preview = vi
      .spyOn(workspaceService, "previewSupportDiagnostics")
      .mockRejectedValue(
        new Error("The saved run evidence could not be verified."),
      );
    const exportFile = vi
      .spyOn(workspaceService, "exportSupportDiagnostics")
      .mockResolvedValue();
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
      />,
    );
    await screen.findByText("Diagnose this run");
    expect(preview).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("Diagnose this run"));
    fireEvent.click(screen.getByTestId("support-diagnostics-preview"));
    await waitFor(() =>
      expect(preview).toHaveBeenCalledWith("workspace", {
        source_run_id: "run-one",
      }),
    );
    expect(
      await screen.findByText("The saved run evidence could not be verified."),
    ).toBeVisible();
    expect(exportFile).not.toHaveBeenCalled();
    expect(client.start).not.toHaveBeenCalled();
  });
  it("shows an undeclared-input diagnostic and exact correction without inventing a response form", async () => {
    const { client, store } = fixture();
    vi.mocked(client.follow).mockImplementation(async function* () {
      yield {
        type: "snapshot",
        snapshot: {
          ...running,
          state: "failed",
          actions: [],
          interactions: [],
          navigation: [
            { kind: "block", block_id: "measure", run_id: "run-one" },
          ],
          diagnostics: [
            {
              code: "INTERACTION_NOT_DECLARED",
              message:
                "Measure: additional user input was requested in an unattended step.",
              correction:
                "Supply the missing load before starting or declare a human-input step.",
              step_id: "measure",
              navigation: {
                kind: "block",
                block_id: "measure",
                run_id: "run-one",
              },
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
      />,
    );
    await screen.findByText(
      "Measure: additional user input was requested in an unattended step.",
    );
    expect(
      screen.getByText(
        "Supply the missing load before starting or declare a human-input step.",
      ),
    ).toBeVisible();
    expect(
      screen.queryByRole("button", { name: "Submit response" }),
    ).toBeNull();
    expect(screen.queryByRole("combobox")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Open affected step" }));
    await waitFor(() =>
      expect(client.navigate).toHaveBeenCalledWith({
        kind: "block",
        block_id: "measure",
        run_id: "run-one",
      }),
    );
    expect(client.start).not.toHaveBeenCalled();
    expect(client.respond).not.toHaveBeenCalled();
    expect(client.decide).not.toHaveBeenCalled();
  });

  it("renders only the declared form, submits its exact subject and follows the same run", async () => {
    const { client, store } = fixture();
    let submitted = false;
    vi.mocked(client.follow).mockImplementation(async function* () {
      yield {
        type: "snapshot",
        snapshot: submitted
          ? { ...running, state: "completed", interactions: [], actions: [] }
          : waitingInput,
      };
    });
    vi.mocked(client.respond).mockImplementation(async (request) => {
      submitted = true;
      return { ...recordedAnswer, request_id: request.requestId };
    });
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
      />,
    );
    const field = await screen.findByLabelText("selection (required)");
    expect(
      screen.getByRole("button", { name: "Submit response" }),
    ).toBeDisabled();
    expect(
      screen.getByText("Provide the declared response before submitting."),
    ).toBeVisible();
    expect(client.respond).not.toHaveBeenCalled();
    fireEvent.change(field, { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "Submit response" }));
    await screen.findByText("Process completed");
    expect(client.respond).toHaveBeenCalledTimes(1);
    expect(client.respond).toHaveBeenCalledWith(
      expect.objectContaining({
        checkpointId: "input-checkpoint",
        subjectDigest: hash,
        value: { selection: "b" },
        requestId: expect.any(String),
      }),
    );
    expect(client.follow).toHaveBeenLastCalledWith(
      expect.objectContaining({ runId: "run-one" }),
    );
    expect(client.start).not.toHaveBeenCalled();
  });
  it("keeps a lost acknowledgement's exact response frozen for explicit reconciliation", async () => {
    const { client, store } = fixture();
    vi.mocked(client.follow).mockImplementation(async function* () {
      yield { type: "snapshot", snapshot: waitingInput };
    });
    vi.mocked(client.respond).mockRejectedValueOnce(
      new ProcessClientError({
        code: "OUTCOME_UNKNOWN",
        message: "Response acknowledgement was lost.",
        correction: "Reconcile the exact saved response.",
      }),
    );
    vi.mocked(client.respond).mockImplementationOnce(async (request) => ({
      ...recordedAnswer,
      request_id: request.requestId,
    }));
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
      />,
    );
    const field = await screen.findByLabelText("selection (required)");
    fireEvent.change(field, { target: { value: "1" } });
    fireEvent.click(screen.getByRole("button", { name: "Submit response" }));
    await screen.findByText("Response acknowledgement was lost.");
    expect(client.respond).toHaveBeenCalledTimes(1);
    expect(field).toBeDisabled();
    fireEvent.click(
      screen.getByRole("button", { name: "Reconcile response request" }),
    );
    await waitFor(() => expect(client.respond).toHaveBeenCalledTimes(2));
    expect(vi.mocked(client.respond).mock.calls[1]).toEqual(
      vi.mocked(client.respond).mock.calls[0],
    );
    expect(client.start).not.toHaveBeenCalled();
  });
  it("preserves declared form inspection without giving read-only views response authority", async () => {
    const { client, store } = fixture();
    vi.mocked(client.follow).mockImplementation(async function* () {
      yield { type: "snapshot", snapshot: waitingInput };
    });
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
        readOnly
      />,
    );
    expect(await screen.findByLabelText("selection (required)")).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Submit response" }),
    ).toBeDisabled();
    expect(client.respond).not.toHaveBeenCalled();
  });
  it("evaluates fresh observations at snapshot receipt without waiting for a clock tick", async () => {
    const measuredAt = Date.now();
    const clock = vi.spyOn(Date, "now").mockReturnValue(measuredAt - 2000);
    const { client, store } = fixture();
    const fresh = {
      ...running,
      observations: [
        {
          observation_id: "fresh-read",
          provider_binding: "controlled-test",
          state: "running" as const,
          observed_at: new Date(measuredAt).toISOString(),
          stale_after: new Date(measuredAt + 60_000).toISOString(),
          progress_percent: 20,
        },
      ],
    };
    client.follow = vi.fn(async function* () {
      clock.mockReturnValue(measuredAt + 10);
      yield { type: "snapshot" as const, snapshot: fresh };
    });
    await act(async () => {
      render(
        <CommonProcessView
          client={client}
          sessionId="session"
          runId="run-one"
          recoveryStore={store}
        />,
      );
    });
    expect(screen.getByText("20% complete")).toBeInTheDocument();
    expect(
      screen.queryByText(/status needs a fresh observation/),
    ).not.toBeInTheDocument();
  });
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
      screen.getByRole("button", { name: "Start workflow" }),
    ).toBeDisabled();
  });
  it("keeps saved defaults inspectable while showing unanswered inputs first", async () => {
    const { client, store } = fixture();
    const snapshot: InteractionSnapshot = {
      ...initial,
      inputs: [
        {
          ...initial.inputs![0],
          input_id: "material",
          block_id: "material",
          title: "Material",
          default: {
            input_id: "material",
            value: "PETG",
            provenance: "explicit_default",
          },
        },
        initial.inputs![0],
        {
          ...initial.inputs![0],
          input_id: "drawing",
          block_id: "drawing",
          title: "Reference drawing",
          binding_kind: "file",
          default: {
            input_id: "drawing",
            reference: { artifact_ref: "inputs/drawing.png", sha256: hash },
            provenance: "explicit_default",
          },
        },
      ],
    };
    vi.mocked(client.getSnapshot).mockResolvedValue(snapshot);
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
      />,
    );
    expect(
      await screen.findByLabelText("Design request (required)"),
    ).toBeVisible();
    const summary = screen.getByText("Saved defaults (2)");
    expect(summary.closest("details")).not.toHaveAttribute("open");
    expect(screen.getByLabelText("Material (required)")).not.toBeVisible();
    fireEvent.click(summary);
    expect(screen.getByLabelText("Material (required)")).toBeVisible();
    expect(screen.getByLabelText("Material (required)")).toHaveValue("PETG");
    expect(screen.getByText("File attached")).toBeVisible();
    expect(screen.getByText("inputs/drawing.png")).not.toBeVisible();
    fireEvent.click(screen.getByText("File details"));
    expect(screen.getByText("inputs/drawing.png")).toBeVisible();
    for (const mutation of [
      client.setInputs,
      client.start,
      client.respond,
      client.decide,
    ])
      expect(mutation).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText("Material (required)"), {
      target: { value: "PA12" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Prepare and check inputs" }),
    );
    await waitFor(() =>
      expect(client.setInputs).toHaveBeenCalledWith([
        {
          input_id: "material",
          kind: "value",
          value: "PA12",
          provenance: "supplied",
        },
      ]),
    );
    // Omitted, unchanged defaults still resolve through the existing backend path.
    expect(client.checkReadiness).toHaveBeenCalledTimes(1);
    expect(client.start).not.toHaveBeenCalled();
  });
  it("expands saved defaults after blocked readiness without enabling Start", async () => {
    const { client, store } = fixture();
    const defaults: InteractionSnapshot = {
      ...initial,
      inputs: [
        {
          ...initial.inputs![0],
          default: {
            input_id: "prompt",
            kind: "value",
            value: "Saved design",
            provenance: "explicit_default",
          },
        },
      ],
    };
    const blocked: Readiness = {
      ...readiness,
      state: "blocked",
      reasons: [
        {
          code: "INPUT_REQUIRED",
          message: "Inspect the saved design reference.",
          correction: "Select the correct revision.",
          navigation: { kind: "block", block_id: "intent" },
        },
      ],
    };
    vi.mocked(client.getSnapshot).mockImplementation(async (options) =>
      options?.inputSnapshotId
        ? { ...defaults, context: prepared.context, readiness: blocked }
        : defaults,
    );
    vi.mocked(client.checkReadiness).mockResolvedValue(blocked);
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
      />,
    );
    const summary = await screen.findByText("Saved defaults (1)");
    expect(summary.closest("details")).not.toHaveAttribute("open");
    expect(
      screen.getByRole("button", { name: "Prepare and check inputs" }),
    ).toBeVisible();
    fireEvent.click(
      screen.getByRole("button", { name: "Prepare and check inputs" }),
    );
    await waitFor(() =>
      expect(summary.closest("details")).toHaveAttribute("open"),
    );
    expect(
      screen.getByText("Inspect the saved design reference."),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Start workflow" }),
    ).toBeDisabled();
    expect(client.setInputs).toHaveBeenCalledWith([]);
    expect(client.start).not.toHaveBeenCalled();
  });
  it("keeps unresolved, invalid and live-choice saved defaults visible", async () => {
    const { client, store } = fixture();
    const snapshot: InteractionSnapshot = {
      ...initial,
      inputs: [
        {
          ...initial.inputs![0],
          title: "Unresolved input",
          default: { input_id: "prompt", value: "draft" },
          dependencies: [{ binding_id: "size", classification: "unresolved" }],
        },
        {
          ...initial.inputs![0],
          input_id: "size",
          title: "Size",
          value_schema: { type: "number", minimum: 1 },
          default: { input_id: "size", value: -1 },
        },
        {
          ...initial.inputs![0],
          input_id: "option",
          title: "Live choice",
          binding_kind: "option",
          default: { input_id: "option", value: "unused" },
        },
      ],
    };
    vi.mocked(client.getSnapshot).mockResolvedValue(snapshot);
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
      />,
    );
    expect(
      await screen.findByLabelText("Unresolved input (required)"),
    ).toBeVisible();
    expect(screen.getByLabelText("Size (required)")).toBeVisible();
    expect(screen.getByText("Enter a value of at least 1.")).toBeVisible();
    expect(screen.getByLabelText("Live choice (required)")).toBeVisible();
    expect(
      screen.getByText("The configured choices are unavailable."),
    ).toBeVisible();
    expect(screen.queryByText(/Saved defaults \(/)).not.toBeInTheDocument();
    expect(client.setInputs).not.toHaveBeenCalled();
  });
  it("invalidates prepared readiness when a saved default is edited", async () => {
    const { client, store } = fixture();
    const inputs: InteractionSnapshot["inputs"] = [
      {
        ...initial.inputs![0],
        default: {
          input_id: "prompt",
          kind: "value",
          value: "Saved design",
          provenance: "explicit_default",
        },
      },
    ];
    vi.mocked(client.getSnapshot).mockImplementation(async (options) => ({
      ...(options?.inputSnapshotId ? prepared : initial),
      inputs,
    }));
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
      />,
    );
    await screen.findByText("Saved defaults (1)");
    fireEvent.click(
      screen.getByRole("button", { name: "Prepare and check inputs" }),
    );
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Start workflow" }),
      ).toBeEnabled(),
    );
    fireEvent.click(screen.getByText("Saved defaults (1)"));
    fireEvent.change(screen.getByLabelText("Design request (required)"), {
      target: { value: "Changed design" },
    });
    expect(
      screen.getByRole("button", { name: "Start workflow" }),
    ).toBeDisabled();
    expect(screen.getByText("Readiness has not been checked")).toBeVisible();
    expect(store.clear).toHaveBeenCalled();
    expect(client.start).not.toHaveBeenCalled();
  });
  it("keeps recorded run inputs visible and frozen even when defaults exist", async () => {
    const { client, store } = fixture();
    client.follow = vi.fn(async function* () {
      yield {
        type: "snapshot" as const,
        snapshot: {
          ...running,
          inputs: [
            {
              ...initial.inputs![0],
              default: {
                input_id: "prompt",
                kind: "value" as const,
                value: "Earlier default",
                provenance: "explicit_default" as const,
              },
              current_value: {
                input_id: "prompt",
                kind: "value" as const,
                value: "Actual run input",
                provenance: "supplied" as const,
              },
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
    const field = await screen.findByLabelText("Design request (required)");
    expect(field).toBeVisible();
    expect(field).toBeDisabled();
    expect(field).toHaveValue("Actual run input");
    expect(screen.queryByText(/Saved defaults \(/)).not.toBeInTheDocument();
    expect(client.setInputs).not.toHaveBeenCalled();
    expect(client.start).not.toHaveBeenCalled();
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
    fireEvent.click(screen.getByRole("button", { name: "Start workflow" }));
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
      screen.getByRole("button", { name: "Start workflow" }),
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
          binding_id: "destination",
          navigation: { kind: "block", block_id: "destination" },
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
    const mounted = render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
        canNavigate
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
      screen.getByRole("button", { name: "Start workflow" }),
    ).toBeDisabled();
    expect(client.start).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Open affected step" }));
    await waitFor(() =>
      expect(client.navigate).toHaveBeenCalledWith({
        kind: "block",
        block_id: "destination",
      }),
    );
    // Returning without a source change restores the exact prepared inputs;
    // navigation must not silently start or prepare another run.
    mounted.unmount();
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
        canNavigate
      />,
    );
    await screen.findByText("A later step needs a destination.");
    expect(
      screen.getByLabelText("Cooling enabled (required)"),
    ).not.toBeChecked();
    expect(client.getSnapshot).toHaveBeenLastCalledWith(
      expect.objectContaining({ inputSnapshotId: input.snapshot_id }),
    );
    expect(client.setInputs).toHaveBeenCalledTimes(1);
    expect(client.checkReadiness).toHaveBeenCalledTimes(1);
    expect(client.start).not.toHaveBeenCalled();
  });
  it("shows a capability blocker once by default and keeps Start reasons inspectable", async () => {
    const { client, store } = fixture();
    const reason = {
      code: "CAPABILITY_UNAVAILABLE",
      message: "The required measurement reader is unavailable.",
      correction: "Restore the reader before starting.",
    };
    const blocked: Readiness = {
      ...readiness,
      state: "blocked",
      reasons: [reason],
    };
    vi.mocked(client.checkReadiness).mockResolvedValue(blocked);
    vi.mocked(client.getSnapshot).mockImplementation(async (options) =>
      options?.inputSnapshotId
        ? {
            ...prepared,
            state: "preparing",
            readiness: blocked,
            actions: [
              { ...prepared.actions![0], enabled: false, reasons: [reason] },
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
    fireEvent.change(
      await screen.findByLabelText("Design request (required)"),
      {
        target: { value: "Create a small fixture" },
      },
    );
    fireEvent.click(
      screen.getByRole("button", { name: "Prepare and check inputs" }),
    );
    await screen.findByText("Not ready to start");
    const button = screen.getByRole("button", { name: "Start workflow" });
    expect(button).toBeDisabled();
    const disclosures = screen.getByText("Why unavailable").closest("details")!;
    expect(disclosures).not.toHaveAttribute("open");
    const messages = screen.getAllByText(reason.message);
    expect(messages).toHaveLength(2);
    expect(
      messages.filter((element) => !disclosures.contains(element)),
    ).toHaveLength(1);
    fireEvent.click(screen.getByText("Why unavailable"));
    expect(disclosures).toHaveAttribute("open");
    expect(disclosures).toHaveTextContent(reason.message);
    fireEvent.click(button);
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
        screen.getByRole("button", { name: "Start workflow" }),
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
      screen.getByRole("button", { name: "Start workflow" }),
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
      await screen.findByAltText("Selected reference: reference.png"),
    ).toBeVisible();
    expect(
      screen.getByAltText("Selected reference: reference.png"),
    ).toHaveAttribute("src", "data:image/png;base64,aW1hZ2U=");
    expect(create).not.toHaveBeenCalled();
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
    expect(
      screen.getByRole("button", { name: "View workflow diagram" }),
    ).toBeDisabled();
    expect(screen.getByText(/File previews are unavailable/)).toBeVisible();
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
    fireEvent.click(screen.getByRole("button", { name: "Start workflow" }));
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
    fireEvent.click(screen.getByRole("button", { name: "Start workflow" }));
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
    const button = screen.getByRole("button", { name: "Start workflow" });
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
    fireEvent.click(screen.getByRole("button", { name: "Start workflow" }));
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
  it("separates prior attempt evidence from current results without retrying a failed run", async () => {
    const { client, store } = fixture();
    const reference = {
      artifact_ref: "attempts/1/model.csv",
      sha256: hash,
      result_id: "history-one",
    };
    vi.mocked(client.follow).mockImplementation(async function* () {
      yield {
        type: "snapshot",
        snapshot: {
          ...running,
          state: "failed",
          actions: [],
          outputs: [
            {
              result_id: "history-one",
              step_id: "geometry",
              port_id: "out",
              role: "previous_attempt",
              producer_attempt: "1",
              title: "Attempt 1: Measured geometry",
              representations: [reference],
              assessments: [],
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
    await screen.findByRole("heading", { name: "Previous attempts" });
    expect(
      screen.getByText("Historical evidence · superseded output"),
    ).toBeVisible();
    expect(
      screen.getByText("No outputs are recorded on this page yet."),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Attempt 1: Measured geometry" }),
    ).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Open file" }));
    await waitFor(() => expect(client.getRepresentation).toHaveBeenCalled());
    expect(vi.mocked(client.getRepresentation).mock.calls[0][0]).toEqual(
      reference,
    );
    expect(client.start).not.toHaveBeenCalled();
    expect(client.requestAction).not.toHaveBeenCalled();
  });
  it("retains exact result, assessment, evidence and producer navigation", async () => {
    const { client, store } = fixture();
    const scroll = vi.fn();
    const originalScroll = HTMLElement.prototype.scrollIntoView;
    HTMLElement.prototype.scrollIntoView = scroll;
    let emitRefresh: (() => void) | undefined;
    let finishPreview: ((text: string) => void) | undefined;
    const preview = new Blob(["exact output"], { type: "text/plain" });
    vi.spyOn(preview, "text").mockImplementation(
      () =>
        new Promise<string>((resolve) => {
          finishPreview = resolve;
        }),
    );
    vi.mocked(client.getRepresentation).mockResolvedValue(preview);
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
      await new Promise<void>((resolve) => {
        emitRefresh = resolve;
      });
      yield {
        type: "snapshot",
        snapshot: { ...running, state: "completed", actions: [], outputs: [] },
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
    expect(scroll).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Open assessment" }));
    expect(client.navigate).toHaveBeenCalledWith({
      kind: "assessment",
      assessment_id: "check-one",
      result_id: "result-one",
      run_id: "run-one",
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Open producing step" }),
    );
    expect(client.navigate).toHaveBeenCalledWith({
      kind: "block",
      block_id: "geometry",
      result_id: "result-one",
      run_id: "run-one",
    });
    const opener = screen.getByRole("button", { name: "Open file" });
    opener.focus();
    fireEvent.click(opener);
    await screen.findByText("Opening representation…");
    expect(scroll).not.toHaveBeenCalled();
    expect(
      screen.getByRole("region", { name: "Selected file" }),
    ).not.toHaveFocus();
    await waitFor(() => expect(finishPreview).toBeDefined());
    await act(async () => {
      finishPreview!("exact output");
    });
    await screen.findByText("exact output");
    expect(screen.getByRole("region", { name: "Selected file" })).toHaveFocus();
    expect(screen.getByRole("heading", { name: "geometry.csv" })).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Back to results" }),
    ).toBeVisible();
    expect(scroll).toHaveBeenCalledExactlyOnceWith({ block: "start" });
    expect(screen.getByText("Failed")).toBeVisible();
    await act(async () => {
      emitRefresh?.();
    });
    expect(scroll).toHaveBeenCalledTimes(1);
    expect(
      screen.getByRole("link", { name: "Download exact file" }),
    ).toHaveAttribute("download", "geometry.csv");
    expect(client.getRepresentation).toHaveBeenCalledWith(artifact, {
      runId: "run-one",
      signal: expect.any(AbortSignal),
    });
    fireEvent.click(screen.getByRole("button", { name: "Back to results" }));
    expect(
      screen.queryByRole("region", { name: "Selected file" }),
    ).not.toBeInTheDocument();
    // The refreshed snapshot removed the original output; return to results,
    // never to a detached control or a different run.
    expect(
      screen
        .getByRole("heading", { name: "Results and checks" })
        .closest("section"),
    ).toHaveFocus();
    expect(scroll).toHaveBeenLastCalledWith({ block: "nearest" });
    expect(client.start).not.toHaveBeenCalled();
    expect(client.cancel).not.toHaveBeenCalled();
    HTMLElement.prototype.scrollIntoView = originalScroll;
  });
  it("aborts a representation read on close without cancelling the process", async () => {
    const { client, store } = fixture();
    const artifact = {
      artifact_ref: "outputs/part.stl",
      sha256: hash,
      result_id: "result-one",
    };
    vi.mocked(client.follow).mockImplementation(async function* () {
      yield {
        type: "snapshot",
        snapshot: {
          ...running,
          state: "completed",
          outputs: [
            {
              result_id: "result-one",
              step_id: "geometry",
              port_id: "out",
              role: "geometry",
              title: "Exact part",
              representations: [artifact],
            },
          ],
        },
      };
    });
    let signal: AbortSignal | undefined;
    vi.mocked(client.getRepresentation).mockImplementation(
      async (_reference, options) => {
        signal = options?.signal;
        return new Promise<Blob>((_resolve, reject) =>
          signal?.addEventListener("abort", () => reject(signal?.reason), {
            once: true,
          }),
        );
      },
    );
    const view = render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
        canReadRepresentations
      />,
    );
    await screen.findByText("Exact part");
    const opener = screen.getByRole("button", { name: "Open file" });
    opener.focus();
    fireEvent.click(opener);
    expect(signal?.aborted).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: "Back to results" }));
    expect(signal?.aborted).toBe(true);
    expect(opener).toHaveFocus();
    view.unmount();
    expect(client.cancel).not.toHaveBeenCalled();
    expect(client.start).not.toHaveBeenCalled();
  });
  it("a reopened run whose recorded representation was removed shows its exact failure without substitution or execution", async () => {
    const { client, store } = fixture();
    const artifact = {
      artifact_ref: "outputs/removed.stl",
      sha256: hash,
      result_id: "removed-result",
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
              result_id: artifact.result_id,
              step_id: "geometry",
              port_id: "out",
              role: "geometry",
              title: "Original recorded part",
              representations: [artifact],
            },
          ],
        },
      };
    });
    vi.mocked(client.getRepresentation).mockRejectedValue(
      new ProcessClientError({
        code: "CAPABILITY_UNAVAILABLE",
        message: "The recorded part file is no longer available.",
        correction:
          "Inspect the recorded run; no replacement file was selected.",
      }),
    );
    const view = render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
        canReadRepresentations
      />,
    );
    await screen.findByText("Original recorded part");
    fireEvent.click(screen.getByRole("button", { name: "Open file" }));
    await screen.findByText("The recorded part file is no longer available.");
    expect(client.getRepresentation).toHaveBeenCalledExactlyOnceWith(artifact, {
      runId: "run-one",
      signal: expect.any(AbortSignal),
    });
    expect(
      screen.queryByRole("link", { name: "Download exact file" }),
    ).not.toBeInTheDocument();
    expect(client.start).not.toHaveBeenCalled();
    expect(client.cancel).not.toHaveBeenCalled();
    expect(client.requestAction).not.toHaveBeenCalled();
    expect(client.navigate).not.toHaveBeenCalled();
    view.unmount();
  });
  it.each([false, true])(
    "focuses an exact assessment and reads its separate recorded evidence only once (shared assessment: %s)",
    async (sharedAssessment) => {
      const { client, store } = fixture();
      const output = {
        result_id: "subject-result",
        step_id: "geometry",
        port_id: "part",
        role: "geometry",
        title: "Checked part",
        assessments: [
          {
            assessment_id: "assessment-one",
            subject_digest: hash,
            outcome: "fail" as const,
            currentness: "current" as const,
          },
        ],
      };
      const completed: InteractionSnapshot = {
        ...running,
        state: "completed",
        outputs: sharedAssessment
          ? [
              {
                ...output,
                result_id: "earlier-result",
                title: "Earlier checked part",
              },
              output,
            ]
          : [output],
      };
      vi.mocked(client.getSnapshot).mockResolvedValue(completed);
      vi.mocked(client.follow).mockImplementation(async function* () {
        yield { type: "snapshot", snapshot: completed };
      });
      const reference = {
        artifact_ref: "outputs/assessment.json",
        sha256: hash,
        result_id: "validator-evidence",
      };
      const navigation = {
        requestId: "focus-assessment",
        resolution: {
          process,
          target: {
            kind: "assessment" as const,
            assessment_id: "assessment-one",
            result_id: "subject-result",
            run_id: "run-one",
          },
          representation: reference,
        },
      };
      const props = {
        client,
        sessionId: "session",
        runId: "run-one",
        recoveryStore: store,
        canReadRepresentations: true,
        navigation,
      };
      const view = render(<CommonProcessView {...props} />);
      await screen.findByText("exact output");
      expect(document.activeElement).toHaveAttribute(
        "data-assessment-id",
        "assessment-one",
      );
      expect(
        document.activeElement?.closest("[data-result-id]"),
      ).toHaveAttribute("data-result-id", "subject-result");
      expect(client.getRepresentation).toHaveBeenCalledExactlyOnceWith(
        reference,
        { runId: "run-one", signal: expect.any(AbortSignal) },
      );
      view.rerender(
        <CommonProcessView {...props} navigation={{ ...navigation }} />,
      );
      expect(client.getRepresentation).toHaveBeenCalledTimes(1);
      expect(client.start).not.toHaveBeenCalled();
      expect(client.cancel).not.toHaveBeenCalled();
    },
  );
  it("rejects foreign navigation without reading files or changing the run", async () => {
    const { client, store } = fixture();
    vi.mocked(client.getSnapshot).mockResolvedValue(running);
    const navigation = {
      requestId: "foreign",
      resolution: {
        process: { ...process, workspace_id: "foreign" },
        target: {
          kind: "evidence" as const,
          run_id: "run-one",
          artifact_ref: "private.txt",
          result_id: "other",
        },
        representation: {
          artifact_ref: "private.txt",
          sha256: hash,
          result_id: "other",
        },
      },
    };
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
        canReadRepresentations
        navigation={navigation}
      />,
    );
    await screen.findByText("This item belongs to another process or run.");
    expect(client.getRepresentation).not.toHaveBeenCalled();
    expect(client.start).not.toHaveBeenCalled();
    expect(client.cancel).not.toHaveBeenCalled();
  });
  it("keeps progress visible without an empty frozen-input panel", async () => {
    const { client, store } = fixture();
    const held: InteractionSnapshot = {
      ...running,
      state: "failed",
      inputs: [],
      actions: running.actions?.map((action) => ({
        ...action,
        enabled: false,
      })),
    };
    vi.mocked(client.attach).mockResolvedValue(held);
    vi.mocked(client.follow).mockImplementation(async function* () {
      yield { type: "snapshot", snapshot: held };
    });
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
      />,
    );
    await screen.findByRole("heading", { name: "Progress" });
    expect(
      screen.queryByRole("heading", { name: "Run inputs" }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText("No user inputs are available on this page."),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Cancel this run" }),
    ).toBeDisabled();
    expect(client.cancel).not.toHaveBeenCalled();
    expect(client.start).not.toHaveBeenCalled();
  });
  it.each(["completed", "cancelled"] as const)(
    "keeps results visible and cancellation details expandable after a run is %s",
    async (state) => {
      const { client, store } = fixture();
      const reason = `This Wright run has ${state}; there is no active execution to cancel.`;
      const ended: InteractionSnapshot = {
        ...running,
        state,
        inputs: [],
        actions: running.actions?.map((action) => ({
          ...action,
          enabled: false,
          reasons: [
            {
              code: "ACTION_NOT_PERMITTED",
              message: reason,
              correction: "Open its saved results or prepare another run.",
            },
          ],
        })),
      };
      vi.mocked(client.attach).mockResolvedValue(ended);
      vi.mocked(client.follow).mockImplementation(async function* () {
        yield { type: "snapshot", snapshot: ended };
      });
      render(
        <CommonProcessView
          client={client}
          sessionId="session"
          runId="run-one"
          recoveryStore={store}
        />,
      );
      const summary = await screen.findByText(
        `${state === "completed" ? "Completed" : "Cancelled"} · Run details`,
      );
      expect(summary).toBeVisible();
      expect(
        screen.getByRole("heading", { name: "Progress" }),
      ).not.toBeVisible();
      fireEvent.click(summary);
      expect(screen.getByRole("heading", { name: "Progress" })).toBeVisible();
      expect(
        await screen.findByRole("button", { name: "Cancel this run" }),
      ).toBeDisabled();
      const explanation = screen.getByText(reason);
      expect(explanation).not.toBeVisible();
      fireEvent.click(screen.getByText("Why unavailable"));
      expect(explanation).toBeVisible();
      expect(client.cancel).not.toHaveBeenCalled();
      expect(client.start).not.toHaveBeenCalled();
    },
  );
  it.each(["completed", "failed", "cancelled", "waiting_human"] as const)(
    "offers visible preparation for %s without starting or resuming",
    async (state) => {
      const { client, store } = fixture();
      const ended: InteractionSnapshot = {
        ...running,
        state,
        inputs: [],
        actions: [],
      };
      vi.mocked(client.attach).mockResolvedValue(ended);
      vi.mocked(client.follow).mockImplementation(async function* () {
        yield { type: "snapshot", snapshot: ended };
      });
      const prepare = vi.fn();
      render(
        <CommonProcessView
          client={client}
          sessionId="session"
          runId="run-one"
          recoveryStore={store}
          onPrepareAnother={prepare}
        />,
      );
      const button = await screen.findByRole("button", {
        name: "Prepare new run",
      });
      expect(button).toBeVisible();
      expect(button.closest("details")).toBeNull();
      fireEvent.click(button);
      expect(prepare).toHaveBeenCalledTimes(1);
      expect(client.start).not.toHaveBeenCalled();
      expect(client.cancel).not.toHaveBeenCalled();
    },
  );
  it.each(["running", "waiting_external", "reconciliation_required"] as const)(
    "does not offer a replacement run while state is %s",
    async (state) => {
      const { client, store } = fixture();
      const observed: InteractionSnapshot = { ...running, state, actions: [] };
      vi.mocked(client.follow).mockImplementation(async function* () {
        yield { type: "snapshot", snapshot: observed };
      });
      const prepare = vi.fn();
      render(
        <CommonProcessView
          client={client}
          sessionId="session"
          runId="run-one"
          recoveryStore={store}
          onPrepareAnother={prepare}
        />,
      );
      await waitFor(() => expect(client.follow).toHaveBeenCalled());
      expect(
        screen.queryByRole("button", { name: "Prepare new run" }),
      ).toBeNull();
      expect(prepare).not.toHaveBeenCalled();
      expect(client.start).not.toHaveBeenCalled();
    },
  );
  it("retains preparation controls for a process without initial input fields", async () => {
    const { client, store } = fixture();
    vi.mocked(client.getSnapshot).mockResolvedValue({ ...initial, inputs: [] });
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        recoveryStore={store}
      />,
    );
    await screen.findByRole("button", { name: "Prepare and check inputs" });
    expect(screen.getByRole("heading", { name: "Inputs" })).toBeInTheDocument();
    expect(client.setInputs).not.toHaveBeenCalled();
    expect(client.start).not.toHaveBeenCalled();
  });
  it("puts a pending question ahead of preparation and diagnostics without answering it", async () => {
    const { client, store } = fixture();
    vi.mocked(client.attach).mockResolvedValue(waitingInput);
    vi.mocked(client.follow).mockImplementation(async function* () {
      yield { type: "snapshot", snapshot: waitingInput };
    });
    render(
      <CommonProcessView
        client={client}
        sessionId="session"
        runId="run-one"
        recoveryStore={store}
      />,
    );
    const question = await screen.findByRole("heading", {
      name: "Your next step",
    });
    const inputs = screen.getByRole("heading", { name: "Run inputs" });
    const progress = screen.getByRole("heading", { name: "Progress" });
    expect(
      question.compareDocumentPosition(inputs) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(
      question.compareDocumentPosition(progress) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    expect(
      screen.getAllByText("Choose the comparison to carry forward."),
    ).toHaveLength(1);
    expect(client.respond).not.toHaveBeenCalled();
    expect(client.decide).not.toHaveBeenCalled();
    expect(client.start).not.toHaveBeenCalled();
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
