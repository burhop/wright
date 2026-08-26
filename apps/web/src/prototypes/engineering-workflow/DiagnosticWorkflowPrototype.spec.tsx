import { act, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { EngineeringWorkflowVisualSlice } from "./EngineeringWorkflowVisualSlice";
import {
  diagnosticScenario,
  diagnosticWorkflow,
} from "./fixtures/diagnostic-workflow";
import type {
  DiagnosticLlmAdapter,
  DiagnosticLlmResult,
} from "./services/diagnostic-llm-adapter";
import type { DiagnosticMcpCatalogAdapter } from "./services/diagnostic-mcp-catalog-adapter";
import type { DiagnosticMcpRuntimeAdapter } from "./services/diagnostic-four-block-executor";

describe("four-block diagnostic workflow", () => {
  it("shows the active block, elapsed activity, and uncommitted output while AI runs", async () => {
    const user = userEvent.setup();
    let resolveExecution: (result: DiagnosticLlmResult) => void = () =>
      undefined;
    const execution = new Promise<DiagnosticLlmResult>((resolve) => {
      resolveExecution = resolve;
    });
    const controlledAdapter: DiagnosticLlmAdapter = {
      async listModels() {
        return [
          {
            provider: "test",
            label: "Controlled test",
            options: [
              {
                value: "test::controlled",
                label: "Controlled model",
                provider: "test",
                model: "controlled",
                isCurrent: true,
              },
            ],
          },
        ];
      },
      async execute(_request, _settings, observer) {
        observer?.onProgress({
          stage: "generating",
          message: "Receiving controlled output.",
          partialText: "The first reviewable sentence is arriving.",
          observedAt: Date.now(),
        });
        return execution;
      },
    };

    render(
      <EngineeringWorkflowVisualSlice
        badge="CP3F · Run observability"
        diagnosticLlmAdapter={controlledAdapter}
        diagnosticScenario={diagnosticScenario}
        workflow={diagnosticWorkflow}
      />,
    );

    await user.click(
      await screen.findByRole("button", { name: "▶ Run selected AI" }),
    );

    const monitor = await screen.findByLabelText("Workflow execution monitor");
    expect(within(monitor).getByText("Executing block 2 of 4")).toBeVisible();
    expect(within(monitor).getByText("2. Interpret Request")).toBeVisible();
    expect(
      within(monitor).getByText(/Receiving controlled output/),
    ).toBeVisible();
    expect(
      within(monitor).getByText("The first reviewable sentence is arriving."),
    ).toBeVisible();
    expect(within(monitor).getByText(/elapsed/)).toBeVisible();
    expect(
      screen.getByRole("button", { name: "AI task 2. Interpret Request" }),
    ).toHaveAttribute("data-run-state", "running");

    await act(async () => {
      resolveExecution({
        text: "The completed controlled output.",
        provider: "test",
        model: "controlled",
        thinkingLevel: "default",
      });
      await execution;
    });

    expect(
      within(monitor).getByText("Active frontier block 3 of 4"),
    ).toBeVisible();
    expect(within(monitor).getByText("3. Run Selected MCP Tool")).toBeVisible();
    expect(
      within(monitor).getByText("The completed controlled output."),
    ).toBeVisible();
    const unresolvedQuickBinding = screen.getByLabelText("Quick MCP binding");
    expect(
      within(unresolvedQuickBinding).getByLabelText("Quick MCP server"),
    ).toHaveValue("");
    expect(
      within(unresolvedQuickBinding).getByText("Choose from workspace"),
    ).toBeVisible();
  });

  it("validates and applies one workflow document to the same diagram", async () => {
    const user = userEvent.setup();
    render(
      <EngineeringWorkflowVisualSlice
        badge="CP3E · Code ↔ diagram"
        diagnosticScenario={diagnosticScenario}
        workflow={diagnosticWorkflow}
      />,
    );

    await user.click(screen.getByRole("button", { name: "Code" }));
    const editor = screen.getByLabelText("Workflow source code");
    expect((editor as HTMLTextAreaElement).value).toContain("0.1-discovery");
    expect(screen.getByText("Applied to diagram")).toBeVisible();

    const edited = (editor as HTMLTextAreaElement).value
      .replace(
        '"title": "Four-Block Diagnostic Workflow"',
        '"title": "Generic Four-Block Experiment"',
      )
      .replace('"title": "Interpret Request"', '"title": "Review Research"');
    fireEvent.change(editor, { target: { value: edited } });

    expect(screen.getByText("Valid · not applied")).toBeVisible();
    expect(
      screen.getByRole("button", { name: "⚠ Apply workflow code" }),
    ).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Apply to diagram" }));
    expect(
      screen.getByRole("heading", { name: "Generic Four-Block Experiment" }),
    ).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Diagram" }));
    expect(
      screen.getByRole("button", { name: "AI task 2. Review Research" }),
    ).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Code" }));
    fireEvent.change(screen.getByLabelText("Workflow source code"), {
      target: { value: "{" },
    });
    expect(screen.getByText("JSON_SYNTAX")).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Apply to diagram" }),
    ).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Diagram" }));
    expect(
      screen.getByRole("heading", { name: "Generic Four-Block Experiment" }),
    ).toBeVisible();
  });

  it("runs a prompt-only request through the selected AI and stops honestly before MCP", async () => {
    const user = userEvent.setup();
    render(
      <EngineeringWorkflowVisualSlice
        badge="CP3D · Diagnostic loop"
        diagnosticScenario={diagnosticScenario}
        workflow={diagnosticWorkflow}
      />,
    );

    expect(
      screen.getByRole("heading", { name: "Four-Block Diagnostic Workflow" }),
    ).toBeVisible();
    expect(screen.getByLabelText("Request prompt")).toHaveValue(
      "Create a 100 x 60 x 8 mm editable mounting plate with four 8 mm through holes whose centers are 10 mm from the nearest X and Z edges.",
    );
    expect(screen.getAllByText(/Optional.*0 provided/)).toHaveLength(2);

    await user.click(
      await screen.findByRole("button", { name: "▶ Run selected AI" }),
    );

    expect(
      await screen.findByRole("button", { name: "⚠ Select exact MCP tool" }),
    ).toBeDisabled();

    expect(screen.getByRole("tab", { name: "Details" })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await user.click(screen.getByRole("tab", { name: "Diagnosis" }));
    expect(
      screen.getByRole("heading", { name: "Exact MCP tool not selected" }),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "AI output is preserved" }),
    ).toBeVisible();
    expect(
      screen.getAllByText(/Candidate brief created from/)[0],
    ).toBeVisible();
    expect(screen.queryByText(/mounting spacing/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/outcome failed/i)).not.toBeInTheDocument();
  });

  it("reaches the same honest AI boundary when an optional image is attached", async () => {
    const user = userEvent.setup();
    render(
      <EngineeringWorkflowVisualSlice
        badge="CP3D · Diagnostic loop"
        diagnosticScenario={diagnosticScenario}
        workflow={diagnosticWorkflow}
      />,
    );

    await user.upload(
      screen.getByLabelText("Upload reference images"),
      new File(["image"], "mounting-reference.png", { type: "image/png" }),
    );
    expect(await screen.findByText("1 selected")).toBeVisible();

    await user.click(
      await screen.findByRole("button", { name: "▶ Run selected AI" }),
    );

    expect(await screen.findByLabelText("Installed MCP server")).toBeVisible();
    await user.click(screen.getByRole("tab", { name: "Diagnosis" }));
    expect(screen.getByText("MCP_TOOL_NOT_SELECTED")).toBeVisible();
    expect(screen.queryByText(/mounting spacing/i)).not.toBeInTheDocument();
  });

  it("binds an installed MCP and exact catalog tool without executing it", async () => {
    const user = userEvent.setup();
    render(
      <EngineeringWorkflowVisualSlice
        badge="CP3D · Diagnostic loop"
        diagnosticScenario={diagnosticScenario}
        workflow={diagnosticWorkflow}
      />,
    );

    await user.click(
      await screen.findByRole("button", { name: "▶ Run selected AI" }),
    );
    const serverSelect = await screen.findByLabelText("Installed MCP server");
    expect(
      within(serverSelect).getByRole("option", {
        name: "Fixture Modeling MCP · active",
      }),
    ).toBeVisible();
    expect(
      within(serverSelect).getByRole("option", {
        name: "Fixture Search MCP · inactive",
      }),
    ).toBeVisible();

    await user.selectOptions(serverSelect, "fixture-modeling");
    await user.selectOptions(
      screen.getByLabelText("Exact MCP tool"),
      "fixture-modeling:create-candidate",
    );

    expect(
      screen.getByRole("button", {
        name: "⚠ Map MCP input: brief",
      }),
    ).toBeDisabled();
    expect(
      screen.getAllByText("fixture-modeling:create-candidate")[0],
    ).toBeVisible();
    expect(screen.getByText("brief")).toBeVisible();

    await user.click(screen.getByRole("tab", { name: "Diagnosis" }));
    expect(
      screen.getByRole("heading", {
        name: "MCP tool selected; input mapping required",
      }),
    ).toBeVisible();
    expect(screen.getByText(/Step 2 produced text/)).toBeVisible();
    expect(
      screen.queryByRole("heading", { name: "Exact MCP tool not selected" }),
    ).not.toBeInTheDocument();
  });

  it("initializes the live diagnostic fixture with BREP and its intended exact tool", async () => {
    const user = userEvent.setup();
    const brepCatalogAdapter: DiagnosticMcpCatalogAdapter = {
      async listCatalog() {
        return {
          servers: [
            {
              serverId: "installed-brep-id",
              name: "BREP MCP",
              description: "Boundary representation modeling tools.",
              transport: "stdio",
              active: true,
              installed: true,
            },
          ],
          tools: [
            {
              toolId: "installed-brep-id:brep.model.apply_history",
              serverId: "installed-brep-id",
              name: "brep.model.apply_history",
              description: "Apply a bounded PartHistory model.",
              inputSchema: {
                type: "object",
                properties: { history: { type: "object" } },
                required: ["history"],
              },
              enabled: true,
            },
          ],
        };
      },
    };

    render(
      <EngineeringWorkflowVisualSlice
        badge="CP3D · Diagnostic loop"
        diagnosticScenario={diagnosticScenario}
        diagnosticMcpCatalogAdapter={brepCatalogAdapter}
        workflow={diagnosticWorkflow}
      />,
    );

    await user.click(
      screen.getByRole("button", {
        name: "MCP action 3. Run Selected MCP Tool",
      }),
    );

    const quickBinding = await screen.findByLabelText("Quick MCP binding");
    expect(within(quickBinding).getByLabelText("Quick MCP server")).toHaveValue(
      "installed-brep-id",
    );
    expect(
      within(quickBinding).getByLabelText("Quick exact MCP tool"),
    ).toHaveValue("installed-brep-id:brep.model.apply_history");
    expect(
      within(quickBinding).getByText("Fixture starting value"),
    ).toBeVisible();
    expect(
      screen.getByText(/diagnostic test explicitly uses BREP MCP/i),
    ).toBeVisible();
    expect(screen.getByLabelText("Exact MCP tool")).toHaveValue(
      "installed-brep-id:brep.model.apply_history",
    );
    expect(
      within(quickBinding).getByText(/map required input: history/i),
    ).toBeVisible();
    expect(screen.getByText("Input mapping required")).toBeVisible();
  });

  it("runs all four blocks through one shared runner and exposes each block result", async () => {
    const user = userEvent.setup();
    const catalogAdapter: DiagnosticMcpCatalogAdapter = {
      async listCatalog() {
        return {
          servers: [
            {
              serverId: "installed-brep-id",
              name: "BREP MCP",
              description: "Fixture BREP server.",
              transport: "stdio",
              active: true,
              installed: true,
            },
          ],
          tools: [
            {
              toolId: "installed-brep-id:brep.model.apply_history",
              serverId: "installed-brep-id",
              name: "brep.model.apply_history",
              description: "Apply history.",
              inputSchema: {
                type: "object",
                properties: { history: { type: "object" } },
                required: ["history"],
              },
              enabled: true,
            },
          ],
        };
      },
    };
    const llmAdapter: DiagnosticLlmAdapter = {
      async listModels() {
        return [
          {
            provider: "test",
            label: "Test provider",
            options: [
              {
                value: "test::current",
                label: "Current Wright model",
                provider: "test",
                model: "current",
                isCurrent: true,
              },
            ],
          },
        ];
      },
      async execute() {
        return {
          text: JSON.stringify({
            kind: "mounting-plate",
            units: "mm",
            width: 100,
            height: 60,
            thickness: 8,
            holes: [],
          }),
          provider: "test",
          model: "current",
          thinkingLevel: "default",
        };
      },
    };
    const performOutputAction = vi.fn(async () => ({
      kind: "completed" as const,
      message: "Opened test model.",
    }));
    const runtimeAdapter: DiagnosticMcpRuntimeAdapter = {
      supports: () => true,
      performOutputAction,
      createRun() {
        return {
          responseInstructions: () => "Return the typed fixture.",
          parseGeneratedOutput: (text) => JSON.parse(text),
          async invoke(specification) {
            return {
              output: { artifactId: "candidate-1" },
              evidence: { mappedFrom: specification },
            };
          },
          async evaluate() {
            return {
              output: {
                accepted: true,
                meaning: "Fixture accepted.",
                outputs: [
                  {
                    outputId: "model-1",
                    title: "Mounting plate",
                    kind: "model",
                    description: "A test model.",
                    format: "Test CAD",
                    durability: "session",
                    producer: { block: "mcp", toolName: "example.create" },
                    actions: [
                      {
                        actionId: "view",
                        kind: "view",
                        label: "View model",
                        available: true,
                      },
                    ],
                  },
                ],
              },
              evidence: { inspections: 3 },
            };
          },
          async dispose() {},
        };
      },
    };

    render(
      <EngineeringWorkflowVisualSlice
        badge="Shared runner"
        diagnosticScenario={diagnosticScenario}
        diagnosticLlmAdapter={llmAdapter}
        diagnosticMcpCatalogAdapter={catalogAdapter}
        diagnosticMcpRuntimeAdapter={runtimeAdapter}
        workflow={diagnosticWorkflow}
      />,
    );

    await user.click(await screen.findByRole("button", { name: "▶ Run" }));
    expect(
      await screen.findByRole("button", { name: "✓ Demo complete" }),
    ).toBeDisabled();

    const monitor = screen.getByLabelText("Workflow execution monitor");
    expect(
      within(monitor).getAllByText("Completed · view result"),
    ).toHaveLength(4);
    expect(within(monitor).getByText("1 output ready")).toBeVisible();
    expect(within(monitor).getByText("Mounting plate")).toBeVisible();
    await user.click(
      within(monitor).getByRole("button", { name: "View model" }),
    );
    expect(performOutputAction).toHaveBeenCalledWith(
      expect.objectContaining({ outputId: "model-1" }),
      expect.objectContaining({ actionId: "view" }),
    );
    await user.click(
      within(monitor).getByRole("button", {
        name: /3.*Run Selected MCP Tool.*Completed · view result/,
      }),
    );
    const resultPanel = await screen.findByRole("tabpanel", {
      name: "Run result",
    });
    expect(resultPanel).toHaveTextContent("Completed");
    expect(resultPanel).toHaveTextContent("Result summary");
    expect(resultPanel).toHaveTextContent("Artifact Id");
    expect(resultPanel).toHaveTextContent("candidate-1");
    expect(
      within(resultPanel).getByText("Produced data").closest("details"),
    ).not.toHaveAttribute("open");
    expect(
      within(resultPanel)
        .getByText("Technical details and evidence")
        .closest("details"),
    ).not.toHaveAttribute("open");
  });
});
