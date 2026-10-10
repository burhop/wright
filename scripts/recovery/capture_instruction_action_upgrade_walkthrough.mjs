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
const taskBrowserTemp = path.resolve(path.dirname(workspace.local_path), 'playwright-temp');
mkdirSync(taskBrowserTemp, { recursive: true });
process.env.TEMP = taskBrowserTemp; process.env.TMP = taskBrowserTemp;
const runLabel =
  "instruction-action-upgrade-" +
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
    "Saved instruction updates, legacy migration, copies and concurrent edits",
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

let accepted, activePath;
const currentSource = async () => { await ui.getByTestId('workflow-recovery-view-code').click(); return ui.getByTestId('workflow-recovery-source-editor').inputValue(); };
const save = async () => {
 const pending=page.waitForResponse(r=>r.request().method()==='PUT'&&new URL(r.url()).pathname==='/api/workspace/workflow-sources');
 await ui.getByTestId('workflow-recovery-save').click(); const result=await pending;
 if(!result.ok())throw Error('Save rejected HTTP '+result.status());return result.json();
};
try {
 await step('01-create','Create an isolated upgrade example','Open Workflows, Workflow files, New workflow; give the workflow its distinct test name.','A fresh blank definition is created through ordinary Wright authoring.',async()=>{
  await page.goto(workspace.url);await ui.getByTestId('activity-bar-workflows-btn').click();await ui.getByTestId('workflow-file-menu').click();await ui.getByTestId('workflow-file-new').click();await ui.getByLabel('Workflow name').fill(runLabel);await ui.getByTestId('workflow-file-create').click();await page.getByRole('heading',{name:runLabel,exact:true}).waitFor();activePath=new URL(page.url()).searchParams.get('workflowPath');
 });
 await step('02-legacy','Save a distinct legacy profile with custom guidance','In Source, remove only the action intent metadata/helper from this test profile. Apply source. In Instructions add Test custom policy guidance, Apply and Save.','The accepted legacy profile has custom task guidance; no other workflow or global default changes.',async()=>{
  let source=await currentSource();const profile=JSON.parse(source.match(/^  instructions: (.+)$/m)[1]);delete profile.action_intent_contract;profile.assets=profile.assets.filter(a=>a.id!=='protocol.action-intent');profile.bindings=profile.bindings.map(b=>({...b,asset_ids:b.asset_ids.filter(id=>id!=='protocol.action-intent')})).filter(b=>b.asset_ids.length);
  source=source.replace(/^  instructions: .+$/m,'  instructions: '+JSON.stringify(profile));await ui.getByTestId('workflow-recovery-source-editor').fill(source);await ui.getByTestId('workflow-recovery-source-apply').click();await ui.getByTestId('workflow-recovery-instructions').click();await ui.getByTestId('workflow-instructions-guidance').fill('Test custom policy guidance: preserve supplied plate dimensions.');await ui.getByTestId('workflow-instructions-apply').click();await page.getByText('Instructions applied to the draft.',{exact:false}).waitFor();await ui.getByTestId('workflow-recovery-modal-close').click();accepted=await save();
  writeFileSync(path.join(artifactRoot,'legacy-source.json'),JSON.stringify(accepted,null,2));
 });
 await step('03-proposal','Review protocol upgrade without changing the source','Open Instructions and click Review instruction compatibility upgrade. Inspect current/proposed collections and the action contract change.','Only a proposal is shown. The accepted source remains at its previous revision and customized guidance is present.',async()=>{
  await ui.getByTestId('workflow-recovery-instructions').click();await ui.getByTestId('workflow-instructions-review-action-upgrade').click();await ui.getByTestId('workflow-instructions-action-intent-diff').waitFor();const proposed=await ui.getByTestId('workflow-instructions-proposed-collection').inputValue();if(!proposed.includes('wright.workflow-action-intent/1')||!proposed.includes('Test custom policy guidance'))throw Error('Protocol proposal lost marker or custom guidance');
  if(!(await ui.getByTestId('workflow-instructions-action-intent').innerText()).includes('Not declared'))throw Error('Proposal changed the draft before approval');
  const r=await context.request.get(base+'/api/workspace/workflow-sources?'+new URLSearchParams({session_id:workspace.session_id,path:activePath}));if(!r.ok())throw Error('Saved subject inspection failed');const stored=await r.json();if(stored.storage_digest!==accepted.storage_digest)throw Error('Proposal mutated saved source');await ui.getByTestId('workflow-instructions-action-intent-diff').scrollIntoViewIfNeeded();
 });
 await step('04-apply','Apply and save the reviewed upgrade','Click Apply reviewed instruction update, close Instructions and Save.','A new accepted revision carries the protocol marker and custom instruction text.',async()=>{
  await ui.getByTestId('workflow-instructions-apply-update').click();await page.getByText('Instructions applied to the draft.',{exact:false}).waitFor();await ui.getByTestId('workflow-recovery-modal-close').click();const updated=await save();if(updated.storage_digest===accepted.storage_digest)throw Error('No accepted upgrade revision');const profile=JSON.parse(updated.source.match(/^  instructions: (.+)$/m)[1]);if(profile.action_intent_contract!=='wright.workflow-action-intent/1'||!updated.source.includes('Test custom policy guidance'))throw Error('Saved upgrade lost marker or custom guidance');writeFileSync(path.join(artifactRoot,'upgraded-source.json'),JSON.stringify(updated,null,2));accepted=updated;
 });
 await step('05-reload','Reload and inspect the saved profile','Reload the accepted source URL, open Instructions and inspect its saved action contract.','The upgraded contract survives source roundtrip and reload; no process has run.',async()=>{
  await page.reload();await ui.getByTestId('workflow-recovery-instructions').click();await ui.getByTestId('workflow-instructions-action-intent').waitFor();if(!(await ui.getByTestId('workflow-instructions-action-intent').innerText()).includes('wright.workflow-action-intent/1'))throw Error('Saved contract not shown');if((await ui.getByTestId('workflow-instructions-guidance').inputValue())!=='Test custom policy guidance: preserve supplied plate dimensions.')throw Error('Guidance not retained');
 });
 status.overall='pass';status.summary='Read-only proposal, visible action contract diff, explicit reviewed apply and accepted revision reload verified in the ordinary workspace. Custom task guidance retained; no execution or global mutation.';report();
} catch(error){process.exitCode=2;console.log(JSON.stringify({status:'stopped',reason:String(error.message).slice(0,1000),report:path.join(artifactRoot,'report.html')}));}
finally {writeFileSync(path.join(artifactRoot,'playwright/diagnostics.json'),JSON.stringify(diagnostics,null,2));await context.tracing.stop({path:path.join(artifactRoot,'trace/trace.zip')});await browser.close();report();}
