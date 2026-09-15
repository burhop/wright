// Read-only live workspace acceptance: no workflow starts, edits or approval writes.
import { chromium, expect } from "@playwright/test";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const evidence = path.join(root, ".local-run/feature-081-live/campaign-workspace-evidence");
await fs.mkdir(evidence, { recursive: true });
const workspace = "c33593b1-73a8-4056-a7f4-a07a9903dd2d";
const workflow = "workflows/campaign-robot-tracking-diagnosis-01-attempt-003.workflow.wflow";
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1600, height: 1050 } });
const errors = [];
page.on("pageerror", error => errors.push(error.message));
try {
  await page.goto("http://127.0.0.1:5173/workspace/" + workspace);
  await page.getByTestId("activity-bar-workflows-btn").click();
  await expect(page.getByTestId("workflow-recovery-canvas")).toBeVisible({ timeout: 30000 });
  await page.getByTestId("workflow-file-menu").click();
  await page.getByTestId("workflow-start-template").click();
  await expect(page.getByTestId("workflow-template-list").getByRole("option")).toHaveCount(10);
  await page.screenshot({ path: path.join(evidence, "templates.png") });
  await page.getByTestId("workflow-template-cancel").click();
  await page.getByTestId("workflow-file-menu").click();
  await page.getByTestId("workflow-file-open").click();
  await page.getByTestId("workflow-file-choice-" + workflow).click();
  const activeWorkflow = page.getByRole("region", {
    name: "Engineering Workflow Demos workflow " + workflow, exact: true,
  });
  await expect(activeWorkflow.getByTestId("workflow-recovery-canvas")).toBeVisible();
  await expect(activeWorkflow.getByRole("alert")).toHaveCount(0);
  await expect(page).toHaveURL(new RegExp("workflowPath=" + encodeURIComponent(workflow)));
  await expect(activeWorkflow.getByTestId("workflow-recovery-save")).toBeVisible();
  await activeWorkflow.getByTestId("workflow-recovery-view-code").click();
  const source = activeWorkflow.getByTestId("workflow-recovery-source-editor");
  await expect(source).toHaveValue(/robot-tracking-diagnosis|Robot/);
  await expect(source).toHaveValue(/\n\s+instructions:/);
  await expect(source).toHaveValue(/\n\s+prompt:/);
  await expect(source).toHaveValue(/"approval_binding":\s*\{/);
  await activeWorkflow.getByTestId("workflow-recovery-view-diagram").click();
  await page.screenshot({ path: path.join(evidence, "completed-workflow.png") });
  if (errors.length) throw new Error(errors.join("; "));
  const result = { checked_at: new Date().toISOString(), url: page.url(), workspace,
    source_path: workflow, template_options: 10, entry: "normal workspace Workflows control",
    source_diagram_navigation: "passed", read_only: true, browser_errors: errors,
    scope: "Template browsing and existing canonical source navigation; no new execution or authoring acceptance" };
  await fs.writeFile(path.join(evidence, "result.json"), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result));
} catch (error) {
  await page.screenshot({ path: path.join(evidence, "failure.png") });
  await fs.writeFile(path.join(evidence, "failure.json"), JSON.stringify({ error: String(error),
    url: page.url(), browser_errors: errors, body: (await page.locator("body").innerText()).slice(0, 18000) }, null, 2));
  throw error;
} finally {
  await browser.close();
}
