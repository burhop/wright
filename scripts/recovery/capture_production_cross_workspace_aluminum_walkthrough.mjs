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
const workspaces = JSON.parse(readFileSync(process.argv[4], "utf8"));
const sourceWorkspace = workspaces[0];
const workspace = workspaces[1];
const taskBrowserTemp = path.resolve(path.dirname(workspace.local_path), 'playwright-temp');
mkdirSync(taskBrowserTemp, { recursive: true });
process.env.TEMP = taskBrowserTemp; process.env.TMP = taskBrowserTemp;
const runLabel =
  "production-cross-aluminum-mass-" +
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
    "Production cross-workspace process reuse and frozen instructions",
  summary:
    "Approved isolated digital workflow proof in progress. Actual model calls are authorized; no physical action or engineering acceptance is submitted.",
  overall: "pending",
  updated: new Date().toISOString(),
  manualSteps: [],
  steps: [],
};
const diagnostics = [];
writeFileSync(
  path.join(artifactRoot, "progress.md"),
  "# Production workflow proof\n\nStarted " +
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

const previous=JSON.parse(readFileSync(process.argv[5],'utf8'));
let transferPath, accepted, receipt, activePath;
const starts=[];page.on('request',r=>{if(r.method()==='POST'&&new URL(r.url()).pathname==='/api/workspace/workflow-sources/run')starts.push(JSON.parse(r.postData()));});
const instructionCollection = source => {const line=source.split('\n').find(line=>/^\s*instructions: /.test(line));if(!line)throw Error('Embedded instructions missing');return JSON.parse(line.slice(line.indexOf(':')+1));};
const assertReaderSelected = async () => {const reader=page.getByRole('region',{name:'Selected representation',exact:true}).filter({visible:true});const box=await reader.boundingBox();if(!box||box.y< -2||box.y>(page.viewportSize()?.height??1000)/2)throw Error('Opened reader was not brought into view');if(!await reader.evaluate(element=>document.activeElement===element))throw Error('Opened reader did not receive focus');};
const save=async()=>{const pending=page.waitForResponse(r=>r.request().method()==='PUT'&&new URL(r.url()).pathname==='/api/workspace/workflow-sources');await ui.getByTestId('workflow-recovery-save').click();const r=await pending;if(!r.ok())throw Error('Save rejected HTTP '+r.status());return r.json();};
const readExactWaitingRun = async () => {
 const response=await context.request.get(base+'/api/workspace/workflow-sources/runs',{params:{session_id:workspace.session_id,path:activePath,latest_only:'true'}});if(!response.ok())throw Error('Run history read failed');const history=await response.json();const latest=history.runs?.[0];if(history.workflow_path!==activePath||latest?.status!=='waiting_human'||latest.source_digest!==accepted.storage_digest||!latest.run_id||!latest.path)throw Error('Latest durable wait does not match accepted source');const location=path.resolve(workspace.local_path,latest.path);if(!location.startsWith(path.resolve(workspace.local_path)+path.sep))throw Error('Run log outside isolated workspace');const record=JSON.parse(readFileSync(location,'utf8'));if(record.run_id!==latest.run_id||record.source_digest!==accepted.storage_digest)throw Error('Run log identity mismatch');return {...record.result,input_checkpoint:record.input_checkpoint??record.result.input_checkpoint,run_id:record.run_id,workspace_id:workspace.workspace_id,workflow_path:activePath,run_log_path:latest.path,source_digest:record.source_digest,status:record.status};
};
try {
 await step('01-reuse','Open the previous accepted mass process','Open the accepted first-input process from the prior production journey. Do not start it again.','The same saved process opens with its portable instruction profile.',async()=>{await page.goto(sourceWorkspace.url+'?workflow=canonical&workflowPath='+encodeURIComponent(previous.path));await ui.getByTestId('workflow-recovery-view-code').click();const text=await ui.getByTestId('workflow-recovery-source-editor').inputValue();if(!text.includes('instructions:'))throw Error('Saved profile unavailable');});
 await step('02-export','Export the accepted process for reuse','Open Export / import workflow; choose Bundle and download without selecting optional assets.','The accepted definition exports instructions and a dependency manifest, without copying run decisions.',async()=>{await ui.getByTestId('workflow-transfer-open').click();await ui.getByTestId('workflow-transfer-mode').selectOption('bundle');const d=page.waitForEvent('download');await ui.getByTestId('workflow-transfer-export').click();transferPath=path.join(artifactRoot,'workflow-transfer.json');await(await d).saveAs(transferPath);const envelope=JSON.parse(readFileSync(transferPath,'utf8'));if(!envelope.bundle.source.includes('instructions:'))throw Error('Export omitted instructions');});
 await step('03-import','Inspect and import in another workspace','Navigate to the separate import workspace, create a blank editor entry, open Export / import workflow, upload the downloaded transfer, choose workflows/'+runLabel+'.workflow.wflow, Inspect, then Import inspected definition.','A separate definition opens in a different workspace tab, preserving the saved instructions despite current defaults B. Import does not execute the previous run.',async()=>{await page.goto(workspace.url);await ui.getByTestId('activity-bar-workflows-btn').click();await ui.getByTestId('workflow-file-menu').click();await ui.getByTestId('workflow-file-new').click();await ui.getByLabel('Workflow name').fill('cross-entry-'+runLabel.slice(-14));await ui.getByTestId('workflow-file-create').click();await page.getByRole('heading',{name:'cross-entry-'+runLabel.slice(-14),exact:true}).filter({visible:true}).waitFor();await page.locator('dialog[open]').waitFor({state:'hidden'});await ui.getByTestId('workflow-transfer-open').click();const defaultsResponse=await context.request.get(base+'/api/settings/workflow-instructions');if(!defaultsResponse.ok())throw Error('Current defaults unavailable');const defaults=await defaultsResponse.json();if(defaults.instructions.policy.assumption_policy!=='require_specified'||!defaults.instructions.assets.find(asset=>asset.id==='task.response')?.body.includes('Default variation B'))throw Error('Isolated defaults B not established before import');writeFileSync(path.join(artifactRoot,'current-defaults-before-import.json'),JSON.stringify({digest:defaults.digest,revision:defaults.revision,origin:defaults.origin,policy:defaults.instructions.policy,profile_id:defaults.instructions.profile_id,task_response_body_digest:defaults.instructions.assets.find(asset=>asset.id==='task.response').body_digest},null,2));await ui.getByTestId('workflow-transfer-upload').setInputFiles(transferPath);await ui.getByTestId('workflow-transfer-destination').fill('workflows/'+runLabel+'.workflow.wflow');await ui.getByTestId('workflow-transfer-inspect').click();await page.getByText('Definition can be imported',{exact:true}).filter({visible:true}).waitFor();await ui.getByTestId('workflow-transfer-import').click();await ui.getByTestId('workflow-transfer-dialog').waitFor({state:'hidden'});activePath=new URL(page.url()).searchParams.get('workflowPath');if(activePath===previous.path||starts.length)throw Error('Import reused original path or started a run');});
 await step('04-change','Refine the imported calculation using existing step controls','In Diagram select the AI prompt block. Temporarily select Write here to update its retained calculation text to 80 x40 mm, then From another block and reconnect the same User response. Update Step instruction settings to the same 80 x40 mm guidance, Apply and Save.','A new accepted revision changes only existing task guidance. Imported saved profile text and instruction contracts remain frozen.',async()=>{
  await ui.getByTestId('workflow-recovery-view-diagram').click();await page.locator('.react-flow__node-recovery').filter({has:page.getByRole('heading',{name:'AI prompt',exact:true})}).filter({visible:true}).click();const guidance='Use the supplied structured answer. Calculate volume and mass only of identical rectangular solid plates, 80 mm x 40 mm with supplied thickness_mm in millimeters; selection is steel or aluminum. Steel density is 7850 kg/m3; aluminum density is 2700 kg/m3. Preserve supplied values. Show unit conversions, volume in m3, both masses in grams, and chosen focus. Do not ask questions or claim verified strength, fit or manufacturing feasibility.';const promptFrom=ui.getByTestId('workflow-recovery-prompt-from');const answerSource=await promptFrom.inputValue();await ui.getByTestId('workflow-recovery-prompt-source').selectOption('inline');await ui.getByTestId('workflow-recovery-prompt-editor').locator('.recovery-prompt-editor__prompt textarea').fill(guidance);await ui.getByTestId('workflow-recovery-prompt-source').selectOption('connection');await ui.getByTestId('workflow-recovery-prompt-from').selectOption(answerSource);await ui.getByTestId('workflow-step-instructions-toggle').click();await ui.getByLabel('Additional step guidance').fill(guidance);await ui.getByTestId('workflow-step-instructions-apply').click();accepted=await save();if(JSON.stringify(instructionCollection(accepted.source))!==JSON.stringify(instructionCollection(previous.source)))throw Error('Import changed frozen instruction profile to current defaults');writeFileSync(path.join(artifactRoot,'accepted-instruction-profile.json'),JSON.stringify(instructionCollection(accepted.source),null,2));writeFileSync(path.join(artifactRoot,'accepted-source.json'),JSON.stringify(accepted,null,2));
 });
 await step('05-run','Run the changed calculation to its declared input','Click Run once, then Answer in working view. Leave the answer unsent for the attributed synthetic integration response.','A separate exact run waits at its declared input, with no reused decision from the exported process.',async()=>{
  const pending=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/api/workspace/workflow-sources/run');await ui.getByTestId('workflow-recovery-run-start').click();const r=await pending;if(!r.ok())throw Error('Run rejected HTTP '+r.status());await ui.getByTestId('workflow-run-input-wait').waitFor();receipt=await readExactWaitingRun();if(receipt?.status!=='waiting_human'||!receipt.run_id||!receipt.input_checkpoint)throw Error('Imported process did not create its own declared wait');writeFileSync(path.join(artifactRoot,'waiting-run.json'),JSON.stringify({...receipt,software_integration_test:true,engineering_acceptance:false,expected_response:{selection:'aluminum',thickness_mm:3}},null,2));await ui.getByTestId('workflow-run-answer-input').click();await page.getByRole('button',{name:'Submit response',exact:true}).filter({visible:true}).waitFor();writeFileSync(path.join(artifactRoot,'awaiting-coordinator.json'),JSON.stringify({run_id:receipt.run_id,path:activePath,workspace_id:workspace.workspace_id,session_id:workspace.session_id,expected_response:{selection:'aluminum',thickness_mm:3},actor_required:'integration_test',checkpoint:receipt.input_checkpoint},null,2));
 });
 const gate=path.join(artifactRoot,'integration-response.json');const deadline=Date.now()+20*60*1000;
 while(Date.now()<deadline){try{const response=JSON.parse(readFileSync(gate,'utf8'));if(response.run_id!==receipt.run_id)throw Error('Coordinator receipt has different run');break;}catch(error){if(error.code!=='ENOENT')throw error;}await new Promise(resolve=>setTimeout(resolve,1000));}
 try{readFileSync(gate);}catch{throw Error('Timed out awaiting attributed integration response; durable wait remains unchanged.');}
 const completed=JSON.parse(readFileSync(gate,'utf8'));const emittedPath=completed.outcome?.output_path;if(!emittedPath)throw Error('Completed receipt omitted exact output path');const actualInstructions=completed.outcome.steps.find(step=>step.execution_kind==='ai')?.instructions;if(actualInstructions?.assumption_policy!=='document_reasonable')throw Error('Actual imported execution adopted current default policy');writeFileSync(path.join(artifactRoot,'actual-instruction-provenance.json'),JSON.stringify(actualInstructions,null,2));
 await step('06-result','Open and read the changed numerical result','Open working view for the completed run. In Results and checks, open the mass document representation and scroll within its bounded text preview to read the calculated masses.','The real model output shows volume9.6e-6 m3, steel75.36g and aluminum25.92g; the answer is explicitly attributed integration_test and no approval is invented.',async()=>{await page.reload();await page.getByRole('heading',{name:'Results and checks',exact:true}).filter({visible:true}).waitFor();const result=page.locator('.wp-result').filter({hasText:emittedPath}).getByRole('button',{name:'Open representation',exact:true});await result.first().click();await page.locator('.wp-text').filter({visible:true,hasText:'75.36'}).waitFor({timeout:30000});await assertReaderSelected();const text=await page.locator('.wp-text').filter({visible:true}).innerText();if(!text.includes('25.92'))throw Error('Changed numerical output missing aluminum mass');writeFileSync(path.join(artifactRoot,'visible-result-text.txt'),text);await page.locator('.wp-text').filter({visible:true}).hover();await page.mouse.wheel(0,600);await page.waitForTimeout(250);if(new URL(page.url()).searchParams.get('processRun')!==receipt.run_id)throw Error('Result working view bound to wrong run');});
 await step('07-reload','Reopen durable results without rerunning','Reload the working view and open the recorded document again.','Same-run results survive reload; exactly one changed-process run was started.',async()=>{await page.reload();await page.getByRole('heading',{name:'Results and checks',exact:true}).filter({visible:true}).waitFor();await page.locator('.wp-result').filter({hasText:emittedPath}).getByRole('button',{name:'Open representation',exact:true}).first().click();await page.locator('.wp-text').filter({visible:true,hasText:'75.36'}).waitFor();if(starts.length!==1)throw Error('Duplicate run start');writeFileSync(path.join(artifactRoot,'run-start-requests.json'),JSON.stringify(starts,null,2));});
 status.overall='pass';status.summary='Production normal workspace exported/imported a saved process, authored changed dimensions through existing task controls, resumed the new declared wait using an attributed synthetic response and ran the actual model, opened real comparative results and reloaded the same run. Software proof; no engineering acceptance or physical effects.';report();
}catch(error){process.exitCode=2;console.log(JSON.stringify({status:'stopped',reason:String(error.message).slice(0,1000),report:path.join(artifactRoot,'report.html')}));}
finally{writeFileSync(path.join(artifactRoot,'playwright/diagnostics.json'),JSON.stringify(diagnostics,null,2));await context.tracing.stop({path:path.join(artifactRoot,'trace/trace.zip')});await browser.close();report();}
