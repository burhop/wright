import { useCallback, useEffect, useState } from "react";

import {
  workspaceService,
  type EngineeringScenarioReport,
} from "../../services/workspace-service";

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

  const refresh = useCallback(async () => {
    try {
      const next = await workspaceService.getEngineeringScenarioReport(
        sessionId,
        scenarioRunId,
      );
      setReport(next);
      setMessage(`Scenario is ${next.state}.`);
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
    const timer = window.setInterval(() => {
      if (!report || !TERMINAL.has(report.state)) void refresh();
    }, 1000);
    return () => window.clearInterval(timer);
  }, [refresh, report]);

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
                  {assertion.producer.node_id} / {assertion.producer.capability} /{" "}
                  {assertion.reason_code}
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
        </>
      ) : null}
    </section>
  );
}
