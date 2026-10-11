import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { HistoricalResultView } from "./HistoricalResultView";

const fetch = vi.hoisted(() => vi.fn());
vi.mock("../../services/host-adapter", () => ({
  hostAdapter: { fetch, resolveBackendUrl: (path: string) => path },
}));
const props = {
  sessionId: "session",
  workflowPath: "workflows/saved.workflow.wflow",
  runLogPath: "runs/saved/history.json",
  onClose: vi.fn(),
};
const history = {
  schema_version: "wright.historical-result/1",
  read_only: true,
  workflow_path: props.workflowPath,
  run_log_path: props.runLogPath,
  permitted_actions: [],
  run: {
    run_id: "old-run",
    status: "failed",
    error: "Retained failure",
    source_matches_current: false,
    results: [],
  },
};

describe("read-only historical result", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    fetch.mockResolvedValue({ ok: true, json: async () => history });
  });
  it("reads exact history and offers no execution or device controls", async () => {
    const open = vi.fn();
    render(<HistoricalResultView {...props} onOpenFile={open} />);
    await screen.findByText(/Recorded run: old-run/);
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(fetch.mock.calls[0][0]).toContain(
      "run_log_path=runs%2Fsaved%2Fhistory.json",
    );
    expect(fetch.mock.calls[0][1]).not.toHaveProperty("method", "POST");
    expect(screen.getByText(/workflow has changed/)).toBeVisible();
    expect(
      screen.queryByRole("button", { name: /start|print|approve|cancel/i }),
    ).not.toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Open saved run record" }),
    );
    expect(open).toHaveBeenCalledWith(props.runLogPath);
    fireEvent.click(screen.getByRole("button", { name: "Back to workflow" }));
    expect(props.onClose).toHaveBeenCalledTimes(1);
  });
  it("rejects an identity mismatch without rendering foreign results", async () => {
    fetch.mockResolvedValue({
      ok: true,
      json: async () => ({
        ...history,
        workflow_path: "workflows/foreign.workflow.wflow",
      }),
    });
    render(<HistoricalResultView {...props} />);
    await screen.findByRole("alert");
    expect(screen.queryByText(/Recorded run/)).not.toBeInTheDocument();
  });
  it("aborts its observer on close without a mutation request", async () => {
    fetch.mockReturnValue(new Promise(() => {}));
    const view = render(<HistoricalResultView {...props} />);
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    const signal = fetch.mock.calls[0][1].signal;
    view.unmount();
    expect(signal.aborted).toBe(true);
    expect(fetch).toHaveBeenCalledTimes(1);
  });
});
