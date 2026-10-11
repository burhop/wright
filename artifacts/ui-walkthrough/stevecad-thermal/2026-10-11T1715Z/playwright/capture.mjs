// Bounded read/inspect walkthrough. No run, review, or approval is submitted.
import { chromium } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(process.argv[2]);
const base = 'http://wright.localhost:8891';
const workspace = '225aca34-3ae9-4557-85d6-0d8defd90a86';
const workflow = 'workflows/stevecad-heat-spreader-native-003.workflow.wflow';
for (const dir of ['playwright','screenshots/raw','screenshots/annotated','trace']) fs.mkdirSync(path.join(root,dir),{recursive:true});
fs.copyFileSync(new URL(import.meta.url),path.join(root,'playwright/capture.mjs'));
fs.writeFileSync(path.join(root,'progress.md'),'# SteveCAD saved process in Wright\n\nActual isolated workspace; inspection only. No engineering acceptance.\n');
const status = {title:'SteveCAD comparison in Wright',summary:'Opening the saved thermal process through the workspace.',overall:'pending',updated:new Date().toISOString(),manualSteps:[],steps:[]};
const diagnostics = [];
let authenticationPhase = true;
let page;
const escape = x => String(x).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
function report() {
  status.updated = new Date().toISOString();
  fs.writeFileSync(path.join(root,'status.json'),JSON.stringify(status,null,2));
  fs.writeFileSync(path.join(root,'report.html'),`<!doctype html><meta charset="utf-8"><title>${escape(status.title)}</title><style>body{font:16px system-ui;max-width:1000px;margin:30px auto}.pass{border-left:8px solid green}.blocked{border-left:8px solid red}.pending{border-left:8px solid gray}section{padding:15px;margin:15px 0;background:#f5f5f5}img{max-width:90%}dialog{max-width:95vw}dialog img{max-height:85vh}</style><h1>${escape(status.title)}</h1><p>${escape(status.summary)}</p><h2>Repeat manually</h2><ol>${status.manualSteps.map(x=>`<li>${escape(x.instruction)}</li>`).join('')}</ol>${status.steps.map(x=>`<section class="${x.state}"><h2>${escape(x.label)} — ${x.state}</h2><p>${escape(x.actual)}</p>${['raw','annotated'].filter(k=>x[k]).map(k=>`<a href="${x[k]}" onclick="event.preventDefault();document.querySelector('dialog img').src=this.href;document.querySelector('dialog').showModal()"><img src="${x[k]}" alt="${k}"></a>`).join('')}</section>`).join('')}<dialog><button onclick="this.closest('dialog').close()">Close</button><br><img alt="Full size screenshot"></dialog>`);
}
report();
const browser = await chromium.launch({headless:true, executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
const context = await browser.newContext({viewport:{width:1440,height:960},reducedMotion:'reduce'});
await context.tracing.start({screenshots:true,snapshots:true,sources:true});
page = await context.newPage();
page.on('console',m=>{if(m.type()==='error')diagnostics.push({kind:'console',text:m.text().slice(0,500),expected:authenticationPhase&&/401|Unauthorized|Failed to fetch|Failed to sync/.test(m.text())});});
page.on('pageerror',e=>diagnostics.push({kind:'page-error',text:e.message.slice(0,500)}));
page.on('response',r=>{if(r.status()>=400)diagnostics.push({kind:'http',path:new URL(r.url()).pathname,status:r.status(),expected:(authenticationPhase&&r.status()===401)||(r.status()===404&&new URL(r.url()).pathname.includes('workflow-sources'))});});
async function capture(name, controls) {
  const raw='screenshots/raw/'+name+'.png', annotated='screenshots/annotated/'+name+'.png';
  await page.screenshot({path:path.join(root,raw)});
  await page.evaluate(controls=>{
    const holder=document.createElement('div'); holder.id='capture-overlays';
    const legend=document.createElement('div'); legend.style.cssText='position:fixed;bottom:10px;right:10px;z-index:2147483647;background:white;color:#111;padding:12px;border:2px solid #127cbe;font:14px sans-serif';
    controls.forEach((c,i)=>{const el=document.querySelector(c.selector);if(!el)return;const b=el.getBoundingClientRect();if(!b.width||!b.height)return;const mark=document.createElement('span');mark.textContent=String(i+1);mark.style.cssText=`position:fixed;left:${b.left}px;top:${b.top}px;z-index:2147483647;background:#127cbe;color:white;padding:4px;border-radius:50%`;holder.append(mark);const row=document.createElement('div');row.textContent=`${i+1}. ${c.label}`;legend.append(row);});
    holder.append(legend);document.body.append(holder);
  },controls);
  await page.screenshot({path:path.join(root,annotated)});
  await page.evaluate(()=>document.getElementById('capture-overlays')?.remove());
  return {raw,annotated};
}
async function step(id,label,action,controls,expected,operation) {
  const row={id,state:'pending',label,summary:label,purpose:expected,action,controls,expected,actual:'Not reached'};
  status.steps.push(row);status.manualSteps.push({label,instruction:action});report();
  const start=diagnostics.length;
  try {
    if(id!=='01') Object.assign(row,await capture(id+'-before',controls));
    await operation();
    Object.assign(row,await capture(id+'-after',controls));
    const errors=diagnostics.slice(start).filter(x=>!x.expected);
    if(errors.length) throw Error('Unexpected browser diagnostics: '+JSON.stringify(errors));
    row.state='pass';row.actual=expected+' Verified in the served UI.';
  } catch(error) {
    row.state='blocked';row.actual=error.message;status.overall='blocked';status.summary='Stopped at '+label+'. Earlier evidence retained; no process was run or approved.';
    Object.assign(row,await capture(id+'-stopped',controls));
    throw error;
  } finally {
    fs.appendFileSync(path.join(root,'progress.md'),`\n## ${new Date().toISOString()} UTC — ${id}\nURL: ${page.url()}\nAction/control/value: ${action}\nExpected: ${expected}\nActual: ${row.actual}\nDiagnostics: ${JSON.stringify(diagnostics.slice(start))}\nRaw: ${row.raw}\nAnnotated: ${row.annotated}\nStatus: ${row.state==='pass'?'PASS':'STOPPED'}\n`);report();
  }
}
try {
  await step('00','Unlock the isolated local Wright instance','Open Wright and unlock it with the existing private local access token. Do not share the token.',[{selector:'input[type="password"]',label:'Private Access Token'},{selector:'button[type="submit"]',label:'Unlock'}],'Normal local access succeeds without exposing credentials',async()=>{
    await page.goto(base+'/');
    await page.getByLabel('Access Token',{exact:true}).waitFor();
    await capture('00-unlock-before',[{selector:'input[type="password"]',label:'Private Access Token'},{selector:'button[type="submit"]',label:'Unlock'}]);
    const token=fs.readFileSync(path.resolve('.local-run/runtime/api-token'),'utf8').trim();
    await page.getByLabel('Access Token',{exact:true}).fill(token);await page.getByRole('button',{name:'Unlock',exact:true}).click();
    await page.getByTestId('card-workspace-'+workspace).waitFor();
    authenticationPhase=false;
  });
  await step('01','Open the isolated dashboard','Open Wright on port 8891.',[{selector:`[data-testid="card-workspace-${workspace}"]`,label:'SteveCAD engineering demonstrations'}],'The exact isolated workspace card is visible',async()=>{
    await page.goto(base+'/');await page.getByTestId('card-workspace-'+workspace).waitFor();
  });
  await step('02','Enter the workspace','Click SteveCAD engineering demonstrations.',[{selector:'[data-testid="activity-bar-workflows-btn"]',label:'Workflows'}],'The workspace opens with its Workflows control',async()=>{
    await page.getByTestId('card-workspace-'+workspace).click();await page.getByTestId('activity-bar-workflows-btn').waitFor();
  });
  await step('03','Open the workflow editor','Click Workflows.',[{selector:'[data-testid="activity-bar-workflows-btn"]',label:'Workflows'},{selector:'[data-testid="workflow-file-menu"]',label:'Workflow file menu'}],'The preserved workflow editor opens in the workspace',async()=>{
    await page.getByTestId('activity-bar-workflows-btn').click();await page.getByTestId('workflow-file-menu').waitFor();
  });
  await step('04','Choose an existing saved workflow','Open the workflow file menu, then click Open workflow.',[{selector:'[data-testid="workflow-file-menu"]',label:'Workflow file menu'},{selector:'[data-testid="workflow-file-open"]',label:'Open workflow'}],'The saved thermal process is listed',async()=>{
    await page.getByTestId('workflow-file-menu').click();await page.getByTestId('workflow-file-open').click();await page.getByTestId('workflow-file-choice-'+workflow).waitFor();
  });
  await step('05','Inspect the saved thermal process','Click stevecad-heat-spreader-native-003.workflow.wflow.',[{selector:'[data-testid="workflow-working-view-open"]',label:'Open working view'},{selector:'[data-testid="workflow-workspace-context"]',label:'Saved process context'}],'The exact saved heat-spreader process opens with its authoring and working-view controls',async()=>{
    await page.getByTestId('workflow-file-choice-'+workflow).click();await page.getByTestId('workflow-working-view-open').waitFor();
    if(!page.url().includes(encodeURIComponent(workflow))) throw Error('Expected exact saved workflow locator');
  });
  status.overall='pass';status.summary='The saved SteveCAD heat-spreader process opened through the normal workspace Workflows control. This proves saved-process navigation, not engineering compliance or run completion.';
} catch(error) {process.exitCode=2;console.log('Walkthrough stopped: '+error.message);}
finally {
  fs.writeFileSync(path.join(root,'playwright/diagnostics.json'),JSON.stringify(diagnostics,null,2));
  await context.tracing.stop({path:path.resolve('.local-run/stevecad-ui-trace.zip')});
  await browser.close();report();
  console.log(JSON.stringify({status:status.overall,report:path.join(root,'report.html')}));
}
