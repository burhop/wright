import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const privateRoot = path.resolve('.local-run/process-interfaces-083/t049-original-installed-001');
const proof = JSON.parse(readFileSync(path.join(privateRoot, 'browser-context.json'), 'utf8'));
const cases = JSON.parse(readFileSync(path.join(privateRoot, 'cases.json'), 'utf8'));
const readbacks=JSON.parse(readFileSync(path.join(privateRoot,'api-readback.json'),'utf8'));
const root = path.resolve('artifacts/process-interfaces/083/20261003-original-history-installed-001/workspace-walkthrough');
if (existsSync(root)) throw new Error('Preserve the previous walkthrough; select a fresh root');
for (const dir of ['playwright','screenshots/raw','screenshots/annotated','trace']) mkdirSync(path.join(root, dir), {recursive:true});
const status={title:'Original pumpkin histories through the installed workspace',summary:'Three original pumpkin records, exact partial/completed outputs and Wright file tabs; read-only history with no device operations.',overall:'pending',updated:new Date().toISOString(),manualSteps:[{label:'Workspace',instruction:'Open the proof workspace and click Workflows.'},{label:'History',instruction:'Open each original pumpkin workflow link with its exact saved run.'},{label:'Return',instruction:'Click Back to workflow, then View saved result.'},{label:'Saved record',instruction:'Click Open saved run record and inspect its workspace file tab.'}],steps:[]};
const escape = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function publish() {
  status.updated = new Date().toISOString();
  writeFileSync(path.join(root,'status.json'),JSON.stringify(status,null,2));
  writeFileSync(path.join(root,'report.html'),`<!doctype html><html><head><meta charset="utf-8"><title>${escape(status.title)}</title><style>body{font:16px system-ui;max-width:1100px;margin:24px auto;background:#101922;color:#e8f4f7}section{padding:18px;border:1px solid #647486;margin:16px 0}.pass{border-color:#64bda4}.blocked{border-color:#ee7373}img{max-width:100%}a{color:#7fe0cb}</style></head><body><h1>${escape(status.title)}</h1><p>${escape(status.summary)}</p><p>Status: ${escape(status.overall)}</p><h2>Manual steps</h2><ol>${status.manualSteps.map(s=>`<li>${escape(s.instruction)}</li>`).join('')}</ol>${status.steps.map(s=>`<section class="${s.state}"><h2>${escape(s.label)} Â· ${escape(s.state)}</h2><p>${escape(s.summary)}</p><p>Expected: ${escape(s.expected)}</p><p>Actual: ${escape(s.actual)}</p>${['raw','annotated'].filter(k=>s[k]).map(k=>`<p>${k}<a class="image-button" href="${escape(s[k])}" onclick="event.preventDefault();document.getElementById('full-image').src=this.href;document.getElementById('image-dialog').showModal()"><img src="${escape(s[k])}" alt="${escape(s.label)} ${k}"></a></p>`).join('')}</section>`).join('')}<dialog id="image-dialog"><button onclick="document.getElementById('image-dialog').close()">Close</button><img id="full-image" style="max-width:none" alt="Full-size walkthrough evidence"></dialog></body></html>`);
}
writeFileSync(path.join(root,'progress.md'),'# Installed original-history walkthrough\n\nPrepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive. Expected unavailable-model responses are disclosed; original and copied run/evidence files are checked independently.\n');
publish();
writeFileSync(path.join(root,'playwright','workspace-entry.mjs'),readFileSync(new URL(import.meta.url)));
const browser = await chromium.launch({headless:true});
const context = await browser.newContext({viewport:{width:1440,height:1000}});
await context.addCookies([{name:'wright_session',value:proof.browser_cookie,url:proof.frontend_url+'/api',httpOnly:true,sameSite:'Strict'}]);
await context.tracing.start({screenshots:true,snapshots:true,sources:true});
const page = await context.newPage();
const diagnostics={console:[],pageErrors:[],failedResponses:[]};
page.on('console',m=>{if(m.type()==='error') diagnostics.console.push(m.text().slice(0,2000));});
page.on('pageerror',e=>diagnostics.pageErrors.push(e.message));
page.on('response',r=>{if(r.status()>=400) diagnostics.failedResponses.push({path:new URL(r.url()).pathname,status:r.status()});});
const cleanUrl = () => {const u=new URL(page.url());u.hash='';return u.href;};
async function capture(id,label) {
  const raw=`screenshots/raw/${id}.png`, annotated=`screenshots/annotated/${id}.png`;
  await page.screenshot({path:path.join(root,raw),fullPage:true});
  await page.evaluate(()=>{
    const layer=document.createElement('div');layer.id='wright-walkthrough-overlays';layer.style='position:fixed;inset:0;pointer-events:none;z-index:2147483647';
    let index=0;const labels=[];
    for(const control of document.querySelectorAll('button,[role="tab"],input,textarea,select')){
      const r=control.getBoundingClientRect();if(r.width<2||r.height<2||r.top<0||r.top>innerHeight)continue;
      const title=(control.getAttribute('aria-label')||control.textContent||control.getAttribute('placeholder')||'').trim().slice(0,70);if(!title)continue;
      index++;const tag=document.createElement('span');tag.textContent=String(index);tag.style=`position:absolute;left:${r.left}px;top:${r.top}px;background:#fbcc42;color:#111;border-radius:4px;padding:1px 4px;font:13px system-ui`;layer.appendChild(tag);labels.push(index+': '+title);
    }
    const legend=document.createElement('div');legend.textContent=labels.join(' | ');legend.style='position:absolute;left:8px;bottom:8px;right:8px;background:#111e;color:#fff;padding:8px;font:12px system-ui';layer.appendChild(legend);document.body.appendChild(layer);
  });
  await page.screenshot({path:path.join(root,annotated),fullPage:true});
  await page.locator('#wright-walkthrough-overlays').evaluate(e=>e.remove());
  return {raw,annotated};
}
async function record(step){status.steps.push(step);publish();appendFileSync(path.join(root,'progress.md'),`\n## ${new Date().toISOString()} UTC â€” ${step.label}\n\nURL: ${cleanUrl()}\nAction: ${step.action}\nControls: ${step.controls.join(', ')}\nExpected: ${step.expected}\nActual: ${step.actual}\nStatus: ${step.state}\nScreenshots: ${step.raw??''}; ${step.annotated??''}\n`);}
try {
  await page.goto(proof.frontend_url+'/workspace/'+proof.workspace_id);
  const button = name => page.getByRole('button',{name,exact:true}).filter({visible:true});
  await expect(button('Workflows')).toBeVisible({timeout:60000});
  await record({id:'S01',state:'pass',label:'Installed workspace entry',summary:'Normal Wright workspace loads from the current installed wheel.',purpose:'Use normal workspace context.',action:'Open workspace.',controls:['Workflows'],expected:'Workflows visible.',actual:'Workflows visible.',...await capture('S01','Workspace')});
  await button('Workflows').click();
  await expect(page.getByTestId('workflow-file-menu').filter({visible:true})).toBeVisible({timeout:60000});
  await expect(page.getByRole('button',{name:'Print a part demo',exact:true})).toHaveCount(0);
  await record({id:'S02',state:'pass',label:'Shared authoring entry',summary:'Established workflow editor remains; active vendor demo entry is absent.',purpose:'Verify workspace integration.',action:'Click Workflows.',controls:['Workflow files'],expected:'Editor controls without active print demo.',actual:'Editor controls present; Print a part demo absent.',...await capture('S02','Editor')});
  let index=2;
  for (const test of cases) {
    const readback=readbacks.find(row=>row.label===test.label).body;
    const url=new URL(proof.frontend_url+'/workspace/'+proof.workspace_id);
    url.search=new URLSearchParams({workflow:'canonical',workflowPath:test.path,printDemoRun:test.run_log_path});
    await page.goto(url.href);
    await expect(page.getByRole('heading',{name:'Saved workflow result',exact:true})).toBeVisible({timeout:60000});
    await expect(page.getByText('Recorded run: '+test.run_id+' · '+test.status,{exact:true})).toBeVisible({timeout:60000});
    if(test.error) await expect(page.getByText('Recorded error: '+test.error,{exact:true})).toBeVisible();
    const files=readback.run.results.flatMap(row=>row.representations).filter(row=>row.kind==='workspace_file');
    await expect(button('Open saved artifact')).toHaveCount(files.length);
    for(const id of test.result_ids) await expect(page.getByText(id,{exact:false}).filter({visible:true})).toHaveCount(1);
    await expect(page.getByRole('button',{name:/Print on|Cancel this print|Create printable part|Start process|Resume process/}).filter({visible:true})).toHaveCount(0);
    let id='S'+String(++index).padStart(2,'0');
    await record({id,state:'pass',label:test.label+' — exact history',summary:'Original '+test.status+' recorder and '+test.result_ids.length+' result identities are preserved.',purpose:'Preserve original format and exact evidence.',action:'Open exact historical workspace link.',controls:['Back to workflow','Open saved artifact','Open saved run record'],expected:'Exact recorded run/status/error and result links; no execution controls.',actual:test.run_id+'; '+test.status+'; '+test.result_ids.length+' exact results and '+files.length+' artifact links.',...await capture(id,'History')});
    await button('Back to workflow').click();
    await expect(page.locator('[data-workflow-file="'+test.path+'"]:visible')).toBeVisible({timeout:60000});
    await expect(button('View saved result')).toBeVisible();
    id='S'+String(++index).padStart(2,'0');
    await record({id,state:'pass',label:test.label+' — editor return',summary:'History returns to its exact saved source.',purpose:'Preserve complementary authoring view.',action:'Click Back to workflow.',controls:['View saved result','Workflow files'],expected:'Exact workflow editor restored.',actual:'Exact workflow editor and saved-result reopen control visible.',...await capture(id,'Editor return')});
    await button('View saved result').click();
    await expect(page.getByText('Recorded run: '+test.run_id+' · '+test.status,{exact:true})).toBeVisible({timeout:60000});
    await expect(button('Open saved run record')).toBeVisible();
    id='S'+String(++index).padStart(2,'0');
    await record({id,state:'pass',label:test.label+' — read-only reopen',summary:'Same retained history reopens without a new run.',purpose:'Reconcile historical identity.',action:'Click View saved result.',controls:['Open saved run record','Open saved artifact'],expected:'Same retained run and outputs.',actual:'Same exact retained run restored.',...await capture(id,'Reopened history')});
    await button('Open saved run record').click();
    await expect(page.getByTestId('editor-tab-/'+test.run_log_path)).toHaveAttribute('aria-selected','true',{timeout:60000});
    id='S'+String(++index).padStart(2,'0');
    await record({id,state:'pass',label:test.label+' — recorder file tab',summary:'Exact original recorder opens inside Wright.',purpose:'Verify evidence navigation.',action:'Click Open saved run record.',controls:[test.run_log_path],expected:'Exact recorder tab selected; no external window.',actual:'Exact recorder tab selected; one browser page.',...await capture(id,'Record tab')});
    if(context.pages().length!==1) throw new Error('Unexpected external browser page');
    // Select the existing workflow tab to return to history, then open one exact
    // small JSON artifact. Reading it does not invoke a manufacturing provider.
    await page.getByTestId('editor-tab-'+test.path).click();
    await expect(button('Open saved artifact')).toHaveCount(files.length,{timeout:60000});
    const artifactIndex=files.findIndex(row=>row.location.endsWith('.json'));
    if(artifactIndex>=0) {
      await button('Open saved artifact').nth(artifactIndex).click();
      await expect(page.getByTestId('editor-tab-/'+files[artifactIndex].location)).toHaveAttribute('aria-selected','true',{timeout:60000});
      id='S'+String(++index).padStart(2,'0');
      await record({id,state:'pass',label:test.label+' — artifact file tab',summary:'Exact recorded JSON evidence opens inside Wright.',purpose:'Verify retained artifact identity.',action:'Select saved workflow tab, then click Open saved artifact for '+files[artifactIndex].location+'.',controls:[test.path,'Open saved artifact',files[artifactIndex].location],expected:'Exact artifact tab selected; no new window or provider call.',actual:'Exact recorded artifact file tab selected.',...await capture(id,'Artifact tab')});
    }
  }
  const unexpected=diagnostics.failedResponses.filter(row=>!(row.path==='/api/agent/models'&&row.status===503));
  if(unexpected.length||diagnostics.pageErrors.length)throw new Error('Unexpected browser diagnostics: '+JSON.stringify({unexpected,pageErrors:diagnostics.pageErrors}));
  status.overall='pass';
} catch(error) {
  status.overall='blocked';
  await record({id:'STOP',state:'blocked',label:'Original-history proof stopped',summary:'First unexpected state preserved.',purpose:'Retain honest failure evidence.',action:'Stop at unexpected state.',controls:['Historical result'],expected:'Exact original history and workspace navigation.',actual:error.message,...await capture('STOP','Stop')});
} finally {
  publish();
  writeFileSync(path.join(root,'browser-diagnostics.json'),JSON.stringify(diagnostics,null,2));
  await context.tracing.stop({path:path.join(privateRoot,'trace-original-001.zip')});
  await browser.close();
  console.log(JSON.stringify({overall:status.overall,steps:status.steps.map(step=>({id:step.id,state:step.state,actual:step.actual}))}));
  if(status.overall!=='pass')process.exitCode=1;
}
