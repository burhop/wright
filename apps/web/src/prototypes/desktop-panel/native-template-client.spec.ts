import { expect, it, vi } from "vitest";
import { nativeTemplateClient } from "./native-template-client";
import type { EngineeringWorkflowTemplate } from "../../services/workspace-service";
const workspace = {
  workspace_id: "w",
  session_id: "s",
  workspace_name: "Demo",
  available: true,
  reason: null,
};
const template = {
  template_id: "robot-tracking-diagnosis",
  version: "1.0.0",
  source_digest: "a".repeat(64),
} as EngineeringWorkflowTemplate;
it("preserves pinned template and scoped creation request without execution", async () => {
  const call = vi.fn().mockResolvedValue({
    content: [],
    structuredContent: {
      workspace_id: "w",
      path: "workflows/robot.workflow.wflow",
      storage_digest: "b".repeat(64),
    },
  });
  const client = nativeTemplateClient(call, workspace);
  await client.instantiateEngineeringWorkflowTemplate(
    "s",
    template,
    "workflows/robot.workflow.wflow",
    "request-one",
  );
  expect(call).toHaveBeenCalledExactlyOnceWith(
    "wright_workflow_template_create",
    {
      workspace_id: "w",
      session_id: "s",
      template_id: template.template_id,
      template_version: "1.0.0",
      expected_source_digest: template.source_digest,
      workflow_path: "workflows/robot.workflow.wflow",
      request_id: "request-one",
    },
  );
  await expect(
    client.instantiateEngineeringWorkflowTemplate(
      "other",
      template,
      "workflows/robot.workflow.wflow",
      "request-two",
    ),
  ).rejects.toThrow("workspace changed");
  expect(call).toHaveBeenCalledTimes(1);
});
it("does not treat failed catalog loading as an empty success", async () => {
  const call = vi.fn().mockResolvedValue({ content: [], isError: true });
  await expect(
    nativeTemplateClient(call, workspace).getEngineeringWorkflowTemplates(),
  ).rejects.toThrow("did not confirm");
  call.mockResolvedValue({
    content: [],
    structuredContent: { catalog_version: "1.0.0", templates: [] },
  });
  await expect(
    nativeTemplateClient(call, workspace).getEngineeringWorkflowTemplates(),
  ).rejects.toThrow("incompatible");
});
it("rejects cross-workspace creation receipts", async () => {
  const call = vi.fn().mockResolvedValue({
    content: [],
    structuredContent: {
      workspace_id: "other",
      path: "workflows/robot.workflow.wflow",
      storage_digest: "b".repeat(64),
    },
  });
  await expect(
    nativeTemplateClient(
      call,
      workspace,
    ).instantiateEngineeringWorkflowTemplate(
      "s",
      template,
      "workflows/robot.workflow.wflow",
      "request",
    ),
  ).rejects.toThrow("identity is unconfirmed");
});
