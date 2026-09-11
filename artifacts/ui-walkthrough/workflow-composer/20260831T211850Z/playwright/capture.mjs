import { chromium } from "@playwright/test";
import { appendFileSync, mkdirSync, rmSync, writeFileSync } from "node:fs";
import path from "node:path";

const root = process.env.WRIGHT_WALKTHROUGH_ROOT;
const baseUrl = process.env.WRIGHT_WALKTHROUGH_URL;
if (!root || !baseUrl) throw new Error("Walkthrough environment is incomplete");
for (const directory of ["playwright", "screenshots/raw", "screenshots/annotated", "trace"]) {
  mkdirSync(path.join(root, directory), { recursive: true });
}
for (const staleStopImage of ["screenshots/raw/99-stopped.png", "screenshots/annotated/99-stopped.png"]) {
  rmSync(path.join(root, staleStopImage), { force: true });
}

const subject = "e0354dd7346c7573f1aa6a36e1c29ed854a3bbe9";
const diagnostics = [];
let diagnosticCursor = 0;
const status = {
  title: "Workflow Composer Checkpoint D invalid-edit recovery",
  summary: "Walking the provisional composer through a normal edit, an incompatible connection, bounded correction, validation, and save.",
  overall: "pending",
  updated: new Date().toISOString(),
  manualSteps: [
    { label: "Create composition", instruction: "Open **Workflow Composer**, click **Create working draft**, then add **Capture input**, **Engineering work**, **Review**, and **Release boundary**." },
    { label: "Edit review block", instruction: "Select **Review product definition**, change its definition and position, then apply both edits." },
    { label: "Attempt invalid connection", instruction: "Delete **connection.definition-to-review**, choose **Product definition · output** as source and **Accepted definition · output** as target, then click **Create connection**." },
    { label: "Correct connection", instruction: "Keep the source, choose **Product definition · input** as target, then click **Create connection**." },
    { label: "Validate and save", instruction: "Click **Validate**, then click **Save draft**." },
  ],
  steps: [],
};

const esc = (value) => String(value)
  .replaceAll("&", "&amp;").replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;").replaceAll('"', "&quot;");

function flush() {
  status.updated = new Date().toISOString();
  writeFileSync(path.join(root, "status.json"), `${JSON.stringify(status, null, 2)}\n`, "utf8");
  const cards = status.steps.map((step) => `<article class="card ${step.state}"><b>${step.state.toUpperCase()}</b><h2>${esc(step.label)}</h2><p>${esc(step.summary)}</p><dl><dt>Purpose</dt><dd>${esc(step.purpose)}</dd><dt>Action</dt><dd>${esc(step.action)}</dd><dt>Expected</dt><dd>${esc(step.expected)}</dd><dt>Actual</dt><dd>${esc(step.actual)}</dd></dl>${step.raw ? `<p><button class="image-button" data-image="${esc(step.raw)}">Raw image</button> <button class="image-button" data-image="${esc(step.annotated)}">Annotated image</button></p>` : ""}</article>`).join("");
  const manual = status.manualSteps.map((step) => `<li>${esc(step.instruction)}</li>`).join("");
  writeFileSync(path.join(root, "report.html"), `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(status.title)}</title><style>body{margin:0;background:#07111f;color:#e8eef8;font:16px/1.5 system-ui}main{max-width:1120px;margin:auto;padding:28px}.hero,.card{background:#111d30;border:1px solid #30425f;border-left:9px solid #98a2b3;border-radius:14px;padding:20px;margin:16px 0}.pass{border-left-color:#32d583}.blocked{border-left-color:#f04438}.pending{border-left-color:#98a2b3}dl{display:grid;grid-template-columns:110px 1fr;gap:8px}dt{font-weight:700;color:#9cc7ff}dd{margin:0}button{padding:8px 12px;color:#07111f;background:#9cc7ff;border:0;border-radius:6px;cursor:pointer}code{overflow-wrap:anywhere;color:#7ee7ff}dialog{max-width:96vw;background:#111d30;color:#fff;border:1px solid #49617f;border-radius:12px}dialog img{max-width:92vw;max-height:82vh;display:block;margin-top:12px}</style></head><body><main><section class="hero"><h1>${esc(status.title)}</h1><p><strong>${status.overall.toUpperCase()}:</strong> ${esc(status.summary)}</p><p>Exact commit <code>${subject}</code></p></section>${cards}<section class="card"><h2>Manual repeat checklist</h2><ol>${manual}</ol></section></main><dialog id="viewer"><button id="close">Close</button><img alt="Full-size walkthrough evidence"></dialog><script>const d=document.getElementById('viewer'),i=d.querySelector('img');document.querySelectorAll('[data-image]').forEach(b=>b.onclick=()=>{i.src=b.dataset.image;d.showModal()});document.getElementById('close').onclick=()=>d.close();document.onkeydown=e=>{if(e.key==='Escape')d.close()};</script></body></html>`, "utf8");
}

writeFileSync(path.join(root, "progress.md"), `# Workflow Composer Checkpoint D invalid-edit recovery\n\nCommit: \`${subject}\`  \nBase URL: \`${baseUrl}\`  \nPersona: local engineer  \nAuthority: provisional draft only; no execution, release, MCP, model, benchmark, or publication action is present.\n\n`, "utf8");
flush();

function record(step, url) {
  status.steps.push(step);
  if (step.state === "blocked") {
    status.overall = "blocked";
    status.summary = step.summary;
  } else if (status.steps.at(-1)?.id === "save" && status.steps.every((item) => item.state === "pass")) {
    status.overall = "pass";
    status.summary = "The local engineer edited and moved the review block, contained an output-to-output connection without changing the last-valid draft or saved revision, applied the named correction, validated, and saved revision 2 with no browser diagnostics.";
  }
  const freshDiagnostics = diagnostics.slice(diagnosticCursor);
  diagnosticCursor = diagnostics.length;
  appendFileSync(path.join(root, "progress.md"), [
    `## ${new Date().toLocaleString("en-US", { timeZone: "America/New_York", timeZoneName: "short" })} — ${step.state.toUpperCase()}`,
    "", `- Current URL: \`${url}\``, `- Action: ${step.action}`,
    `- Exact control: ${step.controls.join(", ")}`, `- Value: ${step.value ?? "No value entered."}`,
    `- Expected: ${step.expected}`, `- Actual: ${step.actual}`, "- Diagnostics:",
    ...(freshDiagnostics.length ? freshDiagnostics.map((item) => `  - ${item}`) : ["  - No console errors, page errors, or failed responses recorded."]),
    "- Screenshots:", ...(step.raw ? [`  - Raw: \`${step.raw}\``, `  - Annotated: \`${step.annotated}\``] : ["  - None."]),
    `- Status: **${step.state.toUpperCase()}**`, "",
  ].join("\n"), "utf8");
  flush();
}

async function capture(page, id, controls) {
  const raw = `screenshots/raw/${id}.png`;
  const annotated = `screenshots/annotated/${id}.png`;
  await page.screenshot({ path: path.join(root, raw), fullPage: true });
  const missing = await page.evaluate((items) => {
    const markerClass = "wright-walkthrough-marker";
    const missingItems = [];
    const legend = document.createElement("div");
    legend.className = markerClass;
    legend.style.cssText = "position:fixed;right:16px;top:16px;z-index:2147483647;max-width:390px;padding:14px;background:#111827;color:#fff;border:3px solid #fbbf24;border-radius:10px;font:14px/1.4 system-ui";
    legend.innerHTML = `<strong>Visible controls and evidence</strong><ol>${items.map((item) => `<li>${item.label}</li>`).join("")}</ol>`;
    document.body.appendChild(legend);
    items.forEach((item, index) => {
      const element = document.querySelector(item.selector);
      if (!(element instanceof HTMLElement)) { missingItems.push(item.label); return; }
      element.dataset.oldOutline = element.style.outline;
      element.style.outline = "4px solid #f59e0b";
      const bounds = element.getBoundingClientRect();
      const marker = document.createElement("div");
      marker.className = markerClass; marker.textContent = String(index + 1);
      marker.style.cssText = `position:absolute;left:${Math.max(0, bounds.left + scrollX - 13)}px;top:${Math.max(0, bounds.top + scrollY - 13)}px;z-index:2147483647;width:26px;height:26px;border-radius:50%;display:grid;place-items:center;background:#f59e0b;color:#111827;font:bold 15px system-ui;border:2px solid white`;
      document.body.appendChild(marker);
    });
    return missingItems;
  }, controls);
  if (missing.length) throw new Error(`Missing annotated controls: ${missing.join(", ")}`);
  await page.screenshot({ path: path.join(root, annotated), fullPage: true });
  await page.evaluate(() => {
    document.querySelectorAll(".wright-walkthrough-marker").forEach((element) => element.remove());
    document.querySelectorAll("[data-old-outline]").forEach((element) => {
      if (element instanceof HTMLElement) { element.style.outline = element.dataset.oldOutline ?? ""; delete element.dataset.oldOutline; }
    });
  });
  return { raw, annotated };
}

function noBrowserDiagnostics() {
  const fresh = diagnostics.slice(diagnosticCursor);
  if (fresh.length) throw new Error(`Unexpected browser diagnostics: ${fresh.join(" | ")}`);
}

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1600, height: 1000 }, colorScheme: "dark" });
await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
const page = await context.newPage();
page.on("console", (message) => { if (["error", "warning"].includes(message.type())) diagnostics.push(`console ${message.type()}: ${message.text()}`); });
page.on("pageerror", (error) => diagnostics.push(`page error: ${error.message}`));
page.on("response", (response) => { if (response.status() >= 400) diagnostics.push(`failed response: ${response.status()} ${response.url()}`); });

let failure;
try {
  await page.goto(`${baseUrl}/workflow-composer`, { waitUntil: "domcontentloaded" });
  await page.getByTestId("workflow-composer-create").waitFor({ timeout: 30_000 });
  const createScreen = await capture(page, "01-create", [
    { selector: '[data-testid="workflow-composer-create-title"]', label: "Draft title" },
    { selector: '[data-testid="workflow-composer-create-purpose"]', label: "Purpose" },
    { selector: '[data-testid="workflow-composer-create"]', label: "Create working draft" },
  ]);
  await page.getByTestId("workflow-composer-create").click();
  await page.getByTestId("workflow-composer-canvas").waitFor(); noBrowserDiagnostics();
  record({ id: "create", state: "pass", label: "Create a separate working draft", summary: "Revision 1 opened under explicit provisional authority.", purpose: "Begin from an isolated empty working draft.", action: "Clicked Create working draft.", controls: ["Draft title", "Purpose", "Create working draft"], value: "Product definition draft", expected: "An empty revision 1 opens with no released or executable authority.", actual: "Revision 1 opened with Working draft and Not released · Not executable labels.", ...createScreen }, page.url());

  const palette = [["input", "Capture input"], ["work", "Engineering work"], ["review", "Review"], ["release", "Release boundary"]];
  for (let index = 0; index < palette.length; index += 1) {
    const [role, label] = palette[index];
    const control = page.getByTestId(`workflow-composer-palette-${role}`);
    const screen = await capture(page, `0${index + 2}-add-${role}`, [
      { selector: `[data-testid="workflow-composer-palette-${role}"]`, label },
      { selector: '[data-testid="workflow-composer-canvas"]', label: "Last-valid graphical draft" },
    ]);
    await control.click();
    await page.getByTestId(`workflow-composer-palette-${role}`).waitFor(); noBrowserDiagnostics();
    record({ id: `add-${role}`, state: "pass", label: `Add ${label}`, summary: `${label} was added through the bounded palette.`, purpose: "Build the representative valid starting graph.", action: `Clicked ${label}.`, controls: [label], expected: "The next complete valid candidate replaces the working copy.", actual: "The block and its reciprocal declarations appeared without browser diagnostics.", ...screen }, page.url());
  }

  await page.getByTestId("workflow-canvas-select-block.review-product-definition").click();
  await page.getByTestId("workflow-inspector-title").waitFor();
  const editScreen = await capture(page, "06-edit-review", [
    { selector: '[data-testid="workflow-canvas-select-block.review-product-definition"]', label: "Selected review block" },
    { selector: '[data-testid="workflow-inspector-title"]', label: "Title" },
    { selector: '[data-testid="workflow-inspector-purpose"]', label: "Purpose" },
    { selector: '[data-testid="workflow-inspector-apply-definition"]', label: "Apply definition" },
    { selector: '[data-testid="workflow-inspector-apply-position"]', label: "Apply position" },
  ]);
  await page.getByTestId("workflow-inspector-title").fill("Review the product definition");
  await page.getByTestId("workflow-inspector-purpose").fill("Check completeness and record bounded corrections.");
  await page.getByTestId("workflow-inspector-apply-definition").click();
  await page.getByTestId("workflow-inspector-position-x").fill("720");
  await page.getByTestId("workflow-inspector-position-y").fill("96");
  await page.getByTestId("workflow-inspector-apply-position").click();
  await page.getByTestId("workflow-composer-text").getByText("Review the product definition", { exact: true }).waitFor(); noBrowserDiagnostics();
  record({ id: "edit", state: "pass", label: "Edit and move the review block", summary: "The selected block changed definition and layout without changing unrelated identities.", purpose: "Demonstrate direct routine editing before invalid recovery.", action: "Changed the selected block title, purpose, X, and Y, then applied both edits.", controls: ["Title", "Purpose", "Apply definition", "X", "Y", "Apply position"], value: "Review the product definition; 720,96", expected: "Canvas, text, and inspector agree on the same stable block identity and new values.", actual: "All three surfaces show the edited block at layout 720,96; revision remains 1.", ...editScreen }, page.url());

  const deleteScreen = await capture(page, "07-delete-connection", [
    { selector: '[data-testid="workflow-connection-delete-connection.definition-to-review"]', label: "Delete connection" },
    { selector: '[data-testid="workflow-composer-canvas"]', label: "Current three-connection graph" },
  ]);
  await page.getByTestId("workflow-connection-delete-connection.definition-to-review").click();
  await page.getByTestId("workflow-composer-canvas").locator('[data-semantic-id="connection.definition-to-review"]').waitFor({ state: "detached" }); noBrowserDiagnostics();
  record({ id: "delete", state: "pass", label: "Remove one valid connection", summary: "The selected relationship was removed as one valid working-copy transaction.", purpose: "Create a valid opening for the corrected relationship.", action: "Clicked Delete connection for connection.definition-to-review.", controls: ["Delete connection"], expected: "Only that connection disappears; ports and saved revision remain unchanged.", actual: "The relationship count fell from three to two and revision remained 1.", ...deleteScreen }, page.url());

  const attemptScreen = await capture(page, "08-attempt-invalid", [
    { selector: '[data-testid="workflow-connection-source"]', label: "Source port" },
    { selector: '[data-testid="workflow-connection-target"]', label: "Target port" },
    { selector: '[data-testid="workflow-connection-create"]', label: "Create connection" },
  ]);
  await page.getByTestId("workflow-connection-source").selectOption("port.product-definition-out");
  await page.getByTestId("workflow-connection-target").selectOption("port.accepted-definition-out");
  await page.getByTestId("workflow-connection-create").click();
  const invalid = page.getByTestId("workflow-diagnostic-CONNECTION_TARGET_INVALID");
  await invalid.waitFor();
  await page.getByTestId("workflow-composer-diagnostics").scrollIntoViewIfNeeded();
  const invalidScreen = await capture(page, "09-invalid-contained", [
    { selector: '[data-testid="workflow-composer-diagnostics"]', label: "Rejected-edit explanation and correction" },
    { selector: '[data-semantic-id="port.accepted-definition-out"][data-diagnostic="true"]', label: "Affected target port" },
    { selector: '[aria-label="Working draft authority"]', label: "Unchanged revision 1 authority" },
  ]);
  if (!(await invalid.textContent())?.includes("Choose an existing input port")) throw new Error("Bounded correction was not visible");
  if ((await page.getByTestId("workflow-composer-canvas").locator('[data-semantic-id^="connection.draft-"]').count()) !== 0) throw new Error("Rejected connection leaked into the last-valid draft");
  noBrowserDiagnostics();
  record({ id: "invalid", state: "pass", label: "Contain an output-to-output connection", summary: "The invalid candidate was isolated with specific affected identities and correction; the two-connection last-valid draft and revision 1 remained unchanged.", purpose: "Prove invalid intent cannot corrupt working or saved state.", action: "Selected Product definition output as source, Accepted definition output as target, and clicked Create connection.", controls: ["Source port", "Target port", "Create connection"], value: "port.product-definition-out → port.accepted-definition-out", expected: "The invalid connection is rejected, affected identities are marked, and a bounded correction is shown.", actual: "CONNECTION_TARGET_INVALID identified the output target, stated it is not an input, and directed the engineer to choose an existing input; no candidate connection appeared.", ...invalidScreen, priorRaw: attemptScreen.raw }, page.url());

  await page.getByTestId("workflow-connection-target").selectOption("port.product-definition-in");
  await page.getByTestId("workflow-connection-create").click();
  await page.getByTestId("workflow-composer-diagnostics").waitFor({ state: "detached" });
  await page.getByTestId("workflow-composer-canvas").getByText("port.product-definition-out → port.product-definition-in", { exact: true }).waitFor();
  const correctedScreen = await capture(page, "10-corrected", [
    { selector: '[data-testid="workflow-connection-source"]', label: "Compatible output source" },
    { selector: '[data-testid="workflow-connection-target"]', label: "Compatible input target" },
    { selector: '[data-testid="workflow-composer-canvas"]', label: "Corrected three-connection graph" },
    { selector: '[data-testid="workflow-composer-text"]', label: "Matching corrected text projection" },
  ]); noBrowserDiagnostics();
  record({ id: "correct", state: "pass", label: "Apply the named connection correction", summary: "Choosing the compatible input cleared the diagnostic and restored a valid three-connection graph.", purpose: "Prove recovery preserves the earlier edit and produces a saveable candidate.", action: "Changed only the target to Product definition input and clicked Create connection.", controls: ["Target port", "Create connection"], value: "port.product-definition-out → port.product-definition-in", expected: "The correction clears the diagnostic and appears in both diagram and text.", actual: "The diagnostic cleared; the corrected connection appears in diagram and text while the review edit and position remain.", ...correctedScreen }, page.url());

  await page.getByTestId("workflow-composer-validate").click();
  await page.getByText("Validation passed. The working draft is structurally valid.", { exact: true }).waitFor();
  const validScreen = await capture(page, "11-validated", [
    { selector: '[data-testid="workflow-composer-validate"]', label: "Validate" },
    { selector: '[data-testid="workflow-composer-inspector"]', label: "Validation passed" },
  ]); noBrowserDiagnostics();
  record({ id: "validate", state: "pass", label: "Validate the recovered draft", summary: "Server validation accepted the corrected candidate.", purpose: "Verify the complete recovered graph before persistence.", action: "Clicked Validate.", controls: ["Validate"], expected: "Validation passes with no contradictory local or server diagnostic.", actual: "The status and inspector both report validation passed.", ...validScreen }, page.url());

  await page.getByTestId("workflow-composer-save").click();
  await page.getByText("Saved revision 2.", { exact: true }).waitFor();
  const saveScreen = await capture(page, "12-saved", [
    { selector: '[data-testid="workflow-composer-save"]', label: "Save draft" },
    { selector: '[aria-label="Working draft authority"]', label: "Saved revision 2" },
    { selector: '[data-testid="workflow-composer-canvas"]', label: "Saved corrected graph" },
  ]); noBrowserDiagnostics();
  record({ id: "save", state: "pass", label: "Save only the corrected draft", summary: "The valid recovered candidate advanced atomically to revision 2.", purpose: "Complete Checkpoint D without persisting the rejected candidate.", action: "Clicked Save draft after validation passed.", controls: ["Save draft"], expected: "Only the corrected candidate advances to revision 2.", actual: "Revision 2 saved with the edited review block and compatible connection; the rejected output-to-output relationship is absent.", ...saveScreen }, page.url());
} catch (error) {
  failure = error;
  let stopped = {};
  try { stopped = await capture(page, "99-stopped", [{ selector: "body", label: "Stopping screen" }]); } catch {}
  record({ id: "stopped", state: "blocked", label: "Walkthrough stopped", summary: `Stopped at the first unexpected condition: ${String(error)}`, purpose: "Preserve the stopping point without working around it.", action: "Stopped immediately.", controls: ["Current visible screen"], expected: "The next documented state renders without error, ambiguity, or missing capability.", actual: String(error), ...stopped }, page.url());
} finally {
  writeFileSync(path.join(root, "trace", "browser-diagnostics.json"), `${JSON.stringify(diagnostics, null, 2)}\n`, "utf8");
  await context.tracing.stop({ path: path.join(root, "trace", "trace.zip") });
  await browser.close();
}
if (failure) throw failure;
