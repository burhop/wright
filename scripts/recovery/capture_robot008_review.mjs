// Read-only campaign review walkthrough. Never submits a decision or resumes a run.
import { chromium } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, copyFileSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const walkthroughRoot = path.resolve(process.argv[2]);
if (existsSync(walkthroughRoot)) throw new Error('Use a new artifact directory.');
for (const d of ['playwright', 'screenshots/raw', 'screenshots/annotated', 'trace']) mkdirSync(path.join(walkthroughRoot, d), { recursive: true });
copyFileSync(fileURLToPath(import.meta.url), path.join(walkthroughRoot, 'playwright/capture.mjs'));
const url = 'http://127.0.0.1:5173/workspace/c33593b1-73a8-4056-a7f4-a07a9903dd2d';
const workflow = 'workflows/validator-082-robot-tracking-diagnosis-01-attempt-008.workflow.wflow';
const digest = 'bf5cce0f15829bb136b98b99a66ad5632bf5a0b0ccc78cbc9ad781b89fadf8a5';
const status = { title: 'Robot attempt 008 — human review', summary: 'Preparing the existing review; no decision or resume will be submitted.', overall: 'pending', updated: new Date().toISOString(), manualSteps: [
  { label: 'Open workspace', instruction: `Open ${url}, then click Workflows.` },
  { label: 'Choose attempt 008', instruction: 'Click File, then Open workflow, and choose validator-082-robot-tracking-diagnosis-01-attempt-008.workflow.wflow.' },
  { label: 'Inspect review', instruction: 'Open run details. Review ACTION-SCOPE, DIAGNOSIS, and PLOTS against the diagnosis and trajectory overlay.' },
  { label: 'Human decision only', instruction: 'Record your decision with Approve reviewed requirements or Request changes. Leave Resume to the campaign runner.' },
], steps: [] };
const diagnostics = [];
const esc = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('"', '&quot;');
function save() {
  status.updated = new Date().toISOString();
  writeFileSync(path.join(walkthroughRoot, 'status.json'), JSON.stringify(status, null, 2));
  writeFileSync(path.join(walkthroughRoot, 'trace/diagnostics.json'), JSON.stringify(diagnostics, null, 2));
  writeFileSync(path.join(walkthroughRoot, 'report.html'), `<!doctype html><meta charset="utf-8"><title>${esc(status.title)}</title><style>body{font:16px system-ui;max-width:1100px;margin:30px auto;background:#f5f7fa;color:#172130}.pass{border-left:6px solid #188343}.blocked{border-left:6px solid #c52b34}.pending{border-left:6px solid #89919a}section{padding:16px;margin:16px 0;background:white}img{width:48%;vertical-align:top}code{overflow-wrap:anywhere}</style><h1>${esc(status.title)}</h1><p>${esc(status.summary)}</p><h2>Manual repeat checklist</h2><ol>${status.manualSteps.map(s => `<li>${esc(s.instruction)}</li>`).join('')}</ol>${status.steps.map(s => `<section class="${s.state}"><h2>${esc(s.label)} — ${s.state}</h2><p>${esc(s.action)}</p><p>Expected: ${esc(s.expected)}</p><p>Actual: ${esc(s.actual)}</p>${s.raw ? `<a target="_blank" href="${s.raw}"><img src="${s.raw}" alt="Raw screen"></a><a target="_blank" href="${s.annotated}"><img src="${s.annotated}" alt="Annotated screen"></a>` : ''}</section>`).join('')}`);
}
writeFileSync(path.join(walkthroughRoot, 'progress.md'), `# Robot 008 review walkthrough\n\n${status.updated} UTC — prepared before browser launch. Existing campaign only; no approval or resume.\n`);
save();
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1500, height: 1000 } });
await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
const page = await context.newPage();
page.on('console', m => { if (m.type() === 'error') diagnostics.push({ type: 'console', message: m.text() }); });
page.on('pageerror', e => diagnostics.push({ type: 'pageerror', message: e.message }));
page.on('response', r => { if (r.status() >= 400) diagnostics.push({ type: 'http', status: r.status(), url: r.url() }); });
page.on('requestfailed', r => diagnostics.push({ type: 'requestfailed', url: r.url(), error: r.failure() }));
// Reuse the repository's raw/annotated capture utility without invoking its editing scenario.
const harness = readFileSync('scripts/recovery/capture_workspace_workflow_walkthrough.mjs', 'utf8');
const captureSource = harness.slice(harness.indexOf('async function capture('), harness.indexOf('async function screenshotFailure('));
const captureBase = new Function('page', 'path', 'walkthroughRoot', `${captureSource}; return capture;`)(page, path, walkthroughRoot);
async function capture(name, title, markers) {
  const visibleMarkers = [];
  for (const [index, item] of markers.entries()) {
    const control = page.locator(item.selector).filter({ visible: true });
    if (await control.count() !== 1) throw new Error(`Expected one visible ${item.label}`);
    await control.evaluate((element, index) => element.setAttribute('data-review-visible-control', String(index)), index);
    visibleMarkers.push({ ...item, selector: `[data-review-visible-control="${index}"]` });
  }
  try { return await captureBase(name, title, visibleMarkers); }
  finally { await page.locator('[data-review-visible-control]').evaluateAll(elements => elements.forEach(element => element.removeAttribute('data-review-visible-control'))); }
}
const runDetails = () => page.getByTestId('workflow-recovery-run-details-toggle').filter({ visible: true });
const marker = (id, label) => ({ selector: `[data-testid="${id}"]`, label });
let current;
async function step(label, action, controls, expected, operation, markers = []) {
  current = { id: `S${status.steps.length + 1}`, state: 'pending', label, summary: 'In progress', purpose: 'Reach the exact existing human review without modifying campaign evidence.', action, controls, expected, actual: 'Pending' };
  status.steps.push(current); save();
  if (page.url() !== 'about:blank') Object.assign(current, await capture(`${current.id}-before`, label, markers));
  await operation();
  current.state = 'pass'; current.actual = expected; current.summary = expected;
  appendFileSync(path.join(walkthroughRoot, 'progress.md'), `\n${new Date().toISOString()} UTC | PASS | ${page.url()}\nAction: ${action}\nControls/value: ${controls.join(', ')}\nExpected/actual: ${expected}\nImages: ${current.raw || 'initial navigation'}, ${current.annotated || 'initial navigation'}\nDiagnostics: ${JSON.stringify(diagnostics)}\n`);
  save();
}
try {
  await step('Workspace entry', `Open ${url}`, ['Workspace'], 'Ordinary workspace shows Workflows.', async () => { await page.goto(url); await page.getByTestId('activity-bar-workflows-btn').waitFor({ timeout: 60000 }); });
  await step('Workflows', 'Click Workflows.', ['Workflows'], 'Workspace workflow editor is visible.', async () => { await page.getByTestId('activity-bar-workflows-btn').click(); await page.getByTestId('workflow-file-menu').waitFor({ timeout: 60000 }); }, [marker('activity-bar-workflows-btn', 'Workflows')]);
  await step('File menu', 'Click File.', ['File'], 'Open workflow is available.', async () => { await page.getByTestId('workflow-file-menu').click(); await page.getByTestId('workflow-file-open').waitFor(); }, [marker('workflow-file-menu', 'File')]);
  await step('Open workflow', 'Click Open workflow.', ['Open workflow'], 'Existing attempt 008 is listed.', async () => { await page.getByTestId('workflow-file-open').click(); await page.getByTestId(`workflow-file-choice-${workflow}`).waitFor({ timeout: 60000 }); await page.getByTestId(`workflow-file-choice-${workflow}`).scrollIntoViewIfNeeded(); }, [marker('workflow-file-open', 'Open workflow')]);
  await step('Select exact attempt', `Choose ${workflow}`, [workflow], 'Attempt 008 opens with run details available.', async () => { await page.getByTestId(`workflow-file-choice-${workflow}`).click(); await runDetails().waitFor({ timeout: 60000 }); }, [marker(`workflow-file-choice-${workflow}`, 'Robot attempt 008')]);
  await step('Run details', 'Open run details if collapsed.', ['Run details'], 'Exact digest and all three robot review requirements are visible in the pending review.', async () => {
    if (!(await page.getByTestId('workflow-external-approval').isVisible())) await runDetails().click();
    const panel = page.getByTestId('workflow-external-approval'); await panel.waitFor({ timeout: 60000 });
    const body = await panel.innerText();
    for (const value of [digest, 'ROBOT01-ACTION-SCOPE', 'ROBOT01-DIAGNOSIS', 'ROBOT01-PLOTS', 'pending']) if (!body.includes(value)) throw new Error(`Review missing ${value}`);
    writeFileSync(path.join(walkthroughRoot, 'trace/review-text.txt'), body);
    await panel.scrollIntoViewIfNeeded();
  }, [marker('workflow-recovery-run-details-toggle', 'Run details')]);
  const images = await capture('review-requirements', 'Exact human review — no decision submitted', [marker('workflow-validation-review-requirements', 'Three pinned requirements')]);
  status.steps.push({ id: 'S7', state: 'blocked', label: 'Human decision', summary: 'Awaiting authenticated human review.', purpose: 'Keep human review authority with the reviewer.', action: 'No approval, changes request, or resume submitted.', controls: ['Decision note', 'Approve reviewed requirements', 'Request changes'], expected: 'Human reviews evidence and records their own decision.', actual: 'Exact pending checkpoint is shown. Automation stopped before decision controls.', ...images });
  status.overall = 'blocked'; status.summary = 'Exact robot attempt 008 review reached through Workflows. Awaiting your decision; nothing approved or resumed.';
  appendFileSync(path.join(walkthroughRoot, 'progress.md'), `\n${new Date().toISOString()} UTC | BLOCKED | ${page.url()}\nHuman decision required. No campaign data modified by this walkthrough; only navigation/selection UI state changed. Images: ${images.raw}, ${images.annotated}\n`);
} catch (error) {
  if (current) { current.state = 'blocked'; current.actual = error.message; current.summary = 'Stopped at first unexpected UI result.'; }
  try { if (current) Object.assign(current, await capture('stopped', 'Unexpected stopping point', [])); } catch {}
  status.overall = 'blocked'; status.summary = `Stopped: ${error.message}`;
  appendFileSync(path.join(walkthroughRoot, 'progress.md'), `\n${new Date().toISOString()} UTC | STOPPED | ${page.url()}\n${error.stack}\nDiagnostics: ${JSON.stringify(diagnostics)}\n`);
  process.exitCode = 1;
} finally {
  writeFileSync(path.join(walkthroughRoot, 'trace/page-text.txt'), await page.locator('body').innerText().catch(() => 'Unavailable'));
  save(); await context.tracing.stop({ path: path.join(walkthroughRoot, 'trace/review.zip') }); await browser.close();
  console.log(JSON.stringify({ root: walkthroughRoot, overall: status.overall, summary: status.summary }));
}
