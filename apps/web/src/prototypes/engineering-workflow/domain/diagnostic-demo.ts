import type { WorkflowBlockRunState } from "../workflow-preview-model";
import type { DiagnosticMcpBindingDefault } from "./diagnostic-mcp-binding";

export type DiagnosticDemoStatus =
  "ready" | "running" | "blocked" | "failed" | "revised" | "passed";

export interface DiagnosticEvidence {
  nodeId: string;
  observation: string;
}

export interface DiagnosticFinding {
  code: string;
  severity: "low" | "medium" | "high";
  evaluationBlockId: string;
  title: string;
  criterion: string;
  expected: string;
  actual: string;
  evidence: readonly DiagnosticEvidence[];
}

export interface DiagnosticCorrection {
  correctionId: string;
  targetBlockId: string;
  label: string;
  description: string;
}

export interface DiagnosticPromptRequestRequirements {
  promptRequired: boolean;
  minImages: number;
  minDocuments: number;
}

export interface DiagnosticPromptRequestDefinition {
  blockId: string;
  initialPrompt: string;
  requirements: DiagnosticPromptRequestRequirements;
}

export interface DiagnosticPromptRequestSnapshot {
  prompt: string;
  imageCount: number;
  documentCount: number;
}

export interface DiagnosticInputIssue {
  code: "PROMPT_REQUIRED" | "IMAGES_REQUIRED" | "DOCUMENTS_REQUIRED";
  field: "prompt" | "images" | "documents";
  message: string;
}

export interface DiagnosticScenario {
  scenarioId: string;
  request: DiagnosticPromptRequestDefinition;
  executorBlockId: string;
  mcpBlockId: string;
  mcpBindingDefault?: DiagnosticMcpBindingDefault;
  evaluationBlockId: string;
  blockIds: readonly string[];
  finding: DiagnosticFinding;
  corrections: readonly DiagnosticCorrection[];
}

export interface DiagnosticRunRecord {
  runId: string;
  definitionStatus: "valid";
  executionStatus: "completed";
  outcomeStatus: "failed" | "passed";
  summary: string;
  correctionId: string | null;
}

export interface DiagnosticDemoState {
  status: DiagnosticDemoStatus;
  selectedCorrectionId: string | null;
  blockedAtBlockId: string | null;
  inputIssues: readonly DiagnosticInputIssue[];
  llmResult: DiagnosticLlmRunResult | null;
  executionError: string | null;
  runs: readonly DiagnosticRunRecord[];
}

export interface DiagnosticLlmRunResult {
  text: string;
  provider: string;
  model: string;
  thinkingLevel:
    "default" | "none" | "minimal" | "low" | "medium" | "high" | "xhigh";
}

export type DiagnosticDemoAction =
  | { type: "run"; request: DiagnosticPromptRequestSnapshot }
  | { type: "llm-succeeded"; result: DiagnosticLlmRunResult }
  | { type: "llm-failed"; message: string }
  | { type: "execution-succeeded"; summary: string }
  | { type: "execution-failed"; blockId: string; message: string }
  | { type: "apply-correction"; correctionId: string }
  | { type: "reset" };

export interface DiagnosticBlockOverlay {
  runState?: WorkflowBlockRunState;
  status: string;
}

export function createDiagnosticDemoState(): DiagnosticDemoState {
  return {
    status: "ready",
    selectedCorrectionId: null,
    blockedAtBlockId: null,
    inputIssues: [],
    llmResult: null,
    executionError: null,
    runs: [],
  };
}

export function diagnosticRequestIssues(
  request: DiagnosticPromptRequestSnapshot,
  requirements: DiagnosticPromptRequestRequirements,
): DiagnosticInputIssue[] {
  const issues: DiagnosticInputIssue[] = [];

  if (requirements.promptRequired && request.prompt.trim().length === 0) {
    issues.push({
      code: "PROMPT_REQUIRED",
      field: "prompt",
      message: "Enter a prompt describing what this workflow should do.",
    });
  }

  if (request.imageCount < requirements.minImages) {
    issues.push({
      code: "IMAGES_REQUIRED",
      field: "images",
      message: `At least ${requirements.minImages} image is required; ${request.imageCount} provided.`,
    });
  }

  if (request.documentCount < requirements.minDocuments) {
    issues.push({
      code: "DOCUMENTS_REQUIRED",
      field: "documents",
      message: `At least ${requirements.minDocuments} document is required; ${request.documentCount} provided.`,
    });
  }

  return issues;
}

export function reduceDiagnosticDemoState(
  state: DiagnosticDemoState,
  action: DiagnosticDemoAction,
  scenario: DiagnosticScenario,
): DiagnosticDemoState {
  if (action.type === "reset") return createDiagnosticDemoState();

  if (action.type === "llm-succeeded") {
    if (state.status !== "running") return state;
    return {
      ...state,
      status: "blocked",
      blockedAtBlockId: scenario.mcpBlockId,
      llmResult: action.result,
      executionError: null,
    };
  }

  if (action.type === "llm-failed") {
    if (state.status !== "running") return state;
    return {
      ...state,
      status: "blocked",
      blockedAtBlockId: scenario.executorBlockId,
      llmResult: null,
      executionError: action.message,
    };
  }

  if (action.type === "execution-succeeded") {
    if (state.status !== "running") return state;
    const runNumber = state.runs.length + 1;
    return {
      ...state,
      status: "passed",
      blockedAtBlockId: null,
      inputIssues: [],
      executionError: null,
      runs: [
        ...state.runs,
        {
          runId: `run-${runNumber}`,
          definitionStatus: "valid",
          executionStatus: "completed",
          outcomeStatus: "passed",
          summary: action.summary,
          correctionId: state.selectedCorrectionId,
        },
      ],
    };
  }

  if (action.type === "execution-failed") {
    if (state.status !== "running") return state;
    return {
      ...state,
      status: "blocked",
      blockedAtBlockId: action.blockId,
      executionError: action.message,
    };
  }

  if (action.type === "apply-correction") {
    const correctionExists = scenario.corrections.some(
      ({ correctionId }) => correctionId === action.correctionId,
    );
    if (!correctionExists || state.status !== "failed") return state;
    return {
      ...state,
      status: "revised",
      selectedCorrectionId: action.correctionId,
    };
  }

  const inputIssues = diagnosticRequestIssues(
    action.request,
    scenario.request.requirements,
  );
  if (inputIssues.length > 0) {
    return {
      ...state,
      status: "blocked",
      blockedAtBlockId: scenario.request.blockId,
      inputIssues,
      llmResult: null,
      executionError: null,
    };
  }

  if (state.status === "ready" || state.status === "blocked") {
    return {
      ...state,
      status: "running",
      blockedAtBlockId: scenario.executorBlockId,
      inputIssues: [],
      llmResult: null,
      executionError: null,
    };
  }

  if (state.status === "revised") {
    const runNumber = state.runs.length + 1;
    return {
      ...state,
      status: "passed",
      inputIssues: [],
      runs: [
        ...state.runs,
        {
          runId: `run-${runNumber}`,
          definitionStatus: "valid",
          executionStatus: "completed",
          outcomeStatus: "passed",
          summary:
            "The corrected input produced sufficient evidence and the evaluation passed.",
          correctionId: state.selectedCorrectionId,
        },
      ],
    };
  }

  return state;
}

export function diagnosticBlockOverlay(
  state: DiagnosticDemoState,
  scenario: DiagnosticScenario,
  blockId: string,
): DiagnosticBlockOverlay {
  if (state.status === "ready") {
    return { runState: "idle", status: "Not run" };
  }

  if (state.status === "running") {
    const executorIndex = scenario.blockIds.indexOf(scenario.executorBlockId);
    const blockIndex = scenario.blockIds.indexOf(blockId);
    if (blockIndex < executorIndex) {
      return { runState: "completed", status: "Completed" };
    }
    if (blockId === scenario.executorBlockId) {
      return { runState: "running", status: "Running selected AI" };
    }
    return { runState: "idle", status: "Waiting upstream" };
  }

  if (state.status === "blocked") {
    const blockedIndex = scenario.blockIds.indexOf(
      state.blockedAtBlockId ?? scenario.request.blockId,
    );
    const blockIndex = scenario.blockIds.indexOf(blockId);
    if (blockIndex < blockedIndex) {
      return { runState: "completed", status: "Completed" };
    }
    if (blockIndex === blockedIndex) {
      if (state.blockedAtBlockId === scenario.request.blockId) {
        return { runState: "warning", status: "Missing required input" };
      }
      if (state.blockedAtBlockId === scenario.executorBlockId) {
        return state.executionError
          ? { runState: "failed", status: "AI execution failed" }
          : { runState: "warning", status: "AI configuration required" };
      }
      return state.blockedAtBlockId === scenario.mcpBlockId
        ? { runState: "warning", status: "Select exact MCP tool" }
        : { runState: "warning", status: "Execution blocked" };
    }
    return { runState: "idle", status: "Blocked upstream" };
  }

  if (state.status === "failed") {
    if (blockId === scenario.evaluationBlockId) {
      return { runState: "failed", status: "Outcome failed" };
    }
    return { runState: "completed", status: "Completed" };
  }

  if (state.status === "revised") {
    const correction = scenario.corrections.find(
      ({ correctionId }) => correctionId === state.selectedCorrectionId,
    );
    if (correction?.targetBlockId === blockId) {
      return { runState: "revised", status: "Revised for rerun" };
    }
    if (blockId === scenario.evaluationBlockId) {
      return { runState: "warning", status: "Rerun required" };
    }
    return { runState: "completed", status: "Previous run" };
  }

  if (blockId === scenario.evaluationBlockId) {
    return { runState: "passed", status: "Outcome passed" };
  }
  return { runState: "completed", status: "Completed" };
}

export function diagnosticStatusMessage(
  state: DiagnosticDemoState,
  scenario: DiagnosticScenario,
): string {
  if (state.status === "ready") {
    return "Definition valid · Run to validate the request and advance to the first executable block.";
  }
  if (state.status === "running") {
    return "Prompt / Request completed · Selected AI is running · MCP and evaluation are waiting.";
  }
  if (state.status === "blocked") {
    if (state.blockedAtBlockId === scenario.request.blockId) {
      return "Preflight stopped at Prompt / Request · An explicit required input is missing · Nothing downstream ran.";
    }
    if (state.blockedAtBlockId === scenario.executorBlockId) {
      return state.executionError
        ? `Stopped at Interpret Request · ${state.executionError}`
        : "Stopped at Interpret Request · Select a configured model before running.";
    }
    if (state.executionError && state.blockedAtBlockId) {
      return `Workflow stopped at ${state.blockedAtBlockId} · ${state.executionError}`;
    }
    return "AI output ready · Stopped before MCP · Select an exact tool and schema mapping to continue.";
  }
  if (state.status === "failed") {
    return "Run 1 complete · Definition valid · Execution completed · OUTCOME FAILED · Diagnosis opened automatically.";
  }
  if (state.status === "revised") {
    return "Correction staged · Run again to compare the result.";
  }
  return state.runs.length > 1
    ? "Rerun passed · Earlier run records remain available for comparison."
    : "All four blocks completed · Select any block and open Run result to inspect its output and evidence.";
}

export function diagnosticReportForLlm(
  state: DiagnosticDemoState,
  scenario: DiagnosticScenario,
) {
  const latestRun = state.runs.at(-1) ?? null;
  return {
    schemaVersion: "0.1-diagnostic-report",
    scenarioId: scenario.scenarioId,
    definitionStatus: latestRun?.definitionStatus ?? "valid",
    executionStatus:
      state.status === "blocked" || state.status === "running"
        ? "blocked"
        : (latestRun?.executionStatus ?? "not-run"),
    outcomeStatus: latestRun?.outcomeStatus ?? "not-evaluated",
    blockedAtBlockId: state.blockedAtBlockId,
    llmResult: state.llmResult,
    executionError: state.executionError,
    finding:
      (state.status === "blocked" &&
        state.blockedAtBlockId === scenario.mcpBlockId) ||
      latestRun?.outcomeStatus === "failed"
        ? scenario.finding
        : null,
    selectedCorrectionId: state.selectedCorrectionId,
    inputIssues: state.inputIssues,
  } as const;
}
