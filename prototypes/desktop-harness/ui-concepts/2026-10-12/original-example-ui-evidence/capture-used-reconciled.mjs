// Original copies, compiled GB10 browser only. No model/gateway/run calls.
import { chromium, expect } from '/tmp/wright-host-adaptive-ui-prototype/node_modules/@playwright/test/index.mjs';
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join } from 'node:path';
import { execFileSync } from 'node:child_process';
const state='/tmp/wright-host-ui-original-examples-20261012-01';
const evidence=JSON.parse(readFileSync(join(state,'existing-examples.json'),'utf8'));
const output=join(state,'ui-inspection');mkdirSync(output,{recursive:true});
const sha=x=>createHash('sha256').update(x).digest('hex');
const dist='/tmp/wright-host-adaptive-ui-prototype/apps/web/dist';
const assets=Object.fromEntries(readdirSync(join(dist,'assets')).map(x=>['/assets/'+x,sha(readFileSync(join(dist,'assets',x)))]));
const browser=await chromium.launch({headless:true});const entries=[];
try{
 for(const row of evidence.examples){
  const page=await browser.newPage({viewport:{width:1440,height:960}});const requests=[],served=[];
  page.on('request',r=>{const u=new URL(r.url());if(u.pathname.startsWith('/api/'))requests.push({path:u.pathname,method:r.method()});});
  page.on('response',r=>{const name=new URL(r.url()).pathname;if(assets[name])served.push(r.body().then(bytes=>({path:name,matches:sha(bytes)===assets[name],sha256:sha(bytes)})));});
  const before=readFileSync(join(row.workspace_path,row.source_path),'utf8');const beforeSha=sha(before);
  await page.goto(`http://127.0.0.1:8121/workspace/${row.workspace_id}?host=openai-desktop`);
  await page.getByLabel('Access Token',{exact:true}).fill(readFileSync(join(state,'.preview-api-token'),'utf8').trim());
  await page.getByRole('button',{name:'Unlock',exact:true}).click();
  await page.getByRole('button',{name:/^Workflows?$/}).click();
  await expect(page.getByTestId('workflow-recovery-canvas')).toBeVisible();
  const selected=new URL(page.url());selected.searchParams.set('workflowPath',row.source_path);
  await page.goto(selected.href);
  await expect(page.getByTestId('workflow-recovery-canvas')).toBeVisible();
  const nodes=page.locator('.recovery-block');const nodeCount=await nodes.count();expect(nodeCount).toBe((before.match(/^(?:task|input|output) /gm)||[]).length);
  await page.getByTestId('workflow-recovery-canvas-fit').click();
  await page.screenshot({path:join(output,row.template_id+'.png')});
  await page.getByTestId('workflow-recovery-view-code').click();
  const displayed=await page.getByTestId('workflow-recovery-source-editor').inputValue();
  expect(displayed).toBe(before);
  await page.reload();await expect(page.getByTestId('workflow-recovery-canvas')).toBeVisible();
  await page.getByTestId('workflow-recovery-view-code').click();expect(await page.getByTestId('workflow-recovery-source-editor').inputValue()).toBe(before);
  expect(sha(readFileSync(join(row.workspace_path,row.source_path)))).toBe(beforeSha);
  const forbidden=requests.filter(r=>/^\/api\/(agent|inference)/.test(r.path)||r.method!=='GET'&&(/process-interfaces\/(runs|interactions)|workflow-sources\/run/.test(r.path)));
  expect(forbidden).toEqual([]);
  const checks=await Promise.all(served);expect(checks.length).toBeGreaterThan(0);expect(checks.every(x=>x.matches)).toBe(true);
  entries.push({template_id:row.template_id,workspace_id:row.workspace_id,source_path:row.source_path,source_sha256:beforeSha,exact_source_displayed_and_reopened:true,source_unchanged:true,entered_via_workflows:true,node_count:nodeCount,catalog_readiness:row.catalog_readiness,compiler:row.compiler,engineering_run_started:false,forbidden_requests:forbidden,requests,served_assets:checks});
  await page.close();
 }
 const commit=execFileSync('git',['rev-parse','HEAD'],{cwd:'/tmp/wright-host-adaptive-ui-prototype',encoding:'utf8'}).trim();
 writeFileSync(join(output,'report.json'),JSON.stringify({boundary:'compiled GB10 browser; no native Windows acceptance or engineering execution',commit,build_flags:{VITE_WRIGHT_WORKFLOW_RECOVERY:'1'},entries},null,2)+'\n');
 console.log('Both original workflows display and reopen exact source through Workflows; provider gates retained, no runs.');
}finally{await browser.close();}
