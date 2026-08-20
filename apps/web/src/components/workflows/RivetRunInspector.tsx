import { useEffect, useState } from "react";

import type {
  RivetRunInspection,
  RivetRunStep,
  RivetRunSummary,
} from "../../services/workspace-service";
import { RunStateBadge } from "../common/RunStateBadge";
import { RivetRunResult } from "./RivetRunResult";
import { RivetRunStepList } from "./RivetRunStepList";
import "./rivet-run-inspector.css";

type InspectorTab = "outputs" | "steps" | "diagnosis" | "history";

interface RivetRunInspectorProps {
  inspection: RivetRunInspection | null;
  recentRuns: RivetRunSummary[];
  currentRevision: number | null;
  elapsedMs: number;
  error?: string | null;
  onSelectRun: (runId: string) => void;
  onFocusStep?: (step: RivetRunStep) => void;
  onRerun?: () => void;
  onExportEvidence?: () => void;
}

const formatDuration = (milliseconds: number) => {
  if (milliseconds < 1000) return `${milliseconds} ms`;
  const seconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(seconds / 60);
  return minutes ? `${minutes}m ${seconds % 60}s` : `${seconds}s`;
};

export function RivetRunInspector({
  inspection,
  recentRuns,
  currentRevision,
  elapsedMs,
  error,
  onSelectRun,
  onFocusStep,
  onRerun,
  onExportEvidence,
}: RivetRunInspectorProps) {
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<InspectorTab>("outputs");

  useEffect(() => {
    if (
      inspection?.run.state === "failed" ||
      inspection?.run.state === "cancelled"
    ) {
      setOpen(true);
      setTab("diagnosis");
    } else if (
      inspection?.run.state === "running" ||
      inspection?.run.state === "succeeded"
    ) {
      setOpen(true);
    }
  }, [inspection?.run.run_id, inspection?.run.state]);

  const state = inspection?.run.state || "idle";
  return (
    <section
      className={`rivet-run-inspector ${open ? "is-open" : "is-collapsed"}`}
      aria-label="Run Inspector"
      data-testid="rivet-run-inspector"
    >
      <button
        className="rivet-run-inspector__summary"
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
      >
        <strong>Run Inspector</strong>
        {inspection ? (
          <RunStateBadge state={state} />
        ) : (
          <span>No run selected</span>
        )}
        {inspection && (
          <span>
            {formatDuration(elapsedMs || inspection.run.duration_ms || 0)}
          </span>
        )}
        {inspection?.progress.total_steps ? (
          <span>
            {inspection.progress.completed_steps}/
            {inspection.progress.total_steps} steps
          </span>
        ) : null}
        <span aria-hidden="true">{open ? "⌄" : "⌃"}</span>
      </button>
      {open && (
        <div className="rivet-run-inspector__body">
          {error && (
            <div className="rivet-run-inspector__error" role="alert">
              {error}
            </div>
          )}
          <nav aria-label="Run Inspector sections">
            {(
              ["outputs", "steps", "diagnosis", "history"] as InspectorTab[]
            ).map((value) => (
              <button
                key={value}
                type="button"
                aria-current={tab === value ? "page" : undefined}
                onClick={() => setTab(value)}
              >
                {value[0].toUpperCase() + value.slice(1)}
              </button>
            ))}
          </nav>
          <div className="rivet-run-inspector__content">
            {!inspection ? (
              <p className="rivet-run-empty">
                Run this workflow to see status, steps, outputs, and errors
                here.
              </p>
            ) : tab === "outputs" ? (
              <div className="rivet-run-results">
                {!inspection.completeness.outputs_complete && (
                  <p className="rivet-run-warning" role="status">
                    Some output values were bounded. Export contains the same
                    safe retained projection.
                  </p>
                )}
                {inspection.final_outputs.length ? (
                  inspection.final_outputs.map((result) => (
                    <RivetRunResult key={result.result_id} result={result} />
                  ))
                ) : (
                  <p className="rivet-run-empty">
                    This run has no final outputs yet.
                  </p>
                )}
              </div>
            ) : tab === "steps" ? (
              <RivetRunStepList
                steps={inspection.steps}
                onFocusStep={onFocusStep}
              />
            ) : tab === "diagnosis" ? (
              inspection.diagnostic ? (
                <div className="rivet-run-diagnosis">
                  <h3>{inspection.diagnostic.summary}</h3>
                  <p>{inspection.diagnostic.recovery_action}</p>
                  {inspection.diagnostic.residue_possible && (
                    <p className="rivet-run-warning">
                      The target application may contain a partial change.
                      Inspect it before rerunning.
                    </p>
                  )}
                  <div className="rivet-run-actions">
                    {inspection.diagnostic.full_rerun_available && onRerun && (
                      <button type="button" onClick={onRerun}>
                        Run saved revision again
                      </button>
                    )}
                    {onExportEvidence && (
                      <button type="button" onClick={onExportEvidence}>
                        Export technical evidence
                      </button>
                    )}
                  </div>
                  <details>
                    <summary>Technical details</summary>
                    <dl>
                      <dt>Code</dt>
                      <dd>{inspection.diagnostic.code}</dd>
                      <dt>Tool</dt>
                      <dd>
                        {inspection.diagnostic.qualified_tool_name ||
                          "Unavailable"}
                      </dd>
                      <dt>Trace</dt>
                      <dd>{inspection.diagnostic.trace_id || "Unavailable"}</dd>
                    </dl>
                  </details>
                </div>
              ) : (
                <p className="rivet-run-empty">
                  No failure diagnosis is available for this run.
                </p>
              )
            ) : (
              <ul
                className="rivet-run-history"
                aria-label="Recent workflow runs"
              >
                {recentRuns.map((run) => (
                  <li key={run.run_id}>
                    <button
                      type="button"
                      aria-current={
                        run.run_id === inspection.run.run_id
                          ? "true"
                          : undefined
                      }
                      onClick={() => onSelectRun(run.run_id)}
                    >
                      <RunStateBadge state={run.state} />
                      <span>
                        Revision {run.revision}
                        {currentRevision != null &&
                        run.revision !== currentRevision
                          ? " · historical"
                          : ""}
                      </span>
                      <span>
                        {run.duration_ms == null
                          ? "—"
                          : formatDuration(run.duration_ms)}
                      </span>
                    </button>
                  </li>
                ))}
                {!recentRuns.length && (
                  <li className="rivet-run-empty">No recent runs.</li>
                )}
              </ul>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
