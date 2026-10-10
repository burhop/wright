import { afterEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { WorkingControls } from "@wright/ui-kit";
import {
  ProcessClientError,
  type InteractionSnapshot,
  type ProcessClient,
  type Readiness,
} from "@wright/process-client";

const process = {
  workspace_id: "fixture",
  source_path: "workflows/fixture.wflow",
  source_digest: "a".repeat(64),
};
const initial: InteractionSnapshot = {
  context: { process, generated_at: new Date().toISOString() },
  state: "preparing",
  inputs: [
    {
      input_id: "brief",
      block_id: "brief",
      port_id: "out",
      title: "Requirements",
      required: true,
      value_schema: { type: "string" },
    },
  ],
};
const frozen = {
  process,
  snapshot_id: "inputs-fixture",
  created_at: new Date().toISOString(),
  digest: "b".repeat(64),
  bindings: [],
};
const ready: Readiness = {
  process,
  assessment_id: "ready-fixture",
  assessed_at: new Date().toISOString(),
  input_digest: frozen.digest,
  state: "ready",
  expires_at: new Date(Date.now() + 60000).toISOString(),
};
const waiting: InteractionSnapshot = {
  context: { ...initial.context, run_id: "run-fixture" },
  state: "waiting_human",
  interactions: [
    {
      checkpoint_id: "review-fixture",
      step_id: "review",
      kind: "review",
      subject_digest: "c".repeat(64),
      instructions: "Inspect the fixture output.",
      decisions: ["approved", "changes_requested"],
      state: "waiting",
    },
  ],
  actions: [
    {
      action_id: "review-fixture",
      operation: "review",
      title: "Review",
      enabled: true,
      checkpoint_id: "review-fixture",
      subject_digest: "c".repeat(64),
    },
  ],
};
function client() {
  return {
    process,
    getSnapshot: vi.fn().mockResolvedValue({
      ...initial,
      readiness: ready,
      actions: [
        {
          action_id: "start",
          operation: "start",
          title: "Start process",
          enabled: true,
          subject_digest: frozen.digest,
        },
      ],
    }),
    setInputs: vi.fn().mockResolvedValue(frozen),
    checkReadiness: vi.fn().mockResolvedValue(ready),
    start: vi.fn().mockResolvedValue({ run_id: "run-fixture" }),
    decide: vi.fn().mockResolvedValue(waiting),
    respond: vi.fn(),
    requestAction: vi.fn(),
    cancel: vi.fn(),
    uploadInput: vi.fn(),
    navigate: vi.fn(),
  } as unknown as ProcessClient;
}
afterEach(() => {
  cleanup();
  sessionStorage.clear();
  vi.restoreAllMocks();
});

it("does no process work on mount or readonly preview", async () => {
  const c = client();
  render(<WorkingControls client={c} snapshot={initial} readOnly />);
  expect(
    screen.getByRole("button", { name: "Check inputs and readiness" }),
  ).toBeDisabled();
  expect(screen.getByRole("button", { name: "Start process" })).toBeDisabled();
  expect(c.setInputs).not.toHaveBeenCalled();
  expect(c.start).not.toHaveBeenCalled();
  expect(c.getSnapshot).not.toHaveBeenCalled();
});
it("freezes explicit input choices, checks those inputs and starts only after a click", async () => {
  const c = client();
  render(<WorkingControls client={c} snapshot={initial} readOnly={false} />);
  fireEvent.change(screen.getByRole("textbox", { name: /Requirements/ }), {
    target: { value: "Supplied requirement" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Check inputs and readiness" }),
  );
  await waitFor(() =>
    expect(c.checkReadiness).toHaveBeenCalledWith(frozen, {
      signal: expect.any(AbortSignal),
    }),
  );
  expect(c.setInputs).toHaveBeenCalledWith(
    [
      {
        kind: "value",
        input_id: "brief",
        value: "Supplied requirement",
        provenance: "supplied",
      },
    ],
    { signal: expect.any(AbortSignal) },
  );
  expect(c.start).not.toHaveBeenCalled();
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Start process" })).toBeEnabled(),
  );
  fireEvent.click(screen.getByRole("button", { name: "Start process" }));
  await waitFor(() => expect(c.start).toHaveBeenCalledTimes(1));
  expect(vi.mocked(c.start).mock.calls[0][0]).toBe(frozen);
  expect(vi.mocked(c.start).mock.calls[0][1]).toBeTruthy();
});
it("invalidates readiness after an input edit", async () => {
  const c = client();
  render(<WorkingControls client={c} snapshot={initial} readOnly={false} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Check inputs and readiness" }),
  );
  await waitFor(() =>
    expect(screen.getByRole("button", { name: "Start process" })).toBeEnabled(),
  );
  fireEvent.change(screen.getByRole("textbox", { name: /Requirements/ }), {
    target: { value: "Changed requirement" },
  });
  expect(screen.getByRole("button", { name: "Start process" })).toBeDisabled();
  expect(c.start).not.toHaveBeenCalled();
});
it.each(["disabled", "foreign-subject", "missing"])(
  "requires a backend-permitted start for the frozen input: %s",
  async (condition) => {
    const c = client();
    vi.mocked(c.getSnapshot).mockResolvedValue({
      ...initial,
      readiness: ready,
      actions:
        condition === "missing"
          ? []
          : [
              {
                action_id: "start",
                operation: "start",
                title: "Start process",
                enabled: condition !== "disabled",
                subject_digest:
                  condition === "foreign-subject"
                    ? "d".repeat(64)
                    : frozen.digest,
              },
            ],
    });
    render(<WorkingControls client={c} snapshot={initial} readOnly={false} />);
    fireEvent.click(
      screen.getByRole("button", { name: "Check inputs and readiness" }),
    );
    await waitFor(() =>
      expect(c.getSnapshot).toHaveBeenCalledWith({
        inputSnapshotId: frozen.snapshot_id,
        signal: expect.any(AbortSignal),
      }),
    );
    expect(
      screen.getByRole("button", { name: "Start process" }),
    ).toBeDisabled();
    expect(c.start).not.toHaveBeenCalled();
  },
);
it("rejects a preparation projection for a different accepted source", async () => {
  const c = client();
  vi.mocked(c.getSnapshot).mockResolvedValue({
    ...initial,
    context: {
      ...initial.context,
      process: { ...process, source_digest: "d".repeat(64) },
    },
  });
  render(<WorkingControls client={c} snapshot={initial} readOnly={false} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Check inputs and readiness" }),
  );
  await screen.findByText("Wright could not confirm this operation.");
  expect(screen.getByRole("button", { name: "Start process" })).toBeDisabled();
  expect(c.start).not.toHaveBeenCalled();
});
it("retains exact review intent before calling the scoped client", async () => {
  const c = client();
  vi.mocked(c.decide).mockImplementation(async (request) => {
    const retained = JSON.parse(
      sessionStorage.getItem(sessionStorage.key(0)!)!,
    );
    expect(retained.requestId).toBe(request.requestId);
    expect(retained.checkpointId).toBe("review-fixture");
    expect(retained.subjectDigest).toBe("c".repeat(64));
    return waiting;
  });
  render(<WorkingControls client={c} snapshot={waiting} readOnly={false} />);
  fireEvent.click(screen.getByRole("button", { name: /^Approve$/ }));
  await waitFor(() => expect(c.decide).toHaveBeenCalledTimes(1));
  expect(vi.mocked(c.decide).mock.calls[0][0]).toMatchObject({
    checkpointId: "review-fixture",
    subjectDigest: "c".repeat(64),
    decision: "approved",
  });
  await waitFor(() => expect(sessionStorage.length).toBe(0));
});
it("cannot send a mutation when request persistence fails", async () => {
  const c = client();
  vi.spyOn(sessionStorage, "setItem").mockImplementation(() => {
    throw new Error("Storage unavailable");
  });
  render(<WorkingControls client={c} snapshot={waiting} readOnly={false} />);
  fireEvent.click(screen.getByRole("button", { name: /^Approve$/ }));
  await waitFor(() =>
    expect(
      screen.getByText("Wright could not confirm this operation."),
    ).toBeVisible(),
  );
  expect(c.decide).not.toHaveBeenCalled();
});
it("restores uncertain intent without replay and reconciles only the exact decision receipt", async () => {
  const c = client();
  vi.mocked(c.getSnapshot).mockResolvedValue(waiting);
  vi.mocked(c.decide).mockRejectedValue(
    new ProcessClientError({
      code: "OUTCOME_UNKNOWN",
      message: "Unknown receipt",
      correction: "Reconcile",
    }),
  );
  const view = render(
    <WorkingControls client={c} snapshot={waiting} readOnly={false} />,
  );
  fireEvent.click(screen.getByRole("button", { name: /^Approve$/ }));
  await screen.findByRole("button", { name: "Reconcile recorded request" });
  const request = vi.mocked(c.decide).mock.calls[0][0];
  view.unmount();
  render(<WorkingControls client={c} snapshot={waiting} readOnly={false} />);
  expect(screen.getByRole("button", { name: /^Approve$/ })).toBeDisabled();
  expect(c.decide).toHaveBeenCalledTimes(1);
  fireEvent.click(
    screen.getByRole("button", { name: "Reconcile recorded request" }),
  );
  await waitFor(() => expect(c.getSnapshot).toHaveBeenCalledTimes(1));
  expect(sessionStorage.length).toBe(1);
  expect(c.decide).toHaveBeenCalledTimes(1);
  vi.mocked(c.getSnapshot).mockResolvedValue({
    ...waiting,
    interactions: [
      {
        ...waiting.interactions![0],
        decision: {
          decision: "approved",
          actor: "controlled-test",
          request_id: request.requestId,
        },
      },
    ],
  });
  await waitFor(() =>
    expect(
      screen.getByRole("button", { name: "Reconcile recorded request" }),
    ).toBeEnabled(),
  );
  fireEvent.click(
    screen.getByRole("button", { name: "Reconcile recorded request" }),
  );
  await waitFor(() => expect(sessionStorage.length).toBe(0));
  expect(c.decide).toHaveBeenCalledTimes(1);
});
it("keeps readonly reviews and disabled backend actions disabled", () => {
  const c = client();
  const view = render(
    <WorkingControls client={c} snapshot={waiting} readOnly />,
  );
  expect(screen.getByRole("button", { name: /^Approve$/ })).toBeDisabled();
  view.rerender(
    <WorkingControls
      client={c}
      snapshot={{
        ...waiting,
        actions: [{ ...waiting.actions![0], enabled: false }],
      }}
      readOnly={false}
    />,
  );
  expect(screen.getByRole("button", { name: /^Approve$/ })).toBeDisabled();
  expect(c.decide).not.toHaveBeenCalled();
});

it("prevents a second click while the first review is unresolved", async () => {
  const c = client();
  vi.mocked(c.decide).mockImplementation(() => new Promise(() => {}));
  render(<WorkingControls client={c} snapshot={waiting} readOnly={false} />);
  const button = screen.getByRole("button", { name: /^Approve$/ });
  fireEvent.click(button);
  fireEvent.click(button);
  await waitFor(() => expect(c.decide).toHaveBeenCalledTimes(1));
  expect(button).toBeDisabled();
  expect(
    screen.getByText("Waiting for Wright to confirm the recorded request…"),
  ).toBeVisible();
  expect(sessionStorage.length).toBe(1);
});

it("does not release uncertain intent from a foreign run's receipt", async () => {
  const c = client();
  const requestId = "request-retained";
  sessionStorage.setItem(
    "wright-working-control:" +
      JSON.stringify([
        process.workspace_id,
        process.source_path,
        process.source_digest,
        "run-fixture",
      ]),
    JSON.stringify({
      version: 1,
      scope: JSON.stringify([
        process.workspace_id,
        process.source_path,
        process.source_digest,
        "run-fixture",
      ]),
      kind: "review",
      requestId,
      checkpointId: "review-fixture",
      subjectDigest: "c".repeat(64),
      runId: "run-fixture",
    }),
  );
  vi.mocked(c.getSnapshot).mockResolvedValue({
    ...waiting,
    context: { ...waiting.context, run_id: "foreign-run" },
    interactions: [
      {
        ...waiting.interactions![0],
        decision: {
          decision: "approved",
          actor: "controlled-test",
          request_id: requestId,
        },
      },
    ],
  });
  render(<WorkingControls client={c} snapshot={waiting} readOnly={false} />);
  fireEvent.click(
    await screen.findByRole("button", { name: "Reconcile recorded request" }),
  );
  await screen.findByText("Wright could not confirm this operation.");
  expect(sessionStorage.length).toBe(1);
  expect(c.decide).not.toHaveBeenCalled();
});

it("does not start after a ready assessment expires", async () => {
  const c = client();
  vi.mocked(c.checkReadiness).mockResolvedValue({
    ...ready,
    expires_at: new Date(Date.now() - 1000).toISOString(),
  });
  render(<WorkingControls client={c} snapshot={initial} readOnly={false} />);
  fireEvent.click(
    screen.getByRole("button", { name: "Check inputs and readiness" }),
  );
  await waitFor(() => expect(c.getSnapshot).toHaveBeenCalledTimes(1));
  expect(screen.getByRole("button", { name: "Start process" })).toBeDisabled();
  expect(c.start).not.toHaveBeenCalled();
});

it.each([null, undefined])(
  "permits exact prepared inputs when readiness has no expiring choice (%s)",
  async (expires_at) => {
    const c = client();
    vi.mocked(c.checkReadiness).mockResolvedValue({ ...ready, expires_at });
    render(<WorkingControls client={c} snapshot={initial} readOnly={false} />);
    fireEvent.click(
      screen.getByRole("button", { name: "Check inputs and readiness" }),
    );
    await waitFor(() =>
      expect(
        screen.getByRole("button", { name: "Start process" }),
      ).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Start process" }));
    await waitFor(() => expect(c.start).toHaveBeenCalledTimes(1));
    expect(c.start).toHaveBeenCalledWith(frozen, expect.any(String));
  },
);
