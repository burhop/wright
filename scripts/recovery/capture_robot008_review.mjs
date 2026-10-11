// Read-only engineering UX walkthrough. Never submits a decision or resumes a run.
import { chromium, expect as baseExpect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, copyFileSync, existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const expect = baseExpect.configure({ timeout: 30000 });
const attempt = process.argv[3] || 'attempt-008';
if (!/^attempt-\d{3}$/.test(attempt)) throw new Error('Use an exact attempt-NNN identity.');
const label = `Robot ${attempt}`;

const walkthroughRoot = path.resolve(process.argv[2]);
if (existsSync(walkthroughRoot)) throw new Error('Use a new artifact directory.');
for (const d of ['playwright', 'screenshots/raw', 'screenshots/annotated', 'trace']) mkdirSync(path.join(walkthroughRoot, d), { recursive: true });
copyFileSync(fileURLToPath(import.meta.url), path.join(walkthroughRoot, 'playwright/capture.mjs'));
const url = 'http://127.0.0.1:5173/workspace/c33593b1-73a8-4056-a7f4-a07a9903dd2d';
const workflow = `workflows/validator-082-robot-tracking-diagnosis-01-${attempt}.workflow.wflow`;
let digest;
const status = { title: `${label} — engineering run details`, summary: 'Checking input access, useful run details, and review evidence without changing the run.', overall: 'pending', updated: new Date().toISOString(), manualSteps: [
  { label: 'Open workspace', instruction: `Open ${url}, then click Workflows.` },
  { label: `Choose ${attempt}`, instruction: `Click File, then Open workflow, and choose ${workflow.split('/').at(-1)}.` },
  { label: 'Inspect input', instruction: 'Select human context. Read the full selected filename and click Open file. Return to the workflow tab.' },
  ...(attempt === 'attempt-009' ? [{label:'Inspect result blocks', instruction:'Open Results beside Inputs. Choose Plots and supporting data. The teal RESULT block has View results; the result viewer has Open plot or image in tab. Also inspect Diagnosis and Evidence index; the latter must say Not produced yet. Repeat at 1060 and 752 pixels wide.'}] : []),
  { label: 'Inspect review', instruction: 'Open Run details, then Expand details. Open diagnosis.md and trajectory-overlay.svg. Return to the workflow tab after each file.' },
  { label: 'Inspect a step', instruction: 'Open Step progress and select a step to read its purpose, input sources, and recorded results.' },
  { label: 'Review checks', instruction: 'Compare the evidence with the three requirements. This walkthrough stops before Approve reviewed requirements or Request changes.' },
], steps: [] };
const diagnostics = [];
const esc = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('"', '&quot;');
function save() {
  status.updated = new Date().toISOString();
  writeFileSync(path.join(walkthroughRoot, 'status.json'), JSON.stringify(status, null, 2));
  writeFileSync(path.join(walkthroughRoot, 'trace/diagnostics.json'), JSON.stringify(diagnostics, null, 2));
  writeFileSync(path.join(walkthroughRoot, 'report.html'), `<!doctype html><meta charset="utf-8"><title>${esc(status.title)}</title><style>body{font:16px system-ui;max-width:1100px;margin:30px auto;background:#f5f7fa;color:#172130}.pass{border-left:6px solid #188343}.blocked{border-left:6px solid #c52b34}.pending{border-left:6px solid #89919a}section{padding:16px;margin:16px 0;background:white}img{width:48%;vertical-align:top}code{overflow-wrap:anywhere}</style><h1>${esc(status.title)}</h1><p>${esc(status.summary)}</p><h2>Manual repeat checklist</h2><ol>${status.manualSteps.map(s => `<li>${esc(s.instruction)}</li>`).join('')}</ol>${status.steps.map(s => `<section class="${s.state}"><h2>${esc(s.label)} — ${s.state}</h2><p>${esc(s.action)}</p><p>Expected: ${esc(s.expected)}</p><p>Actual: ${esc(s.actual)}</p>${s.raw ? `<a target="_blank" href="${s.raw}"><img src="${s.raw}" alt="Raw screen"></a><a target="_blank" href="${s.annotated}"><img src="${s.annotated}" alt="Annotated screen"></a>` : ''}</section>`).join('')}`);
  appendFileSync(path.join(walkthroughRoot, 'report.html'), `<h2>Resulting screens</h2>${status.steps.filter(s => s.after).map(s => `<section><h3>${esc(s.label)}</h3><a href="${s.after.raw}"><img src="${s.after.raw}" alt="Result after ${esc(s.label)}"></a><a href="${s.after.annotated}"><img src="${s.after.annotated}" alt="Annotated result"></a></section>`).join('')}<style>dialog{max-width:95vw;max-height:95vh;padding:12px}dialog::backdrop{background:#000b}dialog img{display:block;width:auto;max-width:90vw;max-height:82vh}</style><dialog id="image-preview"><button autofocus onclick="this.closest('dialog').close()">Close</button><img alt="Full-size walkthrough screenshot"></dialog><script>document.addEventListener('click',e=>{const a=e.target.closest('a');if(a&&a.querySelector('img')){e.preventDefault();const d=document.getElementById('image-preview');d.querySelector('img').src=a.href;d.showModal();}});</script>`);
}
writeFileSync(path.join(walkthroughRoot, 'progress.md'), `# ${label} review walkthrough\n\n${status.updated} UTC — prepared before browser launch. Existing campaign only; no approval or resume.\n`);
save();
const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 944, height: 791 } });
await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
const page = await context.newPage();
page.on('console', m => { if (m.type() === 'error') diagnostics.push({ type: 'console', message: m.text() }); });
page.on('pageerror', e => diagnostics.push({ type: 'pageerror', message: e.message }));
page.on('response', r => { if (r.status() >= 400) diagnostics.push({ type: 'http', status: r.status(), url: r.url() }); });
page.on('requestfailed', r => diagnostics.push({ type: 'requestfailed', url: r.url(), error: r.failure() }));
await page.route('**/api/workspace/workflow-sources**', async route => {
  if (!['GET', 'HEAD', 'OPTIONS'].includes(route.request().method())) {
    diagnostics.push({ type: 'blocked-mutation', method: route.request().method(), url: route.request().url() });
    await route.abort();
  } else await route.continue();
});
const statusUrl = `http://127.0.0.1:8000/api/workspace/workflow-sources/runs?session_id=wright-local-e3dc0ef1-06da-45dd-83b9-290347814f8a&path=${encodeURIComponent(workflow)}&latest_only=true`;
async function runIdentity() {
  const response = await context.request.get(statusUrl, { timeout: 60000 });
  if (!response.ok()) throw new Error(`Run status read failed: ${response.status()}`);
  const run = (await response.json()).runs[0];
  return { run: run.run_id, status: run.status, source: run.source_digest, checkpoint: run.approval.checkpoint_id,
    subject: run.approval.subject_digest, decision: run.approval.state, actor: run.approval.actor,
    artifacts: run.approval.continuation.artifact_files };
}
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
async function resultIsInsideCanvas() {
  await expect.poll(() => page.locator('.recovery-result-block.is-selected').evaluate(el => {
    const block = el.getBoundingClientRect();
    const canvas = el.closest('.recovery-canvas').getBoundingClientRect();
    return block.left >= canvas.left && block.right <= canvas.right;
  })).toBe(true);
}
let current;
async function step(label, action, controls, expected, operation, markers = []) {
  current = { id: `S${status.steps.length + 1}`, state: 'pending', label, summary: 'In progress', purpose: 'Reach the exact existing human review without modifying campaign evidence.', action, controls, expected, actual: 'Pending' };
  status.steps.push(current); save();
  appendFileSync(path.join(walkthroughRoot, 'progress.md'), `\n${new Date().toISOString()} UTC | PENDING | ${label}\nAction: ${action}\nControls/value: ${controls.join(', ')}\nExpected: ${expected}\n`);
  if (page.url() !== 'about:blank') Object.assign(current, await capture(`${current.id}-before`, label, markers));
  await operation();
  const errors = diagnostics.filter(d => ['console', 'pageerror', 'blocked-mutation', 'http'].includes(d.type));
  if (errors.length) throw new Error(`Browser error at ${label}: ${JSON.stringify(errors)}`);
  current.after = await capture(`${current.id}-after`, `${label} — result`, []);
  current.state = 'pass'; current.actual = expected; current.summary = expected;
  appendFileSync(path.join(walkthroughRoot, 'progress.md'), `\n${new Date().toISOString()} UTC | PASS | ${page.url()}\nAction: ${action}\nControls/value: ${controls.join(', ')}\nExpected/actual: ${expected}\nImages: ${current.raw || 'initial navigation'}, ${current.annotated || 'initial navigation'}\nDiagnostics: ${JSON.stringify(diagnostics)}\n`);
  save();
}
try {
  const before = await runIdentity();
  if (before.status !== 'awaiting_approval' || before.decision !== 'pending' || before.actor !== null) throw new Error('Run is not at an untouched pending engineering review.');
  digest = before.subject;
  writeFileSync(path.join(walkthroughRoot, 'trace/before-run.json'), JSON.stringify(before, null, 2));
  await step('Workspace entry', `Open ${url}`, ['Workspace'], 'Ordinary workspace shows Workflows.', async () => { await page.goto(url); await page.getByTestId('activity-bar-workflows-btn').waitFor({ timeout: 60000 }); });
  await step('Workflows', 'Click Workflows.', ['Workflows'], 'Workspace workflow editor is visible.', async () => { await page.getByTestId('activity-bar-workflows-btn').click(); await page.getByTestId('workflow-file-menu').waitFor({ timeout: 60000 }); }, [marker('activity-bar-workflows-btn', 'Workflows')]);
  await step('File menu', 'Click File.', ['File'], 'Open workflow is available.', async () => { await page.getByTestId('workflow-file-menu').click(); await page.getByTestId('workflow-file-open').waitFor(); }, [marker('workflow-file-menu', 'File')]);
  await step('Open workflow', 'Click Open workflow.', ['Open workflow'], `Existing ${attempt} is listed.`, async () => { await page.getByTestId('workflow-file-open').click(); await page.getByTestId(`workflow-file-choice-${workflow}`).waitFor({ timeout: 60000 }); await page.getByTestId(`workflow-file-choice-${workflow}`).scrollIntoViewIfNeeded(); }, [marker('workflow-file-open', 'Open workflow')]);
  await step('Select exact attempt', `Choose ${workflow}`, [workflow], `${attempt} opens with its recorded pending review loaded.`, async () => { await page.getByTestId(`workflow-file-choice-${workflow}`).click(); await runDetails().waitFor({ timeout: 60000 }); await expect(runDetails()).toContainText('Awaiting your review', { timeout: 60000 }); }, [marker(`workflow-file-choice-${workflow}`, label)]);
  const workflowTab = () => page.getByRole('tab', { name: new RegExp(`validator-082-robot-tracking-diagnosis-01-${attempt}`, 'i') });
  const inputId = `workflow-recovery-block-block.campaign-human-context-robot-tracking-diagnosis-01-${attempt}`;
  await step('Input meaning', 'Select human context.', ['human context'], 'Input purpose, full selected path, and Open file are visible.', async () => {
    await page.getByTestId(inputId).click();
    await expect(page.getByTestId('workflow-engineering-step-context')).toContainText('What this input supplies');
    await expect(page.getByTestId('workflow-recovery-input-open')).toBeVisible();
  }, [marker(inputId, 'Input source')]);
  await step('Open input', 'Hover over the selected file, then click Open file.', ['Workspace file', 'Open file'], 'The exact input file opens in a selected workspace tab without editing the workflow.', async () => {
    const selected = await page.getByTestId('workflow-recovery-input-selected-path').innerText();
    await expect(page.getByTestId('workflow-recovery-input-select')).toHaveAttribute('title', selected);
    await page.getByTestId('workflow-recovery-input-select').hover();
    await page.getByTestId('workflow-recovery-input-open').click();
    await expect(page.getByRole('tab', { name: new RegExp(selected.split('/').at(-1).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')) })).toHaveAttribute('aria-selected', 'true');
    await expect(page.getByTestId('markdown-viewer').locator('article')).toBeVisible();
  }, [marker('workflow-recovery-input-open', 'Open the selected file')]);
  await step('Return to workflow', `Select the ${label} workflow tab.`, [label], 'The same workflow and pending review are retained.', async () => { await workflowTab().click(); await runDetails().waitFor(); });
  if (attempt === 'attempt-009') {
    await step('Results without Run details', 'Collapse Run details if open, then open Results.', ['Results'], 'Five result groups are visible; four contain recorded files. No review or execution is needed to view them.', async () => {
      if (await page.getByTestId('workflow-external-approval').isVisible()) await runDetails().click();
      await expect(page.getByTestId('workflow-results-toggle').filter({visible:true})).toContainText('4/5 available');
      await page.getByTestId('workflow-results-toggle').filter({visible:true}).click();
      await expect(page.getByRole('region', {name:'Workflow results'})).toContainText('Not produced yet');
    }, [marker('workflow-results-toggle', 'Results — as accessible as Inputs')]);
    await step('Find plots on the diagram', 'Select Plots and supporting data in Results.', ['Plots and supporting data'], 'A teal RESULT block and the result viewer show the recorded plot and direct Open in tab action.', async () => {
      await page.getByRole('region', {name:'Workflow results'}).getByRole('button', {name:/Plots and supporting data/}).click();
      const inspector = page.getByTestId('workflow-result-inspector');
      await expect(inspector).toBeVisible();
      await expect(inspector).toContainText('Includes files awaiting review');
      await expect(inspector.locator('img')).toBeVisible();
      await expect.poll(() => inspector.locator('img').evaluate(img => img.complete && img.naturalWidth > 0)).toBe(true);
      await expect(page.locator('.recovery-result-block.is-selected')).toContainText('View results');
      await resultIsInsideCanvas();
    });
    await step('Result block opens its viewer', 'Close the result viewer, then click View results on the selected block.', ['Collapse Inspector', 'View results'], 'The result block directly opens its files without using Run details.', async () => {
      await page.getByTestId('workflow-recovery-inspector-close').filter({visible:true}).click();
      await page.locator('.recovery-result-block.is-selected').getByRole('button', {name:/View results/}).click();
      await expect(page.getByTestId('workflow-result-inspector')).toBeVisible();
    });
    await step('Open result full size', 'Click Open plot or image in tab.', ['Open plot or image in tab'], 'The plot opens in a workspace tab with a rendered image.', async () => {
      await page.getByTestId('workflow-result-open').click();
      await expect(page.getByRole('tab', {name:/trajectory-overlay.svg/})).toHaveAttribute('aria-selected','true');
      await expect.poll(() => page.locator('img').evaluateAll(images => images.some(img => img.currentSrc.includes('trajectory-overlay.svg') && img.complete && img.naturalWidth > 0))).toBe(true);
    }, [marker('workflow-result-open', 'Open this result in a tab')]);
    await step('Return from plot', 'Select the workflow tab.', [label], 'Result viewer selection and pending review are retained.', async () => { await workflowTab().click(); await expect(page.getByTestId('workflow-result-inspector')).toBeVisible(); });
    for (const width of [1060, 752]) {
      await step(`Results at ${width} pixels`, `Resize to ${width} × 791; inspect result access.`, ['Results', 'Open plot or image in tab'], 'Result viewer and direct opening remain usable without horizontal overflow.', async () => {
        await page.setViewportSize({width, height:791});
        await expect(page.getByTestId('workflow-result-open')).toBeVisible();
        await expect.poll(() => page.getByTestId('workflow-result-inspector').evaluate(el => el.scrollWidth - el.clientWidth)).toBeLessThanOrEqual(2);
        await expect(page.getByTestId('workflow-results-toggle').filter({visible:true})).toBeVisible();
        await resultIsInsideCanvas();
      });
    }
    await step('Expected final result is honest', 'Open Results, then select Evidence index.', ['Results', 'Evidence index'], 'The final result says Not produced yet and cannot open a nonexistent file.', async () => {
      await page.getByTestId('workflow-results-toggle').filter({visible:true}).click();
      await page.getByRole('region', {name:'Workflow results'}).getByRole('button', {name:/Evidence index/}).click();
      await expect(page.getByTestId('workflow-result-inspector')).toContainText('Not produced yet');
      await expect(page.getByTestId('workflow-result-open')).toHaveCount(0);
      await expect(page.getByTestId('workflow-result-inspector').getByRole('button', {name:/evidence-index.md/})).toBeDisabled();
    });
    await step('Open diagnosis through Results', 'Choose Diagnosis under Results, then open the document.', ['Results', 'Diagnosis', 'Open document in tab'], 'The diagnosis is directly accessible through Results and renders as a readable report.', async () => {
      await page.getByTestId('workflow-results-toggle').filter({visible:true}).click();
      await page.getByRole('region', {name:'Workflow results'}).getByRole('button', {name:/^Diagnosis/}).click();
      await page.getByTestId('workflow-result-open').click();
      await expect(page.getByRole('heading', {name:/What remains unknown/i})).toBeVisible();
    });
    await step('Return to review controls', 'Return to the workflow and restore 944 × 791.', [label], 'The existing review remains pending.', async () => {
      await workflowTab().click(); await page.setViewportSize({width:944, height:791});
      await page.getByTestId('workflow-recovery-inspector-close').filter({visible:true}).click();
    });
  }
  await step('Run details', 'Open Run details if collapsed.', ['Run details'], 'Awaiting your review is shown; three engineering requirements are readable and technical records are closed.', async () => {
    if (!(await page.getByTestId('workflow-external-approval').isVisible())) await runDetails().click();
    const panel = page.getByTestId('workflow-external-approval'); await panel.waitFor({ timeout: 60000 });
    await expect(runDetails()).toContainText('Awaiting your review');
    await expect(page.getByTestId('workflow-approval-technical-record')).not.toHaveAttribute('open', '');
    await expect(page.getByTestId('workflow-validation-review-requirements').locator(':scope > li')).toHaveCount(3);
    const body = await panel.innerText();
    for (const value of ['campaign runner', digest, 'ROBOT01-ACTION-SCOPE', '"server"', 'tests/datasets']) if (body.includes(value)) throw new Error(`Technical content leaked into ordinary review: ${value}`);
    writeFileSync(path.join(walkthroughRoot, 'trace/review-text.txt'), body);
  }, [marker('workflow-recovery-run-details-toggle', 'Run details')]);
  await step('Readable review area', 'Click Expand details.', ['Expand details'], 'The review area grows and stays within the viewport width.', async () => {
    await page.getByTestId('workflow-recovery-run-details-expand').click();
    await expect(page.getByTestId('workflow-recovery-run-drawer').filter({ visible: true })).toHaveClass(/is-expanded/);
    const overflow = await page.getByTestId('workflow-recovery-run-drawer').filter({ visible: true }).evaluate(el => el.scrollWidth - el.clientWidth);
    if (overflow > 2) throw new Error(`Run details overflow horizontally by ${overflow}px`);
  }, [marker('workflow-recovery-run-details-expand', 'Expand review area')]);
  await step('See the engineering evidence', 'Scroll to Results to inspect.', ['Results to inspect'], 'Recorded plots render inline; findings are directly accessible and calculation records stay collapsed.', async () => {
    const files = page.getByTestId('workflow-review-files');
    await files.scrollIntoViewIfNeeded();
    await expect.poll(() => files.locator('img').evaluateAll(images => images.length > 0 && images.every(img => img.complete && img.naturalWidth > 0))).toBe(true);
    await expect(files.getByRole('alert')).toHaveCount(0);
    await expect(files.locator('details')).not.toHaveAttribute('open', '');
    if (attempt === 'attempt-009') {
      await expect(files.getByTestId('workflow-review-image')).toHaveCount(2);
      await expect(page.getByTestId('workflow-run-purpose')).toContainText('floor-seam crossing');
      await expect(files.getByRole('button', { name: 'Open plot-guide.md', exact: true })).toBeVisible();
    }
  });
  const reviewNames = attempt === 'attempt-009' ? ['diagnosis.md', 'trajectory-overlay.svg', 'alignment-comparison.svg', 'plot-guide.md'] : ['diagnosis.md', 'trajectory-overlay.svg'];
  for (const filename of reviewNames) {
    const controlLabel = filename.endsWith('.svg') ? 'Open full-size image' : 'Open file';
    await step(`Open ${filename}`, `Click ${controlLabel} beside ${filename}.`, [filename, controlLabel], `${filename} opens in its own selected workspace tab.`, async () => {
      await page.getByTestId('workflow-review-files').getByRole('button', { name: `Open ${filename}`, exact: true }).click();
      await expect(page.getByRole('tab', { name: new RegExp(filename.replace('.', '\\.')) })).toHaveAttribute('aria-selected', 'true');
      if (filename.endsWith('.md')) {
        await expect(page.getByTestId('markdown-viewer').filter({ visible: true }).locator('article')).toBeVisible();
        if (attempt === 'attempt-009' && filename === 'diagnosis.md') {
          await expect(page.getByRole('heading', { name: /What remains unknown/i })).toBeVisible();
          await expect(page.getByRole('heading', { name: /Next inexpensive test/i })).toBeVisible();
        }
      } else await expect.poll(() => page.locator('img').evaluateAll((images, filename) => images.some(img => img.currentSrc.includes(filename) && img.complete && img.naturalWidth > 0), filename)).toBe(true);
      await expect(page.getByText(/Failed to (load|open)|Unable to (load|open)/)).toHaveCount(0);
    });
    await step('Return to review', `Select the ${label} workflow tab.`, [label], 'The existing review is unchanged.', async () => { await workflowTab().click(); await runDetails().waitFor(); });
  }
  await step('Engineering checks', 'Scroll to Check these 3 requirements.', ['Check these 3 requirements'], 'The complete engineering requirements are readable without hashes, repository paths, or JSON.', async () => {
    await page.getByTestId('workflow-validation-review-requirements').scrollIntoViewIfNeeded();
    await expect(page.getByTestId('workflow-validation-review-requirements')).toContainText('does not claim wheel slip');
  });
  await step('Traceability remains available', 'Open Technical record, inspect it, then close it.', ['Technical record'], 'The exact review fingerprint and requirement identifiers remain available on demand.', async () => {
    const technical = page.getByTestId('workflow-approval-technical-record');
    await technical.locator('summary').click();
    await expect(technical).toContainText(digest);
    await expect(technical).toContainText('ROBOT01-DIAGNOSIS');
    await capture('technical-record', 'Optional technical record', []);
    await technical.locator('summary').click();
  });
  await step('Inspect a calculation step', 'Open Step progress and select Align samples and calculate tracking metrics.', ['Step progress', 'Align samples and calculate tracking metrics'], 'The inspector explains the step, upstream inputs, and exact files produced in this run.', async () => {
    const progress = page.getByTestId('workflow-engineering-run-progress');
    await progress.locator('summary').click();
    await progress.getByRole('button', { name: 'Align samples and calculate tracking metrics', exact: true }).click();
    await expect(page.getByTestId('workflow-engineering-step-context')).toContainText('Files produced in this run');
    await expect(page.getByTestId('workflow-engineering-step-context')).toContainText('Uses information from');
  });
  await step('See the process connections', 'Collapse Run details and fit the diagram.', ['Run details', 'Fit diagram'], 'The process diagram is visible for connection inspection.', async () => {
    await runDetails().click();
    await page.getByTestId('workflow-recovery-canvas-fit').filter({ visible: true }).click();
  });
  await step('Connection meaning', 'Focus the bounded typed samples connection and press Enter.', ['Select connection bounded typed samples'], 'The inspector explains this line sets step order, not an input-file transfer.', async () => {
    const connection = page.getByRole('button', { name: 'Select connection bounded typed samples', exact: true });
    await connection.focus();
    await connection.press('Enter');
    await expect(page.getByTestId('workflow-engineering-connection-context')).toContainText('This line does not carry an input file');
    await expect(page.getByTestId('workflow-engineering-connection-context')).toContainText('Inspect bag and topic schemas');
  });
  const after = await runIdentity();
  writeFileSync(path.join(walkthroughRoot, 'trace/after-run.json'), JSON.stringify(after, null, 2));
  expect(after).toEqual(before);
  const significant = diagnostics.filter(d => d.type === 'pageerror' || d.type === 'blocked-mutation' || (d.type === 'http' && d.status >= 400));
  if (significant.length) throw new Error(`Browser diagnostics need review: ${JSON.stringify(significant)}`);
  status.overall = 'pass'; status.summary = `${attempt === 'attempt-009' ? 'Read-only result blocks, direct plot/report tabs, inline plot preview, honest unproduced files, and result access at 1060 and 752 pixels verified. ' : ''}Input files, engineering review, rendered report and plot, optional traceability, and step/connection inspection verified at 944 × 791 with no console or page errors. The run and pending decision are unchanged; no approval or resume was submitted.`;
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
