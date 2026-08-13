import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

import { mockWorkspaceShell } from "./workspace-surfaces/presentation-fixture";

const digest = "d".repeat(64);
const bindingDigest = "b".repeat(64);

export type JourneyKind = "mcp-only" | "mcp-model";

export function identities(kind: JourneyKind) {
  const id = kind === "mcp-only" ? "structural-bracket" : "chatter-review";
  return {
    scenario: {
      scenario_id: id,
      revision: 1,
      title:
        kind === "mcp-only"
          ? "Structural bracket MCP review"
          : "Chatter MCP and local-model review",
      summary:
        kind === "mcp-only"
          ? "Build and assess a static bracket with reviewed MCP fixtures."
          : "Compare static CAM candidates with a reviewed local model fixture.",
      domains: kind === "mcp-only" ? ["cad", "fea"] : ["cad", "cam", "python"],
      tier: "tier1",
      resource_class: "small",
      expected_duration_seconds: 25,
      manifest_digest: digest,
    },
    workflow: {
      workflow_id: `workflow-${id}`,
      slug: id,
      revision: 1,
      etag: digest,
      review_state: "approved",
      reviewer: "local-user",
      reviewed_at: 1,
      workflow_digest: digest,
      graph_id: "Main",
      binding_set_id: `binding-${id}`,
      binding_set_digest: bindingDigest,
      policy_snapshot_digest: "p".repeat(64),
      review_digest: "r".repeat(64),
      stale_reasons: [],
    },
    runId: `scenario-run-${id}`,
  };
}

function provider(kind: "mcp" | "engineering_model", id: string) {
  return {
    schema_version: "1.0",
    provider_kind: kind,
    provider_id: id,
    capability_id: `${id}-capability`,
    resource_class: "small",
    evidence: {},
  };
}

export async function mockJourney(page: Page, kind: JourneyKind) {
  const fixture = identities(kind);
  let diagnosticExports = 0;
  await page.route("**/api/auth/session/status", (route) =>
    route.fulfill({ json: { auth_required: false, authenticated: true } }),
  );
  await mockWorkspaceShell(page, []);
  await page.route("**/api/workspace/workflow-templates", (route) =>
    route.fulfill({ json: { templates: [] } }),
  );
  await page.route("**/api/workspace/workflows?session_id=*", (route) =>
    route.fulfill({ json: { workflows: [fixture.workflow] } }),
  );
  await page.route("**/api/workspace/engineering-scenarios", (route) =>
    route.fulfill({ json: { scenarios: [fixture.scenario] } }),
  );
  await page.route(
    `**/api/workspace/engineering-scenarios/${fixture.scenario.scenario_id}/preflight`,
    (route) =>
      route.fulfill({
        json: {
          preflight_id: `preflight-${kind}`,
          scenario_id: fixture.scenario.scenario_id,
          scenario_revision: 1,
          manifest_digest: digest,
          workflow_slug: fixture.workflow.slug,
          workflow_revision: 1,
          workflow_digest: digest,
          graph_id: "Main",
          binding_set_digest: bindingDigest,
          state: "ready",
          capabilities: [
            {
              node_id: "node-cad",
              requested_tool: "fixture_cad__inspect",
              selected_tool: "fixture_cad__inspect",
              binding_digest: "1".repeat(64),
              blockers: [],
              provider: provider("mcp", "fixture-cad"),
              provider_evidence_digest: "2".repeat(64),
            },
            {
              node_id: kind === "mcp-only" ? "node-fea" : "node-cam",
              requested_tool:
                kind === "mcp-only"
                  ? "fixture_fea__solve"
                  : "fixture_cam__candidates",
              selected_tool:
                kind === "mcp-only"
                  ? "fixture_fea__solve"
                  : "fixture_cam__candidates",
              binding_digest: "3".repeat(64),
              blockers: [],
              provider: provider(
                "mcp",
                kind === "mcp-only" ? "fixture-fea" : "fixture-cam",
              ),
              provider_evidence_digest: "4".repeat(64),
            },
            ...(kind === "mcp-model"
              ? [
                  {
                    node_id: "node-model",
                    requested_tool: "wright_model__chatter__screen",
                    selected_tool: "wright_model__chatter__screen",
                    binding_digest: "5".repeat(64),
                    blockers: [],
                    provider: provider("engineering_model", "fixture-chatter"),
                    provider_evidence_digest: "6".repeat(64),
                  },
                ]
              : []),
          ],
          environment: {
            tier: "tier1",
            network: false,
            physical_actuation: false,
          },
          blockers: [],
          expires_at: "2099-01-01T00:00:00Z",
        },
      }),
  );
  await page.route(
    `**/api/workspace/workflows/${fixture.workflow.slug}/mcp-capabilities?*`,
    (route) =>
      route.fulfill({
        json: {
          ...fixture.workflow,
          snapshot_digest: "s".repeat(64),
          requirements: [],
          issues: [],
          capabilities: [],
          next_after: null,
        },
      }),
  );
  await page.route(
    `**/api/workspace/engineering-scenarios/${fixture.scenario.scenario_id}/runs`,
    (route) =>
      route.fulfill({
        status: 202,
        json: {
          scenario_run_id: fixture.runId,
          state: "running",
          workflow_run: { run_id: `workflow-run-${kind}`, state: "running" },
        },
      }),
  );
  const report = {
    scenario_run_id: fixture.runId,
    workflow_run_id: `workflow-run-${kind}`,
    workspace_id: "ws-1",
    session_id: "session-1",
    scenario_id: fixture.scenario.scenario_id,
    scenario_revision: 1,
    manifest_digest: digest,
    workflow_digest: digest,
    binding_set_digest: bindingDigest,
    state: "passed",
    identity: { seed: 0 },
    environment: { tier: "tier1", physical_actuation: false },
    artifacts: [
      {
        artifact_id: `evidence-${kind}`,
        domain: kind === "mcp-only" ? "fea" : "cam",
        kind: kind === "mcp-only" ? "fea-result" : "chatter-advisory-report",
        content_digest: "a".repeat(64),
        validation_state: "valid",
        producer: {
          run_id: `workflow-run-${kind}`,
          node_id: kind === "mcp-only" ? "node-fea" : "node-model",
          call_id: "call-1",
          capability:
            kind === "mcp-only"
              ? "fixture_fea__solve"
              : "wright_model__chatter__screen",
        },
      },
    ],
    assertions: [
      {
        assertion_id: "engineering-boundary",
        plugin: "fixture",
        state: "pass",
        reason_code: "reviewed_boundary_satisfied",
        artifact_digests: ["a".repeat(64)],
        expected: { maximum: 150, unit: "MPa" },
        observed: { value: 135, unit: "MPa" },
        producer: {
          node_id: kind === "mcp-only" ? "node-fea" : "node-model",
          capability:
            kind === "mcp-only"
              ? "fixture_fea__solve"
              : "wright_model__chatter__screen",
        },
      },
    ],
    cleanup_state: "clean",
    residue: {},
    report_digest: "e".repeat(64),
  };
  await page.route(
    `**/api/workspace/engineering-scenarios/runs/${fixture.runId}?*`,
    (route) => route.fulfill({ json: report }),
  );
  await page.route("**/api/workspace/support-diagnostics/preview", (route) =>
    route.fulfill({
      json: {
        snapshot: {
          schema_version: "1.0",
          snapshot_id: "snapshot_12345678",
          created_at: "2026-08-13T12:00:00Z",
          expires_at: "2099-08-13T12:05:00Z",
          workspace_id: "ws-1",
          principal_digest: `sha256:${"1".repeat(64)}`,
          scope: { session_id: "session-1", scenario_run_id: fixture.runId },
          summary: {
            status: "healthy",
            reason: "READY",
            next_action: "REVIEW",
          },
          providers: [],
          state_inventory: {
            schema_version: "1.0",
            data_schema: 16,
            catalog_snapshot: {
              channel: "bundled",
              sequence: 0,
              digest: `sha256:${"2".repeat(64)}`,
              state: "bundled",
            },
            counts: { scenario_reports: 1 },
            digests: { program_material: `sha256:${"3".repeat(64)}` },
            storage: [],
          },
          failures: [],
          categories: [
            {
              name: "program-state",
              disposition: "included",
              item_count: 1,
              reason: "INCLUDED",
            },
            {
              name: "raw-engineering-payloads",
              disposition: "omitted",
              item_count: 0,
              reason: "PROPRIETARY_CONTENT_FORBIDDEN",
            },
          ],
          snapshot_digest: `sha256:${"4".repeat(64)}`,
        },
        snapshot_digest: `sha256:${"4".repeat(64)}`,
        confirmation_token: "one-use-confirmation",
        expires_at: "2099-08-13T12:05:00Z",
        filename: `wright-support-${kind}.json`,
      },
    }),
  );
  await page.route("**/api/workspace/support-diagnostics/export", (route) => {
    diagnosticExports += 1;
    return route.fulfill({
      contentType: "application/json",
      headers: {
        "Content-Disposition": `attachment; filename=wright-support-${kind}.json`,
      },
      body: JSON.stringify({ schema_version: "1.0", kind }),
    });
  });
  return { fixture, diagnosticExports: () => diagnosticExports };
}

for (const kind of ["mcp-only", "mcp-model"] as const) {
  test(`${kind} engineering journey stays within the explicit interaction and time budget`, async ({
    page,
  }) => {
    const started = Date.now();
    let primaryInteractions = 0;
    const journey = await mockJourney(page, kind);
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("/workspace/ws-1");
    await page.getByTestId("activity-bar-workflows-btn").focus();
    await page.keyboard.press("Enter");
    primaryInteractions += 1;
    await page.setViewportSize({ width: 320, height: 850 });
    const check = page.getByTestId(
      `scenario-preflight-${journey.fixture.scenario.scenario_id}`,
    );
    await check.focus();
    await page.keyboard.press("Enter");
    primaryInteractions += 1;
    await expect(
      page.getByTestId(
        `scenario-preflight-result-${journey.fixture.scenario.scenario_id}`,
      ),
    ).toContainText(
      kind === "mcp-only" ? "fixture-fea" : "local engineering model",
    );
    const start = page.getByTestId(
      `scenario-start-${journey.fixture.scenario.scenario_id}`,
    );
    await start.focus();
    await page.keyboard.press("Enter");
    primaryInteractions += 1;
    const report = page.getByTestId(`scenario-report-${journey.fixture.runId}`);
    await expect(report).toContainText("Scenario is passed");
    await expect(report).toContainText("Material engineering evidence");
    await expect(report).toContainText("Observed assertion results");
    await expect(report.getByTestId("scenario-phase-summary")).toBeFocused();

    await report.getByTestId("support-diagnostics-preview").focus();
    await page.keyboard.press("Enter");
    primaryInteractions += 1;
    await expect(report).toContainText("raw engineering payloads: omitted");
    await report.getByTestId("support-diagnostics-confirm").focus();
    await page.keyboard.press("Space");
    primaryInteractions += 1;
    await report.getByTestId("support-diagnostics-export").focus();
    await page.keyboard.press("Enter");
    primaryInteractions += 1;
    await expect.poll(journey.diagnosticExports).toBe(1);
    await expect(report).toContainText("Nothing is uploaded automatically");

    await page.evaluate(() => {
      document.documentElement.style.zoom = "2";
    });
    await expect(report).toBeVisible();
    const accessibility = await new AxeBuilder({ page })
      .include('[data-testid="engineering-scenario-library"]')
      .analyze();
    expect(
      accessibility.violations.filter((violation) =>
        ["serious", "critical"].includes(violation.impact || ""),
      ),
    ).toEqual([]);
    expect(primaryInteractions).toBeLessThanOrEqual(20);
    expect(Date.now() - started).toBeLessThan(5 * 60 * 1000);
  });
}
