// Real-browser, human-repeatable image-led authoring acceptance. No route mocks.
import { createRequire } from "node:module";
import { appendFileSync, mkdirSync, writeFileSync, readFileSync, copyFileSync, readdirSync, mkdtempSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repo = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const require = createRequire(path.join(repo, "apps/web/package.json"));
const { chromium, expect } = require("@playwright/test");
const args = Object.fromEntries(process.argv.slice(2).map((item) => { const i = item.indexOf("="); return [item.slice(2, i), item.slice(i + 1)]; }));
const mode = args.mode ?? "shell";
const full = mode === "functional" || mode === "final";
const needsZoom = full || mode === "zoom";
const label = args.label ?? `${mode}-continuation`;
const started = new Date().toISOString();
const stamp = started.replace(/[-:]/g, "").replace(/\.\d+Z/, "Z");
const root = path.join(repo, "artifacts/ui-walkthrough/image-redesign", `${stamp}-${label}`);
for (const dir of ["playwright", "screenshots/raw", "screenshots/annotated", "trace"]) mkdirSync(path.join(root, dir), { recursive: true });
copyFileSync(fileURLToPath(import.meta.url), path.join(root, "playwright/capture_image_redesign.mjs"));
const git = (...values) => execFileSync("git", values, { cwd: repo, encoding: "utf8" }).trim();
const workflowPath = args.path ?? `workflows/image-redesign-acceptance-${stamp.toLowerCase()}.workflow.wflow`;
const untrackedImplementation = () => git("ls-files", "--others", "--exclude-standard").split("\n").filter((file) => /^(apps|packages|scripts|src|tests)\//.test(file));
const subject = { commit: git("rev-parse", "HEAD"), tree: git("show", "-s", "--format=%T", "HEAD"), dirty: git("status", "--porcelain", "--untracked-files=no"), untrackedImplementation: untrackedImplementation(), label, mode, url: args.url, workflowPath: full ? workflowPath : null, started };
const servedPaths = [
  "components/chat/WorkspacePanel.tsx", "components/pages/WorkflowRecoveryPage.tsx", "services/workspace-service.ts",
  ...["WorkflowRecoveryConcept.tsx", "ReactFlowRecoveryCanvas.tsx", "AuthoringControls.tsx", "WorkflowObjectIcon.tsx", "authoring-objects.ts", "authoring-positioning.ts", "recovery-authoring.ts", "command-system.ts", "model.ts", "canonical-wire.ts", "workflow-recovery.css"].map((file) => `prototypes/workflow-recovery/${file}`),
];
const normalizedSource = (source) => source.replace(/\r\n/g, "\n");
const sha = (source) => createHash("sha256").update(source).digest("hex");
const expectedServedSources = new Map(servedPaths.map((file) => { const repositoryPath = `apps/web/src/${file}`; const rawSource = mode === "final" ? execFileSync("git", ["show", `${subject.commit}:${repositoryPath}`], { cwd: repo, encoding: "utf8" }) : readFileSync(path.join(repo, repositoryPath), "utf8"); return [`/src/${file}`, { repositoryPath, source: normalizedSource(rawSource), rawSha256: sha(rawSource) }]; }));
const servedChecks = [], servedTasks = [];
function inspectServedModule(response) {
  const pathname = new URL(response.url()).pathname; const expected = expectedServedSources.get(pathname); if (!expected || response.status() !== 200) return;
  servedTasks.push(response.text().then((transformed) => {
    let source;
    if (pathname.endsWith(".css")) { const embedded = /const __vite__css = ("(?:\\.|[^"\\])*")/.exec(transformed); if (embedded) source = JSON.parse(embedded[1]); }
    else { const embedded = /sourceMappingURL=data:application\/json;base64,([^\s]+)/.exec(transformed); if (embedded) { const map = JSON.parse(Buffer.from(embedded[1], "base64").toString("utf8")); const index = map.sources?.findIndex((file) => path.basename(file) === path.basename(pathname)); source = map.sourcesContent?.[index >= 0 ? index : 0]; } }
    const actualSha256 = typeof source === "string" ? sha(normalizedSource(source)) : null; const expectedSha256 = sha(expected.source);
    servedChecks.push({ path: expected.repositoryPath, url: response.url(), method: pathname.endsWith(".css") ? "actual browser-loaded Vite CSS module content" : "actual browser-loaded module inline sourcemap sourcesContent", lineEndingNormalization: "CRLF to LF only; comparison hashes are normalized, not raw byte identity", expectedSource: mode === "final" ? `git:${subject.commit}` : "recorded working-tree source snapshot", expectedRawSha256: expected.rawSha256, actualRawSha256: typeof source === "string" ? sha(source) : null, expectedSha256, actualSha256, matches: actualSha256 === expectedSha256 });
  }).catch((error) => { servedChecks.push({ path: expected.repositoryPath, url: response.url(), matches: false, error: String(error) }); }));
}
async function verifyServedSubject() {
  await Promise.all(servedTasks);
  const missing = [...expectedServedSources.values()].map((item) => item.repositoryPath).filter((file) => !servedChecks.some((check) => check.path === file));
  const mismatches = servedChecks.filter((check) => !check.matches);
  writeFileSync(path.join(root, "served-subject.json"), JSON.stringify({ subjectCommit: subject.commit, assertion: mode === "final" ? "Actual loaded frontend source text matches the exact committed subject after CRLF-to-LF normalization only; raw hashes are also recorded." : "Actual loaded frontend source text matches the recorded working-tree snapshot after CRLF-to-LF normalization; this is not committed acceptance.", backendAuthority: "Not inferred from frontend evidence. Requires separate controlled API process/restart provenance.", missing, mismatches, checks: servedChecks }, null, 2));
  if (missing.length || mismatches.length) throw new Error(`Served frontend source provenance failed: missing ${missing.join(", ") || "none"}; mismatched ${mismatches.map((item) => item.path).join(", ") || "none"}`);
}
writeFileSync(path.join(root, "subject.json"), JSON.stringify(subject, null, 2));
writeFileSync(path.join(root, "progress.md"), `# Image-led authoring — ${label}\n\nStarted ${started} (UTC).\nCommit ${subject.commit}; tracked changes: ${subject.dirty ? "yes — working-tree verification, not exact-subject acceptance" : "none"}.\n\nNo route mocks. No unrelated user files deleted. ${full ? `A new evidence-only workflow will be created through the normal workspace UI: ${workflowPath}.` : "Shell-only review."}\n`);
const diagnostics = { console: [], pageErrors: [], failedRequests: [], httpErrors: [] };
const expectedHttp = new Set();
const status = { title: `Wright image-led authoring — ${label}`, summary: "Browser review in progress.", overall: "pending", updated: started, manualSteps: [], steps: [] };
const esc = (text) => String(text ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
let browser, context, page, zoomWorker, active = null, tracing = false;
const mutations = [];
function writeReport() {
  status.updated = new Date().toISOString();
  writeFileSync(path.join(root, "status.json"), JSON.stringify(status, null, 2));
  writeFileSync(path.join(root, "trace/browser-diagnostics.json"), JSON.stringify(diagnostics, null, 2));
  writeFileSync(path.join(root, "mutations.json"), JSON.stringify(mutations, null, 2));
  const cards = status.steps.map((step) => `<section class="${step.state}"><b>${step.state.toUpperCase()}</b><h2>${esc(step.label)}</h2><p>${esc(step.actual)}</p><p>Expected: ${esc(step.expected)}</p>${[...new Set([step.beforeRaw, step.beforeAnnotated, ...(step.evidenceImages ?? []), step.raw, step.annotated].filter(Boolean))].map((image) => `<button class="image-button" data-image="${esc(image)}">${esc(path.basename(image, ".png"))} · ${image.includes("annotated") ? "Annotated" : "Raw"}</button>`).join(" ")}</section>`).join("");
  writeFileSync(path.join(root, "report.html"), `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(status.title)}</title><style>body{background:#09111d;color:#e5edf8;font:15px/1.5 system-ui;margin:24px auto;max-width:1180px;padding:16px}section{border:1px solid #34435a;border-left:6px solid #8292a8;border-radius:8px;padding:18px;margin:16px 0;background:#101c2d}.pass{border-left-color:#20bd81}.blocked{border-left-color:#f46c76}button{background:#203753;color:white;border:1px solid #47729c;padding:8px;cursor:pointer}a{color:#68cfff}dialog{background:#101c2d;max-width:96vw;max-height:96vh}dialog img{display:block;max-width:92vw;max-height:84vh}</style><h1>${esc(status.title)}</h1><p>${esc(status.summary)}</p><p>Commit ${subject.commit} · ${subject.dirty ? "working-tree verification" : "clean subject"}</p><p><a href="progress.md">Progress</a> · <a href="subject.json">Subject</a> · <a href="mutations.json">Created/changed files</a> · <a href="trace/browser-diagnostics.json">Diagnostics</a></p>${cards}<h2>Manual repeat checklist</h2><ol>${status.manualSteps.map((step) => `<li>${esc(step.instruction)}</li>`).join("")}</ol><dialog><button id="close">Close</button><img alt="Full-size evidence"></dialog><script>const d=document.querySelector('dialog');document.querySelectorAll('[data-image]').forEach(b=>b.onclick=()=>{d.querySelector('img').src=b.dataset.image;d.showModal()});document.querySelector('#close').onclick=()=>d.close();document.addEventListener('keydown',e=>{if(e.key==='Escape'&&d.open)d.close()})</script></html>`);
}
writeReport();
// Workspace tabs are retained deliberately; operate only on the visible tab.
const tid = (id) => page.getByTestId(id).filter({ visible: true });
function logAction(action, value = "") {
  appendFileSync(path.join(root, "progress.md"), `\n- ${new Date().toISOString()} UTC · PASS control action · ${action}${value ? ` · value: ${value}` : ""} · URL: ${page?.url() ?? "browser unavailable"} · expected: ${active?.expected ?? "startup"} · actual: browser action completed; step assertions are recorded separately below · raw before: ${active?.beforeRaw ?? "startup navigation"} · annotated before: ${active?.beforeAnnotated ?? "startup navigation"} · captured states: ${(active?.evidenceImages ?? []).join(", ") || "initial navigation"} · diagnostics: ${JSON.stringify(diagnostics)}\n`);
  writeReport();
}
async function click(id) { await tid(id).click(); logAction(`Click ${id}`); }
async function fill(id, value) { await tid(id).fill(value); logAction(`Fill ${id}`, value); }
async function capture(id, markers = []) {
  const images = { raw: `screenshots/raw/${id}.png`, annotated: `screenshots/annotated/${id}.png` };
  await page.screenshot({ path: path.join(root, images.raw) });
  try {
    await page.evaluate((items) => {
      const legend = document.createElement("aside"); legend.className = "wright-walkthrough-overlay";
      legend.style.cssText = "position:fixed;right:12px;bottom:12px;z-index:2147483647;max-width:340px;padding:12px;background:#101c2d;color:white;border:2px solid #38bdf8;font:13px/1.5 system-ui;pointer-events:none";
      const list = document.createElement("ol");
      for (const { testId, label } of items) {
        const target = [...document.querySelectorAll(`[data-testid="${testId}"]`)].find((node) => node.getBoundingClientRect().width > 0); if (!target) continue;
        const index = list.children.length + 1; const row = document.createElement("li"); row.textContent = label; list.appendChild(row);
        const b = target.getBoundingClientRect(); const marker = document.createElement("div"); marker.className = "wright-walkthrough-overlay"; marker.textContent = String(index);
        marker.style.cssText = `position:fixed;left:${Math.max(0, b.left)}px;top:${Math.max(0, b.top)}px;z-index:2147483647;border:2px solid white;border-radius:20px;background:#0079cd;color:white;padding:1px 7px;font:14px system-ui;pointer-events:none`; document.body.appendChild(marker);
      }
      if (list.children.length) { legend.append(list); document.body.appendChild(legend); }
    }, markers);
    await page.screenshot({ path: path.join(root, images.annotated) });
  } finally { await page.evaluate(() => document.querySelectorAll(".wright-walkthrough-overlay").forEach((node) => node.remove())); }
  if (active) active.evidenceImages = [...(active.evidenceImages ?? []), images.raw, images.annotated];
  return images;
}
function diagnosticFailures() {
  return [...diagnostics.pageErrors, ...diagnostics.failedRequests.filter((r) => !r.error?.includes("ERR_ABORTED")).map((r) => JSON.stringify(r)), ...diagnostics.httpErrors.filter((r) => !expectedHttp.has(`${r.status}:${r.url}`)).map((r) => JSON.stringify(r)), ...diagnostics.console.filter((r) => !expectedHttp.has(`404:${r.url}`) && !expectedHttp.has(`409:${r.url}`)).map((r) => JSON.stringify(r))];
}
const plans = [];
function add(id, label, instruction, expected, action, markers = []) {
  const record = { id, state: "pending", label, summary: "Not reached", purpose: label, action: instruction, controls: markers.map((m) => m.label), expected, actual: "Not yet reached" };
  status.steps.push(record); status.manualSteps.push({ label, instruction }); plans.push({ record, action, markers });
}
async function showInput(id) { await click("workflow-recovery-inputs-toggle"); await click(`workflow-recovery-input-navigate-${id}`); }
async function selectSettings(id) {
  if (id.startsWith("block.text-input-") || id.startsWith("block.file-input-")) await showInput(id);
  else { await click("workflow-recovery-canvas-fit"); await click(`workflow-recovery-block-${id}`); }
  await click("workflow-recovery-inspector-tab-definition");
}
async function create(group, template, id) {
  await click(`workflow-recovery-create-group-${group}`); await capture(`${active.id}-menu`, [{ testId: `workflow-recovery-create-template-${template}`, label: `Create ${template}` }]);
  await click(`workflow-recovery-create-template-${template}`); await expect(tid(`workflow-recovery-block-${id}`)).toBeVisible(); await expect(tid(`workflow-recovery-block-title-${id}`)).toBeFocused();
}
async function sourceText() { await click("workflow-recovery-view-code"); const value = await tid("workflow-recovery-source-editor").inputValue(); await click("workflow-recovery-view-diagram"); return value; }
async function connect(from, to, relationship) {
  await tid(`workflow-recovery-handle-${from}`).focus(); await page.keyboard.press("Enter"); logAction(`Focus ${from} and press Enter`);
  await tid(`workflow-recovery-handle-${to}`).focus(); await page.keyboard.press("Enter"); logAction(`Focus ${to} and press Enter`);
  await expect(tid(`workflow-recovery-edge-${relationship}`)).toHaveCount(1);
}
async function verifyOutputPreviewLayout(label, browserTabZoomFactor = 1) {
  const backdrop = tid("workflow-recovery-modal-backdrop");
  const overlay = await backdrop.evaluate((element) => {
    const bounds = element.getBoundingClientRect();
    const samples = [
      { label: "top-left workspace chrome", x: 4, y: 4 }, { label: "global header", x: innerWidth / 2, y: 20 }, { label: "top-right header", x: innerWidth - 4, y: 20 },
      { label: "left activity bar", x: 20, y: innerHeight / 2 }, { label: "small-window surface/chat switcher", x: innerWidth / 2, y: 60 },
      { label: "bottom-left chrome", x: 4, y: innerHeight - 4 }, { label: "bottom-right chrome", x: innerWidth - 4, y: innerHeight - 4 },
    ].map((point) => { const hit = document.elementFromPoint(point.x, point.y); return { ...point, hitInsideOverlay: hit === element || element.contains(hit), hitTag: hit?.tagName, hitTestId: hit?.getAttribute("data-testid") }; });
    const header = element.querySelector(".recovery-modal > header"); const headerBounds = header?.getBoundingClientRect();
    const headerCenter = headerBounds ? document.elementFromPoint(headerBounds.x + headerBounds.width / 2, headerBounds.y + headerBounds.height / 2) : null;
    return { parentIsBody: element.parentElement === document.body, bounds: bounds.toJSON(), viewport: { width: innerWidth, height: innerHeight }, samples, headerBounds: headerBounds?.toJSON(), headerCenterInsideHeader: Boolean(header && (header === headerCenter || header.contains(headerCenter))) };
  });
  writeFileSync(path.join(root, `24-output-overlay-${label}.json`), JSON.stringify(overlay, null, 2));
  expect(overlay.parentIsBody, "Modal must escape the retained-tab stacking context").toBe(true); expect(overlay.bounds.x).toBe(0); expect(overlay.bounds.y).toBe(0);
  // Real 200% zoom can produce a half-CSS-pixel viewport while innerWidth and
  // innerHeight report integers. Allow only that browser rounding difference.
  expect(Math.abs(overlay.bounds.width - overlay.viewport.width)).toBeLessThanOrEqual(1); expect(Math.abs(overlay.bounds.height - overlay.viewport.height)).toBeLessThanOrEqual(1);
  expect(overlay.samples.filter((point) => !point.hitInsideOverlay), `Workspace chrome must not paint above the modal at ${label}`).toEqual([]); expect(overlay.headerCenterInsideHeader, `Modal header must not be occluded at ${label}`).toBe(true);
  const closeTarget = await tid("workflow-recovery-modal-close").evaluate((element) => { const box = element.getBoundingClientRect(); const hit = document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2); return { box: box.toJSON(), hitIsControl: hit === element || element.contains(hit) }; });
  overlay.closeTarget = closeTarget; writeFileSync(path.join(root, `24-output-overlay-${label}.json`), JSON.stringify(overlay, null, 2)); expect(closeTarget.hitIsControl, `Close control must not be occluded at ${label}`).toBe(true);
  const panel = page.locator(".output-preview > aside").filter({ visible: true }); await expect(panel).toBeVisible();
  const measurements = await panel.evaluate((element) => {
    const bounds = element.getBoundingClientRect(); const modal = element.closest('[role="dialog"]')?.getBoundingClientRect();
    const lines = [...element.querySelectorAll("b, span, a")].flatMap((child) => { const range = document.createRange(); range.selectNodeContents(child); return [...range.getClientRects()].map((line) => ({ text: child.textContent, x: line.x, right: line.right, y: line.y, height: line.height })); });
    return { viewport: { width: innerWidth, height: innerHeight, dpr: devicePixelRatio }, panel: bounds.toJSON(), modal: modal?.toJSON(), panelScrollWidth: element.scrollWidth, panelClientWidth: element.clientWidth, lines, escapedLines: lines.filter((line) => line.x < bounds.x - 1 || line.right > bounds.right + 1) };
  });
  measurements.browserTabZoomFactor = browserTabZoomFactor; measurements.zoomMethod = browserTabZoomFactor === 2 ? "chrome.tabs.setZoom/getZoom; actual browser zoom" : "Ordinary viewport resize at 100% browser zoom";
  writeFileSync(path.join(root, `24-output-layout-${label}.json`), JSON.stringify(measurements, null, 2));
  expect(measurements.panelScrollWidth, `Output panel horizontal overflow at ${label}`).toBeLessThanOrEqual(measurements.panelClientWidth + 1);
  expect(measurements.escapedLines, `Filename, checksum, lineage or action text clips outside output panel at ${label}`).toEqual([]);
  expect(measurements.panel.x).toBeGreaterThanOrEqual((measurements.modal?.x ?? 0) - 1); expect(measurements.panel.x + measurements.panel.width).toBeLessThanOrEqual((measurements.modal?.x ?? 0) + (measurements.modal?.width ?? measurements.viewport.width) + 1);
  measurements.controls = [];
  for (const id of ["workflow-recovery-output-open-artifact.step", "workflow-recovery-output-download-artifact.step"]) {
    await tid(id).scrollIntoViewIfNeeded(); logAction(`Scroll output preview to ${id}`, "Inspect only; no external report opened or file downloaded");
    const target = await tid(id).evaluate((element) => { const box = element.getBoundingClientRect(); const hit = document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2); return { box: box.toJSON(), scrollWidth: element.scrollWidth, clientWidth: element.clientWidth, hitIsControl: hit === element || element.contains(hit) }; });
    measurements.controls.push({ id, ...target }); writeFileSync(path.join(root, `24-output-layout-${label}.json`), JSON.stringify(measurements, null, 2));
    expect(target.hitIsControl, `Output action must be hittable at ${label}`).toBe(true); expect(target.scrollWidth).toBeLessThanOrEqual(target.clientWidth + 1); expect(target.box.y).toBeGreaterThanOrEqual(0); expect(target.box.y + target.box.height).toBeLessThanOrEqual(measurements.viewport.height + 1);
  }
  await capture(`24-output-preview-${label}`, [{ testId: "workflow-recovery-output-open-artifact.step", label: "Fully visible demo report action" }, { testId: "workflow-recovery-output-download-artifact.step", label: "Fully visible demo download action; not pressed" }]);
}
const textOne = "Support a 400 N pump load. Use stainless steel. Review the mounting interface before releasing drawings.";
const textTwo = "Company practice: retain accessible fasteners and record assumptions separately from supplied requirements.";
let savedSource = "", savedLayoutDigest = "", chosenFile = "", stalePage, referenceSource = "", functionalUrl = "", semanticBeforeMismatch;
const selectedMarker = (id, label) => [{ testId: `workflow-recovery-block-${id}`, label }];

add("01-shell", "Open the approved native editor", "Open the workspace workflow URL.", "Seven Create groups and a dominant canvas open without a permanent input list or Inspector.", async () => {
  if (!args.url) throw new Error("Provide --url=the-exact-workspace-editor-URL");
  if (mode === "final" && (subject.dirty || subject.untrackedImplementation.length)) throw new Error("Final acceptance requires a clean committed subject, including all implementation files.");
  await page.goto(args.url); logAction("Open workspace workflow", args.url);
  await expect(tid("workflow-recovery-palette")).toBeVisible({ timeout: 30000 });
  await expect(page.locator(".workflow-recovery--redesign")).toBeVisible(); await expect(page.locator(".recovery-create-group")).toHaveCount(7); await expect(page.locator(".recovery-palette")).toHaveCount(0); await expect(tid("workflow-recovery-inspector")).toHaveCount(0); await page.evaluate(() => document.fonts.ready);
  await verifyServedSubject();
}, [{ testId: "workflow-recovery-palette", label: "Compact Create rail" }, { testId: "workflow-recovery-canvas", label: "Native workflow canvas" }]);
add("01-workspace-controls", "Use independent workspace controls", "Open Agent Console, collapse it, maximize the active tab, and restore the workspace layout.", "The Console and maximize controls have separate unobscured pointer targets and both actions work without moving the workflow out of its workspace.", async () => {
  const targets = {};
  for (const id of ["workspace-tab-focus", "agent-sidebar-toggle"]) {
    const control = tid(id); await expect(control).toBeVisible();
    targets[id] = await control.evaluate((element) => { const box = element.getBoundingClientRect(); const hit = document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2); return { x: box.x, y: box.y, width: box.width, height: box.height, hitIsControl: hit === element || element.contains(hit) }; });
    expect(targets[id].hitIsControl).toBe(true);
  }
  const left = targets["workspace-tab-focus"], right = targets["agent-sidebar-toggle"];
  expect(left.x + left.width <= right.x || right.x + right.width <= left.x).toBe(true);
  writeFileSync(path.join(root, "workspace-control-targets.json"), JSON.stringify(targets, null, 2));
  await click("agent-sidebar-toggle"); await expect(page.getByTitle("Collapse Agent Console").filter({ visible: true })).toBeVisible();
  await capture("01-agent-console-open", [{ testId: "workspace-tab-focus", label: "Independent maximize control" }]);
  await page.getByTitle("Collapse Agent Console").filter({ visible: true }).click(); logAction("Collapse Agent Console"); await expect(tid("agent-sidebar-toggle")).toBeVisible();
  await click("workspace-tab-focus"); await expect(tid("workspace-tab-focus")).toHaveAttribute("aria-label", "Restore workspace layout"); await capture("01-maximized", [{ testId: "workspace-tab-focus", label: "Restore workspace layout" }]);
  await click("workspace-tab-focus"); await expect(tid("workspace-tab-focus")).toHaveAttribute("aria-label", "Maximize active tab"); await expect(tid("agent-sidebar-toggle")).toBeVisible();
}, [{ testId: "workspace-tab-focus", label: "Maximize active tab" }, { testId: "agent-sidebar-toggle", label: "Open Agent Console" }]);
add("02-create", "Inspect the Create menu", "Click Input in the Create rail, then press Escape.", "Input templates are legible and Escape closes the menu and restores focus.", async () => {
  await click("workflow-recovery-create-group-input"); const menu = page.locator(".recovery-create-popover"); await expect(menu).toBeVisible(); const b = await menu.boundingBox(); if (!b || b.width < 200 || b.x < 0 || b.x + b.width > 1537) throw new Error("Create menu is clipped or too narrow"); await capture("02-create-open", [{ testId: "workflow-recovery-create-template-text-input", label: "Text input template" }]); await page.keyboard.press("Escape"); await expect(menu).toHaveCount(0); await expect(tid("workflow-recovery-create-group-input")).toBeFocused();
}, [{ testId: "workflow-recovery-create-group-input", label: "Input creation group" }]);
add("03-inputs", "Inspect input state", "Click Inputs and choose Design intent.", "Input configuration is honest, temporary navigation closes, and contextual Overview opens.", async () => {
  await click("workflow-recovery-inputs-toggle"); await expect(tid("workflow-recovery-inputs-navigator")).toBeVisible(); await capture("03-inputs-open", [{ testId: "workflow-recovery-input-navigate-block.design-intent", label: "Design intent" }]); await click("workflow-recovery-input-navigate-block.design-intent"); await expect(tid("workflow-recovery-overview-block.design-intent")).toBeVisible(); await expect(tid("workflow-recovery-inputs-navigator")).toHaveCount(0);
}, [{ testId: "workflow-recovery-inputs-toggle", label: "Configured input summary" }]);

if (full) {
  add("04-new-file", "Create an independent evidence workflow", `Click New workflow. Enter ${path.basename(workflowPath, ".workflow.wflow")} as Workflow name, then click Create workflow.`, "A new default workflow is created at the named path; the original workflow is unchanged.", async () => {
    referenceSource = await sourceText(); const url = new URL(args.url); url.searchParams.set("workflowPath", workflowPath); functionalUrl = url.href;
    await page.getByRole("button", { name: "New workflow", exact: true }).click(); logAction("Click New workflow");
    await page.getByLabel("Workflow name", { exact: true }).fill(path.basename(workflowPath, ".workflow.wflow")); logAction("Fill Workflow name", path.basename(workflowPath, ".workflow.wflow"));
    await page.getByRole("button", { name: "Create workflow", exact: true }).click(); logAction("Create evidence workflow", workflowPath);
    await expect(tid("workflow-recovery-filebar")).toContainText(path.basename(workflowPath), { timeout: 30000 });
    await expect(tid("workflow-recovery-filebar")).toContainText("Saved in workspace"); mutations.push({ action: "created", path: workflowPath, scope: "evidence workspace", via: "New workflow UI creates an editable default example" });
  }, [{ testId: "workflow-recovery-filebar", label: "New engineer-owned workspace file" }]);
  add("05-text-input", "Create and configure the first real input", `Create → Input → Text input. Name it Pump requirements. Enter: ${textOne} Click Apply settings.`, "A new independent input contains engineer-authored text; no tool runs.", async () => {
    await create("input", "text-input", "block.text-input-1"); await fill("workflow-recovery-block-title-block.text-input-1", "Pump requirements"); await fill("workflow-recovery-input-text-block.text-input-1", textOne); await click("workflow-recovery-config-apply"); await expect(tid("workflow-recovery-block-block.text-input-1")).toContainText("Pump requirements");
  }, selectedMarker("block.text-input-1", "Independent pump requirements input"));
  add("06-second-input", "Create another independent text input", `Create another Text input. Name it Company practices. Enter: ${textTwo} Click Apply settings.`, "The second text input has a different identity and preserves the first input.", async () => {
    await create("input", "text-input", "block.text-input-2"); await fill("workflow-recovery-block-title-block.text-input-2", "Company practices"); await fill("workflow-recovery-input-text-block.text-input-2", textTwo); await click("workflow-recovery-config-apply"); await expect(tid("workflow-recovery-block-block.text-input-1")).toContainText("Pump requirements");
  }, selectedMarker("block.text-input-2", "Separate company practices input"));
  add("07-file-input", "Reference an actual workspace document", "Create → Input → Workspace file. Refresh files, select a real listed document, and apply.", "The exact permitted relative file reference is authored; no fictional filename is substituted.", async () => {
    await create("input", "file-input", "block.file-input-1"); await click("workflow-recovery-input-files-refresh-block.file-input-1");
    const select = tid("workflow-recovery-input-file-block.file-input-1"); await expect(select).toBeEnabled(); const choices = await select.locator("option").evaluateAll((options) => options.map((o) => o.value).filter(Boolean));
    chosenFile = choices.find((item) => /\.(md|txt|docx)$/.test(item)) ?? choices.find((item) => item.endsWith("mounting-bracket.workflow.wflow")) ?? choices[0]; if (!chosenFile) throw new Error("No permitted real workspace file is available.");
    active.action = `Create → Input → Workspace file. Refresh workspace files, select ${chosenFile}, name it Reference document, then Apply settings.`; status.manualSteps.find((item) => item.label === active.label).instruction = active.action;
    await select.selectOption(chosenFile); logAction("Select actual workspace document", chosenFile); await fill("workflow-recovery-block-title-block.file-input-1", "Reference document"); await click("workflow-recovery-config-apply"); await expect(tid("workflow-recovery-inputs-toggle")).toContainText("3/6 configured");
  }, selectedMarker("block.file-input-1", "Actual workspace file input"));
  add("08-document", "Create and configure an unbound document step", "Create → LLM document → Engineering document. Name it Pump design note, edit the prompt, and apply.", "The document has editable instructions and separate typed text/file inputs. It remains an unbound draft.", async () => {
    await create("document", "document", "block.document-1"); await fill("workflow-recovery-block-title-block.document-1", "Pump design note"); await fill("workflow-recovery-block-instructions-block.document-1", "Draft a design note from the connected requirements and reference document. Separate supplied facts from assumptions."); await click("workflow-recovery-config-apply"); await click("workflow-recovery-inspector-tab-overview"); await expect(tid("workflow-recovery-overview-block.document-1")).toContainText("Unbound draft");
  }, selectedMarker("block.document-1", "Configurable document step"));
  add("09-second-document", "Create a second configurable document step", "Create another Engineering document. Name it Assembly guidance and edit its prompt.", "A second independent document preserves the first; no model execution is implied.", async () => {
    await create("document", "document", "block.document-2"); await fill("workflow-recovery-block-title-block.document-2", "Assembly guidance"); await fill("workflow-recovery-block-instructions-block.document-2", "Prepare assembly guidance from the supplied practices. Flag missing information for engineer review."); await click("workflow-recovery-config-apply");
  }, selectedMarker("block.document-2", "Second independent document step"));
  add("10-tool", "Create an unbound tool step", "Create → MCP tools → MCP tool. Name it Downstream engineering tool, edit its instructions, and apply.", "The tool object can be authored without claiming availability or executing anything.", async () => {
    await create("tool", "mcp-tool", "block.mcp-tool-1"); await fill("workflow-recovery-block-title-block.mcp-tool-1", "Downstream engineering tool"); await fill("workflow-recovery-block-instructions-block.mcp-tool-1", "Use the reviewed engineering document. Tool assignment and execution approval remain required."); await click("workflow-recovery-config-apply");
  }, selectedMarker("block.mcp-tool-1", "Unbound downstream tool"));
  add("11-connections", "Connect exact endpoints by keyboard", "Focus each named output, press Enter, then focus its compatible input and press Enter: requirements→design note; file→design note; practices→assembly guidance; design note→tool.", "Four exact typed connections are accepted, including distinct text and file inputs on one document.", async () => {
    await connect("port.text-input-1-text-out", "port.document-1-text-in", "rel.user-text-input-1-text-out-to-document-1-text-in");
    await connect("port.file-input-1-file-out", "port.document-1-file-in", "rel.user-file-input-1-file-out-to-document-1-file-in");
    await connect("port.text-input-2-text-out", "port.document-2-text-in", "rel.user-text-input-2-text-out-to-document-2-text-in");
    await connect("port.document-1-document-out", "port.mcp-tool-1-document-in", "rel.user-document-1-document-out-to-mcp-tool-1-document-in");
  });
  add("12-fanout", "Fan out one file to two consumers", "Connect the same Reference document output to Assembly guidance’s reference-file input.", "One output feeds two distinct consumers, without collapsing their endpoint identities.", async () => {
    await connect("port.file-input-1-file-out", "port.document-2-file-in", "rel.user-file-input-1-file-out-to-document-2-file-in"); await showInput("block.file-input-1"); await click("workflow-recovery-inspector-tab-outputs"); await expect(tid("workflow-recovery-inspector")).toContainText("Pump design note"); await expect(tid("workflow-recovery-inspector")).toContainText("Assembly guidance");
  });
  add("13-reject-mismatch", "Reject an incompatible connection", "Try connecting the text requirements output to the tool’s Engineering document input.", "A type-mismatch explanation appears and the accepted semantic digest does not change.", async () => {
    semanticBeforeMismatch = await tid("workflow-recovery-concept").getAttribute("data-semantic-digest"); await tid("workflow-recovery-handle-port.text-input-1-text-out").focus(); await page.keyboard.press("Enter"); await tid("workflow-recovery-handle-port.mcp-tool-1-document-in").focus(); await page.keyboard.press("Enter"); logAction("Attempt incompatible text to document connection");
    await expect(page.locator(".recovery-diagnostics")).toBeVisible(); await expect(page.locator(".recovery-diagnostics")).toContainText(/type|compatible|accept/i); await expect(tid("workflow-recovery-concept")).toHaveAttribute("data-semantic-digest", semanticBeforeMismatch); await click("workflow-recovery-validate"); await expect(page.locator(".recovery-diagnostics")).toHaveCount(0);
  });
  add("14-live-drag", "Move an object with live feedback", "Drag Pump requirements by its title; observe its position before releasing the pointer.", "The rendered node moves during the drag and its position commits on release.", async () => {
    await showInput("block.text-input-1"); const node = tid("workflow-recovery-block-block.text-input-1"); const title = node.locator("h3"); const before = await node.boundingBox(); const handle = await title.boundingBox(); if (!before || !handle) throw new Error("Drag target is unavailable");
    await page.mouse.move(handle.x + handle.width / 2, handle.y + handle.height / 2); await page.mouse.down(); await page.mouse.move(handle.x + handle.width / 2 + 70, handle.y + handle.height / 2 + 45, { steps: 9 }); const during = await node.boundingBox(); if (!during || Math.abs(during.x - before.x) < 20) throw new Error("Node did not visibly move before mouse-up"); await capture("14-live-drag-before-release", selectedMarker("block.text-input-1", "Node is moving before pointer release")); await page.mouse.up(); logAction("Drag Pump requirements", "70px right, 45px down; measured before release");
    writeFileSync(path.join(root, "drag-measurements.json"), JSON.stringify({ before, during, after: await node.boundingBox() }, null, 2));
  });
  add("15-source-invalid", "Contain an invalid Source edit", "Open Source, replace it with malformed workflow text, and apply the checked edit.", "The invalid edit remains visible, an actionable diagnostic appears, and accepted workflow identity is unchanged.", async () => {
    await click("workflow-recovery-view-code"); savedSource = await tid("workflow-recovery-source-editor").inputValue(); const digest = await tid("workflow-recovery-concept").getAttribute("data-semantic-digest"); await fill("workflow-recovery-source-editor", "workflow malformed\nend\n"); await click("workflow-recovery-source-apply"); await expect(page.locator(".recovery-diagnostics")).toBeVisible(); await expect(tid("workflow-recovery-concept")).toHaveAttribute("data-semantic-digest", digest);
  }, [{ testId: "workflow-recovery-source-editor", label: "Invalid draft retained" }]);
  add("16-source-valid", "Apply a valid source change", "Restore the complete source, rename Assembly guidance to Assembly guidance reviewed in Source, and apply.", "Valid Source edits update the same diagram atomically.", async () => {
    await fill("workflow-recovery-source-editor", savedSource.replace('name: "Assembly guidance"', 'name: "Assembly guidance reviewed"')); await click("workflow-recovery-source-apply"); await expect(page.locator(".recovery-diagnostics")).toHaveCount(0); await click("workflow-recovery-view-diagram"); await expect(tid("workflow-recovery-block-block.document-2")).toContainText("Assembly guidance reviewed");
  });
  add("17-history", "Undo and redo the source change", "Click Undo, verify the previous name, then click Redo.", "History restores and reapplies the same canonical change.", async () => {
    await click("workflow-recovery-undo"); await expect(tid("workflow-recovery-block-block.document-2")).toContainText("Assembly guidance"); await expect(tid("workflow-recovery-block-block.document-2")).not.toContainText("reviewed"); await click("workflow-recovery-redo"); await expect(tid("workflow-recovery-block-block.document-2")).toContainText("Assembly guidance reviewed");
  });
  add("18-delete-cancel", "Review deletion impact without losing work", "Select Assembly guidance reviewed → Settings → Delete step. Read the connection count and choose Keep step.", "The dialog names the object and both affected connections. Cancel preserves them.", async () => {
    await selectSettings("block.document-2"); await click("workflow-recovery-delete"); await expect(page.getByRole("dialog", { name: "Delete workflow step" })).toContainText("2 connection(s)"); await capture("18-delete-dialog", [{ testId: "workflow-recovery-delete-cancel", label: "Keep step" }, { testId: "workflow-recovery-delete-confirm", label: "Delete step and connections" }]); await click("workflow-recovery-delete-cancel"); await expect(tid("workflow-recovery-block-block.document-2")).toHaveCount(1);
  });
  add("19-delete-undo", "Delete atomically and undo the complete change", "Delete Assembly guidance reviewed and its connections, then Undo.", "The step and its connections disappear together and return together on Undo.", async () => {
    await click("workflow-recovery-delete"); await click("workflow-recovery-delete-confirm"); await expect(tid("workflow-recovery-block-block.document-2")).toHaveCount(0); await expect(tid("workflow-recovery-edge-rel.user-file-input-1-file-out-to-document-2-file-in")).toHaveCount(0); await click("workflow-recovery-undo"); await expect(tid("workflow-recovery-block-block.document-2")).toHaveCount(1); await expect(tid("workflow-recovery-edge-rel.user-file-input-1-file-out-to-document-2-file-in")).toHaveCount(1);
  });
  add("20-save-reopen", "Save and reopen source plus positions", "Click Save, then reload the workspace workflow URL.", "Authored texts, file references, prompts, exact connections and saved canvas positions survive reopening.", async () => {
    savedSource = await sourceText(); await expect(tid("workflow-recovery-concept")).toHaveAttribute("data-layout-digest", /^sha256:[a-f0-9]{64}$/); savedLayoutDigest = await tid("workflow-recovery-concept").getAttribute("data-layout-digest"); await click("workflow-recovery-save"); await expect(tid("workflow-recovery-save-status")).toHaveText("Saved in workspace"); await expect(tid("workflow-recovery-concept")).toHaveAttribute("data-layout-digest", /^sha256:[a-f0-9]{64}$/); savedLayoutDigest = await tid("workflow-recovery-concept").getAttribute("data-layout-digest"); mutations.push({ action: "saved authored source and layout", path: workflowPath, chosenFile, inputValues: [textOne, textTwo] });
    await page.reload(); logAction("Reload saved workflow", functionalUrl); await expect(tid("workflow-recovery-filebar")).toContainText(path.basename(workflowPath), { timeout: 30000 }); await expect(tid("workflow-recovery-inputs-toggle")).toContainText("3/6 configured"); await expect(tid("workflow-recovery-concept")).toHaveAttribute("data-layout-digest", savedLayoutDigest); const reopened = await sourceText(); expect(reopened.replace(/\r\n/g, "\n")).toBe(savedSource.replace(/\r\n/g, "\n")); await click("workflow-recovery-run-start"); await expect(page.getByRole("dialog", { name: "Process cannot start" })).toContainText("Automatic execution is not available"); await expect(tid("workflow-recovery-run-mode")).toHaveCount(0); await click("workflow-recovery-modal-close");
  });
  add("21-conflict", "Protect a stale tab’s authored work", "Open the same workflow in a second tab. Save a name edit there. In the original tab edit the same name differently and Save.", "The stale save conflicts; local text remains protected and the newer stored file is not overwritten.", async () => {
    stalePage = await context.newPage(); await stalePage.goto(functionalUrl); await expect(stalePage.getByTestId("workflow-recovery-palette").filter({ visible: true })).toBeVisible({ timeout: 30000 });
    const currentPage = page; page = stalePage; await selectSettings("block.text-input-1"); await fill("workflow-recovery-block-title-block.text-input-1", "Pump requirements stored update"); await click("workflow-recovery-config-apply"); await click("workflow-recovery-save"); await expect(tid("workflow-recovery-save-status")).toHaveText("Saved in workspace"); page = currentPage;
    await selectSettings("block.text-input-1"); await fill("workflow-recovery-block-title-block.text-input-1", "Pump requirements unsaved local edit"); await click("workflow-recovery-config-apply"); await click("workflow-recovery-save"); await expect(tid("workflow-recovery-conflict-actions")).toBeVisible(); await expect(tid("workflow-recovery-save-status")).toContainText("local edits are still here");
  });
  add("22-compare-reload", "Compare conflict sources and reload explicitly", "Click Compare stored file. Confirm both versions remain distinct. Close, then Discard local edits and reload; confirm the named action.", "Comparison preserves both sources; only explicit reload replaces unsaved local edits with the newer saved version.", async () => {
    await click("workflow-recovery-conflict-compare"); await expect(tid("workflow-recovery-source-comparison-local")).toHaveValue(/Pump requirements unsaved local edit/); await expect(tid("workflow-recovery-source-comparison-stored")).toHaveValue(/Pump requirements stored update/); await capture("22-compare-dialog", [{ testId: "workflow-recovery-source-comparison-local", label: "Protected local source" }, { testId: "workflow-recovery-source-comparison-stored", label: "Current stored source" }]); await click("workflow-recovery-modal-close"); await click("workflow-recovery-conflict-reload"); await click("workflow-recovery-conflict-reload-confirm"); await expect(tid("workflow-recovery-block-block.text-input-1")).toContainText("Pump requirements stored update"); await expect(tid("workflow-recovery-conflict-actions")).toHaveCount(0); await stalePage.close();
  });
  add("23-example-suggestion", "Open the original workflow and review an example suggestion", "Click Open workflow and choose mounting-bracket.workflow.wflow. Open Example suggestion, inspect the preview and its no-live-AI label, then discard it.", "Open workflow selects the actual saved original. The reviewed proposal remains bounded and never changes that file.", async () => {
    await page.getByRole("button", { name: "Open workflow", exact: true }).click(); logAction("Click Open workflow"); await page.getByRole("button", { name: "mounting-bracket.workflow.wflow", exact: true }).click(); logAction("Open actual saved original", "mounting-bracket.workflow.wflow"); await expect(tid("workflow-recovery-filebar")).toContainText("mounting-bracket.workflow.wflow"); expect(await sourceText()).toBe(referenceSource); await click("workflow-recovery-ai-request"); await expect(tid("workflow-recovery-proposal")).toContainText("NO LIVE AI CALL"); await expect(tid("workflow-recovery-proposal-preview")).toContainText("Preview only"); await capture("23-proposal-open", [{ testId: "workflow-recovery-proposal-reject", label: "Discard example suggestion" }, { testId: "workflow-recovery-proposal-accept", label: "Apply reviewed suggestion" }]); await click("workflow-recovery-proposal-reject"); expect(await sourceText()).toBe(referenceSource);
  });
  add("24-run-preflight", "Explain missing inputs without queuing a demo", "Click Run. Review each missing input and the unavailable execution integration. Click Configure Design intent to open its Settings, then collapse Inspector without changing values.", "Run gives an actionable error, identifies three missing inputs, and states MCP execution is unavailable. No run is queued and no Advance simulation control is offered.", async () => {
    await click("workflow-recovery-run-start");
    const dialog = page.getByRole("dialog", { name: "Process cannot start" });
    await expect(dialog).toContainText("3 inputs need configuration");
    await expect(dialog).toContainText("Nothing was started or queued");
    await expect(dialog).toContainText("configuring inputs alone will not enable execution");
    await expect(tid("workflow-recovery-run-mode")).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Advance simulation" })).toHaveCount(0);
    for (const width of [1537, 907, 830]) {
      await page.setViewportSize({ width, height: 791 }); logAction("Resize run error", `${width}×791`);
      await tid("workflow-recovery-run-fix-block.design-intent").scrollIntoViewIfNeeded();
      await expect(tid("workflow-recovery-run-fix-block.design-intent")).toBeInViewport();
      await capture(`24-run-error-${width}`, [{ testId: "workflow-recovery-run-fix-block.design-intent", label: "Open missing input Settings" }, { testId: "workflow-recovery-execution-unavailable", label: "Execution integration remains unavailable" }]);
    }
    await click("workflow-recovery-run-fix-block.design-intent");
    await expect(dialog).toHaveCount(0);
    await expect(tid("workflow-recovery-input-text-block.design-intent")).toBeVisible();
    await expect(tid("workflow-recovery-config-apply")).toBeVisible();
    await capture("24-configure-missing-input", [{ testId: "workflow-recovery-input-text-block.design-intent", label: "Supply design instructions" }]);
    await click("workflow-recovery-inspector-close");
    await page.setViewportSize({ width: 1537, height: 791 });
  });
}

const dimensions = full || args.viewports === "all" ? [{ width: 1536, height: 1024 }, { width: 1537, height: 791 }, { width: 1070, height: 791 }, { width: 907, height: 791 }, { width: 830, height: 791 }] : [];
if (full) add("image-reference-match", "Review the full canvas at the approved image size", "Return to the original unchanged workflow. Resize to 1536×1024 and reload it without opening Inspector.", "The original workflow opens with a readable canvas-first default at the selected reference image dimensions. No persistent input cards or blank Inspector column consume the canvas.", async () => {
  await page.setViewportSize({ width: 1536, height: 1024 }); await page.reload(); logAction("Reload unchanged original at image-match dimensions", "1536×1024; no Fit-all overview or forced selection"); await expect(tid("workflow-recovery-palette")).toBeVisible({ timeout: 30000 }); await expect(tid("workflow-recovery-inspector")).toHaveCount(0); await expect(tid("workflow-recovery-filebar")).toContainText("mounting-bracket.workflow.wflow");
}, [{ testId: "workflow-recovery-palette", label: "Compact object creation rail" }, { testId: "workflow-recovery-canvas", label: "Default readable canvas at approved reference dimensions" }]);
for (const viewport of dimensions) add(`viewport-${viewport.width}`, `Viewport ${viewport.width}×${viewport.height}`, `Resize the window to ${viewport.width}×${viewport.height}. Open Design intent in the Inputs navigator.`, "Document and controls remain in the viewport; details scroll internally.", async () => {
  await page.setViewportSize(viewport); logAction("Resize viewport", `${viewport.width}×${viewport.height}`); await click("workflow-recovery-inputs-toggle"); await click("workflow-recovery-input-navigate-block.design-intent");
  const measurements = await page.evaluate(() => ({ width: innerWidth, height: innerHeight, dpr: devicePixelRatio, scrollWidth: document.documentElement.scrollWidth, scrollHeight: document.documentElement.scrollHeight, canvas: document.querySelector('[data-testid="workflow-recovery-canvas"]')?.getBoundingClientRect().toJSON() })); writeFileSync(path.join(root, `viewport-${viewport.width}.json`), JSON.stringify(measurements, null, 2));
  const tiles = await page.locator('.recovery-create-group').evaluateAll((buttons) => buttons.map((button) => { const box = button.getBoundingClientRect(); return { label: button.textContent, width: box.width, height: box.height }; }));
  expect(tiles).toHaveLength(7); for (const tile of tiles) { expect(tile.width, tile.label).toBe(64); expect(tile.height, tile.label).toBe(64); }
  const rail = await page.locator('.recovery-create-buttons').evaluate((element) => ({ width: element.clientWidth, content: element.scrollWidth })); expect(rail.content).toBeLessThanOrEqual(rail.width);
  writeFileSync(path.join(root, `palette-${viewport.width}.json`), JSON.stringify({ tiles, rail }, null, 2));
  if (measurements.scrollWidth > viewport.width + 2 || measurements.scrollHeight > viewport.height + 2) throw new Error(`Document overflow: ${JSON.stringify(measurements)}`);
}, [{ testId: "workflow-recovery-canvas", label: "Readable canvas viewport" }, { testId: "workflow-recovery-inspector", label: "Internally scrolling Inspector" }]);
if (full) add("short-rail-keyboard", "Reach the complete Create rail in a short window", "Resize to 768×512. Focus Input, press Tab six times to reach More, then press Enter. Press Escape to close.", "Keyboard navigation scrolls More into view; its options remain reachable without force clicking or treating viewport size as zoom.", async () => {
  await page.setViewportSize({ width: 768, height: 512 }); await tid("workflow-recovery-create-group-input").focus(); for (let i = 0; i < 6; i++) await page.keyboard.press("Tab"); await expect(tid("workflow-recovery-create-group-more")).toBeFocused();
  const box = await tid("workflow-recovery-create-group-more").boundingBox(); if (!box || box.y < 0 || box.y + box.height > 512) throw new Error("More is keyboard-focused but clipped outside the short viewport");
  await page.keyboard.press("Enter"); await expect(tid("workflow-recovery-create-template-engineering-step")).toBeVisible(); await capture("short-rail-more-open", [{ testId: "workflow-recovery-create-group-more", label: "Keyboard-focused More" }, { testId: "workflow-recovery-create-template-engineering-step", label: "Reachable engineering step template" }]); await page.keyboard.press("Escape"); logAction("Keyboard through all seven Create groups", "768×512 viewport, 6 Tabs, Enter, Escape");
});
if (needsZoom) add("browser-zoom-200", "Actual browser zoom at 200%", "Set browser zoom to 200% on a 1537×791 window. Open Settings for Design intent and scroll inside Inspector to Apply settings without changing values. Collapse Inspector and overview map, then return zoom to 100%.", "Chromium reports a real tab zoom factor of 2.0. Settings and Apply remain reachable; optional panels collapse for usable canvas space. No values are authored.", async () => {
  await page.setViewportSize({ width: 1537, height: 791 }); const before = await page.evaluate(() => ({ width: innerWidth, height: innerHeight, dpr: devicePixelRatio }));
  const zoom = await zoomWorker.evaluate(async (url) => { const tab = (await chrome.tabs.query({})).find((item) => item.url === url); if (!tab?.id) throw new Error("Could not identify the exact evidence tab"); await chrome.tabs.setZoom(tab.id, 2); return chrome.tabs.getZoom(tab.id); }, page.url());
  logAction("Set actual Chromium tab zoom", "200% using chrome.tabs.setZoom; not viewport emulation"); expect(zoom).toBe(2);
  await expect.poll(() => page.evaluate(() => devicePixelRatio)).toBeGreaterThan(before.dpr * 1.8);
  const after = await page.evaluate(() => ({ width: innerWidth, height: innerHeight, dpr: devicePixelRatio, scrollWidth: document.documentElement.scrollWidth, scrollHeight: document.documentElement.scrollHeight })); writeFileSync(path.join(root, "browser-zoom-200.json"), JSON.stringify({ method: "chrome.tabs.setZoom", tabZoomFactor: zoom, before, after }, null, 2)); if (after.scrollWidth > after.width + 2 || after.scrollHeight > after.height + 2) throw new Error(`Document overflows at actual 200% zoom: ${JSON.stringify(after)}`); await capture("browser-zoom-200-actual", [{ testId: "workflow-recovery-canvas", label: "Actual 200% browser zoom" }]);
  await click("workflow-recovery-inspector-tab-definition"); await tid("workflow-recovery-config-apply").scrollIntoViewIfNeeded(); logAction("Scroll inside Settings to Apply settings", "No field values changed and Apply was not pressed");
  const apply = await tid("workflow-recovery-config-apply").evaluate((element) => { const box = element.getBoundingClientRect(); const hit = document.elementFromPoint(box.x + box.width / 2, box.y + box.height / 2); return { x: box.x, y: box.y, width: box.width, height: box.height, hitIsControl: hit === element || element.contains(hit) }; }); expect(apply.hitIsControl).toBe(true); expect(apply.y).toBeGreaterThanOrEqual(0); expect(apply.y + apply.height).toBeLessThanOrEqual(after.height);
  await capture("browser-zoom-200-settings-apply", [{ testId: "workflow-recovery-config-apply", label: "Apply reachable by internal scrolling; not pressed" }]);
  await click("workflow-recovery-inspector-close"); await expect(tid("workflow-recovery-inspector")).toHaveCount(0); if (await tid("workflow-recovery-minimap-toggle").getAttribute("aria-expanded") === "true") await click("workflow-recovery-minimap-toggle");
  const canvas = await tid("workflow-recovery-canvas").boundingBox(); writeFileSync(path.join(root, "browser-zoom-200.json"), JSON.stringify({ method: "chrome.tabs.setZoom", tabZoomFactor: zoom, before, after, apply, canvasWithoutOptionalPanels: canvas }, null, 2)); await capture("browser-zoom-200-canvas", [{ testId: "workflow-recovery-canvas", label: "Canvas with optional Inspector and minimap collapsed" }]);
  await zoomWorker.evaluate(async (url) => { const tab = (await chrome.tabs.query({})).find((item) => item.url === url); await chrome.tabs.setZoom(tab.id, 1); }, page.url());
});

if (mode === "blocks") {
  plans.length = 0; status.steps.length = 0; status.manualSteps.length = 0;
  const { registerBlockAcceptance } = await import("./block_acceptance.mjs");
  registerBlockAcceptance({ add, getPage: () => page, tid, click, fill, capture, logAction, expect, args, root, stamp, mutations });
  status.title = "Wright individual blocks and interoperability";
  if (args.only) {
    const ids = new Set(args.only.split(","));
    const selected = plans.filter(p => ids.has(p.record.id));
    plans.splice(0, plans.length, ...selected);
    status.steps = selected.map(p => p.record);
    status.manualSteps = status.manualSteps.filter(s => selected.some(p => p.record.label === s.label));
  }
}
writeReport();
try {
  // A local, minimal extension supplies the browser's real per-tab zoom API.
  // It has no content scripts or host permissions and makes no network requests.
  if (needsZoom) {
    const extension = path.join(root, "playwright/zoom-extension"); mkdirSync(extension);
    writeFileSync(path.join(extension, "manifest.json"), JSON.stringify({ manifest_version: 3, name: "Wright evidence tab zoom", version: "1.0", permissions: ["tabs"], background: { service_worker: "worker.js" } }));
    writeFileSync(path.join(extension, "worker.js"), "chrome.runtime.onInstalled.addListener(() => {});\n");
    context = await chromium.launchPersistentContext(mkdtempSync(path.join(tmpdir(), "wright-evidence-browser-")), { channel: "chromium", headless: true, viewport: { width: 1537, height: 791 }, reducedMotion: "reduce", args: [`--disable-extensions-except=${extension}`, `--load-extension=${extension}`] });
    zoomWorker = context.serviceWorkers()[0] ?? await context.waitForEvent("serviceworker", { timeout: 15000 });
  } else { browser = await chromium.launch({ headless: true }); context = await browser.newContext({ viewport: { width: 1537, height: 791 }, reducedMotion: "reduce" }); }
  await context.tracing.start({ screenshots: true, snapshots: true, sources: true }); tracing = true;
  context.on("page", attachDiagnostics);
  page = context.pages()[0] ?? await context.newPage(); attachDiagnostics(page);
  function attachDiagnostics(target) {
    if (target.__wrightDiagnostics) return; target.__wrightDiagnostics = true;
    target.on("console", (message) => { if (message.type() === "error") diagnostics.console.push({ message: message.text(), url: message.location().url }); });
    target.on("pageerror", (error) => diagnostics.pageErrors.push(String(error)));
    target.on("requestfailed", (request) => diagnostics.failedRequests.push({ url: request.url(), error: request.failure()?.errorText }));
    target.on("response", (response) => {
      inspectServedModule(response);
      if (response.url().endsWith("/workflow-sources") && ["POST", "PUT"].includes(response.request().method()) && response.status() < 400) {
        const body = response.request().postDataJSON(); mutations.push({ action: response.request().method() === "POST" ? "created" : "updated", path: body.path, via: "normal workspace API from browser UI", responseStatus: response.status(), at: new Date().toISOString() });
      }
      if (response.status() >= 400) { const entry = { status: response.status(), url: response.url() }; if ((entry.status === 404 && entry.url.includes("/workflow-sources?") && entry.url.includes("image-redesign-acceptance-")) || (entry.status === 409 && entry.url.endsWith("/workflow-sources") && active?.id === "21-conflict")) expectedHttp.add(`${entry.status}:${entry.url}`); diagnostics.httpErrors.push(entry); }
    });
  }
  for (const plan of plans) {
    active = plan.record; active.summary = "In progress"; writeReport();
    if (page.url() !== "about:blank") { const before = await capture(`${active.id}-before`, plan.markers); Object.assign(active, { beforeRaw: before.raw, beforeAnnotated: before.annotated }); }
    await plan.action(); const failures = diagnosticFailures(); if (failures.length) throw new Error(`Unexpected browser diagnostics: ${failures.join("; ")}`);
    Object.assign(active, await capture(active.id, plan.markers), { state: "pass", summary: active.expected, actual: active.expected });
    appendFileSync(path.join(root, "progress.md"), `\n## ${new Date().toISOString()} UTC — PASS\n\n- URL: ${page.url()}\n- Exact action: ${active.action}\n- Expected: ${active.expected}\n- Actual: ${active.actual}\n- Diagnostics: ${JSON.stringify(diagnostics)}\n- Raw: ${active.raw}\n- Annotated: ${active.annotated}\n`); writeReport(); console.log(`PASS ${active.id}: ${active.label}`);
  }
  await verifyServedSubject();
  if (mode === "final" && (git("rev-parse", "HEAD") !== subject.commit || git("status", "--porcelain", "--untracked-files=no") || untrackedImplementation().length)) throw new Error("The exact committed subject changed during final acceptance; preserve this run and capture a new frozen continuation.");
  status.overall = "pass"; status.summary = mode === "blocks" ? "Individual block authoring and live interoperability checks passed through the workspace UI. Evidence covers the current working tree; CI and user acceptance remain separate." : full ? `${status.steps.length} functional and responsive checks passed against ${subject.dirty || subject.untrackedImplementation.length ? "the recorded working tree" : "the exact clean committed subject"}. Execution remains unavailable; missing inputs are actionable and no manual simulation is offered in the workspace. Created ${workflowPath}; original example preserved.` : "Early integrated shell reviewed in the real browser. Functional and exact-subject acceptance remain separate.";
} catch (error) {
  status.overall = "blocked"; status.summary = `Stopped at first failure: ${error.message}`;
  if (!active) { active = { id: "startup", label: "Browser startup", purpose: "Open evidence browser", action: "Launch Chromium and start trace", controls: [], expected: "The evidence browser starts safely" }; status.steps.unshift(active); }
  Object.assign(active, { state: "blocked", summary: status.summary, actual: status.summary }, page ? await capture(`stopped-${active.id}`).catch(() => ({})) : {});
  appendFileSync(path.join(root, "progress.md"), `\n## ${new Date().toISOString()} UTC — STOPPED\n\nURL: ${page?.url() ?? "browser unavailable"}\nControl: ${active.action}\nExpected: ${active.expected}\nActual: ${status.summary}\nDiagnostics: ${JSON.stringify(diagnostics)}\nRaw: ${active.raw ?? "Unavailable: browser did not start"}\nAnnotated: ${active.annotated ?? "Unavailable"}\nCreated/changed data: ${JSON.stringify(mutations)}\nRemaining steps stay pending. This stopped evidence is preserved; repairs require a new continuation.\n`); process.exitCode = 1;
} finally {
  writeReport();
  if (tracing) await context.tracing.stop({ path: path.join(root, "trace/walkthrough.zip") }).catch((error) => writeFileSync(path.join(root, "trace/trace-stop-error.txt"), String(error)));
  await context?.close().catch(() => undefined); await browser?.close().catch(() => undefined);
  const files = []; function walk(dir) { for (const file of readdirSync(path.join(root, dir), { withFileTypes: true })) { const relative = path.join(dir, file.name); if (file.isDirectory()) walk(relative); else files.push({ path: relative.replaceAll("\\", "/"), sha256: createHash("sha256").update(readFileSync(path.join(root, relative))).digest("hex") }); } } walk(""); writeFileSync(path.join(root, "manifest.json"), JSON.stringify({ ...subject, files }, null, 2)); console.log(JSON.stringify({ root, overall: status.overall, summary: status.summary }));
}
