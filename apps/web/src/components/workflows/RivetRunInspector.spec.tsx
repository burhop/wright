import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import {
  cancelledInspection,
  emptyInspection,
  failedInspection,
  historicalRun,
  runningInspection,
  succeededInspection,
} from "./rivet-run-inspector.fixtures";
import { RivetRunInspector } from "./RivetRunInspector";

const renderInspector = (
  inspection = succeededInspection,
  overrides: Partial<React.ComponentProps<typeof RivetRunInspector>> = {},
) => render(
  <RivetRunInspector
    inspection={inspection}
    recentRuns={[inspection.run, historicalRun]}
    currentRevision={2}
    elapsedMs={inspection.run.duration_ms || 2500}
    onSelectRun={vi.fn()}
    onFocusStep={vi.fn()}
    onRerun={vi.fn()}
    onExportEvidence={vi.fn()}
    {...overrides}
  />,
);

describe("RivetRunInspector", () => {
  it("opens for running state and can collapse to its compact summary", async () => {
    const user = userEvent.setup();
    renderInspector(runningInspection);
    expect(await screen.findByTestId("rivet-run-state-running")).toBeVisible();
    expect(screen.getByTestId("rivet-run-inspector")).toHaveClass("is-open");
    await user.click(screen.getByRole("button", { name: /run inspector/i }));
    expect(screen.getByTestId("rivet-run-inspector")).toHaveClass("is-collapsed");
  });

  it("renders every retained output type and bounded/redacted disclosures", async () => {
    const user = userEvent.setup();
    renderInspector();
    expect(await screen.findByTestId("rivet-run-result-empty")).toHaveTextContent("null");
    expect(screen.getByTestId("rivet-run-result-dimensions")).toHaveTextContent('"width": 4');
    expect(screen.getByTestId("rivet-run-result-items")).toHaveTextContent('"a"');
    expect(screen.getByRole("link", { name: "Open link" })).toHaveAttribute("href", "https://example.test/report");
    expect(screen.getByTestId("rivet-run-result-large")).toHaveTextContent("Incomplete");
    expect(screen.getByTestId("rivet-run-result-secret")).toHaveTextContent("Redacted");
    await user.click(screen.getByRole("button", { name: "Expand" }));
    expect(screen.getByRole("button", { name: "Collapse" })).toBeVisible();
  });

  it("states explicitly when a successful run has no outputs", async () => {
    renderInspector(emptyInspection);
    expect(await screen.findByText("This run has no final outputs yet.")).toBeVisible();
  });

  it("auto-opens failed diagnosis, preserves upstream steps, and offers only safe full rerun", async () => {
    const user = userEvent.setup();
    const rerun = vi.fn();
    renderInspector(failedInspection, { onRerun: rerun });
    expect(await screen.findByText(/connection ended/i)).toBeVisible();
    expect(screen.getByText(/partial change/i)).toBeVisible();
    expect(screen.queryByRole("button", { name: /retry step/i })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /run saved revision again/i }));
    expect(rerun).toHaveBeenCalledTimes(1);
    await user.click(screen.getByRole("button", { name: "Steps" }));
    expect(screen.getByText(/Inspect CAD/)).toBeVisible();
    expect(screen.getByText(/Create feature/)).toBeVisible();
  });

  it("shows cancellation and technical details without residue warning when cleanup is known", async () => {
    const user = userEvent.setup();
    renderInspector(cancelledInspection);
    expect(await screen.findByText(/workflow run was cancelled/i)).toBeVisible();
    expect(screen.queryByText(/partial change/i)).not.toBeInTheDocument();
    fireEvent.click(screen.getByText("Technical details"));
    expect(screen.getByText("RIVET_RUN_CANCELLED")).toBeVisible();
    expect(screen.getByText("trace-child")).toBeVisible();
    await user.click(screen.getByRole("button", { name: "History" }));
    expect(screen.getByText(/Revision 1 · historical/)).toBeVisible();
  });
});
