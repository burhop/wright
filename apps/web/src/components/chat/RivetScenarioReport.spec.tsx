import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { workspaceService } from "../../services/workspace-service";
import { RivetScenarioReport } from "./RivetScenarioReport";

vi.mock("../../services/workspace-service", async (loadOriginal) => {
  const original =
    await loadOriginal<typeof import("../../services/workspace-service")>();
  return {
    ...original,
    workspaceService: {
      getEngineeringScenarioReport: vi.fn(),
      cancelEngineeringScenario: vi.fn(),
      exportEngineeringScenarioReport: vi.fn(),
    },
  };
});

describe("RivetScenarioReport", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(workspaceService.getEngineeringScenarioReport).mockResolvedValue({
      scenario_run_id: "scenario-run",
      workflow_run_id: "workflow-run",
      workspace_id: "workspace",
      session_id: "session",
      scenario_id: "structural-bracket",
      scenario_revision: 1,
      manifest_digest: "a".repeat(64),
      workflow_digest: "b".repeat(64),
      binding_set_digest: "c".repeat(64),
      state: "failed",
      identity: {},
      artifacts: [
        {
          artifact_id: "bracket-fea",
          domain: "fea",
          kind: "fea-result",
          content_digest: "f".repeat(64),
          validation_state: "valid",
          producer: {
            run_id: "scenario-run",
            node_id: "node-fea",
            call_id: "call-fea",
            capability: "fea__solve_static",
          },
        },
      ],
      environment: { tier: "tier1" },
      cleanup_state: "clean",
      residue: {},
      assertions: [
        {
          assertion_id: "stress-limit",
          plugin: "fea",
          state: "fail",
          reason_code: "range_exceeded",
          artifact_digests: ["f".repeat(64)],
          expected: { maximum: 120, unit: "MPa" },
          observed: { value: 135, unit: "MPa" },
          producer: {
            node_id: "node-fea",
            capability: "fea__solve_static",
          },
          message: "stress-limit violated range_exceeded",
          recovery: "Inspect load, constraints, material, and geometry.",
        },
      ],
      advisory: {
        schema_version: "1.0",
        simulation_only: true,
        machine_authority: false,
        score_semantics: "uncalibrated_screening_score",
        selected_candidate_id: "candidate-a",
        candidate_outcomes: [
          {
            candidate_id: "candidate-a",
            review_status: "selected_for_review",
            reason: "Lowest eligible score.",
            chatter_score: 0.1,
          },
          {
            candidate_id: "candidate-b",
            review_status: "rejected",
            reason: "Classified as chatter.",
            chatter_score: 0.9,
          },
        ],
        notices: ["Human engineering review is required."],
        provider_evidence: [
          { provider_kind: "mcp" },
          { provider_kind: "engineering_model" },
        ],
      },
      report_digest: "d".repeat(64),
    });
  });

  it("names the exact node, capability, invariant, values, units, and recovery", async () => {
    render(
      <RivetScenarioReport sessionId="session" scenarioRunId="scenario-run" />,
    );

    expect(await screen.findByText(/Scenario is failed/)).toBeInTheDocument();
    const assertion = screen.getByTestId("scenario-assertion-stress-limit");
    expect(assertion).toHaveTextContent("node-fea");
    expect(assertion).toHaveTextContent("fea__solve_static");
    expect(assertion).toHaveTextContent("range_exceeded");
    expect(assertion).toHaveTextContent("MPa");
    expect(assertion).toHaveTextContent("135");
    expect(assertion).toHaveTextContent("Inspect load, constraints");
    expect(assertion).toHaveTextContent("f".repeat(64));
    const artifact = screen.getByTestId("scenario-artifact-bracket-fea");
    expect(artifact).toHaveTextContent("fea / fea-result");
    expect(artifact).toHaveTextContent("fea__solve_static");
    expect(artifact).toHaveTextContent("valid");
    expect(screen.queryByText(/Cancel scenario/)).not.toBeInTheDocument();
    expect(screen.queryByTestId("scenario-advisory")).toBeNull();
  });

  it("suppresses a stale advisory after cancellation and shows residue recovery", async () => {
    const previous = await workspaceService.getEngineeringScenarioReport(
      "session",
      "scenario-run",
    );
    vi.mocked(workspaceService.getEngineeringScenarioReport).mockResolvedValue({
      ...previous!,
      state: "cancelled",
      cleanup_state: "residue",
      residue: {
        kinds: ["model_runtime"],
        recovery: "Inspect cleanup before retrying.",
      },
    });
    render(
      <RivetScenarioReport sessionId="session" scenarioRunId="scenario-run" />,
    );
    expect(
      await screen.findByText(/Scenario is cancelled/),
    ).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Inspect cleanup before retrying",
    );
    expect(screen.queryByTestId("scenario-advisory")).toBeNull();
    expect(screen.queryByText(/Selected discrete candidate/)).toBeNull();
  });
});
