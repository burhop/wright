import { useEffect, useState } from "react";
import type {
  WorkflowReasoningStatusReader,
  WorkflowReasoningWait,
} from "../../services/desktop-reasoning-status";

const pageVisible = () => document.visibilityState !== "hidden";

export function useWorkflowReasoningStatus(
  runId: string | undefined,
  read: WorkflowReasoningStatusReader | undefined,
) {
  const [state, setState] = useState<{
    runId?: string;
    read?: WorkflowReasoningStatusReader;
    wait: WorkflowReasoningWait | null;
    error: string;
    checkedAt: string;
  }>({ wait: null, error: "", checkedAt: "" });
  useEffect(() => {
    if (!runId || !read) return;
    let current = true;
    let serial = 0;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let request: AbortController | undefined;
    const refresh = async () => {
      if (!current || !pageVisible()) return;
      clearTimeout(timer);
      request?.abort();
      request = new AbortController();
      const token = ++serial;
      try {
        const wait = await read(runId, request.signal);
        if (!current || token !== serial) return;
        if (wait && wait.runId !== runId)
          throw new Error("AI handoff status belongs to another run.");
        setState({
          runId,
          read,
          wait,
          error: "",
          checkedAt: new Date().toISOString(),
        });
      } catch (cause) {
        if (!current || token !== serial) return;
        setState({
          runId,
          read,
          wait: null,
          checkedAt: "",
          error:
            cause instanceof Error
              ? cause.message
              : "AI handoff status is unavailable.",
        });
      } finally {
        if (current && token === serial && pageVisible())
          timer = setTimeout(() => void refresh(), 2000);
      }
    };
    const visible = () => {
      if (document.visibilityState === "hidden") {
        clearTimeout(timer);
        ++serial;
        request?.abort();
      } else void refresh();
    };
    const focus = () => void refresh();
    void refresh();
    document.addEventListener("visibilitychange", visible);
    window.addEventListener("focus", focus);
    return () => {
      current = false;
      ++serial;
      clearTimeout(timer);
      request?.abort(); // Only the status read is cancelled.
      document.removeEventListener("visibilitychange", visible);
      window.removeEventListener("focus", focus);
    };
  }, [runId, read]);
  return runId && read && state.runId === runId && state.read === read
    ? state
    : { wait: null, error: "", checkedAt: "" };
}
