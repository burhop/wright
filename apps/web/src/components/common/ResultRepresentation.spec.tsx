import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ResultRepresentation } from "@wright/ui-kit";
import type { ArtifactRef, InteractionSnapshot, ProcessClient } from "@wright/process-client";

afterEach(cleanup);
beforeEach(() => {
  vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:exact-evidence");
  vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);
});
const hash = "a".repeat(64);
const reference: ArtifactRef = {
  artifact_ref: "outputs/evidence.txt", sha256: hash, result_id: "result-one",
};
function snapshot(ref = reference, runId: string | null = "run-one"): InteractionSnapshot {
  return {
    context: {
      process: { workspace_id: "workspace", source_path: "workflows/example.wflow", source_digest: hash },
      run_id: runId, generated_at: "2026-10-03T00:00:00Z", cursor: 1,
    },
    state: "failed",
    outputs: [{ result_id: ref.result_id!, step_id: "produce", port_id: "out", role: "deliverable", title: "Recorded evidence", representations: [ref] }],
  };
}
function textBlob(text: string): Blob {
  const blob = new Blob([text], { type: "text/plain" });
  Object.defineProperty(blob, "text", { value: async () => text });
  return blob;
}

describe("shared exact result representation reader", () => {
  it("uses the current run and abortable two-argument scoped read", async () => {
    const read = vi.fn<ProcessClient["getRepresentation"]>().mockResolvedValue(textBlob("Exact current evidence"));
    const close = vi.fn();
    const current = snapshot();
    const view = render(<ResultRepresentation client={{ getRepresentation: read }} snapshot={current} reference={reference} onClose={close} />);
    await screen.findByText("Exact current evidence");
    expect(read).toHaveBeenCalledWith(reference, { runId: "run-one", signal: expect.any(AbortSignal) });
    expect(screen.getByRole("link", { name: "Download exact file" })).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Close representation" }));
    expect(close).toHaveBeenCalledTimes(1);
    view.rerender(<ResultRepresentation client={{ getRepresentation: read }} snapshot={{ ...current, context: { ...current.context, cursor: 2 } }} reference={reference} />);
    // The supplied client object changes here, so its read authority is rebound.
    await waitFor(() => expect(read).toHaveBeenCalledTimes(2));
  });
  it("does not reread for a refreshed snapshot when client and exact context are unchanged", async () => {
    const read = vi.fn<ProcessClient["getRepresentation"]>().mockResolvedValue(textBlob("Exact evidence"));
    const client = { getRepresentation: read };
    const current = snapshot();
    const view = render(<ResultRepresentation client={client} snapshot={current} reference={reference} />);
    await screen.findByText("Exact evidence");
    view.rerender(<ResultRepresentation client={client} snapshot={{ ...current, context: { ...current.context, cursor: 2, generated_at: "2026-10-03T00:00:10Z" } }} reference={reference} />);
    expect(read).toHaveBeenCalledTimes(1);
  });
  it("aborts old reads and ignores their late replies after an exact run/result change", async () => {
    let resolveOld!: (blob: Blob) => void;
    const read = vi.fn<ProcessClient["getRepresentation"]>()
      .mockImplementationOnce(() => new Promise(resolve => { resolveOld = resolve; }))
      .mockResolvedValueOnce(textBlob("New exact evidence"));
    const client = { getRepresentation: read };
    const view = render(<ResultRepresentation client={client} snapshot={snapshot()} reference={reference} />);
    await waitFor(() => expect(read).toHaveBeenCalledTimes(1));
    const firstSignal = read.mock.calls[0][1]!.signal!;
    const next = { ...reference, result_id: "result-two", sha256: "b".repeat(64) };
    view.rerender(<ResultRepresentation client={client} snapshot={snapshot(next, "run-two")} reference={next} />);
    await screen.findByText("New exact evidence");
    expect(firstSignal.aborted).toBe(true);
    await act(async () => resolveOld(textBlob("Old untrusted late evidence")));
    expect(screen.queryByText("Old untrusted late evidence")).not.toBeInTheDocument();
    expect(screen.getByText("New exact evidence")).toBeVisible();
  });
  it("requires current result membership and a recorded run before any read", async () => {
    const read = vi.fn<ProcessClient["getRepresentation"]>();
    const client = { getRepresentation: read };
    const view = render(<ResultRepresentation client={client} snapshot={snapshot()} reference={{ ...reference, sha256: "b".repeat(64) }} />);
    expect(screen.getByText(/not part of the current recorded run/)).toBeVisible();
    view.rerender(<ResultRepresentation client={client} snapshot={snapshot(reference, null)} reference={reference} />);
    expect(screen.getByText(/not part of the current recorded run/)).toBeVisible();
    expect(read).not.toHaveBeenCalled();
  });
  it("clears stale output selection and disposes pending reads on close/unmount", async () => {
    const read = vi.fn<ProcessClient["getRepresentation"]>().mockImplementation(() => new Promise(() => {}));
    const client = { getRepresentation: read };
    const view = render(<ResultRepresentation client={client} snapshot={snapshot()} reference={reference} />);
    await waitFor(() => expect(read).toHaveBeenCalledTimes(1));
    const signal = read.mock.calls[0][1]!.signal!;
    view.rerender(<ResultRepresentation client={client} snapshot={{ ...snapshot(), outputs: [] }} reference={reference} />);
    expect(signal.aborted).toBe(true);
    expect(screen.getByText(/not part of the current recorded run/)).toBeVisible();
    view.rerender(<ResultRepresentation client={client} snapshot={snapshot()} reference={null} />);
    expect(view.container).toBeEmptyDOMElement();
    expect(read).toHaveBeenCalledTimes(1);
    view.rerender(<ResultRepresentation client={client} snapshot={snapshot()} reference={reference} />);
    await waitFor(() => expect(read).toHaveBeenCalledTimes(2));
    const unmountSignal = read.mock.calls[1][1]!.signal!;
    view.unmount();
    expect(unmountSignal.aborted).toBe(true);
  });
  it("shows a safe owning-view recovery message and never retries a failed read automatically", async () => {
    const read = vi.fn<ProcessClient["getRepresentation"]>().mockRejectedValue(new Error("Synthetic private diagnostic"));
    render(<ResultRepresentation client={{ getRepresentation: read }} snapshot={snapshot()} reference={reference} />);
    expect(await screen.findByRole("alert")).toHaveTextContent(/Refresh the common working view/);
    expect(screen.queryByText(/Synthetic private diagnostic/)).not.toBeInTheDocument();
    expect(read).toHaveBeenCalledTimes(1);
  });
});
