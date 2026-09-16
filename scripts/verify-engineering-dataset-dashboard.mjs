// Live local dashboard acceptance; no mocked run receipts or workflow outputs.
import { chromium, expect } from "@playwright/test";
import fs from "node:fs/promises";
import { createHash } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const readOnly = process.argv.includes("--read-only");
const evidence = path.join(root, readOnly
  ? ".local-run/feature-081-live/dataset-dashboard-running-evidence"
  : ".local-run/feature-081-live/dataset-dashboard-evidence");
await fs.mkdir(evidence, { recursive: true });
const url = "http://127.0.0.1:8771";
const browser = await chromium.launch({ headless: true });
const errors = [];
let result;
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1040 } });
  page.on("pageerror", error => errors.push(error.message));
  await page.goto(url);
  await expect(page.getByTestId("metric-datasets-created")).toHaveText("30");
  await expect(page.locator("tr.dataset-row")).toHaveCount(30);
  await expect(page.locator("path.chart-line")).toHaveCount(4);
  const state = await (await page.request.get(url + "/api/status")).json();
  if (JSON.stringify(state.history[0].metrics) !== JSON.stringify({
    datasets_created: 0, combinations_run: 0, processes_with_outputs: 0, valid_data: 0,
  })) throw new Error("Missing real zero baseline");
  if (!readOnly) {
    await page.getByTestId("campaign-approval-mode").selectOption("manual");
    await expect(page.locator("#config-message")).toContainText("Manual approval");
    await page.getByTestId("campaign-approval-mode").selectOption("auto");
    await expect(page.locator("#config-message")).toContainText("Auto approvals");
    const denied = await page.request.post(url + "/api/config", {
      headers: { Origin: "http://unrelated.invalid", "Content-Type": "application/json" },
      data: { approval_mode: "manual" },
    });
    if (denied.status() !== 403) throw new Error("Cross-origin settings change was accepted");
  }
  const metricNames = ["datasets_created", "combinations_run", "processes_with_outputs", "valid_data"];
  for (let index = 0; index < state.history.length; index++) {
    for (const name of metricNames) {
      const value = state.history[index].metrics[name];
      if (!Number.isInteger(value) || value < 0 || value > 30)
        throw new Error("Invalid history counter: " + name);
      if (index && value < state.history[index - 1].metrics[name])
        throw new Error("Cumulative history regressed: " + name);
    }
    if (state.history[index].metrics.valid_data !== 0)
      throw new Error("Content validation was incorrectly credited");
  }
  let imagesChecked = 0;
  let completedFilesChecked = 0;
  for (const dataset of state.datasets) {
    for (const name of dataset.files.images.filter(name => name.endsWith(".png"))) {
      const image = await page.request.get(url + "/inputs/" + dataset.path + "/" + name);
      if (!image.ok() || !image.headers()["content-type"].startsWith("image/png"))
        throw new Error("Input image unavailable: " + dataset.scenario_id);
      imagesChecked++;
    }
    const attempt = dataset.latest_attempt;
    if (attempt?.status === "completed") {
      const outputBase = url + "/output/" + encodeURIComponent(dataset.scenario_id)
        + "/" + encodeURIComponent(attempt.attempt_id);
      const receiptResponse = await page.request.get(outputBase + "/run.json");
      if (!receiptResponse.ok()) throw new Error("Completed run receipt is unavailable");
      const receipt = await receiptResponse.json();
      if (receipt.run_id !== attempt.run_id || receipt.status !== "completed"
        || !receipt.all_required_steps_succeeded || !receipt.terminal_step_reached
        || receipt.content_validated !== false)
        throw new Error("Completed output link has a different runtime identity");
      for (const file of receipt.produced_files) {
        const fileResponse = await page.request.get(outputBase + "/artifacts/"
          + file.path.split("/").map(encodeURIComponent).join("/"));
        if (!fileResponse.ok()) throw new Error("Completed output file is unavailable: " + file.path);
        const bytes = await fileResponse.body();
        if (!bytes.length || bytes.length !== file.size_bytes
          || createHash("sha256").update(bytes).digest("hex") !== file.sha256
          || file.run_id !== receipt.run_id)
          throw new Error("Output link does not serve the recorded file: " + file.path);
        completedFilesChecked++;
      }
    }
  }
  await page.locator("tr.dataset-row button").first().click();
  await expect(page.locator(".file-links a").first()).toBeVisible();
  await page.getByTestId("campaign-search").fill("riverstone");
  await expect(page.locator("tr.dataset-row")).toHaveCount(1);
  await page.getByTestId("campaign-search").fill("");
  await expect(page.locator("tr.dataset-row")).toHaveCount(30);
  await page.getByTestId("legend-valid_data").click();
  await expect(page.getByTestId("legend-valid_data")).toHaveAttribute("aria-pressed", "true");
  await page.getByTestId("legend-valid_data").click();
  await page.screenshot({ path: path.join(evidence, "desktop.png") });
  await page.getByTestId("campaign-output-folder").click();
  await expect(page.getByRole("heading", { name: "Workflow output files" })).toBeVisible();
  await expect(page.locator('a[href^="/output/"]')).toHaveCount(31);
  await page.goto(url);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByTestId("metric-datasets-created")).toHaveText("30");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
  if (overflow) throw new Error("Mobile page has horizontal overflow");
  await page.screenshot({ path: path.join(evidence, "mobile.png") });
  result = { url, checked_at: new Date().toISOString(), dataset_rows: 30,
    uploaded_pngs_checked: imagesChecked, completed_output_files_checked: completedFilesChecked,
    output_validation: "presence, bytes and same-run identity only", chart_series: 4, metrics: state.metrics,
    history_points: state.history.length, read_only: readOnly,
    approval_controls: readOnly ? "not changed during active campaign" : "passed",
    cross_origin_write: readOnly ? "not repeated" : "rejected",
    cumulative_history: "passed", mobile_overflow: false, browser_errors: errors };
  if (errors.length) throw new Error(errors.join("; "));
  await fs.writeFile(path.join(evidence, "result.json"), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result));
} finally {
  // Restore the user's authorized test policy even if a later UI assertion fails.
  if (!readOnly) {
    const context = await browser.newContext();
    await context.request.post(url + "/api/config", {
      headers: { Origin: url, "Content-Type": "application/json" }, data: { approval_mode: "auto" },
    }).catch(() => {});
  }
  await browser.close();
}
