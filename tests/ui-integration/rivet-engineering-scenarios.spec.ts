import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

import { mockWorkspaceShell } from "./workspace-surfaces/presentation-fixture";

const digest = "d".repeat(64);
const bindingDigest = "b".repeat(64);

const scenario = {
  scenario_id: "structural-bracket",
  revision: 1,
  title: "Structural bracket",
  summary: "Build, weigh, and analyze a bracket.",
  domains: ["cad", "python", "fea"],
  tier: "tier1",
  resource_class: "small",
  expected_duration_seconds: 20,
  manifest_digest: digest,
};

const workflow = {
  workflow_id: "workflow-structural-bracket",
  slug: "structural-bracket",
  revision: 1,
  etag: digest,
  review_state: "approved",
  reviewer: "local-user",
  reviewed_at: 1,
  workflow_digest: digest,
  graph_id: "Main",
  binding_set_id: "binding-set-1",
  binding_set_digest: bindingDigest,
  policy_snapshot_digest: "p".repeat(64),
  review_digest: "r".repeat(64),
  stale_reasons: [],
};

const preflight = (state: "ready" | "blocked") => ({
  preflight_id: `preflight-${state}`,
  scenario_id: scenario.scenario_id,
  scenario_revision: scenario.revision,
  manifest_digest: digest,
  workflow_slug: workflow.slug,
  workflow_revision: workflow.revision,
  workflow_digest: digest,
  graph_id: "Main",
  state,
  tier: "tier1",
  resource_class: "small",
  capabilities: [
    { node_id: "node-cad", selected_tool: "cad__build_bracket", blockers: [] },
    { node_id: "node-fea", selected_tool: "fea__solve_static", blockers: [] },
  ],
  blockers:
    state === "blocked"
      ? [
          {
            code: "capability_missing",
            message: "FEA capability is not enabled in this workspace.",
            recovery: "Enable and validate the FEA MCP, then check again.",
          },
        ]
      : [],
  expires_at: "2099-01-01T00:00:00Z",
});

function report(
  state: "running" | "passed" | "failed" | "cancelled",
  residueAfterCancel = false,
) {
  const hasEngineeringEvidence = state === "passed" || state === "failed";
  return {
    scenario_run_id: "scenario-run-1",
    workflow_run_id: "workflow-run-1",
    workspace_id: "ws-1",
    session_id: "session-1",
    scenario_id: scenario.scenario_id,
    scenario_revision: scenario.revision,
    manifest_digest: digest,
    workflow_digest: digest,
    binding_set_digest: bindingDigest,
    state,
    identity: { seed: 0 },
    environment: { tier: "tier1", network: false },
    artifacts: hasEngineeringEvidence
      ? [
          {
            artifact_id: "fea-result",
            domain: "fea",
            kind: "fea-result",
            content_digest: "a".repeat(64),
            validation_state: "valid",
            producer: {
              node_id: "node-fea",
              capability: "fea__solve_static",
            },
          },
        ]
      : [],
    assertions: hasEngineeringEvidence
      ? [
          {
            assertion_id: "stress-limit",
            plugin: "fea",
            plugin_version: "1.0",
            state: state === "passed" ? "pass" : "fail",
            category: "convergence",
            reason_code:
              state === "passed" ? "stress_within_limit" : "range_exceeded",
            artifact_digests: ["a".repeat(64)],
            producer: {
              node_id: "node-fea",
              capability: "fea__solve_static",
            },
            expected: { maximum: 150, unit: "MPa" },
            observed: {
              value: state === "passed" ? 135 : 175,
              unit: "MPa",
            },
            message:
              state === "passed"
                ? "Peak stress is below the reviewed limit."
                : "Peak stress exceeds the reviewed limit.",
            recovery:
              state === "passed" ? null : "Inspect loads and constraints.",
          },
        ]
      : [],
    cleanup_state:
      state === "running"
        ? "pending"
        : state === "cancelled" && residueAfterCancel
          ? "residue"
          : "clean",
    residue:
      state === "cancelled" && residueAfterCancel
        ? { kinds: ["temporary_file"], recovery: "Inspect before retry." }
        : {},
    accounting: { assertion_count: hasEngineeringEvidence ? 1 : 0 },
    created_at: 1,
    finalized_at: state === "running" ? null : 2,
    report_digest: state === "running" ? null : "e".repeat(64),
  };
}

async function mockScenarioJourney(
  page: Page,
  options: {
    preflightState?: "ready" | "blocked";
    terminal?: "passed" | "failed" | "running";
    cancelResidue?: boolean;
  } = {},
) {
  const preflightState = options.preflightState ?? "ready";
  let currentState: "running" | "passed" | "failed" | "cancelled" =
    options.terminal ?? "passed";
  let exportRequests = 0;

  await page.route("**/api/auth/session/status", (route) =>
    route.fulfill({ json: { auth_required: false, authenticated: true } }),
  );
  await mockWorkspaceShell(page, []);
  await page.route("**/api/workspace/workflow-templates", (route) =>
    route.fulfill({ json: { templates: [] } }),
  );
  await page.route("**/api/workspace/workflows?session_id=*", (route) =>
    route.fulfill({ json: { workflows: [workflow] } }),
  );
  await page.route("**/api/workspace/engineering-scenarios", (route) =>
    route.fulfill({ json: { scenarios: [scenario] } }),
  );
  await page.route(
    "**/api/workspace/engineering-scenarios/structural-bracket/preflight",
    (route) => route.fulfill({ json: preflight(preflightState) }),
  );
  await page.route(
    "**/api/workspace/workflows/structural-bracket/mcp-capabilities?*",
    (route) =>
      route.fulfill({
        json: {
          ...workflow,
          snapshot_digest: "s".repeat(64),
          requirements: [],
          issues: [],
          capabilities: [],
          next_after: null,
        },
      }),
  );
  await page.route(
    "**/api/workspace/engineering-scenarios/structural-bracket/runs",
    (route) =>
      route.fulfill({
        status: 202,
        json: {
          scenario_run_id: "scenario-run-1",
          state: "running",
          workflow_run: { run_id: "workflow-run-1", state: "running" },
        },
      }),
  );
  await page.route(
    "**/api/workspace/engineering-scenarios/runs/scenario-run-1/cancel",
    (route) => {
      currentState = "cancelled";
      return route.fulfill({
        json: { run_id: "workflow-run-1", state: "cancelled" },
      });
    },
  );
  await page.route(
    "**/api/workspace/engineering-scenarios/runs/scenario-run-1/export?*",
    (route) => {
      exportRequests += 1;
      return route.fulfill({
        contentType: "application/json",
        body: JSON.stringify(report(currentState, options.cancelResidue)),
      });
    },
  );
  await page.route(
    "**/api/workspace/engineering-scenarios/runs/scenario-run-1?*",
    (route) =>
      route.fulfill({ json: report(currentState, options.cancelResidue) }),
  );

  await page.goto("/workspace/ws-1");
  await page.getByTestId("activity-bar-workflows-btn").click();
  await expect(page.getByText("Structural bracket")).toBeVisible();
  return { exportRequests: () => exportRequests };
}

test("runs a reviewed multi-MCP scenario and exposes engineering evidence", async ({
  page,
}) => {
  const journey = await mockScenarioJourney(page);
  await page.getByTestId("scenario-preflight-structural-bracket").click();
  await expect(
    page.getByTestId("scenario-preflight-result-structural-bracket"),
  ).toContainText("cad__build_bracket");
  await expect(
    page.getByTestId("scenario-start-structural-bracket"),
  ).toBeEnabled();
  await page.getByTestId("scenario-start-structural-bracket").click();

  const reportPanel = page.getByTestId("scenario-report-scenario-run-1");
  await expect(reportPanel).toContainText("Scenario is passed");
  await expect(reportPanel).toContainText("stress_within_limit");
  await expect(reportPanel).toContainText("135");
  await expect(reportPanel).toContainText("MPa");

  const accessibility = await new AxeBuilder({ page })
    .include('[data-testid="engineering-scenario-library"]')
    .analyze();
  expect(
    accessibility.violations.filter((violation) =>
      ["serious", "critical"].includes(violation.impact || ""),
    ),
  ).toEqual([]);

  await reportPanel.getByRole("button", { name: "Export evidence" }).click();
  await expect.poll(journey.exportRequests).toBe(1);
});

test("blocks an unavailable capability with a recovery action on a narrow screen", async ({
  page,
}) => {
  await mockScenarioJourney(page, { preflightState: "blocked" });
  await page.setViewportSize({ width: 360, height: 800 });
  const check = page.getByTestId("scenario-preflight-structural-bracket");
  await check.focus();
  await expect(check).toBeFocused();
  await check.press("Enter");
  await expect(page.getByRole("alert")).toContainText(
    "Enable and validate the FEA MCP",
  );
  await expect(
    page.getByTestId("scenario-start-structural-bracket"),
  ).toBeDisabled();
  await page.setViewportSize({ width: 640, height: 900 });
  await page.evaluate(() => {
    document.documentElement.style.zoom = "2";
  });
  await expect(page.getByTestId("engineering-scenario-library")).toBeVisible();
});

test("shows a failed engineering invariant with exact recovery", async ({
  page,
}) => {
  await mockScenarioJourney(page, { terminal: "failed" });
  await page.getByTestId("scenario-preflight-structural-bracket").click();
  await page.getByTestId("scenario-start-structural-bracket").click();
  const reportPanel = page.getByTestId("scenario-report-scenario-run-1");
  await expect(reportPanel).toContainText("Scenario is failed");
  await expect(reportPanel).toContainText("range_exceeded");
  await expect(reportPanel).toContainText("175");
  await expect(reportPanel).toContainText("Inspect loads and constraints");
});

test("cancels a running scenario through the existing run boundary", async ({
  page,
}) => {
  await mockScenarioJourney(page, {
    terminal: "running",
    cancelResidue: true,
  });
  await page.getByTestId("scenario-preflight-structural-bracket").click();
  await page.getByTestId("scenario-start-structural-bracket").click();
  const reportPanel = page.getByTestId("scenario-report-scenario-run-1");
  await expect(reportPanel).toContainText("Scenario is running");
  await reportPanel.getByTestId("scenario-cancel-scenario-run-1").click();
  await expect(reportPanel).toContainText("Scenario is cancelled");
  await expect(reportPanel).toContainText("Cleanup: residue");
  await expect(reportPanel.getByRole("alert")).toContainText("temporary_file");
});
