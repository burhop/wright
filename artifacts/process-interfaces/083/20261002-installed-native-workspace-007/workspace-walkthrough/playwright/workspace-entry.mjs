import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const repo = 'D:/repos/wright';
const privateRoot = path.join(repo,'.local-run/process-interfaces-083/t051-mounted-native-007');
const proof = JSON.parse(readFileSync(path.join(privateRoot,'browser-context.json'),'utf8'));
const prepared = JSON.parse(readFileSync(path.join(repo,'.local-run/process-interfaces-083/t047-wheel-saved-reuse-007/prepared-run.json'),'utf8'));
const receipt = JSON.parse(readFileSync(path.join(repo,'.local-run/process-interfaces-083/t047-wheel-saved-reuse-007/start-receipt.json'),'utf8')).body;
const root = path.join(repo,'artifacts/process-interfaces/083/20261002-installed-native-workspace-007/workspace-walkthrough');
if (existsSync(root)) throw new Error('Fresh walkthrough root required');
for (const dir of ['playwright','screenshots/raw','screenshots/annotated','trace']) mkdirSync(path.join(root,dir),{recursive:true});
const status = {title:'Installed Wright: common and saved process interfaces',summary:'Genuine local wheel installation, cached dependencies, copied isolated engineering workspace; no model/compiler or engineering dispatch.',overall:'pending',updated:new Date().toISOString(),manualSteps:[
  {label:'Open installed Wright',instruction:'Open the installed native Wright home page, then the isolated proof workspace.'},
  {label:'Open process',instruction:'Click Workflows, Workflow files, Open workflow, then choose the saved wheel workflow.'},
  {label:'Use working view',instruction:'Click Use saved process and open the second recorded run link.'},
  {label:'Reuse interface',instruction:'Click Create or choose interface, choose the saved focus-wheel interface and current revision, then Open saved interface.'},
  {label:'Reload',instruction:'Reload the working tab and inspect the same waiting review. Leave the review unanswered.'},
],steps:[]};
const escape = v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function publish(){
  status.updated=new Date().toISOString();
  writeFileSync(path.join(root,'status.json'),JSON.stringify(status,null,2));
  writeFileSync(path.join(root,'report.html'),`<!doctype html><html><meta charset="utf-8"><title>${escape(status.title)}</title><style>body{font:16px system-ui;background:#101922;color:#e8f4f7;max-width:1100px;margin:24px auto}section{padding:18px;border:1px solid #647486;margin:16px 0}.pass{border-color:#64bda4}.blocked{border-color:#ee7373}img{max-width:100%}a{color:#7fe0cb}</style><h1>${escape(status.title)}</h1><p>${escape(status.summary)}</p><p>Status: ${status.overall}</p><h2>Manual repeat</h2><ol>${status.manualSteps.map(s=>`<li>${escape(s.instruction)}</li>`).join('')}</ol>${status.steps.map(s=>`<section class="${s.state}"><h2>${escape(s.label)} · ${s.state}</h2><p>${escape(s.summary)}</p><p>Expected: ${escape(s.expected)}</p><p>Actual: ${escape(s.actual)}</p>${['raw','annotated'].filter(k=>s[k]).map(k=>`<p>${k}<a class="image-button" href="${escape(s[k])}" onclick="event.preventDefault();document.getElementById('full-image').src=this.href;document.getElementById('image-dialog').showModal()"><img src="${escape(s[k])}" alt="${escape(s.label)} ${k}"></a></p>`).join('')}</section>`).join('')}<dialog id="image-dialog"><button onclick="document.getElementById('image-dialog').close()">Close</button><img id="full-image" style="max-width:none" alt="Full-size evidence"></dialog></html>`);
}
writeFileSync(path.join(root,'progress.md'),'# Installed native process workspace walkthrough\n\nPrepared before navigation. Authenticated browser trace remains private.\n');
writeFileSync(path.join(root,'playwright','workspace-entry.mjs'),readFileSync(new URL(import.meta.url)));
publish();
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({viewport:{width:1440,height:1000}});
await context.tracing.start({screenshots:true,snapshots:true,sources:true});
const page=await context.newPage();
page.setDefaultTimeout(30000);
const diagnostics={console:[],pageErrors:[],failedResponses:[],mutations:[]};
page.on('console',m=>{if(m.type()==='error') diagnostics.console.push(m.text().slice(0,1500));});
page.on('pageerror',e=>diagnostics.pageErrors.push(e.message));
page.on('response',r=>{if(r.status()>=400) diagnostics.failedResponses.push({path:new URL(r.url()).pathname,status:r.status()});});
page.on('request',r=>{if(!['GET','HEAD','OPTIONS'].includes(r.method())) diagnostics.mutations.push({path:new URL(r.url()).pathname,method:r.method()});});
const safeUrl=()=>{const u=new URL(page.url());u.hash='';return u.href;};
async function capture(id){
  const raw=`screenshots/raw/${id}.png`,annotated=`screenshots/annotated/${id}.png`;
  await page.screenshot({path:path.join(root,raw),fullPage:true});
  await page.evaluate(()=>{
    const layer=document.createElement('div');layer.id='walkthrough-overlay';layer.style='position:fixed;inset:0;pointer-events:none;z-index:2147483647';
    const labels=[];
    for(const c of document.querySelectorAll('button,input,select,[role="tab"]')){
      const r=c.getBoundingClientRect();if(r.width<2||r.height<2||r.top<0||r.top>innerHeight) continue;
      const title=(c.getAttribute('aria-label')||c.textContent||'').trim().slice(0,55);if(!title)continue;
      const n=labels.push(title);const tag=document.createElement('span');tag.textContent=String(n);tag.style=`position:absolute;left:${r.left}px;top:${r.top}px;background:#fbcc42;color:#111;padding:1px 4px;font:13px system-ui`;layer.appendChild(tag);
    }
    const legend=document.createElement('div');legend.textContent=labels.map((v,i)=>`${i+1}: ${v}`).join(' | ');legend.style='position:absolute;left:8px;right:8px;bottom:8px;background:#111e;color:white;padding:8px;font:12px system-ui';layer.appendChild(legend);document.body.appendChild(layer);
  });
  await page.screenshot({path:path.join(root,annotated),fullPage:true});
  await page.locator('#walkthrough-overlay').evaluate(e=>e.remove());
  return {raw,annotated};
}
async function record(id,label,action,controls,expected,actual,state='pass'){
  const step={id,label,action,controls,expected,actual,state,purpose:label,summary:actual,...await capture(id)};
  status.steps.push(step);publish();
  appendFileSync(path.join(root,'progress.md'),`\n## ${new Date().toISOString()} UTC — ${label}\nURL: ${safeUrl()}\nAction: ${action}\nControls: ${controls.join(', ')}\nExpected: ${expected}\nActual: ${actual}\nStatus: ${state}\nScreenshots: ${step.raw}; ${step.annotated}\n`);
}
try{
  await page.goto(proof.frontend_url+'/');
  expect((await context.cookies()).some(c=>c.name==='wright_session'&&c.httpOnly)).toBe(true);
  await page.goto(proof.frontend_url+'/workspace/'+proof.workspace_id);
  await expect(page.getByRole('button',{name:'Workflows',exact:true})).toBeVisible({timeout:120000});
  await record('S01','Installed workspace loads','Open native home and proof workspace.',['Workflows'],'Native session bootstrap and workspace entry.','Installed frontend loads with native HttpOnly session and Workflows control.');
  await page.getByRole('button',{name:'Workflows',exact:true}).click();
  await expect(page.getByTestId('workflow-file-menu')).toBeVisible();
  await record('S02','Established editor entry','Click Workflows.',['Workflow files'],'Existing editor in workspace.','Workflow file menu and editor open within the installed workspace.');
  await page.getByTestId('workflow-file-menu').click();
  await page.getByTestId('workflow-file-open').click();
  await expect(page.getByTestId('workflow-file-choice-'+prepared.path)).toBeVisible();
  await record('S03','Saved engineering workflow','Click Workflow files, then Open workflow.',['Open workflow',prepared.path],'Exact accepted wheel source offered.','Accepted wheel workflow appears in the installed file chooser.');
  await page.getByTestId('workflow-file-choice-'+prepared.path).click();
  const editor=page.locator('[data-workflow-file="'+prepared.path+'"]:visible');
  await expect(editor.getByTestId('workflow-working-view-open')).toBeEnabled();
  await record('S04','Authoring and working views share source','Choose the accepted wheel source.',['Use saved process'],'Same accepted source in diagram and working view.','The original review/repair/slice source is open with Use saved process enabled.');
  await editor.getByTestId('workflow-working-view-open').click();
  await expect(page.getByTestId('common-process-view')).toBeVisible();
  const attached=new URL(page.url());attached.searchParams.set('processRun',receipt.run_id);
  await record('S05','Installed common working view','Click Use saved process.',['Create or choose interface'],'Common view opens as a workspace tab.','Installed shared common view opens without starting another run.');
  await page.goto(attached.href);
  await expect(page.getByText('Waiting for your review or response',{exact:true})).toBeVisible({timeout:120000});
  await record('S06','Exact existing run remains waiting','Open recorded second-run link.',['Review the next action'],'Existing second run remains at its declared review.','Common view shows the same second run and pending geometry-basis review.');
  await page.getByRole('button',{name:'Create or choose interface',exact:true}).click();
  await expect(page.getByLabel('Saved interface',{exact:true})).toBeVisible();
  await expect(page.locator('.wp-field').first()).toHaveCSS('display','flex');
  expect(await page.getByLabel('Saved interface',{exact:true}).evaluate(e=>e.getBoundingClientRect().height)).toBeGreaterThanOrEqual(44);
  await expect(page.getByText('The qualified interface compiler is unavailable.',{exact:true})).toBeVisible({timeout:60000});
  await record('S07','Saved UI independent of authoring compiler','Click Create or choose interface.',['Saved interface'],'Unavailable compiler explained; saved interfaces offered.','Compiler unavailable is explicit and the saved interface chooser remains usable.');
  await page.getByLabel('Saved interface',{exact:true}).selectOption('ui-1e7b6edb71e74b19a754b7fd2b88633a');
  await page.getByLabel('Saved revision',{exact:true}).selectOption('revision-415f9e4911f0447199dd6fbd4bbc46c0');
  await expect(page.getByRole('button',{name:'Open saved interface',exact:true})).toBeEnabled();
  await record('S08','Existing built revision selected','Choose saved focus-wheel interface and current revision.',['Open saved interface'],'Previously generated immutable revision selectable.','Exact original saved UI/revision selected without generating or compiling.');
  await page.getByRole('button',{name:'Open saved interface',exact:true}).click();
  const frame=page.locator('[data-testid="surface-panel-host"]:visible').frameLocator('iframe');
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:120000});
  await expect(frame.getByText('Waiting for your review or response',{exact:true})).toBeVisible();
  await expect(frame.locator('[data-result-id]')).toHaveCount(1);
  const result=await frame.locator('[data-result-id]').getAttribute('data-result-id');
  expect(result.startsWith(receipt.run_id+':')).toBe(true);
  await record('S09','Installed saved interface mounts','Click Open saved interface.',['Review the next action'],'Saved React UI connected to the exact run through the installed bridge.','Saved UI renders in its workspace tab with the second run’s single result and waiting review.');
  await page.reload();
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:120000});
  await expect(frame.getByText('Waiting for your review or response',{exact:true})).toBeVisible();
  await expect(frame.locator('[data-result-id]')).toHaveCount(1);
  await record('S10','Installed reopening reconciles','Reload the saved interface tab.',['Review the next action'],'Same run, saved revision and waiting review after reload.','Installed tab restores the same waiting run and saved compiled interface.');
  const forbidden=diagnostics.mutations.filter(r=>/authoring-jobs|\/start$|\/respond$|\/actions\//.test(r.path));
  expect(forbidden).toEqual([]);
  writeFileSync(path.join(privateRoot,'installed-dom.json'),JSON.stringify({url:safeUrl(),run_id:receipt.run_id,body:await page.locator('body').innerText(),frame:await frame.locator('#wright-process-ui').innerText()},null,2));
  status.overall='pass';
}catch(error){
  status.overall='blocked';
  await record('STOP','Installed journey stopped','Stop at first unexpected state.',['Current workspace control'],'Installed common/saved journey remains usable.',error.message,'blocked');
  writeFileSync(path.join(privateRoot,'installed-dom.json'),JSON.stringify({url:safeUrl(),body:await page.locator('body').innerText()},null,2));
}finally{
  publish();
  writeFileSync(path.join(root,'browser-diagnostics.json'),JSON.stringify(diagnostics,null,2));
  await context.tracing.stop({path:path.join(privateRoot,'installed-workspace-trace.zip')});
  await browser.close();
  console.log(JSON.stringify({status:status.overall,report:path.join(root,'report.html'),steps:status.steps.map(s=>({id:s.id,state:s.state,actual:s.actual}))}));
}
