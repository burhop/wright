import { useMemo, useState } from "react";

import type {
  RivetRunInspection,
  RivetRunStep,
  RivetRunSummary,
} from "../../services/workspace-service";
import { RunStateBadge } from "../common/RunStateBadge";
import { RivetRunResult } from "../workflows/RivetRunResult";
import { TraceExportMenu } from "./TraceExportMenu";
import { TraceGraph, type TraceGraphSelection } from "./TraceGraph";
import { TraceInspector } from "./TraceInspector";
import { TraceProcessDetails } from "./TraceProcessDetails";
import "./workflow-trace.css";

type TraceTab = "results" | "process" | "evidence" | "history";

const formatDuration = (milliseconds: number) => {
  if (milliseconds < 1000) return `${milliseconds} ms`;
  const seconds = Math.floor(milliseconds / 1000);
  const minutes = Math.floor(seconds / 60);
  return minutes ? `${minutes}m ${seconds % 60}s` : `${seconds}s`;
};

export function WorkflowTracePage({
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
}: {
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
}) {
  const [tab, setTab] = useState<TraceTab>("results");
  const [selection, setSelection] = useState<TraceGraphSelection | null>(null);
  const [selectedStep, setSelectedStep] = useState<RivetRunStep | null>(null);
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(
    null,
  );
  const artifactResults = useMemo(
    () =>
      inspection?.final_outputs.filter(
        (result) => result.kind === "artifact",
      ) || [],
    [inspection],
  );
  const valueResults = useMemo(
    () =>
      inspection?.final_outputs.filter(
        (result) => result.kind !== "artifact",
      ) || [],
    [inspection],
  );
  if (!inspection) {
    return (
      <div className="workflow-trace workflow-trace--empty">
        {error ? (
          <p role="alert">{error}</p>
        ) : (
          <p>Select a saved run to review its results.</p>
        )}
      </div>
    );
  }
  const run = inspection.run;
  const evidenceForResult = (resultId: string, artifactId?: unknown) =>
    (inspection.evidence_records || []).filter((record) =>
      record.subjects.some(
        (subject) =>
          subject.subject_id === resultId ||
          (typeof artifactId === "string" && subject.subject_id === artifactId),
      ),
    );
  const resultForSubject = (subjectId: string) =>
    inspection.final_outputs.find(
      (result) =>
        result.result_id === subjectId ||
        (typeof result.artifact?.artifact_id === "string" &&
          result.artifact.artifact_id === subjectId),
    );
  const selectStep = (step: RivetRunStep) => {
    setSelectedStep(step);
    setSelection(step.node_id ? { kind: "node", id: step.node_id } : null);
    onFocusStep?.(step);
  };
  return (
    <article className="workflow-trace" data-testid="workflow-trace-page">
      <header className="workflow-trace__heading">
        <div>
          <span>Workflow review</span>
          <h2>{inspection.graph?.name || run.graph || run.workflow_id}</h2>
          <p>
            Recorded revision {run.revision} |{" "}
            {formatDuration(elapsedMs || run.duration_ms || 0)}
          </p>
        </div>
        <div className="workflow-trace__heading-actions">
          <RunStateBadge state={run.state} />
          <TraceExportMenu
            onExportEvidence={onExportEvidence}
            onExportTrace={onExportTrace}
          />
        </div>
      </header>
      {error && (
        <p className="workflow-trace__error" role="alert">
          {error}
        </p>
      )}
      {inspection.diagnostic && (
        <section
          className="workflow-trace__diagnostic"
          aria-label="Run error or blocker"
        >
          <strong>{inspection.diagnostic.summary}</strong>
          <p>
            Failed box:{" "}
            {inspection.diagnostic.failed_node_label || "Unavailable"}
          </p>
          <p>{inspection.diagnostic.recovery_action}</p>
          {inspection.diagnostic.residue_possible && (
            <p>
              The target application may contain a partial change. Inspect it
              before rerunning.
            </p>
          )}
          <details>
            <summary>Technical details</summary>
            <dl>
              <dt>Code</dt>
              <dd>{inspection.diagnostic.code}</dd>
              <dt>Failed box</dt>
              <dd>
                {inspection.diagnostic.failed_node_label || "Unavailable"}
              </dd>
              <dt>Trace</dt>
              <dd>{inspection.diagnostic.trace_id || "Unavailable"}</dd>
            </dl>
          </details>
          {inspection.diagnostic.full_rerun_available && onRerun && (
            <button type="button" onClick={onRerun}>
              Run saved revision again
            </button>
          )}
        </section>
      )}
      <nav
        className="workflow-trace__tabs"
        aria-label="Workflow review sections"
      >
        {(["results", "process", "evidence", "history"] as TraceTab[]).map(
          (value) => (
            <button
              key={value}
              type="button"
              aria-current={tab === value ? "page" : undefined}
              onClick={() => setTab(value)}
            >
              {value === "history"
                ? "Run history"
                : value[0].toUpperCase() + value.slice(1)}
            </button>
          ),
        )}
      </nav>
      <div className="workflow-trace__content">
        {tab === "results" && (
          <section aria-label="Run results">
            {!inspection.completeness.outputs_complete && (
              <p className="workflow-trace__warning">
                Some recorded output content is incomplete or unavailable.
              </p>
            )}
            {artifactResults.length > 0 && <h3>Created artifacts</h3>}
            <div className="workflow-trace__results">
              {artifactResults.map((result) => (
                <div
                  key={result.result_id}
                  id={`trace-result-${result.result_id}`}
                >
                  <RivetRunResult
                    result={result}
                    onOpenArtifact={onOpenArtifact}
                  />
                  {evidenceForResult(
                    result.result_id,
                    result.artifact?.artifact_id,
                  ).length > 0 && (
                    <button
                      type="button"
                      className="workflow-trace__evidence-link"
                      onClick={() => {
                        const evidence = evidenceForResult(
                          result.result_id,
                          result.artifact?.artifact_id,
                        );
                        setSelectedEvidenceId(evidence[0].evidence_id);
                        setTab("evidence");
                      }}
                    >
                      View recorded evidence (
                      {
                        evidenceForResult(
                          result.result_id,
                          result.artifact?.artifact_id,
                        ).length
                      }
                      )
                    </button>
                  )}
                </div>
              ))}
            </div>
            {valueResults.length > 0 && <h3>Result values</h3>}
            <div className="workflow-trace__results">
              {valueResults.map((result) => (
                <RivetRunResult key={result.result_id} result={result} />
              ))}
            </div>
            {!inspection.final_outputs.length && (
              <p className="workflow-trace__empty">
                {run.state === "succeeded"
                  ? "This run succeeded with no final outputs."
                  : "No final outputs were retained. Partial work may still be available in Process."}
              </p>
            )}
          </section>
        )}
        {tab === "process" && (
          <section
            className="workflow-trace__process"
            aria-label="Executed process"
          >
            <TraceGraph
              inspection={inspection}
              onSelect={(next) => {
                setSelection(next);
                setSelectedStep(null);
              }}
            />
            <TraceProcessDetails
              inspection={inspection}
              onSelectStep={selectStep}
            />
          </section>
        )}
        {tab === "evidence" && (
          <section
            className="workflow-trace__evidence"
            aria-label="Recorded inputs and evidence"
          >
            <details open>
              <summary>Run inputs ({inspection.run_inputs.length})</summary>
              <div className="workflow-trace__results">
                {inspection.run_inputs.map((result) => (
                  <RivetRunResult key={result.result_id} result={result} />
                ))}
                {!inspection.run_inputs.length && (
                  <p className="workflow-trace__empty">
                    Inputs were {inspection.inputs_state.replaceAll("-", " ")}.
                  </p>
                )}
              </div>
            </details>
            <details>
              <summary>Capture completeness</summary>
              {inspection.completeness.reasons.length ? (
                <ul>
                  {inspection.completeness.reasons.map((reason) => (
                    <li key={reason}>{reason.replaceAll("_", " ")}</li>
                  ))}
                </ul>
              ) : (
                <p>No retained capture gaps were reported.</p>
              )}
            </details>
            {(inspection.evidence_records || []).length > 0 && (
              <section aria-label="Producer-supplied evidence">
                <h3>Producer-supplied evidence</h3>
                {(inspection.evidence_records || []).map((record) => (
                  <details
                    key={record.evidence_id}
                    open={
                      selectedEvidenceId === record.evidence_id || undefined
                    }
                  >
                    <summary>
                      {record.kind}: {record.recorded_outcome || "recorded"}
                    </summary>
                    <p>{record.statement}</p>
                    <dl>
                      <dt>Producer</dt>
                      <dd>
                        {record.producer} {record.producer_version}
                      </dd>
                      <dt>Exact subjects</dt>
                      <dd>
                        {record.subjects
                          .map(
                            (subject) =>
                              `${subject.subject_kind}:${subject.subject_id}${subject.revision ? `@${subject.revision}` : ""}`,
                          )
                          .join(", ")}
                      </dd>
                    </dl>
                    {record.subjects.map((subject) => {
                      const result = resultForSubject(subject.subject_id);
                      return result ? (
                        <button
                          type="button"
                          className="workflow-trace__evidence-link"
                          key={`${record.evidence_id}:${subject.subject_id}`}
                          onClick={() => {
                            setTab("results");
                            window.setTimeout(() => {
                              const target = document.getElementById(
                                `trace-result-${result.result_id}`,
                              );
                              if (typeof target?.scrollIntoView === "function")
                                target.scrollIntoView({ block: "nearest" });
                            }, 0);
                          }}
                        >
                          View subject {result.name}
                        </button>
                      ) : null;
                    })}
                    {record.supersedes_id && (
                      <p>Corrects evidence {record.supersedes_id}.</p>
                    )}
                  </details>
                ))}
              </section>
            )}
            <p className="workflow-trace__empty">
              Validation shown here is producer-supplied evidence. This review
              does not run validators or create an acceptance verdict.
            </p>
          </section>
        )}
        {tab === "history" && (
          <ul
            className="workflow-trace__history"
            aria-label="Recent workflow runs"
          >
            {recentRuns.map((item) => (
              <li key={item.run_id}>
                <button
                  type="button"
                  aria-current={item.run_id === run.run_id ? "true" : undefined}
                  onClick={() => onSelectRun(item.run_id)}
                >
                  <RunStateBadge state={item.state} />
                  <span>
                    Revision {item.revision}
                    {currentRevision != null &&
                    item.revision !== currentRevision
                      ? " | historical"
                      : ""}
                  </span>
                  <span>
                    {item.duration_ms == null
                      ? ""
                      : formatDuration(item.duration_ms)}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
      {tab === "process" && (
        <TraceInspector
          inspection={inspection}
          selection={selection}
          selectedStep={selectedStep}
          onSelectStep={selectStep}
          onClose={() => {
            setSelection(null);
            setSelectedStep(null);
          }}
          onOpenArtifact={onOpenArtifact}
        />
      )}
    </article>
  );
}
