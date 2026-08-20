import { useCallback, useEffect, useRef, useState } from "react";

import {
  workspaceService,
  type RivetRecentRuns,
  type RivetRunInspection,
} from "../services/workspace-service";

const ACTIVE_STATES = new Set(["queued", "running", "cancelling"]);

interface UseRivetRunInspectionOptions {
  sessionId: string;
  workflowSlug: string | null;
  runId?: string | null;
}

export function useRivetRunInspection({
  sessionId,
  workflowSlug,
  runId = null,
}: UseRivetRunInspectionOptions) {
  const [recent, setRecent] = useState<RivetRecentRuns | null>(null);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(runId);
  const [inspection, setInspection] = useState<RivetRunInspection | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [elapsedMs, setElapsedMs] = useState(0);
  const cursorRef = useRef(0);
  const refreshTokenRef = useRef(0);

  useEffect(() => {
    if (runId) setSelectedRunId(runId);
  }, [runId]);

  const refreshRecent = useCallback(async () => {
    if (!workflowSlug) return null;
    const value = await workspaceService.getRecentRivetRuns(
      sessionId,
      workflowSlug,
    );
    setRecent(value);
    setSelectedRunId((current) => {
      if (runId) return runId;
      if (current && value.runs.some((item) => item.run_id === current)) return current;
      return (
        value.runs.find((item) => ACTIVE_STATES.has(item.state))?.run_id ||
        value.runs[0]?.run_id ||
        null
      );
    });
    return value;
  }, [runId, sessionId, workflowSlug]);

  useEffect(() => {
    let cancelled = false;
    if (!workflowSlug) {
      setRecent(null);
      if (!runId) setSelectedRunId(null);
      return;
    }
    void refreshRecent().catch((caught) => {
      if (!cancelled) {
        setError(caught instanceof Error ? caught.message : "Recent workflow runs are unavailable");
      }
    });
    return () => {
      cancelled = true;
    };
  }, [refreshRecent, runId, workflowSlug]);

  useEffect(() => {
    cursorRef.current = 0;
    setInspection(null);
    setError(null);
    if (!selectedRunId) return;
    let cancelled = false;
    let timer = 0;
    let failures = 0;
    const poll = async () => {
      try {
        const next = await workspaceService.getRivetRunInspection(
          sessionId,
          selectedRunId,
          cursorRef.current,
        );
        if (cancelled) return;
        failures = 0;
        cursorRef.current = Math.max(cursorRef.current, next.progress.last_sequence);
        setInspection((current) => {
          if (!current || current.run.run_id !== next.run.run_id) return next;
          const merged = new Map(
            [...current.events, ...next.events].map((event) => [event.sequence, event]),
          );
          return { ...next, events: [...merged.values()].sort((a, b) => a.sequence - b.sequence) };
        });
        setError(null);
        if (ACTIVE_STATES.has(next.run.state)) {
          timer = window.setTimeout(poll, 500);
        } else {
          void refreshRecent();
        }
      } catch (caught) {
        if (cancelled) return;
        failures += 1;
        setError(caught instanceof Error ? caught.message : "Workflow run inspection is unavailable");
        timer = window.setTimeout(poll, Math.min(4000, 500 * 2 ** failures));
      }
    };
    void poll();
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [selectedRunId, sessionId, refreshRecent]);

  useEffect(() => {
    if (!inspection?.run.started_at || !ACTIVE_STATES.has(inspection.run.state)) {
      setElapsedMs(inspection?.run.duration_ms || 0);
      return;
    }
    const started = Date.parse(inspection.run.started_at);
    const update = () => setElapsedMs(Math.max(0, Date.now() - started));
    update();
    const timer = window.setInterval(update, 250);
    return () => window.clearInterval(timer);
  }, [inspection?.run.duration_ms, inspection?.run.started_at, inspection?.run.state]);

  const selectRun = useCallback((nextRunId: string) => {
    refreshTokenRef.current += 1;
    setSelectedRunId(nextRunId);
  }, []);

  return {
    inspection,
    recentRuns: recent?.runs || [],
    currentRevision: recent?.current_revision ?? null,
    selectedRunId,
    selectRun,
    error,
    elapsedMs,
    refreshRecent,
  };
}
