import AxeBuilder from '@axe-core/playwright';
import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const privateRoot = path.resolve('.local-run/process-interfaces-083/t052-mounted-native-008');
const proof = JSON.parse(readFileSync(path.join(privateRoot, 'browser-context.json'), 'utf8'));
const prepared = JSON.parse(readFileSync(path.join(privateRoot, 'prepared-run.json'), 'utf8'));
const root = path.resolve('artifacts/process-interfaces/083/20261003-current-heat-installed-014/workspace-walkthrough');
if (existsSync(root)) throw new Error('Preserve the previous walkthrough; select a fresh root');
for (const dir of ['playwright','screenshots/raw','screenshots/annotated','trace']) mkdirSync(path.join(root, dir), {recursive:true});
const status = {title:'Saved Heat comparison after repeated CAD and solver execution', summary:'Normal Wright workspace and actual isolated engineering run. No mocked routes or physical action.', overall:'pending', updated:new Date().toISOString(), manualSteps:[
 {label:'Open process',instruction:'Open the proof workspace, click Workflows, choose the saved heat workflow and click Use saved process.'},
 {label:'Attach second run',instruction:'Open the third recorded run link and inspect its CAD, analysis and held assessment results.'},
 {label:'Reuse',instruction:'Click Create or choose interface, select Heat-spreader candidate comparison and click Open saved interface. Inspect the full results; leave human reviews untouched.'},
 {label:'Reload',instruction:'Reload the working interface and inspect the same third-run results and held assessment.'},
], steps:[]};
const escape = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function publish() {
  status.updated = new Date().toISOString();
  writeFileSync(path.join(root,'status.json'),JSON.stringify(status,null,2));
  writeFileSync(path.join(root,'report.html'),`<!doctype html><html><head><meta charset="utf-8"><title>${escape(status.title)}</title><style>body{font:16px system-ui;max-width:1100px;margin:24px auto;background:#101922;color:#e8f4f7}section{padding:18px;border:1px solid #647486;margin:16px 0}.pass{border-color:#64bda4}.blocked{border-color:#ee7373}img{max-width:100%}a{color:#7fe0cb}</style></head><body><h1>${escape(status.title)}</h1><p>${escape(status.summary)}</p><p>Status: ${escape(status.overall)}</p><h2>Manual steps</h2><ol>${status.manualSteps.map(s=>`<li>${escape(s.instruction)}</li>`).join('')}</ol>${status.steps.map(s=>`<section class="${s.state}"><h2>${escape(s.label)} · ${escape(s.state)}</h2><p>${escape(s.summary)}</p><p>Expected: ${escape(s.expected)}</p><p>Actual: ${escape(s.actual)}</p>${['raw','annotated'].filter(k=>s[k]).map(k=>`<p>${k}<a class="image-button" href="${escape(s[k])}" onclick="event.preventDefault();document.getElementById('full-image').src=this.href;document.getElementById('image-dialog').showModal()"><img src="${escape(s[k])}" alt="${escape(s.label)} ${k}"></a></p>`).join('')}</section>`).join('')}<dialog id="image-dialog"><button onclick="document.getElementById('image-dialog').close()">Close</button><img id="full-image" style="max-width:none" alt="Full-size walkthrough evidence"></dialog></body></html>`);
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
async function record(step){status.steps.push(step);publish();appendFileSync(path.join(root,'progress.md'),`\n## ${new Date().toISOString()} UTC — ${step.label}\n\nURL: ${cleanUrl()}\nAction: ${step.action}\nControls: ${step.controls.join(', ')}\nExpected: ${step.expected}\nActual: ${step.actual}\nStatus: ${step.state}\nScreenshots: ${step.raw??''}; ${step.annotated??''}\n`);}
try {
  await page.goto(proof.frontend_url+'/workspace/'+proof.workspace_id);
  await expect(page.getByRole('button',{name:'Workflows',exact:true})).toBeVisible({timeout:45000});
  await record({id:'S01',state:'pass',label:'Current installed workspace entry',summary:'The normal workspace opens on the same current installed package.',purpose:'Continue unreached authoring and preview checks after retained harness failures.',action:'Open the isolated workspace.',controls:['Workflows'],expected:'Normal workspace available.',actual:'Workflows is visible on the current installed host.',...await capture('S01','Installed workspace')});
  const receipt=JSON.parse(readFileSync(path.join(privateRoot,'third-start-receipt.json'),'utf8')).body;
  const snapshot=JSON.parse(readFileSync(path.join(privateRoot,'third-current-interaction.json'),'utf8'));
  const saved=JSON.parse(readFileSync(path.join(privateRoot,'heat-ui-focused-update-013-saved-revision.json'),'utf8'));
  const savedUrl=JSON.parse(readFileSync(path.join(privateRoot,'current-heat-installed-010-dom.json'),'utf8')).url;
  const ids=snapshot.outputs.map(value=>value.result_id).sort();
  const fine=snapshot.outputs.find(value=>value.port_id==='revision_60_fine');
  const rows=readFileSync(path.join(proof.workspace_root,fine.representations[0].artifact_ref),'utf8').trim().split(/\r?\n/).length-1;
  const frame=page.locator('[data-testid="surface-panel-host"]:visible').frameLocator('iframe');
  const previewLocator=JSON.parse(readFileSync(path.join(privateRoot,'preview-locator.json'),'utf8'));
  const previewUrl=new URL(savedUrl);previewUrl.searchParams.set('processUIKind','preview');previewUrl.searchParams.set('processUIJob',previewLocator.job_id);previewUrl.searchParams.set('processView','view-installed-heat-preview-014');
  const observedPreview=[];
  page.on('response',async response=>{if(new URL(response.url()).pathname.endsWith('/__wright/process/context')&&response.status()===200){const value=await response.json().catch(()=>null);if(!value)return;observedPreview.push({read_only:value.read_only,run_id:value.run_id,ui_id:value.ui_id,revision_id:value.revision_id});}});
  const previewStarted=Date.now();
  await page.goto(previewUrl.href);
  await expect(frame.getByText('Preview - process controls are read-only.',{exact:true})).toBeVisible({timeout:90000});
  await expect(frame.locator('[data-result-id]')).toHaveCount(ids.length,{timeout:45000});
  expect((await frame.locator('[data-result-id]').evaluateAll(es=>es.map(e=>e.getAttribute('data-result-id')))).sort()).toEqual(ids);
  await expect.poll(()=>observedPreview.find(value=>value.read_only===true),{timeout:30000}).toMatchObject({read_only:true,run_id:receipt.run_id,ui_id:saved.manifest.ui_id,revision_id:saved.manifest.revision_id});
  await record({id:'S15',state:'pass',label:'Existing built preview is read-only in a workspace tab',summary:'The saved job preview renders the same exact engineering outputs without compiler/model availability.',purpose:'Prove current installed preview hosting and authoritative read-only scope.',action:'Open the retained preview link for the exact saved revision and recorded run.',controls:['Preview tab'],expected:'Read-only preview and exact same eighteen result identities.',actual:'Preview banner, backend read-only context and exact engineering result parity verified in '+(Date.now()-previewStarted)+' ms. The retained 45-second failure remains unresolved until timing and lifecycle evidence are reconciled.',...await capture('S15','Installed read-only preview')});
  await page.setViewportSize({width:1024,height:800});
  const processView=page.locator('[data-testid="workspace-process-view"]:visible');
  await expect(processView).toBeVisible();
  const measurements=await processView.evaluate(element=>({width:element.clientWidth,scrollWidth:element.scrollWidth,openWorkflowVisible:!!element.querySelector('[data-testid="process-open-definition"]')}));
  expect(measurements.scrollWidth).toBeLessThanOrEqual(measurements.width+1);
  await expect(processView.getByTestId('process-open-definition')).toBeVisible();
  writeFileSync(path.join(privateRoot,'preview-context-and-width.json'),JSON.stringify({observedPreview,measurements},null,2));
  await record({id:'S16',state:'pass',label:'Preview remains in the workspace at tablet width',summary:'The preview and definition navigation remain available within the workspace.',purpose:'Preserve practical workspace hosting at a narrower viewport.',action:'Resize to 1024 by 800 and inspect Open workflow.',controls:['Open workflow','Preview tab'],expected:'No outer horizontal overflow and reachable definition navigation.',actual:'Current preview tab remains hosted with no outer horizontal overflow and visible Open workflow.',...await capture('S16','Narrower preview workspace')});


  for(const [id,width,height] of [['S17',480,900],['S18',1440,1000]]){
    await page.setViewportSize({width,height});
    await expect(processView).toBeVisible();
    const size=await processView.evaluate(element=>({width:element.clientWidth,scrollWidth:element.scrollWidth}));
    expect(size.scrollWidth).toBeLessThanOrEqual(size.width+1);
    const openWorkflow=processView.getByTestId('process-open-definition');
    await expect(openWorkflow).toBeVisible();await openWorkflow.focus();await page.keyboard.press('Tab');
    const focus=await page.evaluate(()=>({text:document.activeElement.textContent.trim(),outline:getComputedStyle(document.activeElement).outlineWidth}));
    expect(focus.text).toBe('Create or choose interface');expect(focus.outline).toBe('3px');
    await record({id,state:'pass',label:'Preview controls at '+width+' pixels',summary:'Workspace preview controls remain reachable and keyboard focus stays visible.',purpose:'Verify responsive workspace hosting without changing engineering state.',action:'Resize and press Tab from Open workflow.',controls:['Open workflow','Create or choose interface'],expected:'No outer overflow and a visible focus ring on the next control.',actual:'No outer overflow; Create or choose interface receives Tab focus with a 3px outline.',...await capture(id,'Responsive preview')});
  }
  const cdp=await context.newCDPSession(page);await cdp.send('Emulation.setPageScaleFactor',{pageScaleFactor:2});
  expect(await page.evaluate(()=>visualViewport.scale)).toBe(2);
  await expect(processView.getByTestId('process-open-definition')).toBeVisible();
  await record({id:'S19',state:'pass',label:'Measured two-times page scale',summary:'Definition navigation remains reachable at measured page scale two.',purpose:'Check compact page scaling without claiming desktop zoom preference or assistive-technology acceptance.',action:'Set measured page scale to two and inspect Open workflow.',controls:['Open workflow'],expected:'Page scale two and reachable navigation.',actual:'visualViewport.scale is two and Open workflow remains visible.',...await capture('S19','Two-times page scale')});
  await cdp.send('Emulation.setPageScaleFactor',{pageScaleFactor:1});

  expect(rows).toBe(765);
  expect(authoringOrExecutionPosts).toEqual([]);
  expect(diagnostics).toEqual({console:[],pageErrors:[],failedResponses:[]});
  writeFileSync(path.join(privateRoot,'current-heat-installed-014-retention.json'),JSON.stringify({saved_url:savedUrl,run_id:receipt.run_id,ui_id:saved.manifest.ui_id,revision_id:saved.manifest.revision_id,common_result_ids:ids,tailored_result_ids:ids,field_sample_count:rows,authoringOrExecutionPosts,diagnostics},null,2));
  status.overall='pass';
} catch(error){
  status.overall='blocked';
  await record({id:'STOP',state:'blocked',label:'Entry stopped',summary:'The normal workspace entry did not meet the expected state.',purpose:'Retain the first stopping point.',action:'Stop at the unexpected entry state.',controls:['Workflows'],expected:'Workspace and established editor available.',actual:error.message,...await capture('STOP','Stopping point')});
  writeFileSync(path.join(privateRoot,'current-heat-installed-014-dom.json'),JSON.stringify({url:cleanUrl(),body:await page.locator('body').innerText(),buttons:await page.locator('button').evaluateAll(es=>es.map(e=>({text:e.textContent,label:e.getAttribute('aria-label'),id:e.getAttribute('data-testid')})))},null,2));
} finally {
  publish();
  writeFileSync(path.join(root,'browser-diagnostics.json'),JSON.stringify(diagnostics,null,2));
  writeFileSync(path.join(root,'presentation-request-timings.json'),JSON.stringify(observedRequests,null,2));
  await context.tracing.stop({path:path.join(privateRoot,'current-heat-installed-014-trace.zip')});
  await browser.close();
  console.log(JSON.stringify({status:status.overall,report:path.join(root,'report.html'),steps:status.steps.map(s=>({id:s.id,state:s.state,actual:s.actual}))}));
}


