import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  nativeRunApi,
  fetchNativeArtifact,
  type NativeRun,
  type NativeRunSummary,
} from "../../services/native-process";
import { NativeRunPanel } from "./NativeRunPanel";
import { example, savedProcess } from "./native-process.fixture";
vi.mock("../../services/native-process", async (original) => {
  const actual =
    await original<typeof import("../../services/native-process")>();
  return {
    ...actual,
    fetchNativeArtifact: vi.fn(),
    nativeRunApi: {
      history: vi.fn(),
      get: vi.fn(),
      start: vi.fn(),
      cancel: vi.fn(),
      bindings: vi.fn(),
      events: vi.fn(),
    },
  };
});
function fixture(state: NativeRun["state"] = "failed"): NativeRun {
  return {
    run_id: "run-one",
    process_id: example.definition.id,
    state,
    semantic_digest: "a".repeat(64),
    created_at: "2026-09-04T12:00:00Z",
    started_at: "2026-09-04T12:00:01Z",
    completed_at: state === "running" ? null : "2026-09-04T12:00:02Z",
    derived_from_run_id: null,
    reason:
      state === "failed"
        ? {
            code: "NATIVE_ASSERTION_FAILED",
            message: "Expected text was absent.",
            recovery: "Correct the input and run a new version.",
            step_id: "brief-check",
            port_id: null,
          }
        : null,
    trace_id: "native-trace",
    snapshot: {
      definition: example.definition,
      revision: 1,
      token: "1".repeat(64),
      semantic_digest: "a".repeat(64),
    },
    bindings: {},
    actor: "engineer",
    timeout_seconds: 60,
    steps: example.definition.steps.map((step) => ({
      step_id: step.id,
      operation: step.operation,
      state:
        step.id === "brief-check"
          ? "failed"
          : step.id === "brief-file"
            ? "blocked"
            : "succeeded",
      started_at: null,
      completed_at: null,
      inputs: null,
      outputs: null,
      reason: null,
    })),
    artifacts: [],
    last_sequence: 10,
  };
}
const props = () => ({
  sessionId: "session-one",
  saved: savedProcess(),
  definition: example.definition,
  dirty: false,
  authoringBusy: false,
  bindings: {},
  setBindings: vi.fn(),
  inspectStep: vi.fn(),
});
beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(nativeRunApi.history).mockResolvedValue({
    runs: [fixture()],
    next_cursor: null,
  });
  vi.mocked(nativeRunApi.get).mockResolvedValue(fixture());
});
afterEach(cleanup);
describe("mocked run inspection and recovery", () => {
  it("shows actual failure, immutable revision and missing observed artifacts", async () => {
    const input = props();
    render(<NativeRunPanel {...input} />);
    await screen.findByTestId("native-run-inspection");
    expect(screen.getByTestId("native-run-state")).toHaveTextContent("failed");
    expect(screen.getByTestId("native-run-reason")).toHaveTextContent(
      "Correct the input",
    );
    expect(screen.getByText(/No artifacts are recorded/)).toBeInTheDocument();
    fireEvent.click(screen.getByTestId("native-correct-brief-check"));
    expect(input.inspectStep).toHaveBeenCalledWith("brief-check");
    expect(
      screen.queryByText(/Actual artifact bytes verified/),
    ).not.toBeInTheDocument();
  });
  it("gates dirty work and retains the idempotency key on an ambiguous linked rerun", async () => {
    const input = props();
    const view = render(<NativeRunPanel {...input} dirty />);
    await screen.findByTestId("native-run-derived");
    expect(screen.getByTestId("native-run-derived")).toBeDisabled();
    view.rerender(
      <NativeRunPanel {...input} saved={savedProcess(example, 2)} />,
    );
    vi.mocked(nativeRunApi.start)
      .mockRejectedValueOnce(new Error("Connection lost after submission"))
      .mockResolvedValue({
        run_id: "run-two",
        state: "queued",
        semantic_digest: "a".repeat(64),
      });
    fireEvent.click(screen.getByTestId("native-run-derived"));
    await screen.findByText(/Connection lost after submission/);
    fireEvent.click(screen.getByTestId("native-run-derived"));
    await waitFor(() => expect(nativeRunApi.start).toHaveBeenCalledTimes(2));
    const first = vi.mocked(nativeRunApi.start).mock.calls[0],
      second = vi.mocked(nativeRunApi.start).mock.calls[1];
    expect(first).toEqual([
      "session-one",
      example.definition.id,
      "2".repeat(64),
      expect.any(String),
      {},
      60,
      "run-one",
    ]);
    expect(second).toEqual(first);
  });
  it("cancels using the service response and refreshes terminal state", async () => {
    vi.mocked(nativeRunApi.get).mockResolvedValue(fixture("running"));
    vi.mocked(nativeRunApi.cancel).mockImplementation(async () => {
      vi.mocked(nativeRunApi.get).mockResolvedValue({
        ...fixture("cancelled"),
        last_sequence: 11,
      });
      return fixture("cancelled") as NativeRunSummary;
    });
    render(<NativeRunPanel {...props()} />);
    await screen.findByTestId("native-run-cancel");
    fireEvent.click(screen.getByTestId("native-run-cancel"));
    await waitFor(() =>
      expect(screen.getByTestId("native-run-state")).toHaveTextContent(
        "cancelled",
      ),
    );
    expect(nativeRunApi.cancel).toHaveBeenCalledWith("session-one", "run-one");
    expect(screen.queryByTestId("native-run-cancel")).not.toBeInTheDocument();
  });
  it("reconnects after an unavailable snapshot without issuing cancellation", async () => {
    vi.mocked(nativeRunApi.get)
      .mockRejectedValueOnce(new Error("Service disconnected"))
      .mockResolvedValue(fixture());
    render(<NativeRunPanel {...props()} />);
    await screen.findByTestId("native-run-disconnected");
    fireEvent.click(screen.getByTestId("native-run-reconnect"));
    await screen.findByTestId("native-run-inspection");
    expect(nativeRunApi.cancel).not.toHaveBeenCalled();
  });
  it("never exposes failed artifact bytes through preview or download", async () => {
    const run = fixture("succeeded");
    run.artifacts = [
      {
        artifact_id: "artifact-one",
        step_id: "brief-file",
        port_id: "brief-file-output-artifact",
        filename: "brief.md",
        content_digest: "b".repeat(64),
        size: 20,
        media_type: "text/markdown",
        provenance: { operation: "artifact.write-text@1" },
      },
    ];
    vi.mocked(nativeRunApi.get).mockResolvedValue(run);
    vi.mocked(fetchNativeArtifact).mockRejectedValue(
      new Error("Artifact digest mismatch"),
    );
    render(<NativeRunPanel {...props()} />);
    await screen.findByTestId("native-inspect-artifact-artifact-one");
    fireEvent.click(screen.getByTestId("native-inspect-artifact-artifact-one"));
    await screen.findByText("Artifact digest mismatch");
    expect(
      screen.queryByTestId("native-download-artifact-one"),
    ).not.toBeInTheDocument();
  });
  it("requires rebinding when a selected tool's exact schema changes", async () => {
    const input = props(),
      binding = {
        server_id: "server-local",
        tool_name: "calculate",
        input_schema_digest: "a".repeat(64),
        output_schema_digest: "b".repeat(64),
      };
    vi.mocked(nativeRunApi.bindings).mockResolvedValue({
      bindings: [
        {
          ...binding,
          input_schema_digest: "c".repeat(64),
          title: "Calculate",
          input_schema: {},
          output_schema: null,
        },
      ],
    });
    render(
      <NativeRunPanel
        {...input}
        definition={{
          ...example.definition,
          steps: [
            {
              id: "call-step",
              title: "Calculate",
              operation: "mcp.call@1",
              config: {},
            },
          ],
        }}
        bindings={{ "call-step": binding }}
      />,
    );
    await screen.findByText(/Prior binding is unavailable or changed/);
    expect(screen.getByTestId("native-run-start")).toBeDisabled();
  });
});
