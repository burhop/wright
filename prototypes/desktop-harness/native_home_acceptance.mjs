// Read-only owner integration; simulated MCP App host, not Windows acceptance.
// Reuses native_editor_acceptance.mjs's official SDK iframe handshake.
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { chromium, expect } from '@playwright/test';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

const state = resolve(process.argv[2]);
const evidence = JSON.parse(readFileSync(resolve(state, process.argv[3] ?? 'home-probe.json')));
const preview = JSON.parse(readFileSync(resolve(state, 'preview.json')));
const token = readFileSync(resolve(state, '.preview-api-token'), 'utf8');
const bundle = readFileSync('prototypes/desktop-harness/native-editor.html', 'utf8');
const output = resolve(state, `browser-home-${Date.now()}`);
mkdirSync(output);
const calls = [];
let createdScope;
let uploadedInput;
let uploadSubmitted = false;
let transferSubmitted = false;
let transferredWorkflow;
let createSubmitted = false;
let createdWorkflow;
let workflowSubmitted = false;
const templateCopies = new Map();
const mcp = new Client({name:'wright-home-browser-qualification',version:'0.1.0'});
const transport = new StdioClientTransport({
 command:process.env.WRIGHT_PROBE_PYTHON ?? resolve('.venv/bin/python'),
 args:[resolve('prototypes/desktop-harness/mcp_bridge.py'),'--state-dir',state,'--native-editor',...(evidence.native_working_view === false ? [] : ['--native-working-view'])],
 stderr:'pipe',
});
// Keep transport diagnostics out of the browser and evidence; retain only test failures.
await mcp.connect(transport);
const safe = value => JSON.stringify(value).replaceAll('<', '\\u003c');
async function get(path, params = {}) {
  const url = new URL(path, preview.api_url);
  for (const [key, value] of Object.entries(params)) url.searchParams.set(key, value);
  const response = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (!response.ok) throw Error(`Owner read failed: ${response.status}`);
  return response.json();
}
async function source() {
  return get('/api/workspace/workflow-sources', {
    session_id: evidence.scope.session_id, path: evidence.scope.path,
  });
}
const before = await source();
const fixture = `<!doctype html><html><body style="margin:0;background:#181818;color:#ddd;font:13px system-ui"><div style="height:32px;padding-left:12px">GB10 browser preview · simulated desktop host · real Wright storage · no engineering run</div><iframe id="panel" title="Wright" style="border:0;width:100%;height:calc(100vh - 32px)"></iframe><script>
const frame = document.getElementById('panel');
window.addEventListener('message', async event => {
 if (event.source !== frame.contentWindow) return;
 const m = event.data;
 const send = data => frame.contentWindow.postMessage({jsonrpc:'2.0', ...data}, '*');
 if (m.method === 'ui/initialize') send({id:m.id,result:{protocolVersion:'2026-01-26',hostInfo:{name:'wright-browser-fixture',version:'0.1.0'},hostCapabilities:{serverTools:{}},hostContext:{theme:'dark'}}});
 if (m.method === 'ui/notifications/initialized') {
  send({method:'ui/notifications/tool-input',params:{arguments:{}}});
  send({method:'ui/notifications/tool-result',params:{content:[],structuredContent:{view:'home'}}});
 }
 if (m.method === 'tools/call') {
  try { const r = await fetch('/tool', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(m.params)}); send({id:m.id,result:await r.json()}); }
  catch { send({id:m.id,error:{code:-32000,message:'Fixture unavailable'}}); }
 }
}); frame.srcdoc = ${safe(bundle)};
</script></body></html>`;
const server = createServer(async (req, res) => {
  try {
    if (req.method === 'GET' && req.url === '/') {
      res.writeHead(200, {'Content-Type':'text/html;charset=utf-8'}); res.end(fixture); return;
    }
    if (req.method !== 'POST' || req.url !== '/tool') throw Error('Fixture route denied');
    let body = ''; for await (const chunk of req) body += chunk;
    const {name, arguments: args} = JSON.parse(body);
    calls.push({name, arguments:args});
    const allowed = new Set(['wright_workflow_templates','wright_workspace_list','wright_workspace_files','wright_workspace_file_preview','wright_workflow_read','wright_workflow_open','wright_connections_list','wright_connection_plans','wright_connection_plan_read','wright_workflow_history','wright_process_view','wright_process_ui_read']);
    if (name === 'wright_workspace_create') {
      if (!evidence.create_workspace || createSubmitted || args.name !== evidence.create_workspace)
        throw Error('Fixture creation denied');
      createSubmitted = true;
      const result = await mcp.callTool({name,arguments:args});
      if (!result.isError) createdScope = result.structuredContent ?? JSON.parse(result.content[0].text);
      res.writeHead(200, {'Content-Type':'application/json'}); res.end(JSON.stringify(result)); return;
    }
    if (name === 'wright_workflow_create') {
      if (!evidence.create_workflow || workflowSubmitted || !createdScope || args.workspace_id !== createdScope.workspace_id || args.session_id !== createdScope.session_id || !args.source.includes(JSON.stringify(evidence.create_workflow)))
        throw Error('Fixture workflow creation denied');
      workflowSubmitted = true;
      const result = await mcp.callTool({name,arguments:args});
      if (!result.isError) createdWorkflow = result.structuredContent ?? JSON.parse(result.content[0].text);
      res.writeHead(200, {'Content-Type':'application/json'}); res.end(JSON.stringify(result)); return;
    }
    if (name === 'wright_workflow_template_create') {
      if (!evidence.template_ids?.includes(args.template_id) || templateCopies.has(args.template_id) || !createdScope || args.workspace_id !== createdScope.workspace_id || args.session_id !== createdScope.session_id)
        throw Error('Fixture template copy denied');
      const result = await mcp.callTool({name,arguments:args});
      if (!result.isError) templateCopies.set(args.template_id, result.structuredContent ?? JSON.parse(result.content[0].text));
      res.writeHead(200, {'Content-Type':'application/json'}); res.end(JSON.stringify(result)); return;
    }
    if (name === 'wright_process_ui_update' && evidence.input_upload) {
      const r = args.request;
      const expected = { ...evidence.scope, expected_storage_digest: before.storage_digest,
        operation:'upload', input_id:evidence.input_upload.input_id,
        filename:evidence.input_upload.filename,
        bytes_base64:Buffer.from(evidence.input_upload.text).toString('base64') };
      if (uploadSubmitted || !r || Object.keys(r).length !== Object.keys(expected).length ||
          Object.entries(expected).some(([key,value]) => r[key] !== value))
        throw Error('Fixture permits one exact synthetic declared-input upload');
      uploadSubmitted = true;
      const result = await mcp.callTool({name,arguments:args});
      if (!result.isError && result.structuredContent?.ok) uploadedInput = result.structuredContent.document;
      res.writeHead(200, {'Content-Type':'application/json'}); res.end(JSON.stringify(result)); return;
    }
    if (evidence.transfer_destination && ['wright_workflow_export','wright_workflow_transfer_assets','wright_workflow_import_inspect','wright_workflow_import'].includes(name)) {
      const r = args.request;
      if (!r || r.workspace_id !== evidence.scope.workspace_id || r.session_id !== evidence.scope.session_id)
        throw Error('Transfer fixture scope denied');
      if (['wright_workflow_export','wright_workflow_transfer_assets'].includes(name) &&
          (r.path !== evidence.scope.path || r.expected_storage_digest !== before.storage_digest))
        throw Error('Transfer fixture source denied');
      if (['wright_workflow_import_inspect','wright_workflow_import'].includes(name) &&
          (r.destination_path !== evidence.transfer_destination || r.bundle?.source !== before.source))
        throw Error('Transfer fixture destination or source denied');
      if (name === 'wright_workflow_import') {
        if (transferSubmitted) throw Error('Transfer fixture denies repeated import');
        transferSubmitted = true;
      }
      const result = await mcp.callTool({name,arguments:args});
      if (name === 'wright_workflow_import' && result.structuredContent?.ok)
        transferredWorkflow = result.structuredContent.document.source;
      if (name === 'wright_workflow_import' && transferredWorkflow && evidence.lose_import_reply) {
        res.writeHead(200, {'Content-Type':'application/json'});
        res.end(JSON.stringify({content:[{type:'text',text:'Private fixture: import reply lost'}],isError:true})); return;
      }
      res.writeHead(200, {'Content-Type':'application/json'}); res.end(JSON.stringify(result)); return;
    }
    if (!allowed.has(name)) throw Error('Read-only fixture denies this operation');
    const scoped = args.request ?? args;
    if (name !== 'wright_workspace_list' &&
        (scoped.workspace_id !== evidence.scope.workspace_id || scoped.session_id !== evidence.scope.session_id) &&
        !(createdScope && scoped.workspace_id === createdScope.workspace_id && scoped.session_id === createdScope.session_id && (['wright_workspace_files','wright_workflow_templates'].includes(name) || (['wright_workflow_read','wright_workflow_open'].includes(name) && (args.path === createdWorkflow?.path || [...templateCopies.values()].some(copy => copy.path === args.path))))))
      throw Error('Fixture scope denied');
    if (name === 'wright_workspace_file_preview' && ![evidence.scope.path, evidence.preview_path].includes(args.path))
      throw Error('Fixture preview file denied');
    if (name.startsWith('wright_workflow_') && name !== 'wright_workflow_templates' && args.path !== evidence.scope.path && args.path !== transferredWorkflow?.path && args.path !== createdWorkflow?.path && ![...templateCopies.values()].some(copy => copy.path === args.path))
      throw Error('Fixture file denied');
    if (name.startsWith('wright_process_') &&
        (scoped.path !== evidence.scope.path || scoped.operation !== 'snapshot' || scoped.run_id !== evidence.run_id))
      throw Error('Fixture permits only the exact saved run snapshot');
    const result = await mcp.callTool({name,arguments:args});
    res.writeHead(200, {'Content-Type':'application/json'});
    res.end(JSON.stringify(result));
  } catch (error) {
    res.writeHead(400, {'Content-Type':'application/json'});
    res.end(JSON.stringify({content:[{type:'text',text:error.message}],isError:true}));
  }
});
await new Promise(done => server.listen(0, '127.0.0.1', done));
const browser = await chromium.launch({headless:true});
const passed = [], errors = [];
let page;
try {
  page = await browser.newPage({viewport:{width:1100,height:820}});
  page.setDefaultTimeout(15000);
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(`http://127.0.0.1:${server.address().port}`);
  const frame = page.frameLocator('#panel');
  if (evidence.create_workspace) {
    await frame.getByRole('button',{name:'New workspace',exact:true}).click();
    await frame.getByLabel('Workspace name',{exact:true}).fill(evidence.create_workspace);
    await frame.getByRole('button',{name:'Create workspace',exact:true}).click();
    await expect(frame.getByText('No saved workflows here yet. Choose New workflow or ask this conversation to create one.',{exact:true})).toBeVisible();
    expect(createdScope).toBeTruthy();
    await expect(frame.getByLabel('Workspace',{exact:true})).toHaveValue(createdScope.workspace_id);
    expect(calls.filter(call=>call.name==='wright_workspace_create')).toHaveLength(1);
    await page.screenshot({path:resolve(output,'created-workspace.png')});
    passed.push('explicit UI workspace creation once, discovered exact session, no workflow execution');
    if (evidence.create_workflow) {
      await frame.getByRole('button',{name:'New workflow',exact:true}).click();
      await frame.getByLabel('Workflow name',{exact:true}).fill(evidence.create_workflow);
      await frame.getByRole('button',{name:'Create workflow',exact:true}).click();
      await expect(frame.getByTestId('workflow-recovery-save')).toBeVisible();
      expect(createdWorkflow.workspace_id).toBe(createdScope.workspace_id);
      const stored = await get('/api/workspace/workflow-sources',{session_id:createdScope.session_id,path:createdWorkflow.path});
      expect(stored.storage_digest).toBe(createdWorkflow.storage_digest);
      expect(stored.source).toBe(createdWorkflow.source);
      expect(calls.filter(call=>call.name==='wright_workflow_create')).toHaveLength(1);
      await page.screenshot({path:resolve(output,'created-workflow-editor.png')});
      await frame.getByRole('button',{name:'← Workspace home',exact:true}).click();
      await expect(frame.getByLabel('Workspace',{exact:true})).toHaveValue(createdScope.workspace_id);
      await frame.getByRole('button',{name:createdWorkflow.path.split('/').at(-1),exact:true}).click();
      await expect(frame.getByTestId('workflow-recovery-save')).toBeVisible();
      await frame.getByRole('button',{name:'← Workspace home',exact:true}).click();
      passed.push('native New workflow saves once through source owner, opens shared editor and reopens from Workflows with exact digest');
    }

  }
  for (const templateId of evidence.template_ids ?? []) {
    await frame.getByRole('button',{name:'Use a template',exact:true}).click();
    await frame.getByTestId('workflow-template-option-'+templateId).click();
    await expect(frame.getByTestId('workflow-template-readiness')).not.toContainText('Ready to run');
    await expect(frame.getByText('Template image preview is not available in this host yet.',{exact:true})).toBeVisible();
    for (const width of [460, 1100]) {
      await page.setViewportSize({width,height:820});
      const layout = await frame.locator('.engineering-template-dialog').evaluate(dialog => {
        const header=dialog.querySelector('header').getBoundingClientRect();
        const footer=dialog.querySelector('footer').getBoundingClientRect();
        const rect=dialog.getBoundingClientRect();
        return {headerInside:header.top>=rect.top && header.bottom<=rect.bottom,footerInside:footer.top>=rect.top && footer.bottom<=rect.bottom,horizontalOverflow:dialog.scrollWidth>dialog.clientWidth+1};
      });
      expect(layout).toEqual({headerInside:true,footerInside:true,horizontalOverflow:false});
      await page.screenshot({path:resolve(output,templateId+'-picker-'+width+'.png')});
    }
    await page.screenshot({path:resolve(output,templateId+'-picker.png')});
    await frame.getByTestId('workflow-template-create').click();
    await expect(frame.getByTestId('workflow-recovery-save')).toBeVisible();
    const copy = templateCopies.get(templateId);
    expect(copy.workspace_id).toBe(createdScope.workspace_id);
    const stored = await get('/api/workspace/workflow-sources',{session_id:createdScope.session_id,path:copy.path});
    expect(stored.storage_digest).toBe(copy.storage_digest);
    expect(stored.source).toBe(copy.source);
    expect(calls.filter(call=>call.name==='wright_workflow_template_create' && call.arguments.template_id===templateId)).toHaveLength(1);
    await page.screenshot({path:resolve(output,templateId+'-editor.png')});
    await frame.getByRole('button',{name:'← Workspace home',exact:true}).click();
    await expect(frame.getByRole('button',{name:copy.path.split('/').at(-1),exact:true})).toBeVisible();
    passed.push(templateId+': explicit template copy, exact saved source/digest and shared editor; no execution');
  }
  await frame.getByLabel('Workspace', {exact:true}).selectOption(evidence.scope.workspace_id);
  const workflow = frame.getByRole('button', {name:evidence.scope.path.split('/').at(-1),exact:true});
  await expect(workflow).toBeVisible();
  await page.screenshot({path:resolve(output, 'home.png')});
  passed.push('real isolated workspace and saved workflow source discovered');
  await workflow.click();
  await expect(frame.getByTestId('workflow-recovery-save')).toBeVisible();
  await page.screenshot({path:resolve(output, 'editor.png')});
  if (evidence.transfer_destination) {
    await frame.getByRole('button',{name:'Export / import workflow',exact:true}).click();
    const dialog = frame.getByTestId('workflow-transfer-dialog');
    await expect(dialog).toBeVisible();
    for (const width of [460, 1100]) {
      await page.setViewportSize({width,height:820});
      expect(await dialog.evaluate(el => el.scrollWidth > el.clientWidth + 1)).toBe(false);
      await expect(frame.getByTestId('workflow-transfer-close')).toBeInViewport();
      await page.screenshot({path:resolve(output,'transfer-'+width+'.png')});
    }
    await frame.getByTestId('workflow-transfer-mode').selectOption('bundle');
    await frame.getByTestId('workflow-transfer-list-assets').click();
    await expect(frame.getByTestId('workflow-transfer-list-assets')).toBeEnabled();
    await expect(frame.getByTestId('workflow-transfer-file-inputs/private-transfer-proof.txt')).toHaveCount(0);
    await frame.getByTestId('workflow-transfer-mode').selectOption('source');
    const downloadEvent = page.waitForEvent('download');
    await frame.getByTestId('workflow-transfer-export').click();
    const download = await downloadEvent;
    const transferPath = resolve(output,download.suggestedFilename());
    await download.saveAs(transferPath);
    const exported = JSON.parse(readFileSync(transferPath,'utf8'));
    expect(exported.bundle.source).toBe(before.source);
    await frame.getByTestId('workflow-transfer-upload').setInputFiles(transferPath);
    await frame.getByTestId('workflow-transfer-destination').fill(evidence.transfer_destination);
    await frame.getByTestId('workflow-transfer-inspect').click();
    await expect(frame.getByText('Definition can be imported',{exact:true})).toBeVisible();
    await page.screenshot({path:resolve(output,'transfer-inspected.png')});
    await frame.getByTestId('workflow-transfer-import').click();
    if (evidence.lose_import_reply) {
      await expect(frame.getByRole('button',{name:'Open saved destination',exact:true})).toBeVisible();
      await expect(frame.getByTestId('workflow-transfer-import')).toBeEnabled();
      await frame.getByTestId('workflow-transfer-import').click();
      await expect(frame.getByRole('alert')).toContainText('no import was repeated');
      expect(calls.filter(call=>call.name==='wright_workflow_import')).toHaveLength(1);
      await page.screenshot({path:resolve(output,'transfer-uncertain-reply.png')});
      await frame.getByRole('button',{name:'Open saved destination',exact:true}).click();
      passed.push('lost import acknowledgement retained; repeat submission blocked locally; explicit read-only destination recovery without replay');
    }
    await expect(dialog).toHaveCount(0);
    await expect(frame.getByTestId('workflow-recovery-save')).toBeVisible();
    await expect.poll(() => transferredWorkflow?.path).toBe(evidence.transfer_destination);
    const stored = await get('/api/workspace/workflow-sources',{session_id:evidence.scope.session_id,path:evidence.transfer_destination});
    expect(stored.source).toBe(before.source);
    expect(calls.filter(call=>call.name==='wright_workflow_import')).toHaveLength(1);
    expect(calls.some(call=>call.name==='wright_workflow_open' && call.arguments.path===evidence.transfer_destination)).toBe(true);
    await page.screenshot({path:resolve(output,'transfer-imported-editor.png')});
    passed.push('native transfer dialog fits narrow host; real browser download, unrelated reference excluded, inspection and one import return to exact saved source; Windows delivery unverified');
    await frame.getByRole('button',{name:'← Workspace home',exact:true}).click();
    await workflow.click();
    await expect(frame.getByTestId('workflow-recovery-save')).toBeVisible();
  }
  await frame.getByRole('button',{name:'← Workspace home',exact:true}).click();
  await expect(frame.getByLabel('Workspace',{exact:true})).toBeVisible();
  await expect(frame.getByLabel('Workspace',{exact:true})).toHaveValue(evidence.scope.workspace_id);
  await expect(workflow).toBeVisible();
  passed.push('home opens shared editor and Back restores exact workspace without mutation');
  await frame.getByRole('button',{name:'Files',exact:true}).click();
  await frame.getByRole('button',{name:'Refresh',exact:true}).click();
  await expect(frame.getByLabel('Workspace',{exact:true})).toHaveValue(evidence.scope.workspace_id);
  await expect(workflow).toBeVisible();
  await expect(frame.getByLabel('Find a file')).toBeVisible();
  passed.push('Refresh reconciles exact workspace/session and retains Files view without execution');
  await expect(frame.getByText('/'+evidence.scope.path,{exact:true})).toBeVisible();
  await frame.getByLabel('Find a file').fill('no-such-file-in-this-proof');
  await expect(frame.getByText('No files match this search.',{exact:true})).toBeVisible();
  await frame.getByLabel('Find a file').fill(evidence.scope.path.split('/').at(-1));
  await expect(frame.getByText('/'+evidence.scope.path,{exact:true})).toBeVisible();
  await expect(frame.getByText('Text previews support files up to 64 KiB; downloads support visible files up to 16 MiB. Other previews are unavailable here.',{exact:true})).toBeVisible();
  await page.screenshot({path:resolve(output,'files.png')});
  passed.push('Files lists and filters real scoped storage; unavailable operations explicit');
  if (evidence.expect_large_preview) {
    await frame.getByRole('button',{name:evidence.scope.path.split('/').at(-1),exact:true}).click();
    await expect(frame.getByText('Text preview is unavailable. Choose an existing workspace text file up to 64 KiB.',{exact:true})).toBeVisible();
    await frame.getByRole('button',{name:'Close preview',exact:true}).click();
    passed.push('oversized source preview explicitly unavailable; full shared editor remains available');
  }
  if (evidence.preview_text !== undefined) {
    const previewPath = evidence.preview_path ?? evidence.scope.path;
    await frame.getByLabel('Find a file').fill(previewPath.split('/').at(-1));
    await frame.getByRole('button',{name:previewPath.split('/').at(-1),exact:true}).click();
    await expect(frame.getByText('Read-only text preview · current saved file',{exact:true})).toBeVisible();
    expect(await frame.locator('section[aria-label="File preview"] pre').textContent()).toBe(evidence.preview_text);
    await page.screenshot({path:resolve(output,'file-preview.png')});
    await frame.getByRole('button',{name:'Close preview',exact:true}).click();
    await expect(frame.locator('section[aria-label="File preview"]')).toHaveCount(0);
    passed.push('explicit bounded text preview matches real saved bytes and closes without mutation');
  }
  if (!evidence.skip_connections) {
  await frame.getByRole('button',{name:'Connections',exact:true}).click();
  await frame.getByLabel('Find an MCP').fill('SteveCAD');
  await frame.getByRole('button',{name:'Search / refresh',exact:true}).click();
  await frame.getByRole('button',{name:/Saved setup for SteveCAD/i}).click();
  await frame.getByRole('button',{name:/Open reviewable setup/}).first().click();
  await expect(frame.getByText('Plan state: reviewable.',{exact:true})).toBeVisible();
  await page.screenshot({path:resolve(output,'saved-setup.png')});
  passed.push('real MCP catalog and saved-plan recovery; no setup mutations');
  }
  if (evidence.run_id) {
    await frame.getByRole('button',{name:'Recent runs',exact:true}).click();
    await frame.getByLabel('Workflow history').selectOption(evidence.scope.path);
    await expect(frame.getByText(evidence.run_id,{exact:true})).toBeVisible();
    await page.screenshot({path:resolve(output,'recent-runs.png')});
    await frame.getByRole('button',{name:'Inspect run',exact:true}).click();
    if (evidence.expect_stale) {
      await expect(frame.getByText("This run's source changed. Reopen its exact accepted workflow; no action was repeated.",{exact:true})).toBeVisible();
      await expect(frame.locator('.native-home')).toBeVisible();
      passed.push('changed source blocks exact-run navigation without substituting current source');
    } else {
    if (evidence.expected_review_decision) {
      await expect(frame.getByText('Review recorded: ' + evidence.expected_review_decision,{exact:true})).toBeVisible();
      if (evidence.expected_review_decision === 'Changes requested') {
        await expect(frame.getByRole('heading',{name:'Recorded review',exact:true})).toBeVisible();
        await expect(frame.getByRole('heading',{name:'Your next step',exact:true})).toHaveCount(0);
        await expect(frame.getByText('Paused at a review or response step',{exact:true})).toBeVisible();
        await expect(frame.getByText(/does not itself revise or restart/)).toBeVisible();
      }
    } else {
      await expect(frame.getByText('Process completed',{exact:true})).toBeVisible();
    }
    await expect(frame.getByRole('button',{name:'← Workspace home',exact:true})).toBeVisible();
    await expect(frame.locator('.native-home')).toHaveCount(0);
    await page.screenshot({path:resolve(output,'recorded-run.png')});
    if (evidence.expected_review_decision) {
      await frame.getByRole('heading',{name:'Recorded review',exact:true}).scrollIntoViewIfNeeded();
      await page.screenshot({path:resolve(output,'recorded-review.png')});
    }
    await frame.getByRole('button',{name:'← Workspace home',exact:true}).click();
    await expect(workflow).toBeVisible();
    passed.push('recorded run discovered and exact working view opened without execution');
    }
  }
  await frame.getByRole('button',{name:'Workflows',exact:true}).click();
  await page.setViewportSize({width:460,height:800});
  await frame.getByLabel('Workspace',{exact:true}).selectOption(evidence.scope.workspace_id);
  await expect(workflow).toBeVisible();
  const overflow = await frame.locator('html').evaluate(el => el.scrollWidth > el.clientWidth + 1);
  expect(overflow).toBe(false);
  await page.screenshot({path:resolve(output, 'home-narrow.png')});
  await workflow.click();
  await frame.getByTestId('workflow-recovery-view-select').selectOption('code');
  const editor = frame.getByTestId('workflow-recovery-source-editor');
  await editor.fill((await editor.inputValue()) + '\n# unsaved navigation test\n');
  await frame.getByRole('button',{name:'← Workspace home',exact:true}).click();
  await expect(frame.getByText('Your draft is kept. Save it before changing workspace.',{exact:true})).toBeVisible();
  await expect(editor).toHaveValue(/unsaved navigation test/);
  passed.push('narrow home fits; unsaved source draft prevents workspace navigation');
  expect((await source()).storage_digest).toBe(before.storage_digest);
  expect(errors).toEqual([]);
  passed.push('accepted source unchanged and no browser errors');
  if (evidence.input_upload) {
    // Start a fresh observer after the synthetic unsaved-draft guard test.
    // Replacing editor text is itself an edit, not an implicit discard action.
    await page.reload();
    await frame.getByLabel('Workspace',{exact:true}).selectOption(evidence.scope.workspace_id);
    await workflow.click();
    const working = frame.getByRole('button',{name:'Run and results',exact:true});
    await expect(working).toBeEnabled();
    await working.click();
    const picker = frame.getByLabel(evidence.input_upload.label,{exact:true});
    await expect(picker).toBeEnabled();
    await picker.setInputFiles({name:evidence.input_upload.filename,mimeType:'text/plain',buffer:Buffer.from(evidence.input_upload.text)});
    await expect.poll(() => uploadedInput?.artifact_ref).toMatch(/^\.wright\/process-inputs\//);
    await expect(frame.getByText('File attached: '+evidence.input_upload.filename,{exact:true})).toBeVisible();
    await expect(frame.getByText(/bitmap preview/i)).toHaveCount(0);
    await expect(frame.getByText(uploadedInput.artifact_ref,{exact:true})).not.toBeVisible();
    await frame.getByText('File details',{exact:true}).click();
    await expect(frame.getByText(uploadedInput.artifact_ref,{exact:true})).toBeVisible();
    await frame.getByText('File details',{exact:true}).click();
    // Recorded input identity is checked below; this proof never starts a process.
    expect(calls.filter(call=>call.name==='wright_process_ui_update')).toHaveLength(1);
    expect((await source()).storage_digest).toBe(before.storage_digest);
    expect(errors).toEqual([]);
    await page.screenshot({path:resolve(output,'declared-input-upload.png')});
    passed.push('existing common-view file picker uploads once, displays exact owner reference and preserves source; no process start');
  }
  writeFileSync(resolve(output,'report.json'),JSON.stringify({passed,errors,calls,uploaded_input:uploadedInput??null,boundary:'simulated MCP App host, actual MCP bridge; read-only navigation and optional explicit isolated workspace/workflow creation',native_desktop_verified:false,engineering_runs:0,template_copies:[...templateCopies.values()].map(copy=>({path:copy.path,storage_digest:copy.storage_digest,template:copy.template})),workspace_created:createdScope??null,workflow_created:createdWorkflow?{workspace_id:createdWorkflow.workspace_id,path:createdWorkflow.path,storage_digest:createdWorkflow.storage_digest}:null},null,2));
  console.log(JSON.stringify({output,passed}));
} catch (error) {
  if (page) await page.screenshot({path:resolve(output,'failure.png')});
  writeFileSync(resolve(output,'failure.json'),JSON.stringify({error:String(error),passed,errors,calls},null,2));
  throw error;
} finally {
  await browser.close();
  await mcp.close();
  await new Promise(done => server.close(done));
}
