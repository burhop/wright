import { useEffect, useState } from "react";
import {
  nativeRunApi,
  NativeProcessError,
  type NativeRun,
} from "../../services/native-process";
export function activeRun(state: string) {
  return state === "queued" || state === "running";
}
export function nativeErrorText(failure: unknown) {
  return failure instanceof NativeProcessError
    ? `${failure.detail.message} ${failure.detail.recovery}`
    : failure instanceof Error
      ? failure.message
      : "The native service request failed.";
}
/** One request at a time; cancel/stale selection cleanup aborts old polls. Terminal runs stop polling. */
export function useNativeRun(
  sessionId: string,
  runId: string | null,
  refresh: number,
) {
  const [cache, setCache] = useState<{
    run: NativeRun;
    receivedAt: string;
  } | null>(null);
  const [failure, setFailure] = useState<{
    runId: string;
    message: string;
  } | null>(null);
  useEffect(() => {
    if (!runId) return;
    const controller = new AbortController();
    let timer = 0;
    async function poll() {
      try {
        const run = await nativeRunApi.get(
          sessionId,
          runId!,
          controller.signal,
        );
        if (controller.signal.aborted) return;
        if (run.run_id !== runId)
          throw new Error("The service returned a different run identity.");
        setCache((previous) =>
          previous?.run.run_id === run.run_id &&
          previous.run.last_sequence > run.last_sequence
            ? previous
            : { run, receivedAt: new Date().toISOString() },
        );
        setFailure(null);
        if (activeRun(run.state))
          timer = window.setTimeout(() => void poll(), 1000);
      } catch (error) {
        if (controller.signal.aborted) return;
        setFailure({ runId: runId!, message: nativeErrorText(error) });
        timer = window.setTimeout(() => void poll(), 5000);
      }
    }
    void poll();
    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [sessionId, runId, refresh]);
  return {
    run: cache?.run.run_id === runId ? cache.run : null,
    receivedAt: cache?.run.run_id === runId ? cache.receivedAt : null,
    error: failure?.runId === runId ? failure.message : "",
  };
}
