import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

import { mockWorkspaceShell } from "./workspace-surfaces/presentation-fixture";

const digest = "d".repeat(64);
const bindingSetDigest = "8".repeat(64);

test("reviews an exact namespaced MCP binding without starting a child", async ({
  page,
}) => {
  await page.route("**/api/auth/session/status", (route) =>
    route.fulfill({ json: { auth_required: false, authenticated: true } }),
  );
  await mockWorkspaceShell(page, []);
  let reviewRequest: Record<string, unknown> | null = null;
  let childReceipts = 0;
  const workflow = (approved = false) => ({
    workflow_id: "workflow-a",
    slug: "multi-mcp",
    revision: 2,
    etag: digest,
    review_state: approved ? "approved" : null,
    reviewer: approved ? "local-user" : null,
    reviewed_at: approved ? 1 : null,
    workflow_digest: approved ? digest : null,
    graph_id: approved ? "graph-a" : null,
    binding_set_id: approved ? "binding-set-a" : null,
    binding_set_digest: approved ? bindingSetDigest : null,
    policy_snapshot_digest: approved ? "f".repeat(64) : null,
    review_digest: approved ? "9".repeat(64) : null,
    stale_reasons: [],
  });
  await page.route("**/api/workspace/workflow-templates", (route) =>
    route.fulfill({ json: { templates: [] } }),
  );
  await page.route("**/api/workspace/workflows?session_id=*", (route) =>
    route.fulfill({ json: { workflows: [workflow(Boolean(reviewRequest))] } }),
  );
  await page.route(
    "**/api/workspace/workflows/multi-mcp/mcp-capabilities?*",
    (route) =>
      route.fulfill({
        json: {
          ...workflow(),
          graph_id: "graph-a",
          snapshot_digest: "e".repeat(64),
          policy_snapshot_digest: "f".repeat(64),
          requirements: [
            {
              graph_id: "graph-a",
              node_id: "node-a",
              node_type: "mcpToolCall",
              static_tool_name: "inspect",
            },
          ],
          issues: [],
          capabilities: ["alpha", "beta"].map((server) => ({
            qualified_tool_name: `${server}__inspect`,
            server_id: server,
            tool_name: "inspect",
            title: `${server} inspect`,
            description: "Inspect a part",
            server_revision: `${server}-v1`,
            capability_digest: "a".repeat(64),
            validation_evidence_id: `${server}-validation`,
            workspace_grant_digest: "b".repeat(64),
            input_schema: { type: "object" },
            output_schema: { type: "object" },
            schema_digest: "c".repeat(64),
            annotations: { readOnlyHint: server === "alpha" },
            required_approvals: server === "beta" ? ["engineering.write"] : [],
            compatibility: "compatible",
            binding_eligible: true,
            blocking_reasons: [],
          })),
          next_after: null,
        },
      }),
  );
  await page.route(
    "**/api/workspace/workflows/multi-mcp/mcp-bindings/preview",
    async (route) => {
      const request = route.request().postDataJSON() as {
        selections: Array<{ qualified_tool_name: string }>;
      };
      expect(request.selections[0].qualified_tool_name).toBe("beta__inspect");
      await route.fulfill({
        json: {
          workflow_id: "workflow-a",
          slug: "multi-mcp",
          revision: 2,
          etag: digest,
          graph_id: "graph-a",
          snapshot_digest: "e".repeat(64),
          policy_snapshot_digest: "f".repeat(64),
          binding_set_id: "binding-set-a",
          binding_set_digest: bindingSetDigest,
          expires_at: "2099-01-01T00:00:00Z",
          ready: true,
          bindings: [
            {
              node_id: "node-a",
              node_handle: "wright:abcdefghijklmnop",
              selected_tool: "beta__inspect",
              binding_digest: "7".repeat(64),
              server_id: "beta",
              server_revision: "beta-v1",
              schema_digest: "c".repeat(64),
              validation_evidence_id: "beta-validation",
              workspace_grant_digest: "b".repeat(64),
              risk: { required_approvals: ["engineering.write"] },
              units_policy: {},
              material_defaults: {},
              blockers: [],
            },
          ],
        },
      });
    },
  );
  await page.route(
    "**/api/workspace/workflows/multi-mcp/review",
    async (route) => {
      reviewRequest = route.request().postDataJSON() as Record<string, unknown>;
      await route.fulfill({ json: workflow(true) });
    },
  );
  await page.route("**/fake-child/**", (route) => {
    childReceipts += 1;
    route.abort();
  });

  await page.goto("/workspace/ws-1");
  await page.getByTestId("activity-bar-workflows-btn").click();
  await page.getByTestId("rivet-workflow-review-multi-mcp").click();
  const select = page.getByTestId("workflow-binding-select-node-a");
  await expect(select).toBeVisible();
  await select.selectOption("beta__inspect");
  await page.getByTestId("workflow-review-binding-summary").press("Enter");
  await page.getByText("Reviewed identity and risk").click();
  await expect(page.getByText("engineering.write")).toBeVisible();

  const accessibility = await new AxeBuilder({ page })
    .include('[data-testid="workflow-capabilities-tab"]')
    .analyze();
  expect(
    accessibility.violations.filter((violation) =>
      ["serious", "critical"].includes(violation.impact || ""),
    ),
  ).toEqual([]);

  await page.getByTestId("workflow-review-approve").click();
  await expect.poll(() => reviewRequest).not.toBeNull();
  expect(reviewRequest).toMatchObject({
    expected_digest: digest,
    graph: "graph-a",
    binding_set_digest: bindingSetDigest,
  });
  expect(childReceipts).toBe(0);
});
