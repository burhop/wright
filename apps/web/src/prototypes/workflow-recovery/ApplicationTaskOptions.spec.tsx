import { expect, it, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import {
  ApplicationTaskOptions,
  applicationCommands,
  configureApplicationExport,
  type ApplicationOptions,
} from "./ApplicationTaskOptions";
import type { RecoveryCommand } from "./command-system";
import { createAuthoringObject } from "./authoring-objects";
import { initialWorkflow, initialLayout } from "./model";
import {
  applyRecoveryBatch,
  recoveryCommandBatch,
  acceptRecoveryResult,
} from "./command-system";
import {
  validateRecoveryAuthoringRoundTrip,
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
  const block = created.workflow.blocks.find((b) => b.id === add.block.id)!;
  return { ...created, block };
}
it.each([true, false])(
  "explains whether exports are workspace files (%s)",
  async (workspace) => {
    const { workflow, block } = fixture();
    const settings: ApplicationOptions = {
      source: "new",
      kind: "analysis",
      edit_mode: "modify",
      exports: [
        {
          id: "report",
          format: "markdown",
          name: "reports/analysis.md",
          policy: "indexed",
        },
      ],
    };
    const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          supported: true,
          name: "Analysis fixture",
          kind: "analysis",
          can_create: true,
          can_copy: false,
          formats: ["markdown"],
          export_policies: ["indexed", "overwrite"],
          exports_to_workspace: workspace,
          resources: [],
        }),
      ),
    );
    try {
      render(
        <ApplicationTaskOptions
          block={{
            ...block,
            configuration: {
              ...block.configuration,
              mcp_server: "analysis",
              application_resource: JSON.stringify(settings),
            },
          }}
          workflow={workflow}
          sessionId="session"
          readOnly={false}
          onApply={() => true}
        />,
      );
      await screen.findByText("Work with Analysis fixture");
      expect(
        screen.getByLabelText(workspace ? "File name or path" : "Export name"),
      ).toHaveValue("reports/analysis.md");
      expect(Boolean(screen.queryByText(/Saved in this workspace/))).toBe(
        workspace,
      );
      expect(
        screen.queryByText("export_path_argument"),
      ).not.toBeInTheDocument();
    } finally {
      fetch.mockRestore();
    }
  },
);
it("preserves cloud resource identity and named exports through workspace source roundtrip", () => {
  const { workflow, layout, block } = fixture();
  const settings: ApplicationOptions = {
    source: "resource",
    kind: "cad_model",
    resource_id: "model-1",
    revision: "revision-3",
    edit_mode: "copy",
    exports: [{ id: "step", format: "step", name: "bracket.step" }],
  };
  const result = applyRecoveryBatch(
    workflow,
    layout,
    recoveryCommandBatch(
      workflow.revision,
      "form",
      applicationCommands(block, workflow, settings),
    ),
  );
  expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
  const accepted = acceptRecoveryResult(workflow, layout, result)!;
  expect(validateRecoveryAuthoringRoundTrip(accepted.workflow).ok).toBe(true);
  const parsed = parseRecoveryAuthoringSource(
    formatRecoveryAuthoringSource(accepted.workflow).text,
    initialWorkflow,
  );
  expect(parsed.ok).toBe(true);
  expect(
    JSON.parse(
      String(
        parsed.workflow!.blocks.find((b) => b.id === block.id)!.configuration
          .application_resource,
      ),
    ),
  ).toMatchObject(settings);
  expect(accepted.layout.positions[block.id]).toEqual(
    layout.positions[block.id],
  );
});
it("shows provider resource names and pins the chosen revision without exposing argument names", async () => {
  const { workflow, block } = fixture();
  const settings: ApplicationOptions = {
    source: "resource",
    kind: "cad_model",
    edit_mode: "modify",
    exports: [],
  };
  const apply = vi.fn((_commands: RecoveryCommand[]) => true);
  const fetch = vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(
      JSON.stringify({
        supported: true,
        name: "Cloud fixture",
        kind: "cad_model",
        can_create: true,
        can_copy: true,
        formats: ["step"],
        resources: [
          {
            resource_id: "m1",
            name: "Bracket",
            revision: "r3",
            durability: "persistent",
          },
        ],
      }),
    ),
  );
  try {
    render(
      <ApplicationTaskOptions
        block={{
          ...block,
          configuration: {
            ...block.configuration,
            mcp_server: "cloud",
            application_resource: JSON.stringify(settings),
          },
        }}
        workflow={workflow}
        sessionId="session"
        readOnly={false}
        onApply={apply}
      />,
    );
    await waitFor(() =>
      expect(
        screen.getByRole("option", { name: "Bracket · r3" }),
      ).toBeInTheDocument(),
    );
    fireEvent.change(
      screen.getByTestId("workflow-recovery-application-resource"),
      { target: { value: "m1" } },
    );
    expect(apply.mock.calls[0][0]).toContainEqual(
      expect.objectContaining({
        key: "application_resource",
        value: expect.stringContaining('"revision":"r3"'),
      }),
    );
    expect(screen.queryByText("resource_id")).not.toBeInTheDocument();
  } finally {
    fetch.mockRestore();
  }
});

it("configures a named export and matching file connection atomically without moving existing blocks", () => {
  let { workflow, layout, block: producer } = fixture();
  const add = createAuthoringObject("mcp-task", workflow, layout);
  let accepted = acceptRecoveryResult(
    workflow,
    layout,
    applyRecoveryBatch(
      workflow,
      layout,
      recoveryCommandBatch(workflow.revision, "form", [add]),
    ),
  )!;
  workflow = accepted.workflow;
  layout = accepted.layout;
  let consumer = workflow.blocks.find((b) => b.id === add.block.id)!;
  const base: ApplicationOptions = {
    source: "new",
    kind: "cad_model",
    edit_mode: "modify",
    exports: [],
  };
  accepted = acceptRecoveryResult(
    workflow,
    layout,
    applyRecoveryBatch(
      workflow,
      layout,
      recoveryCommandBatch(workflow.revision, "form", [
        ...applicationCommands(producer, workflow, base),
        ...applicationCommands(consumer, workflow, {
          ...base,
          source: "upstream",
        }),
      ]),
    ),
  )!;
  workflow = accepted.workflow;
  layout = accepted.layout;
  producer = workflow.blocks.find((b) => b.id === producer.id)!;
  consumer = workflow.blocks.find((b) => b.id === consumer.id)!;
  const result = applyRecoveryBatch(
    workflow,
    layout,
    recoveryCommandBatch(
      workflow.revision,
      "form",
      configureApplicationExport(producer, consumer, workflow, "step"),
    ),
  );
  expect(result.ok, JSON.stringify(result.diagnostics)).toBe(true);
  accepted = acceptRecoveryResult(workflow, layout, result)!;
  const producerOptions = JSON.parse(
    String(
      accepted.workflow.blocks.find((b) => b.id === producer.id)!.configuration
        .application_resource,
    ),
  );
  expect(producerOptions.exports).toHaveLength(1);
  expect(producerOptions.exports[0]).toMatchObject({
    format: "step",
    policy: "indexed",
  });
  const edge = accepted.workflow.relationships.find(
    (e) => e.id === `rel.${consumer.id.slice(6)}-application-resource`,
  )!;
  expect(
    accepted.workflow.ports.find((p) => p.id === edge.targetId)?.typeId,
  ).toBe("type.file.workspace");
  expect(accepted.layout.positions).toEqual(layout.positions);
  expect(validateRecoveryAuthoringRoundTrip(accepted.workflow).ok).toBe(true);
});
