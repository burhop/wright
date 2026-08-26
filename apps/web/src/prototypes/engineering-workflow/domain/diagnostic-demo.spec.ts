import { describe, expect, it } from "vitest";

import { diagnosticScenario } from "../fixtures/diagnostic-workflow";
import {
  createDiagnosticDemoState,
  diagnosticBlockOverlay,
  diagnosticReportForLlm,
  reduceDiagnosticDemoState,
} from "./diagnostic-demo";

const validRequest = {
  prompt: diagnosticScenario.request.initialPrompt,
  imageCount: 0,
  documentCount: 0,
};

describe("diagnostic demo", () => {
  it("runs the selected AI, preserves its output, and stops at the generic MCP boundary", () => {
    const state = reduceDiagnosticDemoState(
      createDiagnosticDemoState(),
      { type: "run", request: validRequest },
      diagnosticScenario,
    );

    expect(state.status).toBe("running");
    expect(state.blockedAtBlockId).toBe(diagnosticScenario.executorBlockId);
    expect(state.inputIssues).toEqual([]);
    expect(state.runs).toEqual([]);
    expect(
      diagnosticBlockOverlay(
        state,
        diagnosticScenario,
        diagnosticScenario.request.blockId,
      ),
    ).toEqual({ runState: "completed", status: "Completed" });
    expect(
      diagnosticBlockOverlay(
        state,
        diagnosticScenario,
        diagnosticScenario.executorBlockId,
      ),
    ).toEqual({ runState: "running", status: "Running selected AI" });
    expect(
      diagnosticBlockOverlay(
        state,
        diagnosticScenario,
        "diagnostic-mcp-action",
      ),
    ).toEqual({ runState: "idle", status: "Waiting upstream" });

    const completed = reduceDiagnosticDemoState(
      state,
      {
        type: "llm-succeeded",
        result: {
          text: "Reviewable candidate output",
          provider: "test",
          model: "fixture",
          thinkingLevel: "medium",
        },
      },
      diagnosticScenario,
    );

    expect(completed.status).toBe("blocked");
    expect(completed.blockedAtBlockId).toBe(diagnosticScenario.mcpBlockId);
    expect(completed.llmResult?.text).toBe("Reviewable candidate output");
    expect(diagnosticReportForLlm(completed, diagnosticScenario)).toEqual(
      expect.objectContaining({
        executionStatus: "blocked",
        outcomeStatus: "not-evaluated",
        blockedAtBlockId: diagnosticScenario.mcpBlockId,
        llmResult: expect.objectContaining({
          text: "Reviewable candidate output",
        }),
        finding: expect.objectContaining({ code: "MCP_TOOL_NOT_SELECTED" }),
      }),
    );
  });

  it("treats an image as optional when no explicit requirement exists", () => {
    const state = reduceDiagnosticDemoState(
      createDiagnosticDemoState(),
      { type: "run", request: { ...validRequest, imageCount: 1 } },
      diagnosticScenario,
    );

    expect(state.status).toBe("running");
    expect(state.blockedAtBlockId).toBe(diagnosticScenario.executorBlockId);
    expect(state.inputIssues).toEqual([]);
  });

  it("stops at Prompt / Request when the explicit prompt is missing", () => {
    const state = reduceDiagnosticDemoState(
      createDiagnosticDemoState(),
      {
        type: "run",
        request: { ...validRequest, prompt: "" },
      },
      diagnosticScenario,
    );

    expect(state.status).toBe("blocked");
    expect(state.blockedAtBlockId).toBe(diagnosticScenario.request.blockId);
    expect(state.runs).toEqual([]);
    expect(state.inputIssues).toEqual([
      expect.objectContaining({ code: "PROMPT_REQUIRED", field: "prompt" }),
    ]);
    expect(
      diagnosticBlockOverlay(
        state,
        diagnosticScenario,
        diagnosticScenario.request.blockId,
      ),
    ).toEqual({ runState: "warning", status: "Missing required input" });
    expect(diagnosticReportForLlm(state, diagnosticScenario)).toEqual(
      expect.objectContaining({
        executionStatus: "blocked",
        outcomeStatus: "not-evaluated",
      }),
    );
  });
  it("rejects corrections until a failed result exists", () => {
    const initial = createDiagnosticDemoState();
    const unchanged = reduceDiagnosticDemoState(
      initial,
      { type: "apply-correction", correctionId: "state-dimension" },
      diagnosticScenario,
    );

    expect(unchanged).toBe(initial);
  });
});
