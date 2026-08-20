import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  workspaceService,
  type EngineeringScenarioEntry,
  type EngineeringScenarioPreflight,
} from "../../services/workspace-service";
import { RivetScenarioLibrary } from "./RivetScenarioLibrary";

vi.mock("../../services/workspace-service", async (loadOriginal) => {
  const original =
    await loadOriginal<typeof import("../../services/workspace-service")>();
  return {
    ...original,
    workspaceService: {
      listEngineeringScenarios: vi.fn(),
      preflightEngineeringScenario: vi.fn(),
      startEngineeringScenario: vi.fn(),
      getEngineeringScenarioReport: vi.fn(),
      cancelEngineeringScenario: vi.fn(),
      exportEngineeringScenarioReport: vi.fn(),
    },
  };
});

const scenario: EngineeringScenarioEntry = {
  scenario_id: "structural-bracket",
  revision: 1,
  title: "Structural bracket",
  summary: "Build, weigh, and analyze a bracket.",
  domains: ["cad", "python", "fea"],
  tier: "tier1",
  resource_class: "small",
  expected_duration_seconds: 20,
  manifest_digest: "a".repeat(64),
};

const preflight: EngineeringScenarioPreflight = {
  preflight_id: "preflight",
  scenario_id: scenario.scenario_id,
  scenario_revision: 1,
  manifest_digest: scenario.manifest_digest,
  workflow_slug: "scenario-structural-bracket",
  workflow_revision: 1,
  workflow_digest: "b".repeat(64),
  graph_id: "graph-structural",
  binding_set_digest: "c".repeat(64),
  state: "ready",
  capabilities: [
    {
      node_id: "node-cad",
      requested_tool: "cad__build_bracket",
      selected_tool: "cad__build_bracket",
      binding_digest: "d".repeat(64),
      blockers: [],
      provider: {
        schema_version: "1.0",
        provider_kind: "mcp",
        provider_id: "fixture-cad",
        capability_id: "build_bracket",
        resource_class: "small",
        evidence: {},
      },
      provider_evidence_digest: "f".repeat(64),
    },
    {
      node_id: "node-model",
      requested_tool: "wright_model__fixture__screen",
      selected_tool: "wright_model__fixture__screen",
      binding_digest: "1".repeat(64),
      blockers: [],
      provider: {
        schema_version: "1.0",
        provider_kind: "engineering_model",
        provider_id: "fixture-model",
        capability_id: "screen",
        resource_class: "medium",
        evidence: {},
      },
      provider_evidence_digest: "2".repeat(64),
    },
  ],
  environment: {
    tier: "tier1",
    network: false,
    credentials: false,
    physical_actuation: false,
  },
  blockers: [],
  expires_at: "2099-01-01T00:00:00Z",
};

describe("RivetScenarioLibrary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(workspaceService.listEngineeringScenarios).mockResolvedValue([
      scenario,
    ]);
    vi.mocked(workspaceService.preflightEngineeringScenario).mockResolvedValue(
      preflight,
    );
    vi.mocked(workspaceService.startEngineeringScenario).mockResolvedValue({
      scenario_run_id: "scenario-run",
      workflow_run: {
        run_id: "workflow-run",
        workflow_id: "workflow",
        revision: 1,
        digest: "b".repeat(64),
        graph: "graph-structural",
        generation: 1,
        state: "running",
        reason: null,
        outputs: null,
        duration_ms: null,
        output_truncated: false,
      },
      state: "running",
    });
    vi.mocked(workspaceService.getEngineeringScenarioReport).mockResolvedValue({
      scenario_run_id: "scenario-run",
      workflow_run_id: "workflow-run",
      workspace_id: "workspace",
      session_id: "session",
      scenario_id: scenario.scenario_id,
      scenario_revision: 1,
      manifest_digest: scenario.manifest_digest,
      workflow_digest: "b".repeat(64),
      binding_set_digest: "c".repeat(64),
      state: "running",
      identity: {},
      artifacts: [],
      environment: {},
      cleanup_state: "not_started",
      residue: {},
      assertions: [],
      report_digest: null,
    });
  });

  it("shows domains, tier, resources, safety, exact capabilities, and starts after preflight", async () => {
    const user = userEvent.setup();
    const onPrepared = vi.fn();
    render(
      <RivetScenarioLibrary sessionId="session" onPrepared={onPrepared} />,
    );

    expect(await screen.findByText("Structural bracket")).toBeInTheDocument();
    expect(screen.getByText(/Domains: cad, python, fea/i)).toBeInTheDocument();
    expect(screen.getByText(/TIER1/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Optional dependencies: none/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/no physical actuation/i)).toBeInTheDocument();

    await user.click(
      screen.getByTestId("scenario-preflight-structural-bracket"),
    );
    await waitFor(() =>
      expect(onPrepared).toHaveBeenCalledWith(preflight.workflow_slug),
    );
    expect(
      screen.getByText(/node-cad: cad__build_bracket/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Provider: MCP \/ fixture-cad/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/local engineering model \/ fixture-model/),
    ).toBeInTheDocument();
    const start = screen.getByTestId("scenario-start-structural-bracket");
    expect(start).toBeEnabled();
    await user.click(start);
    await waitFor(() =>
      expect(workspaceService.startEngineeringScenario).toHaveBeenCalledWith(
        "session",
        preflight,
      ),
    );
    expect(await screen.findByText(/Engineering report/)).toBeInTheDocument();
  });

  it("keeps a blocked preflight disabled and presents recovery as text", async () => {
    const user = userEvent.setup();
    vi.mocked(workspaceService.preflightEngineeringScenario).mockResolvedValue({
      ...preflight,
      state: "blocked",
      binding_set_digest: null,
      blockers: [
        {
          code: "scenario_binding_missing",
          message: "CAD capability is missing.",
          recovery: "Enable and validate the CAD MCP.",
        },
      ],
    });
    render(<RivetScenarioLibrary sessionId="session" onPrepared={vi.fn()} />);
    await user.click(
      await screen.findByTestId("scenario-preflight-structural-bracket"),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Enable and validate the CAD MCP.",
    );
    expect(
      screen.getByTestId("scenario-start-structural-bracket"),
    ).toBeDisabled();
  });
});
