import { useCallback, useEffect, useRef, useState } from "react";

import {
  workspaceService,
  type RivetCallApproval,
  type RivetWorkflowRun,
} from "../../services/workspace-service";

type RunEvent = {
  sequence: number;
  kind: string;
  payload: Record<string, unknown>;
};

const activeStates = new Set(["queued", "running", "cancelling"]);

export function RivetWorkflowRun({
  sessionId,
  run,
  onRunUpdate,
  onCancel,
}: {
  sessionId: string;
  run: RivetWorkflowRun;
  onRunUpdate: (run: RivetWorkflowRun) => void;
  onCancel: () => void | Promise<void>;
}) {
  const [approvals, setApprovals] = useState<RivetCallApproval[]>([]);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [selected, setSelected] = useState<RivetCallApproval | null>(null);
  const [message, setMessage] = useState("Run evidence is current.");
  const dialogRef = useRef<HTMLDivElement>(null);
  const offeredApprovals = useRef(new Set<string>());
  const onRunUpdateRef = useRef(onRunUpdate);

  useEffect(() => {
    onRunUpdateRef.current = onRunUpdate;
  }, [onRunUpdate]);

  const refresh = useCallback(async () => {
    try {
      const [current, currentApprovals, history] = await Promise.all([
        workspaceService.getRivetWorkflowRun(sessionId, run.run_id),
        workspaceService.getRivetCallApprovals(sessionId, run.run_id),
        workspaceService.getRivetWorkflowHistory(sessionId, run.run_id),
      ]);
      onRunUpdateRef.current(current);
      setApprovals(currentApprovals);
      setEvents(history);
      const pending = currentApprovals.find((item) => item.state === "pending");
      if (
        pending &&
        !selected &&
        !offeredApprovals.current.has(pending.approval_id)
      ) {
        offeredApprovals.current.add(pending.approval_id);
        setSelected(pending);
      }
      setMessage(
        pending
          ? "An exact MCP call is waiting for your decision."
          : `Run is ${current.state}.`,
      );
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Run evidence is unavailable.",
      );
    }
  }, [run.run_id, selected, sessionId]);

  useEffect(() => {
    void refresh();
    if (!activeStates.has(run.state)) return;
    const timer = window.setInterval(() => void refresh(), 750);
    return () => window.clearInterval(timer);
  }, [refresh, run.state]);

  useEffect(() => {
    if (selected) dialogRef.current?.focus();
  }, [selected]);

  const decide = async (decision: "approved" | "denied") => {
    if (!selected) return;
    try {
      await workspaceService.decideRivetCallApproval(
        sessionId,
        run.run_id,
        selected,
        decision,
      );
      setSelected(null);
      await refresh();
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Call decision failed.",
      );
    }
  };

  return (
    <section
      aria-label={`Run ${run.run_id}`}
      data-testid={`rivet-run-${run.run_id}`}
      style={{ marginTop: "var(--space-sm)" }}
    >
      <p aria-live="polite" style={{ fontSize: "0.72rem" }}>
        {message}
      </p>
      <ol aria-label="Run timeline" style={{ paddingLeft: "1.25rem" }}>
        {events.slice(-12).map((event) => (
          <li key={event.sequence} style={{ fontSize: "0.7rem" }}>
            {event.kind}
            {typeof event.payload.phase === "string"
              ? ` · ${event.payload.phase}`
              : ""}
          </li>
        ))}
      </ol>
      {activeStates.has(run.state) && (
        <button type="button" onClick={() => void onCancel()}>
          Cancel run
        </button>
      )}
      {run.manifest && (
        <details>
          <summary>Run evidence</summary>
          <small>
            Terminal state {String(run.manifest.terminal_state || run.state)} ·{" "}
            manifest{" "}
            {String(run.manifest.manifest_digest || "unavailable").slice(0, 12)}
          </small>
          {run.manifest.residue_possible === true && (
            <p role="alert">
              Cleanup could not be confirmed. The child application may still
              contain partial changes. Inspect its status before retrying.
              Recovery code:{" "}
              {String(run.manifest.recovery_code || "unavailable")}.
            </p>
          )}
          {run.manifest.cancellation_acknowledged === true &&
            run.manifest.residue_possible !== true && (
              <p>Cancellation was acknowledged and cleanup completed.</p>
            )}
        </details>
      )}
      {selected && (
        <div
          ref={dialogRef}
          role="dialog"
          aria-modal="true"
          aria-labelledby="rivet-call-approval-title"
          tabIndex={-1}
          onKeyDown={(event) => {
            if (event.key === "Escape") setSelected(null);
          }}
          style={{
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-md)",
            padding: "var(--space-md)",
            marginTop: "var(--space-sm)",
            background: "var(--color-surface)",
          }}
        >
          <h3 id="rivet-call-approval-title">Approve this exact MCP call?</h3>
          <p>
            Node {selected.node_id} will call {selected.qualified_tool_name}.
            This decision applies once, only to the reviewed arguments shown
            below.
          </p>
          <pre style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
            {JSON.stringify(selected.argument_summary, null, 2)}
          </pre>
          <p>Required safety gates: {selected.required_gates.join(", ")}</p>
          <button type="button" onClick={() => void decide("approved")}>
            Approve exact call
          </button>{" "}
          <button type="button" onClick={() => void decide("denied")}>
            Deny
          </button>{" "}
          <button type="button" onClick={() => setSelected(null)}>
            Close
          </button>
        </div>
      )}
      {!selected && approvals.some((item) => item.state === "pending") && (
        <button
          type="button"
          onClick={() =>
            setSelected(
              approvals.find((item) => item.state === "pending") || null,
            )
          }
        >
          Review pending call
        </button>
      )}
    </section>
  );
}
