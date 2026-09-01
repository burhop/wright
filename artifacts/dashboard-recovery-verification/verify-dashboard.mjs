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
  checks[name] = {
    viewport: page.viewportSize(),
    subject: body.includes("f9237763"),
    tree: body.includes("aeca6ab8"),
    manifest: body.includes("f2b4964e"),
    recoveryLedger: body.includes("55/60"),
    productionBoundary: body.includes(
      "T056 automated keyboard, focus-order, 2× page-scale, accessibility-tree, Axe, reduced-motion, and responsive qualification pass",
    ),
    approval: body.includes("T051 exact-subject product/visual approval is complete"),
    readiness: body.includes("Customer readiness is incomplete"),
    governedFreeze: body.includes("F02B remains 27/38 with T028–T038 open"),
    galleryCount: images.length,
    imagesLoaded: images.every((image) => image.complete && image.width > 0),
    horizontalOverflowPixels: overflow,
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
  decision: apiBody.recovery.approvalEvidence.decision,
  commit: apiBody.recovery.approvalEvidence.commit,
  tree: apiBody.recovery.approvalEvidence.tree,
  manifestSha256: apiBody.recovery.approvalEvidence.manifestSha256,
  customerReady: apiBody.recovery.customerReady,
};
for (const [label, path] of Object.entries({
  root: "/",
  report: apiBody.recovery.evidence.recoveryReport,
  status: apiBody.recovery.evidence.recoveryStatus,
  manifest: apiBody.recovery.evidence.recoveryManifest,
  frozen: apiBody.recovery.evidence.frozenImage,
  ...Object.fromEntries(
    apiBody.recovery.evidence.recoveryImages.map((path, index) => [`recoveryImage${index + 1}`, path]),
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
  for (const field of ["subject", "tree", "manifest", "recoveryLedger", "productionBoundary", "approval", "readiness", "governedFreeze", "imagesLoaded"]) {
    if (!result[field]) failures.push(`${name}.${field}=false`);
  }
  if (result.galleryCount !== 8) failures.push(`${name}.galleryCount=${result.galleryCount}`);
  if (result.horizontalOverflowPixels !== 0) failures.push(`${name}.overflow=${result.horizontalOverflowPixels}`);
}
if (checks.api.status !== 200 || checks.api.completed !== 55 || checks.api.total !== 60 ||
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
