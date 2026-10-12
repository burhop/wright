import { act, renderHook, waitFor } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { useWorkflowReasoningStatus } from "./useWorkflowReasoningStatus";
import type { WorkflowReasoningWait } from "../../services/desktop-reasoning-status";

const wait = (runId: string): WorkflowReasoningWait => ({ runId, requestId: "request", queuedAt: "2026-10-12T01:09:23Z", label: "Waiting for desktop chat", detail: "Continue in the chat." });

it("drops a stale observation on run change and aborts only status reads", async () => {
  let resolveOld!: (value: WorkflowReasoningWait) => void;
  const read = vi.fn()
    .mockImplementationOnce(() => new Promise<WorkflowReasoningWait>((resolve) => { resolveOld = resolve; }))
    .mockResolvedValueOnce(wait("run-2"));
  const view = renderHook(({ runId }) => useWorkflowReasoningStatus(runId, read), { initialProps: { runId: "run-1" } });
  await waitFor(() => expect(read).toHaveBeenCalledOnce());
  const oldSignal = read.mock.calls[0][1] as AbortSignal;
  view.rerender({ runId: "run-2" });
  await waitFor(() => expect(view.result.current.wait?.runId).toBe("run-2"));
  expect(oldSignal.aborted).toBe(true);
  await act(async () => resolveOld(wait("run-1")));
  expect(view.result.current.wait?.runId).toBe("run-2");
  const currentSignal = read.mock.calls[1][1] as AbortSignal;
  view.unmount();
  expect(currentSignal.aborted).toBe(true);
});

it("does not poll a finished run, and rejects a response for another run", async () => {
  const read = vi.fn().mockResolvedValue(wait("wrong-run"));
  const view = renderHook(({ runId }: { runId?: string }) => useWorkflowReasoningStatus(runId, read), { initialProps: { runId: undefined as string | undefined } });
  expect(read).not.toHaveBeenCalled();
  view.rerender({ runId: "run-1" });
  await waitFor(() => expect(view.result.current.error).toContain("another run"));
  expect(view.result.current.wait).toBeNull();
  const calls = read.mock.calls.length;
  view.rerender({ runId: undefined });
  expect(view.result.current.wait).toBeNull();
  expect(read.mock.calls.length).toBe(calls);
  view.unmount();
});
