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
  validationRevisionCommands,
  validationRevisionLimitCommands,
  validationRevisionTargets,
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
  it("retains source-configured correction subjects through diagram save/reopen", () => {
    const selected = configured();
    const block = selected.workflow.blocks.find((b) => b.id === selected.id)!;
    const settings = {
      ...validatorSettings(block)!,
      rework_scope: "verified_segment",
      repair_subjects: ["result"],
    };
    block.configuration.validation = JSON.stringify(settings);
    expect(validatorSettings(block)).toEqual(settings);
    const source = formatRecoveryAuthoringSource(selected.workflow).text;
    const parsed = parseRecoveryAuthoringSource(source, initialWorkflow);
    expect(parsed.ok, JSON.stringify(parsed.diagnostics)).toBe(true);
    const reopened = parsed.workflow!.blocks.find((b) => b.id === selected.id)!;
    expect(validatorSettings(reopened)).toEqual(settings);
    expect(() =>
      validationProfileCommands(reopened, parsed.workflow!, "structured-demo"),
    ).toThrow(
      "Edit its requirements and correction settings together in Source",
    );
    for (const repair_subjects of [[], ["missing"], ["result", "result"]]) {
      block.configuration.validation = JSON.stringify({
        ...settings,
        repair_subjects,
      });
      expect(validatorSettings(block)).toBeNull();
    }
  });

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

  it("adds one bounded correction path to the exact safe subject producer and round-trips it", () => {
    const selected = configured();
    const block = selected.workflow.blocks.find((b) => b.id === selected.id)!;
    const producer = selected.workflow.blocks.find(
      (candidate) =>
        candidate.id !== block.id && candidate.executionKind === "ai_capable",
    )!;
    const source = selected.workflow.ports.find(
      (port) =>
        port.ownerBlockId === producer.id && port.direction === "output",
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
    const current = connected.workflow.blocks.find((b) => b.id === block.id)!;
    expect(validationRevisionTargets(current, connected.workflow)).toEqual([
      expect.objectContaining({ id: producer.id }),
    ]);
    const revised = apply(
      connected.workflow,
      connected.layout,
      validationRevisionCommands(current, connected.workflow, producer.id),
    );
    const revisedBlock = revised.workflow.blocks.find(
      (b) => b.id === block.id,
    )!;
    expect(revisedBlock.configuration.max_revisions).toBe(1);
    expect(revised.workflow.relationships).toContainEqual(
      expect.objectContaining({
        kind: "feedback",
        sourceId: block.id,
        targetId: producer.id,
        condition: "revise",
      }),
    );
    expect(validateRecoveryAuthoringRoundTrip(revised.workflow).ok).toBe(true);
    const reopened = parseRecoveryAuthoringSource(
      formatRecoveryAuthoringSource(revised.workflow).text,
      initialWorkflow,
    );
    expect(reopened.ok).toBe(true);
    expect(reopened.workflow!.relationships).toContainEqual(
      expect.objectContaining({
        kind: "feedback",
        sourceId: block.id,
        targetId: producer.id,
      }),
    );

    const disabled = apply(
      revised.workflow,
      revised.layout,
      validationRevisionLimitCommands(revisedBlock, revised.workflow, 0),
    );
    expect(
      disabled.workflow.blocks.find((b) => b.id === block.id)!.configuration
        .max_revisions,
    ).toBe(0);
    expect(
      disabled.workflow.relationships.some(
        (edge) => edge.kind === "feedback" && edge.sourceId === block.id,
      ),
    ).toBe(false);
  });

  it.each(["overwrite", "publish_indexed", "publish_overwrite"])(
    "does not offer %s producers for automatic correction",
    (policy) => {
      const selected = configured();
      const block = selected.workflow.blocks.find((b) => b.id === selected.id)!;
      const source = selected.workflow.ports.find(
        (port) =>
          port.direction === "output" &&
          port.ownerBlockId !== block.id &&
          port.typeId === "type.document.engineering",
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
      const owner = connected.workflow.blocks.find(
        (b) => b.id === source.ownerBlockId,
      )!;
      owner.configuration.file_policy = policy;
      expect(validationRevisionTargets(block, connected.workflow)).toEqual([]);
      expect(() =>
        validationRevisionCommands(block, connected.workflow, owner.id),
      ).toThrow(/ordinary AI producer/);
    },
  );

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
