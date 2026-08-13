import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

import { mockWorkspaceShell } from "./workspace-surfaces/presentation-fixture";

const digest = "d".repeat(64);
const bindingSetDigest = "8".repeat(64);

type EvidenceScenario = "success" | "denied" | "restarted";

async function mockEvidenceJourney(page: Page, scenario: EvidenceScenario) {
  await page.route("**/api/auth/session/status", (route) =>
    route.fulfill({ json: { auth_required: false, authenticated: true } }),
  );
  await mockWorkspaceShell(page, []);
  const runId = `run-${scenario}`;
  const state = scenario === "success" ? "succeeded" : "failed";
  const reason =
    scenario === "denied"
      ? "RIVET_CALL_APPROVAL_DENIED"
      : scenario === "restarted"
        ? "runner_restarted"
        : null;
  const workflow = {
    workflow_id: "workflow-evidence",
    slug: "evidence-flow",
    revision: 1,
    etag: digest,
    review_state: "approved",
    reviewer: "local-user",
    reviewed_at: 1,
    workflow_digest: digest,
    graph_id: "graph-a",
    binding_set_id: "binding-set-a",
    binding_set_digest: bindingSetDigest,
    policy_snapshot_digest: "f".repeat(64),
    review_digest: "9".repeat(64),
    stale_reasons: [],
  };
  const run = {
    run_id: runId,
    workflow_id: "workflow-evidence",
    revision: 1,
    digest,
    graph: "Main",
    generation: 1,
    state,
    reason,
    outputs: scenario === "success" ? { inspected: true } : null,
    duration_ms: 12,
    output_truncated: false,
    manifest: {
      terminal_state: state,
      reason_code: reason,
      manifest_digest: "7".repeat(64),
    },
  };
  const denied = scenario === "denied";
  const restarted = scenario === "restarted";
  const evidence = {
    schema_version: 1,
    run_id: runId,
    manifest: run.manifest,
    bindings: [
      {
        node_id: "node-alpha",
        qualified_tool_name: "alpha__inspect",
        binding_digest: "6".repeat(64),
      },
    ],
    child_calls: denied
      ? []
      : [{ call_id: "call-1", state: state, child_received: true }],
    approvals: denied ? [{ approval_id: "approval-1", state: "denied" }] : [],
    artifacts:
      scenario === "success"
        ? [{ artifact_id: "mesh.vtk", label: "Validated mesh" }]
        : [],
    timeline: [
      {
        kind: "binding",
        node_id: "node-alpha",
        qualified_tool_name: "alpha__inspect",
        state: "reviewed",
      },
      ...(denied
        ? [{ kind: "approval", state: "denied", request_id: "request-1" }]
        : [{ kind: "child-call", state, call_id: "call-1" }]),
    ],
    reproducibility: {
      reproducible: !restarted,
      summary: restarted
        ? "A new review is required before reproducing this run."
        : "Recorded identities match the current reviewed configuration.",
      differences: restarted
        ? [
            {
              code: "binding_set_changed",
              recorded: bindingSetDigest,
              current: "5".repeat(64),
              recovery_action: "review_current_bindings",
            },
          ]
        : [],
    },
    accounting: {
      binding_count: 1,
      child_call_count: denied ? 0 : 1,
      approval_count: denied ? 1 : 0,
      artifact_count: scenario === "success" ? 1 : 0,
      denied_before_child_count: denied ? 1 : 0,
      redaction_count: 1,
      truncated: false,
    },
  };
  await page.route("**/api/workspace/workflow-templates", (route) =>
    route.fulfill({ json: { templates: [] } }),
  );
  await page.route("**/api/workspace/workflows?session_id=*", (route) =>
    route.fulfill({ json: { workflows: [workflow] } }),
  );
  await page.route("**/api/workspace/workflows/evidence-flow/runs", (route) =>
    route.fulfill({ json: run }),
  );
  await page.route(
    `**/api/workspace/workflows/runs/${runId}/approvals?*`,
    (route) => route.fulfill({ json: { approvals: evidence.approvals } }),
  );
  await page.route(
    `**/api/workspace/workflows/runs/${runId}/history?*`,
    (route) =>
      route.fulfill({
        json: {
          run_id: runId,
          events: [
            { sequence: 1, kind: "started", payload: {} },
            { sequence: 2, kind: state, payload: { code: reason } },
          ],
        },
      }),
  );
  await page.route(
    `**/api/workspace/workflows/runs/${runId}/evidence/export?*`,
    (route) =>
      route.fulfill({
        contentType: "application/json",
        headers: {
          "Content-Disposition": `attachment; filename="${runId}.json"`,
        },
        body: JSON.stringify(evidence),
      }),
  );
  await page.route(
    `**/api/workspace/workflows/runs/${runId}/evidence?*`,
    (route) => route.fulfill({ json: evidence }),
  );
  await page.route(`**/api/workspace/workflows/runs/${runId}?*`, (route) =>
    route.fulfill({ json: run }),
  );
  await page.goto("/workspace/ws-1");
  await page.getByTestId("activity-bar-workflows-btn").click();
  await page.getByTestId("rivet-workflow-run-evidence-flow").click();
  await expect(page.getByTestId(`rivet-run-${runId}`)).toBeVisible();
  return { runId };
}

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

test("exports complete successful run evidence without secret text", async ({
  page,
}) => {
  await mockEvidenceJourney(page, "success");
  await page.getByText("Run evidence", { exact: true }).click();
  await expect(page.getByText(/1 bindings/)).toContainText("1 child calls");
  await expect(page.getByText("Validated mesh")).toBeVisible();
  await expect(
    page.getByRole("status").filter({ hasText: "Recorded identities match" }),
  ).toContainText("Recorded identities match");
  await expect(page.getByTestId("rivet-run-timeline")).toContainText(
    "alpha__inspect",
  );
  await page.getByRole("button", { name: "Export evidence JSON" }).click();
  await expect(page.locator("body")).not.toContainText("super-secret");

  const accessibility = await new AxeBuilder({ page })
    .include('[data-testid="rivet-run-evidence"]')
    .analyze();
  expect(
    accessibility.violations.filter((violation) =>
      ["serious", "critical"].includes(violation.impact || ""),
    ),
  ).toEqual([]);
});

test("attributes a denied call before any child receipt", async ({ page }) => {
  await mockEvidenceJourney(page, "denied");
  await page.getByText("Run evidence", { exact: true }).click();
  await expect(page.getByText(/Failure boundary/)).toContainText(
    "RIVET_CALL_APPROVAL_DENIED",
  );
  await expect(page.getByText(/denied before any child/)).toContainText("1");
  await expect(page.getByText(/0 child calls/)).toBeVisible();
});

test("explains restart evidence and exact recovery review", async ({
  page,
}) => {
  await mockEvidenceJourney(page, "restarted");
  await page.getByText("Run evidence", { exact: true }).click();
  await expect(page.getByText(/Failure boundary/)).toContainText(
    "runner_restarted",
  );
  await expect(
    page.getByRole("status").filter({ hasText: "new review" }),
  ).toContainText("new review");
  await expect(page.getByText(/binding_set_changed/)).toContainText(
    "review_current_bindings",
  );
  await page.setViewportSize({ width: 420, height: 800 });
  await expect(page.getByTestId("rivet-run-evidence")).toBeVisible();
});

test("uses keyboard-only exact approval and reports cancellation residue at narrow zoom", async ({
  page,
}) => {
  await page.route("**/api/auth/session/status", (route) =>
    route.fulfill({ json: { auth_required: false, authenticated: true } }),
  );
  await mockWorkspaceShell(page, []);
  let runState = "running";
  let approvalState = "pending";
  let approvalRequest: Record<string, unknown> | null = null;
  let cancelRequest: Record<string, unknown> | null = null;
  const runId = "run-active";
  const workflow = {
    workflow_id: "workflow-active",
    slug: "active-flow",
    revision: 1,
    etag: digest,
    review_state: "approved",
    reviewer: "local-user",
    reviewed_at: 1,
    workflow_digest: digest,
    graph_id: "graph-a",
    binding_set_id: "binding-set-a",
    binding_set_digest: bindingSetDigest,
    policy_snapshot_digest: "f".repeat(64),
    review_digest: "9".repeat(64),
    stale_reasons: [],
  };
  const currentRun = () => ({
    run_id: runId,
    workflow_id: "workflow-active",
    revision: 1,
    digest,
    graph: "Main",
    generation: 1,
    state: runState,
    reason: runState === "cancelled" ? "cancelled_by_user" : null,
    outputs: null,
    duration_ms: runState === "cancelled" ? 20 : null,
    output_truncated: false,
    manifest:
      runState === "cancelled"
        ? {
            terminal_state: "cancelled",
            reason_code: "cancelled_by_user",
            manifest_digest: "7".repeat(64),
            cancellation: {
              child_acknowledged: false,
              residue_state: "possible",
              recovery_code: "RIVET_MCP_RESIDUE_POSSIBLE",
            },
          }
        : null,
  });
  const approval = () => ({
    approval_id: "approval-active",
    approval_digest: "4".repeat(64),
    run_id: runId,
    node_id: "node-write",
    binding_digest: "6".repeat(64),
    server_id: "cad",
    qualified_tool_name: "cad__write_part",
    request_id: "request-write",
    argument_digest: "3".repeat(64),
    argument_summary: { operation: "write", part: "bracket" },
    required_gates: ["engineering.write"],
    state: approvalState,
    created_at: "2026-08-13T00:00:00Z",
    expires_at: "2099-01-01T00:00:00Z",
  });
  await page.route("**/api/workspace/workflow-templates", (route) =>
    route.fulfill({ json: { templates: [] } }),
  );
  await page.route("**/api/workspace/workflows?session_id=*", (route) =>
    route.fulfill({ json: { workflows: [workflow] } }),
  );
  await page.route("**/api/workspace/workflows/active-flow/runs", (route) =>
    route.fulfill({ json: currentRun() }),
  );
  await page.route(
    `**/api/workspace/workflows/runs/${runId}/approvals?*`,
    (route) => route.fulfill({ json: { approvals: [approval()] } }),
  );
  await page.route(
    `**/api/workspace/workflows/runs/${runId}/approvals/approval-active`,
    async (route) => {
      approvalRequest = route.request().postDataJSON() as Record<
        string,
        unknown
      >;
      approvalState = "consumed";
      await route.fulfill({ json: approval() });
    },
  );
  await page.route(
    `**/api/workspace/workflows/runs/${runId}/history?*`,
    (route) =>
      route.fulfill({
        json: {
          run_id: runId,
          events: [{ sequence: 1, kind: "started", payload: {} }],
        },
      }),
  );
  await page.route(
    `**/api/workspace/workflows/runs/${runId}/evidence?*`,
    (route) => route.fulfill({ status: 404, json: { detail: "pending" } }),
  );
  await page.route(
    `**/api/workspace/workflows/runs/${runId}/cancel`,
    async (route) => {
      cancelRequest = route.request().postDataJSON() as Record<string, unknown>;
      runState = "cancelled";
      await route.fulfill({ json: currentRun() });
    },
  );
  await page.route(`**/api/workspace/workflows/runs/${runId}?*`, (route) =>
    route.fulfill({ json: currentRun() }),
  );

  await page.goto("/workspace/ws-1");
  await page.getByTestId("activity-bar-workflows-btn").click();
  await page.getByTestId("rivet-workflow-run-active-flow").focus();
  await page.keyboard.press("Enter");

  const dialog = page.getByRole("dialog", {
    name: "Approve this exact MCP call?",
  });
  await expect(dialog).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(
    page.getByRole("button", { name: "Approve exact call" }),
  ).toBeFocused();
  await page.keyboard.press("Shift+Tab");
  await expect(dialog.getByRole("button", { name: "Close" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "Review pending call" }),
  ).toBeFocused();
  await page.keyboard.press("Enter");
  await page.getByRole("button", { name: "Approve exact call" }).focus();
  await page.keyboard.press("Enter");
  await expect
    .poll(() => approvalRequest)
    .toMatchObject({
      session_id: "session-1",
      expected_digest: "4".repeat(64),
      decision: "approved",
      actor: "local-user",
    });

  await page.getByRole("button", { name: "Cancel run" }).focus();
  await page.keyboard.press("Enter");
  await expect
    .poll(() => cancelRequest)
    .toMatchObject({
      session_id: "session-1",
      generation: 1,
    });
  await page.getByText("Run evidence", { exact: true }).click();
  const runPanel = page.getByTestId(`rivet-run-${runId}`);
  await expect(runPanel.getByRole("alert")).toContainText(
    "RIVET_MCP_RESIDUE_POSSIBLE",
  );
  await expect(page.locator("body")).not.toContainText("super-secret");
  await page.setViewportSize({ width: 420, height: 800 });
  await page.evaluate(() => {
    document.documentElement.style.zoom = "2";
  });

  const accessibility = await new AxeBuilder({ page })
    .include('[data-testid="rivet-workflows-tab"]')
    .analyze();
  expect(
    accessibility.violations.filter((violation) =>
      ["serious", "critical"].includes(violation.impact || ""),
    ),
  ).toEqual([]);
  await expect(runPanel).toBeVisible();
});
