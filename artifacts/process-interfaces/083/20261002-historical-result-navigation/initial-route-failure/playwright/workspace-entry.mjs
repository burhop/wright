import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const privateRoot = path.resolve('.local-run/process-interfaces-083/t049-historical-wheel-browser-009');
const proof = JSON.parse(readFileSync(path.join(privateRoot, 'browser-context.json'), 'utf8'));
const prepared = JSON.parse(readFileSync(path.join(privateRoot, 'prepared-run.json'), 'utf8'));
const root = path.resolve('artifacts/ui-walkthrough/process-interfaces-083-wheel/20261002T155800Z-wheel-historical-result');
if (existsSync(root)) throw new Error('Preserve the previous walkthrough; select a fresh root');
for (const dir of ['playwright','screenshots/raw','screenshots/annotated','trace']) mkdirSync(path.join(root, dir), {recursive:true});
const status={title:'Historical wheel result through the workspace',summary:'Exact retained failed native run, saved outputs and file tabs; no active vendor panel or process replay.',overall:'pending',updated:new Date().toISOString(),manualSteps:[{label:'Workspace',instruction:'Open the proof workspace and click Workflows.'},{label:'History',instruction:'Open its saved workflow link with printDemoRun identifying the retained failed run.'},{label:'Return',instruction:'Click Back to workflow, then View saved result.'},{label:'Saved record',instruction:'Click Open saved run record and inspect its workspace file tab.'}],steps:[]};
const escape = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function publish() {
  status.updated = new Date().toISOString();
  writeFileSync(path.join(root,'status.json'),JSON.stringify(status,null,2));
  writeFileSync(path.join(root,'report.html'),`<!doctype html><html><head><meta charset="utf-8"><title>${escape(status.title)}</title><style>body{font:16px system-ui;max-width:1100px;margin:24px auto;background:#101922;color:#e8f4f7}section{padding:18px;border:1px solid #647486;margin:16px 0}.pass{border-color:#64bda4}.blocked{border-color:#ee7373}img{max-width:100%}a{color:#7fe0cb}</style></head><body><h1>${escape(status.title)}</h1><p>${escape(status.summary)}</p><p>Status: ${escape(status.overall)}</p><h2>Manual steps</h2><ol>${status.manualSteps.map(s=>`<li>${escape(s.instruction)}</li>`).join('')}</ol>${status.steps.map(s=>`<section class="${s.state}"><h2>${escape(s.label)} Â· ${escape(s.state)}</h2><p>${escape(s.summary)}</p><p>Expected: ${escape(s.expected)}</p><p>Actual: ${escape(s.actual)}</p>${['raw','annotated'].filter(k=>s[k]).map(k=>`<p>${k}<a class="image-button" href="${escape(s[k])}" onclick="event.preventDefault();document.getElementById('full-image').src=this.href;document.getElementById('image-dialog').showModal()"><img src="${escape(s[k])}" alt="${escape(s.label)} ${k}"></a></p>`).join('')}</section>`).join('')}<dialog id="image-dialog"><button onclick="document.getElementById('image-dialog').close()">Close</button><img id="full-image" style="max-width:none" alt="Full-size walkthrough evidence"></dialog></body></html>`);
}
writeFileSync(path.join(root,'progress.md'),'# Heat workspace entry walkthrough\n\nPrepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.\n');
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
  await expect(page.getByRole('button',{name:'Workflows',exact:true})).toBeVisible({timeout:60000});
  await record({id:'S01',state:'pass',label:'Workspace entry',summary:'Normal workspace loads.',purpose:'Use normal workspace context.',action:'Open workspace.',controls:['Workflows'],expected:'Workflows visible.',actual:'Workflows visible.',...await capture('S01','Workspace')});
  await page.getByRole('button',{name:'Workflows',exact:true}).click();
  await expect(page.getByTestId('workflow-file-menu')).toBeVisible({timeout:60000});
  await expect(page.getByRole('button',{name:'Print a part demo',exact:true})).toHaveCount(0);
  await record({id:'S02',state:'pass',label:'Shared authoring entry',summary:'Established workflow editor remains; the active vendor demo entry is absent.',purpose:'Verify entry migration.',action:'Click Workflows.',controls:['Workflow files'],expected:'Editor controls without active print demo.',actual:'Editor controls present; Print a part demo absent.',...await capture('S02','Editor')});
  const receipt=JSON.parse(readFileSync(path.join(privateRoot,'start-receipt.json'),'utf8'));
  const readback=JSON.parse(readFileSync(path.join(privateRoot,'api-readback.json'),'utf8')).body;
  const url=new URL(proof.frontend_url+'/workspace/'+proof.workspace_id);
  url.search=new URLSearchParams({workflow:'canonical',workflowPath:prepared.path,printDemoRun:receipt.run_log_path});
  await page.goto(url.href);
  await expect(page.getByRole('heading',{name:'Saved workflow result',exact:true})).toBeVisible({timeout:60000});
  await expect(page.getByText('Recorded run: '+receipt.run_id+' · failed',{exact:true})).toBeVisible({timeout:60000});
  await expect(page.getByText('Recorded error: '+readback.run.error,{exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'Open saved artifact',exact:true})).toHaveCount(readback.run.results.flatMap(r=>r.representations).filter(r=>r.kind==='workspace_file').length);
  await expect(page.getByRole('button',{name:/Print on|Cancel this print|Create printable part/})).toHaveCount(0);
  await record({id:'S03',state:'pass',label:'Exact read-only history',summary:'Historical link shows the retained failed run and eleven saved outputs without device controls.',purpose:'Preserve actual run/artifact identity.',action:'Open historical workspace link.',controls:['Back to workflow','Open saved artifact','Open saved run record'],expected:'Exact failed run, original error and saved outputs; no print controls.',actual:'Exact retained failed run/error and artifact links verified.',...await capture('S03','History')});
  await page.getByRole('button',{name:'Back to workflow',exact:true}).click();
  await expect(page.locator('[data-workflow-file="'+prepared.path+'"]:visible')).toBeVisible({timeout:60000});
  await expect(page.getByRole('button',{name:'View saved result',exact:true})).toBeVisible();
  await record({id:'S04',state:'pass',label:'Return to its editor',summary:'History returns to the same saved workflow.',purpose:'Retain authoring navigation.',action:'Click Back to workflow.',controls:['View saved result','Workflow files'],expected:'Exact workflow editor restored.',actual:'Exact workflow editor and history reopen control visible.',...await capture('S04','Editor return')});
  await page.getByRole('button',{name:'View saved result',exact:true}).click();
  await expect(page.getByRole('button',{name:'Open saved run record',exact:true})).toBeVisible({timeout:60000});
  await record({id:'S05',state:'pass',label:'Reopen saved history',summary:'History reopens without preparing or executing a new process.',purpose:'Verify read-only reuse.',action:'Click View saved result.',controls:['Open saved run record'],expected:'Same retained run.',actual:'Same retained run restored.',...await capture('S05','Reopened history')});
  await page.getByRole('button',{name:'Open saved run record',exact:true}).click();
  await expect(page.getByTestId('editor-tab-'+receipt.run_log_path)).toHaveAttribute('aria-selected','true',{timeout:60000});
  await record({id:'S06',state:'pass',label:'Saved record in a workspace tab',summary:'The exact recorder file opens in Wright’s file tabs.',purpose:'Preserve evidence navigation without an external window.',action:'Click Open saved run record.',controls:[receipt.run_log_path],expected:'Exact saved recorder tab selected.',actual:'Exact saved recorder file tab selected.',...await capture('S06','Saved file tab')});
  status.overall='pass';
} catch(error){status.overall='blocked';await record({id:'STOP',state:'blocked',label:'History stopped',summary:'First unexpected historical result retained.',purpose:'Preserve failure evidence.',action:'Stop at unexpected state.',controls:['Historical result'],expected:'Exact saved history and workspace navigation.',actual:error.message,...await capture('STOP','Stop')});}
finally {publish();writeFileSync(path.join(root,'browser-diagnostics.json'),JSON.stringify(diagnostics,null,2));await context.tracing.stop({path:path.join(privateRoot,'trace.zip')});await browser.close();console.log(JSON.stringify({overall:status.overall,steps:status.steps.map(s=>({id:s.id,state:s.state,actual:s.actual}))}));}
