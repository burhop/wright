import { expect, it } from "vitest";
import { createAuthoringObject } from "./authoring-objects";
import {
  applyRecoveryBatch,
  acceptRecoveryResult,
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
  connectPromptCommands,
  connectReferenceCommands,
  promptConfigurationLabel,
  promptSourceCandidates,
  sourceKey,
} from "./prompt-settings";
import { cadCommands, type CadOptions } from "./CadTaskOptions";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
} from "./recovery-authoring";

function apply(
  workflow: RecoveryWorkflow,
  layout: RecoveryLayout,
  commands: RecoveryCommand[],
) {
  const result = applyRecoveryBatch(
    workflow,
    layout,
    recoveryCommandBatch(workflow.revision, "graph", commands),
  );
  expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
  return acceptRecoveryResult(workflow, layout, result)!;
}
it("labels a native AI prompt from its actual inline or connected prompt, without requiring a tool binding", () => {
  const input = createAuthoringObject(
    "text-input",
    initialWorkflow,
    initialLayout,
  );
  let state = apply(initialWorkflow, initialLayout, [input]);
  const task = createAuthoringObject("ai-prompt", state.workflow, state.layout);
  state = apply(state.workflow, state.layout, [task]);
  const block = () =>
    state.workflow.blocks.find((item) => item.id === task.block.id)!;
  expect(block().bindingId).toBeNull();
  expect(
    promptConfigurationLabel({ ...block(), instructions: "" }, state.workflow),
  ).toBe("Prompt not configured");
  expect(
    promptConfigurationLabel(
      { ...block(), instructions: "Calculate plate mass." },
      state.workflow,
    ),
  ).toBe("Configured AI prompt");
  state = apply(
    state.workflow,
    state.layout,
    connectPromptCommands(block(), state.workflow, input.ports[0]!.id),
  );
  expect(promptConfigurationLabel(block(), state.workflow)).toBe(
    "Configured AI prompt",
  );
  state = apply(
    state.workflow,
    state.layout,
    connectPromptCommands(block(), state.workflow, ""),
  );
  expect(
    promptConfigurationLabel(
      { ...block(), instructions: "Retained inline text" },
      state.workflow,
    ),
  ).toBe("Prompt not configured");
});
it.each(["mcp-task", "ai-prompt"])(
  "%s starts with visible optional prompt and image sockets and reuses the prompt address",
  (template) => {
    const input = createAuthoringObject(
      "text-input",
      initialWorkflow,
      initialLayout,
    );
    let state = apply(initialWorkflow, initialLayout, [input]);
    const add = createAuthoringObject(template, state.workflow, state.layout);
    expect(
      add.ports
        .filter((port) => port.direction === "input")
        .map((port) => port.name),
    ).toEqual(["Prompt", "Reference image"]);
    state = apply(state.workflow, state.layout, [add]);
    const port = add.ports.find((port) => port.name === "Prompt")!;
    expect(port.required).toBe(false);
    state = apply(
      state.workflow,
      state.layout,
      connectPromptCommands(add.block, state.workflow, input.ports[0]!.id),
    );
    expect(
      state.workflow.ports.find((item) => item.id === port.id)?.typeId,
    ).toBe("type.value.text");
    expect(
      state.workflow.ports.filter(
        (item) => item.ownerBlockId === add.block.id && item.name === "Prompt",
      ),
    ).toHaveLength(1);
    expect(
      state.workflow.blocks.find((item) => item.id === add.block.id)
        ?.configuration.prompt_input,
    ).toBe(sourceKey(port.id));
    const reopened = parseRecoveryAuthoringSource(
      formatRecoveryAuthoringSource(state.workflow).text,
      initialWorkflow,
    );
    expect(reopened.ok).toBe(true);
    expect(
      reopened.workflow!.relationships.some(
        (edge) =>
          edge.sourceId === input.ports[0]!.id && edge.targetId === port.id,
      ),
    ).toBe(true);
  },
);
it("connects a named CAD screenshot as image reference, keeping instructions separate", () => {
  const cad = createAuthoringObject("mcp-task", initialWorkflow, initialLayout);
  let state = apply(initialWorkflow, initialLayout, [cad]);
  const config: CadOptions = {
    source: "new",
    edit_mode: "in_place",
    copy_path: "copy.par",
    save_native: true,
    native_path: "part.par",
    policy: "indexed",
    exports: [
      {
        id: "view",
        format: "screenshot_jpeg",
        path: "part.jpg",
        policy: "indexed",
      },
    ],
  };
  state = apply(
    state.workflow,
    state.layout,
    cadCommands(cad.block, state.workflow, config),
  );
  const consumer = createAuthoringObject(
    "ai-prompt",
    state.workflow,
    state.layout,
  );
  state = apply(state.workflow, state.layout, [consumer]);
  const screenshot = state.workflow.ports.find(
    (port) => port.id === "port.mcp-task-1-cad-view",
  )!;
  const imageInput = consumer.ports.find(
    (port) => port.name === "Reference image",
  )!;
  expect(
    promptSourceCandidates(consumer.block, state.workflow).map(
      (port) => port.id,
    ),
  ).not.toContain(screenshot.id);
  expect(
    promptSourceCandidates(consumer.block, state.workflow, true).map(
      (port) => port.id,
    ),
  ).toContain(screenshot.id);
  state = apply(
    state.workflow,
    state.layout,
    connectReferenceCommands(
      consumer.block,
      state.workflow,
      screenshot.id,
      imageInput.id,
    ),
  );
  expect(
    state.workflow.relationships.some(
      (edge) =>
        edge.sourceId === screenshot.id && edge.targetId === imageInput.id,
    ),
  ).toBe(true);
  expect(
    state.workflow.blocks.find((block) => block.id === consumer.block.id)
      ?.configuration.prompt_source,
  ).toBe("inline");
  expect(() =>
    connectPromptCommands(consumer.block, state.workflow, screenshot.id),
  ).toThrow("compatible upstream response");
});
it("permits an uploaded image reference for an MCP task and rejects cycle candidates", () => {
  const image = createAuthoringObject(
    "image-input",
    initialWorkflow,
    initialLayout,
  );
  let state = apply(initialWorkflow, initialLayout, [image]);
  const task = createAuthoringObject("mcp-task", state.workflow, state.layout);
  state = apply(state.workflow, state.layout, [task]);
  const target = task.ports.find((port) => port.name === "Reference image")!;
  state = apply(
    state.workflow,
    state.layout,
    connectReferenceCommands(
      task.block,
      state.workflow,
      image.ports[0]!.id,
      target.id,
    ),
  );
  expect(
    state.workflow.ports.find((port) => port.id === target.id)?.typeId,
  ).toBe("type.image.reference-set");
  expect(
    promptSourceCandidates(image.block, state.workflow, true).map(
      (port) => port.ownerBlockId,
    ),
  ).not.toContain(task.block.id);
});
