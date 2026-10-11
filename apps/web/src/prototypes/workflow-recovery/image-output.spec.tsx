import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { createAuthoringObject } from "./authoring-objects";
import { imageOutputCommands, imageOutput } from "./image-output";
import { initialWorkflow, initialLayout } from "./model";
import {
  applyRecoveryBatch,
  acceptRecoveryResult,
  recoveryCommandBatch,
  type RecoveryCommand,
} from "./command-system";
import {
  formatRecoveryAuthoringSource,
  parseRecoveryAuthoringSource,
} from "./recovery-authoring";
import { PromptBlockEditor } from "./PromptBlockEditor";

function fixture() {
  const add = createAuthoringObject(
    "ai-prompt",
    initialWorkflow,
    initialLayout,
  );
  const state = acceptRecoveryResult(
    initialWorkflow,
    initialLayout,
    applyRecoveryBatch(
      initialWorkflow,
      initialLayout,
      recoveryCommandBatch(initialWorkflow.revision, "form", [add]),
    ),
  )!;
  return {
    ...state,
    block: state.workflow.blocks.find((block) => block.id === add.block.id)!,
  };
}
afterEach(() => vi.unstubAllGlobals());
it("declares a native AI image file and preserves it through source reopen", () => {
  const { workflow, layout, block } = fixture();
  const commands = imageOutputCommands(block, workflow, {
    format: "png",
    path: "render.png",
    port: "",
  });
  const result = applyRecoveryBatch(
    workflow,
    layout,
    recoveryCommandBatch(workflow.revision, "form", commands),
  );
  expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
  const accepted = acceptRecoveryResult(workflow, layout, result)!;
  const parsed = parseRecoveryAuthoringSource(
    formatRecoveryAuthoringSource(accepted.workflow).text,
    initialWorkflow,
  );
  expect(parsed.ok).toBe(true);
  const image = parsed.workflow!.blocks.find((item) => item.id === block.id)!;
  expect(image.configuration.authoring_template).toBe("ai-prompt");
  expect(image.configuration.output_format).toBe("text"); // Activity summary, not encoded image data.
  expect(image.configuration.mcp_server).toBeUndefined(); // No provider is guessed.
  expect(image.configuration.expected_files).toBe(
    "outputs/{{wright.run_id}}/ai_prompt_1/render.png",
  );
  expect(image.configuration.run_path_template).toBe("wright.run-path/1");
  expect(imageOutput(image)).toEqual({
    format: "png",
    path: "render.png",
    port: "ai_prompt_1_document_out",
  });
  expect(
    parsed.workflow!.ports.find((port) => port.id === image.outputPortIds[0])
      ?.typeId,
  ).toBe("type.file.workspace");
});
it("protects a connected response from being replaced with an image", () => {
  const { workflow, block } = fixture();
  workflow.relationships.push({
    id: "rel.downstream",
    kind: "data",
    sourceId: block.outputPortIds[0]!,
    targetId: "port.design-intent-in",
    label: "Prompt",
    condition: null,
  });
  expect(() =>
    imageOutputCommands(block, workflow, {
      format: "jpeg",
      path: "render.jpg",
      port: "",
    }),
  ).toThrow("Disconnect");
  expect(imageOutput(block)).toBeNull();
});
it("adds an image socket when explicitly configuring an older AI block", () => {
  const { workflow, layout, block } = fixture();
  workflow.ports = workflow.ports.filter(
    (port) => port.ownerBlockId !== block.id || port.name !== "Reference image",
  );
  block.inputPortIds = block.inputPortIds.filter((id) =>
    workflow.ports.some((port) => port.id === id),
  );
  const result = applyRecoveryBatch(
    workflow,
    layout,
    recoveryCommandBatch(
      workflow.revision,
      "form",
      imageOutputCommands(block, workflow, {
        format: "png",
        path: "render.png",
        port: "",
      }),
    ),
  );
  expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
  const accepted = acceptRecoveryResult(workflow, layout, result)!;
  expect(
    accepted.workflow.ports.some(
      (port) =>
        port.ownerBlockId === block.id && port.name === "Reference image",
    ),
  ).toBe(true);
  expect(
    workflow.ports.some(
      (port) =>
        port.ownerBlockId === block.id && port.name === "Reference image",
    ),
  ).toBe(false);
});
it("offers native image results without requiring another MCP provider", async () => {
  const { workflow, layout, block } = fixture();
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(JSON.stringify({ tools: [], servers: [] }))),
  );
  const apply = vi.fn((_commands: RecoveryCommand[]) => true);
  const { rerender } = render(
    <PromptBlockEditor
      block={block}
      workflow={workflow}
      readOnly={false}
      onApply={apply}
    />,
  );
  fireEvent.change(screen.getByTestId("workflow-recovery-response-format"), {
    target: { value: "image-jpeg" },
  });
  const result = applyRecoveryBatch(
    workflow,
    layout,
    recoveryCommandBatch(workflow.revision, "form", apply.mock.calls[0]![0]),
  );
  expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
  const next = acceptRecoveryResult(workflow, layout, result)!;
  rerender(
    <PromptBlockEditor
      block={next.workflow.blocks.find((item) => item.id === block.id)!}
      workflow={next.workflow}
      readOnly={false}
      onApply={apply}
    />,
  );
  expect(
    await screen.findByText(
      "Wright sends the prompt and reference images to your configured AI connection, then saves and displays the returned image.",
    ),
  ).toBeInTheDocument();
  expect(
    screen.queryByTestId("workflow-recovery-task-server"),
  ).not.toBeInTheDocument();
  expect(screen.getByTestId("workflow-recovery-image-output-path")).toHaveValue(
    "render.jpg",
  );
  expect(
    screen.queryByTestId("workflow-recovery-save-response"),
  ).not.toBeInTheDocument();
});
