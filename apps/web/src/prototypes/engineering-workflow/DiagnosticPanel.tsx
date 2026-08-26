import {
  diagnosticReportForLlm,
  type DiagnosticDemoState,
  type DiagnosticScenario,
} from "./domain/diagnostic-demo";
import type { DiagnosticMcpBindingSummary } from "./DiagnosticMcpBindingPanel";

export function DiagnosticPanel({
  scenario,
  state,
  mcpBinding,
  onApplyCorrection,
}: {
  scenario: DiagnosticScenario;
  state: DiagnosticDemoState;
  mcpBinding: DiagnosticMcpBindingSummary | null;
  onApplyCorrection: (correctionId: string) => void;
}) {
  const latestRun = state.runs.at(-1) ?? null;
  const selectedCorrection = scenario.corrections.find(
    ({ correctionId }) => correctionId === state.selectedCorrectionId,
  );
  const baseLlmReport = diagnosticReportForLlm(state, scenario);
  const llmReport = {
    ...baseLlmReport,
    finding: mcpBinding ? null : baseLlmReport.finding,
    mcpBinding,
  };
  const requestBlocked = state.blockedAtBlockId === scenario.request.blockId;
  const executorBlocked = state.blockedAtBlockId === scenario.executorBlockId;
  const mcpBlocked = state.blockedAtBlockId === scenario.mcpBlockId;

  return (
    <div className="ewp-diagnostic">
      <p className="ewp-inspector__summary">
        This demo validates typed inputs, runs the selected AI with tools
        disabled, preserves its output, and then stops at the MCP binding and
        execution boundary.
      </p>
      <dl className="ewp-diagnostic__status-grid">
        <div data-state="passed">
          <dt>Definition</dt>
          <dd>Valid</dd>
        </div>
        <div
          data-state={
            state.status === "running"
              ? "warning"
              : state.status === "blocked"
                ? "warning"
                : latestRun
                  ? "passed"
                  : "idle"
          }
        >
          <dt>Execution</dt>
          <dd>
            {state.status === "running"
              ? "Running selected AI"
              : state.status === "blocked"
                ? requestBlocked
                  ? "Stopped at request"
                  : executorBlocked
                    ? "Stopped at AI"
                    : mcpBlocked
                      ? mcpBinding
                        ? mcpBinding.unmappedInputs.length > 0
                          ? "MCP bound; map inputs"
                          : "MCP bound; not executed"
                        : "Stopped before MCP"
                      : "Blocked"
                : latestRun
                  ? "Completed"
                  : "Not run"}
          </dd>
        </div>
        <div
          data-state={
            state.status === "failed"
              ? "failed"
              : state.status === "passed"
                ? "passed"
                : state.status === "blocked" || state.status === "revised"
                  ? "warning"
                  : "idle"
          }
        >
          <dt>Outcome</dt>
          <dd>
            {state.status === "ready"
              ? "Not evaluated"
              : state.status === "blocked" || state.status === "running"
                ? "Not reached"
                : state.status === "failed"
                  ? "Failed"
                  : state.status === "revised"
                    ? "Rerun required"
                    : "Passed"}
          </dd>
        </div>
      </dl>

      {state.status === "ready" ? (
        <section className="ewp-diagnostic__guide">
          <h2>Start the test</h2>
          <p>
            Select <strong>Run diagnostic demo</strong>. Preflight checks the
            Prompt / Request before any AI or MCP action can run.
          </p>
        </section>
      ) : null}

      {state.status === "running" ? (
        <section
          className="ewp-diagnostic__guide"
          data-state="warning"
          role="status"
        >
          <h2>Selected AI is running</h2>
          <p>
            Prompt / Request passed preflight. MCP execution and outcome
            evaluation remain blocked until this model request completes.
          </p>
        </section>
      ) : null}

      {state.status === "blocked" ? (
        requestBlocked ? (
          <section
            className="ewp-diagnostic__guide"
            data-state="warning"
            role="alert"
          >
            <h2>Stopped at Prompt / Request</h2>
            <p>
              No AI or MCP action ran. Supply the missing input and continue.
            </p>
            <ul>
              {state.inputIssues.map((issue) => (
                <li key={issue.code}>
                  <strong>{issue.field}</strong> · {issue.message}
                </li>
              ))}
            </ul>
          </section>
        ) : executorBlocked ? (
          <section className="ewp-diagnostic__finding" role="alert">
            <header>
              <span>execution stopped</span>
              <code>AI_EXECUTION_FAILED</code>
            </header>
            <h2>AI task did not produce output</h2>
            <dl>
              <div>
                <dt>Actual</dt>
                <dd>
                  {state.executionError ??
                    "Select a configured model and retry."}
                </dd>
              </div>
            </dl>
          </section>
        ) : state.executionError ? (
          <section className="ewp-diagnostic__finding" role="alert">
            <header>
              <span>execution stopped</span>
              <code>WORKFLOW_STEP_FAILED</code>
            </header>
            <h2>Workflow stopped before downstream blocks ran</h2>
            <dl>
              <div>
                <dt>Stopped at</dt>
                <dd>{state.blockedAtBlockId}</dd>
              </div>
              <div>
                <dt>Actual</dt>
                <dd>{state.executionError}</dd>
              </div>
            </dl>
            <p>
              Select the failed block and open <strong>Run result</strong> to
              inspect its preserved output, evidence, and error.
            </p>
          </section>
        ) : mcpBinding ? (
          <>
            <section
              className="ewp-diagnostic__guide"
              data-state="warning"
              role="status"
            >
              <h2>
                {mcpBinding.unmappedInputs.length > 0
                  ? "MCP tool selected; input mapping required"
                  : "MCP tool selected"}
              </h2>
              <p>
                <strong>{mcpBinding.serverName}</strong> · {mcpBinding.toolName}
              </p>
              <small>{mcpBinding.toolId}</small>
              {mcpBinding.unmappedInputs.length > 0 ? (
                <p>
                  This tool requires {mcpBinding.unmappedInputs.join(", ")}.
                  Step 2 produced text, not a schema-compatible object, so
                  Wright cannot validate the tool arguments. No MCP call or
                  outcome evaluation ran.
                </p>
              ) : (
                <p>
                  The exact binding is reviewable. No MCP call or outcome
                  evaluation ran because execution is intentionally disabled in
                  this increment.
                </p>
              )}
            </section>
            {state.llmResult ? (
              <section className="ewp-diagnostic__guide">
                <h2>AI output is preserved</h2>
                <p>
                  {state.llmResult.provider} · {state.llmResult.model} ·
                  thinking {state.llmResult.thinkingLevel}
                </p>
                <pre className="ewp-diagnostic__llm-output">
                  {state.llmResult.text}
                </pre>
              </section>
            ) : null}
            <section className="ewp-diagnostic__guide" data-state="warning">
              <h2>Next honest boundary</h2>
              <p>
                {mcpBinding.unmappedInputs.length > 0
                  ? `Configure Step 2 to produce ${mcpBinding.unmappedInputs.join(", ")} or insert an explicit mapping step. Then validate the arguments and require governed approval before a live call.`
                  : "Validate the arguments and require governed approval before enabling a live call."}
              </p>
            </section>
          </>
        ) : (
          <>
            <section className="ewp-diagnostic__finding" role="alert">
              <header>
                <span>{scenario.finding.severity} severity</span>
                <code>{scenario.finding.code}</code>
              </header>
              <h2>{scenario.finding.title}</h2>
              <dl>
                <div>
                  <dt>Expected</dt>
                  <dd>{scenario.finding.expected}</dd>
                </div>
                <div>
                  <dt>Actual</dt>
                  <dd>{scenario.finding.actual}</dd>
                </div>
              </dl>
            </section>
            {state.llmResult ? (
              <section className="ewp-diagnostic__guide">
                <h2>AI output is preserved</h2>
                <p>
                  {state.llmResult.provider} · {state.llmResult.model} ·
                  thinking {state.llmResult.thinkingLevel}
                </p>
                <pre className="ewp-diagnostic__llm-output">
                  {state.llmResult.text}
                </pre>
              </section>
            ) : null}
            <section className="ewp-diagnostic__guide" data-state="warning">
              <h2>Next honest boundary</h2>
              <p>
                No MCP call or outcome evaluation ran. Select an exact MCP
                catalog tool and validate its arguments against that tool's
                declared schema before continuing.
              </p>
            </section>
          </>
        )
      ) : null}
      {state.status === "failed" ? (
        <>
          <section className="ewp-diagnostic__finding" role="alert">
            <header>
              <span>{scenario.finding.severity} severity</span>
              <code>{scenario.finding.code}</code>
            </header>
            <h2>{scenario.finding.title}</h2>
            <dl>
              <div>
                <dt>Criterion</dt>
                <dd>{scenario.finding.criterion}</dd>
              </div>
              <div>
                <dt>Expected</dt>
                <dd>{scenario.finding.expected}</dd>
              </div>
              <div>
                <dt>Actual</dt>
                <dd>{scenario.finding.actual}</dd>
              </div>
            </dl>
          </section>
          <section className="ewp-diagnostic__trace">
            <h2>Trace upstream evidence</h2>
            <ol>
              {scenario.finding.evidence.map((evidence) => (
                <li key={evidence.nodeId}>
                  <strong>{evidence.nodeId}</strong>
                  <span>{evidence.observation}</span>
                </li>
              ))}
            </ol>
          </section>
          <section className="ewp-diagnostic__corrections">
            <h2>Try one correction</h2>
            <p>Each option changes a different upstream contributor.</p>
            {scenario.corrections.map((correction) => (
              <button
                key={correction.correctionId}
                type="button"
                onClick={() => onApplyCorrection(correction.correctionId)}
              >
                <strong>{correction.label}</strong>
                <span>{correction.description}</span>
              </button>
            ))}
          </section>
        </>
      ) : null}

      {state.status === "revised" && selectedCorrection ? (
        <section className="ewp-diagnostic__resolution" data-state="warning">
          <h2>Correction staged</h2>
          <strong>{selectedCorrection.label}</strong>
          <p>{selectedCorrection.description}</p>
          <small>
            Run the workflow again to create a comparable second run.
          </small>
        </section>
      ) : null}

      {state.status === "passed" ? (
        <section className="ewp-diagnostic__resolution" data-state="passed">
          <h2>Outcome passed</h2>
          <p>
            All four blocks completed. Select any block and open Run result to
            inspect the output and evidence preserved at that boundary.
          </p>
        </section>
      ) : null}

      {state.runs.length > 0 ? (
        <section className="ewp-diagnostic__runs">
          <h2>Run comparison</h2>
          <ol>
            {state.runs.map((run) => (
              <li key={run.runId} data-state={run.outcomeStatus}>
                <strong>{run.runId.replace("run-", "Run ")}</strong>
                <span>
                  Definition valid · Execution completed · Outcome{" "}
                  {run.outcomeStatus}
                </span>
                <small>{run.summary}</small>
              </li>
            ))}
          </ol>
        </section>
      ) : null}

      <details className="ewp-diagnostic__machine-report">
        <summary>Structured diagnostic for an LLM</summary>
        <pre>{JSON.stringify(llmReport, null, 2)}</pre>
      </details>
    </div>
  );
}

export default DiagnosticPanel;
