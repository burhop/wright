import { useEffect, useState } from "react";

import type { SurfaceDescriptor } from "../../services/surfaces/surface-contract";
import {
  getLiveApp,
  getLiveAppHealth,
  getLiveAppLogs,
  operateLiveApp,
  type LiveAppHealth,
  type LiveAppLogs,
  type LiveAppOperation,
  type LiveAppRuntime,
} from "../../services/surfaces/surface-client";

interface Props {
  readonly descriptor: SurfaceDescriptor;
  readonly sessionId: string;
  readonly onRuntimeChange?: (runtime: LiveAppRuntime) => void;
}

const fallbackActions = (
  state: SurfaceDescriptor["lifecycle"],
): readonly { operation: LiveAppOperation; label: string }[] => {
  if (state === "declared") return [{ operation: "start", label: "Start application" }];
  if (state === "failed") return [{ operation: "retry", label: "Retry application" }];
  if (state === "stopped") return [{ operation: "restart", label: "Start application again" }];
  if (state === "ready" || state === "unhealthy") {
    return [
      { operation: "restart", label: "Restart application" },
      { operation: "stop", label: "Stop application" },
    ];
  }
  return [];
};

export function LiveAppControls({ descriptor, sessionId, onRuntimeChange }: Props) {
  const [runtime, setRuntime] = useState<LiveAppRuntime | null>(null);
  const [health, setHealth] = useState<LiveAppHealth | null>(null);
  const [logs, setLogs] = useState<LiveAppLogs | null>(null);
  const [busy, setBusy] = useState<LiveAppOperation | "health" | "logs" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const hasInstance = descriptor.instance !== null;

  useEffect(() => {
    setRuntime(null);
    setHealth(null);
    setLogs(null);
    if (!hasInstance) return;
    void getLiveApp(descriptor.surfaceId, descriptor.workspaceId, sessionId)
      .then(setRuntime)
      .catch((reason) => setError(reason instanceof Error ? reason.message : String(reason)));
  }, [descriptor.instance?.generation, descriptor.surfaceId, descriptor.workspaceId, hasInstance, sessionId]);

  const state = runtime?.state ?? descriptor.lifecycle;
  const actions = runtime?.actions ?? fallbackActions(state);

  const operate = async (operation: LiveAppOperation) => {
    setBusy(operation);
    setError(null);
    try {
      const next = await operateLiveApp(
        descriptor.surfaceId,
        descriptor.workspaceId,
        sessionId,
        operation,
      );
      setRuntime(next);
      setHealth(null);
      onRuntimeChange?.(next);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setBusy(null);
    }
  };

  const inspectHealth = async () => {
    setBusy("health");
    setError(null);
    try {
      setHealth(
        await getLiveAppHealth(
          descriptor.surfaceId,
          descriptor.workspaceId,
          sessionId,
        ),
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setBusy(null);
    }
  };

  const inspectLogs = async () => {
    setBusy("logs");
    setError(null);
    try {
      setLogs(
        await getLiveAppLogs(
          descriptor.surfaceId,
          descriptor.workspaceId,
          sessionId,
        ),
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : String(reason));
    } finally {
      setBusy(null);
    }
  };

  return (
    <section aria-label="Managed application controls" data-testid="live-app-controls">
      <p role="status" aria-live="polite">
        Application state: {state}.
        {runtime?.failure ? ` ${runtime.failure.message}` : ""}
      </p>
      <div>
        {actions.map((action) => (
          <button
            key={action.operation}
            type="button"
            data-operation={action.operation}
            disabled={busy !== null}
            onClick={() => void operate(action.operation)}
          >
            {busy === action.operation ? `${action.label}…` : action.label}
          </button>
        ))}
        {hasInstance && state !== "stopped" && (
          <>
            <button type="button" disabled={busy !== null} onClick={() => void inspectHealth()}>
              Check application health
            </button>
            <button type="button" disabled={busy !== null} onClick={() => void inspectLogs()}>
              View application logs
            </button>
          </>
        )}
      </div>
      {health && (
        <p role="note">
          Health: {health.ok === null ? "not declared" : health.ok ? "healthy" : "unhealthy"}. {health.message}
        </p>
      )}
      {logs && (
        <div role="log" aria-label="Managed application logs" aria-live="polite">
          {logs.entries.length === 0 ? (
            <p>No captured log entries.</p>
          ) : (
            <ol>
              {logs.entries.map((entry) => (
                <li key={entry.sequence}>
                  <span>{entry.stream}: </span>
                  <span>{entry.message}</span>
                </li>
              ))}
            </ol>
          )}
          {logs.droppedBytes > 0 && <p>{logs.droppedBytes} log bytes were dropped by policy.</p>}
        </div>
      )}
      {error && <p role="alert">{error}</p>}
    </section>
  );
}
