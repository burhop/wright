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
    "Recorded native CAD image result in the common working view",
  summary:
    "Read-only result proof: inspect an already completed digital CAD/image run. No new run, model call, answer or approval is submitted.",
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


const runId='e3a2f56a090f4e9cb765582b42cb21d8';
const fileName='exhaustive-strict-9663f682-on-table.png';
const links=readFileSync('specs/083-process-working-interfaces/evidence/instruction-portability-workflow-links.md','utf8');
const exactUrl=[...links.matchAll(/\((http[^)]+)\)/g)].map(match=>match[1]).find(url=>new URL(url).searchParams.get('processRun')===runId);
if(!exactUrl)throw Error('Exact recorded image link missing');
const mutations=[];page.on('request',r=>{const pathname=new URL(r.url()).pathname;if(r.method()==='POST' && (/workflow-sources\/run$/.test(pathname)||/\/(actions|responses|approve|answer|review)$/.test(pathname)))mutations.push(pathname);});
const openImage=async()=>{
 const opening=page.locator('.wp-result').filter({hasText:fileName}).getByRole('button',{name:'Open representation',exact:true}).filter({visible:true});await opening.first().waitFor({timeout:30000});await opening.first().click();
 const reader=page.getByRole('region',{name:'Selected representation',exact:true}).filter({visible:true});const image=reader.getByRole('img');await image.waitFor();await page.waitForFunction(()=>{const image=document.querySelector('[aria-label="Selected representation"] img');return image instanceof HTMLImageElement&&image.naturalWidth>0&&image.naturalHeight>0;});
 const imageBox=await image.boundingBox();if(!imageBox||imageBox.y<60||imageBox.y+imageBox.height>(page.viewportSize()?.height??1000)+2)throw Error('Loaded image is not fully visible in the reader');if(!await reader.evaluate(element=>document.activeElement===element))throw Error('Loaded image reader not focused');
 const info=await image.evaluate(element=>({alt:element.alt,width:element.naturalWidth,height:element.naturalHeight}));if(!info.alt.includes(fileName))throw Error('Displayed image identity differs from exact artifact');if(new URL(page.url()).searchParams.get('processRun')!==runId)throw Error('Wrong recorded run');return info;
};
try{
 await step('01-completed','Open the exact completed native CAD/image run','Open the saved exact working-view link for exhaustive-strict-shape-9663f682. Do not start the process.','The recorded run is completed and its exact result list is available in a Wright tab.',async()=>{await page.goto(exactUrl);await page.getByRole('heading',{name:'Results and checks',exact:true}).filter({visible:true}).waitFor();await page.getByText('Process completed',{exact:true}).filter({visible:true}).first().waitFor();await page.getByRole('heading',{name:'Results and checks',exact:true}).filter({visible:true}).scrollIntoViewIfNeeded();});
 await step('02-image','Open the final generated PNG','In the final image result, choose Open representation.','The actual PNG loads visibly, is focused after bitmap load, and retains the exact run and artifact identity.',async()=>{const info=await openImage();writeFileSync(path.join(artifactRoot,'loaded-image.json'),JSON.stringify({run_id:runId,working_view_url:exactUrl,...info},null,2));});
 await step('03-reopen','Reload and reopen the same recorded image','Reload the working view and open the final PNG representation again.','The same image remains readable with no new run, model invocation, answer or approval.',async()=>{await page.reload();await page.getByRole('heading',{name:'Results and checks',exact:true}).filter({visible:true}).waitFor();await openImage();if(mutations.length)throw Error('Unexpected process mutation during read-only image proof');writeFileSync(path.join(artifactRoot,'process-mutations.json'),JSON.stringify(mutations,null,2));});
 status.overall='pass';status.summary='Actual recorded native CAD/image PNG visibly loads and receives focus in the common Wright working view, reloads on the exact run, and causes no process actions. Read-only software proof, not engineering acceptance.';report();
}catch(error){process.exitCode=2;console.log(JSON.stringify({status:'stopped',reason:String(error.message).slice(0,1000),report:path.join(artifactRoot,'report.html')}));}
finally{writeFileSync(path.join(artifactRoot,'playwright/diagnostics.json'),JSON.stringify(diagnostics,null,2));await context.tracing.stop({path:path.join(artifactRoot,'trace/trace.zip')});await browser.close();report();}
