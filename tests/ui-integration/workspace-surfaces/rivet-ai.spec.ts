import { expect, test, type Page } from "@playwright/test";

import { mockWorkspaceShell } from "./presentation-fixture";

const digest = "a".repeat(64);
const baseProject = "version: 4\ndata:\n  graphs: {}\n";

const canvasFixture = (aiAvailable: boolean) => `<!doctype html>
<html>
  <body style="margin:0;background:#202733;color:white;font:14px sans-serif">
    <main data-testid="rivet2-graph-canvas" style="min-height:100vh;padding:24px">
      <button data-testid="rivet-sparkle" ${aiAvailable ? "" : "disabled"}>Sparkle</button>
      <output data-testid="project-summary">Base graph</output>
    </main>
    <script>
      const parentOrigin = new URLSearchParams(location.search).get('parentOrigin');
      let project = '';
      const reply = (message) => parent.postMessage(message, parentOrigin);
      const summary = document.querySelector('[data-testid="project-summary"]');
      document.querySelector('[data-testid="rivet-sparkle"]').addEventListener('click', () => {
        project = 'version: 4\\ndata:\\n  aiGenerated: true\\n';
        summary.textContent = 'AI graph applied';
      });
      addEventListener('message', (event) => {
        if (event.source !== parent || event.origin !== parentOrigin) return;
        const message = event.data || {};
        if (message.type === 'wright-rivet:set-project') {
          project = String(message.project || '');
          summary.textContent = project.includes('aiGenerated') ? 'AI graph applied' : 'Base graph';
          reply({ type: 'wright-rivet:project-set', requestId: message.requestId });
        } else if (message.type === 'wright-rivet:get-project') {
          reply({ type: 'wright-rivet:project', requestId: message.requestId, project });
        }
      });
      setTimeout(() => {
        reply({ type: 'wright-rivet:ready', protocolVersion: 2 });
        reply({ type: 'wright-rivet:ai-status', available: ${String(aiAvailable)} });
      }, 50);
    </script>
  </body>
</html>`;

interface MockState {
  savedProject: () => string;
  runRequest: () => Record<string, unknown> | null;
}

async function mockAiWorkflow(
  page: Page,
  options: { aiAvailable?: boolean; run?: boolean } = {},
): Promise<MockState> {
  let project = baseProject;
  let revision = 1;
  let requestedRun: Record<string, unknown> | null = null;
  let runPolls = 0;
  const operation = () => ({
    workflow_id: "workflow-ai",
    slug: "ai-agent",
    revision,
    etag: digest,
    review_state: "approved",
    reviewer: "wright",
    reviewed_at: 1,
  });
  const run = (state: "running" | "succeeded") => ({
    run_id: "run-ai",
    workflow_id: "workflow-ai",
    revision,
    digest,
    graph: "AI Chat",
    generation: 1,
    state,
    reason: null,
    outputs:
      state === "succeeded"
        ? { output: { type: "string", value: "AI through Hermes" } }
        : null,
    duration_ms: state === "succeeded" ? 123 : null,
    output_truncated: false,
  });

  await page.route("**/api/auth/session/status", (route) =>
    route.fulfill({ json: { auth_required: false, authenticated: true } }),
  );
  await page.route(/^http:\/\/(?:localhost|127\.0\.0\.1):9180\//, (route) =>
    route.fulfill({
      contentType: "text/html",
      body: canvasFixture(options.aiAvailable !== false),
    }),
  );
  await page.route("**/api/workspace/workflow-templates", (route) =>
    route.fulfill({ json: { templates: [] } }),
  );
  await page.route("**/api/workspace/workflows?session_id=*", (route) =>
    route.fulfill({ json: { workflows: [operation()] } }),
  );
  await page.route("**/api/workspace/workflows/ai-agent?session_id=*", (route) =>
    route.fulfill({
      json: { ...operation(), project, datasets: {} },
    }),
  );
  await page.route("**/api/workspace/workflows/ai-agent", async (route) => {
    const body = route.request().postDataJSON() as { project: string };
    project = body.project;
    revision += 1;
    await route.fulfill({ json: operation() });
  });

  if (options.run) {
    await page.route("**/api/workspace/workflows/ai-agent/runs", async (route) => {
      requestedRun = route.request().postDataJSON() as Record<string, unknown>;
      await route.fulfill({ status: 202, json: run("running") });
    });
    await page.route("**/api/workspace/workflows/runs/run-ai?session_id=*", (route) => {
      runPolls += 1;
      route.fulfill({ json: run(runPolls > 1 ? "succeeded" : "running") });
    });
    await page.route(
      "**/api/workspace/workflows/runs/run-ai/history?session_id=*",
      (route) =>
        route.fulfill({
          json: {
            events: [
              {
                sequence: 1,
                kind: "progress",
                payload: { phase: "executing-graph" },
              },
            ],
          },
        }),
    );
  }

  return {
    savedProject: () => project,
    runRequest: () => requestedRun,
  };
}

async function openRivet(page: Page) {
  await page.goto("/workspace/ws-1");
  await page.getByTestId("activity-bar-workflows-btn").click();
  await expect(page.getByTestId("direct-rivet-status")).toContainText(
    "Workflow opened",
  );
  return page.frameLocator('iframe[title="Rivet graph canvas"]');
}

test.describe("Rivet Hermes AI", () => {
  test("generates, applies, saves, and reloads a sparkle result", async ({ page }) => {
    await mockWorkspaceShell(page, []);
    const state = await mockAiWorkflow(page);
    let frame = await openRivet(page);

    await expect(page.getByTestId("direct-rivet-ai-status")).toHaveAttribute(
      "aria-label",
      "Rivet AI connected",
    );
    await frame.getByTestId("rivet-sparkle").click();
    await expect(frame.getByTestId("project-summary")).toHaveText(
      "AI graph applied",
    );
    await page.getByTestId("direct-rivet-save-workspace").click();
    await expect.poll(state.savedProject).toContain("aiGenerated");

    await page.reload();
    frame = await openRivet(page);
    await expect(frame.getByTestId("project-summary")).toHaveText(
      "AI graph applied",
    );
  });

  test("keeps the canvas usable when Hermes is unavailable", async ({ page }) => {
    await mockWorkspaceShell(page, []);
    await mockAiWorkflow(page, { aiAvailable: false });
    const frame = await openRivet(page);

    await expect(page.getByTestId("direct-rivet-ai-status")).toHaveAttribute(
      "aria-label",
      "Rivet AI unavailable",
    );
    await expect(frame.getByTestId("rivet2-graph-canvas")).toBeVisible();
    await expect(frame.getByTestId("rivet-sparkle")).toBeDisabled();
    await expect(frame.getByText(/API key|provider/i)).toHaveCount(0);
  });

  test("shows correlated canvas-run progress and terminal output", async ({ page }) => {
    await mockWorkspaceShell(page, []);
    const state = await mockAiWorkflow(page, { run: true });
    await openRivet(page);

    await page.getByTestId("direct-rivet-run").click();
    await page.getByTestId("direct-rivet-run-graph").fill("AI Chat");
    await page
      .getByTestId("direct-rivet-run-inputs")
      .fill('{"prompt":"Say hello"}');
    await page.getByTestId("direct-rivet-run-start").click();

    await expect(page.getByTestId("direct-rivet-status")).toContainText(
      /executing graph|succeeded/,
    );
    await expect(page.getByTestId("direct-rivet-run-result")).toHaveAttribute(
      "title",
      /AI through Hermes/,
    );
    expect(state.runRequest()).toMatchObject({
      expected_revision: 1,
      expected_digest: digest,
      graph: "AI Chat",
      inputs: { prompt: "Say hello" },
    });
  });
});
