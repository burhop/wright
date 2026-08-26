export type HeadlessBlockName = "request" | "ai" | "mcp" | "evaluation";
export type HeadlessStepStatus = "running" | "completed" | "failed";

export interface HeadlessAdapterResult<T> {
  output: T;
  evidence?: unknown;
}

export interface HeadlessStepRecord {
  block: HeadlessBlockName;
  startedAt: string;
  finishedAt: string | null;
  status: HeadlessStepStatus;
  output: unknown;
  evidence: unknown;
  error: string | null;
}

export interface HeadlessFourBlockRun<TOutcome> {
  schemaVersion: "wright-headless-four-block-run/0.1";
  startedAt: string;
  finishedAt: string | null;
  status: "running" | "passed" | "failed";
  steps: HeadlessStepRecord[];
  outcome?: TOutcome;
}

export interface HeadlessFourBlockOptions<
  TRequest,
  TValidated,
  TGenerated,
  TToolResult,
  TOutcome extends { accepted: boolean },
> {
  request: TRequest;
  validateInput(request: TRequest): Promise<HeadlessAdapterResult<TValidated>>;
  generate(value: TValidated): Promise<HeadlessAdapterResult<TGenerated>>;
  invoke(value: TGenerated): Promise<HeadlessAdapterResult<TToolResult>>;
  evaluate(
    toolResult: TToolResult,
    generated: TGenerated,
  ): Promise<HeadlessAdapterResult<TOutcome>>;
  clock?: () => number;
  onStep?: (step: HeadlessStepRecord) => void;
}

export function runHeadlessFourBlockChain<
  TRequest,
  TValidated,
  TGenerated,
  TToolResult,
  TOutcome extends { accepted: boolean },
>(
  options: HeadlessFourBlockOptions<
    TRequest,
    TValidated,
    TGenerated,
    TToolResult,
    TOutcome
  >,
): Promise<HeadlessFourBlockRun<TOutcome>>;
