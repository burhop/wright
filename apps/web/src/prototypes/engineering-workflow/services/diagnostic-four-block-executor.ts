import type {
  HeadlessFourBlockRun,
  HeadlessStepRecord,
} from "../evaluation/headless-four-block-runner.mjs";
import { runHeadlessFourBlockChain } from "../evaluation/headless-four-block-runner.mjs";
import type {
  DiagnosticMcpServerOption,
  DiagnosticMcpToolOption,
} from "../domain/diagnostic-mcp-binding";
import type {
  DiagnosticLlmAdapter,
  DiagnosticLlmExecutionObserver,
  DiagnosticLlmRequest,
  DiagnosticLlmSettings,
} from "./diagnostic-llm-adapter";
import type {
  WorkflowOutputAction,
  WorkflowOutputReference,
} from "../domain/workflow-output";

export interface DiagnosticExactMcpBinding {
  server: DiagnosticMcpServerOption;
  tool: DiagnosticMcpToolOption;
}

export interface DiagnosticOutcome {
  accepted: boolean;
  meaning: string;
  outputs?: readonly WorkflowOutputReference[];
}

export type DiagnosticOutputActionResult =
  | {
      kind: "embedded";
      close(): void;
    }
  | {
      kind: "completed";
      message: string;
    };

export interface DiagnosticMcpRunSession {
  responseInstructions(
    request: DiagnosticLlmRequest,
    binding: DiagnosticExactMcpBinding,
  ): string;
  parseGeneratedOutput(
    text: string,
    binding: DiagnosticExactMcpBinding,
  ): unknown;
  invoke(
    argumentsValue: unknown,
    binding: DiagnosticExactMcpBinding,
  ): Promise<{ output: unknown; evidence?: unknown }>;
  evaluate(
    toolResult: unknown,
    generatedArguments: unknown,
    binding: DiagnosticExactMcpBinding,
  ): Promise<{ output: DiagnosticOutcome; evidence?: unknown }>;
  dispose(): Promise<void>;
}

/**
 * A selected MCP may need a host application or another bounded transport.
 * The generic runner knows none of those details; a prototype adapter owns
 * them for one run and must clean them up afterward.
 */
export interface DiagnosticMcpRuntimeAdapter {
  supports(binding: DiagnosticExactMcpBinding): boolean;
  createRun(binding: DiagnosticExactMcpBinding): DiagnosticMcpRunSession;
  performOutputAction?(
    output: WorkflowOutputReference,
    action: WorkflowOutputAction,
  ): Promise<DiagnosticOutputActionResult>;
  releaseOutputs?(outputs: readonly WorkflowOutputReference[]): Promise<void>;
}

export interface DiagnosticFourBlockExecutionOptions {
  request: DiagnosticLlmRequest;
  settings: DiagnosticLlmSettings;
  binding: DiagnosticExactMcpBinding;
  llmAdapter: DiagnosticLlmAdapter;
  mcpRuntimeAdapter: DiagnosticMcpRuntimeAdapter;
  onStep?(step: HeadlessStepRecord): void;
  llmObserver?: DiagnosticLlmExecutionObserver;
}

export type DiagnosticFourBlockRun = HeadlessFourBlockRun<DiagnosticOutcome>;

export async function executeDiagnosticFourBlockChain({
  request,
  settings,
  binding,
  llmAdapter,
  mcpRuntimeAdapter,
  onStep,
  llmObserver,
}: DiagnosticFourBlockExecutionOptions): Promise<DiagnosticFourBlockRun> {
  const runtime = mcpRuntimeAdapter.createRun(binding);
  try {
    return await runHeadlessFourBlockChain({
      request,
      onStep,
      async validateInput(value) {
        if (!value.prompt.trim()) throw new Error("A prompt is required.");
        return {
          output: value,
          evidence: {
            promptCharacters: value.prompt.length,
            imageCount: value.images.length,
            documentCount: value.documents.length,
          },
        };
      },
      async generate(validatedRequest) {
        const result = await llmAdapter.execute(
          {
            ...validatedRequest,
            responseInstructions: runtime.responseInstructions(
              validatedRequest,
              binding,
            ),
          },
          settings,
          llmObserver,
        );
        let generatedArguments: unknown;
        try {
          generatedArguments = runtime.parseGeneratedOutput(
            result.text,
            binding,
          );
        } catch (error) {
          throw Object.assign(
            error instanceof Error ? error : new Error(String(error)),
            {
              stepOutput: result.text,
              stepEvidence: {
                provider: result.provider,
                model: result.model,
                thinkingLevel: result.thinkingLevel,
                toolPolicy: "none",
              },
            },
          );
        }
        return {
          output: generatedArguments,
          evidence: {
            provider: result.provider,
            model: result.model,
            thinkingLevel: result.thinkingLevel,
            toolPolicy: "none",
            rawModelOutput: result.text,
          },
        };
      },
      invoke: (argumentsValue) => runtime.invoke(argumentsValue, binding),
      evaluate: (toolResult, generatedArguments) =>
        runtime.evaluate(toolResult, generatedArguments, binding),
    });
  } finally {
    await runtime.dispose();
  }
}
