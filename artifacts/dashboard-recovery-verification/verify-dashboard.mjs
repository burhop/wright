import { chromium } from "@playwright/test";
import { writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

const base = "http://127.0.0.1:8765";
const output = new URL("./", import.meta.url);
const browser = await chromium.launch({ headless: true });
const diagnostics = [];
const checks = {};

async function inspect(name, viewport, screenshot) {
  const page = await browser.newPage({ viewport });
  page.on("console", (message) => {
    if (message.type() === "error") diagnostics.push(`${name}:console:${message.text()}`);
  });
  page.on("pageerror", (error) => diagnostics.push(`${name}:page:${error.message}`));
  await page.goto(base, { waitUntil: "networkidle" });
  await page.locator("text=Recovery execution ledger").waitFor();
  const body = await page.locator("body").innerText();
  const images = await page.locator(".evidence-gallery img").evaluateAll((nodes) =>
    nodes.map((node) => ({ complete: node.complete, width: node.naturalWidth, src: node.src })),
  );
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  );
  const overflowingElements = await page.evaluate(() =>
    [...document.querySelectorAll("body *")]
      .map((node) => {
        const rect = node.getBoundingClientRect();
        return {
          tag: node.tagName.toLowerCase(),
          className: typeof node.className === "string" ? node.className : "",
          right: Math.round(rect.right),
          width: Math.round(rect.width),
          text: (node.textContent ?? "").trim().slice(0, 120),
        };
      })
      .filter((node) => node.right > document.documentElement.clientWidth + 1)
      .slice(0, 12),
  );
  const internallyOverflowingElements = await page.evaluate(() =>
    [...document.querySelectorAll("body *")]
      .map((node) => ({
        tag: node.tagName.toLowerCase(),
        className: typeof node.className === "string" ? node.className : "",
        clientWidth: node.clientWidth,
        scrollWidth: node.scrollWidth,
        overflowX: getComputedStyle(node).overflowX,
        text: (node.textContent ?? "").trim().slice(0, 120),
      }))
      .filter((node) => node.scrollWidth > node.clientWidth + 1 && node.overflowX === "visible")
      .slice(0, 20),
  );
  const layoutRoots = await page.evaluate(() =>
    Object.fromEntries(
      ["html", "body", ".shell", ".tabs"].map((selector) => {
        const node = document.querySelector(selector);
        const rect = node.getBoundingClientRect();
        const style = getComputedStyle(node);
        return [selector, {
          left: Math.round(rect.left), right: Math.round(rect.right), width: Math.round(rect.width),
          clientWidth: node.clientWidth, scrollWidth: node.scrollWidth,
          overflowX: style.overflowX, contain: style.contain,
        }];
      }),
    ),
  );
  checks[name] = {
    viewport: page.viewportSize(),
    historicalSubject: body.includes("f9237763"),
    correctionSubject: body.includes("38b409bf"),
    correctionTree: body.includes("452c1ab8"),
    correctionManifest: body.includes("b8764a02"),
    recoveryLedger: body.includes("77/80"),
    productionBoundary: body.includes("No artifact was pushed, published, or released"),
    approval: body.includes("conditional approval is now bound honestly to the exact correction"),
    readiness: body.toLowerCase().includes("customer readiness") && body.toLowerCase().includes("false"),
    governedFreeze: body.includes("F02B remains 27/38 with T028–T038 open"),
    galleryCount: images.length,
    imagesLoaded: images.every((image) => image.complete && image.width > 0),
    horizontalOverflowPixels: overflow,
    overflowingElements,
    layoutRoots,
    internallyOverflowingElements,
  };
  await page.screenshot({ path: fileURLToPath(new URL(screenshot, output)), fullPage: true });
  await page.close();
}

await inspect("desktop", { width: 1440, height: 1100 }, "desktop-goal.png");
await inspect("mobile", { width: 390, height: 844 }, "mobile-goal.png");

const context = await browser.newContext();
const page = await context.newPage();
const api = await page.request.get(`${base}/api/status`);
const apiBody = await api.json();
checks.api = {
  status: api.status(),
  completed: apiBody.recovery.completed,
  total: apiBody.recovery.total,
  approval: apiBody.recovery.approval,
  decision: apiBody.recovery.approvalBaseline.decision,
  baselineCommit: apiBody.recovery.approvalBaseline.commit,
  correctionCommit: apiBody.recovery.correctionEvidence.commit,
  correctionTree: apiBody.recovery.correctionEvidence.tree,
  correctionManifestSha256: apiBody.recovery.correctionEvidence.manifestSha256,
  customerReady: apiBody.recovery.customerReady,
};
for (const [label, path] of Object.entries({
  root: "/",
  report: apiBody.recovery.evidence.correctionReport,
  status: apiBody.recovery.evidence.correctionStatus,
  manifest: apiBody.recovery.evidence.correctionManifest,
  frozen: apiBody.recovery.evidence.frozenImage,
  ...Object.fromEntries(
    apiBody.recovery.evidence.correctionImages.map((path, index) => [`correctionImage${index + 1}`, path]),
  ),
})) {
  checks[`http:${label}`] = (await page.request.get(`${base}${path}`)).status();
}
checks["http:encodedTraversal"] = (
  await page.request.get(`${base}/evidence/%252e%252e/%252e%252e/AGENTS.md`)
).status();
checks["http:plainTraversal"] = (
  await page.request.get(`${base}/evidence/..%2F..%2FAGENTS.md`)
).status();
await context.close();
await browser.close();

const failures = [];
for (const [name, value] of Object.entries(checks)) {
  if (name.startsWith("http:") && name.includes("Traversal")) {
    if (value !== 403) failures.push(`${name}=${value}`);
  } else if (name.startsWith("http:") && value !== 200) {
    failures.push(`${name}=${value}`);
  }
}
for (const name of ["desktop", "mobile"]) {
  const result = checks[name];
  for (const field of ["historicalSubject", "correctionSubject", "correctionTree", "correctionManifest", "recoveryLedger", "productionBoundary", "approval", "readiness", "governedFreeze", "imagesLoaded"]) {
    if (!result[field]) failures.push(`${name}.${field}=false`);
  }
  if (result.galleryCount !== 15) failures.push(`${name}.galleryCount=${result.galleryCount}`);
  if (result.horizontalOverflowPixels !== 0) failures.push(`${name}.overflow=${result.horizontalOverflowPixels}`);
}
if (checks.api.status !== 200 || checks.api.completed !== 77 || checks.api.total !== 80 ||
    checks.api.approval !== "complete" || checks.api.decision !== "approved" || checks.api.customerReady !== false) {
  failures.push("api recovery ledger/approval/readiness mismatch");
}
if (diagnostics.length) failures.push(`browser diagnostics=${diagnostics.length}`);

const result = {
  overall: failures.length ? "fail" : "pass",
  checkedAt: new Date().toISOString(),
  checks,
  diagnostics,
  failures,
};
await writeFile(new URL("dashboard-verification.json", output), `${JSON.stringify(result, null, 2)}\n`);
console.log(JSON.stringify(result, null, 2));
if (failures.length) process.exitCode = 1;
