import { UnboundTaskSetup } from "./UnboundTaskSetup";
import { afterEach, expect, it, vi } from "vitest";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { WorkflowRecoveryConcept as Editor } from "./WorkflowRecoveryConcept";
import { WorkflowToolDiscovery } from "./workflow-tool-discovery";
import { parseRecoverySourceDocument } from "./recovery-authoring";
import source from "../../../../../prototypes/desktop-harness/engineering-experience/handle/replacement-handle-draft.workflow.wflow?raw";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
it("assigns a server explicitly, undoes/redoes and saves without replacing the step connections", async () => {
  vi.stubGlobal(
    "ResizeObserver",
    class {
      observe = vi.fn();
      unobserve = vi.fn();
      disconnect = vi.fn();
    },
  );
  const read = vi.fn(async () => [
    {
      name: "cad.inspect",
      server_id: "cad",
      server_name: "Study CAD",
      workspace_server: true,
      tool_name: "inspect",
      title: "Inspect",
      description: "",
      input_schema: {},
      schema_digest: "a".repeat(64),
    },
  ]);
  const save = vi.fn(async (text: string) => ({
    source: text,
    definition_revision: 2,
    storage_digest: "b".repeat(64),
  }));
  render(
    <WorkflowToolDiscovery.Provider value={{ read, sessionId: "session" }}>
      <Editor
        workflowSource={source}
        definitionRevision={1}
        storageDigest={"a".repeat(64)}
        simulationPreview={false}
        onSave={save}
      />
    </WorkflowToolDiscovery.Provider>,
  );
  fireEvent.click(screen.getByTestId("workflow-recovery-block-block.cad"));
  const select = await screen.findByLabelText("Engineering server");
  await screen.findByRole("option", { name: "Study CAD" });
  expect(save).not.toHaveBeenCalled();
  fireEvent.change(select, { target: { value: "cad" } });
  fireEvent.click(
    screen.getByRole("button", { name: "Use AI with this server" }),
  );
  await waitFor(() =>
    expect(screen.queryByLabelText("Engineering server")).toBeNull(),
  );
  fireEvent.click(screen.getByTestId("workflow-recovery-undo"));
  await screen.findByLabelText("Engineering server");
  fireEvent.click(screen.getByTestId("workflow-recovery-redo"));
  await waitFor(() =>
    expect(screen.queryByLabelText("Engineering server")).toBeNull(),
  );
  fireEvent.change(screen.getByLabelText("Handle STEP"), {
    target: { value: "results/handle.step" },
  });
  fireEvent.change(screen.getByLabelText("Source mesh"), {
    target: { value: "results/handle.stl" },
  });
  fireEvent.change(screen.getByLabelText("Handle preview"), {
    target: { value: "results/preview.png" },
  });
  fireEvent.click(screen.getByTestId("workflow-recovery-undo"));
  expect(screen.getByLabelText("Handle preview")).toHaveValue("");
  fireEvent.click(screen.getByTestId("workflow-recovery-redo"));
  expect(screen.getByLabelText("Handle preview")).toHaveValue(
    "results/preview.png",
  );
  fireEvent.click(screen.getByTestId("workflow-recovery-save"));
  await waitFor(() => expect(save).toHaveBeenCalledTimes(1));
  const before = parseRecoverySourceDocument(source, 1).workflow!;
  const after = parseRecoverySourceDocument(
    save.mock.calls[0]![0],
    2,
  ).workflow!;
  const cad = after.blocks.find((b) => b.id === "block.cad")!;
  expect(JSON.parse(String(cad.configuration.expected_file_ports))).toEqual({
    cad_geometry: "results/handle.step",
    cad_mesh: "results/handle.stl",
    cad_preview: "results/preview.png",
  });
  expect(cad.instructions).toBe(
    before.blocks.find((b) => b.id === "block.cad")!.instructions,
  );
  expect(after.ports).toEqual(before.ports);
  expect(after.relationships).toEqual(before.relationships);
  expect(after.blocks.find((b) => b.id === "block.cad")).toMatchObject({
    executionKind: "ai_capable",
    configuration: { mcp_server: "cad", authoring_template: "mcp-task" },
  });
});

it("lets an engineer open Connections and refresh an unavailable server without applying a binding", async () => {
  const parsed = parseRecoverySourceDocument(source, 1);
  if (!parsed.ok || !parsed.workflow) throw new Error("Invalid fixture");
  const block = parsed.workflow.blocks.find((b) => b.id === "block.cad")!;
  const read = vi
    .fn()
    .mockRejectedValueOnce(new Error("Disconnected"))
    .mockResolvedValueOnce([
      {
        name: "cad.inspect",
        server_id: "cad",
        server_name: "Study CAD",
        workspace_server: true,
        tool_name: "inspect",
        title: "Inspect",
        description: "",
        input_schema: {},
        schema_digest: "a".repeat(64),
      },
    ]);
  const openConnections = vi.fn();
  const apply = vi.fn();
  render(
    <WorkflowToolDiscovery.Provider
      value={{ read, sessionId: "session", openConnections }}
    >
      <UnboundTaskSetup block={block} readOnly={false} onApply={apply} />
    </WorkflowToolDiscovery.Provider>,
  );
  await screen.findByText(/Workspace servers could not be read/);
  expect(screen.getByLabelText("Engineering server")).toBeDisabled();
  fireEvent.click(screen.getByRole("button", { name: "Open Connections" }));
  expect(openConnections).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole("button", { name: "Refresh servers" }));
  await screen.findByRole("option", { name: "Study CAD" });
  expect(screen.getByLabelText("Engineering server")).toBeEnabled();
  expect(
    screen.getByRole("button", { name: "Use AI with this server" }),
  ).toBeDisabled();
  expect(apply).not.toHaveBeenCalled();
  expect(read).toHaveBeenCalledTimes(2);
});
