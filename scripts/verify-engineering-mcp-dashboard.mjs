#!/usr/bin/env node

import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { chromium } from "playwright";

const option = (name, fallback) => {
  const index = process.argv.indexOf(name);
  return index === -1 ? fallback : process.argv[index + 1];
};

const baseUrl = option("--base-url", "http://127.0.0.1:18765").replace(/\/$/, "");
const outputDir = path.resolve(option("--output-dir", "artifacts/engineering-mcp-status"));
await mkdir(outputDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
const consoleErrors = [];
const pageErrors = [];
const failedResponses = [];
page.on("console", (message) => {
  if (message.type() === "error") consoleErrors.push(message.text());
});
page.on("pageerror", (error) => pageErrors.push(error.message));
page.on("response", (response) => {
  if (response.status() >= 400) failedResponses.push({ status: response.status(), url: response.url() });
});

const assertText = async (testId, expected) => {
  const value = await page.getByTestId(testId).innerText();
  if (!value.toLowerCase().includes(String(expected).toLowerCase())) {
    throw new Error(`${testId} did not contain ${JSON.stringify(expected)}: ${value}`);
  }
};

try {
  await page.goto(`${baseUrl}/index.html`, { waitUntil: "networkidle" });
  await page.getByTestId("engineering-mcp-dashboard").waitFor();

  const statusResponse = await page.request.get(`${baseUrl}/status.json`);
  if (!statusResponse.ok()) throw new Error(`status.json returned ${statusResponse.status()}`);
  const status = await statusResponse.json();
  const dispositionTotal = Object.values(status.counts).reduce((total, value) => total + value, 0);
  if (status.records.length !== dispositionTotal) throw new Error("Status records do not match disposition counts");
  const categoryTotal = Object.values(status.category_counts).reduce((total, value) => total + value, 0);
  if (status.records.length !== categoryTotal) throw new Error("Status records do not match portfolio category counts");

  await page.getByTestId("engineering-category-key").waitFor();
  for (const category of status.category_key) {
    await assertText(`engineering-category-${category.id}`, status.category_counts[category.id]);
    await assertText(`category-key-${category.id}`, category.definition);
  }
  await page.getByTestId("engineering-product-groups").waitFor();
  await assertText("engineering-color-key", "Tested as far as currently possible with no observed problem");
  await assertText("engineering-color-key", "More work or a required environment remains");
  await assertText("engineering-color-key", "Did not work and the evaluation is closed");
  for (const group of status.product_groups) {
    await assertText(`engineering-product-${group.id}`, group.count);
  }
  if (status.product_release.count !== status.category_counts.qualified) {
    throw new Error("Product release count must include only fully qualified servers");
  }
  for (const protocol of status.protocol_status) {
    await assertText(`engineering-protocol-${protocol.protocol}`, `${protocol.known} known`);
  }
  await assertText("engineering-protocol-hardware_mcp", "physical operation has not qualified");
  await assertText("engineering-protocol-mhs", "research preview");

  const chainCards = page.locator('article[data-testid^="engineering-chain-"]');
  if ((await chainCards.count()) !== status.chains.length) {
    throw new Error("Rendered Tier 1 chain count does not match status evidence");
  }
  for (const chain of status.chains) await assertText(`engineering-chain-${chain.chain_id}`, "passed");

  const evidenceRecord =
    status.records.find((record) => record.server_id === "kernelcad-mcp") ||
    status.records.find((record) => record.evidence_href?.startsWith("evidence/"));
  if (!evidenceRecord?.evidence_href) throw new Error("No embedded server evidence found");
  const evidenceResponse = await page.request.get(`${baseUrl}/${evidenceRecord.evidence_href}`);
  const evidenceText = await evidenceResponse.text();
  if (!evidenceResponse.ok()) throw new Error("Exact server evidence is unavailable");
  if (evidenceRecord.server_id === "kernelcad-mcp" && !evidenceText.includes("EALLOWGIT")) {
    throw new Error("Exact kernelCAD package failure is missing from its evidence");
  }

  await page.evaluate(() => window.scrollTo(0, 0));
  const overviewPath = path.join(outputDir, "engineering-mcp-dashboard.png");
  await page.screenshot({ path: overviewPath });

  const changes = page.getByTestId("engineering-status-changes");
  await changes.locator("summary").click();
  await changes.scrollIntoViewIfNeeded();
  const changesPath = path.join(outputDir, "engineering-mcp-changes.png");
  await page.screenshot({ path: changesPath });

  const records = page.getByTestId("engineering-status-records");
  await records.getByLabel("Search", { exact: true }).fill(evidenceRecord.server_id);
  await records.scrollIntoViewIfNeeded();
  await assertText("engineering-status-records", evidenceRecord.name);
  const recordPath = path.join(outputDir, "engineering-mcp-server-evidence.png");
  await page.screenshot({ path: recordPath });

  const result = {
    observed_at: new Date().toISOString(),
    dashboard_url: `${baseUrl}/index.html`,
    status: "passed",
    counts: status.counts,
    category_counts: status.category_counts,
    qualification_counts: status.qualification_counts,
    chains: status.chains.map((chain) => ({
      chain_id: chain.chain_id,
      status: chain.status,
      call_count: chain.call_count,
    })),
    protocol_status: status.protocol_status,
    evidence_server_id: evidenceRecord.server_id,
    evidence_sha256: evidenceRecord.evidence_sha256,
    console_errors: consoleErrors,
    page_errors: pageErrors,
    failed_responses: failedResponses,
    screenshots: [overviewPath, changesPath, recordPath].map((value) => path.basename(value)),
  };
  if (consoleErrors.length || pageErrors.length || failedResponses.length) result.status = "failed";
  await writeFile(
    path.join(outputDir, "served-dashboard-verification.json"),
    `${JSON.stringify(result, null, 2)}\n`,
    "utf8",
  );
  if (result.status === "failed") throw new Error(`Dashboard diagnostics contain errors: ${JSON.stringify(result)}`);
  console.log(JSON.stringify(result));
} finally {
  await browser.close();
}
