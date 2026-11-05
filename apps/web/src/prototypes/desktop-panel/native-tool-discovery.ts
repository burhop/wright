import { z } from "zod";
import type { HomeCall } from "./NativeHomePanel";
import type { WorkflowMcpTool } from "../workflow-recovery/mcp-settings";
import type { WorkflowOptionReader } from "../workflow-recovery/workflow-tool-discovery";

export function createNativeOptionReader(
  workspaceId: string,
  sessionId: string,
  call?: HomeCall,
): WorkflowOptionReader {
  return async (kind, requestedSession, serverId, includeResources = false) => {
    if (requestedSession !== sessionId || !call)
      throw Error("Engineering options are unavailable for this workspace.");
    const response = await call("wright_workflow_editor_options", {
      request: {
        workspace_id: workspaceId,
        session_id: sessionId,
        kind,
        ...(serverId ? { server_id: serverId } : {}),
        include_resources: includeResources,
      },
    });
    if (response.isError)
      throw Error("Wright could not read the selected engineering options.");
    const data = z
      .object({
        workspace_id: z.literal(workspaceId),
        session_id: z.literal(sessionId),
        kind: z.literal(kind),
        options: z.record(z.string(), z.unknown()),
      })
      .strict()
      .parse(response.structuredContent);
    return new Response(JSON.stringify(data.options), {
      headers: { "content-type": "application/json" },
    });
  };
}

const tool = z
  .object({
    server_name: z.string(),
    workspace_server: z.boolean(),
    name: z.string(),
    server_id: z.string(),
    tool_name: z.string(),
    title: z.string(),
    description: z.string(),
    input_schema: z.record(z.string(), z.unknown()),
    output_schema: z.record(z.string(), z.unknown()).nullable().optional(),
    schema_digest: z.string().regex(/^[a-f0-9]{64}$/),
  })
  .strict();
const result = z
  .object({
    workspace_id: z.string(),
    session_id: z.string(),
    tools: z.array(tool).max(4096),
  })
  .strict();

export function createNativeToolDiscovery(
  workspaceId: string,
  sessionId: string,
  call?: HomeCall,
) {
  return async (requestedSession: string): Promise<WorkflowMcpTool[]> => {
    if (requestedSession !== sessionId || !call)
      throw new Error(
        "Workspace tool discovery is unavailable for this editor.",
      );
    const response = await call("wright_workflow_editor_tools", {
      request: { workspace_id: workspaceId, session_id: sessionId },
    });
    if (response.isError)
      throw new Error("Wright could not read this workspace’s tools.");
    const data = result.parse(response.structuredContent);
    if (data.workspace_id !== workspaceId || data.session_id !== sessionId)
      throw new Error("Wright returned tools for a different workspace.");
    return data.tools.map(({ output_schema, ...item }) => ({
      ...item,
      ...(output_schema ? { output_schema } : {}),
    }));
  };
}
