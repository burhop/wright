import AxeBuilder from '@axe-core/playwright';
import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const kind=process.argv[2]; if(!['heat','printed'].includes(kind))throw new Error('Select exact isolated proof kind');
const heat=kind==='heat';
const base=path.resolve('.local-run/process-interfaces-083');
const privateRoot=path.join(base,heat?'t052-mounted-native-012':'t052-mounted-native-013');
const readPrivate=name=>JSON.parse(readFileSync(path.join(privateRoot,name),'utf8')); 
const proof = JSON.parse(readFileSync(path.join(privateRoot, 'browser-context.json'), 'utf8'));
const prepared = JSON.parse(readFileSync(path.join(privateRoot, 'prepared-run.json'), 'utf8'));
const root=path.resolve('artifacts/process-interfaces/083/20261003-authoring-unavailable-'+kind+'-installed-001/workspace-walkthrough');
if (existsSync(root)) throw new Error('Preserve the previous walkthrough; select a fresh root');
for (const dir of ['playwright','screenshots/raw','screenshots/annotated','trace']) mkdirSync(path.join(root, dir), {recursive:true});
const status = {title:'Installed '+kind+' authoring availability and saved reuse', summary:"Normal installed Wright workspace; compiler/model deliberately unavailable; actual saved engineering outputs. No mocked routes or generation/process/review/action submission.", overall:'pending', updated:new Date().toISOString(), manualSteps:[{"label": "Workspace", "instruction": "Open the proof workspace."}, {"label": "Common view", "instruction": "Open the saved working-interface link, then click Use common working view."}, {"label": "Authoring readiness", "instruction": "Click Create or choose interface and enter a description. Check the unavailable reason and disabled Create/Update controls."}, {"label": "Saved choice", "instruction": "Check Saved interface and Saved revision identify the existing saved interface."}, {"label": "Keyboard reuse", "instruction": "At compact width focus Saved interface, press Tab twice to Open saved interface, then press Enter. Check the same results return in the working tab."}], steps:[]};
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
const requestTimes=new Map(); const observedRequests=[];
const ownedViews=new Map();const presentationReplies=[];
page.on('response',response=>{const p=new URL(response.url()).pathname;if(response.status()===200&&response.request().method()==='POST'&&(p.endsWith('/present')||p.endsWith('/preview'))){const collecting=response.json().then(value=>{if(value.descriptor?.surfaceId&&value.binding?.presentation_id)ownedViews.set(value.binding.presentation_id,value);}).catch(()=>{});presentationReplies.push(collecting);}});

page.on('request',request=>requestTimes.set(request,Date.now()));
page.on('requestfinished',request=>{const p=new URL(request.url()).pathname;if(p.includes('/__wright/')||p.endsWith('/preview')||p.endsWith('/present'))observedRequests.push({path:p,method:request.method(),elapsed_ms:Date.now()-requestTimes.get(request)});});
page.on('requestfailed',request=>{const p=new URL(request.url()).pathname;observedRequests.push({path:p,method:request.method(),elapsed_ms:Date.now()-requestTimes.get(request),failure:request.failure()?.errorText});});

const authoringOrExecutionPosts=[];
page.on('request',r=>{const p=new URL(r.url()).pathname;if(r.method()==='POST'&&(/\/authoring-jobs$|\/runs$|\/actions\/|\/save$|\/respond$/.test(p)))authoringOrExecutionPosts.push(p);});
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
  await expect(page.getByRole('button',{name:'Workflows',exact:true})).toBeVisible({timeout:45000});
  await record({id:'S01',state:'pass',label:'Updated installed workspace',summary:'The updated package opens through the normal workspace.',purpose:'Verify the owning workspace, not a detached UI route.',action:'Open the isolated workspace.',controls:['Workflows','Workspace Files'],expected:'Existing workspace navigation visible.',actual:'Normal Workflows and Files controls are available.',...await capture('S01','Workspace')});

  const snapshot=readPrivate(heat?'third-current-interaction.json':'second-current-interaction.json');
  const receipt=readPrivate(heat?'third-start-receipt.json':'second-start-receipt.json').body;
  const saved=readPrivate(heat?'heat-ui-focused-update-013-saved-revision.json':'printed-ui-configured-update-001-saved-revision.json');
  const ids=snapshot.outputs.map(value=>value.result_id).sort();
  let previousUrl;
  if(heat) previousUrl=JSON.parse(readFileSync(path.join(base,'t052-mounted-native-008/current-heat-installed-010-dom.json'),'utf8')).url;
  else previousUrl=readFileSync('artifacts/process-interfaces/083/20261003-current-printed-installed-009/workspace-walkthrough/progress.md','utf8').split('\n').filter(line=>line.startsWith('URL: ')&&line.includes('processUIKind=working')).at(-1).slice(5).trim();
  const savedUrl=new URL(previousUrl);const origin=new URL(proof.frontend_url);
  savedUrl.host=origin.host;savedUrl.protocol=origin.protocol;savedUrl.searchParams.set('processView','view-authoring-unavailable-'+kind+'-001');
  expect(savedUrl.searchParams.get('processRun')).toBe(receipt.run_id);
  await page.goto(savedUrl.href);
  const processView=page.locator('[data-testid="workspace-process-view"]:visible');
  const host=processView.getByTestId('surface-panel-host');
  const frame=host.frameLocator('iframe');
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:90000});
  await expect(frame.locator('[data-result-id]')).toHaveCount(ids.length);
  const assertParity=async()=>expect((await frame.locator('[data-result-id]').evaluateAll(es=>es.map(e=>e.getAttribute('data-result-id')))).sort()).toEqual(ids);
  await assertParity();

  await page.getByRole('button',{name:'Use common working view',exact:true}).click();
  const common=page.locator('[data-testid="common-process-view"]:visible');
  await expect(common.locator('[data-result-id]')).toHaveCount(ids.length,{timeout:45000});
  expect((await common.locator('[data-result-id]').evaluateAll(es=>es.map(e=>e.getAttribute('data-result-id')))).sort()).toEqual(ids);
  await record({id:'S02',state:'pass',label:'Saved and common results retained',summary:'The saved and common views show the same outputs.',purpose:'Check existing evidence before opening authoring controls.',action:'Click Use common working view.',controls:['Use common working view','Create or choose interface'],expected:'Exact original outputs in both views.',actual:`${ids.length} exact results retained; run ${receipt.run_id}.`,...await capture('S02','Common view')});
  await page.getByRole('button',{name:'Create or choose interface',exact:true}).click();
  const panel=page.getByRole('region',{name:'Interface for this process',exact:true});
  await expect(panel).toBeVisible();
  await expect(panel.getByRole('alert')).toBeVisible({timeout:45000});
  const reason=await panel.getByRole('alert').innerText();
  expect(reason.length).toBeGreaterThan(30);
  await panel.getByRole('textbox',{name:'How should this interface help the user?',exact:true}).fill('Compare the existing results. This is a local availability check; do not generate or run.');
  await expect(panel.getByRole('button',{name:'Create interface',exact:true})).toBeDisabled();
  await expect(panel.getByRole('button',{name:'Update selected interface',exact:true})).toBeDisabled();
  await expect(panel.getByRole('combobox',{name:'Saved interface',exact:true})).toHaveValue(saved.manifest.ui_id);
  await expect(panel.getByRole('combobox',{name:'Saved revision',exact:true})).toHaveValue(saved.manifest.revision_id);
  await expect(panel.getByRole('button',{name:'Open saved interface',exact:true})).toBeEnabled();
  await record({id:'S03',state:'pass',label:'Clear creation limit and usable saved interface',summary:'Creation is unavailable, with a visible reason; saved interfaces remain usable.',purpose:'Verify readiness fails before generation while saved reuse stays available.',action:'Open interface controls and enter a description.',controls:['Create or choose interface','How should this interface help the user?','Create interface','Update selected interface','Saved interface','Saved revision','Open saved interface'],expected:'Visible actionable reason; Create/Update disabled and exact saved interface enabled.',actual:`Reason: ${reason}. Exact saved interface and revision retained; no creation is submitted.`,...await capture('S03','Authoring unavailable')});
  await page.setViewportSize({width:480,height:900});
  await panel.scrollIntoViewIfNeeded();
  const sizes=await processView.evaluate(e=>({width:e.clientWidth,scrollWidth:e.scrollWidth}));
  expect(sizes.width).toBeGreaterThan(420);
  expect(sizes.scrollWidth).toBeLessThanOrEqual(sizes.width+1);
  await panel.evaluate(e=>e.setAttribute('data-walkthrough-authoring','true'));
  const axe=await new AxeBuilder({page}).include('[data-walkthrough-authoring="true"]').withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa']).analyze();
  writeFileSync(path.join(privateRoot,'authoring-unavailable-001-axe.json'),JSON.stringify(axe,null,2));
  expect(axe.violations).toEqual([]);
  await panel.getByRole('combobox',{name:'Saved interface',exact:true}).focus();
  await page.keyboard.press('Tab');
  await expect(panel.getByRole('combobox',{name:'Saved revision',exact:true})).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(panel.getByRole('button',{name:'Open saved interface',exact:true})).toBeFocused();
  await record({id:'S04',state:'pass',label:'Compact authoring and keyboard access',summary:'Authoring controls remain usable at compact width and accessible by keyboard.',purpose:'Check real installed control layout and scoped automated accessibility.',action:'Resize to480px, focus Saved interface and press Tab twice.',controls:['Saved interface','Saved revision','Open saved interface'],expected:'No outer overflow, zero scoped automated violations, exact keyboard focus order.',actual:`Document ${sizes.width}px/${sizes.scrollWidth}px; zero WCAG A/AA violations; keyboard reaches exact saved revision and Open saved interface.`,...await capture('S04','Compact authoring')});
  const reopening=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/present'),{timeout:90000});
  await page.keyboard.press('Enter');
  const response=await reopening;
  expect(response.status()).toBe(200);
  const issued=await response.json();
  expect(issued.binding).toMatchObject({run_id:receipt.run_id,ui_id:saved.manifest.ui_id,revision_id:saved.manifest.revision_id});
  const restored=page.locator('[data-testid="workspace-process-view"]:visible');
  const restoredFrame=restored.getByTestId('surface-panel-host').frameLocator('iframe');
  await expect(restoredFrame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:90000});
  await expect(restoredFrame.locator('[data-result-id]')).toHaveCount(ids.length);
  expect((await restoredFrame.locator('[data-result-id]').evaluateAll(es=>es.map(e=>e.getAttribute('data-result-id')))).sort()).toEqual(ids);
  await record({id:'S05',state:'pass',label:'Saved interface opens while creation is unavailable',summary:'Keyboard activation opens the exact saved interface in the same workspace.',purpose:'Verify real native saved reuse and unchanged engineering context.',action:'Press Enter on Open saved interface.',controls:['Open saved interface','Working tab'],expected:'Exact UI/revision/run with all original outputs and no generation.',actual:`Exact backend binding and ${ids.length} result identities verified; no creation, process start, review or action submitted.`,...await capture('S05','Saved interface restored')});
  expect(authoringOrExecutionPosts).toEqual([]);
  expect(diagnostics.pageErrors).toEqual([]);
  expect(diagnostics.failedResponses.filter(value=>!(value.path==='/api/agent/models'&&value.status===503))).toEqual([]);
  expect(diagnostics.console.filter(value=>!value.includes('503 (Service Unavailable)')&&!value.startsWith('Failed to fetch Hermes model options Error: Failed to list Hermes models: Service Unavailable'))).toEqual([]);
  writeFileSync(path.join(privateRoot,'authoring-unavailable-001-retention.json'),JSON.stringify({run_id:receipt.run_id,ui_id:saved.manifest.ui_id,revision_id:saved.manifest.revision_id,result_ids:ids,reason,sizes,authoringOrExecutionPosts,diagnostics},null,2));
  status.overall='pass';
}
 catch(error){
  status.overall='blocked';
  await record({id:'STOP',state:'blocked',label:'Entry stopped',summary:'The normal workspace entry did not meet the expected state.',purpose:'Retain the first stopping point.',action:'Stop at the unexpected entry state.',controls:['Workflows'],expected:'Workspace and established editor available.',actual:error.message,...await capture('STOP','Stopping point')});
  writeFileSync(path.join(privateRoot,'authoring-unavailable-001-dom.json'),JSON.stringify({url:cleanUrl(),body:await page.locator('body').innerText(),buttons:await page.locator('button').evaluateAll(es=>es.map(e=>({text:e.textContent,label:e.getAttribute('aria-label'),id:e.getAttribute('data-testid')})))},null,2));
} finally {
  publish();
  writeFileSync(path.join(root,'browser-diagnostics.json'),JSON.stringify(diagnostics,null,2));
  writeFileSync(path.join(root,'presentation-request-timings.json'),JSON.stringify(observedRequests,null,2));
  await context.tracing.stop({path:path.join(privateRoot,'authoring-unavailable-001-trace.zip')});
  await Promise.allSettled(presentationReplies);
  const cleanup=[];
  for(const value of ownedViews.values()){
    if(value.binding.process.workspace_id!==proof.workspace_id||value.binding.process.source_digest!==prepared.expected_storage_digest)throw new Error('Refuse cleanup outside this owned proof');
    const closeStatus=await page.evaluate(async data=>{try {const response=await fetch('/api/workspace/process-interfaces/presentations/close',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});return response.status;}catch{return 0;}},{session_id:proof.session_id,path:prepared.path,expected_storage_digest:prepared.expected_storage_digest,surface_id:value.descriptor.surfaceId,presentation_id:value.binding.presentation_id});
    cleanup.push({presentation_id:value.binding.presentation_id,status:closeStatus});
  }
  writeFileSync(path.join(privateRoot,'authoring-unavailable-001-view-cleanup.json'),JSON.stringify(cleanup,null,2));
  await browser.close();
  console.log(JSON.stringify({status:status.overall,report:path.join(root,'report.html'),steps:status.steps.map(s=>({id:s.id,state:s.state,actual:s.actual}))}));
}


