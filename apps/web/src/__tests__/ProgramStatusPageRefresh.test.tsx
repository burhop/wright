import { act, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../services/program-status", async (importOriginal) => {
  const actual =
    await importOriginal<typeof import("../services/program-status")>();
  return {
    ...actual,
    fetchProgramStatus: vi.fn(),
    fetchProgramStatusPublisher: vi.fn(),
  };
});
vi.mock("../components/program-status/AtAGlanceSummary", () => ({
  AtAGlanceSummary: ({ bundle }: any) => (
    <div data-testid="rendered-bundle">
      {bundle.supplement.work.tasks.completed}/
      {bundle.supplement.work.tasks.total}
    </div>
  ),
}));
vi.mock("../components/program-status/ProgramHistory", () => ({
  ProgramHistory: () => null,
}));
vi.mock("../components/program-status/WorkProgress", () => ({
  WorkProgress: () => null,
}));
vi.mock("../components/program-status/ActiveAssignments", () => ({
  ActiveAssignments: () => null,
}));
vi.mock("../components/program-status/UseCaseFunnels", () => ({
  UseCaseFunnels: () => null,
}));
vi.mock("../components/program-status/DeliveryLanes", () => ({
  DeliveryLanes: () => null,
}));
vi.mock("../components/program-status/EvidenceDetails", () => ({
  EvidenceDetails: () => null,
}));

import { ProgramStatusPage } from "../components/pages/ProgramStatusPage";
import {
  fetchProgramStatus,
  fetchProgramStatusPublisher,
  type ProgramStatusBundle,
} from "../services/program-status";
import { makeProgramStatusBundle } from "./program-status-fixture";
import { makeNativeMilestone } from "./native-milestone-fixture";

const fetchBundle = vi.mocked(fetchProgramStatus);
const fetchPublisher = vi.mocked(fetchProgramStatusPublisher);
const bundle = makeProgramStatusBundle() as ProgramStatusBundle;
const publisher = {
  state: "active" as const,
  mode: "committed_watch" as const,
  observed_commit: "c".repeat(40),
  last_attempt_at: "2026-08-29T14:00:00Z",
  last_success_at: "2026-08-29T14:00:00Z",
  failure_code: null,
  recovery: null,
};

async function settleInitialPoll() {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
  });
}

describe("ProgramStatusPage refresh state", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    fetchBundle.mockReset();
    fetchPublisher.mockReset();
  });

  afterEach(() => vi.useRealTimers());

  it("keeps the exact last bundle current after an unchanged 304", async () => {
    fetchBundle
      .mockResolvedValueOnce({ status: 200, etag: '"bundle-1"', bundle })
      .mockResolvedValueOnce({ status: 304, etag: '"bundle-1"', bundle: null });
    fetchPublisher.mockResolvedValue(publisher);
    render(<ProgramStatusPage />);
    await settleInitialPoll();

    expect(screen.getByTestId("rendered-bundle")).toHaveTextContent("4/48");
    expect(screen.queryByTestId("native-milestone")).not.toBeInTheDocument();
    expect(
      screen.queryByTestId("program-historical-details"),
    ).not.toBeInTheDocument();
    expect(
      screen.getByTestId("program-status-refresh-state"),
    ).toHaveTextContent("Committed evidence current");
    await act(async () => vi.advanceTimersByTimeAsync(5000));

    expect(fetchBundle).toHaveBeenLastCalledWith(
      '"bundle-1"',
      expect.anything(),
    );
    expect(screen.getByTestId("rendered-bundle")).toHaveTextContent("4/48");
    expect(
      screen.getByTestId("program-status-refresh-state"),
    ).toHaveTextContent("Committed evidence current");
  });

  it("keeps the last valid bundle visible when a later refresh fails", async () => {
    fetchBundle
      .mockResolvedValueOnce({ status: 200, etag: '"bundle-1"', bundle })
      .mockRejectedValueOnce(new Error("isolated refresh failure"));
    fetchPublisher.mockResolvedValue(publisher);
    render(<ProgramStatusPage />);
    await settleInitialPoll();
    await act(async () => vi.advanceTimersByTimeAsync(5000));

    expect(screen.getByTestId("rendered-bundle")).toHaveTextContent("4/48");
    expect(
      screen.getByTestId("program-status-refresh-state"),
    ).toHaveTextContent("Showing last valid evidence");
    expect(
      screen.getByTestId("program-status-refresh-state"),
    ).toHaveTextContent("Refresh failed; inspect the local Wright API.");
  });

  it("shows an honest unavailable state when no prior bundle exists", async () => {
    fetchBundle.mockRejectedValueOnce(new Error("initial read failed"));
    fetchPublisher.mockRejectedValueOnce(new Error("heartbeat unavailable"));
    render(<ProgramStatusPage />);
    await settleInitialPoll();

    expect(
      screen.getByRole("heading", {
        name: "No validated program-status bundle is available yet",
      }),
    ).toBeVisible();
    expect(
      screen.getByTestId("program-status-refresh-state"),
    ).toHaveTextContent("Program status unavailable");
  });

  it("does not retain a false active publisher when heartbeat polling fails", async () => {
    fetchBundle.mockResolvedValueOnce({
      status: 200,
      etag: '"bundle-1"',
      bundle,
    });
    fetchPublisher.mockRejectedValueOnce(new Error("heartbeat unavailable"));
    render(<ProgramStatusPage />);
    await settleInitialPoll();

    const status = screen.getByTestId("program-status-refresh-state");
    expect(status).toHaveTextContent("Showing last valid evidence");
    expect(status).toHaveTextContent("Publisher heartbeat unavailable");
    expect(status).not.toHaveTextContent("Publisher: active");
  });

  it("retains the last bundle but marks a failed publisher heartbeat stale", async () => {
    fetchBundle.mockResolvedValueOnce({
      status: 200,
      etag: '"bundle-1"',
      bundle,
    });
    fetchPublisher.mockResolvedValueOnce({
      ...publisher,
      state: "failed",
      failure_code: "PROGRAM_STATUS_SOURCE_INVALID",
      recovery: "repair the exact committed source",
    });
    render(<ProgramStatusPage />);
    await settleInitialPoll();

    const status = screen.getByTestId("program-status-refresh-state");
    expect(screen.getByTestId("rendered-bundle")).toHaveTextContent("4/48");
    expect(status).toHaveTextContent("Showing last valid evidence");
    expect(status).toHaveTextContent("PROGRAM_STATUS_SOURCE_INVALID");
    expect(status).toHaveTextContent("repair the exact committed source");
  });

  it("prioritizes the native milestone and retains it when refresh fails", async () => {
    const nativeBundle = structuredClone(bundle);
    Object.assign(nativeBundle.supplement.work, {
      milestone: makeNativeMilestone(),
    });
    fetchBundle
      .mockResolvedValueOnce({
        status: 200,
        etag: '"native-1"',
        bundle: nativeBundle,
      })
      .mockRejectedValueOnce(new Error("refresh failed"));
    fetchPublisher.mockResolvedValue(publisher);
    render(<ProgramStatusPage />);
    await settleInitialPoll();

    expect(screen.getByTestId("native-milestone")).toBeVisible();
    expect(
      screen.getByTestId("program-historical-details"),
    ).not.toHaveAttribute("open");
    expect(screen.getByTestId("rendered-bundle")).not.toBeVisible();
    await act(async () => vi.advanceTimersByTimeAsync(5000));
    expect(
      screen.getByTestId("native-progress-implementation"),
    ).toHaveTextContent("2/4");
    expect(
      screen.getByTestId("program-status-refresh-state"),
    ).toHaveTextContent("Showing last valid evidence");
  });
});
