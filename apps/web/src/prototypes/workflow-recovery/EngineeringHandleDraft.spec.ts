import acceptedHandleSource from "./fixtures/handle-before-manufacturing-split.wflow?raw";
import { hydrateAuthoringLayout } from "./authoring-positioning";
import source from "../../../../../prototypes/desktop-harness/engineering-experience/handle/replacement-handle-draft.workflow.wflow?raw";
import { expect, it } from "vitest";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
  parseRecoverySourceDocument,
} from "./recovery-authoring";

it("opens the actual desktop handle draft and preserves its evidence and review connections on save", () => {
  const parsed = parseRecoverySourceDocument(source, 1);
  expect(parsed.ok, JSON.stringify(parsed.diagnostics)).toBe(true);
  const workflow = parsed.workflow!;
  expect(
    workflow.blocks.some(
      (block) => block.title === "Review the proposed print package",
    ),
  ).toBe(true);
  const formatted = formatRecoveryAuthoringSource(workflow);
  const reopened = parseRecoveryAuthoringSource(formatted.text, workflow);
  expect(reopened.ok, JSON.stringify(reopened.diagnostics)).toBe(true);
  expect(reopened.workflow!.relationships).toEqual(workflow.relationships);
  expect(reopened.workflow!.ports).toEqual(workflow.ports);
  expect(reopened.workflow!.blocks.map((block) => block.configuration)).toEqual(
    workflow.blocks.map((block) => block.configuration),
  );
});

it("places the handle stages in forward dependency order without changing source or saved moves", () => {
  const parsed = parseRecoverySourceDocument(source, 1);
  expect(parsed.ok).toBe(true);
  const workflow = parsed.workflow!;
  const before = JSON.stringify(workflow);
  const layout = hydrateAuthoringLayout(workflow);
  const owners = new Map(
    workflow.ports.map((port) => [port.id, port.ownerBlockId]),
  );
  let checked = 0;
  for (const edge of workflow.relationships) {
    if (edge.kind === "feedback") continue;
    const from = layout.positions[owners.get(edge.sourceId) ?? edge.sourceId];
    const to = layout.positions[owners.get(edge.targetId) ?? edge.targetId];
    if (!from || !to || from === to) continue;
    expect(from.x, edge.id).toBeLessThan(to.x);
    checked++;
  }
  expect(checked).toBeGreaterThan(30);
  expect(JSON.stringify(workflow)).toBe(before);
  const id = workflow.blocks[0].id;
  layout.positions[id] = { x: 987, y: 654 };
  expect(hydrateAuthoringLayout(workflow, layout)).toEqual(layout);
});

it("keeps cyclic or disconnected drafts inspectable and preserves their connections", () => {
  const workflow = parseRecoverySourceDocument(source, 1).workflow!;
  const [first, second] = workflow.blocks;
  workflow.relationships = [
    {
      ...workflow.relationships[0],
      id: "cycle-a",
      kind: "control",
      sourceId: first.id,
      targetId: second.id,
    },
    {
      ...workflow.relationships[0],
      id: "cycle-b",
      kind: "control",
      sourceId: second.id,
      targetId: first.id,
    },
  ];
  const before = JSON.stringify(workflow);
  const layout = hydrateAuthoringLayout(workflow);
  expect(Object.keys(layout.positions)).toHaveLength(workflow.blocks.length);
  expect(
    new Set(Object.values(layout.positions).map((p) => `${p.x},${p.y}`)).size,
  ).toBe(workflow.blocks.length);
  expect(JSON.stringify(workflow)).toBe(before);
});

it("changes an existing handle step into a review while retaining subjects and revision history", async () => {
  const {
    textEditCommands,
    applyRecoveryBatch,
    recoveryCommandBatch,
    acceptRecoveryResult,
  } = await import("./command-system");
  const oldSource = source.replace(
    /task print_review\n[\s\S]*?\nend/,
    (section) =>
      section
        .replace("step_type: review", "step_type: work")
        .replace(
          / {2}settings: .*/,
          '  settings: {"authoring_template":"manual-review"}',
        ),
  );
  const before = parseRecoverySourceDocument(oldSource, 3).workflow!;
  const parsed = parseRecoveryAuthoringSource(source, before);
  expect(parsed.ok, JSON.stringify(parsed.diagnostics)).toBe(true);
  const commands = textEditCommands(before, parsed.workflow!);
  expect(
    commands.some(
      (command) => "kind" in command && command.kind === "set_block_kind",
    ),
  ).toBe(true);
  const layout = hydrateAuthoringLayout(before);
  const result = applyRecoveryBatch(
    before,
    layout,
    recoveryCommandBatch(
      before.revision,
      "text",
      commands as import("./command-system").RecoveryCommand[],
    ),
  );
  expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
  const accepted = acceptRecoveryResult(before, layout, result)!;
  expect(accepted.workflow.revision).toBe(4);
  const review = accepted.workflow.blocks.find(
    (b) => b.title === "Review the proposed print package",
  )!;
  expect(review.kind).toBe("approval");
  expect(review.inputPortIds).toHaveLength(7);
  expect(accepted.workflow.ports).toEqual(before.ports);
  expect(accepted.workflow.relationships).toEqual(before.relationships);
  const reopened = parseRecoverySourceDocument(
    formatRecoveryAuthoringSource(accepted.workflow).text,
    4,
  );
  expect(reopened.ok).toBe(true);
  expect(
    reopened.workflow!.blocks.find((b) => b.id === review.id)?.configuration,
  ).toEqual(review.configuration);
  const undo = applyRecoveryBatch(
    accepted.workflow,
    accepted.layout,
    recoveryCommandBatch(4, "history", [
      { kind: "restore_snapshot", direction: "undo", workflow: before, layout },
    ]),
  );
  expect(undo.ok).toBe(true);
  expect(undo.workflow!.blocks.find((b) => b.id === review.id)?.kind).toBe(
    "work",
  );
  const redo = applyRecoveryBatch(
    undo.workflow!,
    undo.layout!,
    recoveryCommandBatch(undo.workflow!.revision, "history", [
      {
        kind: "restore_snapshot",
        direction: "redo",
        workflow: accepted.workflow,
        layout: accepted.layout,
      },
    ]),
  );
  expect(redo.ok).toBe(true);
  expect(
    redo.workflow!.blocks.find((b) => b.id === review.id)?.inputPortIds,
  ).toEqual(review.inputPortIds);
});

// Manufacturing must retain a real artifact handoff, not two disconnected tasks.
it("carries the repaired mesh into slicing and final checks while retaining the original CAD evidence", () => {
  const workflow = parseRecoverySourceDocument(source, 1).workflow!;
  const port = (key: string) =>
    workflow.ports.find((p) => p.id === `port.${key.replace(/_/g, "-")}`)!;
  const upstream = (key: string) =>
    workflow.relationships
      .filter((edge) => edge.targetId === port(key).id)
      .map((edge) =>
        workflow.ports
          .find((p) => p.id === edge.sourceId)
          ?.id.replace(/^port\./, "")
          .replace(/-/g, "_"),
      );
  expect(upstream("mesh_repair_mesh")).toEqual(["cad_mesh"]);
  expect(upstream("manufacturing_mesh")).toEqual(["mesh_repair_repaired"]);
  expect(upstream("manufacturing_repair_changes")).toEqual([
    "mesh_repair_changes",
  ]);
  expect(upstream("manufacturing_check_source")).toEqual(["cad_mesh"]);
  expect(upstream("manufacturing_check_repaired")).toEqual([
    "mesh_repair_repaired",
  ]);
  expect(upstream("manufacturing_check_changes")).toEqual([
    "manufacturing_changes",
  ]);
  expect(upstream("print_review_package")).toEqual(["manufacturing_package"]);
  expect(upstream("print_review_final_checks")).toEqual([
    "manufacturing_check_checks",
  ]);
});

it("applies removal of obsolete tool settings as a reversible edit without removing managed review data", async () => {
  const { textEditCommands, applyRecoveryBatch, recoveryCommandBatch } =
    await import("./command-system");
  const after = parseRecoverySourceDocument(source, 1).workflow!;
  const before = structuredClone(after);
  const analysis = before.blocks.find(
    (b) => b.configuration.authoring_template === "mcp-task",
  )!;
  analysis.configuration.qualification_status = "binding_required";
  analysis.configuration.requested_capability = "Strength analysis";
  const layout = hydrateAuthoringLayout(before);
  const commands = textEditCommands(before, after);
  expect(
    commands.filter(
      (c) => "kind" in c && c.kind === "remove_block_configuration",
    ),
  ).toHaveLength(2);
  const result = applyRecoveryBatch(
    before,
    layout,
    recoveryCommandBatch(
      before.revision,
      "text",
      commands as import("./command-system").RecoveryCommand[],
    ),
  );
  expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
  expect(
    result.workflow!.blocks.find((b) => b.id === analysis.id)!.configuration,
  ).toEqual(after.blocks.find((b) => b.id === analysis.id)!.configuration);
  expect(result.workflow!.relationships).toEqual(before.relationships);
  expect(analysis.configuration.qualification_status).toBe("binding_required");
  const undo = applyRecoveryBatch(
    result.workflow!,
    result.layout!,
    recoveryCommandBatch(result.workflow!.revision, "history", [
      { kind: "restore_snapshot", direction: "undo", workflow: before, layout },
    ]),
  );
  expect(undo.ok).toBe(true);
  expect(
    undo.workflow!.blocks.find((b) => b.id === analysis.id)!.configuration
      .qualification_status,
  ).toBe("binding_required");
  const review = before.blocks.find(
    (b) => b.title === "Review the proposed print package",
  )!;
  const guarded = applyRecoveryBatch(
    before,
    layout,
    recoveryCommandBatch(before.revision, "text", [
      {
        kind: "remove_block_configuration",
        blockId: review.id,
        key: "__wright_authoring_approval_objects",
      },
    ]),
  );
  expect(guarded.ok).toBe(false);
  expect(guarded.diagnostics[0].code).toBe(
    "WFR-COMMAND-CONFIGURATION-REMOVE-INVALID",
  );
});

it("applies the actual accepted handle refinement without losing review or result connections", async () => {
  const { textEditCommands, applyRecoveryBatch, recoveryCommandBatch } =
    await import("./command-system");
  const before = parseRecoverySourceDocument(acceptedHandleSource, 1).workflow!;
  const parsed = parseRecoveryAuthoringSource(source, before);
  expect(parsed.ok, JSON.stringify(parsed.diagnostics)).toBe(true);
  const layout = hydrateAuthoringLayout(before);
  const commands = textEditCommands(before, parsed.workflow!, layout);
  expect(
    commands.every((c) => "kind" in c),
    JSON.stringify(commands),
  ).toBe(true);
  const result = applyRecoveryBatch(
    before,
    layout,
    recoveryCommandBatch(
      before.revision,
      "text",
      commands as import("./command-system").RecoveryCommand[],
    ),
  );
  expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
  expect(result.workflow!.ports).toHaveLength(parsed.workflow!.ports.length);
  expect(result.workflow!.relationships).toEqual(
    parsed.workflow!.relationships,
  );
  expect(
    result.workflow!.blocks.find(
      (b) => b.title === "Review the proposed print package",
    )!.inputPortIds,
  ).toHaveLength(7);
});

it("inserts the repair step beside its inputs and preserves the engineer's saved positions", async () => {
  const { textEditCommands, applyRecoveryBatch, recoveryCommandBatch } =
    await import("./command-system");
  const before = parseRecoverySourceDocument(acceptedHandleSource, 1).workflow!;
  const after = parseRecoveryAuthoringSource(source, before).workflow!;
  const layout = hydrateAuthoringLayout(before);
  layout.positions["block.strength-check"] = { x: 2800, y: 730 };
  const savedPositions = structuredClone(layout.positions);
  const commands = textEditCommands(before, after, layout);
  const result = applyRecoveryBatch(
    before,
    layout,
    recoveryCommandBatch(
      before.revision,
      "text",
      commands as import("./command-system").RecoveryCommand[],
    ),
  );
  expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
  for (const [id, point] of Object.entries(savedPositions))
    expect(result.layout!.positions[id]).toEqual(point);
  const inserted = result.layout!.positions["block.mesh-repair"];
  expect(inserted.x).toBeGreaterThan(savedPositions["block.strength-check"].x);
  expect(inserted.y).toBeGreaterThanOrEqual(
    savedPositions["block.strength-check"].y,
  );
  const reopened = hydrateAuthoringLayout(result.workflow!, result.layout!);
  expect(reopened.positions).toEqual(result.layout!.positions);
});

it("places multiple inserted stages in dependency order even when source sections are reversed", async () => {
  const { textEditCommands } = await import("./command-system");
  const after = parseRecoverySourceDocument(source, 1).workflow!;
  after.blocks.reverse();
  const before = structuredClone(after);
  const newIds = new Set(["block.mesh-repair", "block.manufacturing"]);
  const removedPorts = new Set(
    before.ports.filter((p) => newIds.has(p.ownerBlockId)).map((p) => p.id),
  );
  before.blocks = before.blocks.filter((b) => !newIds.has(b.id));
  before.ports = before.ports.filter((p) => !removedPorts.has(p.id));
  before.relationships = before.relationships.filter(
    (e) =>
      !removedPorts.has(e.sourceId) &&
      !removedPorts.has(e.targetId) &&
      !newIds.has(e.sourceId) &&
      !newIds.has(e.targetId),
  );
  const layout = hydrateAuthoringLayout(before);
  const commands = textEditCommands(before, after, layout);
  const additions = commands.filter(
    (c) => "kind" in c && c.kind === "add_block",
  ) as Extract<
    import("./command-system").RecoveryCommand,
    { kind: "add_block" }
  >[];
  expect(additions.map((c) => c.block.id)).toEqual([
    "block.mesh-repair",
    "block.manufacturing",
  ]);
  expect(additions[1].position.x).toBeGreaterThan(additions[0].position.x);
  const hydrated = hydrateAuthoringLayout(after, layout);
  expect(hydrated.positions["block.manufacturing"].x).toBeGreaterThan(
    hydrated.positions["block.mesh-repair"].x,
  );
});

it("reserves the full height of a tall inserted step", async () => {
  const { findAuthoringPosition } = await import("./authoring-positioning");
  const workflow = parseRecoverySourceDocument(source, 1).workflow!;
  const layout = hydrateAuthoringLayout(workflow);
  layout.positions = { [workflow.blocks[0].id]: { x: 380, y: 400 } };
  const point = findAuthoringPosition(
    workflow,
    layout,
    { x: 380, y: 100 },
    380,
  );
  const overlaps =
    point.x < 672 &&
    point.x + 292 > 380 &&
    point.y < 600 &&
    point.y + 412 > 400;
  expect(overlaps).toBe(false);
});

it("declares two package inputs for comparison and retains exact final-check/report handoffs", () => {
  const workflow = parseRecoverySourceDocument(source, 1).workflow!;
  const upstream = (key: string) => {
    const target = `port.${key.replace(/_/g, "-")}`;
    return workflow.relationships
      .filter((e) => e.targetId === target)
      .map((e) => e.sourceId);
  };
  expect(upstream("orient_mesh")).toEqual(["port.mesh-repair-repaired"]);
  expect(upstream("slice_pads")).toEqual(["port.orient-pads"]);
  expect(upstream("slice_side")).toEqual(["port.orient-side"]);
  expect(upstream("manufacturing_pads_package")).toEqual([
    "port.slice-pads-package",
  ]);
  expect(upstream("manufacturing_side_package")).toEqual([
    "port.slice-side-package",
  ]);
  expect(upstream("manufacturing_slice_responses")).toEqual([
    "port.slice-responses",
  ]);
  expect(upstream("manufacturing_check_package")).toEqual([
    "port.manufacturing-package",
  ]);
  expect(upstream("manufacturing_check_orientations")).toEqual([
    "port.orient-record",
  ]);
  expect(upstream("report_selection")).toEqual(["port.manufacturing-changes"]);
  expect(upstream("report_slice_responses")).toEqual(["port.slice-responses"]);
  const formatted = formatRecoveryAuthoringSource(workflow).text;
  const sliceSection = formatted.match(
    /task slice_orientations\n([\s\S]*?)\nend/,
  )![1];
  const settings = JSON.parse(sliceSection.match(/^  settings: (.*)$/m)![1]);
  expect(settings.mcp_task_tools).toEqual(["slice_model_file"]);
  const outputs = settings.expected_file_ports as Record<string, string>;
  expect(new Set(Object.values(outputs)).size).toBe(2);
  expect(
    Object.values(outputs).every((p) =>
      p.includes("{{wright.producer_attempt}}"),
    ),
  ).toBe(true);
  expect(upstream("print_review_final_checks")).toEqual([
    "port.manufacturing-check-checks",
  ]);
  expect(
    workflow.blocks.find((b) => b.id === "block.print-review")!.inputPortIds,
  ).toHaveLength(7);
});

it("preserves runtime hash checks for each connected binary input in bound engineering stages", () => {
  const workflow = parseRecoverySourceDocument(source, 1).workflow!;
  const formatted = formatRecoveryAuthoringSource(workflow).text;
  for (const id of [
    "analysis",
    "mesh_repair",
    "print_orientations",
    "slice_orientations",
  ]) {
    const section = formatted.match(
      new RegExp(`task ${id}\\n([\\s\\S]*?)\\nend`),
    )![1];
    const inputs = JSON.parse(section.match(/^  inputs: (.*)$/m)![1]) as {
      key: string;
      kind: string;
    }[];
    const settings = JSON.parse(section.match(/^  settings: (.*)$/m)![1]);
    const binary = inputs.filter((p) => p.kind === "workspace_file");
    expect(binary.length).toBeGreaterThan(0);
    expect(settings.mcp_file_dependencies).toEqual(
      Object.fromEntries(
        binary.map((p) => [p.key, { source: "connected_output" }]),
      ),
    );
  }
});
