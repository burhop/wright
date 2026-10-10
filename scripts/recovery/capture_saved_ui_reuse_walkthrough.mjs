import { chromium } from "@playwright/test";
import {
  mkdirSync,
  readFileSync,
  writeFileSync,
  appendFileSync,
} from "node:fs";
import path from "node:path";
const artifactRoot = path.resolve(process.argv[2]);
const privateContext = JSON.parse(readFileSync(process.argv[3], "utf8"));
const workspace = JSON.parse(readFileSync(process.argv[4], "utf8"))[0];
const runLabel =
  "instruction-revisions-" +
  new Date().toISOString().replace(/\D/g, "").slice(0, 14);
for (const dir of [
  "playwright",
  "screenshots/raw",
  "screenshots/annotated",
  "trace",
])
  mkdirSync(path.join(artifactRoot, dir), { recursive: true });
writeFileSync(
  path.join(artifactRoot, "playwright/capture.mjs"),
  readFileSync(import.meta.filename),
);
const status = {
  title:
    "Saved working interface reuse without regeneration",
  summary:
    "Approved isolated UI proof in progress; no process execution or external action is submitted.",
  overall: "pending",
  updated: new Date().toISOString(),
  manualSteps: [],
  steps: [],
};
const diagnostics = [];
writeFileSync(
  path.join(artifactRoot, "progress.md"),
  "# Instruction authoring and workflow transfer\n\nStarted " +
    status.updated +
    " UTC. Isolated workspace. No existing run is resumed or approved. Original workspace is read-only except ephemeral presentations.\n",
);
const esc = (value) =>
  String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll('"', "&quot;");
function report() {
  status.updated = new Date().toISOString();
  writeFileSync(
    path.join(artifactRoot, "status.json"),
    JSON.stringify(status, null, 2),
  );
  writeFileSync(
    path.join(artifactRoot, "report.html"),
    '<!doctype html><meta charset="utf-8"><title>Wright authoring and transfer</title><style>body{font:16px system-ui;max-width:1100px;margin:30px auto;background:#101624;color:#eee}article{padding:18px;border:1px solid #556;margin:12px 0}.pass{border-color:#5c9}.blocked{border-color:#e65}img{max-width:95%}a{color:#6de}</style><h1>' +
      esc(status.title) +
      "</h1><p>" +
      esc(status.summary) +
      "</p><h2>Manual repeat</h2><ol>" +
      status.manualSteps
        .map((s) => "<li>" + esc(s.instruction) + "</li>")
        .join("") +
      "</ol>" +
      status.steps
        .map(
          (s) =>
            '<article class="' +
            s.state +
            '"><h2>' +
            esc(s.label + " — " + s.state) +
            "</h2><p>Purpose: " +
            esc(s.purpose) +
            "</p><p>Action: " +
            esc(s.action) +
            "</p><p>Expected: " +
            esc(s.expected) +
            "</p><p>Observed: " +
            esc(s.actual) +
            "</p>" +
            [s.raw, s.annotated]
              .filter(Boolean)
              .map(
                (p) =>
                  '<a href="' +
                  p +
                  '" target="_blank"><img src="' +
                  p +
                  '"></a>',
              )
              .join("") +
            "</article>",
        )
        .join(""),
  );
}
report();
let browser;
try {
  browser = await chromium.launch({ headless: true });
} catch (error) {
  status.overall = "blocked";
  status.summary = "Browser could not start; no UI action was performed.";
  status.steps.push({
    id: "00-browser",
    state: "blocked",
    label: "Start browser",
    summary: status.summary,
    purpose: "Begin isolated walkthrough.",
    action: "Start installed test browser.",
    controls: [],
    expected: "Browser starts.",
    actual: String(error.message).slice(0, 2000),
  });
  appendFileSync(
    path.join(artifactRoot, "progress.md"),
    "\nBrowser launch blocked. No workspace changes.\n" + error.message,
  );
  report();
  throw error;
}
const context = await browser.newContext({
  viewport: { width: 1350, height: 1000 },
  acceptDownloads: true,
});
const base = new URL(workspace.url).origin;
const auth = await context.request.post(base + "/api/auth/session", {
  data: { token: privateContext.api_token },
});
if (auth.status() !== 204)
  throw Error("Browser session unavailable: HTTP " + auth.status());
await context.tracing.start({ screenshots: true, snapshots: true });
const page = await context.newPage();
const ui = {
  getByTestId: (id) => page.getByTestId(id).filter({ visible: true }),
  getByLabel: (...args) => page.getByLabel(...args).filter({ visible: true }),
};
page.on("pageerror", (e) =>
  diagnostics.push({ kind: "pageerror", message: e.message }),
);
page.on("console", (e) => {
  if (e.type() === "error")
    diagnostics.push({ kind: "console", message: e.text().slice(0, 1000) });
});
page.on("response", (r) => {
  if (r.status() >= 400)
    diagnostics.push({ kind: "http", status: r.status(), url: r.url() });
});
async function capture(id) {
  const raw = "screenshots/raw/" + id + ".png",
    annotated = "screenshots/annotated/" + id + ".png";
  await page.screenshot({ path: path.join(artifactRoot, raw) });
  await page.evaluate(() => {
    const holder = document.createElement("aside");
    holder.id = "walkthrough-overlays";
    holder.style.cssText =
      "position:fixed;bottom:8px;right:8px;z-index:2147483647;padding:10px;max-width:650px;background:#fff;color:#111;font:12px sans-serif";
    const selectors = [
      '[data-testid="activity-bar-workflows-btn"]',
      '[data-testid="workflow-recovery-create-group-input"]',
      '[data-testid="workflow-recovery-create-template-human-input"]',
      '[data-testid="workflow-human-input-instructions"]',
      '[data-testid="workflow-human-input-apply"]',
      '[data-testid="workflow-step-instructions-toggle"]',
      '[data-testid="workflow-step-instructions-policy"]',
      '[data-testid="workflow-step-instructions-apply"]',
      '[data-testid="workflow-recovery-save"]',
      '[data-testid="workflow-transfer-open"]',
      '[data-testid="workflow-transfer-export"]',
      '[data-testid="workflow-transfer-upload"]',
      '[data-testid="workflow-transfer-inspect"]',
      '[data-testid="workflow-transfer-import"]',
    ];
    const labels = [];
    for (const [index, selector] of selectors.entries()) {
      const el = document.querySelector(selector);
      if (!el) continue;
      const box = el.getBoundingClientRect();
      if (!box.width || box.top < 0 || box.top > innerHeight) continue;
      const n = index + 1;
      labels.push(
        n +
          " " +
          (el.getAttribute("aria-label") ||
            el.textContent?.trim().slice(0, 65) ||
            selector),
      );
      const marker = document.createElement("span");
      marker.textContent = String(n);
      marker.style.cssText =
        "position:fixed;z-index:2147483647;background:#168be5;color:white;border:2px solid white;border-radius:20px;padding:3px;left:" +
        Math.min(innerWidth - 25, box.right) +
        "px;top:" +
        box.top +
        "px";
      holder.append(marker);
    }
    holder.append(document.createTextNode(labels.join(" · ")));
    document.body.append(holder);
  });
  await page.screenshot({ path: path.join(artifactRoot, annotated) });
  await page.evaluate(() =>
    document.getElementById("walkthrough-overlays")?.remove(),
  );
  return { raw, annotated };
}
async function step(id, label, action, expected, operation) {
  const row = {
    id,
    state: "pending",
    label,
    summary: label,
    purpose: expected,
    action,
    controls: [],
    expected,
    actual: "Not reached",
  };
  status.steps.push(row);
  status.manualSteps.push({ label, instruction: action });
  report();
  const start = diagnostics.length;
  try {
    if (id !== "01-entry") Object.assign(row, await capture(id + "-before"));
    await operation();
    Object.assign(row, await capture(id + "-after"));
    row.controls = await page
      .locator("button:visible,input:visible,select:visible,textarea:visible")
      .evaluateAll((es) =>
        es.map((e) => ({
          role: e.tagName.toLowerCase(),
          name:
            e.getAttribute("aria-label") ||
            e.getAttribute("title") ||
            e.textContent?.trim().slice(0, 100) ||
            "",
        })),
      );
    row.state = "pass";
    row.actual = "Expected state verified.";
  } catch (error) {
    row.state = "blocked";
    row.actual = String(error.message).slice(0, 3000);
    Object.assign(row, await capture(id + "-stopped"));
    status.overall = "blocked";
    status.summary =
      "Stopped at " +
      label +
      ". Earlier evidence retained; repair is authorized by the saved goal.";
    throw error;
  } finally {
    appendFileSync(
      path.join(artifactRoot, "progress.md"),
      "\n## " +
        new Date().toISOString() +
        " UTC — " +
        id +
        " " +
        label +
        "\nURL: " +
        page.url() +
        "\nAction: " +
        action +
        "\nExpected: " +
        expected +
        "\nActual: " +
        row.actual +
        "\nDiagnostics: " +
        JSON.stringify(diagnostics.slice(start)) +
        "\nRaw: " +
        row.raw +
        "\nAnnotated: " +
        row.annotated +
        "\nStatus: " +
        (row.state === "pass" ? "PASS" : "STOPPED") +
        "\n",
    );
    report();
  }
}

const saved = { workspace_id:'083-fresh-prompt-055', session_id:'083-printed-prompt-session-055', source_path:'workflows/printed-replacement-part-mixed-default-071.workflow.wflow', digest:'2ce1aa5f19a5f10a4f989828bdb11748ec922b5b952f87b36ece5d6bcdce6589', ui:'ui-f47e26fbcc2e44a2a7c4dc939aef1948', revision:'revision-b1d66dc13ace45889297568cd38c6ee0' };
const originalUrl = base+'/workspace/'+saved.workspace_id+'?workflow=canonical&workflowPath='+encodeURIComponent(saved.source_path);
const forbidden=[];
page.on('request', r=>{const p=new URL(r.url()).pathname; if(r.method()!=='GET' && (/authoring-jobs|\/start$|\/respond$|\/reviews|\/approve|workflow-sources$/.test(p))) forbidden.push({method:r.method(),path:p});});
try {
 await step('01-entry','Open saved process in ordinary workspace','Open the original accepted source URL in the copied database. Do not edit or run.','The original saved definition opens in the normal workspace and exposes its working view.',async()=>{
 await page.goto(originalUrl); await page.getByRole('button',{name:'Open working view',exact:true}).filter({visible:true}).click(); await page.getByRole('button',{name:'Create or choose interface',exact:true}).filter({visible:true}).waitFor();
 });
 await step('02-select','Choose the saved Wheel interface','Click Create or choose interface. Select Wheel evidence and its Current revision.','The existing accepted UI identity and exact built revision are offered without generation.',async()=>{
 await page.getByRole('button',{name:'Create or choose interface',exact:true}).filter({visible:true}).click();
 await ui.getByLabel('Saved interface',{exact:true}).selectOption(saved.ui);
 await ui.getByLabel('Saved revision',{exact:true}).selectOption(saved.revision);
 await page.getByRole('button',{name:'Open saved interface',exact:true}).filter({visible:true}).waitFor();
 });
 await step('03-open','Open existing compiled interface','Click Open saved interface.','A managed saved interface opens in a Wright workspace tab with no new authoring job or process run.',async()=>{
 await page.getByRole('button',{name:'Open saved interface',exact:true}).filter({visible:true}).click();
 await page.locator('iframe:visible').waitFor({timeout:30000});
 const frame=page.frameLocator('iframe:visible'); await frame.getByText('Wheel evidence',{exact:false}).first().waitFor({timeout:30000});
 const query=new URL(page.url()).searchParams;
 if(query.get('processUI')!==saved.ui || query.get('processUIRevision')!==saved.revision || query.has('processRun')) throw Error('Exact saved preparation locator missing');
 });
 await step('04-reload','Reload saved interface','Reload the current workspace tab and wait for the saved view.','The same exact compiled revision reconciles again; no generation, rebuild or process execution.',async()=>{
 await page.reload(); await page.locator('iframe:visible').waitFor({timeout:30000}); await page.frameLocator('iframe:visible').getByText('Wheel evidence',{exact:false}).first().waitFor({timeout:30000});
 if(forbidden.length) throw Error('Unexpected write '+JSON.stringify(forbidden));
 });
 status.overall='pass'; status.summary='Saved Wheel evidence interface opened and reloaded in the ordinary workspace using its existing compiled revision. No generation or process action submitted. Original source/revision/authoring receipts must be compared separately.';
} catch(error) {process.exitCode=2;console.log(JSON.stringify({status:'stopped',reason:error.message,report:path.join(artifactRoot,'report.html')}));}
finally { writeFileSync(path.join(artifactRoot,'playwright/diagnostics.json'),JSON.stringify(diagnostics,null,2));writeFileSync(path.join(artifactRoot,'forbidden-actions.json'),JSON.stringify(forbidden,null,2));await context.tracing.stop({path:path.join(artifactRoot,'trace/trace.zip')});await browser.close(); report();}
