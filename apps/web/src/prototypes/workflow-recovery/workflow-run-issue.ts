import type { WorkspaceWorkflowRunError } from "../../services/workflow-run-error";

export interface WorkflowRunIssue {
  title: string;
  cause: string;
  notStarted: boolean;
  owner: string;
  inputs: string;
  nextStep: string;
  tools?: string;
}

export function workflowRunIssue(
  error: WorkspaceWorkflowRunError | null,
): WorkflowRunIssue | null {
  if (!error) return null;
  if (
    error.phase === "request" &&
    error.code === "workflow_template_setup_required"
  ) {
    return {
      title: "Run not started",
      cause:
        "Wright has not validated this template's engineering integrations for live execution.",
      notStarted: true,
      owner: "Wright template/integration maintainers",
      inputs:
        "Not assessed. Changing your design request will not remove this blocker.",
      tools:
        "Not checked by this gate. MCP availability and selection are separate requirements.",
      nextStep:
        "The template's required engineering integrations must be configured and tested by its maintainers before Wright can run it. Selecting an MCP server alone does not clear this restriction.",
    };
  }
  if (
    error.phase === "request" &&
    [
      "workflow_source_invalid",
      "workflow_not_ready",
      "workflow_disconnected_process",
      "workflow_source_conflict",
    ].includes(error.code)
  ) {
    return {
      title: "Run not started",
      cause: error.description,
      notStarted: true,
      owner: "Workflow configuration",
      inputs:
        "This is a workflow setup check, not a verdict on the engineering design.",
      nextStep:
        error.correction ||
        "Review the workflow configuration and save the corrected definition before running.",
    };
  }
  if (error.code === "mcp_call_failed") {
    return {
      title: "Tool operation failed",
      cause: error.description,
      notStarted: false,
      owner: "MCP/tool integration",
      inputs:
        "This error alone does not establish whether the design inputs are valid.",
      nextStep:
        error.correction ||
        "Review the tool response and connection in Tool Registry before retrying. Check any outputs already produced.",
    };
  }
  return {
    title: "Workflow failed",
    cause: error.description,
    notStarted: false,
    owner: "Cause not classified",
    inputs: "The available diagnostic does not identify an input error.",
    nextStep:
      error.correction ||
      "Review the technical details and any saved run before retrying. Execution status has not been established by this error.",
  };
}
