import { afterEach, describe, expect, it, vi } from "vitest";
import { hostAdapter } from "../src/services/host-adapter";
import { readDesktopReasoningWait } from "../src/services/desktop-reasoning-status";

const scope = { workspaceId: "workspace-1", sessionId: "session-1", runId: "run-1", workspaceName: "dave" };
const pending = () => ({ request: {
  schema_version: "wright.desktop-reasoning/1", workspace_id: scope.workspaceId,
  session_id: scope.sessionId, run_id: scope.runId, request_id: "request-1",
  created_at: "2026-10-12T01:09:23Z", kind: "response",
  binding: { adapter: "openai-desktop-harness", reported_model: null },
} });
const signal = () => new AbortController().signal;
function serve(value: unknown, status = 200) {
  return vi.spyOn(hostAdapter, "fetch").mockResolvedValue(new Response(JSON.stringify(value), { status }));
}
afterEach(() => vi.restoreAllMocks());

describe("desktop reasoning progress", () => {
  it("reads the exact queued run without submitting a reply or claiming model identity", async () => {
    const fetch = serve([pending()]);
    const abortSignal = signal();
    const wait = await readDesktopReasoningWait(scope, abortSignal);
    expect(wait).toMatchObject({ runId: "run-1", requestId: "request-1", label: "Waiting for desktop chat" });
    expect(wait?.detail).toContain("Continue the workflow in dave");
    expect(fetch).toHaveBeenCalledOnce();
    expect(fetch.mock.calls[0][0]).toContain("/api/desktop/reasoning?workspace_id=workspace-1&session_id=session-1");
    expect(fetch.mock.calls[0][1]).toEqual({ method: "GET", signal: abortSignal });
  });

  it("does not show another run's queued task or a completed request", async () => {
    const other = pending(); other.request.run_id = "other-run";
    const fetch = serve([other]);
    expect(await readDesktopReasoningWait(scope, signal())).toBeNull();
    fetch.mockResolvedValue(new Response("[]"));
    expect(await readDesktopReasoningWait(scope, signal())).toBeNull();
  });

  it.each([
    { workspace_id: "other-workspace" }, { session_id: "other-session" },
    { schema_version: "unsupported" }, { created_at: "invalid" },
    { binding: { adapter: "other-agent" } }, { kind: "unsupported" },
  ])("rejects mismatched or invalid handoff identity %j", async (changes) => {
    const task = pending(); Object.assign(task.request, changes);
    serve([task]);
    await expect(readDesktopReasoningWait(scope, signal())).rejects.toThrow();
  });

  it("reports unavailable or ambiguous status without inferring that reasoning is underway", async () => {
    const fetch = serve([], 503);
    await expect(readDesktopReasoningWait(scope, signal())).rejects.toThrow("HTTP 503");
    fetch.mockResolvedValue(new Response(JSON.stringify([pending(), pending()])));
    await expect(readDesktopReasoningWait(scope, signal())).rejects.toThrow("more than one");
  });
});
