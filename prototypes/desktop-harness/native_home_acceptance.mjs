// Read-only owner integration; simulated MCP App host, not Windows acceptance.
// Reuses native_editor_acceptance.mjs's official SDK iframe handshake.
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { chromium, expect } from '@playwright/test';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

const state = resolve(process.argv[2]);
const evidence = JSON.parse(readFileSync(resolve(state, 'home-probe.json')));
const preview = JSON.parse(readFileSync(resolve(state, 'preview.json')));
const token = readFileSync(resolve(state, '.preview-api-token'), 'utf8');
const bundle = readFileSync('prototypes/desktop-harness/native-editor.html', 'utf8');
const output = resolve(state, `browser-home-${Date.now()}`);
mkdirSync(output);
const calls = [];
let createdScope;
let createSubmitted = false;
const mcp = new Client({name:'wright-home-browser-qualification',version:'0.1.0'});
const transport = new StdioClientTransport({
 command:resolve('.venv/bin/python'),
 args:[resolve('prototypes/desktop-harness/mcp_bridge.py'),'--state-dir',state,'--native-editor','--native-working-view'],
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
    const allowed = new Set(['wright_workspace_list','wright_workspace_files','wright_workflow_read','wright_workflow_open','wright_connections_list','wright_connection_plans','wright_connection_plan_read','wright_workflow_history','wright_process_view','wright_process_ui_read']);
    if (name === 'wright_workspace_create') {
      if (!evidence.create_workspace || createSubmitted || args.name !== evidence.create_workspace)
        throw Error('Fixture creation denied');
      createSubmitted = true;
      const result = await mcp.callTool({name,arguments:args});
      if (!result.isError) createdScope = result.structuredContent ?? JSON.parse(result.content[0].text);
      res.writeHead(200, {'Content-Type':'application/json'}); res.end(JSON.stringify(result)); return;
    }
    if (!allowed.has(name)) throw Error('Read-only fixture denies this operation');
    const scoped = args.request ?? args;
    if (name !== 'wright_workspace_list' &&
        (scoped.workspace_id !== evidence.scope.workspace_id || scoped.session_id !== evidence.scope.session_id) &&
        !(name === 'wright_workspace_files' && createdScope && scoped.workspace_id === createdScope.workspace_id && scoped.session_id === createdScope.session_id))
      throw Error('Fixture scope denied');
    if (name.startsWith('wright_workflow_') && args.path !== evidence.scope.path)
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
    await expect(frame.getByText('No saved workflows here yet. Ask this conversation to create one.',{exact:true})).toBeVisible();
    expect(createdScope).toBeTruthy();
    await expect(frame.getByLabel('Workspace',{exact:true})).toHaveValue(createdScope.workspace_id);
    expect(calls.filter(call=>call.name==='wright_workspace_create')).toHaveLength(1);
    await page.screenshot({path:resolve(output,'created-workspace.png')});
    passed.push('explicit UI workspace creation once, discovered exact session, no workflow execution');
  }
  await frame.getByLabel('Workspace', {exact:true}).selectOption(evidence.scope.workspace_id);
  const workflow = frame.getByRole('button', {name:evidence.scope.path.split('/').at(-1),exact:true});
  await expect(workflow).toBeVisible();
  await page.screenshot({path:resolve(output, 'home.png')});
  passed.push('real isolated workspace and saved workflow source discovered');
  await workflow.click();
  await expect(frame.getByTestId('workflow-recovery-save')).toBeVisible();
  await page.screenshot({path:resolve(output, 'editor.png')});
  await frame.getByRole('button',{name:'Workspaces',exact:true}).click();
  await expect(frame.getByLabel('Workspace',{exact:true})).toBeVisible();
  await expect(frame.getByLabel('Workspace',{exact:true})).toHaveValue(evidence.scope.workspace_id);
  await expect(workflow).toBeVisible();
  passed.push('home opens shared editor and Back restores exact workspace without mutation');
  await frame.getByRole('button',{name:'Files',exact:true}).click();
  await expect(frame.getByText('/'+evidence.scope.path,{exact:true})).toBeVisible();
  await frame.getByLabel('Find a file').fill('no-such-file-in-this-proof');
  await expect(frame.getByText('No files match this search.',{exact:true})).toBeVisible();
  await frame.getByLabel('Find a file').fill(evidence.scope.path.split('/').at(-1));
  await expect(frame.getByText('/'+evidence.scope.path,{exact:true})).toBeVisible();
  await expect(frame.getByText('File preview, upload and download are not available in this panel yet.',{exact:true})).toBeVisible();
  await page.screenshot({path:resolve(output,'files.png')});
  passed.push('Files lists and filters real scoped storage; unavailable operations explicit');
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
    await expect(frame.getByText('Process completed',{exact:true})).toBeVisible();
    await expect(frame.getByRole('button',{name:'Workspaces',exact:true})).toBeVisible();
    await expect(frame.locator('.native-home')).toHaveCount(0);
    await page.screenshot({path:resolve(output,'recorded-run.png')});
    await frame.getByRole('button',{name:'Workspaces',exact:true}).click();
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
  await frame.getByRole('button',{name:'Workspaces',exact:true}).click();
  await expect(frame.getByText('Your draft is kept. Save it before changing workspace.',{exact:true})).toBeVisible();
  await expect(editor).toHaveValue(/unsaved navigation test/);
  passed.push('narrow home fits; unsaved source draft prevents workspace navigation');
  expect((await source()).storage_digest).toBe(before.storage_digest);
  expect(errors).toEqual([]);
  passed.push('accepted source unchanged and no browser errors');
  writeFileSync(resolve(output,'report.json'),JSON.stringify({passed,errors,calls,boundary:'simulated MCP App host, actual MCP bridge; read-only navigation and optional explicit isolated workspace creation',native_desktop_verified:false,engineering_runs:0,workspace_created:createdScope??null},null,2));
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
