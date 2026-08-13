import { useCallback, useEffect, useRef, useState } from "react";

import {
  workspaceService,
  type EngineeringScenarioReport,
} from "../../services/workspace-service";
import { SupportDiagnosticsPanel } from "../support/SupportDiagnosticsPanel";

const TERMINAL = new Set(["passed", "failed", "cancelled", "blocked", "error"]);

function displayValue(value: unknown): string {
  if (value === null || value === undefined) return "Not recorded";
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

export function RivetScenarioReport({
  sessionId,
  scenarioRunId,
}: {
  sessionId: string;
  scenarioRunId: string;
}) {
  const [report, setReport] = useState<EngineeringScenarioReport | null>(null);
  const [message, setMessage] = useState("Loading engineering evidence...");
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const observedAt = useRef(Date.now());
  const terminalSummary = useRef<HTMLDivElement>(null);
  const terminalFocused = useRef(false);
  const reportState = report?.state;

  const refresh = useCallback(async () => {
    try {
      const next = await workspaceService.getEngineeringScenarioReport(
        sessionId,
        scenarioRunId,
      );
      setReport(next);
      setMessage(`Scenario is ${next.state}.`);
      setElapsedSeconds(
        Math.max(0, Math.floor((Date.now() - observedAt.current) / 1000)),
      );
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Scenario report is unavailable.",
      );
    }
  }, [scenarioRunId, sessionId]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  useEffect(() => {
    if (reportState && TERMINAL.has(reportState)) return;
    const timer = window.setInterval(() => {
      void refresh();
    }, 1000);
    return () => window.clearInterval(timer);
  }, [refresh, reportState]);

  useEffect(() => {
    if (report && TERMINAL.has(report.state) && !terminalFocused.current) {
      terminalFocused.current = true;
      terminalSummary.current?.focus();
    }
  }, [report]);

  const cancel = async () => {
    try {
      await workspaceService.cancelEngineeringScenario(
        sessionId,
        scenarioRunId,
      );
      await refresh();
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : "Scenario cancellation failed.",
      );
    }
  };

  return (
    <section
      aria-labelledby={`scenario-report-title-${scenarioRunId}`}
      data-testid={`scenario-report-${scenarioRunId}`}
      style={{
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-sm)",
        marginTop: "var(--space-sm)",
        padding: "var(--space-sm)",
      }}
    >
      <h4 id={`scenario-report-title-${scenarioRunId}`}>Engineering report</h4>
      <p role="status" aria-live="polite">
        {message}
      </p>
      <div
        ref={terminalSummary}
        tabIndex={report && TERMINAL.has(report.state) ? -1 : undefined}
        data-testid="scenario-phase-summary"
      >
        <p>
          <strong>Phase:</strong>{" "}
          {!report
            ? "loading durable report"
            : TERMINAL.has(report.state)
              ? "review evidence and recovery"
              : report.state === "cancelling"
                ? "cancelling and checking cleanup"
                : "running reviewed workflow"}
          . <strong>Progress:</strong>{" "}
          {report && TERMINAL.has(report.state)
            ? "terminal"
            : "in progress; no percentage is available"}
          . <strong>Observed:</strong> {elapsedSeconds} seconds.{" "}
          <strong>Cancellation:</strong>{" "}
          {!report || !TERMINAL.has(report.state)
            ? "available"
            : "not available after a terminal result"}
          .
        </p>
      </div>
      {!report || !TERMINAL.has(report.state) ? (
        <button
          data-testid={`scenario-cancel-${scenarioRunId}`}
          type="button"
          onClick={() => void cancel()}
        >
          Cancel scenario
        </button>
      ) : null}
      <button type="button" onClick={() => void refresh()}>
        Refresh report
      </button>{" "}
      <button
        type="button"
        disabled={!report || !TERMINAL.has(report.state)}
        onClick={() =>
          void workspaceService.exportEngineeringScenarioReport(
            sessionId,
            scenarioRunId,
          )
        }
      >
        Export evidence
      </button>
      {report ? (
        <>
          <p>
            <strong>Status:</strong> {report.state}. <strong>Cleanup:</strong>{" "}
            {report.cleanup_state}.
          </p>
          {report.cleanup_state === "residue" ? (
            <p role="alert">
              Cleanup residue was reported: {displayValue(report.residue)}
            </p>
          ) : null}
          <p>
            {report.artifacts.length} normalized artifacts and{" "}
            {report.assertions.length} engineering assertions.
          </p>
          {report.state === "passed" && report.advisory ? (
            <section
              aria-labelledby={`scenario-advisory-title-${scenarioRunId}`}
              data-testid="scenario-advisory"
            >
              <h5 id={`scenario-advisory-title-${scenarioRunId}`}>
                Human-review advisory
              </h5>
              <p>
                Selected discrete candidate for review:{" "}
                <strong>{report.advisory.selected_candidate_id}</strong>.
              </p>
              <p>
                Simulation only:{" "}
                {report.advisory.simulation_only ? "yes" : "no"}. Machine
                authority: {report.advisory.machine_authority ? "yes" : "no"}.
                Score semantics:{" "}
                {report.advisory.score_semantics.replaceAll("_", " ")}.
              </p>
              <p role="note">
                Scores are uncalibrated screening values, not probabilities or
                machining guarantees. A qualified engineer must review every
                invariant and limitation before taking any separate action.
              </p>
              <ul style={{ paddingLeft: "var(--space-lg)" }}>
                {report.advisory.candidate_outcomes.map((outcome) => (
                  <li key={outcome.candidate_id}>
                    <strong>
                      {outcome.candidate_id}:{" "}
                      {outcome.review_status.replaceAll("_", " ")}
                    </strong>{" "}
                    — {outcome.reason}
                    {typeof outcome.chatter_score === "number" ? (
                      <small>
                        {" "}
                        Uncalibrated score {outcome.chatter_score}.
                      </small>
                    ) : null}
                  </li>
                ))}
              </ul>
              <p>
                Provider evidence records:{" "}
                {report.advisory.provider_evidence.length}.
              </p>
              {report.advisory.notices.map((notice) => (
                <p key={notice}>{notice}</p>
              ))}
            </section>
          ) : null}
          <h5>Material engineering evidence</h5>
          <p>
            Artifact identities and content digests describe deterministic
            engineering material. Run timing and resource values remain
            observations and do not change these identities.
          </p>
          <ul style={{ paddingLeft: "var(--space-lg)" }}>
            {report.artifacts.slice(0, 100).map((artifact, index) => (
              <li
                key={artifact.artifact_id || `artifact-${index}`}
                data-testid={`scenario-artifact-${artifact.artifact_id || index}`}
              >
                <strong>{artifact.artifact_id || "Unnamed artifact"}</strong>
                {artifact.domain || artifact.kind ? (
                  <>
                    :{" "}
                    {[artifact.domain, artifact.kind]
                      .filter(Boolean)
                      .join(" / ")}
                  </>
                ) : null}
                <br />
                <small>
                  Validation {artifact.validation_state || "not recorded"};
                  digest {artifact.content_digest || "not recorded"}
                </small>
                {artifact.producer ? (
                  <>
                    <br />
                    <small>
                      Producer {artifact.producer.node_id || "unknown node"} ·{" "}
                      {artifact.producer.capability || "unknown capability"}
                    </small>
                  </>
                ) : null}
              </li>
            ))}
          </ul>
          {report.artifacts.length > 100 ? (
            <p>
              Showing the first 100 artifacts. Export evidence for the full
              index.
            </p>
          ) : null}
          <h5>Observed assertion results</h5>
          <p>
            Each result names the producing Rivet node and exact reviewed
            capability. Assertion values are observations, not reusable tool or
            machine authority.
          </p>
          <ol style={{ paddingLeft: "var(--space-lg)" }}>
            {report.assertions.slice(0, 100).map((assertion) => (
              <li
                key={assertion.assertion_id}
                data-testid={`scenario-assertion-${assertion.assertion_id}`}
                style={{ marginBottom: "var(--space-sm)" }}
              >
                <strong>
                  {assertion.assertion_id}: {assertion.state}
                </strong>
                <br />
                <small>
                  {assertion.producer.node_id} / {assertion.producer.capability}{" "}
                  / {assertion.reason_code}
                </small>
                <br />
                <small>
                  Expected {displayValue(assertion.expected)}; observed{" "}
                  {displayValue(assertion.observed)}
                </small>
                {assertion.artifact_digests?.length ? (
                  <>
                    <br />
                    <small>
                      Artifact digests {assertion.artifact_digests.join(", ")}
                    </small>
                  </>
                ) : null}
                {assertion.message ? <p>{assertion.message}</p> : null}
                {assertion.recovery ? (
                  <p>
                    <strong>Recovery:</strong> {assertion.recovery}
                  </p>
                ) : null}
              </li>
            ))}
          </ol>
          {report.assertions.length > 100 ? (
            <p>
              Showing the first 100 assertions. Export evidence for the full
              report.
            </p>
          ) : null}
          <SupportDiagnosticsPanel
            workspaceId={report.workspace_id}
            sessionId={sessionId}
            scenarioRunId={scenarioRunId}
          />
        </>
      ) : null}
    </section>
  );
}
