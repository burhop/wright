import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import type {
  EngineeringWorkflowTemplate,
  EngineeringWorkflowTemplateInstance,
} from "../../services/workspace-service";
import type { DesktopWorkspace, HomeCall } from "./NativeHomePanel";

function document(result: CallToolResult): Record<string, unknown> {
  if (result.isError)
    throw new Error(
      "Wright did not confirm the template operation. Refresh and inspect saved workflows before retrying.",
    );
  if (result.structuredContent) return result.structuredContent;
  const text = result.content.find((item) => item.type === "text");
  if (text?.type !== "text") throw new Error("Template response unavailable.");
  return JSON.parse(text.text);
}

export function nativeTemplateClient(
  call: HomeCall,
  workspace: DesktopWorkspace,
) {
  const scope = {
    workspace_id: workspace.workspace_id,
    session_id: workspace.session_id,
  };
  return {
    async getEngineeringWorkflowTemplates(): Promise<
      EngineeringWorkflowTemplate[]
    > {
      const result = document(await call("wright_workflow_templates", scope));
      if (
        result.catalog_version !== "1.0.0" ||
        !Array.isArray(result.templates) ||
        result.templates.length !== 10
      )
        throw new Error(
          "The engineering template catalog is unavailable or incompatible.",
        );
      return result.templates as EngineeringWorkflowTemplate[];
    },
    async instantiateEngineeringWorkflowTemplate(
      sessionId: string,
      template: EngineeringWorkflowTemplate,
      path: string,
      requestId: string,
    ): Promise<EngineeringWorkflowTemplateInstance> {
      if (sessionId !== workspace.session_id)
        throw new Error("Template workspace changed. Reopen the picker.");
      const result = document(
        await call("wright_workflow_template_create", {
          ...scope,
          template_id: template.template_id,
          template_version: template.version,
          expected_source_digest: template.source_digest,
          workflow_path: path,
          request_id: requestId,
        }),
      );
      if (
        result.workspace_id !== workspace.workspace_id ||
        result.path !== path ||
        typeof result.storage_digest !== "string"
      )
        throw new Error(
          "Template creation identity is unconfirmed. Refresh and inspect the saved workflow.",
        );
      return result as unknown as EngineeringWorkflowTemplateInstance;
    },
  };
}
