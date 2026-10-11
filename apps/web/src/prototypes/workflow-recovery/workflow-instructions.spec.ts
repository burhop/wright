import { describe, expect, it } from "vitest";
import { normalizeWorkflowInstructions } from "./workflow-instructions";
import {
  cloneWorkflow,
  cloneLayout,
  initialWorkflow,
  initialLayout,
} from "./model";
import {
  canonicalDefinitionBytes,
  toCanonicalWire,
  fromCanonicalWire,
} from "./canonical-wire";
import { formatRecoveryDsl, parseRecoveryDsl } from "./recovery-dsl";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
} from "./recovery-authoring";
import {
  acceptRecoveryResult,
  applyRecoveryBatch,
  recoveryCommandBatch,
  textEditCommands,
  type RecoveryCommand,
} from "./command-system";

function instructionCollection() {
  const body = "Preserve supplied dimensions and record delegated assumptions.";
  return {
    profile_id: "design-defaults",
    profile_version: "1",
    assets: [
      {
        id: "task-policy",
        role: "workflow-task",
        version: "1",
        body,
        body_digest:
          "a177cccfd6b33b5756adcce75e47b9d25b47db0e2e441b5d0a6b33831f83e173",
        origin: "wright-defaults",
      },
    ],
    bindings: [{ role: "workflow-task", asset_ids: ["task-policy"] }],
  };
}
describe("portable workflow instruction source", () => {
  it("preserves explicit action contract metadata and omits legacy null or absent fields", () => {
    const legacy = normalizeWorkflowInstructions(instructionCollection());
    expect(legacy).not.toHaveProperty("action_intent_contract");
    expect(
      normalizeWorkflowInstructions({
        ...instructionCollection(),
        action_intent_contract: null,
      }),
    ).toEqual(legacy);
    const modern = normalizeWorkflowInstructions({
      ...instructionCollection(),
      action_intent_contract: "wright.workflow-action-intent/1",
    });
    expect(modern.action_intent_contract).toBe(
      "wright.workflow-action-intent/1",
    );
    expect(() =>
      normalizeWorkflowInstructions({
        ...instructionCollection(),
        action_intent_contract: "wright.workflow-action-intent/999",
      }),
    ).toThrow();
  });
  it("normalizes the exact core defaults while retaining text, identifiers and ordered dependencies", () => {
    const source = instructionCollection();
    const normalized = normalizeWorkflowInstructions({
      ...source,
      profile_id: " design-defaults ",
      layers: [{ origin: "workflow-author", text: "Use documented units." }],
    });
    expect(normalized).toEqual({
      ...source,
      schema_version: "wright.workflow-instructions/1",
      assets: [
        {
          ...source.assets[0],
          schema_version: "wright.instruction-asset/1",
          variables: [],
          execution_contract: "wright.workflow-instructions/1",
        },
      ],
      policy: {
        assumption_policy: "require_specified",
        protected_requirements: [],
      },
      layers: [
        {
          origin: "workflow-author",
          roles: ["workflow-task", "image-generation", "mcp-task"],
          mode: "append",
          text: "Use documented units.",
          assumption_policy: null,
        },
      ],
    });
    expect(normalizeWorkflowInstructions(normalized)).toEqual(normalized);
  });
  it.each([
    [
      "missing body",
      (value: Record<string, any>) => delete value.assets[0].body,
    ],
    [
      "missing dependency",
      (value: Record<string, any>) =>
        (value.bindings[0].asset_ids = ["absent"]),
    ],
    [
      "crossed role",
      (value: Record<string, any>) =>
        (value.bindings[0].role = "image-generation"),
    ],
    [
      "duplicate identity",
      (value: Record<string, any>) => value.assets.push(value.assets[0]),
    ],
    [
      "duplicate binding",
      (value: Record<string, any>) => value.bindings.push(value.bindings[0]),
    ],
    [
      "duplicate asset in binding",
      (value: Record<string, any>) =>
        value.bindings[0].asset_ids.push("task-policy"),
    ],
    [
      "unlisted variable",
      (value: Record<string, any>) =>
        (value.assets[0].body += " {{dimensions}}"),
    ],
    [
      "invalid digest",
      (value: Record<string, any>) =>
        (value.assets[0].body_digest = "not-a-digest"),
    ],
    [
      "unknown fields",
      (value: Record<string, any>) => (value.hidden_policy = "override"),
    ],
    [
      "invalid version",
      (value: Record<string, any>) =>
        (value.schema_version = "future-contract"),
    ],
    [
      "empty replace",
      (value: Record<string, any>) =>
        (value.layers = [{ origin: "author", mode: "replace" }]),
    ],
    [
      "too much text",
      (value: Record<string, any>) =>
        (value.assets[0].body = "a".repeat(131073)),
    ],
    [
      "NUL text",
      (value: Record<string, any>) => (value.assets[0].body = "Do\0work"),
    ],
    [
      "invalid UTF-8 text",
      (value: Record<string, any>) => (value.assets[0].body = "Do\ud800work"),
    ],
  ])("rejects a %s without silently replacing defaults", (_label, corrupt) => {
    const value = instructionCollection();
    corrupt(value);
    expect(() => normalizeWorkflowInstructions(value)).toThrow(
      /Workflow instructions/,
    );
  });
  it("retains assumption policy, protected requirements and explicit scoped layer replacements", () => {
    const normalized = normalizeWorkflowInstructions({
      ...instructionCollection(),
      policy: {
        assumption_policy: "document_reasonable",
        protected_requirements: ["width", "thickness"],
      },
      layers: [
        {
          origin: "workflow-author",
          roles: ["workflow-task"],
          mode: "replace",
          text: "Preserve requirements.",
          assumption_policy: "require_specified",
        },
      ],
    });
    expect(normalized.policy).toEqual({
      assumption_policy: "document_reasonable",
      protected_requirements: ["width", "thickness"],
    });
    expect(normalized.layers[0]).toMatchObject({
      mode: "replace",
      roles: ["workflow-task"],
      assumption_policy: "require_specified",
    });
  });
  it("bounds UTF-8 collection size independently of character and per-asset limits", () => {
    const source = instructionCollection();
    expect(() =>
      normalizeWorkflowInstructions({
        ...source,
        assets: [{ ...source.assets[0], body: "界".repeat(45000) }],
      }),
    ).toThrow(/128 KiB/);
    expect(() =>
      normalizeWorkflowInstructions({
        ...source,
        assets: Array.from({ length: 5 }, (_, index) => ({
          ...source.assets[0],
          id: index === 0 ? "task-policy" : `asset-${index}`,
          body: "a".repeat(131072),
        })),
      }),
    ).toThrow(/512 KiB/);
  });
  it.each([undefined, "wright.workflow-action-intent/1"] as const)(
    "roundtrips through authoring source, internal DSL and canonical wire without instruction loss (%s)",
    (action_intent_contract) => {
      const workflow = cloneWorkflow(initialWorkflow);
      workflow.metadata.instructions = normalizeWorkflowInstructions({
        ...instructionCollection(),
        ...(action_intent_contract ? { action_intent_contract } : {}),
      });
      const authoring = formatRecoveryAuthoringSource(workflow).text;
      expect(authoring).toContain("  instructions: {");
      const parsed = parseRecoveryAuthoringSource(authoring, initialWorkflow);
      expect(parsed.ok, JSON.stringify(parsed.diagnostics)).toBe(true);
      expect(parsed.workflow!.metadata.instructions).toEqual(
        workflow.metadata.instructions,
      );
      const internal = parseRecoveryDsl(formatRecoveryDsl(workflow).text);
      expect(internal.ok, JSON.stringify(internal.diagnostics)).toBe(true);
      expect(internal.workflow!.metadata.instructions).toEqual(
        workflow.metadata.instructions,
      );
      const restored = fromCanonicalWire(toCanonicalWire(workflow));
      expect(restored.metadata.instructions).toEqual(
        workflow.metadata.instructions,
      );
      expect(canonicalDefinitionBytes(restored)).toBe(
        canonicalDefinitionBytes(workflow),
      );
    },
  );
  it("keeps legacy source and canonical identity free of injected instruction defaults", () => {
    const legacy = cloneWorkflow(initialWorkflow);
    const original = canonicalDefinitionBytes(legacy);
    expect(toCanonicalWire(legacy).metadata).not.toHaveProperty("instructions");
    expect(
      formatRecoveryAuthoringSource(legacy).text.split("end")[0],
    ).not.toContain("instructions:");
    const baseWithDefaults = cloneWorkflow(legacy);
    baseWithDefaults.metadata.instructions = normalizeWorkflowInstructions(
      instructionCollection(),
    );
    const parsed = parseRecoveryAuthoringSource(
      formatRecoveryAuthoringSource(legacy).text,
      baseWithDefaults,
    );
    expect(parsed.ok).toBe(true);
    expect(parsed.workflow!.metadata).not.toHaveProperty("instructions");
    expect(canonicalDefinitionBytes(parsed.workflow!)).toBe(original);
    expect(parseRecoveryDsl(formatRecoveryDsl(legacy).text).ok).toBe(true);
    expect(
      fromCanonicalWire(toCanonicalWire(legacy)).metadata,
    ).not.toHaveProperty("instructions");
  });
  it("rejects broken dependencies through both source entry points", () => {
    const workflow = cloneWorkflow(initialWorkflow);
    workflow.metadata.instructions = normalizeWorkflowInstructions(
      instructionCollection(),
    );
    const authoring = formatRecoveryAuthoringSource(workflow).text.replace(
      '"asset_ids":["task-policy"]',
      '"asset_ids":["missing"]',
    );
    const parsed = parseRecoveryAuthoringSource(authoring, workflow);
    expect(parsed.ok).toBe(false);
    expect(parsed.diagnostics[0].code).toBe("WFR-SOURCE-INSTRUCTIONS-INVALID");
    const internal = formatRecoveryDsl(workflow).text.replace(
      '"asset_ids":["task-policy"]',
      '"asset_ids":["missing"]',
    );
    expect(parseRecoveryDsl(internal).ok).toBe(false);
  });
  it("applies source instruction edits through accepted atomic commands and revision history", () => {
    const before = cloneWorkflow(initialWorkflow);
    const after = cloneWorkflow(before);
    after.metadata.instructions = normalizeWorkflowInstructions(
      instructionCollection(),
    );
    const commands = textEditCommands(before, after) as RecoveryCommand[];
    expect(commands).toEqual([
      { kind: "set_workflow_instructions", value: after.metadata.instructions },
    ]);
    const layout = cloneLayout(initialLayout);
    const result = applyRecoveryBatch(
      before,
      layout,
      recoveryCommandBatch(before.revision, "text", commands),
    );
    expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
    expect(result.semanticChanged).toBe(true);
    const accepted = acceptRecoveryResult(before, layout, result)!;
    expect(accepted.workflow.revision).toBe(before.revision + 1);
    expect(accepted.workflow.metadata.instructions).toEqual(
      after.metadata.instructions,
    );
    expect(accepted.workflow.blocks).toEqual(before.blocks);
    const removed = cloneWorkflow(accepted.workflow);
    delete removed.metadata.instructions;
    const removeCommands = textEditCommands(
      accepted.workflow,
      removed,
    ) as RecoveryCommand[];
    expect(removeCommands).toEqual([
      { kind: "set_workflow_instructions", value: null },
    ]);
    const removeResult = applyRecoveryBatch(
      accepted.workflow,
      accepted.layout,
      recoveryCommandBatch(accepted.workflow.revision, "text", removeCommands),
    );
    expect(removeResult.ok).toBe(true);
    expect(removeResult.workflow!.metadata).not.toHaveProperty("instructions");
    const undo = applyRecoveryBatch(
      accepted.workflow,
      accepted.layout,
      recoveryCommandBatch(accepted.workflow.revision, "history", [
        {
          kind: "restore_snapshot",
          direction: "undo",
          workflow: before,
          layout,
        },
      ]),
    );
    expect(undo.ok).toBe(true);
    expect(undo.workflow!.metadata).not.toHaveProperty("instructions");
  });
  it("rejects invalid instruction commands atomically without losing previously accepted source", () => {
    const before = cloneWorkflow(initialWorkflow);
    const bad = normalizeWorkflowInstructions(instructionCollection());
    bad.bindings[0].asset_ids = ["missing"];
    const result = applyRecoveryBatch(
      before,
      initialLayout,
      recoveryCommandBatch(before.revision, "form", [
        { kind: "set_workflow_metadata", patch: { title: "Must not commit" } },
        { kind: "set_workflow_instructions", value: bad },
      ]),
    );
    expect(result.ok).toBe(false);
    expect(result.workflow).toBeNull();
    expect(result.diagnostics[0].code).toBe("WFR-COMMAND-INSTRUCTIONS-INVALID");
    expect(before.metadata.title).toBe(initialWorkflow.metadata.title);
    expect(before.metadata).not.toHaveProperty("instructions");
  });
});
