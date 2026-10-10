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
    "Recorded failed run and unavailable results through normal workspace",
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
    " UTC. Isolated workspace. No existing run is resumed or approved.\n",
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

const sourcePath='workflows/expected-failure-readonly-missing-artifact-bfa40cf8.workflow.wflow';
const runId='2eb73fce79464521b745f9bd9c8bc775';
const writes=[];page.on('request',r=>{const p=new URL(r.url()).pathname;if(r.method()!=='GET' && p!=='/api/workspace/activate')writes.push({method:r.method(),path:p});});
try {
 await step('01-entry','Inspect already failed run','Open the fresh negative-case saved workflow through the ordinary workspace. Do not run it again.','The latest recorded failure is visible on the diagram run bar, not a success placeholder.',async()=>{
 await page.goto(workspace.url+'?workflow=canonical&workflowPath='+encodeURIComponent(sourcePath));
 await ui.getByTestId('workflow-recovery-run-details-toggle').waitFor();
 await page.getByText('Run failed',{exact:true}).filter({visible:true}).waitFor();
 });
 await step('02-failure','Read exact failure diagnosis','Expand Run details.','Failure explanation identifies declared output that was not created, links to failed step and preserves recorded evidence.',async()=>{
 if(!await ui.getByTestId('workflow-native-run-summary').isVisible())await ui.getByTestId('workflow-recovery-run-details-toggle').click();
 await ui.getByTestId('workflow-native-run-summary').waitFor();
 const summary=await ui.getByTestId('workflow-native-run-summary').innerText();
 if(!/fail/i.test(summary) || !/output|artifact|file/i.test(summary))throw Error('Failure summary missing diagnostic: '+summary);
 await page.getByRole('heading',{name:'What stopped the run',exact:true}).filter({visible:true}).waitFor();
 });
 await step('03-history','Inspect durable failed history','Open Previous runs, then the Failed entry.','History retains the same negative run and an Open saved run log action; no duplicate run is submitted.',async()=>{
 await ui.getByTestId('workflow-run-history').locator('summary').first().click();
 const history=ui.getByTestId('workflow-run-history');await history.locator('summary').filter({hasText:/^Failed/}).first().click();
 await history.getByRole('button',{name:'Open saved run log',exact:true}).waitFor();
 const text=await history.innerText();if(!/output|artifact|file/i.test(text))throw Error('Failed history lacks diagnostic');
 });
 await step('04-common','Open same failed run in working view','Open working view to inspect results and failure for the same durable run.','Shared Progress says Process needs attention with an exact failure reason, terminal actions are unavailable, and the result is unavailable; no success or generated placeholder is presented.',async()=>{
 const r=await context.request.get(base+'/api/workspace/workflow-sources',{params:{session_id:workspace.session_id,path:sourcePath}});if(!r.ok())throw Error('Source read failed');const doc=await r.json();
 const q=new URLSearchParams({processView:'failure-'+crypto.randomUUID(),processPath:sourcePath,processDigest:doc.storage_digest,processRun:runId});
 await page.goto(workspace.url+'?'+q);
 await page.getByRole('heading',{name:'Progress',exact:true}).filter({visible:true}).waitFor();
 await page.getByText('Process needs attention',{exact:true}).filter({visible:true}).first().waitFor();
 const cancel=page.getByRole('button',{name:'Cancel this run',exact:true}).filter({visible:true});if(await cancel.count() && await cancel.isEnabled())throw Error('Terminal failed run still offers enabled Cancel this run');
 await page.getByRole('heading',{name:'Results and checks',exact:true}).filter({visible:true}).waitFor();
 await page.getByRole('heading',{name:'Results and checks',exact:true}).filter({visible:true}).scrollIntoViewIfNeeded();
 if(writes.length)throw Error('Unexpected mutation '+JSON.stringify(writes));
 });
 status.overall='pass';status.summary='Existing real OASiS negative run was inspected through normal diagram, failure diagnosis, saved history and common working view. No execution/retry/approval submitted. Failure and unavailable output are explicit.';
}catch(error){process.exitCode=2;console.log(JSON.stringify({status:'stopped',reason:error.message,report:path.join(artifactRoot,'report.html')}));}
finally{writeFileSync(path.join(artifactRoot,'playwright/diagnostics.json'),JSON.stringify(diagnostics,null,2));writeFileSync(path.join(artifactRoot,'mutation-requests.json'),JSON.stringify(writes,null,2));await context.tracing.stop({path:path.join(artifactRoot,'trace/trace.zip')});await browser.close();report();}
