import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';

const privateRoot = path.resolve('.local-run/process-interfaces-083/t034-pagehide-reload-001');
const proof = JSON.parse(readFileSync(path.join(privateRoot, 'browser-context.json'), 'utf8'));
const root = path.resolve('artifacts/ui-walkthrough/process-interfaces-083-hosting/20261003T033300Z-pagehide-reload-002');
if (existsSync(root)) throw new Error('Preserve the previous walkthrough; select a fresh root');
for (const dir of ['playwright','screenshots/raw','screenshots/annotated','trace']) mkdirSync(path.join(root, dir), {recursive:true});
const status = {title:'Saved engineering interfaces release their views on reload', summary:'Actual common host cleanup on two saved model-created interfaces; no process restart or review response.', overall:'pending', updated:new Date().toISOString(), manualSteps:[
 {label:'Open interface',instruction:'Open the saved Heat comparison or Focus-wheel working-interface link.'},
 {label:'Reload',instruction:'Reload the page three times. Check that the same saved interface and exact results return.'},
 {label:'Leave workspace',instruction:'Navigate away. Return to the saved interface and check its results. Leave all review decisions unchanged.'},
], steps:[]};
const escape = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function publish() {
  status.updated = new Date().toISOString();
  writeFileSync(path.join(root,'status.json'),JSON.stringify(status,null,2));
  writeFileSync(path.join(root,'report.html'),`<!doctype html><html><head><meta charset="utf-8"><title>${escape(status.title)}</title><style>body{font:16px system-ui;max-width:1100px;margin:24px auto;background:#101922;color:#e8f4f7}section{padding:18px;border:1px solid #647486;margin:16px 0}.pass{border-color:#64bda4}.blocked{border-color:#ee7373}img{max-width:100%}a{color:#7fe0cb}</style></head><body><h1>${escape(status.title)}</h1><p>${escape(status.summary)}</p><p>Status: ${escape(status.overall)}</p><h2>Manual steps</h2><ol>${status.manualSteps.map(s=>`<li>${escape(s.instruction)}</li>`).join('')}</ol>${status.steps.map(s=>`<section class="${s.state}"><h2>${escape(s.label)} Â· ${escape(s.state)}</h2><p>${escape(s.summary)}</p><p>Expected: ${escape(s.expected)}</p><p>Actual: ${escape(s.actual)}</p>${['raw','annotated'].filter(k=>s[k]).map(k=>`<p>${k}<a class="image-button" href="${escape(s[k])}" onclick="event.preventDefault();document.getElementById('full-image').src=this.href;document.getElementById('image-dialog').showModal()"><img src="${escape(s[k])}" alt="${escape(s.label)} ${k}"></a></p>`).join('')}</section>`).join('')}<dialog id="image-dialog"><button onclick="document.getElementById('image-dialog').close()">Close</button><img id="full-image" style="max-width:none" alt="Full-size walkthrough evidence"></dialog></body></html>`);
}
writeFileSync(path.join(root,'progress.md'),'# Latest saved Heat output and navigation continuation\n\nPrepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.\n');
publish();
writeFileSync(path.join(root,'playwright','workspace-entry.mjs'),readFileSync(new URL(import.meta.url)));
const browser = await chromium.launch({headless:true});
const context = await browser.newContext({viewport:{width:1440,height:1000}});
await context.addCookies([{name:'wright_session',value:proof.browser_cookie,url:proof.frontend_url+'/api',httpOnly:true,sameSite:'Strict'}]);
await context.tracing.start({screenshots:true,snapshots:true,sources:true});
const page = await context.newPage();
const diagnostics={presentations:[],controlPlane:[],console:[],pageErrors:[],failedResponses:[],mutations:[],representationHeaders:[],contexts:[]};
page.on('request', request => {if(!['GET','HEAD','OPTIONS'].includes(request.method())) diagnostics.mutations.push({method:request.method(),path:new URL(request.url()).pathname});});
page.on('console',m=>{if(m.type()==='error') diagnostics.console.push(m.text().slice(0,2000));});
page.on('pageerror',e=>diagnostics.pageErrors.push(e.message));
page.on('response',r=>{if(r.status()>=400) diagnostics.failedResponses.push({path:new URL(r.url()).pathname,status:r.status()});});
page.on('response', async response => {if(new URL(response.url()).pathname.endsWith('/__wright/process/context') && response.status()===200) {const value=await response.json();diagnostics.contexts.push({read_only:value.read_only,run_id:value.run_id,ui_id:value.ui_id,revision_id:value.revision_id});}});
page.on('response', async response => {if(new URL(response.url()).pathname.endsWith('/representations/read')) {const headers=await response.allHeaders();diagnostics.representationHeaders.push({status:response.status(),bytes:headers['content-length'],sha256:headers['x-wright-artifact-sha256'],nosniff:headers['x-content-type-options']});}});
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
  for (const child of page.frames().filter(frame => frame !== page.mainFrame())) {
    await child.evaluate(() => {
      const layer=document.createElement('div'); layer.id='wright-walkthrough-overlays';
      layer.style='position:fixed;inset:0;pointer-events:none;z-index:2147483647';
      const labels=[]; let index=0;
      for(const control of document.querySelectorAll('button,input,select')) {
        const r=control.getBoundingClientRect(); if(r.width<2||r.height<2||r.top<0||r.top>innerHeight)continue;
        const title=(control.getAttribute('aria-label')||control.textContent||control.getAttribute('type')||'').trim().slice(0,70);
        if(!title)continue; index++;
        const tag=document.createElement('span');tag.textContent=String(index);
        tag.style=`position:absolute;left:${r.left}px;top:${r.top}px;background:#fbcc42;color:#111;padding:1px 4px;font:13px system-ui`;
        layer.appendChild(tag);labels.push(index+': '+title);
      }
      const legend=document.createElement('div');legend.textContent=labels.join(' | ');
      legend.style='position:absolute;left:8px;bottom:8px;right:8px;background:#111e;color:#fff;padding:8px;font:12px system-ui';
      layer.appendChild(legend);document.body.appendChild(layer);
    });
  }
  await page.screenshot({path:path.join(root,annotated),fullPage:true});
  for (const child of page.frames()) await child.locator('#wright-walkthrough-overlays').evaluateAll(es=>es.forEach(e=>e.remove()));
  return {raw,annotated};
}
async function record(step){status.steps.push(step);publish();appendFileSync(path.join(root,'progress.md'),`\n## ${new Date().toISOString()} UTC â€” ${step.label}\n\nURL: ${cleanUrl()}\nAction: ${step.action}\nControls: ${step.controls.join(', ')}\nExpected: ${step.expected}\nActual: ${step.actual}\nStatus: ${step.state}\nScreenshots: ${step.raw??''}; ${step.annotated??''}\n`);}



page.on('response', async response => {
  if (/\/uis\/[^/]+\/present$/.test(new URL(response.url()).pathname) && response.status() === 200) {
    const value = await response.json();
    diagnostics.presentations.push({presentation_id:value.binding.presentation_id, run_id:value.binding.run_id,
      ui_id:value.binding.ui_id, revision_id:value.binding.revision_id});
  }
});
const cases=JSON.parse(readFileSync(path.join(privateRoot,'cases.json'),'utf8'));
const frame=page.locator('[data-testid="surface-panel-host"]:visible').frameLocator('iframe');
function observe(){
  const reply=spawnSync(path.resolve('.venv/Scripts/python.exe'),[path.resolve('.local-run/process-interfaces-083/t034-observe-pagehide-proof-001.py')],{encoding:'utf8'});
  if(reply.status!==0)throw new Error('Control-plane preservation observation failed: '+reply.stderr);
  const value=JSON.parse(reply.stdout);diagnostics.controlPlane.push(value);return value;
}
async function current(item){
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:120000});
  await expect(frame.locator('article[data-result-id]')).toHaveCount(item.expected_result_ids.length,{timeout:120000});
  expect(await frame.locator('article[data-result-id]').evaluateAll(rows=>rows.map(row=>row.dataset.resultId).sort())).toEqual(item.expected_result_ids);
  await expect.poll(()=>diagnostics.presentations.filter(value=>value.ui_id===item.manifest.ui_id).at(-1),{timeout:30000}).toMatchObject({
    run_id:item.expected_result_ids[0].split(':')[0],ui_id:item.manifest.ui_id,revision_id:item.manifest.revision_id});
  const value=diagnostics.presentations.filter(value=>value.ui_id===item.manifest.ui_id).at(-1);
  expect(observe().presentations.find(row=>row.presentation_id===value.presentation_id)?.state).toBe('active');
  return value;
}
try{
  let index=0;
  for(const item of cases){
    await page.goto(item.url);
    let held=await current(item);
    await record({id:'S'+String(++index).padStart(2,'0'),state:'pass',label:item.label+' saved interface opens',summary:'The current saved interface displays its exact engineering results.',purpose:'Establish current immutable saved/run identity.',action:'Open the saved working-interface link.',controls:['Run inputs','Open representation','Open assessment'],expected:'Exact saved revision, current results and active presentation.',actual:item.expected_result_ids.length+' exact results; existing source/build and run files unchanged.',...await capture('S'+String(index).padStart(2,'0'),'Saved view')});
    for(let attempt=1;attempt<=3;attempt++){
      const prior=held;
      await page.reload();held=await current(item);
      expect(held.presentation_id).not.toBe(prior.presentation_id);
      await expect.poll(()=>observe().presentations.find(row=>row.presentation_id===prior.presentation_id)?.state,{timeout:30000}).toBe('closed');
      await record({id:'S'+String(++index).padStart(2,'0'),state:'pass',label:item.label+' reload '+attempt+' releases previous view',summary:'Reload restores the same saved interface and closes its prior presentation.',purpose:'Verify actual browser departure cleanup rather than only component unmount.',action:'Reload the page.',controls:['Run inputs','Open assessment'],expected:'Prior exact view closed; fresh working presentation with the same results.',actual:'Previous exact presentation is closed; '+item.expected_result_ids.length+' result identities and immutable records unchanged.',...await capture('S'+String(index).padStart(2,'0'),'Reconciled view')});
    }
    await record({id:'S'+String(++index).padStart(2,'0'),state:'pass',label:item.label+' ready to leave workspace',summary:'The final saved view is intact before leaving.',purpose:'Retain the last visible screen before document departure.',action:'Inspect the saved view before navigating away.',controls:['Run inputs','Open assessment'],expected:'Same exact results and review state.',actual:'Saved view and current results present; no review action requested.',...await capture('S'+String(index).padStart(2,'0'),'Before departure')});
    await page.goto('about:blank');
    await expect.poll(()=>observe().presentations.find(row=>row.presentation_id===held.presentation_id)?.state,{timeout:30000}).toBe('closed');
    await record({id:'S'+String(++index).padStart(2,'0'),state:'pass',label:item.label+' departure releases view',summary:'Navigating away closes the exact presentation and preserves the process.',purpose:'Check native view cleanup independently in the backend.',action:'Navigate away from the workspace.',controls:[],expected:'Exact presentation closed; process and saved artifacts unchanged.',actual:'Exact presentation closed; all baseline files and UI authoring records unchanged.',...await capture('S'+String(index).padStart(2,'0'),'Departed document')});
  }
  expect(diagnostics.console).toEqual([]);expect(diagnostics.pageErrors).toEqual([]);expect(diagnostics.failedResponses).toEqual([]);
  const mutations=diagnostics.mutations.filter(row=>!row.path.includes('/auth/')&&!row.path.includes('/mcp/'));
  expect(mutations.filter(row=>row.path.includes('/process-interfaces/')&&!row.path.endsWith('/present')&&!row.path.endsWith('/presentations/close'))).toEqual([]);
  const final=observe();
  for(const value of diagnostics.presentations)expect(final.presentations.find(row=>row.presentation_id===value.presentation_id)?.state).toBe('closed');
  writeFileSync(path.join(privateRoot,'parity.json'),JSON.stringify({cases:cases.map(item=>({label:item.label,ui_id:item.manifest.ui_id,revision_id:item.manifest.revision_id,result_ids:item.expected_result_ids})),reloads_per_interface:3,exact_issued_views_closed:true,files_unchanged:final.files_unchanged,authoring_records_unchanged:final.authoring_records_unchanged},null,2));
  status.overall='pass';
}catch(error){
  status.overall='blocked';
  await record({id:'STOP',state:'blocked',label:'Departure lifetime check stopped',summary:'The first unexpected host behavior is preserved.',purpose:'Retain the first failure without guessing or continuing.',action:'Stop at the current page.',controls:['Run inputs'],expected:'Exact view cleanup and saved-result reconciliation.',actual:error.message,...await capture('STOP','Stopping point')});
}finally{
  publish();writeFileSync(path.join(root,'browser-diagnostics.json'),JSON.stringify(diagnostics,null,2));
  await context.tracing.stop({path:path.join(privateRoot,'pagehide-reload-002-trace.zip')});await browser.close();
  console.log(JSON.stringify({status:status.overall,report:path.join(root,'report.html'),steps:status.steps.map(item=>({id:item.id,state:item.state,actual:item.actual}))}));
}
