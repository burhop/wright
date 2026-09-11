import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { McpTaskOptions } from "./McpTaskOptions";
import { createAuthoringObject } from "./authoring-objects";
import {
  acceptRecoveryResult,
  applyRecoveryBatch,
  recoveryCommandBatch,
} from "./command-system";
import { initialWorkflow, initialLayout } from "./model";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
} from "./recovery-authoring";

function fixture() {
  const add = createAuthoringObject("mcp-task", initialWorkflow, initialLayout);
  const created = acceptRecoveryResult(
    initialWorkflow,
    initialLayout,
    applyRecoveryBatch(
      initialWorkflow,
      initialLayout,
      recoveryCommandBatch(initialWorkflow.revision, "form", [add]),
    ),
  )!;
  return {
    ...created,
    block: created.workflow.blocks.find((block) => block.id === add.block.id)!,
  };
}

it("offers32 calls while preserving default8 and the600-second maximum", () => {
  const { workflow, block } = fixture();
  const apply = vi.fn(() => true);
  render(
    <McpTaskOptions
      block={block}
      workflow={workflow}
      readOnly={false}
      onApply={apply}
    />,
  );
  const calls = screen.getByRole("spinbutton", { name: /Maximum tool calls/ });
  expect(calls).toHaveValue(8);
  expect(calls).toHaveAttribute("max", "32");
  expect(calls).toHaveAttribute("step", "1");
  expect(
    screen.getByText(
      "1–32 calls per task; default 8. The time limit still applies.",
    ),
  ).toBeInTheDocument();
  const timeout = screen.getByRole("spinbutton", {
    name: "Time limit (seconds)",
  });
  expect(timeout).toHaveValue(300);
  expect(timeout).toHaveAttribute("max", "600");
  fireEvent.change(calls, { target: { value: "32" } });
  expect(apply).toHaveBeenCalledWith([
    {
      kind: "set_block_configuration",
      blockId: block.id,
      key: "max_tool_calls",
      value: 32,
    },
  ]);
});

it("preserves an accepted32-call budget through canonical source reopen", () => {
  const { workflow, layout, block } = fixture();
  const result = applyRecoveryBatch(
    workflow,
    layout,
    recoveryCommandBatch(workflow.revision, "form", [
      {
        kind: "set_block_configuration",
        blockId: block.id,
        key: "max_tool_calls",
        value: 32,
      },
    ]),
  );
  expect(result.ok).toBe(true);
  const accepted = acceptRecoveryResult(workflow, layout, result)!;
  const reopened = parseRecoveryAuthoringSource(
    formatRecoveryAuthoringSource(accepted.workflow).text,
    initialWorkflow,
  );
  expect(reopened.ok).toBe(true);
  expect(
    reopened.workflow!.blocks.find((item) => item.id === block.id)!
      .configuration.max_tool_calls,
  ).toBe(32);
});

it.each([33, 0, 1.5, true, "32"])(
  "rejects invalid budget %s through the shared authoring command boundary",
  (value) => {
    const { workflow, layout, block } = fixture();
    const result = applyRecoveryBatch(
      workflow,
      layout,
      recoveryCommandBatch(workflow.revision, "form", [
        {
          kind: "set_block_configuration",
          blockId: block.id,
          key: "max_tool_calls",
          value,
        },
      ]),
    );
    expect(result.ok).toBe(false);
    expect(result.diagnostics).toContainEqual(
      expect.objectContaining({ code: "WFR-MCP-TASK-LIMIT-INVALID" }),
    );
    expect(block.configuration.max_tool_calls).toBe(8);
    const invalidSource = formatRecoveryAuthoringSource({
      ...workflow,
      blocks: workflow.blocks.map((item) =>
        item.id === block.id
          ? {
              ...item,
              configuration: { ...item.configuration, max_tool_calls: value },
            }
          : item,
      ),
    }).text;
    const parsed = parseRecoveryAuthoringSource(invalidSource, initialWorkflow);
    expect(parsed.ok).toBe(false);
    expect(parsed.diagnostics).toContainEqual(
      expect.objectContaining({ code: "WFR-MCP-TASK-LIMIT-INVALID" }),
    );
  },
);
