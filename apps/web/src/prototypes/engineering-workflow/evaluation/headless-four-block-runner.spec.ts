import { describe, expect, it, vi } from "vitest";

import { runHeadlessFourBlockChain } from "./headless-four-block-runner.mjs";

describe("headless four-block runner", () => {
  it("executes the four semantic blocks in order without a UI", async () => {
    const order: string[] = [];
    const run = await runHeadlessFourBlockChain({
      request: { prompt: "Create a plate" },
      validateInput: async (request: { prompt: string }) => {
        order.push("request");
        return { output: request, evidence: { valid: true } };
      },
      generate: async () => {
        order.push("ai");
        return { output: { history: {} }, evidence: { model: "fixture" } };
      },
      invoke: async () => {
        order.push("mcp");
        return { output: { applied: true }, evidence: { tool: "fixture" } };
      },
      evaluate: async () => {
        order.push("evaluation");
        return {
          output: { accepted: true },
          evidence: { checks: ["applied"] },
        };
      },
    });

    expect(order).toEqual(["request", "ai", "mcp", "evaluation"]);
    expect(run.status).toBe("passed");
    expect(run.steps.map(({ status }) => status)).toEqual([
      "completed",
      "completed",
      "completed",
      "completed",
    ]);
    expect(run.steps.map(({ output }) => output)).toEqual([
      { prompt: "Create a plate" },
      { history: {} },
      { applied: true },
      { accepted: true },
    ]);
  });

  it("stops before MCP when generated arguments are invalid", async () => {
    const invoke = vi.fn();
    await expect(
      runHeadlessFourBlockChain({
        request: { prompt: "Create a plate" },
        validateInput: async (request: { prompt: string }) => ({
          output: request,
        }),
        generate: async () => {
          throw new Error("Generated history does not match the tool schema");
        },
        invoke,
        evaluate: vi.fn(),
      }),
    ).rejects.toMatchObject({
      run: {
        status: "failed",
        steps: [
          { block: "request", status: "completed" },
          { block: "ai", status: "failed" },
        ],
      },
    });
    expect(invoke).not.toHaveBeenCalled();
  });
});
