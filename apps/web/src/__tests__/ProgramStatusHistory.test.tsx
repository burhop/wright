import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ProgramStatusSeries } from "../services/program-status";
import { ProgramHistory } from "../components/program-status/ProgramHistory";

vi.mock("../services/surfaces/renderers/plotly-renderer", () => ({
  PlotlyRenderer: ({
    description,
    fallback,
  }: {
    description: string;
    fallback: React.ReactNode;
  }) => (
    <div role="img" aria-label={description}>
      {fallback}
    </div>
  ),
}));

const action = {
  id: "NEXT",
  label: "Demonstrate one customer-visible workflow",
  purpose: "metric_guidance",
  eligibility: "eligible" as const,
  authority_state: "authorized" as const,
  requires_human_approval: false,
  blocker: null,
  evidence: [],
};

const series: ProgramStatusSeries = {
  id: "feature_tasks",
  label: "EPP-F01B task burn-up",
  unit: "completed_tasks",
  counting_rule: "checked_unique_task_ids",
  source_classification: "feature_task",
  availability: "available",
  feature_id: "EPP-F01B",
  decision_use:
    "Shows delivery within this feature, not overall product completion.",
  current_limitation:
    "Later roadmap features are not decomposed into this task total.",
  next_action: action,
  latest_change: {
    commit: "b".repeat(40),
    observed_at: "2026-08-29T02:59:04Z",
    from_value: 4,
    to_value: 8,
    reason: "Browser MVP verified.",
  },
  omitted_observations: 0,
  unavailable_reason: null,
  observations: [
    {
      commit: "a".repeat(40),
      transition_id: "TR-0072",
      parent_commit: null,
      observed_at: "2026-08-29T02:16:28Z",
      value: 4,
      denominator: 48,
      label: "Setup",
      source_classification: "feature_task",
      change_reason: "Setup complete.",
      evidence: [],
    },
    {
      commit: "b".repeat(40),
      transition_id: null,
      parent_commit: "a".repeat(40),
      observed_at: "2026-08-29T02:59:04Z",
      value: 8,
      denominator: 48,
      label: "Browser MVP",
      source_classification: "feature_task",
      change_reason: "Browser MVP verified.",
      evidence: [],
    },
  ],
};

describe("ProgramHistory", () => {
  it("explains task scope and preserves exact time/commit table evidence", () => {
    render(<ProgramHistory history={[series]} />);
    expect(
      screen.getByText(/not total customer-product completion/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/4 → 8: Browser MVP verified/)).toBeInTheDocument();
    expect(screen.getByText(/Later roadmap features/)).toBeInTheDocument();
    expect(
      screen.getByText("Demonstrate one customer-visible workflow"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("table", { name: /exact committed checkpoints/i }),
    ).toHaveTextContent("bbbbbbbb");
  });

  it("renders unavailable rather than inventing history", () => {
    render(
      <ProgramHistory
        history={[
          {
            ...series,
            availability: "unavailable",
            observations: [],
            unavailable_reason: "No committed points.",
          },
        ]}
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent(/unavailable/i);
  });
});
