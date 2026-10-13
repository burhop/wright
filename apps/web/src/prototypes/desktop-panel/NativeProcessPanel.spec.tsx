// Synthetic owner replies; this is not native desktop acceptance.
import { afterEach, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type {
  InteractionResponse,
  InteractionSnapshot,
} from "@wright/process-client";
import type { NativeProcessCall } from "./native-process-client";
import { createNativePanelProcessClient } from "./native-process-client";
import { NativeProcessPanel } from "./NativeProcessPanel";

const hash = "a".repeat(64);
const process = {
  workspace_id: "native-working-workspace",
  source_path: "workflows/common.wflow",
  source_digest: hash,
};
const waiting: InteractionSnapshot = {
  context: {
    process,
    run_id: "saved-run",
    generated_at: "2026-10-12T12:00:00Z",
  },
  state: "waiting_human",
  interactions: [
    {
      checkpoint_id: "choose",
      step_id: "choice",
      kind: "input",
      subject_digest: hash,
      instructions: "Choose the comparison.",
      state: "waiting",
      response_schema: {
        type: "object",
        properties: { selection: { type: "string", enum: ["a", "b"] } },
        required: ["selection"],
        additionalProperties: false,
      },
    },
  ],
  actions: [
    {
      action_id: "respond",
      operation: "respond",
      title: "Submit response",
      enabled: true,
      checkpoint_id: "choose",
      subject_digest: hash,
    },
  ],
};
afterEach(() => {
  cleanup();
  localStorage.clear();
});

it("submits the common declared input against its exact subject and retains the run", async () => {
  let answered = false;
  const call = vi
    .fn<NativeProcessCall>()
    .mockImplementation(async (tool, request) => {
      if (tool === "wright_process_ui_update") {
        expect(request.operation).toBe("respond");
        expect(request.checkpoint_id).toBe("choose");
        expect(request.value).toEqual({ selection: "b" });
        answered = true;
        const answer: InteractionResponse = {
          response_id: "answer",
          workspace_id: process.workspace_id,
          run_id: "saved-run",
          checkpoint_id: "choose",
          subject_digest: hash,
          schema_digest: hash,
          input_digest: hash,
          value: { selection: "b" },
          actor: "wright-owned",
          reason: "Declared input",
          request_id: String(request.request_id),
          created_at: waiting.context.generated_at,
          digest: hash,
        };
        return {
          content: [],
          structuredContent: { ok: true, document: answer },
        };
      }
      expect(request.operation).toBe("snapshot");
      expect(request.run_id).toBe("saved-run");
      return {
        content: [],
        structuredContent: {
          ok: true,
          document: answered
            ? { ...waiting, state: "completed", actions: [], interactions: [] }
            : waiting,
        },
      };
    });
  const native = createNativePanelProcessClient({
    process,
    sessionId: "native-session",
    workspaceName: "Prototype",
    call,
  });
  const view = render(
    <NativeProcessPanel
      {...native}
      sessionId="native-session"
      workspaceName="Prototype"
      title="Common working view"
      runId="saved-run"
    />,
  );
  const field = await screen.findByLabelText("selection (required)");
  expect(
    screen.getByRole("button", { name: "Submit response" }),
  ).toBeDisabled();
  fireEvent.change(field, { target: { value: "1" } });
  fireEvent.click(screen.getByRole("button", { name: "Submit response" }));
  await screen.findByText("Process completed");
  expect(
    call.mock.calls.filter(([tool]) => tool === "wright_process_ui_update"),
  ).toHaveLength(1);
  view.unmount();
  expect(
    call.mock.calls.some(
      ([, request]) =>
        request.operation === "start" || request.operation === "cancel",
    ),
  ).toBe(false);
});
