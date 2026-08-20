import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";

import {
  workspaceService,
  type RivetCallApproval,
  type RivetRunInspection,
  type RivetRunEvidence,
  type RivetWorkflowRun,
} from "../../services/workspace-service";
import { RivetRunInspector } from "../workflows/RivetRunInspector";

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
  const [evidence, setEvidence] = useState<RivetRunEvidence | null>(null);
  const [inspection, setInspection] = useState<RivetRunInspection | null>(null);
  const [selected, setSelected] = useState<RivetCallApproval | null>(null);
  const [message, setMessage] = useState("Run evidence is current.");
  const dialogRef = useRef<HTMLDivElement>(null);
  const reviewButtonRef = useRef<HTMLButtonElement>(null);
  const offeredApprovals = useRef(new Set<string>());
  const onRunUpdateRef = useRef(onRunUpdate);

  useEffect(() => {
    onRunUpdateRef.current = onRunUpdate;
  }, [onRunUpdate]);

  const refresh = useCallback(async () => {
    try {
      const [current, currentApprovals, history, durableEvidence, currentInspection] =
        await Promise.all([
          workspaceService.getRivetWorkflowRun(sessionId, run.run_id),
          workspaceService.getRivetCallApprovals(sessionId, run.run_id),
          workspaceService.getRivetWorkflowHistory(sessionId, run.run_id),
          workspaceService
            .getRivetRunEvidence(sessionId, run.run_id)
            .catch(() => null),
          workspaceService
            .getRivetRunInspection(sessionId, run.run_id)
            .catch(() => null),
        ]);
      onRunUpdateRef.current(current);
      setApprovals(currentApprovals);
      setEvents(history);
      setEvidence(durableEvidence);
      setInspection(currentInspection);
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

  useLayoutEffect(() => {
    if (selected) dialogRef.current?.focus();
  }, [selected]);

  const closeApproval = () => {
    setSelected(null);
    window.setTimeout(() => reviewButtonRef.current?.focus(), 0);
  };

  const decide = async (decision: "approved" | "denied") => {
    if (!selected) return;
    try {
      await workspaceService.decideRivetCallApproval(
        sessionId,
        run.run_id,
        selected,
        decision,
      );
      closeApproval();
      await refresh();
    } catch (error) {
      setMessage(
        error instanceof Error ? error.message : "Call decision failed.",
      );
    }
  };

  const manifest = evidence?.manifest || run.manifest || null;
  const cancellation =
    manifest?.cancellation && typeof manifest.cancellation === "object"
      ? (manifest.cancellation as Record<string, unknown>)
      : null;
  const residuePossible =
    cancellation?.residue_state === "possible" ||
    manifest?.residue_possible === true;
  const cancellationAcknowledged =
    cancellation?.child_acknowledged === true ||
    manifest?.cancellation_acknowledged === true;
  const recoveryCode =
    cancellation?.recovery_code || manifest?.recovery_code || "unavailable";
  const timeline: Array<Record<string, unknown>> = evidence
    ? evidence.timeline
    : events.map((event) => ({
        sequence: event.sequence,
        kind: event.kind,
        ...event.payload,
      }));

  return (
    <section
      aria-label={`Run ${run.run_id}`}
      data-testid={`rivet-run-${run.run_id}`}
      style={{ marginTop: "var(--space-sm)" }}
    >
      <p aria-live="polite" style={{ fontSize: "0.72rem" }}>
        {message}
      </p>
      <ol
        aria-label="Run timeline"
        data-testid="rivet-run-timeline"
        style={{ paddingLeft: "1.25rem", overflowWrap: "anywhere" }}
      >
        {timeline.slice(-50).map((event, index) => (
          <li
            key={String(event.sequence || event.call_id || index)}
            style={{ fontSize: "0.7rem" }}
          >
            {String(event.kind || "evidence")}
            {typeof event.phase === "string" ? ` · ${event.phase}` : ""}
            {typeof event.qualified_tool_name === "string"
              ? ` · ${event.qualified_tool_name}`
              : ""}
            {typeof event.state === "string" ? ` · ${event.state}` : ""}
          </li>
        ))}
      </ol>
      {activeStates.has(run.state) && (
        <button type="button" onClick={() => void onCancel()}>
          Cancel run
        </button>
      )}
      <RivetRunInspector
        inspection={inspection}
        recentRuns={inspection ? [inspection.run] : []}
        currentRevision={run.revision}
        elapsedMs={inspection?.run.duration_ms || run.duration_ms || 0}
        onSelectRun={() => undefined}
        onExportEvidence={() => {
          void workspaceService.exportRivetRunEvidence(sessionId, run.run_id);
        }}
      />
      {manifest && (
        <details data-testid="rivet-run-evidence">
          <summary>Run evidence</summary>
          <small>
            Terminal state {String(manifest.terminal_state || run.state)} ·
            manifest{" "}
            {String(manifest.manifest_digest || "unavailable").slice(0, 12)}
          </small>
          {!inspection?.diagnostic && Boolean(manifest.reason_code) && (
            <p>Failure boundary: {String(manifest.reason_code)}.</p>
          )}
          {residuePossible && (
            <p role="alert">
              Cleanup could not be confirmed. The child application may still
              contain partial changes. Inspect its status before retrying.
              Recovery code: {String(recoveryCode)}.
            </p>
          )}
          {cancellationAcknowledged && !residuePossible && (
            <p>Cancellation was acknowledged and cleanup completed.</p>
          )}
          {evidence && (
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(13rem, 1fr))",
                gap: "var(--space-sm)",
                marginTop: "var(--space-sm)",
              }}
            >
              <section aria-label="Evidence accounting">
                <h4>Accounting</h4>
                <p>
                  {String(evidence.accounting.binding_count || 0)} bindings ·{" "}
                  {String(evidence.accounting.child_call_count || 0)} child
                  calls · {String(evidence.accounting.approval_count || 0)}{" "}
                  approvals · {String(evidence.accounting.artifact_count || 0)}{" "}
                  artifacts
                </p>
                {Number(evidence.accounting.denied_before_child_count || 0) >
                  0 && (
                  <p>
                    {String(evidence.accounting.denied_before_child_count)}{" "}
                    denied before any child received the call.
                  </p>
                )}
              </section>
              <section aria-label="Reproducibility comparison">
                <h4>Reproducibility</h4>
                <p role="status">{evidence.reproducibility.summary}</p>
                {evidence.reproducibility.differences.length > 0 && (
                  <ul>
                    {evidence.reproducibility.differences.map((difference) => (
                      <li key={difference.code}>
                        {difference.code}: {difference.recovery_action}
                      </li>
                    ))}
                  </ul>
                )}
              </section>
              <section aria-label="Authorized artifacts">
                <h4>Artifacts</h4>
                {evidence.artifacts.length ? (
                  <ul>
                    {evidence.artifacts.map((artifact, index) => (
                      <li key={String(artifact.artifact_id || index)}>
                        {String(artifact.label || artifact.artifact_id)}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>No authorized artifacts recorded.</p>
                )}
              </section>
            </div>
          )}
          <button
            type="button"
            onClick={() =>
              void workspaceService
                .exportRivetRunEvidence(sessionId, run.run_id)
                .catch((error) =>
                  setMessage(
                    error instanceof Error
                      ? error.message
                      : "Run evidence export failed.",
                  ),
                )
            }
          >
            Export evidence JSON
          </button>
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
            if (event.key === "Escape") closeApproval();
            if (event.key !== "Tab" || !dialogRef.current) return;
            const controls = Array.from(
              dialogRef.current.querySelectorAll<HTMLButtonElement>(
                "button:not([disabled])",
              ),
            );
            if (!controls.length) return;
            const first = controls[0];
            const last = controls[controls.length - 1];
            if (event.shiftKey && document.activeElement === first) {
              event.preventDefault();
              last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
              event.preventDefault();
              first.focus();
            }
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
          <button type="button" onClick={closeApproval}>
            Close
          </button>
        </div>
      )}
      {!selected && approvals.some((item) => item.state === "pending") && (
        <button
          ref={reviewButtonRef}
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
