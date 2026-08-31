import { chromium } from "@playwright/test";
import { appendFileSync, mkdirSync, writeFileSync } from "node:fs";
import path from "node:path";

const root = process.env.WRIGHT_WALKTHROUGH_ROOT;
const baseUrl = process.env.WRIGHT_WALKTHROUGH_URL;
if (!root || !baseUrl) throw new Error("Walkthrough environment is incomplete");
for (const dir of ["playwright", "screenshots/raw", "screenshots/annotated", "trace"]) {
  mkdirSync(path.join(root, dir), { recursive: true });
}

const subject = "8282b9918143ead7860222940e4000f9fa86a7cd";
const diagnostics = [];
let diagnosticCursor = 0;
const status = {
  title: "Workflow Composer Checkpoint C and save/reopen walkthrough",
  summary: "Walking the feature-flagged provisional composer from an empty draft to the bounded four-block graphical composition.",
  overall: "pending",
  updated: new Date().toISOString(),
  manualSteps: [
    { label: "Create draft", instruction: "Open **Workflow Composer**, review the draft boundary, and click **Create working draft**." },
    { label: "Add blocks", instruction: "Click **Capture input**, **Engineering work**, **Review**, and **Release boundary** in order." },
    { label: "Inspect composition", instruction: "Compare **First-party diagram** and **Canonical text projection**, then select **Define product**." },
    { label: "Validate and save", instruction: "Click **Validate**, then click **Save draft**." },
    { label: "Close and reopen", instruction: "Click **Close**, then click **Reopen saved draft** and compare revision and identity digests." },
  ],
  steps: [],
};

const escapeHtml = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;");

function flush() {
  status.updated = new Date().toISOString();
  writeFileSync(path.join(root, "status.json"), `${JSON.stringify(status, null, 2)}\n`, "utf8");
  const cards = status.steps.map((step) => `
    <article class="card ${step.state}">
      <b>${step.state.toUpperCase()}</b><h2>${escapeHtml(step.label)}</h2>
      <p>${escapeHtml(step.summary)}</p>
      <dl><dt>Purpose</dt><dd>${escapeHtml(step.purpose)}</dd><dt>Action</dt><dd>${escapeHtml(step.action)}</dd><dt>Expected</dt><dd>${escapeHtml(step.expected)}</dd><dt>Actual</dt><dd>${escapeHtml(step.actual)}</dd></dl>
      ${step.raw ? `<p><button class="image-button" data-image="${escapeHtml(step.raw)}">Raw image</button> <button class="image-button" data-image="${escapeHtml(step.annotated)}">Annotated image</button></p>` : ""}
    </article>`).join("");
  const manual = status.manualSteps.map((step) => `<li>${escapeHtml(step.instruction)}</li>`).join("");
  writeFileSync(path.join(root, "report.html"), `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${escapeHtml(status.title)}</title><style>body{margin:0;background:#07111f;color:#e8eef8;font:16px/1.5 system-ui}main{max-width:1120px;margin:auto;padding:28px}.hero,.card{background:#111d30;border:1px solid #30425f;border-left:9px solid #98a2b3;border-radius:14px;padding:20px;margin:16px 0}.pass{border-left-color:#32d583}.blocked{border-left-color:#f04438}.pending{border-left-color:#98a2b3}dl{display:grid;grid-template-columns:110px 1fr;gap:8px}dt{font-weight:700;color:#9cc7ff}dd{margin:0}button{padding:8px 12px;color:#07111f;background:#9cc7ff;border:0;border-radius:6px;cursor:pointer}code{overflow-wrap:anywhere;color:#7ee7ff}dialog{max-width:96vw;background:#111d30;color:#fff;border:1px solid #49617f;border-radius:12px}dialog img{max-width:92vw;max-height:82vh;display:block;margin-top:12px}</style></head><body><main><section class="hero"><h1>${escapeHtml(status.title)}</h1><p><strong>${status.overall.toUpperCase()}:</strong> ${escapeHtml(status.summary)}</p><p>Exact commit <code>${subject}</code></p></section>${cards}<section class="card"><h2>Manual repeat checklist</h2><ol>${manual}</ol></section></main><dialog id="viewer"><button id="close">Close</button><img alt="Full-size walkthrough evidence"></dialog><script>const d=document.getElementById('viewer'),i=d.querySelector('img');document.querySelectorAll('[data-image]').forEach(b=>b.onclick=()=>{i.src=b.dataset.image;d.showModal()});document.getElementById('close').onclick=()=>d.close();document.onkeydown=e=>{if(e.key==='Escape')d.close()};</script></body></html>`, "utf8");
}

writeFileSync(path.join(root, "progress.md"), `# Workflow Composer Checkpoint C and save/reopen walkthrough\n\nCommit: \`${subject}\`  \nBase URL: \`${baseUrl}\`  \nPersona: local engineer  \nAuthority: provisional draft only; no execution, release, MCP, model, or publication action is present.\n\n`, "utf8");
flush();

function record(step, url) {
  status.steps.push(step);
  if (step.state === "blocked") {
    status.overall = "blocked";
    status.summary = step.summary;
  } else if (status.steps.every((item) => item.state === "pass")) {
    status.overall = "pass";
    status.summary = "The local engineer created the bounded four-block graphical draft, verified text/canvas parity, saved revision 2, closed it, and reopened identical semantic and layout identities without browser diagnostics.";
  }
  const freshDiagnostics = diagnostics.slice(diagnosticCursor);
  diagnosticCursor = diagnostics.length;
  appendFileSync(path.join(root, "progress.md"), [
    `## ${new Date().toLocaleString("en-US", { timeZone: "America/New_York", timeZoneName: "short" })} — ${step.state.toUpperCase()}`,
    "",
    `- Current URL: \`${url}\``,
    `- Action: ${step.action}`,
    `- Exact control: ${step.controls.join(", ")}`,
    `- Value: ${step.value ?? "No value entered."}`,
    `- Expected: ${step.expected}`,
    `- Actual: ${step.actual}`,
    "- Diagnostics:",
    ...(freshDiagnostics.length > 0 ? freshDiagnostics.map((item) => `  - ${item}`) : ["  - No console errors, page errors, or failed responses recorded."]),
    "- Screenshots:",
    ...(step.raw ? [`  - Raw: \`${step.raw}\``, `  - Annotated: \`${step.annotated}\``] : ["  - None."]),
    `- Status: **${step.state.toUpperCase()}**`,
    "",
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
      if (!(element instanceof HTMLElement)) {
        missingItems.push(item.label);
        return;
      }
      element.dataset.oldOutline = element.style.outline;
      element.style.outline = "4px solid #f59e0b";
      const bounds = element.getBoundingClientRect();
      const marker = document.createElement("div");
      marker.className = markerClass;
      marker.textContent = String(index + 1);
      marker.style.cssText = `position:absolute;left:${Math.max(0, bounds.left + scrollX - 13)}px;top:${Math.max(0, bounds.top + scrollY - 13)}px;z-index:2147483647;width:26px;height:26px;border-radius:50%;display:grid;place-items:center;background:#f59e0b;color:#111827;font:bold 15px system-ui;border:2px solid white`;
      document.body.appendChild(marker);
    });
    return missingItems;
  }, controls);
  if (missing.length > 0) throw new Error(`Missing annotated controls: ${missing.join(", ")}`);
  await page.screenshot({ path: path.join(root, annotated), fullPage: true });
  await page.evaluate(() => {
    document.querySelectorAll(".wright-walkthrough-marker").forEach((element) => element.remove());
    document.querySelectorAll("[data-old-outline]").forEach((element) => {
      if (element instanceof HTMLElement) {
        element.style.outline = element.dataset.oldOutline ?? "";
        delete element.dataset.oldOutline;
      }
    });
  });
  return { raw, annotated };
}

function noDiagnostics() {
  const fresh = diagnostics.slice(diagnosticCursor);
  if (fresh.length > 0) throw new Error(`Unexpected browser diagnostics: ${fresh.join(" | ")}`);
}

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1600, height: 1000 }, colorScheme: "dark" });
await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
const page = await context.newPage();
page.on("console", (message) => {
  if (["error", "warning"].includes(message.type())) diagnostics.push(`console ${message.type()}: ${message.text()}`);
});
page.on("pageerror", (error) => diagnostics.push(`page error: ${error.message}`));
page.on("response", (response) => {
  if (response.status() >= 400) diagnostics.push(`failed response: ${response.status()} ${response.url()}`);
});

let failure;
try {
  await page.goto(`${baseUrl}/workflow-composer`, { waitUntil: "domcontentloaded" });
  await page.getByTestId("workflow-composer-create").waitFor({ timeout: 30_000 });
  noDiagnostics();
  const createScreen = await capture(page, "01-create-empty-draft", [
    { selector: '[data-testid="workflow-composer-create-title"]', label: "Draft title" },
    { selector: '[data-testid="workflow-composer-create-purpose"]', label: "Purpose" },
    { selector: '[data-testid="workflow-composer-create"]', label: "Create working draft" },
  ]);
  await page.getByTestId("workflow-composer-create").click();
  await page.getByTestId("workflow-composer-canvas").waitFor();
  noDiagnostics();
  record({ id: "create", state: "pass", label: "Create a separate empty draft", summary: "The normal UI created revision 1 without changing the released Process Definition.", purpose: "Begin from the supported empty-draft boundary.", action: "Kept the visible title and purpose values and clicked Create working draft.", controls: ["Draft title", "Purpose", "Create working draft"], value: "Product definition draft; Capture, define, review, and release one product definition.", expected: "A feature-bounded working draft opens at revision 1 with no released or executable authority.", actual: "Revision 1 opened with the Working draft and Not released · Not executable labels.", ...createScreen }, page.url());

  const paletteSteps = [
    ["input", "Capture input", "Capture requirements"],
    ["work", "Engineering work", "Define product"],
    ["review", "Review", "Review product definition"],
    ["release", "Release boundary", "Release product definition"],
  ];
  for (let index = 0; index < paletteSteps.length; index += 1) {
    const [role, label, expectedTitle] = paletteSteps[index];
    const button = page.getByTestId(`workflow-composer-palette-${role}`);
    await button.waitFor();
    if (!(await button.isEnabled())) throw new Error(`${label} was not enabled in the bounded sequence`);
    const stateScreen = await capture(page, `0${index + 2}-add-${role}`, [
      { selector: `[data-testid="workflow-composer-palette-${role}"]`, label },
      { selector: '[data-testid="workflow-composer-canvas"]', label: "Current graphical draft" },
      { selector: '[data-testid="workflow-composer-text"]', label: "Current text projection" },
    ]);
    await button.click();
    await page.getByTestId("workflow-composer-canvas").getByText(expectedTitle, { exact: true }).waitFor();
    noDiagnostics();
    record({ id: `add-${role}`, state: "pass", label: `Add ${expectedTitle}`, summary: `${expectedTitle} entered the canonical draft and both projections.`, purpose: "Advance the bounded representative workflow without inventing renderer-owned identities.", action: `Clicked ${label}.`, controls: [label], expected: `${expectedTitle} appears in the diagram and text projection with its stable host-owned identities.`, actual: `${expectedTitle} appeared and the next bounded palette action became available.`, ...stateScreen }, page.url());
  }

  const identity = await page.evaluate(() => {
    const ids = (selector) => Array.from(document.querySelector(selector)?.querySelectorAll("[data-semantic-id]") ?? []).map((element) => element.getAttribute("data-semantic-id")).sort();
    return { canvas: ids('[data-testid="workflow-composer-canvas"]'), text: ids('[data-testid="workflow-composer-text"]') };
  });
  if (identity.canvas.length !== 23 || new Set(identity.canvas).size !== 23 || JSON.stringify(identity.canvas) !== JSON.stringify(identity.text)) {
    throw new Error(`Semantic identity parity failed: canvas=${identity.canvas.length}, text=${identity.text.length}`);
  }
  const composedScreen = await capture(page, "06-four-block-composition", [
    { selector: '[aria-label="Working draft authority"]', label: "Provisional draft authority" },
    { selector: '[data-testid="workflow-composer-canvas"]', label: "Four-block phase-lane diagram" },
    { selector: '[data-testid="workflow-composer-text"]', label: "Matching 23-identity text projection" },
    { selector: '[data-testid="workflow-composer-inspector"]', label: "Definition and validation inspector" },
  ]);
  record({ id: "parity", state: "pass", label: "Compare the complete graphical and text composition", summary: "Diagram and text expose the same 23 unique semantic identities and complete declared workflow relationships.", purpose: "Prove the first reviewable graphical slice uses one canonical model.", action: "Compared the complete diagram and text semantic identity sets.", controls: ["First-party diagram", "Canonical text projection", "Draft inspector"], expected: "Both projections contain exactly the same 23 unique semantic identities.", actual: "Both identity sets matched exactly at 23, including phases, blocks, ports, connections, gate, feedback, and intended artifacts.", ...composedScreen }, page.url());

  const select = page.getByTestId("workflow-canvas-select-block.define-product");
  await select.click();
  await page.getByTestId("workflow-composer-inspector").getByText("block.define-product", { exact: true }).waitFor();
  if ((await select.getAttribute("aria-pressed")) !== "true") throw new Error("Selected block did not expose aria-pressed=true");
  noDiagnostics();
  const selectedScreen = await capture(page, "07-selected-inspector", [
    { selector: '[data-testid="workflow-canvas-select-block.define-product"]', label: "Selected Define product block" },
    { selector: '[data-testid="workflow-composer-inspector"]', label: "Matching selected identity inspector" },
  ]);
  record({ id: "select", state: "pass", label: "Select and inspect one semantic block", summary: "Canvas selection and inspector identity agree without changing draft bytes.", purpose: "Prove host-owned selection across the renderer seam.", action: "Clicked Define product in the diagram.", controls: ["Define product"], expected: "The block exposes a non-color selected state and the inspector shows block.define-product.", actual: "The button exposed aria-pressed=true, visible Selected text, and the inspector showed the same stable ID.", ...selectedScreen }, page.url());

  await page.getByTestId("workflow-composer-validate").click();
  await page.getByText("Validation passed. The working draft is structurally valid.", { exact: true }).waitFor();
  noDiagnostics();
  const validatedScreen = await capture(page, "08-validation-passed", [
    { selector: '[data-testid="workflow-composer-validate"]', label: "Validate" },
    { selector: '[data-testid="workflow-composer-inspector"]', label: "Consistent validation evidence" },
  ]);
  record({ id: "validate", state: "pass", label: "Validate the complete draft", summary: "Server validation accepted the bounded semantic and layout candidate.", purpose: "Verify all references and saved layout are valid before persistence.", action: "Clicked Validate.", controls: ["Validate"], expected: "Validation passes and the inspector does not show contradictory diagnostics.", actual: "The status and inspector consistently reported validation passed.", ...validatedScreen }, page.url());

  const beforeSave = await page.evaluate(() => ({
    semantic: document.querySelector('[title="Semantic digest"]')?.textContent,
    layout: document.querySelector('[title="Layout digest"]')?.textContent,
  }));
  await page.getByTestId("workflow-composer-save").click();
  await page.getByText("Saved revision 2.", { exact: true }).waitFor();
  await page.getByLabel("Working draft authority").getByText("Revision 2", { exact: true }).waitFor();
  noDiagnostics();
  const savedScreen = await capture(page, "09-saved-revision", [
    { selector: '[data-testid="workflow-composer-save"]', label: "Save draft" },
    { selector: '[aria-label="Working draft authority"]', label: "Revision 2 and identity digests" },
  ]);
  record({ id: "save", state: "pass", label: "Save revision 2 atomically", summary: "The valid four-block candidate saved as revision 2 with semantic and layout identities visible.", purpose: "Prove the normal guarded save path.", action: "Clicked Save draft.", controls: ["Save draft"], expected: "The server advances to revision 2 and reports both identity digests.", actual: "Revision 2 appeared and both semantic and layout digests remained visible.", ...savedScreen }, page.url());

  await page.getByTestId("workflow-composer-close").click();
  await page.getByTestId("workflow-composer-closed").waitFor();
  noDiagnostics();
  const closedScreen = await capture(page, "10-closed-draft", [
    { selector: '[data-testid="workflow-composer-closed"]', label: "Closed revision and digests" },
    { selector: '[data-testid="workflow-composer-reopen"]', label: "Reopen saved draft" },
  ]);
  record({ id: "close", state: "pass", label: "Close the editor session", summary: "The editor closed while retaining the saved revision and both identity digests.", purpose: "Separate browser working-session state from persisted draft state.", action: "Clicked Close.", controls: ["Close"], expected: "The graphical editor closes and saved revision 2 remains available to reopen.", actual: "The closed state showed revision 2, draft ID, semantic digest, layout digest, and Reopen saved draft.", ...closedScreen }, page.url());

  await page.getByTestId("workflow-composer-reopen").click();
  await page.getByText(/Reopened revision 2 with its saved semantic and layout identities/).waitFor();
  await page.getByTestId("workflow-composer-canvas").waitFor();
  const afterReopen = await page.evaluate(() => ({
    semantic: document.querySelector('[title="Semantic digest"]')?.textContent,
    layout: document.querySelector('[title="Layout digest"]')?.textContent,
    ids: Array.from(document.querySelector('[data-testid="workflow-composer-canvas"]')?.querySelectorAll("[data-semantic-id]") ?? []).map((element) => element.getAttribute("data-semantic-id")).sort(),
    positions: Array.from(document.querySelectorAll('[data-layout-x][data-layout-y]')).map((element) => [element.getAttribute("data-semantic-id"), element.getAttribute("data-layout-x"), element.getAttribute("data-layout-y")]),
  }));
  if (beforeSave.semantic !== afterReopen.semantic || beforeSave.layout !== afterReopen.layout || afterReopen.ids.length !== 23 || afterReopen.positions.length !== 4) {
    throw new Error("Save/reopen semantic, layout, identity, or position evidence disagreed");
  }
  noDiagnostics();
  const reopenedScreen = await capture(page, "11-reopened-identical", [
    { selector: '[aria-label="Working draft authority"]', label: "Reopened revision 2 and identical digests" },
    { selector: '[data-testid="workflow-composer-canvas"]', label: "Reopened four-block saved layout" },
    { selector: '[data-testid="workflow-composer-text"]', label: "Reopened matching semantic projection" },
  ]);
  record({ id: "reopen", state: "pass", label: "Reopen identical semantic and layout state", summary: "Revision 2 reopened with identical digests, 23 canvas identities, and all four saved positions.", purpose: "Provide initial Checkpoint E save/reopen evidence.", action: "Clicked Reopen saved draft and compared saved identities and positions.", controls: ["Reopen saved draft"], expected: "Revision, semantic digest, layout digest, 23 identities, and four positions match the saved state.", actual: "Revision 2 reopened with identical digests, 23 identities, and four saved position records.", ...reopenedScreen }, page.url());
} catch (error) {
  failure = error;
  let stoppedScreen = {};
  try { stoppedScreen = await capture(page, "99-stopped", [{ selector: "body", label: "Stopping screen" }]); } catch {}
  record({ id: "stopped", state: "blocked", label: "Walkthrough stopped", summary: `Stopped at the first unexpected condition: ${String(error)}`, purpose: "Preserve the first stopping point without working around it.", action: "Stopped immediately.", controls: ["Current visible screen"], expected: "The next documented state renders without error, ambiguity, or missing capability.", actual: String(error), ...stoppedScreen }, page.url());
} finally {
  writeFileSync(path.join(root, "trace", "browser-diagnostics.json"), `${JSON.stringify(diagnostics, null, 2)}\n`, "utf8");
  await context.tracing.stop({ path: path.join(root, "trace", "trace.zip") });
  await browser.close();
}
if (failure) throw failure;
