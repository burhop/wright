// Actual served preview evidence; this does not capture the desktop app chrome.
import { chromium } from "@playwright/test";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";

const state = path.resolve(process.argv[2]);
const output = path.resolve(process.argv[3]);
const nativeConversation = process.argv[4] === "native-conversation";
const nativeEvidence = nativeConversation ? JSON.parse(readFileSync(process.argv[5], "utf8")) : undefined;
const connectedCheckpoint = process.argv[4] === "checkpoint-connected";
const completedCheckpoint = process.argv[4] === "checkpoint-completed";
const checkpoint = process.argv[4] === "checkpoint" || connectedCheckpoint || completedCheckpoint;
const gateway = process.argv[4] === "gateway";
let info;
if (nativeConversation) {
  info = {workspace_id:nativeEvidence.workspace.workspace_id,source_path:nativeEvidence.source.path,run_id:nativeEvidence.start.run_id};
} else if (checkpoint) {
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
let uiContinuation;
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
  if (completedCheckpoint || nativeConversation) {
    const evidence = nativeConversation ? {...nativeEvidence,stage:nativeEvidence.snapshot.state,final_snapshot:nativeEvidence.snapshot} : JSON.parse(readFileSync(path.join(state, "checkpoint-probe.json"), "utf8"));
    if (evidence.stage !== "completed" || evidence.final_snapshot.context.run_id !== info.run_id) throw new Error("Readback requires the exact recorded completed run");
    const view = new URL(url);
    view.searchParams.set("processView", "desktop-checkpoint-completed-readback");
    view.searchParams.set("processPath", info.source_path);
    view.searchParams.set("processDigest", evidence.source.storage_digest);
    view.searchParams.set("processRun", info.run_id);
    await page.goto(view.toString());
    await page.getByText("Process completed", { exact: true }).waitFor({ timeout: 30000 });
    if (new URL(page.url()).searchParams.get("processRun") !== info.run_id) throw new Error("Completed readback changed run identity");
    await page.screenshot({ path: path.join(output, "03-reopened-completed-run.png") });
    if (nativeConversation) {
      await page.getByRole("button", {name:"Open file",exact:true}).first().click();
      const brief = page.getByRole("heading", {name:"Digital inspection brief",exact:true});
      await brief.waitFor({timeout:10000});
      await brief.scrollIntoViewIfNeeded();
      await page.screenshot({path:path.join(output,"03b-owned-inspection-brief.png")});
    }
    await page.reload();
    await page.getByText("Process completed", { exact: true }).waitFor({ timeout: 30000 });
    await page.screenshot({ path: path.join(output, "04-reloaded-completed-run.png") });
    const tab = page.getByRole("tab", { selected: true });
    const identity = await tab.getAttribute("data-testid");
    if (!identity) throw new Error("Cannot identify the exact common working-view tab for close");
    await tab.getByRole("button", { name: /^Close / }).click();
    await page.getByTestId(identity).waitFor({ state: "detached", timeout: 30000 });
    uiContinuation = { readback_only: true, common_view_closed: true, run_id: info.run_id };
    await page.screenshot({ path: path.join(output, "05-common-view-closed.png") });
  } else if (checkpoint) {
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
    if (connectedCheckpoint) {
      const select = page.getByLabel("selection (required)", { exact: true });
      await select.waitFor({ timeout: 30000 });
      if (!(await select.isEnabled())) throw new Error("Connected input editor is unavailable");
      await select.selectOption({ label: "a" });
      const submit = page.getByRole("button", { name: "Submit response", exact: true });
      if (!(await submit.isEnabled())) throw new Error("Validated connected input cannot be submitted");
      await page.screenshot({ path: path.join(output, "06-connected-choice-ready.png") });
      const reply = page.waitForResponse(r => r.request().method() === "POST" && /\/process-interfaces\/interactions\/[^/]+\/response$/.test(new URL(r.url()).pathname));
      await submit.click();
      const response = await reply;
      const sent = response.request().postDataJSON();
      const receipt = await response.json();
      if (!response.ok() || sent.value?.selection !== "a") throw new Error("The normal UI did not submit the exact declared test selection");
      if (new URL(page.url()).searchParams.get("processRun") !== info.run_id) throw new Error("UI response changed the durable run");
      uiContinuation = { status: response.status(), request: sent, receipt, run_id: info.run_id, test_data: "synthetic selection a; no engineering approval" };
      writeFileSync(path.join(output, "ui-continuation.json"), JSON.stringify(uiContinuation, null, 2));
      await page.screenshot({ path: path.join(output, "07-same-run-continuing.png") });
      // The SDK probe relays this desktop's next reply; this browser never
      // generates a model answer or executes/restarts the process itself.
      const deadline = Date.now() + 300000;
      while (JSON.parse(readFileSync(path.join(state, "checkpoint-probe.json"), "utf8")).stage !== "completed") {
        if (Date.now() > deadline) throw new Error("Awaiting the desktop reply did not reach a recorded completion; reconcile, never restart");
        await page.waitForTimeout(250);
      }
      await page.getByText("Process completed", { exact: true }).waitFor({ timeout: 30000 });
      if (new URL(page.url()).searchParams.get("processRun") !== info.run_id) throw new Error("Completed view changed run identity");
      await page.screenshot({ path: path.join(output, "08-completed-same-run.png") });
      const activeTab = page.getByRole("tab", { selected: true });
      const identity = await activeTab.getAttribute("data-testid");
      if (!identity) throw new Error("Cannot identify the exact common working-view tab for close");
      await activeTab.getByRole("button", { name: /^Close / }).click();
      await page.getByTestId(identity).waitFor({ state: "detached", timeout: 30000 });
      uiContinuation.common_view_closed = true;
      writeFileSync(path.join(output, "ui-continuation.json"), JSON.stringify(uiContinuation, null, 2));
    }
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
    ui_continuation: uiContinuation,
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
