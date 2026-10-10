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
  "production-plate-mass-" +
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
    "Production authoring, declared input and comparative mass results",
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

let accepted, activePath, receipt;
const instructionCollection = source => {const line=source.split('\n').find(line=>/^\s*instructions: /.test(line));if(!line)throw Error('Embedded instructions missing');return JSON.parse(line.slice(line.indexOf(':')+1));};
const assertReaderSelected = async () => {const reader=page.getByRole('region',{name:'Selected representation',exact:true}).filter({visible:true});const box=await reader.boundingBox();if(!box||box.y< -2||box.y>(page.viewportSize()?.height??1000)/2)throw Error('Opened reader was not brought into view');if(!await reader.evaluate(element=>document.activeElement===element))throw Error('Opened reader did not receive focus');};
const save=async()=>{const pending=page.waitForResponse(r=>r.request().method()==='PUT'&&new URL(r.url()).pathname==='/api/workspace/workflow-sources');await ui.getByTestId('workflow-recovery-save').click();const r=await pending;if(!r.ok())throw Error('Save rejected HTTP '+r.status());return r.json();};
const runRequests=[];page.on('request',r=>{const p=new URL(r.url()).pathname;if(r.method()==='POST'&&p==='/api/workspace/workflow-sources/run')runRequests.push({path:p,body:JSON.parse(r.postData())});});

const readExactWaitingRun = async () => {
 const response=await context.request.get(base+'/api/workspace/workflow-sources/runs',{params:{session_id:workspace.session_id,path:activePath,latest_only:'true'}});if(!response.ok())throw Error('Run history read failed');const history=await response.json();const latest=history.runs?.[0];if(history.workflow_path!==activePath||latest?.status!=='waiting_human'||latest.source_digest!==accepted.storage_digest||!latest.run_id||!latest.path)throw Error('Latest durable wait does not match accepted source');const location=path.resolve(workspace.local_path,latest.path);if(!location.startsWith(path.resolve(workspace.local_path)+path.sep))throw Error('Run log outside isolated workspace');const record=JSON.parse(readFileSync(location,'utf8'));if(record.run_id!==latest.run_id||record.source_digest!==accepted.storage_digest)throw Error('Run log identity mismatch');return {...record.result,input_checkpoint:record.input_checkpoint??record.result.input_checkpoint,run_id:record.run_id,workspace_id:workspace.workspace_id,workflow_path:activePath,run_log_path:latest.path,source_digest:record.source_digest,status:record.status};
};
try {
 if(!process.argv[5]) {
 await step('01-create','Create a fresh mass calculation workflow','Open Workflows, Workflow files, New workflow and name the process '+runLabel+'.','An empty definition is created from normal workspace entry.',async()=>{
  await page.goto(workspace.url);await ui.getByTestId('activity-bar-workflows-btn').click();await ui.getByTestId('workflow-file-menu').click();await ui.getByTestId('workflow-file-new').click();await ui.getByLabel('Workflow name').fill(runLabel);await ui.getByTestId('workflow-file-create').click();await page.getByRole('heading',{name:runLabel,exact:true}).waitFor();activePath=new URL(page.url()).searchParams.get('workflowPath');
 });
 await step('02-request','Declare material and thickness before the calculation','Use Create Input → Request input. Enter user instructions and add required choice selection (steel/aluminum) and numeric thickness_mm (1–8mm), then Apply response declaration.','A first-step question has an explicit answer schema without invented upstream evidence.',async()=>{
  await ui.getByTestId('workflow-recovery-create-group-input').click();await ui.getByTestId('workflow-recovery-create-template-human-input').click();await ui.getByTestId('workflow-human-input-instructions').fill('Choose material focus and plate thickness for this software mass comparison. This does not approve a design.');
  while(await page.getByRole('button',{name:/^Remove field /}).filter({visible:true}).count())await page.getByRole('button',{name:/^Remove field /}).filter({visible:true}).first().click();
  await page.getByRole('button',{name:'Add answer field',exact:true}).filter({visible:true}).click();let field=page.getByRole('group',{name:'Field 1',exact:true}).filter({visible:true});await field.getByLabel('Field name',{exact:true}).fill('selection');await field.getByLabel('Field label',{exact:true}).fill('Material focus');await field.getByLabel('Answer type').selectOption('choice');await field.getByLabel('Choices (one per line)').fill('steel\naluminum');
  await page.getByRole('button',{name:'Add answer field',exact:true}).filter({visible:true}).click();field=page.getByRole('group',{name:'Field 2',exact:true}).filter({visible:true});await field.getByLabel('Field name',{exact:true}).fill('thickness_mm');await field.getByLabel('Field label',{exact:true}).fill('Thickness (mm)');await field.getByLabel('Answer type').selectOption('number');await field.getByLabel('Minimum value',{exact:true}).fill('1');await field.getByLabel('Maximum value',{exact:true}).fill('8');await ui.getByTestId('workflow-human-input-apply').click();
  if(await page.getByRole('alert').filter({visible:true}).count())throw Error(await page.getByRole('alert').filter({visible:true}).allTextContents());
 });
 await step('03-calculation','Author the actual AI mass calculation','Use Create AI prompt → AI prompt. Set the mass calculation instructions and comparative-plate-masses.txt output. In Step instruction settings retain the calculation as scoped guidance.','The AI task has explicit supplied geometry/densities and a saved result file; no follow-up question is introduced.',async()=>{
  await ui.getByTestId('workflow-recovery-create-group-document').click();await ui.getByTestId('workflow-recovery-create-template-ai-prompt').click();const prompt='Use the supplied structured answer. Calculate volume and mass only of identical rectangular solid plates, 80 mm x 40 mm with the supplied thickness_mm in millimeters; selection is steel or aluminum. Steel density is 7850 kg/m3; aluminum density is 2700 kg/m3. Preserve every supplied value. Show unit conversions, volume in m3, both masses in grams, and chosen focus. Do not ask questions or claim verified strength, fit or manufacturing feasibility.';
  await ui.getByTestId('workflow-recovery-prompt-editor').locator('.recovery-prompt-editor__prompt textarea').fill(prompt);await ui.getByTestId('workflow-recovery-output-filename').fill('comparative-plate-masses.txt');await ui.getByTestId('workflow-step-instructions-toggle').click();await ui.getByLabel('Additional step guidance').fill(prompt);await ui.getByTestId('workflow-step-instructions-apply').click();
 });
 await step('04-connect','Draw the answer-to-prompt connection and save','Fit workflow to view. Drag User response output from Request input to Prompt input on the AI task. Save.','The graph has the real typed dependency; the saved step guidance supplies calculation intent when its user prompt comes from the answer.',async()=>{
  await ui.getByTestId('workflow-recovery-canvas-fit').click();await page.waitForTimeout(250);const source=page.getByRole('button',{name:'Connect from User response output',exact:true}).filter({visible:true});const target=page.getByRole('button',{name:'Connect to Prompt input',exact:true}).filter({visible:true});const a=await source.boundingBox(),b=await target.boundingBox();if(!a||!b)throw Error('Connection handles not visible');await page.mouse.move(a.x+a.width/2,a.y+a.height/2);await page.mouse.down();await page.mouse.move(b.x+b.width/2,b.y+b.height/2,{steps:20});await page.mouse.up();await page.waitForTimeout(300);await ui.getByTestId('workflow-recovery-view-code').click();const text=await ui.getByTestId('workflow-recovery-source-editor').inputValue();if(!text.includes('"prompt_source":"connection"')&&!text.includes('"prompt_source": "connection"'))throw Error('Drawn connection did not set prompt source');if(!text.includes('instruction_override')||!text.includes('comparative-plate-masses.txt'))throw Error('Calculation guidance/output missing');await ui.getByTestId('workflow-recovery-view-diagram').click();accepted=await save();writeFileSync(path.join(artifactRoot,'accepted-source.json'),JSON.stringify(accepted,null,2));
 });
 await step('05-instructions','Review and save complete instruction dependencies','Open Instructions. Review instruction compatibility upgrade, inspect the exact proposed collection, Apply reviewed instruction update, then Save.','The accepted process carries current helper resources while preserving its author guidance and policy; no installation default is changed.',async()=>{
  await ui.getByTestId('workflow-recovery-instructions').click();await ui.getByTestId('workflow-instructions-review-action-upgrade').click();await ui.getByTestId('workflow-instructions-action-intent-diff').waitFor();await ui.getByTestId('workflow-instructions-action-intent-diff').scrollIntoViewIfNeeded();if(await ui.getByTestId('workflow-instructions-apply-update').isEnabled()){await ui.getByTestId('workflow-instructions-apply-update').click();await page.getByText('Instructions applied to the draft.',{exact:false}).waitFor();}else{await page.getByText('This collection already includes the current instruction contracts and helper resources. No upgrade is needed.',{exact:true}).waitFor();}await ui.getByTestId('workflow-recovery-modal-close').click();if(await ui.getByTestId('workflow-recovery-save').isEnabled())accepted=await save();writeFileSync(path.join(artifactRoot,'accepted-source.json'),JSON.stringify(accepted,null,2));const profile=instructionCollection(accepted.source);if(profile.assets.length<34)throw Error('New saved profile missing current helper dependencies');writeFileSync(path.join(artifactRoot,'accepted-instruction-profile.json'),JSON.stringify(profile,null,2));
 });
 await step('06-run','Run until the declared question','Click Run.','The exact saved process enters Waiting for your input with an answer action, not failure.',async()=>{
  const pending=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname==='/api/workspace/workflow-sources/run');await ui.getByTestId('workflow-recovery-run-start').click();const r=await pending;if(!r.ok())throw Error('Run start rejected HTTP '+r.status());await ui.getByTestId('workflow-run-input-wait').waitFor();receipt=await readExactWaitingRun();if(receipt?.status!=='waiting_human'||!receipt.input_checkpoint||!receipt.run_id)throw Error('Run did not return exact declared wait');await ui.getByTestId('workflow-run-input-wait').waitFor();writeFileSync(path.join(artifactRoot,'waiting-run.json'),JSON.stringify({...receipt,software_integration_test:true,engineering_acceptance:false,expected_response:{selection:'aluminum',thickness_mm:3}},null,2));
 });
 } else {
  accepted=JSON.parse(readFileSync(process.argv[5],'utf8'));activePath=accepted.path;
  await step('01-existing-wait','Reconcile the same manually authored run','Reopen the accepted process after the test recorder lost its streaming response body. Do not start another run.','The already created declared wait is recovered from durable state with the exact source and run identity.',async()=>{await page.goto(workspace.url+'?workflow=canonical&workflowPath='+encodeURIComponent(activePath));await ui.getByTestId('workflow-run-input-wait').waitFor();receipt=await readExactWaitingRun();writeFileSync(path.join(artifactRoot,'waiting-run.json'),JSON.stringify({...receipt,software_integration_test:true,engineering_acceptance:false,expected_response:{selection:'aluminum',thickness_mm:3}},null,2));writeFileSync(path.join(artifactRoot,'accepted-source.json'),JSON.stringify(accepted,null,2));});
 }
 await step('07-working','Open the exact waiting run in its working view','Click Answer in working view. Leave the answer unsent; the test coordinator supplies an attributed synthetic integration response.','The question is shown in a Wright tab bound to the exact run and answer schema.',async()=>{
  await ui.getByTestId('workflow-run-answer-input').click();await page.getByRole('button',{name:'Submit response',exact:true}).filter({visible:true}).waitFor();if(new URL(page.url()).searchParams.get('processRun')!==receipt.run_id)throw Error('Working view not bound to exact run');writeFileSync(path.join(artifactRoot,'awaiting-coordinator.json'),JSON.stringify({run_id:receipt.run_id,path:activePath,workspace_id:workspace.workspace_id,session_id:workspace.session_id,expected_response:{selection:'aluminum',thickness_mm:3},actor_required:'integration_test',checkpoint:receipt.input_checkpoint},null,2));
 });
 // No browser answer, approval or fabricated human identity. The coordinator uses the real trusted test service.
 const gate=path.join(artifactRoot,'integration-response.json');const deadline=Date.now()+20*60*1000;
 while(Date.now()<deadline){try{const response=JSON.parse(readFileSync(gate,'utf8'));if(response.run_id!==receipt.run_id)throw Error('Coordinator receipt has different run');break;}catch(error){if(error.code!=='ENOENT')throw error;}await new Promise(resolve=>setTimeout(resolve,1000));}
 try{readFileSync(gate);}catch{throw Error('Timed out awaiting attributed integration response; durable wait remains unchanged.');}
 const emittedPath=JSON.parse(readFileSync(gate,'utf8')).outcome?.output_path;if(!emittedPath)throw Error('Completed receipt omitted exact output path');
 await step('08-result','Inspect the completed calculation and open its result','Refresh the working view after the exact integration response. Read Progress and Results and checks; open the recorded document.','The same run completes, produces a real document and shows 75.36 g steel and 25.92 g aluminum for 80 x 40 x 3 mm.',async()=>{
  await page.reload();await page.getByRole('heading',{name:'Results and checks',exact:true}).filter({visible:true}).waitFor();await page.getByRole('heading',{name:'Results and checks',exact:true}).filter({visible:true}).scrollIntoViewIfNeeded();
  const body=await page.locator('body').innerText();if(/Process needs attention/.test(body))throw Error('Run failed after response');
  const opening=page.locator('.wp-result').filter({hasText:emittedPath}).getByRole('button',{name:'Open representation',exact:true}).filter({visible:true});await opening.first().waitFor({timeout:30000});await opening.first().click();await page.locator('.wp-text').filter({visible:true,hasText:'75.36'}).waitFor({timeout:30000});await assertReaderSelected();const resultText=await page.locator('body').innerText();if(!/75\.36/.test(resultText)||!/25\.92/.test(resultText))throw Error('Opened result lacks exact changed numeric masses');writeFileSync(path.join(artifactRoot,'visible-result-text.txt'),resultText);
 });
 await step('09-reuse','Reload the saved workflow and completed run','Reload the original workflow URL. Inspect its latest saved run and result availability.','Completed history survives reopen, the output is available, and no duplicate run is started.',async()=>{
  await page.goto(workspace.url+'?workflow=canonical&workflowPath='+encodeURIComponent(activePath));await ui.getByTestId('workflow-recovery-run-details-toggle').waitFor();if(runRequests.length!==(process.argv[5]?0:1))throw Error('Unexpected duplicate run start');await ui.getByTestId('workflow-results-toggle').click();await page.getByRole('region',{name:'Workflow results',exact:true}).filter({visible:true}).getByRole('button').first().click();await ui.getByTestId('workflow-result-open').waitFor();if(!(await ui.getByTestId('workflow-result-open').getAttribute('title')).endsWith(emittedPath))throw Error('Recorded output is not available after reopen');writeFileSync(path.join(artifactRoot,'run-start-requests.json'),JSON.stringify(runRequests,null,2));
 });
 status.overall='pass';status.summary='Fresh ordinary production workspace create/edit/save/run declared wait, exact attributed synthetic response, actual model numeric result and durable reload verified. Software proof only; no engineering acceptance or external effects.';report();
}catch(error){process.exitCode=2;console.log(JSON.stringify({status:'stopped',reason:String(error.message).slice(0,1000),report:path.join(artifactRoot,'report.html')}));}
finally{writeFileSync(path.join(artifactRoot,'playwright/diagnostics.json'),JSON.stringify(diagnostics,null,2));await context.tracing.stop({path:path.join(artifactRoot,'trace/trace.zip')});await browser.close();report();}
