import { describe, expect, it } from "vitest";

import { canonicalDefinitionBytes } from "./canonical-wire";
import {
  acceptRecoveryResult,
  aiDrawingProposal,
  applyRecoveryBatch,
  paletteBlock,
  recoveryCommandBatch,
  textEditCommands,
  type RecoveryCommand,
} from "./command-system";
import { cloneLayout, cloneWorkflow, initialLayout, initialWorkflow, type RecoveryWorkflow } from "./model";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
  recoveryAuthoringSemanticIdAtOffset,
  validateRecoveryAuthoringRoundTrip,
} from "./recovery-authoring";

function semanticBytes(workflow: RecoveryWorkflow): string {
  return canonicalDefinitionBytes(workflow, true);
}

function apply(workflow: RecoveryWorkflow, commands: RecoveryCommand[]): RecoveryWorkflow {
  const layout = cloneLayout(initialLayout);
  layout.semanticRevision = workflow.revision;
  const result = applyRecoveryBatch(workflow, layout, recoveryCommandBatch(workflow.revision, "graph", commands));
  expect(result.ok, result.diagnostics.map((item) => item.code).join(", ")).toBe(true);
  return acceptRecoveryResult(workflow, layout, result)!.workflow;
}

function expectColdRoundTrip(workflow: RecoveryWorkflow): void {
  const result = validateRecoveryAuthoringRoundTrip(workflow);
  expect(result.ok, result.diagnostics.map((item) => item.code).join(", ")).toBe(true);
  expect(semanticBytes(result.workflow!)).toBe(semanticBytes(workflow));
}

function withoutReferenceImages(): RecoveryWorkflow {
  return apply(initialWorkflow, [
    { kind: "disconnect", relationshipId: "rel.reference-to-specification" },
    { kind: "delete_block", blockId: "block.reference-images" },
  ]);
}

function newlyAuthoredInputSource(): string {
  return [
    formatRecoveryAuthoringSource(initialWorkflow).text,
    "input supplier_requirements",
    '  name: "Supplier requirements"',
    '  purpose: "Provide supplier constraints before engineering work begins."',
    '  step_type: "work"',
    "  group: null",
    '  provided_by: "engineer"',
    "  inputs: []",
    "  outputs: []",
    '  instructions: "Attach the approved supplier requirements."',
    "  settings: {}",
    "  tool: null",
    "  reusable_step: null",
    "end",
    "",
  ].join("\n");
}

describe("engineering workflow source", () => {
  it("rehydrates the friendly projection against the exact accepted envelope", () => {
    const formatted = formatRecoveryAuthoringSource(initialWorkflow);
    const parsed = parseRecoveryAuthoringSource(formatted.text, initialWorkflow);
    expect(parsed.diagnostics).toEqual([]);
    expect(parsed.ok).toBe(true);
    expect(canonicalDefinitionBytes(parsed.workflow!)).toBe(canonicalDefinitionBytes(initialWorkflow));
    expect(formatted.text).toContain("input design_intent");
    expect(formatted.text).toContain("task generate_geometry");
    expect(formatted.text).not.toContain("\ngroup ");
    expect(formatted.text).toContain("  group: null");
    expect(formatted.text).not.toMatch(/^\s*(revision|parent|semantic_sha256):/m);
    expect(formatted.text).not.toContain("block.");
  });

  it("keeps canonical software identities out of public connection points", () => {
    const proposal = applyRecoveryBatch(initialWorkflow, initialLayout, aiDrawingProposal(initialWorkflow));
    expect(proposal.ok).toBe(true);
    const proposedWorkflow = acceptRecoveryResult(initialWorkflow, initialLayout, proposal)!.workflow;
    const candidates = [
      initialWorkflow,
      apply(initialWorkflow, [paletteBlock("tolerance")]),
      proposedWorkflow,
    ];

    for (const candidate of candidates) {
      const source = formatRecoveryAuthoringSource(candidate).text;
      expect(source).toContain('"kind":');
      expect(source).not.toContain("engineering_type");
      expect(source).not.toMatch(/\b(?:type|block|port|artifact)\./);
      expectColdRoundTrip(candidate);
    }
  });

  it("fails closed when an internal connection-point type has no public kind", () => {
    const unsupported = cloneWorkflow(initialWorkflow);
    unsupported.ports[0]!.typeId = "type.unsupported.internal";
    expect(() => formatRecoveryAuthoringSource(unsupported)).toThrow("WFR-SOURCE-PORT-KIND-UNSUPPORTED:type.unsupported.internal");
  });

  it("rejects an unknown public connection-point kind", () => {
    const source = formatRecoveryAuthoringSource(initialWorkflow).text.replace('"kind":"reference_images"', '"kind":"unknown_engineering_kind"');
    const parsed = parseRecoveryAuthoringSource(source, initialWorkflow);
    expect(parsed.ok).toBe(false);
    expect(parsed.workflow).toBeNull();
    expect(parsed.diagnostics).toContainEqual(expect.objectContaining({ code: "WFR-SOURCE-PORT-KIND" }));
  });

  it("turns an engineering-source prompt edit into a contained command", () => {
    const formatted = formatRecoveryAuthoringSource(initialWorkflow).text;
    const edited = formatted.replace("Create the bracket with two mounting holes and one slotted interface.", "Create the bracket with two mounting holes and two slotted interfaces.");
    const parsed = parseRecoveryAuthoringSource(edited, initialWorkflow);
    expect(parsed.diagnostics).toEqual([]);
    expect(textEditCommands(initialWorkflow, parsed.workflow!)).toContainEqual({
      kind: "set_block_definition",
      blockId: "block.generate-geometry",
      patch: { instructions: "Create the bracket with two mounting holes and two slotted interfaces." },
    });
  });

  it("rejects host-managed authority fields and retains the accepted definition", () => {
    const formatted = formatRecoveryAuthoringSource(initialWorkflow).text;
    const edited = formatted.replace("  name: \"Mounting bracket development\"", "  revision: 99\n  name: \"Mounting bracket development\"");
    const parsed = parseRecoveryAuthoringSource(edited, initialWorkflow);
    expect(parsed.ok).toBe(false);
    expect(parsed.diagnostics).toContainEqual(expect.objectContaining({ code: "WFR-SOURCE-FIELD-MANAGED" }));
    expect(parsed.workflow).toBeNull();
  });

  it("selects the engineering task instead of an overlapping internal port span", () => {
    const formatted = formatRecoveryAuthoringSource(initialWorkflow);
    const offset = formatted.text.indexOf("task export_step") + "task ".length;
    expect(recoveryAuthoringSemanticIdAtOffset(formatted.sourceMap, offset)).toBe("block.export-step");
  });

  it.each([
    ["add", () => apply(initialWorkflow, [paletteBlock("tolerance")])],
    ["delete", withoutReferenceImages],
    ["disconnect", () => apply(initialWorkflow, [{ kind: "disconnect", relationshipId: "rel.review-to-export" }])],
    ["connect", () => {
      const disconnected = apply(initialWorkflow, [{ kind: "disconnect", relationshipId: "rel.review-to-export" }]);
      return apply(disconnected, [{
        kind: "connect",
        relationship: structuredClone(initialWorkflow.relationships.find((item) => item.id === "rel.review-to-export")!),
      }]);
    }],
  ] as const)("cold-reopens a %s command from the one visible source", (_name, candidate) => {
    expectColdRoundTrip(candidate());
  });

  it("cold-reopens a reviewed AI proposal with its new steps, ports, and routes", () => {
    const result = applyRecoveryBatch(initialWorkflow, initialLayout, aiDrawingProposal(initialWorkflow));
    expect(result.ok).toBe(true);
    const accepted = acceptRecoveryResult(initialWorkflow, initialLayout, result)!.workflow;
    const formatted = formatRecoveryAuthoringSource(accepted).text;
    expect(formatted).toContain("task create_inspection_drawing");
    expect(formatted).toContain("connection approved_to_drawing");
    expectColdRoundTrip(accepted);
  });

  it("keeps groups optional while preserving a group rename when groups exist", () => {
    const renamed = apply(initialWorkflow, [{ kind: "set_phase_name", phaseId: "phase.verify", name: "Engineering review" }]);
    expect(formatRecoveryAuthoringSource(renamed).text).toContain('name: "Engineering review"');
    expectColdRoundTrip(renamed);

    const withoutGroupSections = formatRecoveryAuthoringSource(initialWorkflow).text.replace(/group (define|verify|deliver)\n(?:  .+\n)+end\n\n/g, "");
    const parsed = parseRecoveryAuthoringSource(withoutGroupSections, initialWorkflow);
    expect(parsed.ok).toBe(true);
    expect(semanticBytes(parsed.workflow!)).toBe(semanticBytes(initialWorkflow));

    const ungrouped = cloneWorkflow(initialWorkflow);
    ungrouped.phases = [];
    for (const block of ungrouped.blocks) block.phaseId = null;
    expect(formatRecoveryAuthoringSource(ungrouped).text).not.toContain("\ngroup ");
    const ungroupedResult = validateRecoveryAuthoringRoundTrip(ungrouped, ungrouped);
    expect(ungroupedResult.ok).toBe(true);
  });

  it("lowers a source-added ungrouped task through the atomic command set", () => {
    const source = formatRecoveryAuthoringSource(initialWorkflow).text;
    const task = [
      "task record_release_note",
      '  name: "Record release note"',
      '  purpose: "Record the local handoff note."',
      '  step_type: "work"',
      "  group: null",
      '  performed_by: "engineer"',
      "  inputs: []",
      "  outputs: []",
      '  instructions: "Record the local handoff note."',
      "  settings: {}",
      "  tool: null",
      "  reusable_step: null",
      "end",
      "",
    ].join("\n");
    const parsed = parseRecoveryAuthoringSource(`${source}\n${task}`, initialWorkflow);
    expect(parsed.ok, parsed.diagnostics.map((item) => item.code).join(", ")).toBe(true);
    const commands = textEditCommands(initialWorkflow, parsed.workflow!);
    expect(commands).toContainEqual(expect.objectContaining({
      kind: "add_block",
      block: expect.objectContaining({ id: "block.record-release-note", phaseId: null }),
    }));
    const accepted = apply(initialWorkflow, commands as RecoveryCommand[]);
    expect(accepted.blocks).toContainEqual(expect.objectContaining({ id: "block.record-release-note", phaseId: null }));
    expectColdRoundTrip(accepted);
  });

  it("cold format-parse-formats a newly authored input without changing it into a task", () => {
    const authored = parseRecoveryAuthoringSource(newlyAuthoredInputSource(), initialWorkflow);
    expect(authored.ok, authored.diagnostics.map((item) => item.code).join(", ")).toBe(true);
    const firstFormat = formatRecoveryAuthoringSource(authored.workflow!).text;
    expect(firstFormat).toContain("\ninput supplier_requirements\n");
    expect(firstFormat).toContain("  provided_by: engineer");
    expect(firstFormat).not.toContain("\ntask supplier_requirements\n");
    expect(firstFormat).not.toContain("__wright_authoring_section");

    const reopened = parseRecoveryAuthoringSource(firstFormat, initialWorkflow);
    expect(reopened.ok, reopened.diagnostics.map((item) => item.code).join(", ")).toBe(true);
    expect(formatRecoveryAuthoringSource(reopened.workflow!).text).toBe(firstFormat);
    expect(semanticBytes(reopened.workflow!)).toBe(semanticBytes(authored.workflow!));
  });

  it("carries a newly authored input through the typed add-block command boundary and cold reopen", () => {
    const authored = parseRecoveryAuthoringSource(newlyAuthoredInputSource(), initialWorkflow);
    expect(authored.ok, authored.diagnostics.map((item) => item.code).join(", ")).toBe(true);
    const commands = textEditCommands(initialWorkflow, authored.workflow!);
    expect(commands).toContainEqual(expect.objectContaining({
      kind: "add_block",
      block: expect.objectContaining({ id: "block.supplier-requirements" }),
    }));

    const accepted = apply(initialWorkflow, commands as RecoveryCommand[]);
    const storedSource = formatRecoveryAuthoringSource(accepted).text;
    expect(storedSource).toContain("\ninput supplier_requirements\n");
    expect(storedSource).not.toContain("\ntask supplier_requirements\n");
    const reopened = parseRecoveryAuthoringSource(storedSource, initialWorkflow);
    expect(reopened.ok, reopened.diagnostics.map((item) => item.code).join(", ")).toBe(true);
    expect(formatRecoveryAuthoringSource(reopened.workflow!).text).toBe(storedSource);
    expect(semanticBytes(reopened.workflow!)).toBe(semanticBytes(accepted));
  });

  it.each([
    ["workflow discipline", { kind: "set_workflow_metadata", patch: { engineeringDomain: "mechanical_design.custom" } } as const],
    ["engineering item", { kind: "set_artifact_definition", artifactId: "artifact.design-intent", patch: { name: "Loads and design intent", description: "Engineer-entered loads, interfaces, constraints, units, and material decisions." } } as const],
    ["port requirement", { kind: "set_port_contract", portId: "port.design-intent-out", required: false, cardinality: "optional" } as const],
    ["tool assignment", { kind: "set_binding_tool", bindingId: "binding.generate-geometry", toolId: "tool.create-production-bracket" } as const],
    ["connection details", { kind: "update_relationship", relationshipId: "rel.review-to-export", patch: { label: "released CAD model", condition: "Engineer approval recorded" } } as const],
  ])("cold-reopens an exposed %s edit", (_name, command) => {
    expectColdRoundTrip(apply(initialWorkflow, [command]));
  });

  it("lowers a source-added task and source-created connection to the shared command set", () => {
    const added = apply(initialWorkflow, [paletteBlock("drawing")]);
    const connected = apply(added, [{
      kind: "connect",
      relationship: {
        id: "rel.approved-to-drawing-1",
        kind: "data",
        sourceId: "port.approved-geometry-out",
        targetId: "port.drawing-1-in",
        label: "approved CAD model",
        condition: "decision.accepted",
      },
    }]);
    const parsed = parseRecoveryAuthoringSource(formatRecoveryAuthoringSource(connected).text, initialWorkflow);
    expect(parsed.ok).toBe(true);
    const commands = textEditCommands(initialWorkflow, parsed.workflow!);
    expect(commands).toEqual(expect.arrayContaining([
      expect.objectContaining({ kind: "add_block", block: expect.objectContaining({ id: "block.drawing-1" }) }),
      expect.objectContaining({ kind: "connect", relationship: expect.objectContaining({ id: "rel.approved-to-drawing-1" }) }),
    ]));
  });

  it.each([
    ["disconnect", () => apply(initialWorkflow, [{ kind: "disconnect", relationshipId: "rel.review-to-export" }]), "disconnect"],
    ["delete", withoutReferenceImages, "delete_block"],
  ] as const)("lowers a source-driven %s to the shared command set", (_name, candidate, expectedKind) => {
    const before = initialWorkflow;
    const parsed = parseRecoveryAuthoringSource(formatRecoveryAuthoringSource(candidate()).text, before);
    expect(parsed.ok).toBe(true);
    const commands = textEditCommands(before, parsed.workflow!);
    expect(commands).toEqual(expect.arrayContaining([expect.objectContaining({ kind: expectedKind })]));
  });

  it("rejects a candidate whose semantic facts are not represented by the public source", () => {
    const candidate = cloneWorkflow(initialWorkflow);
    candidate.artifactContracts.find((item) => item.id === "artifact.design-specification")!.mediaType = "application/octet-stream";
    const result = validateRecoveryAuthoringRoundTrip(candidate);
    expect(result.ok).toBe(false);
    expect(result.workflow).toBeNull();
    expect(result.diagnostics).not.toEqual([]);
  });
});
