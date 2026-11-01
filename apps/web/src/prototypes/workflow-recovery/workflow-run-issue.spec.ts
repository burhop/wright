import { expect, it } from "vitest";
import { WorkspaceWorkflowRunError } from "../../services/workflow-run-error";
import { workflowRunIssue } from "./workflow-run-issue";

it("attributes the qualification gate to Wright maintainers, not the user's input or an absent MCP", () => {
  const issue = workflowRunIssue(
    new WorkspaceWorkflowRunError(
      "Template blocked",
      "workflow_template_setup_required",
      "Qualify CalculiX",
      "request",
    ),
  );
  expect(issue).toMatchObject({
    title: "Run not started",
    notStarted: true,
    owner: "Wright template/integration maintainers",
  });
  expect(issue?.inputs).toContain("Not assessed");
  expect(issue?.tools).toContain("Not checked by this gate");
  expect(issue?.nextStep).toContain(
    "Selecting an MCP server alone does not clear",
  );
});

it("distinguishes workflow setup and MCP operation failures", () => {
  expect(
    workflowRunIssue(
      new WorkspaceWorkflowRunError(
        "Missing prompt",
        "workflow_not_ready",
        "Supply a prompt",
        "request",
      ),
    ),
  ).toMatchObject({
    notStarted: true,
    owner: "Workflow configuration",
    nextStep: "Supply a prompt",
  });
  expect(
    workflowRunIssue(
      new WorkspaceWorkflowRunError(
        "Disconnected",
        "mcp_call_failed",
        "Check connection",
        "execution",
      ),
    ),
  ).toMatchObject({
    title: "Tool operation failed",
    notStarted: false,
    owner: "MCP/tool integration",
    nextStep: "Check connection",
  });
});

it("does not infer that execution never started from unknown or streamed errors", () => {
  expect(
    workflowRunIssue(
      new WorkspaceWorkflowRunError("Unavailable", "", "", "request"),
    ),
  ).toMatchObject({ notStarted: false, owner: "Cause not classified" });
  expect(
    workflowRunIssue(
      new WorkspaceWorkflowRunError(
        "Late error",
        "workflow_template_setup_required",
        "",
        "execution",
      ),
    )?.notStarted,
  ).toBe(false);
  expect(workflowRunIssue(null)).toBeNull();
});
