import type { App } from "@modelcontextprotocol/ext-apps";
import type { DesktopWorkspace } from "./NativeHomePanel";
import instruction from "./instructions/plan-workflow.v1.json";

/** Sends a user-requested authoring handoff; no workflow or gateway dispatch. */
export async function requestWorkflowPlan(
  app: Pick<App, "getHostCapabilities" | "sendMessage">,
  workspace: DesktopWorkspace,
): Promise<"sent" | "unsupported"> {
  if (!app.getHostCapabilities()?.message?.text) return "unsupported";
  const result = await app.sendMessage(
    {
      role: "user",
      content: [
        {
          type: "text",
          text:
            instruction.body +
            "\n" +
            JSON.stringify({
              instruction: { id: instruction.id, version: instruction.version },
              workspace_id: workspace.workspace_id,
              session_id: workspace.session_id,
              workspace_name: workspace.workspace_name,
            }),
        },
      ],
    },
    { timeout: 5000 },
  );
  if (result.isError) throw new Error("Chat delivery not confirmed");
  return "sent";
}
