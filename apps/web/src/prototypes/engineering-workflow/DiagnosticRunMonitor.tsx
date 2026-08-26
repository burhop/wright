import type {
  DiagnosticDemoState,
  DiagnosticScenario,
} from "./domain/diagnostic-demo";
import type { DiagnosticLlmProgress } from "./services/diagnostic-llm-adapter";
import type { DiagnosticFourBlockRun } from "./services/diagnostic-four-block-executor";
import type { HeadlessStepRecord } from "./evaluation/headless-four-block-runner.mjs";
import type { WorkflowPreview } from "./workflow-preview-model";
import { DiagnosticWorkflowOutputs } from "./DiagnosticWorkflowOutputs";
import {
  workflowOutputsFrom,
  type WorkflowOutputAction,
  type WorkflowOutputReference,
} from "./domain/workflow-output";

function formatElapsed(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
}

export function DiagnosticRunMonitor({
  scenario,
  state,
  workflow,
  progress,
  startedAt,
  observedAt,
  steps,
  completedRun,
  onSelectBlock,
  onOutputAction,
}: {
  scenario: DiagnosticScenario;
  state: DiagnosticDemoState;
  workflow: WorkflowPreview;
  progress: DiagnosticLlmProgress | null;
  startedAt: number | null;
  observedAt: number;
  steps: readonly HeadlessStepRecord[];
  completedRun: DiagnosticFourBlockRun | null;
  onSelectBlock: (blockId: string) => void;
  onOutputAction: (
    output: WorkflowOutputReference,
    action: WorkflowOutputAction,
  ) => Promise<string | void>;
}) {
  const visible =
    steps.length > 0 ||
    state.status === "running" ||
    state.llmResult !== null ||
    (state.blockedAtBlockId === scenario.executorBlockId &&
      state.executionError !== null);
  if (!visible) return null;

  const activeStep =
    steps.find(({ status }) => status === "running") ??
    steps.find(({ status }) => status === "failed") ??
    steps.at(-1) ??
    null;
  const activeBlockId = activeStep
    ? activeStep.block === "request"
      ? scenario.request.blockId
      : activeStep.block === "ai"
        ? scenario.executorBlockId
        : activeStep.block === "mcp"
          ? scenario.mcpBlockId
          : scenario.evaluationBlockId
    : state.status === "running"
      ? scenario.executorBlockId
      : (state.blockedAtBlockId ?? scenario.executorBlockId);
  const activeBlock = workflow.blocks.find(
    ({ blockId }) => blockId === activeBlockId,
  );
  if (!activeBlock) return null;

  const elapsedSeconds = startedAt
    ? Math.max(0, Math.floor((observedAt - startedAt) / 1000))
    : 0;
  const recordedOutput = activeStep?.output;
  const outputText =
    activeStep?.block === "ai" && activeStep.status === "running"
      ? (progress?.partialText ?? "")
      : recordedOutput === null || recordedOutput === undefined
        ? state.status === "running"
          ? (progress?.partialText ?? "")
          : (state.llmResult?.text ?? progress?.partialText ?? "")
        : typeof recordedOutput === "string"
          ? recordedOutput
          : JSON.stringify(recordedOutput, null, 2);
  const outputLabel = activeStep
    ? activeStep.status === "running"
      ? "Current block output"
      : "Recorded block output"
    : state.executionError
      ? "Partial output before failure"
      : state.status === "running"
        ? "Uncommitted output preview"
        : "Committed AI output";
  const completedOutputs = workflowOutputsFrom(completedRun?.outcome);

  return (
    <section
      className="ewp-run-monitor"
      data-state={completedRun?.status ?? state.status}
      aria-label="Workflow execution monitor"
    >
      <header>
        <span className="ewp-run-monitor__state">
          <i aria-hidden="true" />
          {completedRun?.status === "passed"
            ? "Passed"
            : state.status === "running"
              ? "Running"
              : "Stopped"}
        </span>
        <span>
          {activeStep?.status === "running" || state.status === "running"
            ? "Executing"
            : "Active frontier"}{" "}
          block {activeBlock.sequence} of {scenario.blockIds.length}
        </span>
        <time>{formatElapsed(elapsedSeconds)} elapsed</time>
      </header>

      <div className="ewp-run-monitor__current" role="status">
        <span>
          <strong>
            {activeBlock.sequence}. {activeBlock.title}
          </strong>
          <small>
            {activeStep?.status === "running"
              ? activeStep.block === "ai"
                ? (progress?.message ?? "Starting the selected AI task.")
                : activeStep.block === "request"
                  ? "Validating the workflow request."
                  : activeStep.block === "mcp"
                    ? "Calling the exact selected MCP tool."
                    : "Evaluating the MCP result against the declared criterion."
              : state.status === "running"
                ? (progress?.message ?? "Starting the selected AI task.")
                : state.executionError
                  ? state.executionError
                  : (activeBlock.status ??
                    "AI output is ready. This block is waiting for user action.")}
          </small>
        </span>
        <button type="button" onClick={() => onSelectBlock(activeBlockId)}>
          View block
        </button>
      </div>

      <ol className="ewp-run-monitor__steps" aria-label="Workflow step status">
        {scenario.blockIds.map((blockId) => {
          const block = workflow.blocks.find(
            (candidate) => candidate.blockId === blockId,
          );
          if (!block) return null;
          const stepName =
            blockId === scenario.request.blockId
              ? "request"
              : blockId === scenario.executorBlockId
                ? "ai"
                : blockId === scenario.mcpBlockId
                  ? "mcp"
                  : "evaluation";
          const step = steps.find(
            ({ block: candidate }) => candidate === stepName,
          );
          const runState = step?.status ?? block.runState ?? "idle";
          const status = step
            ? step.status === "failed"
              ? (step.error ?? "Failed")
              : step.status === "running"
                ? "Running"
                : "Completed · view result"
            : (block.status ?? "Not run");
          return (
            <li
              key={blockId}
              data-state={runState}
              data-current={blockId === activeBlockId ? "true" : undefined}
            >
              <button type="button" onClick={() => onSelectBlock(blockId)}>
                <strong>{block.sequence}</strong>
                <span>{block.title}</span>
                <small>{status}</small>
              </button>
            </li>
          );
        })}
      </ol>

      {completedOutputs.length ? (
        <DiagnosticWorkflowOutputs
          outputs={completedOutputs}
          onAction={onOutputAction}
        />
      ) : (
        <section className="ewp-run-monitor__output" aria-label={outputLabel}>
          <header>
            <strong>{outputLabel}</strong>
            <small>{outputText.length} characters received</small>
          </header>
          <pre aria-live="polite">
            {outputText || "Waiting for the first output token…"}
          </pre>
        </section>
      )}
    </section>
  );
}

export default DiagnosticRunMonitor;
