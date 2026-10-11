import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import {
  recordedInstructionsEvidence,
  RunInstructionsEvidence,
} from "./RunInstructionsEvidence";
import { workspaceService } from "../../services/workspace-service";
afterEach(() => vi.restoreAllMocks());
const resolved = {
  role: "workflow-task",
  text: "Actual recorded instructions",
  text_digest: "a".repeat(64),
  instruction_set_digest: "b".repeat(64),
  origins: ["saved-workflow"],
  asset_ids: ["task"],
  assumption_policy: "document_reasonable",
};
const assumption = {
  parameter: "finish",
  value: "matte",
  units: null,
  rationale: "No surface finish supplied",
  affected_outputs: ["render.png"],
};
const record = {
  events: [
    {
      kind: "instructions_resolved",
      task_id: "design",
      instructions: resolved,
    },
    {
      kind: "assumptions_recorded",
      task_id: "design",
      assumptions: [assumption],
    },
    {
      kind: "model_invocation",
      task_id: "design",
      invocation: {
        operation: "render",
        messages: [{ role: "user", content: "Exact request" }],
        tool_schemas: [],
        request_digest: "c".repeat(64),
      },
    },
  ],
  steps: [
    { task_id: "design", instructions: resolved, assumptions: [assumption] },
  ],
};
it("deduplicates recorded events and step summaries without deriving missing historic evidence", () => {
  const evidence = recordedInstructionsEvidence(record);
  expect(evidence.instructions).toHaveLength(1);
  expect(evidence.assumptions).toHaveLength(1);
  expect(evidence.invocations[0].messages).toEqual([
    { role: "user", content: "Exact request" },
  ]);
  expect(
    recordedInstructionsEvidence({ steps: [{ prompt: "legacy task text" }] }),
  ).toEqual({ instructions: [], assumptions: [], invocations: [] });
});
it("reads final result steps and actual MCP model request collections", () => {
  const evidence = recordedInstructionsEvidence({
    result: {
      steps: [
        {
          task_id: "render",
          instructions: resolved,
          assumptions: [assumption],
        },
      ],
    },
    events: [
      {
        kind: "model_invocation_result",
        task_id: "render",
        invocations: [
          {
            operation: "mcp-task",
            request_digest: "actual",
            messages: [{ role: "user", content: "Recorded task" }],
          },
        ],
      },
    ],
  });
  expect(evidence.instructions[0].text).toBe("Actual recorded instructions");
  expect(evidence.assumptions[0].parameter).toBe("finish");
  expect(evidence.invocations[0].request_digest).toBe("actual");
});
it("loads the exact saved log explicitly and displays assumptions and actual model request", async () => {
  const load = vi
    .spyOn(workspaceService, "getFileContentText")
    .mockResolvedValue(JSON.stringify(record));
  render(
    <RunInstructionsEvidence
      sessionId="session"
      runLogPath="runs/exact.json"
    />,
  );
  expect(load).not.toHaveBeenCalled();
  fireEvent.click(
    screen.getByRole("button", {
      name: "Load recorded instructions and assumptions",
    }),
  );
  await waitFor(() =>
    expect(screen.getByLabelText("Recorded instruction text 1")).toHaveValue(
      "Actual recorded instructions",
    ),
  );
  expect(load).toHaveBeenCalledExactlyOnceWith("session", "runs/exact.json");
  expect(screen.getByText("matte")).toBeTruthy();
  expect(screen.getByText("No surface finish supplied")).toBeTruthy();
  expect(screen.getByText(/Exact request/)).toBeTruthy();
});
it("labels missing historic instructions without fetching current defaults", async () => {
  vi.spyOn(workspaceService, "getFileContentText").mockResolvedValue("{}");
  const defaults = vi.spyOn(workspaceService, "getWorkflowInstructionDefaults");
  render(
    <RunInstructionsEvidence
      sessionId="session"
      runLogPath="runs/legacy.json"
    />,
  );
  fireEvent.click(
    screen.getByRole("button", {
      name: "Load recorded instructions and assumptions",
    }),
  );
  await screen.findByText(/Resolved instruction text was not recorded/);
  expect(defaults).not.toHaveBeenCalled();
});

it("never carries displayed evidence or late results into another selected run", async () => {
  let finish: (value: string) => void = () => {};
  const load = vi
    .spyOn(workspaceService, "getFileContentText")
    .mockResolvedValueOnce(JSON.stringify(record))
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
  const view = render(
    <RunInstructionsEvidence
      sessionId="session"
      runLogPath="runs/first.json"
    />,
  );
  fireEvent.click(
    screen.getByRole("button", {
      name: "Load recorded instructions and assumptions",
    }),
  );
  await screen.findByLabelText("Recorded instruction text 1");
  view.rerender(
    <RunInstructionsEvidence
      sessionId="session"
      runLogPath="runs/second.json"
    />,
  );
  expect(
    screen.queryByLabelText("Recorded instruction text 1"),
  ).not.toBeInTheDocument();
  fireEvent.click(
    screen.getByRole("button", {
      name: "Load recorded instructions and assumptions",
    }),
  );
  await waitFor(() => expect(load).toHaveBeenCalledTimes(2));
  view.rerender(
    <RunInstructionsEvidence
      sessionId="session"
      runLogPath="runs/third.json"
    />,
  );
  finish(JSON.stringify(record));
  await waitFor(() =>
    expect(
      screen.getByRole("button", {
        name: "Load recorded instructions and assumptions",
      }),
    ).toBeEnabled(),
  );
  expect(
    screen.queryByLabelText("Recorded instruction text 1"),
  ).not.toBeInTheDocument();
  expect(load).not.toHaveBeenCalledWith("session", "runs/third.json");
});
