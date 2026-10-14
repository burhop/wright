// Read-only owner integration; simulated MCP App host, not Windows acceptance.
// Reuses native_editor_acceptance.mjs's official SDK iframe handshake.
import { createServer } from 'node:http';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { chromium, expect } from '@playwright/test';

const state = resolve(process.argv[2]);
const evidence = JSON.parse(readFileSync(resolve(state, 'home-probe.json')));
const preview = JSON.parse(readFileSync(resolve(state, 'preview.json')));
const token = readFileSync(resolve(state, '.preview-api-token'), 'utf8');
const bundle = readFileSync('prototypes/desktop-harness/native-editor.html', 'utf8');
const output = resolve(state, `browser-home-${Date.now()}`);
mkdirSync(output);
const calls = [];
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
    let data;
    if (name === 'wright_workspace_list') data = await get('/api/desktop/workspaces');
    else {
      if (args.workspace_id !== evidence.scope.workspace_id || args.session_id !== evidence.scope.session_id) throw Error('Fixture scope denied');
      const workspace = await get(`/api/desktop/workspaces/${args.workspace_id}`, {session_id:args.session_id});
      if (name === 'wright_workspace_files') data = await get(`/api/desktop/workspaces/${args.workspace_id}/files`, {session_id:args.session_id});
      else {
        if (args.path !== evidence.scope.path) throw Error('Fixture file denied');
        if (name === 'wright_workflow_read') data = await source();
        else if (name === 'wright_workflow_open') data = {workspace,document:await source(),working_view_enabled:true};
        else throw Error('Read-only fixture denies this operation');
      }
    }
    res.writeHead(200, {'Content-Type':'application/json'});
    res.end(JSON.stringify({content:[],structuredContent:data}));
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
  await frame.getByLabel('Workspace', {exact:true}).selectOption(evidence.scope.workspace_id);
  const workflow = frame.getByRole('button', {name:'stevecad-native.workflow.wflow',exact:true});
  await expect(workflow).toBeVisible();
  await page.screenshot({path:resolve(output, 'home.png')});
  passed.push('real isolated workspace and saved SteveCAD source discovered');
  await workflow.click();
  await expect(frame.getByTestId('workflow-recovery-save')).toBeVisible();
  await page.screenshot({path:resolve(output, 'editor.png')});
  await frame.getByRole('button',{name:'Workspaces',exact:true}).click();
  await expect(frame.getByLabel('Workspace',{exact:true})).toBeVisible();
  passed.push('home opens shared editor and Back returns without mutation');
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
  writeFileSync(resolve(output,'report.json'),JSON.stringify({passed,errors,calls,boundary:'simulated MCP App host, real read-only Wright storage',native_desktop_verified:false,engineering_runs:0},null,2));
  console.log(JSON.stringify({output,passed}));
} catch (error) {
  if (page) await page.screenshot({path:resolve(output,'failure.png')});
  writeFileSync(resolve(output,'failure.json'),JSON.stringify({error:String(error),passed,errors,calls},null,2));
  throw error;
} finally {
  await browser.close();
  await new Promise(done => server.close(done));
}
