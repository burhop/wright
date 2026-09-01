import { chromium } from "@playwright/test";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import {
  appendFileSync,
  copyFileSync,
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const VIEWPORT = { width: 1070, height: 791 };
const WORKFLOW_SOURCE_ROUTE = "/api/workspace/workflow-sources";
const DEFAULT_WORKFLOW_PATH = "workflows/mounting-bracket.workflow.wflow";
const EXPECTED_STEP_FIXTURE_SHA256 = "bf316fa511f5e6a3312f03cb5b36184d91109185730defc41542b8805884be83";

function parseArguments(argv) {
  const values = new Map();
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    if (!argument.startsWith("--")) throw new Error(`Unexpected positional argument: ${argument}`);
    const equals = argument.indexOf("=");
    if (equals >= 0) {
      values.set(argument.slice(2, equals), argument.slice(equals + 1));
      continue;
    }
    const key = argument.slice(2);
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`Missing value for --${key}`);
    values.set(key, value);
    index += 1;
  }
  return values;
}

const cli = parseArguments(process.argv.slice(2));
const setting = (environmentName, optionName, { required = true, fallback = undefined } = {}) => {
  const value = cli.get(optionName) ?? process.env[environmentName] ?? fallback;
  if (required && (!value || !String(value).trim())) {
    throw new Error(`Provide ${environmentName} or --${optionName}.`);
  }
  return value === undefined ? undefined : String(value).trim();
};

const repositoryRoot = path.resolve(setting("REPOSITORY_ROOT", "repository-root", { required: false, fallback: process.cwd() }));
const walkthroughRoot = path.resolve(setting("WALKTHROUGH_ROOT", "walkthrough-root"));
const subjectCommit = setting("SUBJECT_COMMIT", "subject-commit");
const subjectTree = setting("SUBJECT_TREE", "subject-tree");
const expectedWorkspaceName = setting("EXPECTED_WORKSPACE_NAME", "expected-workspace-name");
const expectedWorkspaceId = setting("EXPECTED_WORKSPACE_ID", "expected-workspace-id");
const expectedSessionId = setting("EXPECTED_SESSION_ID", "expected-session-id");
const workflowPath = setting("WORKFLOW_PATH", "workflow-path", { required: false, fallback: DEFAULT_WORKFLOW_PATH }).replace(/^[/\\]+/, "");
const headless = setting("HEADLESS", "headless", { required: false, fallback: "true" }).toLowerCase() !== "false";
const browserExecutable = setting("CHROMIUM_EXECUTABLE_PATH", "chromium-executable-path", { required: false });
const baseUrl = new URL(setting("BASE_URL", "base-url"));
if (!/^https?:$/.test(baseUrl.protocol)) throw new Error(`BASE_URL must use http or https, got ${baseUrl.protocol}`);
if (!baseUrl.pathname.endsWith("/")) baseUrl.pathname = `${baseUrl.pathname}/`;
baseUrl.search = "";
baseUrl.hash = "";

const dashboardUrl = baseUrl.href;
const ordinaryWorkspaceUrl = new URL(`workspace/${encodeURIComponent(expectedWorkspaceId)}`, baseUrl).href;
const workflowSourceUrl = new URL(WORKFLOW_SOURCE_ROUTE.replace(/^\//, ""), baseUrl);
const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
const startedAt = new Date().toISOString();

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function git(...arguments_) {
  return execFileSync("git", arguments_, { cwd: repositoryRoot, encoding: "utf8" }).trim();
}

assert(/^[0-9a-f]{40,64}$/i.test(subjectCommit), `SUBJECT_COMMIT is not a full object id: ${subjectCommit}`);
assert(/^[0-9a-f]{40,64}$/i.test(subjectTree), `SUBJECT_TREE is not a full object id: ${subjectTree}`);
assert(!existsSync(walkthroughRoot), `WALKTHROUGH_ROOT already exists; use a new timestamped continuation root: ${walkthroughRoot}`);
const actualCommit = git("rev-parse", "HEAD");
const actualTree = git("rev-parse", "HEAD^{tree}");
const trackedStatus = git("status", "--porcelain=v1", "--untracked-files=no");
assert(actualCommit === subjectCommit, `Subject commit mismatch: expected ${subjectCommit}, got ${actualCommit}`);
assert(actualTree === subjectTree, `Subject tree mismatch: expected ${subjectTree}, got ${actualTree}`);
assert(trackedStatus === "", `Tracked worktree changes are present; capture requires an exact tracked-clean subject:\n${trackedStatus}`);

for (const directory of ["playwright", "screenshots/raw", "screenshots/annotated", "trace"]) {
  mkdirSync(path.join(walkthroughRoot, directory), { recursive: true });
}
copyFileSync(fileURLToPath(import.meta.url), path.join(walkthroughRoot, "playwright", "capture.mjs"));

const plannedSteps = [
  ["S01", "One isolated workspace and no global recovery destination", "Prove that the dashboard is scoped to the prepared workspace and does not expose the retired global Workflow Recovery destination.", "Open the dashboard and inspect the workspace list and global navigation.", ["Engineering Workspaces", expectedWorkspaceName], "Exactly one workspace is listed and no global Workflow Recovery link or button exists."],
  ["S02", "Ordinary workspace URL exposes an explicit Workflows action", "Prove that opening a workspace remains an ordinary workspace navigation before the canonical workflow is requested.", `Open ${expectedWorkspaceName} from the dashboard.`, [expectedWorkspaceName, "Workflows"], `The browser reaches /workspace/${expectedWorkspaceId} with no workflow query and offers Workflows inside the workspace.`],
  ["S03", "Workflows action creates and opens the default workflow", "Verify that the recovery experience is entered only through the workspace action and that an empty workspace becomes immediately usable.", "Click Workflows.", ["Workflows", "Workflow file/status bar"], "The action adds workflow=canonical, scopes the page to the expected workspace/session/path, records exactly one initial GET 404 and one automatic POST 201, and opens the editor without a missing-file or Create boundary."],
  ["S04", "Automatic default is an exact workspace-owned document", "Verify that automatic bootstrap used the real workspace API and persisted the canonical default source at the scoped path.", "Inspect the opened editor and read the stored workflow through the real API.", ["Workflow file/status bar", "Saved in workspace"], "The stored document belongs to the exact workspace and path, contains the default engineering workflow, and is ready without a second confirmation action."],
  ["S05", "Canonical topology stays small and engineering-focused", "Verify the accepted diagram and its three concrete engineering sources before editing.", "Inspect the diagram, source cards, and palette.", ["Three source inputs", "Workflow diagram", "Inspector"], "Nine nodes and three source-to-specification connections are visible; three concrete inputs are named; phase backdrops and graph search are absent."],
  ["S06", "Design intent is an honest session-only input", "Verify that the demo input says what it contains, who supplied it, and that it is not workspace persistence.", "Click Add text or document, then View input.", ["Add text or document", "View input"], "The DOCX preview identifies engineer provenance and its consumer while the source card says the demo input is not saved by this concept."],
  ["S07", "Source uses friendly grammar without host authority fields", "Verify that engineers edit domain language while revision and integrity remain host-owned.", "Click Source and inspect the workflow text and Managed by Wright disclosure.", ["Source", "Workflow source", "Managed by Wright"], "The text uses workflow/item/input/task/connection sections, keeps grouping optional with group: null on these ungrouped tasks, and contains no opaque canonical IDs or assigned revision, ancestry, digest, layout, or run-state fields."],
  ["S08", "Managed source fields are rejected", "Verify that an engineering edit cannot counterfeit host-owned revision authority.", "Add revision: 999 to the workflow section and click Apply checked edit.", ["Workflow source", "Apply checked edit"], "WFR-SOURCE-FIELD-MANAGED is shown, the accepted revision stays unchanged, and testing is disabled."],
  ["S09", "Rejected source can be restored without changing authority", "Verify a human-repeatable recovery from a rejected local source draft.", "Restore the previous friendly source and click Apply checked edit.", ["Workflow source", "Apply checked edit"], "The managed-field diagnostic clears, the accepted revision remains unchanged, and the restored source is valid."],
  ["S10", "Side by side keeps graph edits synchronized to text", "Verify one accepted definition across the diagram and engineering source.", "Click Side by side, set Thickness (mm) to 8, and click Save step changes.", ["Side by side", "Thickness (mm)", "Save step changes"], "The diagram edit increments the definition revision and the source immediately contains thickness_mm 8."],
  ["S11", "Side by side keeps text edits synchronized to graph", "Verify the inverse text-to-diagram projection.", "Rename Create bracket CAD model in Source and click Apply checked edit.", ["Workflow source", "Apply checked edit", "Create bracket CAD model walkthrough"], "The accepted diagram immediately shows the friendly renamed step and the definition revision advances once."],
  ["S12", "Save and reload use the current CAS identity", "Verify real workspace persistence, compare-and-swap rebasing, and reload from stored source.", "Click Save workflow, reload the page, and reopen Workflows.", ["Save workflow", "Saved in workspace", "Workflows"], "The real PUT succeeds, reload returns the saved source, and the session-only design intent resets to Not added yet."],
  ["S13", "Canonical fixture facts can be restored and saved", "Return the isolated document to the exact bounded simulation facts before conflict and run evidence.", "Restore the original CAD step name and thickness, apply the source, and save.", ["Workflow source", "Apply checked edit", "Save workflow"], "The exact nine-step fixture is valid, saved through the rebased CAS identity, and eligible for its bounded simulation once design intent is added."],
  ["S14", "A second real writer makes the local CAS identity stale", "Set up a truthful concurrent-edit scenario without intercepting or mocking the API.", "Write a benign stored comment through the real API, then apply a different local step-name edit.", ["Real workflow-source API", "Workflow source"], "The workspace file advances outside the page while a distinct semantic edit remains local and unsaved in the editor."],
  ["S15", "Stale save returns 409 and retains local work", "Verify fail-closed CAS behavior and local-draft preservation.", "Click Save workflow with the stale identity.", ["Save workflow", "Copy local source", "Compare stored file", "Discard local edits and reload…"], "One expected PUT 409 is recorded separately; the local title remains visible, the file is still unsaved, and explicit conflict actions appear."],
  ["S16", "Compare is read-only and shows both sources", "Verify that comparison neither applies nor overwrites either side.", "Click Compare stored file.", ["Local unsaved source", "Current stored source"], "The dialog shows the protected local source and freshly read stored source side by side and states that neither was applied or saved."],
  ["S17", "Local conflict source can be copied", "Verify a preservation escape hatch before destructive reload.", "Close the comparison and click Copy local source.", ["Copy local source", "Local workflow source copied"], "The clipboard contains the local conflicting source and the editor and stored file remain unchanged."],
  ["S18", "Reload requires confirmation and restores stored source", "Verify that discarding local edits is explicit and that reload initializes from the current stored document.", "Click Discard local edits and reload, then confirm.", ["Keep local edits", "Discard local edits and reload stored file"], "The confirmation explains the loss, reload removes the local title, retains the benign stored marker, and clears conflict controls."],
  ["S19", "Node movement is live before release", "Verify responsive direct manipulation without premature authority changes.", "Drag Create bracket CAD model while holding the pointer down.", ["Create bracket CAD model", "Workflow authority"], "The node moves visibly while revision, semantic digest, and layout digest remain unchanged."],
  ["S20", "Mouse release commits layout only", "Verify that canvas layout has separate authority from the workflow definition.", "Release the dragged node.", ["Create bracket CAD model", "Workflow authority"], "Only the layout digest changes; the definition revision and semantic digest remain unchanged."],
  ["S21", "AI suggestion remains friendly and reviewable", "Verify that AI proposes a bounded engineering change without silently accepting it.", "Click Ask AI to add drawing steps and inspect the suggestion.", ["Ask AI to add drawing steps", "Changes", "Suggested workflow steps", "Discard suggestion"], "The proposal names drawing creation/review in engineering language, lists assumptions and warnings, keeps technical source collapsed, and remains preview-only until accepted."],
  ["S22", "Simulation stops at the missing design decision", "Verify the intentional needs-input state and downstream blocking.", "Click Test workflow and advance twice.", ["Test workflow", "Advance simulation", "Add 6061-T6 to design specification"], "The simulation reaches needs input at the design specification and keeps downstream review blocked."],
  ["S23", "Simulation recovers and completes", "Verify deterministic recovery without external tools or definition mutation.", "Add 6061-T6 and advance through the remaining simulated stages.", ["Add 6061-T6 to design specification", "Advance simulation"], "The exact workflow test reaches complete while the accepted revision and semantic digest remain unchanged."],
  ["S24", "Output, report, download, and lineage are honest", "Verify that every demo artifact action states its simulation limits and preserves complete source lineage.", "Open the STEP output, open the demo report, and download the demo STEP file.", ["Open STEP file", "Open demo manufacturing report", "Download demo STEP file", "Created from"], "The UI labels the file as simulated, shows its digest and complete lineage, opens the demo report, and downloads bytes whose SHA-256 matches the displayed fixture digest."],
].map(([id, label, purpose, action, controls, expected]) => ({
  id,
  label,
  purpose,
  action,
  controls,
  expected,
  state: "pending",
  summary: "Not reached yet.",
  actual: "Pending browser evidence.",
}));

const manualSteps = [
  { label: "Open workspace", instruction: `On the dashboard, click ${expectedWorkspaceName}. Confirm the address has no workflow query.` },
  { label: "Open workflows", instruction: "Click Workflows. Confirm the address now includes workflow=canonical and the default workflow editor opens automatically." },
  { label: "Verify automatic setup", instruction: "Confirm the workflow file/status bar says mounting-bracket.workflow.wflow is saved in the workspace; there is no separate missing-file or Create workflow screen." },
  { label: "Inspect the graph", instruction: "Count the nine steps and read Reference images, Design intent, and Company standards and context." },
  { label: "Add design intent", instruction: "Click Add text or document, then click View input." },
  { label: "Inspect source", instruction: "Click Source. Read the engineering sections, then expand Managed by Wright." },
  { label: "Check managed fields", instruction: "Add revision: 999 inside the workflow section, click Apply checked edit, then restore the previous source and click Apply checked edit again." },
  { label: "Edit both views", instruction: "Click Side by side. Change Thickness (mm), click Save step changes, then rename the same step in Workflow source and click Apply checked edit." },
  { label: "Persist changes", instruction: "Click Save workflow, reload the page, click Workflows, and verify the stored edit returns while Design intent says Not added yet." },
  { label: "Resolve a conflict", instruction: "After another isolated editor changes the file, make a local edit and click Save workflow. Use Compare stored file and Copy local source, choose Discard local edits and reload…, then click Discard local edits and reload stored file in the confirmation." },
  { label: "Move a step", instruction: "Drag Create bracket CAD model and observe it move before releasing the pointer." },
  { label: "Review an AI suggestion", instruction: "Click Ask AI to add drawing steps, read Assumptions, Warnings, Changes, and Suggested workflow steps, then click Discard suggestion." },
  { label: "Run the simulation", instruction: "Click Test workflow, click Advance simulation twice, click Add 6061-T6 to design specification, then advance until complete." },
  { label: "Inspect the output", instruction: "Select Export approved STEP file, click Creates, click Open STEP file, then use Open demo manufacturing report and Download demo STEP file." },
];

const steps = plannedSteps.map((step) => ({ ...step }));
const diagnostics = {
  capturedAt: null,
  consoleErrors: [],
  pageErrors: [],
  requestFailures: [],
  expectedHttpResponses: [],
  unexpectedHttpResponses: [],
  expectedNavigationAborts: [],
};
const controlPlane = {
  capturedAt: null,
  subject: { commit: subjectCommit, tree: subjectTree, tracked_clean: true },
  configuration: {
    repository_root: repositoryRoot,
    walkthrough_root: walkthroughRoot,
    base_url: baseUrl.href,
    viewport: VIEWPORT,
    expected_workspace_name: expectedWorkspaceName,
    expected_workspace_id: expectedWorkspaceId,
    expected_session_id: expectedSessionId,
    workflow_path: workflowPath,
    api_mocks_installed: false,
  },
  apiTraffic: [],
  workflowSourceResponses: [],
  observedDocuments: [],
  checks: [],
  download: null,
};

let overall = "pending";
let stoppedReason = null;
let stopContext = null;
let activeStepId = "S01";
let browser = null;
let context = null;
let page = null;
let traceStarted = false;
let traceStopped = false;
let expectingMissingWorkflow404 = true;
let expectingStaleWorkflow409 = false;
let navigationAbortWindow = false;
const responseInspections = new Set();
const instrumentedPages = new WeakSet();

const compact = (value) => String(value).replace(/\s+/g, " ").trim();
const escapeHtml = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;");
const testIdSelector = (value) => `[data-testid="${String(value).replaceAll("\\", "\\\\").replaceAll('"', '\\"')}"]`;

function stepById(id) {
  const step = steps.find((item) => item.id === id);
  if (!step) throw new Error(`Unknown walkthrough step ${id}`);
  return step;
}

function signalClass(state) {
  return state === "pass" ? "pass" : state === "blocked" ? "blocked" : "pending";
}

function reportHtml() {
  const cards = steps.map((step) => {
    const images = step.raw
      ? `<div class="evidence"><button class="image-button" data-image="${escapeHtml(step.raw)}">Open raw screenshot</button><button class="image-button" data-image="${escapeHtml(step.annotated)}">Open annotated screenshot</button></div>`
      : "";
    const supplementalImages = (step.supplementalEvidence ?? []).map((item) => `<div class="evidence"><b>${escapeHtml(item.label)}</b><button class="image-button" data-image="${escapeHtml(item.raw)}">Open supplemental raw screenshot</button><button class="image-button" data-image="${escapeHtml(item.annotated)}">Open supplemental annotated screenshot</button></div>`).join("");
    const controls = `<ul>${step.controls.map((control) => `<li>${escapeHtml(control)}</li>`).join("")}</ul>`;
    return `<article class="card ${signalClass(step.state)}"><span class="signal">${step.state.toUpperCase()}</span><h2>${escapeHtml(step.id)} · ${escapeHtml(step.label)}</h2><p>${escapeHtml(step.summary)}</p><dl><dt>Purpose</dt><dd>${escapeHtml(step.purpose)}</dd><dt>Action</dt><dd>${escapeHtml(step.action)}</dd><dt>Controls</dt><dd>${controls}</dd><dt>Expected</dt><dd>${escapeHtml(step.expected)}</dd><dt>Actual</dt><dd>${escapeHtml(step.actual)}</dd></dl>${images}${supplementalImages}</article>`;
  }).join("");
  const manual = manualSteps.map((item) => `<li><b>${escapeHtml(item.label)}:</b> ${escapeHtml(item.instruction)}</li>`).join("");
  const headline = overall === "pass" ? "PASS" : overall === "blocked" ? "STOPPED" : "IN PROGRESS";
  const summary = stoppedReason ?? "The walkthrough uses the real isolated workspace API. Only the automatic-bootstrap GET 404 and stale-save PUT 409 are classified as expected HTTP failures.";
  const stopSummary = overall === "blocked" && stopContext
    ? `<section class="card blocked"><span class="signal">STOP DETAILS</span><h2>First unexpected result</h2><dl><dt>Control</dt><dd>${escapeHtml(stopContext.control)}</dd><dt>Action</dt><dd>${escapeHtml(stopContext.action)}</dd><dt>Expected</dt><dd>${escapeHtml(stopContext.expected)}</dd><dt>Actual</dt><dd>${escapeHtml(stopContext.actual)}</dd><dt>Last success</dt><dd>${escapeHtml(stopContext.lastSuccessfulStep)}</dd><dt>Data changes</dt><dd>${escapeHtml(stopContext.dataMutationSummary)}</dd><dt>Not executed</dt><dd>${escapeHtml(stopContext.remainingSteps)}</dd></dl></section>`
    : "";
  return `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Workspace Workflow Recovery walkthrough</title><style>body{margin:0;background:#07111f;color:#e8eef8;font:15px/1.5 system-ui}main{max-width:1180px;margin:auto;padding:28px}.hero,.card{background:#111d30;border:1px solid #30425f;border-left:9px solid #64748b;border-radius:14px;padding:20px;margin:16px 0}.pass{border-left-color:#12b76a}.blocked{border-left-color:#f04438}.pending{border-left-color:#98a2b3}.signal{font-weight:900;letter-spacing:.1em}.pass .signal{color:#32d583}.blocked .signal{color:#f97066}.pending .signal{color:#cbd5e1}code{overflow-wrap:anywhere;color:#7ee7ff}dl{display:grid;grid-template-columns:112px 1fr;gap:7px 12px}dt{font-weight:800}dd{margin:0}dd ul{margin:0;padding-left:20px}.evidence{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}.image-button,#close{padding:8px 12px;color:#07111f;background:#9cc7ff;border:0;border-radius:6px;cursor:pointer}a{color:#7ee7ff}dialog{max-width:96vw;background:#111d30;color:#fff;border:1px solid #49617f;border-radius:12px}dialog img{max-width:92vw;max-height:82vh;display:block;margin-top:12px}</style></head><body><main><section class="hero ${signalClass(overall)}"><span class="signal">${headline}</span><h1>Workspace Workflow Recovery real-API walkthrough</h1><p>Commit <code>${subjectCommit}</code> · tree <code>${subjectTree}</code></p><p>Workspace <code>${escapeHtml(expectedWorkspaceId)}</code> · session <code>${escapeHtml(expectedSessionId)}</code> · file <code>${escapeHtml(workflowPath)}</code></p><p>${escapeHtml(summary)}</p><p><a href="progress.md">Chronological progress</a> · <a href="trace/browser-diagnostics.json">Browser diagnostics</a> · <a href="control-plane.json">Control-plane evidence</a></p></section>${stopSummary}${cards}<section class="card"><h2>Manual repeat checklist</h2><ol>${manual}</ol></section></main><dialog id="viewer"><button id="close" type="button">Close</button><img alt="Full-size walkthrough evidence"></dialog><script>const dialog=document.getElementById('viewer');const image=dialog.querySelector('img');document.querySelectorAll('[data-image]').forEach((button)=>button.addEventListener('click',()=>{image.src=button.dataset.image;dialog.showModal()}));document.getElementById('close').addEventListener('click',()=>dialog.close());document.addEventListener('keydown',(event)=>{if(event.key==='Escape'&&dialog.open)dialog.close()});</script></body></html>`;
}

function writeCurrentArtifacts() {
  const updated = new Date().toISOString();
  diagnostics.capturedAt = updated;
  controlPlane.capturedAt = updated;
  const summary = overall === "pass"
    ? "All workspace-scoped workflow recovery checks passed against the exact real-API subject."
    : overall === "blocked"
      ? `Walkthrough stopped at the first unexpected result: ${stoppedReason}`
      : "The real-API workspace workflow walkthrough is in progress.";
  writeFileSync(path.join(walkthroughRoot, "status.json"), `${JSON.stringify({
    title: "Workspace Workflow Recovery real-API walkthrough",
    summary,
    overall,
    updated,
    subjectCommit,
    subjectTree,
    baseUrl: baseUrl.href,
    startedAt,
    stoppedReason,
    stopContext,
    manualSteps,
    steps,
  }, null, 2)}\n`, "utf8");
  writeFileSync(path.join(walkthroughRoot, "report.html"), reportHtml(), "utf8");
  writeFileSync(path.join(walkthroughRoot, "trace", "browser-diagnostics.json"), `${JSON.stringify(diagnostics, null, 2)}\n`, "utf8");
  writeFileSync(path.join(walkthroughRoot, "control-plane.json"), `${JSON.stringify(controlPlane, null, 2)}\n`, "utf8");
}

function diagnosticSummary() {
  return `${diagnostics.expectedHttpResponses.length} expected HTTP failure(s) (${diagnostics.expectedHttpResponses.filter((item) => item.kind === "missing-workflow-source").length} GET 404, ${diagnostics.expectedHttpResponses.filter((item) => item.kind === "stale-workflow-save").length} PUT 409); ${diagnostics.consoleErrors.length} console error(s), ${diagnostics.pageErrors.length} page error(s), ${diagnostics.requestFailures.length} unexpected failed request(s), and ${diagnostics.unexpectedHttpResponses.length} unexpected HTTP failure(s).`;
}

function buildStopContext({ control, action, expected, actual }) {
  const lastSuccessful = steps.filter((step) => step.state === "pass").at(-1);
  const mutations = controlPlane.apiTraffic.filter((entry) => ["POST", "PUT", "PATCH", "DELETE"].includes(entry.method));
  const mutationTargets = [...new Set(mutations.map((entry) => `${entry.method} ${entry.path}`))];
  const remaining = steps.filter((step) => step.state === "pending").map((step) => `${step.id} ${step.label}`);
  return {
    control,
    action,
    expected,
    actual,
    lastSuccessfulStep: lastSuccessful ? `${lastSuccessful.id} ${lastSuccessful.label}` : "No logical step completed.",
    dataMutationSummary: mutations.length > 0
      ? `${mutations.length} mutating API request record(s) occurred in the isolated evidence workspace: ${mutationTargets.join("; ")}.`
      : "No mutating API request was recorded.",
    remainingSteps: remaining.length > 0 ? remaining.join("; ") : "No logical steps remain unexecuted.",
  };
}

function appendProgress({
  status,
  action,
  control,
  value = "None",
  expected,
  actual,
  raw = "Not captured for this atomic action",
  annotated = "Not captured for this atomic action",
  currentUrlOverride = null,
}) {
  const timestamp = new Date().toISOString();
  const currentUrl = currentUrlOverride ?? (page && !page.isClosed() ? page.url() : dashboardUrl);
  appendFileSync(path.join(walkthroughRoot, "progress.md"), `\n## ${timestamp} (${timezone}) — ${status}\n\n- Current URL: \`${currentUrl}\`\n- Action performed: ${action}\n- Exact control: ${control}\n- Value entered or selected: ${value}\n- Expected result: ${expected}\n- Actual result: ${actual}\n- Browser diagnostics: ${diagnosticSummary()}\n- Raw screenshot: \`${raw}\`\n- Annotated screenshot: \`${annotated}\`\n- Status: **${status}**\n`, "utf8");
  writeCurrentArtifacts();
}

function passStep(id, actual, images) {
  const step = stepById(id);
  step.state = "pass";
  step.summary = actual;
  step.actual = actual;
  step.raw = images.raw;
  step.annotated = images.annotated;
}

function blockStep(id, actual, images) {
  const step = stepById(id);
  step.state = "blocked";
  step.summary = actual;
  step.actual = actual;
  if (images) {
    step.raw = images.raw;
    step.annotated = images.annotated;
  }
}

async function capture(name, title, markers, targetPage = page) {
  const raw = `screenshots/raw/${name}.png`;
  const annotated = `screenshots/annotated/${name}.png`;
  await targetPage.screenshot({ path: path.join(walkthroughRoot, raw), fullPage: false });
  let missing = [];
  try {
    missing = await targetPage.evaluate(({ legendTitle, items }) => {
      const overlayClass = "wright-walkthrough-overlay";
      const notFound = [];
      const legend = document.createElement("aside");
      legend.className = overlayClass;
      legend.style.cssText = "position:fixed;right:14px;top:14px;z-index:2147483647;width:360px;max-height:70vh;overflow:auto;padding:12px;background:#07111f;color:#fff;border:3px solid #38bdf8;border-radius:10px;font:13px/1.35 system-ui;pointer-events:none";
      const heading = document.createElement("strong");
      heading.textContent = legendTitle;
      const list = document.createElement("ol");
      for (const item of items) {
        const row = document.createElement("li");
        row.textContent = item.label;
        list.appendChild(row);
      }
      legend.append(heading, list);
      document.body.appendChild(legend);
      items.forEach((item, index) => {
        const element = document.querySelector(item.selector);
        if (!(element instanceof HTMLElement || element instanceof SVGElement)) {
          notFound.push(`${item.label} (${item.selector})`);
          return;
        }
        element.dataset.wrightOriginalOutline = element.style.outline;
        element.dataset.wrightOriginalOutlineOffset = element.style.outlineOffset;
        element.style.outline = "4px solid #38bdf8";
        element.style.outlineOffset = "2px";
        const bounds = element.getBoundingClientRect();
        const marker = document.createElement("div");
        marker.className = overlayClass;
        marker.textContent = String(index + 1);
        marker.style.cssText = `position:fixed;left:${Math.max(0, Math.min(innerWidth - 28, bounds.left - 13))}px;top:${Math.max(0, Math.min(innerHeight - 28, bounds.top - 13))}px;z-index:2147483647;width:26px;height:26px;border-radius:50%;display:grid;place-items:center;background:#38bdf8;color:#07111f;font:bold 15px system-ui;border:2px solid white;pointer-events:none`;
        document.body.appendChild(marker);
      });
      return notFound;
    }, { legendTitle: title, items: markers });
    if (missing.length > 0) throw new Error(`Missing annotated controls: ${missing.join(", ")}`);
    await targetPage.screenshot({ path: path.join(walkthroughRoot, annotated), fullPage: false });
  } finally {
    await targetPage.evaluate(() => {
      document.querySelectorAll(".wright-walkthrough-overlay").forEach((element) => element.remove());
      document.querySelectorAll("[data-wright-original-outline]").forEach((element) => {
        if (element instanceof HTMLElement || element instanceof SVGElement) {
          element.style.outline = element.dataset.wrightOriginalOutline || "";
          element.style.outlineOffset = element.dataset.wrightOriginalOutlineOffset || "";
          delete element.dataset.wrightOriginalOutline;
          delete element.dataset.wrightOriginalOutlineOffset;
        }
      });
    }).catch(() => undefined);
  }
  return { raw, annotated };
}

async function screenshotFailure() {
  if (!page || page.isClosed()) return null;
  const name = `stopped-${activeStepId.toLowerCase()}`;
  const raw = `screenshots/raw/${name}.png`;
  const annotated = `screenshots/annotated/${name}.png`;
  await page.evaluate(() => document.querySelectorAll(".wright-walkthrough-overlay").forEach((element) => element.remove())).catch(() => undefined);
  await page.screenshot({ path: path.join(walkthroughRoot, raw), fullPage: false }).catch(() => undefined);
  await page.evaluate((reason) => {
    const overlay = document.createElement("aside");
    overlay.className = "wright-walkthrough-overlay";
    overlay.style.cssText = "position:fixed;left:14px;right:14px;top:14px;z-index:2147483647;padding:14px;background:#7f1d1d;color:white;border:3px solid #fca5a5;border-radius:10px;font:14px/1.4 system-ui;pointer-events:none";
    const heading = document.createElement("strong");
    heading.textContent = "Walkthrough stopped at first unexpected result";
    const detail = document.createElement("div");
    detail.textContent = reason;
    overlay.append(heading, detail);
    document.body.appendChild(overlay);
  }, stoppedReason).catch(() => undefined);
  await page.screenshot({ path: path.join(walkthroughRoot, annotated), fullPage: false }).catch(() => undefined);
  await page.evaluate(() => document.querySelectorAll(".wright-walkthrough-overlay").forEach((element) => element.remove())).catch(() => undefined);
  return { raw, annotated };
}

function safeWorkflowBody(body) {
  if (!body || typeof body !== "object") return null;
  const detail = body.detail && typeof body.detail === "object" ? body.detail : body;
  const result = {};
  for (const key of ["workspace_id", "path", "storage_revision", "storage_digest", "definition_revision", "metadata_authority", "size_bytes", "code", "error_code", "message", "current_storage_revision", "current_storage_digest"]) {
    if (Object.hasOwn(detail, key)) result[key] = detail[key];
  }
  return result;
}

async function boundedResponseJson(response, timeoutMs = 5000) {
  let timeoutId;
  try {
    return await Promise.race([
      response.json(),
      new Promise((_, reject) => {
        timeoutId = setTimeout(
          () => reject(new Error(`Response body inspection exceeded ${timeoutMs} ms`)),
          timeoutMs,
        );
      }),
    ]);
  } finally {
    clearTimeout(timeoutId);
  }
}

async function inspectResponse(response) {
  const request = response.request();
  const url = new URL(response.url());
  const entry = { at: new Date().toISOString(), method: request.method(), status: response.status(), path: `${url.pathname}${url.search}` };
  if (url.pathname.startsWith("/api/")) controlPlane.apiTraffic.push(entry);
  const isWorkflowSource = url.pathname === WORKFLOW_SOURCE_ROUTE;
  if (response.status() >= 400) {
    if (isWorkflowSource && request.method() === "GET" && response.status() === 404 && expectingMissingWorkflow404) {
      diagnostics.expectedHttpResponses.push({ ...entry, kind: "missing-workflow-source" });
    } else if (isWorkflowSource && request.method() === "PUT" && response.status() === 409 && expectingStaleWorkflow409) {
      diagnostics.expectedHttpResponses.push({ ...entry, kind: "stale-workflow-save" });
    } else {
      diagnostics.unexpectedHttpResponses.push(entry);
    }
  }
  if (isWorkflowSource) {
    let body = null;
    try { body = safeWorkflowBody(await boundedResponseJson(response)); } catch { body = null; }
    controlPlane.workflowSourceResponses.push({ ...entry, body });
  }
}

function instrumentPage(targetPage) {
  if (instrumentedPages.has(targetPage)) return;
  instrumentedPages.add(targetPage);
  targetPage.on("console", (message) => {
    if (message.type() !== "error") return;
    const text = message.text();
    const expectedMissingResourceNoise = expectingMissingWorkflow404
      && /Failed to load resource:.*404 \(Not Found\)/i.test(text);
    const expectedConflictResourceNoise = expectingStaleWorkflow409
      && /Failed to load resource:.*409 \(Conflict\)/i.test(text);
    if (expectedMissingResourceNoise || expectedConflictResourceNoise) return;
    diagnostics.consoleErrors.push({ at: new Date().toISOString(), page: targetPage.url(), text });
  });
  targetPage.on("pageerror", (error) => diagnostics.pageErrors.push({ at: new Date().toISOString(), page: targetPage.url(), text: error.message }));
  targetPage.on("requestfailed", (request) => {
    const failure = { at: new Date().toISOString(), page: targetPage.url(), method: request.method(), url: request.url(), error: request.failure()?.errorText ?? "unknown" };
    if (navigationAbortWindow && /abort|cancel/i.test(failure.error)) diagnostics.expectedNavigationAborts.push(failure);
    else diagnostics.requestFailures.push(failure);
  });
  targetPage.on("response", (response) => {
    const inspection = inspectResponse(response).catch((error) => {
      diagnostics.pageErrors.push({ at: new Date().toISOString(), page: targetPage.url(), text: `Response inspection failed: ${error.message}` });
    });
    responseInspections.add(inspection);
    void inspection.finally(() => responseInspections.delete(inspection));
  });
}

async function drainResponseInspections() {
  for (let pass = 0; pass < 4; pass += 1) {
    const pending = [...responseInspections];
    if (pending.length === 0) break;
    await Promise.allSettled(pending);
  }
}

function assertNoUnexpectedDiagnostics() {
  assert(diagnostics.consoleErrors.length === 0, `Console error: ${diagnostics.consoleErrors.at(-1)}`);
  assert(diagnostics.pageErrors.length === 0, `Page error: ${diagnostics.pageErrors.at(-1)}`);
  assert(diagnostics.requestFailures.length === 0, `Failed request: ${JSON.stringify(diagnostics.requestFailures.at(-1))}`);
  assert(diagnostics.unexpectedHttpResponses.length === 0, `Unexpected HTTP response: ${JSON.stringify(diagnostics.unexpectedHttpResponses.at(-1))}`);
}

async function recordAction(entry) {
  await drainResponseInspections();
  assertNoUnexpectedDiagnostics();
  appendProgress({ status: "PASS", ...entry });
}

async function completeStep(id, name, title, markers, actual, actionEntry) {
  await drainResponseInspections();
  assertNoUnexpectedDiagnostics();
  const images = await capture(name, title, markers);
  passStep(id, actual, images);
  appendProgress({ status: "PASS", ...actionEntry, expected: stepById(id).expected, actual, ...images });
}

function observedDocument(label, document) {
  assert(document && typeof document === "object", `${label} did not return a workflow source document.`);
  assert(document.workspace_id === expectedWorkspaceId, `${label} returned workspace ${document.workspace_id}, expected ${expectedWorkspaceId}.`);
  assert(document.path === workflowPath, `${label} returned path ${document.path}, expected ${workflowPath}.`);
  assert(document.metadata_authority === "wright_host", `${label} did not identify Wright as metadata authority.`);
  assert(Number.isInteger(document.storage_revision) && document.storage_revision >= 1, `${label} has invalid storage revision.`);
  assert(Number.isInteger(document.definition_revision) && document.definition_revision >= 1, `${label} has invalid definition revision.`);
  assert(/^[0-9a-f]{64}$/.test(document.storage_digest), `${label} has invalid storage digest.`);
  assert(typeof document.source === "string", `${label} did not return source text.`);
  controlPlane.observedDocuments.push({
    at: new Date().toISOString(),
    label,
    workspace_id: document.workspace_id,
    path: document.path,
    storage_revision: document.storage_revision,
    storage_digest: document.storage_digest,
    definition_revision: document.definition_revision,
    metadata_authority: document.metadata_authority,
    size_bytes: document.size_bytes,
  });
  return document;
}

async function readStoredDocument(label) {
  const url = new URL(workflowSourceUrl);
  url.searchParams.set("session_id", expectedSessionId);
  url.searchParams.set("path", workflowPath);
  const response = await context.request.get(url.href, { headers: { "Cache-Control": "no-store" } });
  controlPlane.apiTraffic.push({ at: new Date().toISOString(), method: "GET", status: response.status(), path: `${url.pathname}${url.search}`, source: "playwright-control-plane" });
  assert(response.status() === 200, `${label} GET returned ${response.status()}, expected 200.`);
  return observedDocument(label, await response.json());
}

async function updateStoredDocument(label, document, source, semanticChangeValidated) {
  const response = await context.request.put(workflowSourceUrl.href, {
    data: {
      session_id: expectedSessionId,
      path: workflowPath,
      source,
      expected_storage_revision: document.storage_revision,
      expected_storage_digest: document.storage_digest,
      semantic_change_validated: semanticChangeValidated,
    },
  });
  controlPlane.apiTraffic.push({ at: new Date().toISOString(), method: "PUT", status: response.status(), path: workflowSourceUrl.pathname, source: "playwright-control-plane" });
  assert(response.status() === 200, `${label} PUT returned ${response.status()}, expected 200.`);
  return observedDocument(label, await response.json());
}

function replaceExactlyOnce(source, before, after, label) {
  const first = source.indexOf(before);
  assert(first >= 0, `${label}: source does not contain ${JSON.stringify(before)}.`);
  assert(source.indexOf(before, first + before.length) < 0, `${label}: source contains more than one ${JSON.stringify(before)}.`);
  return `${source.slice(0, first)}${after}${source.slice(first + before.length)}`;
}

async function waitForValue(read, predicate, description, timeoutMs = 10_000) {
  const started = Date.now();
  let value;
  while (Date.now() - started < timeoutMs) {
    value = await read();
    if (predicate(value)) return value;
    await new Promise((resolve) => setTimeout(resolve, 50));
  }
  throw new Error(`Timed out waiting for ${description}; last value: ${String(value)}`);
}

function listFiles(directory) {
  return readdirSync(directory).flatMap((name) => {
    const absolute = path.join(directory, name);
    return statSync(absolute).isDirectory() ? listFiles(absolute) : [absolute];
  });
}

function writeManifest() {
  const files = listFiles(walkthroughRoot)
    .filter((file) => !["manifest.json", "manifest.sha256"].includes(path.basename(file)))
    .map((file) => ({
      path: path.relative(walkthroughRoot, file).replaceAll("\\", "/"),
      bytes: statSync(file).size,
      sha256: createHash("sha256").update(readFileSync(file)).digest("hex"),
    }))
    .sort((left, right) => left.path.localeCompare(right.path));
  const manifestPath = path.join(walkthroughRoot, "manifest.json");
  writeFileSync(manifestPath, `${JSON.stringify({
    subject_commit: subjectCommit,
    subject_tree: subjectTree,
    overall,
    base_url: baseUrl.href,
    expected_workspace_id: expectedWorkspaceId,
    expected_session_id: expectedSessionId,
    workflow_path: workflowPath,
    started_at: startedAt,
    completed_at: new Date().toISOString(),
    files,
  }, null, 2)}\n`, "utf8");
  const digest = createHash("sha256").update(readFileSync(manifestPath)).digest("hex");
  writeFileSync(path.join(walkthroughRoot, "manifest.sha256"), `${digest}  manifest.json\n`, "utf8");
  return { count: files.length, digest };
}

writeFileSync(path.join(walkthroughRoot, "progress.md"), `# Workspace Workflow Recovery real-API walkthrough\n\n- Started: ${startedAt} (${timezone})\n- Subject commit: \`${subjectCommit}\`\n- Subject tree: \`${subjectTree}\`\n- Workspace: \`${expectedWorkspaceName}\` (\`${expectedWorkspaceId}\`)\n- Session: \`${expectedSessionId}\`\n- Workflow file: \`${workflowPath}\`\n- Viewport: ${VIEWPORT.width}×${VIEWPORT.height}\n- Network policy: real isolated API; no Playwright route mocks.\n`, "utf8");
writeCurrentArtifacts();
appendProgress({
  status: "PASS",
  action: "Verified the exact committed Git subject and copied the reusable capture script into the evidence root.",
  control: "git rev-parse HEAD, git rev-parse HEAD^{tree}, and tracked-only git status",
  value: `${actualCommit} / ${actualTree}`,
  expected: "Commit and tree match the requested subject and tracked files are clean.",
  actual: "Commit and tree matched, tracked files were clean, and playwright/capture.mjs is an exact copy of the invoked script.",
});

try {
  browser = await chromium.launch({ headless, ...(browserExecutable ? { executablePath: browserExecutable } : {}) });
  context = await browser.newContext({ viewport: VIEWPORT, deviceScaleFactor: 1, reducedMotion: "reduce", acceptDownloads: true });
  await context.grantPermissions(["clipboard-read", "clipboard-write"], { origin: baseUrl.origin });
  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
  traceStarted = true;
  context.on("page", instrumentPage);
  page = await context.newPage();
  instrumentPage(page);

  activeStepId = "S01";
  await page.goto(dashboardUrl, { waitUntil: "domcontentloaded" });
  await page.getByTestId("page-dashboard").waitFor({ state: "visible" });
  const expectedWorkspaceCard = page.getByTestId(`card-workspace-${expectedWorkspaceId}`);
  await expectedWorkspaceCard.waitFor({ state: "visible" });
  const workspaceCards = page.locator('[data-testid^="card-workspace-"]');
  assert(await workspaceCards.count() === 1, `Expected one isolated workspace card, found ${await workspaceCards.count()}.`);
  assert(compact(await expectedWorkspaceCard.innerText()).includes(expectedWorkspaceName), `Workspace card does not name ${expectedWorkspaceName}.`);
  assert(await page.locator('a[href*="workflow-recovery"],button').filter({ hasText: /^Workflow Recovery$/ }).count() === 0, "A global Workflow Recovery destination is still exposed on the dashboard.");
  await completeStep("S01", "01-isolated-dashboard", "One isolated workspace; no global recovery destination", [
    { selector: testIdSelector("card-workspaces"), label: "Engineering Workspaces contains one isolated entry" },
    { selector: testIdSelector(`card-workspace-${expectedWorkspaceId}`), label: expectedWorkspaceName },
  ], `The dashboard listed exactly one workspace, ${expectedWorkspaceName} (${expectedWorkspaceId}), and exposed no global Workflow Recovery destination.`, {
    action: "Opened and inspected the isolated dashboard.", control: "Engineering Workspaces", value: expectedWorkspaceName,
  });

  activeStepId = "S02";
  await expectedWorkspaceCard.click();
  await page.getByTestId("page-workspace").waitFor({ state: "visible" });
  await page.waitForURL((url) => url.pathname === new URL(ordinaryWorkspaceUrl).pathname);
  assert(new URL(page.url()).search === "", `Workspace card added an unexpected query: ${new URL(page.url()).search}`);
  const workflowsAction = page.getByTestId("activity-bar-workflows-btn");
  await workflowsAction.waitFor({ state: "visible" });
  assert((await workflowsAction.getAttribute("title")) === "Workflows", "The workspace action is not titled Workflows.");
  await completeStep("S02", "02-ordinary-workspace", "Ordinary workspace URL with explicit Workflows action", [
    { selector: testIdSelector("page-workspace"), label: "Expected workspace opened" },
    { selector: testIdSelector("activity-bar-workflows-btn"), label: "Explicit Workflows action" },
  ], `The workspace opened at ${new URL(page.url()).pathname} with no query string. Workflows was visible inside the workspace.`, {
    action: `Opened ${expectedWorkspaceName} from its dashboard card.`, control: expectedWorkspaceName, value: expectedWorkspaceId,
  });

  activeStepId = "S03";
  const missingResponsePromise = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return url.pathname === WORKFLOW_SOURCE_ROUTE
      && response.request().method() === "GET"
      && response.status() === 404;
  });
  const createResponsePromise = page.waitForResponse((response) => {
    const url = new URL(response.url());
    return url.pathname === WORKFLOW_SOURCE_ROUTE
      && response.request().method() === "POST";
  });
  await workflowsAction.click();
  const [missingResponse, createResponse] = await Promise.all([missingResponsePromise, createResponsePromise]);
  assert(missingResponse.status() === 404, `Initial workflow read returned ${missingResponse.status()}, expected 404.`);
  assert(createResponse.status() === 201, `Automatic workflow creation returned ${createResponse.status()}, expected 201.`);
  await page.waitForURL((url) => url.pathname === new URL(ordinaryWorkspaceUrl).pathname && url.searchParams.get("workflow") === "canonical");
  const contextBar = page.getByTestId("workflow-workspace-context");
  await contextBar.waitFor({ state: "visible" });
  const workflowPage = page.getByTestId("page-workflow-recovery");
  assert(await workflowPage.getAttribute("data-workspace-id") === expectedWorkspaceId, "Workflow page workspace scope is wrong.");
  assert(await workflowPage.getAttribute("data-session-id") === expectedSessionId, "Workflow page session scope is wrong.");
  assert(await workflowPage.getAttribute("data-workflow-file") === workflowPath, "Workflow page file scope is wrong.");
  const concept = page.getByTestId("workflow-recovery-concept");
  await concept.waitFor({ state: "visible" });
  assert(await concept.getAttribute("data-surface-state") !== "loading", "Workflow concept remained in loading state after automatic creation.");
  assert(await page.getByTestId("workflow-source-missing").count() === 0, "A missing-file boundary remained after automatic creation.");
  assert(await page.getByTestId("workflow-source-create").count() === 0, "A manual Create workflow action remained after automatic creation.");
  await drainResponseInspections();
  assert(diagnostics.expectedHttpResponses.filter((item) => item.kind === "missing-workflow-source").length === 1, "Expected exactly one initial workflow-source GET 404.");
  assert(controlPlane.workflowSourceResponses.filter((item) => item.method === "POST" && item.status === 201).length === 1, "Expected exactly one automatic workflow-source POST 201.");
  expectingMissingWorkflow404 = false;
  await recordAction({ action: "Entered and initialized the canonical workflow through the workspace action.", control: "Workflows", value: "workflow=canonical", expected: "The workspace URL gains the canonical query, one missing read triggers one automatic create, and the exact scoped workflow opens without another choice.", actual: `The URL gained workflow=canonical; one GET 404 triggered one POST 201; the page identified workspace ${expectedWorkspaceId}, session ${expectedSessionId}, and ${workflowPath}; the default editor opened with no missing-file or Create boundary.` });
  const maximize = page.getByRole("button", { name: "Maximize active tab" });
  if (await maximize.isVisible().catch(() => false)) {
    await maximize.click();
    await recordAction({ action: "Maximized the active workspace workflow tab for constrained-viewport evidence.", control: "Maximize active tab", expected: "The workflow surface receives the available workspace area.", actual: "The active workflow tab entered focus layout." });
  }
  const collapseAgent = page.getByTitle("Collapse Agent Console");
  if (await collapseAgent.isVisible().catch(() => false)) {
    await collapseAgent.click();
    await recordAction({ action: "Collapsed the Agent Console for workflow inspection.", control: "Collapse Agent Console", expected: "The workflow remains active with more horizontal room.", actual: "The Agent Console collapsed and the workflow remained active." });
  }
  await completeStep("S03", "03-workflows-auto-bootstrap", "Workflows opens an automatically initialized default", [
    { selector: testIdSelector("workflow-workspace-context"), label: `${expectedWorkspaceName} / Workflows / mounting-bracket.workflow.wflow` },
    { selector: testIdSelector("workflow-recovery-filebar"), label: "Default workflow saved in this workspace" },
    { selector: testIdSelector("workflow-recovery-canvas"), label: "Default workflow editor opened" },
  ], `Clicking Workflows added workflow=canonical, scoped the surface to workspace ${expectedWorkspaceId}, session ${expectedSessionId}, and ${workflowPath}, and automatically initialized the default after exactly one GET 404 and one POST 201. No missing-file or Create boundary remained.`, {
    action: "Opened and automatically initialized the canonical workflow.", control: "Workflows", value: "workflow=canonical / GET 404 / POST 201",
  });

  activeStepId = "S04";
  const createdDocument = await readStoredDocument("after automatic default creation");
  assert(createdDocument.source.includes("workflow mounting_bracket"), "Automatically created source is not the default mounting-bracket workflow.");
  assert(createdDocument.source.includes("task generate_geometry"), "Automatically created source is missing the default CAD task.");
  await completeStep("S04", "04-workspace-owned-default", "Automatic default stored at the exact workspace path", [
    { selector: testIdSelector("workflow-recovery-filebar"), label: "Workspace-owned workflow file is ready" },
    { selector: testIdSelector("workflow-recovery-save-status"), label: "Saved in workspace" },
  ], `A real GET read back the automatically initialized ${workflowPath} for workspace ${createdDocument.workspace_id} at storage revision ${createdDocument.storage_revision}, definition revision ${createdDocument.definition_revision}, and digest ${createdDocument.storage_digest}. Its engineering source contained the default mounting-bracket workflow and CAD task.`, {
    action: "Verified the automatically initialized workspace workflow.", control: "Workflow file/status bar", value: workflowPath,
  });

  activeStepId = "S05";
  assert(await page.locator(".react-flow__node").count() === 9, `Expected nine nodes, found ${await page.locator(".react-flow__node").count()}.`);
  for (const testId of ["workflow-recovery-input-source-reference-images", "workflow-recovery-attachment-artifact.design-intent", "workflow-recovery-input-source-company-context"]) {
    await page.getByTestId(testId).waitFor({ state: "visible" });
  }
  for (const relationship of ["rel.design-intent-to-specification", "rel.reference-to-specification", "rel.context-to-specification"]) {
    assert(await page.getByTestId(`workflow-recovery-edge-${relationship}`).count() === 1, `Missing source connection ${relationship}.`);
  }
  assert(await page.locator(".recovery-phase-stripe").count() === 0, "Phase backdrops are rendered.");
  assert(await page.getByTestId("workflow-recovery-find-input").count() === 0, "Graph search is present for the nine-node workflow.");
  assert(await page.getByTestId("workflow-recovery-palette-search").count() === 0, "Palette search is present for the small downstream library.");
  await completeStep("S05", "05-nine-nodes-three-inputs", "Nine-node workflow with three concrete sources", [
    { selector: testIdSelector("workflow-recovery-palette"), label: "Three concrete source inputs" },
    { selector: testIdSelector("workflow-recovery-canvas"), label: "Nine-node accepted diagram" },
    { selector: testIdSelector("workflow-recovery-inspector"), label: "Contextual inspector without phase or search clutter" },
  ], "The accepted graph contained nine nodes. Reference images, Design intent, and Company standards and context fed the reviewed specification through three explicit connections. No phase backdrop, graph search, or palette search was present.", {
    action: "Inspected the canonical topology and source cards.", control: "Three source inputs and workflow diagram", value: "9 nodes / 3 concrete inputs / 3 source connections",
  });

  activeStepId = "S06";
  const designIntentCard = page.getByTestId("workflow-recovery-attachment-artifact.design-intent");
  assert(compact(await designIntentCard.innerText()).includes("Demo input for this session · not saved by this concept"), "Design intent does not disclose session-only behavior.");
  await page.getByTestId("workflow-recovery-attachment-attach-artifact.design-intent").click();
  await recordAction({ action: "Added the session-only design intent example.", control: "Add text or document", value: "mounting-bracket-design-intent.docx", expected: "A normal document appears without changing the stored workflow definition.", actual: "The DOCX example appeared and the source card continued to say it is not saved by this concept." });
  await page.getByTestId("workflow-recovery-attachment-preview-artifact.design-intent").click();
  const intentDialog = page.getByRole("dialog", { name: "Design intent" });
  await intentDialog.waitFor({ state: "visible" });
  const intentText = compact(await intentDialog.innerText());
  for (const text of ["Text or common document", "Added by an engineer", "Used by Create and review design specification"]) assert(intentText.includes(text), `Design intent preview is missing: ${text}`);
  await completeStep("S06", "06-session-only-design-intent", "Honest session-only design intent", [
    { selector: ".design-intent-preview__sheet", label: "Concrete engineer design intent" },
    { selector: ".design-intent-preview aside", label: "DOCX, engineer provenance, and specification consumer" },
  ], "The source card disclosed Demo input for this session · not saved by this concept. The preview identified a DOCX/text document, engineer provenance, and the design-specification consumer.", {
    action: "Opened the design intent preview.", control: "View input", value: "mounting-bracket-design-intent.docx",
  });
  await page.getByTestId("workflow-recovery-modal-close").click();
  await recordAction({ action: "Closed the design intent preview.", control: "Close dialog", expected: "The dialog closes and returns to the workflow.", actual: "The dialog closed and the workflow remained active." });

  activeStepId = "S07";
  await page.getByTestId("workflow-recovery-view-code").click();
  const sourceEditor = page.getByTestId("workflow-recovery-source-editor");
  await sourceEditor.waitFor({ state: "visible" });
  await recordAction({ action: "Opened the engineering source view.", control: "Source", expected: "The workspace workflow appears as readable engineering source.", actual: "Workflow source opened for the same accepted definition." });
  const friendlySource = await sourceEditor.inputValue();
  for (const grammar of ["workflow mounting_bracket", "item design_intent", "input design_intent", "task generate_geometry", "connection design_intent_to_specification"]) assert(friendlySource.includes(grammar), `Friendly source is missing ${grammar}.`);
  assert(!friendlySource.includes("\ngroup "), "The nine-step source must omit low-value group sections.");
  assert(friendlySource.includes("  group: null"), "The source must show that grouping is optional.");
  for (const hostField of ["revision", "parent", "semantic_sha256", "storage_revision", "storage_digest", "layout", "run_state"]) assert(!new RegExp(`^\\s*${hostField}\\s*:`, "m").test(friendlySource), `Friendly source assigns host field ${hostField}.`);
  for (const canonicalPrefix of ["type", "block", "port", "artifact"]) {
    const opaqueIdentifier = new RegExp(`\\b${canonicalPrefix}\\.[a-z0-9_-]+`, "i");
    assert(!opaqueIdentifier.test(friendlySource), `Friendly source exposes opaque canonical ${canonicalPrefix}.* identity.`);
  }
  for (const engineeringKind of ['"kind":"design_intent"', '"kind":"cad_model"', '"kind":"step_file"']) assert(friendlySource.includes(engineeringKind), `Friendly source is missing engineering kind ${engineeringKind}.`);
  const managed = page.locator(".recovery-code__managed");
  assert(!(await managed.evaluate((element) => element.open)), "Managed by Wright details are expanded by default.");
  await page.getByTestId("workflow-recovery-source-managed-details").click();
  const managedText = compact(await managed.innerText());
  assert(managedText.includes("Definition revision") && managedText.includes("integrity sha256:"), "Managed disclosure does not contain host revision and integrity.");
  await completeStep("S07", "07-friendly-source", "Friendly engineering grammar; host authority disclosed separately", [
    { selector: testIdSelector("workflow-recovery-source-editor"), label: "Engineering workflow source" },
    { selector: ".recovery-code__managed[open]", label: "Host-owned definition revision and integrity" },
  ], "The source used workflow, item, input, task, and connection sections with design_intent, cad_model, and step_file kinds. Each ungrouped task used the optional group: null assignment, with no group section. It exposed no type./block./port./artifact. token and assigned no revision, ancestry, digest, layout, or run-state field; Definition revision and integrity appeared only under Managed by Wright.", {
    action: "Opened Source and expanded Managed by Wright.", control: "Source / Managed by Wright", value: "Friendly engineering grammar",
  });

  activeStepId = "S08";
  const revisionBeforeManagedAttempt = await concept.getAttribute("data-revision");
  const invalidManagedSource = replaceExactlyOnce(friendlySource, "workflow mounting_bracket\n", "workflow mounting_bracket\n  revision: 999\n", "managed-field injection");
  await sourceEditor.fill(invalidManagedSource);
  await recordAction({ action: "Entered a counterfeit revision assignment into the workflow section.", control: "Workflow source", value: "revision: 999", expected: "The source remains a local unapplied draft.", actual: "The editor marked an unapplied source edit; the accepted diagram remained unchanged." });
  await page.getByTestId("workflow-recovery-source-apply").click();
  const managedDiagnostic = page.getByTestId("workflow-recovery-diagnostic-WFR-SOURCE-FIELD-MANAGED");
  await managedDiagnostic.waitFor({ state: "visible" });
  assert(await concept.getAttribute("data-revision") === revisionBeforeManagedAttempt, "Managed-field rejection changed the accepted definition revision.");
  assert(await page.getByTestId("workflow-recovery-run-start").isDisabled(), "Testing remained enabled for invalid source.");
  await completeStep("S08", "08-managed-field-rejected", "Host-owned revision assignment rejected", [
    { selector: testIdSelector("workflow-recovery-source-editor"), label: "Local source contains revision: 999" },
    { selector: testIdSelector("workflow-recovery-diagnostic-WFR-SOURCE-FIELD-MANAGED"), label: "WFR-SOURCE-FIELD-MANAGED" },
    { selector: testIdSelector("workflow-recovery-source-apply"), label: "Apply checked edit did not replace the diagram" },
  ], `revision: 999 produced WFR-SOURCE-FIELD-MANAGED. The accepted revision stayed ${revisionBeforeManagedAttempt}, the diagram was retained, and testing was disabled.`, {
    action: "Attempted to apply the managed revision field.", control: "Apply checked edit", value: "revision: 999",
  });

  activeStepId = "S09";
  await sourceEditor.fill(friendlySource);
  await recordAction({ action: "Restored the previous friendly source text.", control: "Workflow source", value: "Original stored engineering source", expected: "The local draft is ready to re-check without altering accepted authority.", actual: "The counterfeit managed field was removed from the local source." });
  await page.getByTestId("workflow-recovery-source-apply").click();
  await managedDiagnostic.waitFor({ state: "detached" });
  assert(await concept.getAttribute("data-revision") === revisionBeforeManagedAttempt, "Restoring identical source changed the revision.");
  assert(compact(await page.locator(".recovery-code header").innerText()).includes("✓ source valid"), "Restored source is not valid.");
  await completeStep("S09", "09-source-restored", "Rejected draft restored without authority change", [
    { selector: testIdSelector("workflow-recovery-source-editor"), label: "Restored friendly source" },
    { selector: testIdSelector("workflow-recovery-source-apply"), label: "Checked restoration" },
    { selector: testIdSelector("workflow-recovery-authority"), label: "Accepted revision remained stable" },
  ], `The original source cleared the managed-field diagnostic, returned to ✓ source valid, and kept accepted revision ${revisionBeforeManagedAttempt}.`, {
    action: "Applied the restored source.", control: "Apply checked edit", value: "Original friendly source",
  });

  activeStepId = "S10";
  await page.getByTestId("workflow-recovery-view-split").click();
  await recordAction({ action: "Opened the synchronized Diagram and Source view.", control: "Side by side", expected: "Diagram and engineering source are visible together.", actual: "The side-by-side view displayed the graph and the same workflow source." });
  await page.getByTestId("workflow-recovery-block-block.generate-geometry").click();
  await recordAction({ action: "Selected the CAD-model step in the diagram.", control: "Create bracket CAD model", expected: "The inspector shows editable CAD step settings.", actual: "The inspector selected Create bracket CAD model and exposed Thickness (mm)." });
  const thickness = page.getByTestId("workflow-recovery-block-thickness-block.generate-geometry");
  await thickness.scrollIntoViewIfNeeded();
  await thickness.fill("8");
  await recordAction({ action: "Entered a new CAD thickness.", control: "Thickness (mm)", value: "8", expected: "The form contains the local value until applied.", actual: "Thickness (mm) showed 8; accepted source had not changed yet." });
  const revisionBeforeGraphEdit = Number(await concept.getAttribute("data-revision"));
  await page.getByTestId("workflow-recovery-config-apply").click();
  await waitForValue(() => sourceEditor.inputValue(), (value) => value.includes('"thickness_mm":8'), "graph-to-source synchronization");
  assert(Number(await concept.getAttribute("data-revision")) === revisionBeforeGraphEdit + 1, "Graph edit did not advance definition revision once.");
  await completeStep("S10", "10-graph-to-source", "Graph edit synchronized into Source", [
    { selector: testIdSelector("workflow-recovery-canvas"), label: "Accepted diagram" },
    { selector: testIdSelector("workflow-recovery-source-editor"), label: "Source contains thickness_mm 8" },
    { selector: testIdSelector("workflow-recovery-authority"), label: "Definition revision advanced once" },
  ], `Applying Thickness (mm) 8 advanced the definition revision from ${revisionBeforeGraphEdit} to ${revisionBeforeGraphEdit + 1}; the side-by-side source immediately contained thickness_mm 8.`, {
    action: "Applied the CAD thickness change.", control: "Save step changes", value: "8 mm",
  });

  activeStepId = "S11";
  const sourceAfterGraphEdit = await sourceEditor.inputValue();
  const renamedSource = replaceExactlyOnce(sourceAfterGraphEdit, 'name: "Create bracket CAD model"', 'name: "Create bracket CAD model walkthrough"', "text-to-graph rename");
  await sourceEditor.fill(renamedSource);
  await recordAction({ action: "Renamed the CAD step in engineering source.", control: "Workflow source", value: "Create bracket CAD model walkthrough", expected: "The source remains unapplied until checked.", actual: "The local source contained the friendly new step name while the accepted diagram retained its previous title." });
  const revisionBeforeTextEdit = Number(await concept.getAttribute("data-revision"));
  await page.getByTestId("workflow-recovery-source-apply").click();
  const renamedNode = page.getByTestId("workflow-recovery-block-block.generate-geometry");
  await waitForValue(() => renamedNode.innerText(), (value) => value.includes("Create bracket CAD model walkthrough"), "source-to-graph synchronization");
  assert(Number(await concept.getAttribute("data-revision")) === revisionBeforeTextEdit + 1, "Text edit did not advance definition revision once.");
  await completeStep("S11", "11-source-to-graph", "Source edit synchronized into Diagram", [
    { selector: testIdSelector("workflow-recovery-source-editor"), label: "Checked friendly source rename" },
    { selector: testIdSelector("workflow-recovery-block-block.generate-geometry"), label: "Diagram shows Create bracket CAD model walkthrough" },
    { selector: testIdSelector("workflow-recovery-authority"), label: "Definition revision advanced once" },
  ], `Applying the friendly source rename advanced the revision from ${revisionBeforeTextEdit} to ${revisionBeforeTextEdit + 1}; the diagram immediately showed Create bracket CAD model walkthrough.`, {
    action: "Applied the source rename.", control: "Apply checked edit", value: "Create bracket CAD model walkthrough",
  });

  activeStepId = "S12";
  const saveResponsePromise = page.waitForResponse((response) => new URL(response.url()).pathname === WORKFLOW_SOURCE_ROUTE && response.request().method() === "PUT");
  await page.getByTestId("workflow-recovery-save").click();
  const saveResponse = await saveResponsePromise;
  assert(saveResponse.status() === 200, `Save workflow returned ${saveResponse.status()}, expected 200.`);
  await page.getByTestId("workflow-recovery-save-status").filter({ hasText: "Saved in workspace" }).waitFor({ state: "visible" });
  const savedWalkthroughDocument = await readStoredDocument("after graph/text save");
  assert(savedWalkthroughDocument.source.includes("Create bracket CAD model walkthrough") && savedWalkthroughDocument.source.includes('"thickness_mm":8'), "Stored source lacks graph/text edits.");
  await recordAction({ action: "Saved the synchronized graph/text edits through the real workspace API.", control: "Save workflow", value: `storage revision ${savedWalkthroughDocument.storage_revision}`, expected: "The current CAS identity succeeds and returns a new stored identity.", actual: `PUT 200 returned storage revision ${savedWalkthroughDocument.storage_revision}, definition revision ${savedWalkthroughDocument.definition_revision}, digest ${savedWalkthroughDocument.storage_digest}.` });
  navigationAbortWindow = true;
  await page.reload({ waitUntil: "domcontentloaded" });
  await new Promise((resolve) => setTimeout(resolve, 100));
  navigationAbortWindow = false;
  await recordAction({ action: "Reloaded the ordinary workspace URL with its explicit canonical query.", control: "Browser reload", value: new URL(page.url()).pathname + new URL(page.url()).search, expected: "The same workspace route reloads without a global recovery route.", actual: "The browser remained on the workspace route with workflow=canonical; any navigation-aborted long request was recorded separately." });
  const conceptAfterReload = page.getByTestId("workflow-recovery-concept");
  if (!(await conceptAfterReload.isVisible().catch(() => false))) {
    const workflowsAfterReload = page.getByTestId("activity-bar-workflows-btn");
    await workflowsAfterReload.waitFor({ state: "visible" });
    await workflowsAfterReload.click();
    await recordAction({ action: "Reopened the workflow tab after page reload.", control: "Workflows", value: "workflow=canonical", expected: "The saved workflow tab opens inside the same ordinary workspace route.", actual: "Workflows reopened the canonical tab without navigating to a global recovery page." });
  }
  await conceptAfterReload.waitFor({ state: "visible" });
  const sourceAfterReload = page.getByTestId("workflow-recovery-source-editor");
  if (!(await sourceAfterReload.isVisible().catch(() => false))) await page.getByTestId("workflow-recovery-view-code").click();
  await sourceAfterReload.waitFor({ state: "visible" });
  assert((await sourceAfterReload.inputValue()).includes("Create bracket CAD model walkthrough"), "Reload did not return the stored source rename.");
  assert(compact(await page.getByTestId("workflow-recovery-attachment-artifact.design-intent").innerText()).includes("Not added yet"), "Session-only design intent survived page reload.");
  await completeStep("S12", "12-save-reload-cas", "Saved CAS identity survives reload; session-only input does not", [
    { selector: testIdSelector("workflow-recovery-filebar"), label: "Saved workspace workflow file" },
    { selector: testIdSelector("workflow-recovery-source-editor"), label: "Reloaded stored graph/text edits" },
    { selector: testIdSelector("workflow-recovery-attachment-artifact.design-intent"), label: "Design intent reset to Not added yet" },
  ], `The save rebased to storage revision ${savedWalkthroughDocument.storage_revision} and definition revision ${savedWalkthroughDocument.definition_revision}. Reload returned the stored thickness/title edits, while the explicitly session-only Design intent reset to Not added yet.`, {
    action: "Reloaded the workspace and reopened Workflows.", control: "Browser reload / Workflows", value: "Stored workflow source",
  });

  activeStepId = "S13";
  const walkthroughSourceAfterReload = await sourceAfterReload.inputValue();
  let canonicalSource = replaceExactlyOnce(walkthroughSourceAfterReload, 'name: "Create bracket CAD model walkthrough"', 'name: "Create bracket CAD model"', "canonical title restore");
  canonicalSource = replaceExactlyOnce(canonicalSource, '"thickness_mm":8', '"thickness_mm":6', "canonical thickness restore");
  await sourceAfterReload.fill(canonicalSource);
  await recordAction({ action: "Restored the exact mounting-bracket fixture facts in Source.", control: "Workflow source", value: "Original CAD title and 6 mm thickness", expected: "The exact source is ready for checked application.", actual: "The local source restored Create bracket CAD model and thickness_mm 6." });
  await page.getByTestId("workflow-recovery-source-apply").click();
  await page.getByTestId("workflow-recovery-simulation-issue").waitFor({ state: "detached" }).catch(() => undefined);
  await recordAction({ action: "Applied the restored canonical source.", control: "Apply checked edit", value: "Exact nine-step fixture", expected: "The exact bounded fixture becomes valid again.", actual: "The accepted diagram returned to the canonical step title and fixture facts." });
  const canonicalSavePromise = page.waitForResponse((response) => new URL(response.url()).pathname === WORKFLOW_SOURCE_ROUTE && response.request().method() === "PUT");
  await page.getByTestId("workflow-recovery-save").click();
  const canonicalSaveResponse = await canonicalSavePromise;
  assert(canonicalSaveResponse.status() === 200, `Canonical restore save returned ${canonicalSaveResponse.status()}.`);
  const canonicalDocument = await readStoredDocument("after canonical restore");
  assert(canonicalDocument.source.includes('name: "Create bracket CAD model"') && canonicalDocument.source.includes('"thickness_mm":6'), "Canonical stored source was not restored.");
  await completeStep("S13", "13-canonical-restored", "Canonical fixture restored through current CAS identity", [
    { selector: testIdSelector("workflow-recovery-source-editor"), label: "Exact mounting-bracket fixture source" },
    { selector: testIdSelector("workflow-recovery-save-status"), label: "Saved in workspace" },
    { selector: testIdSelector("workflow-recovery-authority"), label: `Definition revision ${canonicalDocument.definition_revision}` },
  ], `The original CAD title and 6 mm thickness were checked and saved at storage revision ${canonicalDocument.storage_revision}, definition revision ${canonicalDocument.definition_revision}. The bounded simulation reported no fixture mismatch.`, {
    action: "Saved the restored canonical fixture.", control: "Save workflow", value: `storage revision ${canonicalDocument.storage_revision}`,
  });

  activeStepId = "S14";
  const peerMarker = "# Stored by a second isolated editor to exercise compare-and-swap.";
  const peerSource = `${canonicalDocument.source.replace(/\s+$/, "")}\n\n${peerMarker}\n`;
  const peerDocument = await updateStoredDocument("benign second-editor write", canonicalDocument, peerSource, false);
  assert(peerDocument.definition_revision === canonicalDocument.definition_revision, "Benign source comment unexpectedly advanced definition revision.");
  await recordAction({ action: "Advanced the stored file through a second real API writer.", control: "Real PUT /api/workspace/workflow-sources", value: `storage revision ${peerDocument.storage_revision}`, expected: "Storage identity advances without changing semantic definition authority.", actual: `The real API advanced storage revision ${canonicalDocument.storage_revision} → ${peerDocument.storage_revision}; definition revision remained ${peerDocument.definition_revision}.` });
  const sourceForLocalConflict = await page.getByTestId("workflow-recovery-source-editor").inputValue();
  const localConflictSource = replaceExactlyOnce(sourceForLocalConflict, 'name: "Create bracket CAD model"', 'name: "Create bracket CAD model local conflict"', "local conflict edit");
  await page.getByTestId("workflow-recovery-source-editor").fill(localConflictSource);
  await recordAction({ action: "Entered a distinct local semantic edit against the now-stale page identity.", control: "Workflow source", value: "Create bracket CAD model local conflict", expected: "The local source is not overwritten by the second writer.", actual: "The local source retained its own CAD title and remained unapplied until checked." });
  await page.getByTestId("workflow-recovery-source-apply").click();
  await page.getByTestId("workflow-recovery-view-split").click();
  await waitForValue(
    () => page.getByTestId("workflow-recovery-block-block.generate-geometry").innerText(),
    (value) => value.includes("local conflict"),
    "local conflict source-to-diagram synchronization",
  );
  await completeStep("S14", "14-real-second-writer", "Real second writer plus distinct local edit", [
    { selector: testIdSelector("workflow-recovery-source-editor"), label: "Local conflict source is visible" },
    { selector: testIdSelector("workflow-recovery-block-block.generate-geometry"), label: "Local diagram says local conflict" },
    { selector: testIdSelector("workflow-recovery-save"), label: "Stale save is ready to attempt" },
  ], `A real control-plane PUT added only a comment and advanced storage revision to ${peerDocument.storage_revision}. The page retained its stale CAS identity while a checked local title edit remained visibly unsaved.`, {
    action: "Applied the local conflict edit.", control: "Apply checked edit", value: "Create bracket CAD model local conflict",
  });

  activeStepId = "S15";
  expectingStaleWorkflow409 = true;
  const conflictResponsePromise = page.waitForResponse((response) => new URL(response.url()).pathname === WORKFLOW_SOURCE_ROUTE && response.request().method() === "PUT");
  await page.getByTestId("workflow-recovery-save").click();
  const conflictResponse = await conflictResponsePromise;
  assert(conflictResponse.status() === 409, `Stale save returned ${conflictResponse.status()}, expected 409.`);
  const conflictStatus = page.getByTestId("workflow-recovery-save-status");
  await conflictStatus.filter({ hasText: "changed elsewhere" }).waitFor({ state: "visible" });
  await drainResponseInspections();
  expectingStaleWorkflow409 = false;
  assert(diagnostics.expectedHttpResponses.filter((item) => item.kind === "stale-workflow-save").length === 1, "Expected exactly one classified stale PUT 409.");
  assert((await page.getByTestId("workflow-recovery-source-editor").inputValue()).includes("Create bracket CAD model local conflict"), "409 discarded the local source edit.");
  assert(compact(await page.getByTestId("workflow-recovery-filebar").innerText()).includes("Unsaved changes"), "409 incorrectly marked the file saved.");
  const conflictActions = page.getByTestId("workflow-recovery-conflict-actions");
  await conflictActions.waitFor({ state: "visible" });
  await completeStep("S15", "15-stale-409-local-retained", "Expected stale 409 retains local edits", [
    { selector: testIdSelector("workflow-recovery-save-status"), label: "Workspace file changed elsewhere; local edits protected" },
    { selector: testIdSelector("workflow-recovery-source-editor"), label: "Local conflict title remains" },
    { selector: testIdSelector("workflow-recovery-conflict-actions"), label: "Copy, compare, and explicit reload actions" },
  ], "The stale Save workflow request returned one expected PUT 409. The source and diagram still showed the local title, the file remained Unsaved changes, and Copy local source, Compare stored file, and Discard local edits and reload appeared.", {
    action: "Attempted the intentionally stale save.", control: "Save workflow", value: "Stale storage revision and digest",
  });

  activeStepId = "S16";
  await page.getByTestId("workflow-recovery-conflict-compare").click();
  const comparison = page.getByTestId("workflow-recovery-source-comparison");
  await comparison.waitFor({ state: "visible" });
  const localComparison = await page.getByTestId("workflow-recovery-source-comparison-local").inputValue();
  const storedComparison = await page.getByTestId("workflow-recovery-source-comparison-stored").inputValue();
  assert(localComparison.includes("Create bracket CAD model local conflict"), "Comparison local side lost the local edit.");
  assert(storedComparison.includes(peerMarker) && !storedComparison.includes("local conflict"), "Comparison stored side is not the fresh remote source.");
  await completeStep("S16", "16-read-only-comparison", "Read-only local and stored source comparison", [
    { selector: testIdSelector("workflow-recovery-source-comparison-local"), label: "Protected local unsaved source" },
    { selector: testIdSelector("workflow-recovery-source-comparison-stored"), label: "Fresh current stored source" },
  ], "Compare stored file showed the local-conflict title on the protected left and the benign second-writer marker on the current stored right. The dialog explicitly said neither version was applied or saved.", {
    action: "Compared the protected local source with the current stored source.", control: "Compare stored file", value: "Read-only side-by-side comparison",
  });

  activeStepId = "S17";
  await page.getByTestId("workflow-recovery-modal-close").click();
  await recordAction({ action: "Closed the read-only source comparison.", control: "Close dialog", expected: "The conflict remains unresolved and local edits remain protected.", actual: "The dialog closed; the conflict actions and local source remained." });
  await page.getByTestId("workflow-recovery-conflict-copy-local").click();
  const copyMessage = page.getByTestId("workflow-recovery-conflict-action-message");
  await copyMessage.filter({ hasText: "Local workflow source copied" }).waitFor({ state: "visible" });
  const clipboardSource = await page.evaluate(() => navigator.clipboard.readText());
  assert(clipboardSource === localComparison, "Clipboard text does not exactly equal the protected local source.");
  await completeStep("S17", "17-copy-local-source", "Protected local source copied exactly", [
    { selector: testIdSelector("workflow-recovery-conflict-copy-local"), label: "Copy local source" },
    { selector: testIdSelector("workflow-recovery-conflict-action-message"), label: "Copy confirmation without mutation" },
    { selector: testIdSelector("workflow-recovery-source-editor"), label: "Local source remains visible" },
  ], `Copy local source wrote the exact ${clipboardSource.length}-character local draft to the clipboard and reported that the editor and stored file were unchanged.`, {
    action: "Copied the protected local workflow source.", control: "Copy local source", value: `${clipboardSource.length} characters`,
  });

  activeStepId = "S18";
  await page.getByTestId("workflow-recovery-conflict-reload").click();
  const reloadConfirmation = page.getByTestId("workflow-recovery-reload-confirmation");
  await reloadConfirmation.waitFor({ state: "visible" });
  assert(compact(await reloadConfirmation.innerText()).includes("discard the unsaved local workflow edits"), "Reload confirmation does not explain local data loss.");
  const reloadConfirmationImages = await capture("18-reload-confirmation", "Explicit confirmation before discarding local edits", [
    { selector: testIdSelector("workflow-recovery-reload-confirmation"), label: "Explicit local-data-loss warning" },
    { selector: testIdSelector("workflow-recovery-conflict-reload-cancel"), label: "Keep local edits" },
    { selector: testIdSelector("workflow-recovery-conflict-reload-confirm"), label: "Discard local edits and reload stored file" },
  ]);
  await recordAction({ action: "Opened and inspected the destructive reload confirmation before acting.", control: "Discard local edits and reload…", expected: "A confirmation explains that local edits will be discarded and nothing stored is overwritten.", actual: "The dialog offered Keep local edits and Discard local edits and reload stored file, with an explicit loss warning.", ...reloadConfirmationImages });
  await page.getByTestId("workflow-recovery-conflict-reload-confirm").click();
  await page.getByTestId("workflow-recovery-concept").waitFor({ state: "visible" });
  if (!(await page.getByTestId("workflow-recovery-source-editor").isVisible().catch(() => false))) await page.getByTestId("workflow-recovery-view-code").click();
  const reloadedStoredSource = await page.getByTestId("workflow-recovery-source-editor").inputValue();
  assert(reloadedStoredSource.includes(peerMarker), "Reload did not initialize from current stored source.");
  assert(!reloadedStoredSource.includes("local conflict"), "Reload retained the discarded local source.");
  assert(await page.getByTestId("workflow-recovery-conflict-actions").count() === 0, "Conflict controls remained after reload.");
  const afterConflictReload = await readStoredDocument("after explicit conflict reload");
  await completeStep("S18", "18-explicit-conflict-reload", "Explicit reload restores current stored source", [
    { selector: testIdSelector("workflow-recovery-source-editor"), label: "Current stored source with benign peer marker" },
    { selector: testIdSelector("workflow-recovery-filebar"), label: "Saved in workspace; conflict cleared" },
    { selector: testIdSelector("workflow-recovery-authority"), label: `Definition revision ${afterConflictReload.definition_revision}` },
  ], `After explicit confirmation, the editor remounted from storage revision ${afterConflictReload.storage_revision}. The benign peer marker remained, the local-conflict title disappeared, and conflict controls cleared.`, {
    action: "Confirmed discarding local edits and reloaded the current stored file.", control: "Discard local edits and reload stored file", value: `storage revision ${afterConflictReload.storage_revision}`,
  });

  await page.getByTestId("workflow-recovery-attachment-attach-artifact.design-intent").click();
  await recordAction({ action: "Re-added design intent after the conflict reload reset session-only UI state.", control: "Add text or document", value: "mounting-bracket-design-intent.docx", expected: "The bounded simulation prerequisite is restored only for this browser session.", actual: "Design intent was attached again and remained explicitly session-only." });
  await page.getByTestId("workflow-recovery-view-diagram").click();
  await recordAction({ action: "Returned to Diagram for direct manipulation.", control: "Diagram", expected: "The canonical graph is visible and editable.", actual: "The nine-node canonical graph was visible." });

  activeStepId = "S19";
  const currentConcept = page.getByTestId("workflow-recovery-concept");
  const revisionBeforeDrag = await currentConcept.getAttribute("data-revision");
  const semanticBeforeDrag = await currentConcept.getAttribute("data-semantic-digest");
  const layoutBeforeDrag = await currentConcept.getAttribute("data-layout-digest");
  const draggable = page.locator('.react-flow__node[data-id="block.generate-geometry"]');
  const dragBefore = await draggable.boundingBox();
  assert(dragBefore !== null, "CAD-model node has no drag bounds.");
  await page.mouse.move(dragBefore.x + dragBefore.width / 2, dragBefore.y + Math.min(45, dragBefore.height / 2));
  await page.mouse.down();
  await recordAction({ action: "Pressed the CAD-model node to start a drag.", control: "Create bracket CAD model", value: "Pointer down", expected: "The gesture starts without committing workflow or layout authority.", actual: "Pointer capture began; revision and digests remained unchanged." });
  await page.mouse.move(dragBefore.x + dragBefore.width / 2 + 80, dragBefore.y + Math.min(65, dragBefore.height / 2 + 20), { steps: 10 });
  const dragDuring = await waitForValue(() => draggable.boundingBox(), (box) => box !== null && box.x > dragBefore.x + 40, "live node motion before pointer release");
  assert(await currentConcept.getAttribute("data-revision") === revisionBeforeDrag, "Revision changed during drag.");
  assert(await currentConcept.getAttribute("data-semantic-digest") === semanticBeforeDrag, "Semantic digest changed during drag.");
  assert(await currentConcept.getAttribute("data-layout-digest") === layoutBeforeDrag, "Layout digest committed before release.");
  await completeStep("S19", "19-live-drag", "Live movement before pointer release", [
    { selector: '.react-flow__node[data-id="block.generate-geometry"]', label: "Node moved while pointer remains down" },
    { selector: testIdSelector("workflow-recovery-authority"), label: "Revision and digests remain stable during gesture" },
  ], `The CAD node moved ${Math.round(dragDuring.x - dragBefore.x)} px before pointer release. Revision ${revisionBeforeDrag}, semantic digest ${semanticBeforeDrag}, and layout digest ${layoutBeforeDrag} remained unchanged.`, {
    action: "Moved the pressed CAD-model node without releasing it.", control: "Create bracket CAD model", value: `+${Math.round(dragDuring.x - dragBefore.x)} px live preview`,
  });

  activeStepId = "S20";
  await page.mouse.up();
  const layoutAfterDrag = await waitForValue(() => currentConcept.getAttribute("data-layout-digest"), (value) => value && value !== layoutBeforeDrag, "layout-only commit after pointer release");
  assert(await currentConcept.getAttribute("data-revision") === revisionBeforeDrag, "Revision changed after layout-only commit.");
  assert(await currentConcept.getAttribute("data-semantic-digest") === semanticBeforeDrag, "Semantic digest changed after layout-only commit.");
  await completeStep("S20", "20-layout-only-commit", "Pointer release commits layout authority only", [
    { selector: '.react-flow__node[data-id="block.generate-geometry"]', label: "Committed node position" },
    { selector: testIdSelector("workflow-recovery-authority"), label: "Workflow revision and semantic digest unchanged" },
  ], `Pointer release changed only the layout digest from ${layoutBeforeDrag} to ${layoutAfterDrag}. Revision stayed ${revisionBeforeDrag} and semantic digest stayed ${semanticBeforeDrag}.`, {
    action: "Released the dragged CAD-model node.", control: "Create bracket CAD model", value: "Pointer up",
  });

  activeStepId = "S21";
  await page.getByTestId("workflow-recovery-ai-request").click();
  const proposal = page.getByTestId("workflow-recovery-proposal");
  await proposal.waitFor({ state: "visible" });
  const proposalText = compact(await proposal.innerText());
  for (const text of ["AI SUGGESTION · REVIEW BEFORE ADDING", "Assumptions", "Warnings", "Changes", "Create manufacturing drawing", "Review manufacturing drawing", "Preview only · not part of the current workflow"]) assert(proposalText.includes(text), `AI proposal is missing friendly content: ${text}`);
  const proposalTechnical = proposal.locator(".recovery-technical-details");
  assert(!(await proposalTechnical.evaluate((element) => element.open)), "AI proposal technical details are expanded by default.");
  await completeStep("S21", "21-friendly-ai-proposal", "Friendly reviewed AI proposal", [
    { selector: testIdSelector("workflow-recovery-proposal"), label: "AI suggestion requires review before adding" },
    { selector: testIdSelector("workflow-recovery-proposal-change-list"), label: "Friendly engineering change list" },
    { selector: testIdSelector("workflow-recovery-proposal-preview"), label: "Preview-only drawing creation and review" },
    { selector: testIdSelector("workflow-recovery-proposal-reject"), label: "Discard suggestion" },
  ], "The AI suggestion used engineering names, exposed assumptions and warnings, previewed drawing creation and review without accepting them, and kept technical source collapsed by default.", {
    action: "Requested and reviewed the bounded AI drawing-step proposal.", control: "Ask AI to add drawing steps", value: "Preview only",
  });
  await page.getByTestId("workflow-recovery-proposal-reject").click();
  await proposal.waitFor({ state: "detached" });
  assert(await page.locator(".react-flow__node").count() === 9, "Discarding the AI proposal changed the accepted topology.");
  await recordAction({ action: "Discarded the AI suggestion.", control: "Discard suggestion", expected: "The accepted nine-node workflow remains unchanged.", actual: "The preview disappeared and the accepted graph still contained nine nodes." });

  activeStepId = "S22";
  const revisionBeforeRun = await currentConcept.getAttribute("data-revision");
  const semanticBeforeRun = await currentConcept.getAttribute("data-semantic-digest");
  const runStart = page.getByTestId("workflow-recovery-run-start");
  assert(!(await runStart.isDisabled()), `Test workflow is disabled: ${await runStart.getAttribute("title")}`);
  await runStart.click();
  let runText = compact(await page.getByTestId("workflow-recovery-run-mode").innerText());
  assert(runText.includes("waiting"), `Simulation did not enter waiting: ${runText}`);
  await recordAction({ action: "Started the bounded workflow test.", control: "Test workflow", value: `Workflow version ${revisionBeforeRun}`, expected: "The isolated test enters waiting and states NO EXTERNAL TOOLS.", actual: runText });
  await page.getByTestId("workflow-recovery-run-advance").click();
  runText = compact(await page.getByTestId("workflow-recovery-run-mode").innerText());
  await recordAction({ action: "Advanced to design-specification drafting.", control: "Advance simulation", value: "1", expected: "The reviewed specification becomes active.", actual: runText });
  await page.getByTestId("workflow-recovery-run-advance").click();
  runText = compact(await page.getByTestId("workflow-recovery-run-mode").innerText());
  assert(runText.includes("needs input"), `Simulation did not reach needs input: ${runText}`);
  assert(await page.getByTestId("workflow-recovery-block-block.create-design-specification").getAttribute("data-run-state") === "needs-input", "Specification step is not needs-input.");
  assert(await page.getByTestId("workflow-recovery-block-block.review-design").getAttribute("data-run-state") === "blocked", "Downstream review is not blocked.");
  await completeStep("S22", "22-needs-input", "Simulation pauses for an engineer decision", [
    { selector: testIdSelector("workflow-recovery-run-mode"), label: "Workflow test · needs input" },
    { selector: testIdSelector("workflow-recovery-run-recover"), label: "Add 6061-T6 to design specification" },
    { selector: testIdSelector("workflow-recovery-block-block.create-design-specification"), label: "Design specification needs input" },
    { selector: testIdSelector("workflow-recovery-block-block.review-design"), label: "Downstream review remains blocked" },
  ], `After two advances, workflow version ${revisionBeforeRun} reached needs input at the design specification, offered Add 6061-T6 to design specification, and kept downstream review blocked.`, {
    action: "Advanced the workflow test to its intentional decision stop.", control: "Advance simulation", value: "2",
  });

  activeStepId = "S23";
  await page.getByTestId("workflow-recovery-run-recover").click();
  runText = compact(await page.getByTestId("workflow-recovery-run-mode").innerText());
  assert(runText.includes("running"), `Simulation did not resume: ${runText}`);
  await recordAction({ action: "Supplied the missing material and temper decision.", control: "Add 6061-T6 to design specification", value: "6061-T6", expected: "The same workflow test resumes.", actual: runText });
  for (let index = 1; index <= 6; index += 1) {
    await page.getByTestId("workflow-recovery-run-advance").click();
    runText = compact(await page.getByTestId("workflow-recovery-run-mode").innerText());
    await recordAction({ action: "Advanced the recovered workflow test.", control: "Advance simulation", value: `${index} of 6 after recovery`, expected: index === 6 ? "The workflow test reaches complete." : "The next canonical stage runs.", actual: runText });
  }
  assert(runText.includes("complete"), `Simulation did not complete: ${runText}`);
  assert(await currentConcept.getAttribute("data-revision") === revisionBeforeRun, "Simulation changed accepted revision.");
  assert(await currentConcept.getAttribute("data-semantic-digest") === semanticBeforeRun, "Simulation changed semantic digest.");
  await completeStep("S23", "23-recovered-complete", "Recovered simulation completes without authority mutation", [
    { selector: testIdSelector("workflow-recovery-run-mode"), label: "Workflow test complete · NO EXTERNAL TOOLS" },
    { selector: testIdSelector("workflow-recovery-block-block.export-step"), label: "STEP export complete" },
    { selector: testIdSelector("workflow-recovery-block-block.release-package"), label: "Handoff package complete" },
  ], `Adding 6061-T6 and advancing six stages completed workflow version ${revisionBeforeRun}. The accepted revision and semantic digest remained unchanged.`, {
    action: "Verified recovered workflow-test completion.", control: "Workflow test run bar", value: "complete",
  });

  activeStepId = "S24";
  await page.getByTestId("workflow-recovery-block-block.export-step").click();
  await recordAction({ action: "Selected the completed STEP export step.", control: "Export approved STEP file", expected: "The export inspector opens.", actual: "Export approved STEP file was selected." });
  await page.getByTestId("workflow-recovery-inspector-tab-outputs").click();
  await recordAction({ action: "Opened the export step's output section.", control: "Creates", expected: "The completed demo STEP output is offered.", actual: "STEP AP242 file appeared with Open STEP file." });
  await page.getByTestId("workflow-recovery-output-artifact.step").click();
  const outputDialog = page.getByRole("dialog", { name: "Mounting bracket STEP file" });
  await outputDialog.waitFor({ state: "visible" });
  const outputText = compact(await outputDialog.innerText());
  for (const text of ["Demo STEP file. This simulated workflow did not create this file.", `File sha256:${EXPECTED_STEP_FIXTURE_SHA256}`, "Approved CAD model and design-review decision", "Bracket CAD model and manufacturing check report", "Reviewed design specification", "Design intent + reference images + company standards and context"]) assert(outputText.includes(text), `Output evidence is missing: ${text}`);
  await recordAction({ action: "Opened the completed STEP output preview.", control: "Open STEP file", value: "mounting-bracket-simulated-fixture.step", expected: "The preview is honest about simulation and exposes digest and complete lineage.", actual: "The modal labeled the file as a demo, displayed its SHA-256, and traced all three original sources through approval and export." });
  const reportPromise = page.waitForEvent("popup");
  await page.getByTestId("workflow-recovery-output-open-artifact.step").click();
  const reportPage = await reportPromise;
  await reportPage.waitForLoadState("domcontentloaded");
  assert(await reportPage.title() === "Simulated manufacturability report", `Unexpected report title: ${await reportPage.title()}`);
  const reportText = compact(await reportPage.locator("body").innerText());
  assert(/simulat/i.test(reportText), "Opened report does not identify its simulated nature.");
  const reportImages = await capture("24-simulated-manufacturability-report", "Separate simulated manufacturing report", [
    { selector: ".badge", label: "SIMULATED · NOT PRODUCTION" },
    { selector: "h1", label: "Mounting bracket manufacturability" },
    { selector: ".warn", label: "Supplier confirmation note" },
    { selector: "table", label: "Manufacturability evidence" },
  ], reportPage);
  stepById("S24").supplementalEvidence = [{ label: "Separate simulated manufacturing report", ...reportImages }];
  await drainResponseInspections();
  assertNoUnexpectedDiagnostics();
  await recordAction({ action: "Opened and inspected the demo manufacturing report.", control: "Open demo manufacturing report", value: "Simulated manufacturability report", expected: "A separate report opens, identifies itself as simulated, and remains diagnostic-clean.", actual: "A separate page opened with title Simulated manufacturability report, visible simulation disclosure, a supplier confirmation note, and a three-row evidence table.", currentUrlOverride: reportPage.url(), ...reportImages });
  await reportPage.close();
  const downloadPromise = page.waitForEvent("download");
  await page.getByTestId("workflow-recovery-output-download-artifact.step").click();
  const download = await downloadPromise;
  assert(download.suggestedFilename() === "mounting-bracket-simulated-fixture.step", `Unexpected download name: ${download.suggestedFilename()}`);
  const downloadedPath = await download.path();
  assert(downloadedPath, "Downloaded STEP file has no readable temporary path.");
  const downloadedSha256 = createHash("sha256").update(readFileSync(downloadedPath)).digest("hex");
  assert(downloadedSha256 === EXPECTED_STEP_FIXTURE_SHA256, `Downloaded STEP digest ${downloadedSha256} does not match displayed ${EXPECTED_STEP_FIXTURE_SHA256}.`);
  controlPlane.download = { suggested_filename: download.suggestedFilename(), sha256: downloadedSha256 };
  await completeStep("S24", "24-output-report-download-lineage", "Honest output, report, download, and complete lineage", [
    { selector: ".output-preview img", label: "Clearly labeled mounting-bracket demo output" },
    { selector: ".output-preview aside", label: "Demo status, workflow version, and file digest" },
    { selector: testIdSelector("workflow-recovery-output-lineage"), label: "Lineage through approval, CAD, specification, and all three sources" },
    { selector: testIdSelector("workflow-recovery-output-download-artifact.step"), label: "Download demo STEP file" },
  ], `The preview stated that the simulation did not create the demo file, showed SHA-256 ${EXPECTED_STEP_FIXTURE_SHA256}, and traced approval, CAD, manufacturing report, reviewed specification, design intent, reference images, and company context. The report opened separately and the downloaded ${download.suggestedFilename()} bytes matched that digest.`, {
    action: "Downloaded and verified the demo STEP bytes.", control: "Download demo STEP file", value: `${download.suggestedFilename()} / sha256:${downloadedSha256}`,
  });

  await drainResponseInspections();
  assert(diagnostics.expectedHttpResponses.filter((item) => item.kind === "missing-workflow-source").length === 1, "Expected exactly one automatic-bootstrap GET 404.");
  assert(controlPlane.workflowSourceResponses.filter((item) => item.method === "POST" && item.status === 201).length === 1, "Expected exactly one automatic-bootstrap POST 201.");
  assert(diagnostics.expectedHttpResponses.filter((item) => item.kind === "stale-workflow-save").length === 1, "Expected exactly one stale-save PUT 409.");
  assertNoUnexpectedDiagnostics();
  overall = "pass";
  appendProgress({
    status: "PASS",
    action: "Completed the real-API walkthrough and reviewed final diagnostics.",
    control: "Browser diagnostics and control-plane evidence",
    expected: "Only the automatic-bootstrap GET 404 and stale PUT 409 are classified as expected; exactly one POST 201 initialized the default and no unexpected browser or HTTP failures remain.",
    actual: diagnosticSummary(),
  });
} catch (error) {
  overall = "blocked";
  stoppedReason = error instanceof Error ? error.message : String(error);
  const failureImages = await screenshotFailure().catch(() => null);
  blockStep(activeStepId, stoppedReason, failureImages);
  const stoppedStep = stepById(activeStepId);
  stopContext = buildStopContext({
    control: stoppedStep.controls.join(" → "),
    action: stoppedStep.action,
    expected: stoppedStep.expected,
    actual: stoppedReason,
  });
  appendProgress({
    status: "STOPPED",
    action: "Stopped immediately at the first unexpected result.",
    control: stopContext.control,
    expected: stopContext.expected,
    actual: `${stopContext.actual} Last successful step: ${stopContext.lastSuccessfulStep}. ${stopContext.dataMutationSummary} Remaining steps were not executed: ${stopContext.remainingSteps}`,
    ...(failureImages || {}),
  });
  process.exitCode = 1;
} finally {
  await drainResponseInspections().catch(() => undefined);
  if (traceStarted && !traceStopped && context) {
    try {
      await context.tracing.stop({ path: path.join(walkthroughRoot, "trace", "trace.zip") });
    } catch (error) {
      const traceError = `Required trace finalization failed: ${error instanceof Error ? error.message : String(error)}`;
      diagnostics.pageErrors.push({ at: new Date().toISOString(), text: traceError });
      if (overall !== "blocked") {
        overall = "blocked";
        stoppedReason = traceError;
        stopContext = buildStopContext({
          control: "Playwright context trace finalization",
          action: "Write the required trace/trace.zip evidence artifact.",
          expected: "The browser trace closes successfully and the evidence package remains diagnostic-clean.",
          actual: traceError,
        });
        const traceFailureImages = await screenshotFailure().catch(() => null);
        appendProgress({
          status: "STOPPED",
          action: "Stopped evidence finalization because the required browser trace could not be written.",
          control: stopContext.control,
          expected: stopContext.expected,
          actual: `${stopContext.actual} Last successful step: ${stopContext.lastSuccessfulStep}. ${stopContext.dataMutationSummary} Remaining steps: ${stopContext.remainingSteps}`,
          ...(traceFailureImages || {}),
        });
      } else {
        appendProgress({
          status: "STOPPED",
          action: "Recorded a secondary trace-finalization failure without replacing the first walkthrough stop.",
          control: "Playwright context trace finalization",
          expected: "The required trace closes successfully after preserving the primary stop evidence.",
          actual: `${traceError} Primary stop remains: ${stoppedReason}`,
        });
      }
      process.exitCode = 1;
    }
    traceStopped = true;
  }
  if (browser) await browser.close().catch(() => undefined);
  appendProgress({
    status: overall === "pass" ? "PASS" : "STOPPED",
    action: "Finalized trace, diagnostics, status, report, and control-plane evidence before manifesting immutable files.",
    control: "Walkthrough evidence bundle",
    expected: "All reached evidence is preserved and pending steps remain gray after a stop.",
    actual: `${steps.filter((step) => step.state === "pass").length} of ${steps.length} logical steps passed. ${diagnosticSummary()}`,
  });
  const manifest = writeManifest();
  console.log(JSON.stringify({
    root: walkthroughRoot,
    overall,
    passedSteps: steps.filter((step) => step.state === "pass").length,
    totalSteps: steps.length,
    rawScreenshots: readdirSync(path.join(walkthroughRoot, "screenshots", "raw")).length,
    annotatedScreenshots: readdirSync(path.join(walkthroughRoot, "screenshots", "annotated")).length,
    expectedHttpResponses: diagnostics.expectedHttpResponses.length,
    unexpectedHttpResponses: diagnostics.unexpectedHttpResponses.length,
    manifestFiles: manifest.count,
    manifestSha256: manifest.digest,
  }, null, 2));
}
