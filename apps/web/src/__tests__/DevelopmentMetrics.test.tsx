import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  fetchDevelopmentMetrics,
  metricsSchema,
  projectTasks,
  cumulativeTaskSeries,
  type MetricEvent,
} from "../services/development-metrics";
import { DevelopmentMetrics } from "../components/program-status/DevelopmentMetrics";

vi.mock("../services/development-metrics", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../services/development-metrics")>()),
  fetchDevelopmentMetrics: vi.fn(),
}));
vi.mock("../services/surfaces/renderers/plotly-renderer", () => ({
  PlotlyRenderer: ({
    description,
    representation,
  }: {
    description: string;
    representation: unknown;
  }) => (
    <div
      role="img"
      aria-label={description}
      data-plot={JSON.stringify(representation)}
    />
  ),
}));
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});
const snapshot = (checked: boolean, tasks = true): MetricEvent => ({
  id: "s",
  at: new Date().toISOString(),
  kind: "snapshot",
  feature: "F01",
  subject: "a",
  data: { tasks: tasks ? [{ task: "T001", title: "Example", checked }] : [] },
});

describe("development metrics", () => {
  it("keeps manual validation pending across unchanged unchecked snapshots", () => {
    const manual: MetricEvent = {
      ...snapshot(false),
      kind: "task",
      data: {
        task: "T001",
        title: "Example",
        state: "manual_validation",
        evidence: "User validation pending",
        reason: "Needs user",
        action: "Run checklist",
        owner: "Mark",
      },
    };
    const result = projectTasks([snapshot(false), manual, snapshot(false)]);
    expect(result.points.at(-1)?.counts.manual_validation).toBe(1);
    expect(result.tasks.get("F01:T001")?.action).toBe("Run checklist");
    expect(result.points.at(-1)?.counts.queued).toBe(0);
    expect(result.points.at(-1)?.counts.verified).toBe(0);
  });
  it("carries completed totals into the next batch and preserves reopened work", () => {
    const events = [
      { ...snapshot(true), at: "2026-09-01T00:00:00Z" },
      { ...snapshot(false), feature: "F02", at: "2026-09-02T00:00:00Z" },
      { ...snapshot(true), feature: "F02", at: "2026-09-03T00:00:00Z" },
      { ...snapshot(false), at: "2026-09-04T00:00:00Z" },
    ];
    const series = cumulativeTaskSeries(
      projectTasks(events).points,
      0,
      Date.now(),
    );
    expect(series[0].y.at(-1)).toBe(1);
    expect(series[1].y).toEqual([1, 1, 2, 1]);
    const clipped = cumulativeTaskSeries(
      projectTasks(events).points,
      Date.parse("2026-09-02T12:00:00Z"),
      Date.now(),
    );
    expect(clipped[0].y).toEqual([1, 1, 2, 1]);
  });
  it("separates imported checked tasks from observed completions and repeated snapshots", () => {
    const points = projectTasks([
      snapshot(true),
      snapshot(true),
      snapshot(false),
      snapshot(true),
      snapshot(true),
    ]).points;
    expect(points.map((p) => p.firstSeenChecked)).toEqual([1, 0, 0, 0, 0]);
    expect(points.map((p) => p.completed)).toEqual([0, 0, 0, 1, 0]);
  });
  it("groups token demand and keeps integrated tasks in verified delivery", async () => {
    const base = snapshot(true);
    const usage: MetricEvent = {
      ...base,
      id: "u1",
      kind: "usage",
      data: {
        session: "s",
        task: "T001",
        input_tokens: 100,
        output_tokens: 10,
      },
    };
    const integrated: MetricEvent = {
      ...base,
      id: "done",
      kind: "task",
      data: {
        task: "T001",
        title: "Example",
        state: "integrated",
        evidence: "merge.json",
      },
    };
    vi.mocked(fetchDevelopmentMetrics).mockResolvedValue({
      schema_version: 1,
      availability: "available",
      truncated: false,
      events: [base, usage, { ...usage, id: "u2" }, integrated],
    });
    render(<DevelopmentMetrics />);
    const usagePlot = await screen.findByRole("img", {
      name: "Model usage over time",
    });
    const tokens = JSON.parse(usagePlot.getAttribute("data-plot")!).data.data;
    expect(tokens[0].y).toEqual([200]);
    expect(tokens[1].y).toEqual([20]);
    const delivery = JSON.parse(
      screen
        .getByRole("img", { name: "Verified and integrated work" })
        .getAttribute("data-plot")!,
    ).data.data;
    expect(delivery[0].y.at(-1)).toBe(1);
    expect(delivery[1].y.at(-1)).toBe(1);
  });
  it("never promotes a checked task to verified and retains removed scope", () => {
    const result = projectTasks([
      snapshot(true),
      snapshot(false),
      snapshot(false, false),
    ]);
    expect(result.points[0].counts.implemented).toBe(1);
    expect(result.points[0].counts.verified).toBe(0);
    expect(result.points[1].change).toContain("reopened");
    expect(result.points[2].counts.withdrawn).toBe(1);
  });
  it("preserves explicit verification until checkbox or task scope changes", () => {
    const verified: MetricEvent = {
      id: "v",
      at: new Date().toISOString(),
      kind: "task",
      feature: "F01",
      subject: "a",
      data: {
        task: "T001",
        title: "Example",
        state: "verified",
        evidence: "review.json",
      },
    };
    expect(
      projectTasks([snapshot(true), verified, snapshot(true)]).points.at(-1)
        ?.counts.verified,
    ).toBe(1);
    expect(
      projectTasks([snapshot(true), verified, snapshot(false)]).points.at(-1)
        ?.counts.verified,
    ).toBe(0);
  });
  it("rejects invalid counts and renders unknown usage without zero fabrication", async () => {
    expect(
      metricsSchema.safeParse({
        schema_version: 1,
        events: [
          {
            ...snapshot(true),
            kind: "usage",
            data: {
              session: "s",
              task: "T001",
              input_tokens: -1,
              output_tokens: 0,
            },
          },
        ],
        availability: "available",
        truncated: false,
      }).success,
    ).toBe(false);
    vi.mocked(fetchDevelopmentMetrics).mockResolvedValue({
      schema_version: 1,
      events: [snapshot(true)],
      availability: "available",
      truncated: false,
    });
    render(<DevelopmentMetrics />);
    await screen.findByRole("img", { name: "Cumulative completed tasks" });
    expect(
      screen.queryByRole("img", { name: "Model usage over time" }),
    ).toBeNull();
    fireEvent.change(screen.getByLabelText("Period"), {
      target: { value: "7 days" },
    });
    await waitFor(() =>
      expect(screen.getByLabelText("Period")).toHaveValue("7 days"),
    );
    expect(screen.getByText(/Observation gap/)).toBeInTheDocument();
    expect(
      screen.queryByRole("img", { name: "Verified and integrated work" }),
    ).toBeNull();
    expect(
      screen.queryByRole("img", {
        name: "Implementation, testing, review and integration",
      }),
    ).toBeNull();
    expect(
      screen.getByText(/Activity tracking incomplete/),
    ).toBeInTheDocument();
    expect(screen.getAllByTestId("chart-purpose")).toHaveLength(7);
  });
});
