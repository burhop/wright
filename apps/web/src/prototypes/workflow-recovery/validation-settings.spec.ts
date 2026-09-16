import { describe, expect, it } from "vitest";
import { createAuthoringObject } from "./authoring-objects";
import {
  acceptRecoveryResult,
  applyRecoveryBatch,
  recoveryCommandBatch,
  type RecoveryCommand,
} from "./command-system";
import {
  initialWorkflow,
  initialLayout,
  type RecoveryWorkflow,
  type RecoveryLayout,
} from "./model";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
  validateRecoveryAuthoringRoundTrip,
} from "./recovery-authoring";
import {
  validationProfileCommands,
  validationSubjectCommands,
  validatorSettings,
} from "./validation-settings";

function apply(
  workflow: RecoveryWorkflow,
  layout: RecoveryLayout,
  commands: RecoveryCommand[],
) {
  const result = applyRecoveryBatch(
    workflow,
    layout,
    recoveryCommandBatch(
      workflow.revision,
      commands[0]?.kind === "restore_snapshot" ? "history" : "form",
      commands,
    ),
  );
  expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
  return acceptRecoveryResult(workflow, layout, result)!;
}

function configured() {
  const produce = createAuthoringObject(
    "ai-prompt",
    initialWorkflow,
    initialLayout,
  );
  const started = apply(initialWorkflow, initialLayout, [produce]);
  const add = createAuthoringObject(
    "process-validator",
    started.workflow,
    started.layout,
  );
  const created = apply(started.workflow, started.layout, [add]);
  const selected = apply(
    created.workflow,
    created.layout,
    validationProfileCommands(add.block, created.workflow, "structured-demo"),
  );
  return { ...selected, id: add.block.id, created };
}

describe("validator authoring uses the accepted command/source model", () => {
  it("adds an ordinary validator and saves/reopens pins and subject roles without an MCP binding", () => {
    const selected = configured();
    const block = selected.workflow.blocks.find((b) => b.id === selected.id)!;
    expect(block.bindingId).toBeNull();
    expect(block.executionKind).toBe("deterministic");
    expect(validatorSettings(block)?.subjects.result).toBeTruthy();
    expect(validateRecoveryAuthoringRoundTrip(selected.workflow).ok).toBe(true);
    const source = formatRecoveryAuthoringSource(selected.workflow).text;
    const parsed = parseRecoveryAuthoringSource(source, initialWorkflow);
    expect(parsed.ok, JSON.stringify(parsed.diagnostics)).toBe(true);
    const reopened = parsed.workflow!.blocks.find((b) => b.id === selected.id)!;
    expect(validatorSettings(reopened)).toEqual(validatorSettings(block));
    expect(source).toMatch(/"validation":\s*\{/);
  });

  it("connects the exact producing output and preserves its type", () => {
    const selected = configured();
    const block = selected.workflow.blocks.find((b) => b.id === selected.id)!;
    const source = selected.workflow.ports.find(
      (p) =>
        p.direction === "output" &&
        p.typeId === "type.document.engineering" &&
        p.ownerBlockId !== block.id,
    )!;
    const connected = apply(
      selected.workflow,
      selected.layout,
      validationSubjectCommands(
        block,
        selected.workflow,
        block.inputPortIds[0]!,
        source.id,
      ),
    );
    expect(
      connected.workflow.relationships.some(
        (e) => e.sourceId === source.id && e.targetId === block.inputPortIds[0],
      ),
    ).toBe(true);
    expect(validateRecoveryAuthoringRoundTrip(connected.workflow).ok).toBe(
      true,
    );
  });

  it("undoes and redoes profile selection through the existing history commands", () => {
    const selected = configured();
    const undo = apply(selected.workflow, selected.layout, [
      {
        kind: "restore_snapshot",
        direction: "undo",
        workflow: selected.created.workflow,
        layout: selected.created.layout,
      },
    ]);
    expect(
      validatorSettings(
        undo.workflow.blocks.find((b) => b.id === selected.id)!,
      ),
    ).toBeNull();
    const redo = apply(undo.workflow, undo.layout, [
      {
        kind: "restore_snapshot",
        direction: "redo",
        workflow: selected.workflow,
        layout: selected.layout,
      },
    ]);
    expect(
      validatorSettings(
        redo.workflow.blocks.find((b) => b.id === selected.id)!,
      ),
    ).toEqual(
      validatorSettings(
        selected.workflow.blocks.find((b) => b.id === selected.id)!,
      ),
    );
  });

  it("rejects malformed pin edits without changing the accepted definition", () => {
    const selected = configured();
    const previous = formatRecoveryAuthoringSource(selected.workflow).text;
    const result = applyRecoveryBatch(
      selected.workflow,
      selected.layout,
      recoveryCommandBatch(selected.workflow.revision, "form", [
        {
          kind: "set_block_configuration",
          blockId: selected.id,
          key: "validation",
          value: '{"profile":{}}',
        },
      ]),
    );
    expect(result.ok).toBe(false);
    expect(formatRecoveryAuthoringSource(selected.workflow).text).toBe(
      previous,
    );
  });
});
