import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ActiveAssignments } from "../components/program-status/ActiveAssignments";
import { DeliveryLanes } from "../components/program-status/DeliveryLanes";
import { UseCaseFunnels } from "../components/program-status/UseCaseFunnels";
import { WorkProgress } from "../components/program-status/WorkProgress";

const action = {
  id: "NEXT",
  label: "Publish exact bundle",
  purpose: "lane_next_action",
  eligibility: "eligible",
  authority_state: "authorized",
  requires_human_approval: false,
  blocker: null,
  evidence: [],
};
const work: any = {
  current_milestone: "Browser program status",
  active_feature: "EPP-F01B",
  program_tasks: {
    completed: 80,
    total: 128,
    remaining: 48,
    registered_sources: ["one", "two"],
    undecomposed_roadmap_items: ["EPP-F02", "EPP-F03"],
  },
  tasks: { feature_id: "EPP-F01B", completed: 8, total: 48, remaining: 40 },
  active_assignments: [],
  checkpoints: [],
  blockers: [],
  current_next_action: action,
  lanes: [
    {
      kind: "integration",
      branch: "077-control-plane-validator",
      milestone: "Integrated",
      latest_capability: "Validator merged",
      blocker: null,
      next_action: action,
      observed_at: "2026-08-29T02:59:04Z",
    },
    {
      kind: "continued_development",
      branch: "codex/epp-continued-development-reconciled",
      milestone: "Browser status",
      latest_capability: "Browser MVP",
      blocker: "Publisher incomplete",
      next_action: action,
      observed_at: "2026-08-29T02:59:04Z",
    },
  ],
};
const supplement: any = {
  customer_catalog: { proposed_total: 100 },
  use_cases: {
    all: {
      total: 0,
      in_progress: 0,
      implemented: 0,
      independently_verified: 0,
    },
    process_100: {
      defined: 0,
      in_progress: 0,
      implemented: 0,
      tested: 0,
      independently_verified: 0,
      benchmark_qualified: 0,
    },
  },
  benchmark_context: {
    hold_reason: "Qualification is not authorized.",
    dependencies: [
      {
        id: "EPP-F03",
        label: "Durable run evidence",
        status: "pending",
        blocking: true,
      },
    ],
  },
};

describe("program status work and capability detail", () => {
  it("states task denominator limitations and undecomposed roadmap work", () => {
    render(<WorkProgress work={work} />);
    expect(
      screen.getByText(/not overall product completion/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/2 roadmap items remain outside/i),
    ).toBeInTheDocument();
  });

  it("does not infer an agent assignment", () => {
    render(<ActiveAssignments assignments={[]} />);
    expect(screen.getByRole("status")).toHaveTextContent(
      /no committed assignment/i,
    );
  });

  it("keeps proposed, implemented, tested, and qualified counts separate", () => {
    render(<UseCaseFunnels supplement={supplement} />);
    const table = screen.getByRole("table", {
      name: /all governed use cases/i,
    });
    expect(table).toHaveTextContent("100 proposed");
    expect(table).toHaveTextContent("0/100");
    expect(screen.getByText(/not authorized/i)).toBeInTheDocument();
    expect(screen.getByText(/EPP-F03/)).toBeInTheDocument();
  });

  it("shows integration and development as separate evidence-backed lanes", () => {
    render(<DeliveryLanes lanes={work.lanes} />);
    expect(screen.getByText("integration")).toBeInTheDocument();
    expect(screen.getByText("continued development")).toBeInTheDocument();
    expect(screen.getByText("Publisher incomplete")).toBeInTheDocument();
  });
});
