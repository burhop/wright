import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

import { mockWorkspaceShell } from "./workspace-surfaces/presentation-fixture";

const digest = "d".repeat(64);
const bindingDigest = "b".repeat(64);

const scenario = {
  scenario_id: "chatter-candidate-review",
  revision: 1,
  title: "Chatter candidate review",
  summary: "Compare discrete simulated candidates with a local model.",
  domains: ["cad", "cam", "python"],
  tier: "tier1",
  resource_class: "small",
  expected_duration_seconds: 25,
  manifest_digest: digest,
};

const workflow = {
  workflow_id: "workflow-chatter",
  slug: "chatter-candidate-review",
  revision: 1,
  etag: digest,
  review_state: "approved",
  reviewer: "local-user",
  reviewed_at: 1,
  workflow_digest: digest,
  graph_id: "graph-chatter-review",
  binding_set_id: "binding-set-chatter",
  binding_set_digest: bindingDigest,
  policy_snapshot_digest: "p".repeat(64),
  review_digest: "r".repeat(64),
  stale_reasons: [],
};

function provider(kind: "mcp" | "engineering_model", id: string) {
  return {
    schema_version: "1.0",
    provider_kind: kind,
    provider_id: id,
    capability_id: "fixture-capability",
    resource_class: kind === "mcp" ? "small" : "medium",
    evidence: {},
  };
}

function preflight(blocked = false) {
  return {
    preflight_id: "preflight-chatter",
    scenario_id: scenario.scenario_id,
    scenario_revision: 1,
    manifest_digest: digest,
    workflow_slug: workflow.slug,
    workflow_revision: 1,
    workflow_digest: digest,
    graph_id: "graph-chatter-review",
    binding_set_digest: blocked ? null : bindingDigest,
    state: blocked ? "blocked" : "ready",
    tier: "tier1",
    resource_class: "small",
    capabilities: [
      {
        node_id: "node-cad-context",
        requested_tool: "fixture_cad__inspect_setup",
        selected_tool: "fixture_cad__inspect_setup",
        binding_digest: "1".repeat(64),
        provider: provider("mcp", "fixture-cad"),
        provider_evidence_digest: "2".repeat(64),
        blockers: [],
      },
      {
        node_id: "node-cam-candidates",
        requested_tool: "fixture_cam__generate_candidates",
        selected_tool: "fixture_cam__generate_candidates",
        binding_digest: "3".repeat(64),
        provider: provider("mcp", "fixture-cam"),
        provider_evidence_digest: "4".repeat(64),
        blockers: [],
      },
      {
        node_id: "node-chatter-model",
        requested_tool:
          "wright_model__wright_chatter_generated_test__screen_chatter_candidates",
        selected_tool:
          "wright_model__wright_chatter_generated_test__screen_chatter_candidates",
        binding_digest: "5".repeat(64),
        provider: provider(
          "engineering_model",
          "wright-chatter-generated-test",
        ),
        provider_evidence_digest: "6".repeat(64),
        blockers: blocked ? ["resource_reservation_unavailable"] : [],
      },
    ],
    environment: {
      tier: "tier1",
      network: false,
      credentials: false,
      physical_actuation: false,
      simulation_only: true,
    },
    blockers: blocked
      ? [
          {
            code: "scenario_model_resource_unavailable",
            message: "The reviewed model RAM reservation is unavailable.",
            recovery:
              "Close another model run, inspect cleanup, and run a fresh preflight.",
          },
        ]
      : [],
    expires_at: "2099-01-01T00:00:00Z",
  };
}

const report = {
  scenario_run_id: "scenario-run-chatter",
  workflow_run_id: "workflow-run-chatter",
  workspace_id: "ws-1",
  session_id: "session-1",
  scenario_id: scenario.scenario_id,
  scenario_revision: 1,
  manifest_digest: digest,
  workflow_digest: digest,
  binding_set_digest: bindingDigest,
  state: "passed",
  identity: { seed: 0 },
  environment: { tier: "tier1", simulation_only: true },
  artifacts: [
    {
      artifact_id: "chatter-advisory",
      domain: "cam",
      kind: "chatter-advisory-report",
      content_digest: "a".repeat(64),
      validation_state: "valid",
      producer: {
        node_id: "node-advisory",
        capability: "fixture_report__compose_advisory",
      },
    },
  ],
  assertions: [
    {
      assertion_id: "advisory-safe-and-correlated",
      plugin: "chatter_advisory",
      state: "pass",
      reason_code: "chatter_advisory_valid",
      artifact_digests: ["a".repeat(64)],
      producer: {
        node_id: "node-advisory",
        capability: "fixture_report__compose_advisory",
      },
    },
  ],
  cleanup_state: "clean",
  residue: {},
  advisory: {
    schema_version: "1.0",
    simulation_only: true,
    machine_authority: false,
    score_semantics: "uncalibrated_screening_score",
    selected_candidate_id: "candidate-stable",
    candidate_outcomes: [
      {
        candidate_id: "candidate-stable",
        review_status: "selected_for_review",
        reason: "Lowest eligible uncalibrated score.",
        chatter_score: 0.1,
        threshold_margin: -0.4,
        applicability: "in_population",
      },
      {
        candidate_id: "candidate-threshold",
        review_status: "rejected",
        reason: "Near threshold; human investigation required.",
        chatter_score: 0.5,
        threshold_margin: 0,
        applicability: "near_threshold",
      },
    ],
    notices: [
      "Simulation only.",
      "Human engineering review is required.",
      "No machine authority or executable instructions.",
    ],
    provider_evidence: [
      { provider_kind: "mcp", provider_id: "fixture-cad" },
      { provider_kind: "mcp", provider_id: "fixture-cam" },
      {
        provider_kind: "engineering_model",
        provider_id: "wright-chatter-generated-test",
      },
    ],
  },
  report_digest: "e".repeat(64),
};

async function mockJourney(page: Page, blocked = false) {
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
    "**/api/workspace/engineering-scenarios/chatter-candidate-review/preflight",
    (route) => route.fulfill({ json: preflight(blocked) }),
  );
  await page.route(
    "**/api/workspace/workflows/chatter-candidate-review/mcp-capabilities?*",
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
    "**/api/workspace/engineering-scenarios/chatter-candidate-review/runs",
    (route) =>
      route.fulfill({
        status: 202,
        json: {
          scenario_run_id: report.scenario_run_id,
          state: "running",
          workflow_run: { run_id: report.workflow_run_id, state: "running" },
        },
      }),
  );
  await page.route(
    `**/api/workspace/engineering-scenarios/runs/${report.scenario_run_id}?*`,
    (route) => route.fulfill({ json: report }),
  );
  await page.goto("/workspace/ws-1");
  await page.getByTestId("activity-bar-workflows-btn").click();
}

test("reviews MCP and model providers and shows a non-actuating Chatter advisory", async ({
  page,
}) => {
  await mockJourney(page);
  await page.setViewportSize({ width: 320, height: 850 });
  const check = page.getByTestId("scenario-preflight-chatter-candidate-review");
  await check.focus();
  await expect(check).toBeFocused();
  await check.press("Enter");
  const preflightPanel = page.getByTestId(
    "scenario-preflight-result-chatter-candidate-review",
  );
  await expect(preflightPanel).toContainText("fixture-cad");
  await expect(preflightPanel).toContainText("fixture-cam");
  await expect(preflightPanel).toContainText("local engineering model");
  await page.getByTestId("scenario-start-chatter-candidate-review").click();
  const panel = page.getByTestId(`scenario-report-${report.scenario_run_id}`);
  await expect(panel).toContainText("selected for review");
  await expect(panel).toContainText("Uncalibrated score 0.1");
  await expect(panel).toContainText("Machine authority: no");
  await expect(panel).toContainText("not probabilities");
  await page.evaluate(() => {
    document.documentElement.style.zoom = "2";
  });
  await expect(panel).toBeVisible();
  const accessibility = await new AxeBuilder({ page })
    .include('[data-testid="engineering-scenario-library"]')
    .analyze();
  expect(
    accessibility.violations.filter((violation) =>
      ["serious", "critical"].includes(violation.impact || ""),
    ),
  ).toEqual([]);
});

test("keeps start disabled when the model resource reservation is blocked", async ({
  page,
}) => {
  await mockJourney(page, true);
  await page.getByTestId("scenario-preflight-chatter-candidate-review").click();
  await expect(page.getByRole("alert")).toContainText("fresh preflight");
  await expect(
    page.getByTestId("scenario-start-chatter-candidate-review"),
  ).toBeDisabled();
});
