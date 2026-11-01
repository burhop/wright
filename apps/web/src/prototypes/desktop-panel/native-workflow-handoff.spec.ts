import { expect, it, vi } from "vitest";
import { requestWorkflowPlan } from "./native-workflow-handoff";
import type { App } from "@modelcontextprotocol/ext-apps";
import instruction from "./instructions/plan-workflow.v2.json";
const workspace = {
  workspace_id: "w1",
  session_id: "s1",
  workspace_name: "Handle",
  available: true,
  reason: null,
};
function host(supported = true) {
  const sendMessage = vi.fn().mockResolvedValue({});
  const app = {
    getHostCapabilities: () => (supported ? { message: { text: {} } } : {}),
    sendMessage,
  } as unknown as Pick<App, "getHostCapabilities" | "sendMessage">;
  return { app, sendMessage };
}
it("sends the exact workspace and versioned authoring request once through the host", async () => {
  const { app, sendMessage } = host();
  expect(await requestWorkflowPlan(app, workspace)).toBe("sent");
  expect(sendMessage).toHaveBeenCalledTimes(1);
  const [request] = sendMessage.mock.calls[0];
  expect(request.role).toBe("user");
  expect(request.content[0].text.slice(0, instruction.body.length)).toBe(
    instruction.body,
  );
  const context = JSON.parse(request.content[0].text.split("\n").at(-1));
  expect(context).toEqual({
    instruction: { id: "wright.desktop.plan-workflow", version: 2 },
    workspace_id: "w1",
    session_id: "s1",
    workspace_name: "Handle",
  });
});
it("reports unsupported chat delivery without sending", async () => {
  const { app, sendMessage } = host(false);
  expect(await requestWorkflowPlan(app, workspace)).toBe("unsupported");
  expect(sendMessage).not.toHaveBeenCalled();
});
it("does not retry rejected or uncertain delivery", async () => {
  const { app, sendMessage } = host();
  sendMessage.mockResolvedValueOnce({ isError: true });
  await expect(requestWorkflowPlan(app, workspace)).rejects.toThrow(
    "not confirmed",
  );
  expect(sendMessage).toHaveBeenCalledTimes(1);
});
