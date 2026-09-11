import { useState } from "react";
import { afterEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  within,
} from "@testing-library/react";
import { initialWorkflow, initialLayout, type RecoveryWorkflow } from "./model";
import {
  applyRecoveryBatch,
  recoveryCommandBatch,
  acceptRecoveryResult,
  textEditCommands,
  type RecoveryCommand,
} from "./command-system";
import { createAuthoringObject } from "./authoring-objects";
import {
  CadTaskOptions,
  cadCommands,
  cadPortId,
  type CadOptions,
} from "./CadTaskOptions";
import {
  applicationCommands,
  applicationPortId,
  type ApplicationOptions,
} from "./ApplicationTaskOptions";
import { connectReferenceCommands } from "./prompt-settings";
import { exportFilename } from "./output-contracts";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
} from "./recovery-authoring";

function fixture(application = false) {
  let state = {
    workflow: structuredClone(initialWorkflow),
    layout: structuredClone(initialLayout),
  };
  const apply = (commands: RecoveryCommand[]) => {
    const result = applyRecoveryBatch(
      state.workflow,
      state.layout,
      recoveryCommandBatch(state.workflow.revision, "form", commands),
    );
    expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
    state = acceptRecoveryResult(state.workflow, state.layout, result)!;
  };
  const producer = createAuthoringObject(
    "mcp-task",
    state.workflow,
    state.layout,
  );
  producer.block.title = "Create model";
  producer.block.configuration.mcp_server = "cad-server";
  apply([producer]);
  const cad: CadOptions = {
    source: "new",
    edit_mode: "in_place",
    copy_path: "copy.par",
    save_native: true,
    native_path: "model.par",
    policy: "indexed",
    exports: [
      { id: "neutral", format: "step", path: "model.step", policy: "indexed" },
    ],
  };
  const app: ApplicationOptions = {
    source: "new",
    kind: "cad_model",
    edit_mode: "modify",
    exports: [
      { id: "neutral", format: "step", name: "model.step", policy: "indexed" },
    ],
  };
  apply(
    application
      ? applicationCommands(producer.block, state.workflow, app)
      : cadCommands(producer.block, state.workflow, cad),
  );
  const consumer = createAuthoringObject(
    "ai-prompt",
    state.workflow,
    state.layout,
  );
  consumer.block.title = "Review model";
  apply([consumer]);
  const portId = (application ? applicationPortId : cadPortId)(
    producer.block,
    "neutral",
  );
  apply(connectReferenceCommands(consumer.block, state.workflow, portId));
  const block = state.workflow.blocks.find(
    (block) => block.id === producer.block.id,
  )!;
  return { ...state, block, cad, app, portId };
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

it.each([false, true])(
  "protects connected local/cloud exports from format changes through forms and source (cloud=%s)",
  (application) => {
    const { workflow, layout, block, cad, app } = fixture(application);
    const commands = application
      ? applicationCommands(block, workflow, {
          ...app,
          exports: [{ ...app.exports[0]!, format: "dxf", name: "model.dxf" }],
        })
      : cadCommands(block, workflow, {
          ...cad,
          exports: [{ ...cad.exports[0]!, format: "dxf", path: "model.dxf" }],
        });
    const result = applyRecoveryBatch(
      workflow,
      layout,
      recoveryCommandBatch(workflow.revision, "form", commands),
    );
    expect(result.ok).toBe(false);
    expect(result.diagnostics[0]).toMatchObject({
      code: "WFR-CONNECTED-OUTPUT-CHANGE",
      explanation: expect.stringContaining("STEP is used by Review model"),
    });
    const changed = structuredClone(workflow);
    const config = commands.at(-1)!;
    if (config.kind !== "set_block_configuration")
      throw new Error("Missing output settings");
    changed.blocks.find((item) => item.id === block.id)!.configuration[
      config.key
    ] = config.value;
    const parsed = parseRecoveryAuthoringSource(
      formatRecoveryAuthoringSource(changed).text,
      workflow,
    );
    expect(parsed.ok).toBe(true);
    const sourceEdit = applyRecoveryBatch(
      workflow,
      layout,
      recoveryCommandBatch(
        workflow.revision,
        "text",
        textEditCommands(
          workflow,
          parsed.workflow!,
          layout,
        ) as RecoveryCommand[],
      ),
    );
    expect(sourceEdit.ok).toBe(false);
    expect(sourceEdit.diagnostics[0]!.code).toBe("WFR-CONNECTED-OUTPUT-CHANGE");
  },
);

it("blocks removal without silently dropping consumers, and allows adding DXF or editing the prompt", () => {
  const { workflow, layout, block, cad, portId } = fixture();
  const removed = applyRecoveryBatch(
    workflow,
    layout,
    recoveryCommandBatch(
      workflow.revision,
      "form",
      cadCommands(block, workflow, { ...cad, exports: [] }),
    ),
  );
  expect(removed.ok).toBe(false);
  expect(workflow.relationships.some((edge) => edge.sourceId === portId)).toBe(
    true,
  );
  const added = applyRecoveryBatch(
    workflow,
    layout,
    recoveryCommandBatch(workflow.revision, "form", [
      ...cadCommands(block, workflow, {
        ...cad,
        exports: [
          ...cad.exports,
          {
            id: "flat",
            format: "flat_dxf",
            path: "model.dxf",
            policy: "indexed",
          },
        ],
      }),
      {
        kind: "set_block_definition",
        blockId: block.id,
        patch: { instructions: "Export a DXF of the design." },
      },
    ]),
  );
  expect(added.ok).toBe(true);
  expect(added.workflow!.relationships).toEqual(workflow.relationships);
  expect(
    JSON.parse(
      String(
        added.workflow!.blocks.find((b) => b.id === block.id)!.configuration
          .cad,
      ),
    ).exports.map((e: { format: string }) => e.format),
  ).toEqual(["step", "flat_dxf"]);
});

it("permits an intentional disconnect followed by a format change", () => {
  const { workflow, layout, block, cad, portId } = fixture();
  const disconnect = applyRecoveryBatch(
    workflow,
    layout,
    recoveryCommandBatch(
      workflow.revision,
      "form",
      workflow.relationships
        .filter((e) => e.sourceId === portId)
        .map((e) => ({ kind: "disconnect", relationshipId: e.id })),
    ),
  );
  const disconnected = acceptRecoveryResult(workflow, layout, disconnect)!;
  const changed = applyRecoveryBatch(
    disconnected.workflow,
    disconnected.layout,
    recoveryCommandBatch(
      disconnected.workflow.revision,
      "form",
      cadCommands(block, disconnected.workflow, {
        ...cad,
        exports: [{ ...cad.exports[0]!, format: "dxf" }],
      }),
    ),
  );
  expect(changed.ok).toBe(true);
  expect(exportFilename("exports/bracket.v2.step", "flat_dxf")).toBe(
    "exports/bracket.v2.dxf",
  );
});

it("preserves a legacy named model and export when adding another format", () => {
  const { workflow, layout, block, cad, portId } = fixture();
  // Earlier saved workflows have explicit port names and no generated export id.
  const model = workflow.ports.find(
    (port) =>
      port.ownerBlockId === block.id && port.typeId === "type.geometry.brep",
  )!;
  block.outputPortIds = block.outputPortIds.map((id) =>
    id === model.id ? "port.model" : id === portId ? "port.preview" : id,
  );
  model.id = "port.model";
  workflow.ports.find((port) => port.id === portId)!.id = "port.preview";
  workflow.relationships
    .filter((edge) => edge.sourceId === portId)
    .forEach((edge) => {
      edge.sourceId = "port.preview";
    });
  const legacy = {
    ...cad,
    exports: [
      {
        format: "step",
        path: "model.step",
        port: "preview",
        policy: "indexed",
      },
    ],
  };
  block.configuration.cad = JSON.stringify(legacy);
  const result = applyRecoveryBatch(
    workflow,
    layout,
    recoveryCommandBatch(
      workflow.revision,
      "form",
      cadCommands(block, workflow, {
        ...cad,
        exports: [
          legacy.exports[0] as CadOptions["exports"][number],
          { id: "new", format: "dxf", path: "model.dxf", policy: "indexed" },
        ],
      }),
    ),
  );
  expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
  expect(result.workflow!.relationships).toEqual(workflow.relationships);
  expect(
    result.workflow!.ports.filter(
      (port) =>
        port.ownerBlockId === block.id && port.typeId === "type.geometry.brep",
    ),
  ).toHaveLength(1);
  const exports = JSON.parse(
    String(
      result.workflow!.blocks.find((b) => b.id === block.id)!.configuration.cad,
    ),
  ).exports;
  expect(exports.map((ex: { port: string }) => ex.port)).toEqual([
    "preview",
    `${block.id.slice(6).replaceAll("-", "_")}_cad_new`,
  ]);
});

it("offers an additive repair without changing the existing connection", async () => {
  const original = fixture();
  let latest: RecoveryWorkflow = original.workflow;
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            supported: true,
            formats: ["step", "dxf"],
            can_create: true,
            can_save: true,
          }),
        ),
    ),
  );
  function Editor() {
    const [state, setState] = useState({
      workflow: original.workflow,
      layout: original.layout,
    });
    return (
      <CadTaskOptions
        block={state.workflow.blocks.find((b) => b.id === original.block.id)!}
        workflow={state.workflow}
        sessionId="session"
        readOnly={false}
        onApply={(commands) => {
          const result = applyRecoveryBatch(
            state.workflow,
            state.layout,
            recoveryCommandBatch(state.workflow.revision, "form", commands),
          );
          if (!result.ok) return false;
          const accepted = acceptRecoveryResult(
            state.workflow,
            state.layout,
            result,
          )!;
          latest = accepted.workflow;
          setState(accepted);
          return true;
        }}
      />
    );
  }
  render(<Editor />);
  const select = screen.getByTestId("workflow-recovery-cad-export-format-0");
  await within(select).findByRole("option", { name: "dxf" });
  fireEvent.change(select, { target: { value: "dxf" } });
  expect(screen.getByRole("alert")).toHaveTextContent("Review model uses STEP");
  expect(latest).toBe(original.workflow);
  fireEvent.click(
    screen.getByRole("button", { name: "Add DXF and keep STEP" }),
  );
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  expect(
    screen.getByTestId("workflow-recovery-cad-export-format-0"),
  ).toHaveValue("step");
  expect(
    screen.getByTestId("workflow-recovery-cad-export-format-1"),
  ).toHaveValue("dxf");
  expect(latest.relationships).toEqual(original.workflow.relationships);
  expect(
    screen.getByRole("button", { name: "Remove export 1" }),
  ).toBeDisabled();
});
