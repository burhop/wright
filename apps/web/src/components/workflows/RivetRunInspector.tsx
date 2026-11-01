import { useEffect, useState } from "react";

import type {
  RivetRunInspection,
  RivetRunStep,
  RivetRunSummary,
} from "../../services/workspace-service";
import { RunStateBadge } from "../common/RunStateBadge";
import { WorkflowTracePage } from "../workflow-trace/WorkflowTracePage";
import "./rivet-run-inspector.css";

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
  onExportTrace?: (mode: "report_only" | "full_data") => void;
  onOpenArtifact?: (artifact: Record<string, unknown>) => void;
}

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
  onExportTrace,
  onOpenArtifact,
}: RivetRunInspectorProps) {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    if (inspection) setOpen(true);
  }, [inspection?.run.run_id, inspection]);
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
        aria-label="Run Inspector product review"
      >
        <strong>Trace</strong>
        <span>Product review</span>
        {inspection ? (
          <RunStateBadge state={inspection.run.state} />
        ) : (
          <span>No run selected</span>
        )}
        {inspection?.final_outputs.length ? (
          <span>{inspection.final_outputs.length} results</span>
        ) : null}
        <span aria-hidden="true">{open ? "v" : "^"}</span>
      </button>
      {open && (
        <div className="rivet-run-inspector__body">
          <WorkflowTracePage
            inspection={inspection}
            recentRuns={recentRuns}
            currentRevision={currentRevision}
            elapsedMs={elapsedMs}
            error={error}
            onSelectRun={onSelectRun}
            onFocusStep={onFocusStep}
            onRerun={onRerun}
            onExportEvidence={onExportEvidence}
            onExportTrace={onExportTrace}
            onOpenArtifact={onOpenArtifact}
          />
        </div>
      )}
    </section>
  );
}
