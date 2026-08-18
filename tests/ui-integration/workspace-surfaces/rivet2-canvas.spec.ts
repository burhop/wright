import { expect, test, type Page } from "@playwright/test";

import {
  mockManagedRivetSurface,
  mockWorkspaceShell,
} from "./presentation-fixture";

const workflow = {
  workflow_id: "workflow-rivet",
  slug: "rivet",
  revision: 1,
  digest: "a".repeat(64),
  review_state: null,
  reviewer: null,
  reviewed_at: null,
};

const basicFlowWorkflow = {
  ...workflow,
  workflow_id: "workflow-basic-flow",
  slug: "basic-flow",
  digest: "b".repeat(64),
};

const basicFlowTemplate = {
  template_id: "basic-flow",
  title: "Basic Flow",
  description: "Small input, context, and chat graphs for learning the canvas.",
  kind: "starter",
  requirements: [],
};

const canvasFixture = `<!doctype html>
<html>
  <head>
    <style>
      body { margin: 0; background: #202733; color: white; font: 14px sans-serif; }
      main { min-height: 100vh; padding: 24px; }
      [data-testid="mock-node"] { margin: 32px; padding: 24px; border: 1px solid #38bdf8; }
    </style>
  </head>
  <body>
    <main data-testid="rivet2-graph-canvas" aria-label="Rivet 2 graph canvas">
      <div data-testid="mock-node">Fixture node</div>
      <button data-testid="canvas-add">Add node</button>
      <button data-testid="canvas-select">Select node</button>
      <button data-testid="canvas-move">Move node</button>
      <button data-testid="canvas-connect">Connect nodes</button>
      <button data-testid="canvas-configure">Configure node</button>
      <button data-testid="canvas-duplicate">Duplicate node</button>
      <button data-testid="canvas-delete">Delete node</button>
      <output data-testid="last-action">ready</output>
    </main>
    <script>
      const parentOrigin = new URLSearchParams(location.search).get('parentOrigin');
      let project = '';
      const actions = [];
      const reply = (message) => parent.postMessage(message, parentOrigin);
      for (const button of document.querySelectorAll('button')) {
        button.addEventListener('click', () => {
          const action = button.textContent;
          actions.push(action);
          document.querySelector('[data-testid="last-action"]').textContent = action;
          project = 'version: 4\\nmockActions: ' + JSON.stringify(actions) + '\\n';
        });
      }
      addEventListener('message', (event) => {
        if (event.source !== parent || event.origin !== parentOrigin) return;
        const message = event.data || {};
        if (message.type === 'wright-rivet:set-project') {
          project = String(message.project || '');
          reply({ type: 'wright-rivet:project-set', requestId: message.requestId });
        } else if (message.type === 'wright-rivet:get-project') {
          reply({ type: 'wright-rivet:project', requestId: message.requestId, project });
        }
      });
      setTimeout(
        () => reply({ type: 'wright-rivet:ready', protocolVersion: 2 }),
        100,
      );
    </script>
  </body>
</html>`;

async function mockRivetWorkflow(page: Page) {
  let project = "version: 4\nmetadata:\n  name: rivet\n";
  let revision = 1;
  let savedProject = "";
  let templateCreated = false;
  let reviewState: "approved" | null = null;

  await page.route("**/api/auth/session/status", (route) =>
    route.fulfill({ json: { auth_required: false, authenticated: true } }),
  );
  const managedSurface = await mockManagedRivetSurface(page, canvasFixture);
  await page.route("**/api/workspace/workflow-templates", (route) =>
    route.fulfill({ json: { templates: [basicFlowTemplate] } }),
  );
  await page.route("**/api/workspace/workflows?session_id=*", (route) =>
    route.fulfill({
      json: {
        workflows: [
          { ...workflow, revision, review_state: reviewState },
          ...(templateCreated ? [basicFlowWorkflow] : []),
        ],
      },
    }),
  );
  await page.route("**/api/workspace/workflows/rivet?session_id=*", (route) =>
    route.fulfill({
      json: {
        ...workflow,
        revision,
        project,
        datasets: {},
      },
    }),
  );
  await page.route("**/api/workspace/workflows/rivet", async (route) => {
    const body = route.request().postDataJSON() as { project: string };
    savedProject = body.project;
    project = savedProject;
    revision += 1;
    await route.fulfill({ json: { ...workflow, revision } });
  });
  await page.route("**/api/workspace/workflows/rivet/review", async (route) => {
    reviewState = "approved";
    await route.fulfill({
      json: {
        ...workflow,
        revision,
        review_state: reviewState,
        reviewer: "local-user",
        reviewed_at: Date.now(),
      },
    });
  });
  await page.route("**/api/workspace/workflows/rivet/runs", (route) =>
    route.fulfill({
      json: {
        run_id: "run-1",
        workflow_id: workflow.workflow_id,
        revision,
        digest: workflow.digest,
        graph: null,
        generation: 1,
        state: "running",
        reason: null,
        outputs: null,
        duration_ms: null,
        output_truncated: false,
      },
    }),
  );
  await page.route(
    "**/api/workspace/workflows/runs/run-1?session_id=*",
    (route) =>
      route.fulfill({
        json: {
          run_id: "run-1",
          workflow_id: workflow.workflow_id,
          revision,
          digest: workflow.digest,
          graph: null,
          generation: 1,
          state: "succeeded",
          reason: null,
          outputs: { output: { type: "string", value: "Hello" } },
          duration_ms: 8,
          output_truncated: false,
        },
      }),
  );
  await page.route(
    "**/api/workspace/workflows/runs/run-1/history?session_id=*",
    (route) => route.fulfill({ json: { events: [] } }),
  );
  await page.route(
    "**/api/workspace/workflow-templates/basic-flow/instantiate",
    async (route) => {
      templateCreated = true;
      await route.fulfill({ status: 201, json: basicFlowWorkflow });
    },
  );
  await page.route(
    "**/api/workspace/workflows/basic-flow?session_id=*",
    (route) =>
      route.fulfill({
        json: {
          ...basicFlowWorkflow,
          project: "version: 4\nmetadata:\n  name: basic-flow\n",
          datasets: {},
        },
      }),
  );
  await page.route("**/api/workspace/workflows/basic-flow", async (route) => {
    const body = route.request().postDataJSON() as { project: string };
    savedProject = body.project;
    await route.fulfill({
      json: { ...basicFlowWorkflow, revision: 2 },
    });
  });

  return {
    savedProject: () => savedProject,
    startCount: managedSurface.startCount,
  };
}

test.describe("Rivet 2 retained canvas", () => {
  test("opens a saved workflow file from the explorer in Rivet", async ({
    page,
  }) => {
    await mockWorkspaceShell(page, []);
    const state = await mockRivetWorkflow(page);
    let genericContentRequests = 0;
    await page.route("**/api/workspace/files?*", (route) =>
      route.fulfill({
        json: {
          workspace: {
            name: "apps",
            path: "/",
            type: "directory",
            children: [
              {
                name: "workflows",
                path: "/workflows",
                type: "directory",
                children: [
                  {
                    name: "rivet",
                    path: "/workflows/rivet",
                    type: "directory",
                    children: [
                      {
                        name: "workflow.rivet-project",
                        path: "/workflows/rivet/workflow.rivet-project",
                        type: "file",
                        size: 128,
                      },
                    ],
                  },
                ],
              },
            ],
          },
        },
      }),
    );
    await page.route("**/api/workspace/files/content?*", (route) => {
      genericContentRequests += 1;
      return route.fulfill({ status: 422, json: { detail: "wrong viewer" } });
    });

    await page.goto("/workspace/ws-1");
    const root = page.getByTestId("file-node-/");
    await expect(root).toBeAttached();
    if (!(await root.isVisible())) {
      await page.getByTestId("activity-bar-explorer-btn").click();
    }
    await root.click();
    await page.getByTestId("file-node-/workflows").click();
    await page.getByTestId("file-node-/workflows/rivet").click();
    await page
      .getByTestId("file-node-/workflows/rivet/workflow.rivet-project")
      .dblclick();

    await expect(page.getByTestId("direct-rivet-status")).toContainText(
      "Workflow opened",
      { timeout: 5_000 },
    );
    await expect(page.getByTitle("Rivet graph canvas")).toBeVisible();
    await expect(
      page.getByTestId(
        "editor-tab-/.wright/rivet-workflows/rivet/workflow.rivet-project",
      ),
    ).toContainText("rivet.rivet-project");
    expect(genericContentRequests).toBe(0);
    expect(state.startCount()).toBe(1);
  });

  test("keeps Wright authoritative while exposing only graph-authoring UI", async ({
    page,
  }) => {
    await mockWorkspaceShell(page, []);
    const state = await mockRivetWorkflow(page);
    await page.goto("/workspace/ws-1");
    expect(state.startCount()).toBe(0);

    const startedAt = Date.now();
    await page.getByTestId("activity-bar-workflows-btn").click();
    await expect(page.getByTestId("direct-rivet-status")).toContainText(
      "Workflow opened",
      { timeout: 5_000 },
    );
    expect(state.startCount()).toBe(1);
    expect(Date.now() - startedAt).toBeLessThan(5_000);

    const frame = page.frameLocator('iframe[title="Rivet graph canvas"]');
    await expect(frame.getByTestId("rivet2-graph-canvas")).toBeVisible();
    await expect(frame.getByTestId("mock-node")).toBeVisible();

    const toolbar = page.getByTestId("direct-rivet-toolbar");
    await expect(toolbar.getByText("rivet.rivet-project")).toHaveCount(0);
    await expect(
      toolbar.getByLabel("Rivet workflow", { exact: true }),
    ).toHaveCount(0);
    await expect(
      toolbar.getByLabel("Open Rivet workflow from workspace"),
    ).toHaveCount(0);

    await page.getByTestId("direct-rivet-run").click();
    const runPanel = page.getByTestId("direct-rivet-run-panel");
    await expect(runPanel).toHaveCSS("background-color", "rgb(24, 34, 56)");
    await expect(page.getByTestId("direct-rivet-review-state")).toContainText(
      "needs approval",
    );
    await expect(page.getByTestId("direct-rivet-run-start")).toBeDisabled();
    await page.getByTestId("direct-rivet-run-approve").click();
    await expect(page.getByTestId("direct-rivet-run-start")).toBeEnabled();
    await page.getByTestId("direct-rivet-run-start").click();
    await expect(page.getByTestId("direct-rivet-run-feedback")).toContainText(
      'Run succeeded in 8 ms. Output: output: "Hello"',
    );

    await toolbar.getByTestId("direct-rivet-template-picker").click();
    await expect(page.getByText("Basic Flow", { exact: true })).toBeVisible();
    await page.getByTestId("direct-rivet-template-basic-flow").click();
    await expect(
      page.getByTestId(
        "editor-tab-/.wright/rivet-workflows/basic-flow/workflow.rivet-project",
      ),
    ).toContainText("basic-flow.rivet-project");

    for (const action of [
      "add",
      "select",
      "move",
      "connect",
      "configure",
      "duplicate",
      "delete",
    ]) {
      await frame.getByTestId(`canvas-${action}`).click();
    }
    await expect(frame.getByTestId("last-action")).toHaveText("Delete node");

    for (const disallowedSurface of [
      "rivet-project-tabs",
      "rivet-file-menu",
      "rivet-project-sidebar",
      "rivet-action-bar",
      "rivet-status-bar",
      "rivet-settings",
      "rivet-help",
      "rivet-prompt-designer",
      "rivet-trivet",
      "rivet-chat-viewer",
      "rivet-data-studio",
      "rivet-web-app-builder",
    ]) {
      await expect(frame.getByTestId(disallowedSurface)).toHaveCount(0);
    }

    await page.getByTestId("direct-rivet-save-workspace").click();
    await expect.poll(state.savedProject).toContain("Delete node");
    await expect(page.getByTestId("direct-rivet-lint")).toBeVisible();
    await expect(page.getByTestId("direct-rivet-run")).toBeVisible();
  });
});
