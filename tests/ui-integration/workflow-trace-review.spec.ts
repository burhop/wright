import { mkdirSync } from "node:fs";
import { resolve } from "node:path";

import { expect, test } from "@playwright/test";

import { succeededInspection } from "../../apps/web/src/components/workflows/rivet-run-inspector.fixtures";
import {
  mockRecoveryWorkspace,
  openRecoveryEditor,
} from "./fixtures/workflow-recovery";

const evidenceDir = resolve(
  process.cwd(),
  "specs/083-workflow-trace-review/evidence",
);

test("reviews a completed run from the normal Workflows entry", async ({
  page,
}) => {
  await mockRecoveryWorkspace(page);
  const graphInspection = {
    ...succeededInspection,
    run: {
      ...succeededInspection.run,
      run_id: "canonical-run-1",
      workflow_id: "workflows/mounting-bracket.workflow.wflow",
    },
    graph: {
      graph_id: "canonical",
      name: "Mounting bracket development",
      nodes: [
        {
          node_id: "node-1",
          node_type: "mcpToolCall",
          label: "Inspect CAD",
          order: 1,
          x: 0,
          y: 0,
          width: 220,
          prompt: "Inspect the retained bracket model.",
          configuration: { tool: "cad.inspect" },
        },
      ],
      connections: [],
    },
  };
  await page.route("**/api/workspace/workflow-sources/runs?**", (route) =>
    route.fulfill({
      json: {
        workspace_id: "ws-recovery",
        workflow_path: "workflows/mounting-bracket.workflow.wflow",
        runs: [
          {
            path: "runs/mounting-bracket/completed.json",
            status: "completed",
            started_at: "2026-09-16T14:00:00Z",
            completed_at: "2026-09-16T14:01:00Z",
            source_digest: "a".repeat(64),
            results: [],
          },
        ],
      },
    }),
  );
  await page.route("**/api/workspace/workflow-sources/run-trace?**", (route) =>
    route.fulfill({ json: graphInspection }),
  );

  await openRecoveryEditor(page);
  await page.getByTestId("workflow-recovery-run-details-toggle").click();
  await page.getByText("Previous runs", { exact: true }).click();
  await page.getByText(/Completed/).click();
  const tracePage = page.getByTestId("workflow-trace-page");
  await expect(tracePage).toBeVisible();
  await expect(page.getByRole("region", { name: "Run results" })).toBeVisible();
  await expect(page.getByText("Created artifacts")).toBeVisible();

  await tracePage.getByRole("button", { name: "Process", exact: true }).click();
  const graph = page.getByLabel("Executed graph Mounting bracket development");
  await expect(graph).toBeVisible();
  await expect(graph.locator(".react-flow__node")).toHaveCount(1);
  await graph.locator(".react-flow__node").click();
  await expect(
    page.getByRole("complementary", { name: "Selected process detail" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Close process detail" }).click();
  await tracePage.getByRole("button", { name: "Results", exact: true }).click();
  await expect(page.getByRole("region", { name: "Run results" })).toBeVisible();

  mkdirSync(evidenceDir, { recursive: true });
  await tracePage.screenshot({
    path: resolve(evidenceDir, "trace-workspace-desktop.png"),
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page
    .getByRole("navigation", { name: "Workspace pane" })
    .getByRole("button", { name: "Surface", exact: true })
    .click();
  await expect(tracePage).toBeInViewport();
  expect((await tracePage.boundingBox())?.width).toBeLessThanOrEqual(390);
  await tracePage.screenshot({
    path: resolve(evidenceDir, "trace-workspace-mobile.png"),
  });
  await page.evaluate(() => {
    document.documentElement.style.fontSize = "200%";
  });
  await expect(tracePage).toBeVisible();
  await tracePage.screenshot({
    path: resolve(evidenceDir, "trace-workspace-text-200.png"),
  });
});
