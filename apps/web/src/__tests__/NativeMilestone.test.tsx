import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { NativeMilestone } from "../components/program-status/NativeMilestone";
import { makeNativeMilestone } from "./native-milestone-fixture";

describe("native milestone dashboard", () => {
  it("keeps implementation, verified tasks, integration and benchmark denominators distinct", () => {
    render(
      <NativeMilestone
        milestone={makeNativeMilestone()}
        benchmarkQualified={0}
      />,
    );
    expect(
      screen.getByTestId("native-progress-implementation"),
    ).toHaveTextContent("2/4");
    expect(
      screen.getByTestId("native-progress-verification"),
    ).toHaveTextContent("1/4");
    expect(screen.getByTestId("native-progress-integration")).toHaveTextContent(
      "1/3",
    );
    expect(screen.getByTestId("native-progress-integration")).toHaveTextContent(
      "1 tasks are exempt",
    );
    expect(screen.getAllByRole("progressbar")).toHaveLength(3);
    expect(screen.getByText("0/100 qualified")).toBeVisible();
    expect(
      screen.getByText(/do not represent overall product completion/),
    ).toBeVisible();
    expect(
      screen.getByText("Inspect the validated native definition"),
    ).toBeVisible();
    expect(
      screen.getByText(/authoritative for AI clients, canvas and runtime/),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Rivet migration" }),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Rivet retirement" }),
    ).toBeVisible();
  });

  it("makes stale coverage, failed/skipped/not-run results and missing human evidence explicit", () => {
    render(
      <NativeMilestone
        milestone={makeNativeMilestone()}
        benchmarkQualified={0}
      />,
    );
    expect(screen.getByText(/covered source scope has changed/)).toBeVisible();
    expect(
      screen.getByTestId("native-check-counts-Q-EDITOR"),
    ).toHaveTextContent(
      "4 passed · 1 failed · 2 skipped · 1 not run (8 total)",
    );
    expect(screen.getByText("No evidence recorded.")).toBeVisible();
    expect(
      screen.getByText("Current source coverage is not established."),
    ).toBeVisible();
    expect(
      screen.getByText(
        "Human validation requires recorded participant evidence.",
      ),
    ).toBeVisible();
    expect(
      screen.getByText(
        "Required action: Arrange and record participant sessions",
      ),
    ).toBeVisible();
    const remaining = screen.getByTestId("native-acceptance-AC02");
    expect(remaining).toHaveTextContent("Required checks remaining:");
    expect(
      within(remaining).getAllByRole("link", { name: "Q-HUMAN" })[0],
    ).toHaveAttribute("href", "#native-check-Q-HUMAN");
  });

  it("offers keyboard-accessible evidence with exact tested identity separate from report and candidate", async () => {
    const user = userEvent.setup();
    const milestone = makeNativeMilestone();
    render(<NativeMilestone milestone={milestone} benchmarkQualified={0} />);
    const summary = screen.getByText("Evidence and coverage for Q-MODEL");
    summary.focus();
    expect(summary).toHaveFocus();
    // jsdom does not emulate native summary activation with Enter.
    await user.click(summary);
    expect(summary.closest("details")).toHaveAttribute("open");
    const artifact = screen.getByRole("link", {
      name: "Q-MODEL evidence artifact 1 (opens in new tab)",
    });
    expect(artifact).toBeVisible();
    expect(artifact).toHaveAttribute(
      "href",
      milestone.checks[0].artifact_urls[0],
    );
    expect(artifact).toHaveAttribute("rel", "noreferrer");
    await user.tab();
    expect(artifact).toHaveFocus();
    expect(
      within(summary.closest("details")!).getByText("a".repeat(40)),
    ).toBeVisible();
    expect(screen.getByText("c".repeat(40))).toBeVisible();
    expect(
      screen
        .getAllByText("b".repeat(40))
        .some((element) => element.closest("details") === null),
    ).toBe(true);
  });

  it("shows scope changes, all task stages, and delivery records on demand", () => {
    render(
      <NativeMilestone
        milestone={makeNativeMilestone()}
        benchmarkQualified={0}
      />,
    );
    const scopeSummary = screen.getByText("Scope changes and task denominator");
    fireEvent.click(scopeSummary);
    expect(screen.getByText("Initial bounded milestone")).toBeVisible();
    expect(screen.getByText(/Added: T001, T002, T003, T004/)).toBeVisible();
    const tasksSummary = screen.getByText("All 4 milestone tasks");
    fireEvent.click(tasksSummary);
    const task = within(tasksSummary.closest("details")!).getByTestId(
      "native-task-T004",
    );
    expect(task).toHaveTextContent("Remaining");
    expect(task).toHaveTextContent("not tested");
    expect(task).toHaveTextContent("Not applicable");
    fireEvent.click(screen.getByText("Branch, PRs, merge and deployment"));
    expect(
      screen.getByRole("link", { name: /wright\/pull\/123/ }),
    ).toBeVisible();
    expect(screen.getByText("not verified")).toBeVisible();
  });

  it("has honest empty states without inferring capabilities from implemented tasks", () => {
    const milestone = makeNativeMilestone();
    milestone.capabilities = [];
    milestone.examples = [];
    milestone.blockers = [];
    milestone.next_task_ids = [];
    milestone.tasks = milestone.tasks.map((task) => ({
      ...task,
      activity: "idle",
    }));
    render(<NativeMilestone milestone={milestone} benchmarkQualified={7} />);
    expect(
      screen.getByText("No native capabilities have delivery evidence yet."),
    ).toBeVisible();
    expect(
      screen.getByText("No development examples registered."),
    ).toBeVisible();
    expect(screen.getByText(/No explicit blockers recorded/)).toBeVisible();
    expect(screen.getByText("No next task recorded.")).toBeVisible();
    expect(screen.getByText("7/100 qualified")).toBeVisible();
  });
});
