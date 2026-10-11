// Actual served preview evidence; this does not capture the desktop app chrome.
import { chromium } from "@playwright/test";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";

const state = path.resolve(process.argv[2]);
const output = path.resolve(process.argv[3]);
const checkpoint = process.argv[4] === "checkpoint";
const gateway = process.argv[4] === "gateway";
let info;
if (checkpoint) {
  const evidence = JSON.parse(readFileSync(path.join(state, "checkpoint-probe.json"), "utf8"));
  info = { workspace_id: evidence.workspace.workspace_id, source_path: evidence.source.path, run_id: evidence.start_receipt.run_id };
} else {
try {
  info = JSON.parse(readFileSync(path.join(state, "probe.json"), "utf8"));
} catch (error) {
  if (error.code !== "ENOENT") throw error;
  const protocol = JSON.parse(readFileSync(path.join(state, gateway ? "mcp-gateway-probe.json" : "protocol-probe.json"), "utf8"));
  info = { workspace_id: protocol.workspace.workspace_id, source_path: protocol.source.path, run_id: protocol.start_receipt.run_id };
}
}
const preview = JSON.parse(readFileSync(path.join(state, "preview.json"), "utf8"));
const token = readFileSync(path.join(state, ".preview-api-token"), "utf8");
mkdirSync(output, { recursive: true });
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1600, height: 1000 },
  extraHTTPHeaders: { Authorization: `Bearer ${token}` },
});
const page = await context.newPage();
const requests = [];
const failures = [];
page.on("request", (r) => {
  const url = new URL(r.url());
  if (url.pathname.startsWith("/api/")) requests.push({ method: r.method(), path: url.pathname });
});
page.on("pageerror", (error) => failures.push(error.message));
try {
  const workspaceUrl = new URL(preview.web_url);
  workspaceUrl.pathname = `/workspace/${info.workspace_id}`;
  await page.goto(workspaceUrl.toString());
  const unlock = page.getByRole("button", { name: "Unlock", exact: true });
  await unlock.or(page.getByTestId("workspace-panel")).waitFor({ timeout: 30000 });
  if (await unlock.isVisible()) {
    await page.getByLabel("Access Token", { exact: true }).fill(token);
    await unlock.click();
  }
  await page.getByTestId("workspace-panel").waitFor({ timeout: 30000 });
  if (await page.getByTestId("agent-sidebar").count()) throw new Error("Hosted preview mounted Wright chat");
  await page.screenshot({ path: path.join(output, "01-workspace.png") });
  const workflowControl = page.getByRole("button", { name: /^Workflows?$/ });
  await workflowControl.click();
  await page.getByTestId("workflow-recovery-canvas").waitFor({ timeout: 30000 });
  await page.screenshot({ path: path.join(output, "02-workflows-entry.png") });
  const url = new URL(workspaceUrl);
  url.searchParams.set("workflow", "canonical");
  url.searchParams.set("workflowPath", info.source_path);
  await page.goto(url.toString());
  if (checkpoint) {
    // Reuse the normal wait/reopen controls verified by the existing
    // scripts/recovery/capture_instruction_wait_walkthrough.mjs harness.
    await page.getByTestId("workflow-run-input-wait").waitFor({ timeout: 30000 });
    await page.screenshot({ path: path.join(output, "03-declared-input-wait.png") });
    await page.getByTestId("workflow-run-answer-input").click();
    await page.getByRole("button", { name: "Submit response", exact: true }).waitFor({ timeout: 30000 });
    if (new URL(page.url()).searchParams.get("processRun") !== info.run_id) throw new Error("Working view changed run identity");
    await page.screenshot({ path: path.join(output, "04-working-input-view.png") });
    await page.reload();
    await page.getByRole("button", { name: "Submit response", exact: true }).waitFor({ timeout: 30000 });
    if (new URL(page.url()).searchParams.get("processRun") !== info.run_id) throw new Error("Reload changed run identity");
    await page.screenshot({ path: path.join(output, "05-reopened-input-view.png") });
  } else {
    await page.getByLabel(gateway ? "Desktop confined gateway inspection diagram" : "Desktop reasoning handoff diagram", { exact: true }).waitFor({ timeout: 30000 });
    await page.getByText(gateway ? "Inspect the enrolled requirements" : "Prepare a digital inspection brief", { exact: true }).first().waitFor();
    await page.screenshot({ path: path.join(output, "03-inspection-workflow.png") });
    await page.getByRole("button", { name: /^View results/ }).first().click();
    await page.getByRole("button", { name: /^Open document in tab/ }).waitFor();
    await page.screenshot({ path: path.join(output, "04-saved-result.png") });
  }
  const unexpectedAgent = requests.filter((r) => r.path.startsWith("/api/agent") || r.path.startsWith("/api/inference"));
  if (unexpectedAgent.length) throw new Error("Hosted preview requested standalone agent APIs");
  writeFileSync(path.join(output, "capture.json"), JSON.stringify({
    status: "passed", host: "GB10 browser preview, desktop chrome not verified",
    url: url.toString(), viewport: { width: 1600, height: 1000 },
    workspace_id: info.workspace_id, source_path: info.source_path,
    preserved_run_id: info.run_id, requests, page_errors: failures,
  }, null, 2));
  console.log(JSON.stringify({ status: "passed", output }));
} catch (error) {
  await page.screenshot({ path: path.join(output, "failure.png") });
  writeFileSync(path.join(output, "capture.json"), JSON.stringify({
    status: "failed", diagnostic: error.message, requests, page_errors: failures,
  }, null, 2));
  throw error;
} finally {
  await context.close();
  await browser.close();
}
