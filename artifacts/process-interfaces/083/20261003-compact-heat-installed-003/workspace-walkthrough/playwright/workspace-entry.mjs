import AxeBuilder from '@axe-core/playwright';
import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const kind=process.argv[2]; if(!['heat','printed'].includes(kind))throw new Error('Select exact isolated proof kind');
const heat=kind==='heat';
const base=path.resolve('.local-run/process-interfaces-083');
const privateRoot=path.join(base,heat?'t052-mounted-native-010':'t052-mounted-native-011');
const readPrivate=name=>JSON.parse(readFileSync(path.join(privateRoot,name),'utf8')); 
const proof = JSON.parse(readFileSync(path.join(privateRoot, 'browser-context.json'), 'utf8'));
const prepared = JSON.parse(readFileSync(path.join(privateRoot, 'prepared-run.json'), 'utf8'));
const root=path.resolve('artifacts/process-interfaces/083/20261003-compact-'+kind+'-installed-003/workspace-walkthrough');
if (existsSync(root)) throw new Error('Preserve the previous walkthrough; select a fresh root');
for (const dir of ['playwright','screenshots/raw','screenshots/annotated','trace']) mkdirSync(path.join(root, dir), {recursive:true});
const status = {title:'Compact '+kind+' working interface and workspace navigation', summary:'Normal Wright workspace and actual isolated engineering run. No mocked routes or physical action.', overall:'pending', updated:new Date().toISOString(), manualSteps:[{label:'Open saved interface',instruction:'Open the saved working-interface link for the proof run.'},{label:'Desktop preference',instruction:'At desktop width, open Workspace Files.'},{label:'Compact navigation',instruction:'Resize to480px. Open Files, then close with Escape, Close or Return to workspace.'},{label:'Restore',instruction:'Resize back to1440px and check the file panel returns.'},{label:'Editor',instruction:'At compact width click Open workflow and inspect Diagram and Source.'}], steps:[]};
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
async function record(step){status.steps.push(step);publish();appendFileSync(path.join(root,'progress.md'),`\n## ${new Date().toISOString()} UTC — ${step.label}\n\nURL: ${cleanUrl()}\nAction: ${step.action}\nControls: ${step.controls.join(', ')}\nExpected: ${step.expected}\nActual: ${step.actual}\nStatus: ${step.state}\nScreenshots: ${step.raw??''}; ${step.annotated??''}\n`);}
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
  savedUrl.host=origin.host;savedUrl.protocol=origin.protocol;savedUrl.searchParams.set('processView','view-compact-'+kind+'-001');
  expect(savedUrl.searchParams.get('processRun')).toBe(receipt.run_id);
  await page.goto(savedUrl.href);
  const processView=page.locator('[data-testid="workspace-process-view"]:visible');
  const host=processView.getByTestId('surface-panel-host');
  const frame=host.frameLocator('iframe');
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:90000});
  await expect(frame.locator('[data-result-id]')).toHaveCount(ids.length);
  const assertParity=async()=>expect((await frame.locator('[data-result-id]').evaluateAll(es=>es.map(e=>e.getAttribute('data-result-id')))).sort()).toEqual(ids);
  await assertParity();
  const initialFrame=await host.locator('iframe').elementHandle();
  const files=page.getByTestId('activity-bar-explorer-btn');
  const sidebar=page.getByTestId('workspace-sidebar');
  if(!await sidebar.isVisible())await files.click();
  await expect(sidebar).toBeVisible();
  await expect(files).toHaveAttribute('aria-expanded','true');
  const layoutKey='wright-workspace-layout-'+proof.workspace_id;
  await expect.poll(()=>page.evaluate(key=>JSON.parse(localStorage.getItem(key)).isSidebarCollapsed,layoutKey)).toBe(false);
  const desktopWidth=await sidebar.evaluate(e=>e.getBoundingClientRect().width);
  await record({id:'S02',state:'pass',label:'Saved engineering interface and desktop navigation',summary:'The same exact results render with the desktop file panel open.',purpose:'Establish saved identity and desktop preference before compact resizing.',action:'Open the saved working link; click Workspace Files if closed.',controls:['Workspace Files','Working tab'],expected:'Exact recorded results and docked navigation.',actual:`${ids.length} exact result identities; docked file panel ${desktopWidth}px wide.`,...await capture('S02','Desktop working interface')});

  await page.setViewportSize({width:480,height:900});
  await expect(sidebar).not.toBeVisible();
  await expect(files).toHaveAttribute('aria-expanded','false');
  await expect.poll(()=>processView.evaluate(e=>e.getBoundingClientRect().width)).toBeGreaterThan(420);
  await assertParity();
  expect(await host.locator('iframe').evaluate((e,old)=>e===old,initialFrame)).toBe(true);
  const frameSize=await frame.locator('body').evaluate(e=>({clientWidth:e.clientWidth,scrollWidth:e.scrollWidth,overflowX:getComputedStyle(e).overflowX}));
  writeFileSync(path.join(privateRoot,'compact-'+kind+'-body-metrics.json'),JSON.stringify(frameSize,null,2));
  if(frameSize.scrollWidth>frameSize.clientWidth+1)expect(frameSize.overflowX).not.toMatch(/hidden|clip/);
  await expect(processView.getByTestId('process-open-definition')).toBeVisible();
  await record({id:'S03',state:'pass',label:'Compact content gets the workspace width',summary:'The file panel no longer consumes the compact document width.',purpose:'Check actual document/iframe width and retained engineering results.',action:'Resize to 480 by 900.',controls:['Workspace Files','Open workflow'],expected:'Navigation closed; document wider than420px; same live frame/results.',actual:`Document ${await processView.evaluate(e=>e.clientWidth)}px; embedded body ${frameSize.clientWidth}px with ${frameSize.scrollWidth}px scroll width and ${frameSize.overflowX} horizontal overflow; same iframe and results.`,...await capture('S03','Compact working interface')});

  await files.click();await expect(sidebar).toBeVisible();
  await expect(files).toHaveAttribute('aria-expanded','true');
  await expect(page.getByRole('button',{name:'Close workspace navigation',exact:true})).toBeFocused();
  expect(await sidebar.evaluate(e=>getComputedStyle(e).position)).toBe('absolute');
  await expect.poll(()=>processView.evaluate(e=>e.clientWidth)).toBeGreaterThan(420);
  await record({id:'S04',state:'pass',label:'Files remains accessible as compact navigation',summary:'Files opens over the working view without resizing or restarting it.',purpose:'Keep normal file navigation available at compact widths.',action:'Click Workspace Files.',controls:['Workspace Files','Close workspace navigation','Return to workspace'],expected:'Focused close control and overlay navigation; document width unchanged.',actual:'Compact overlay opens; Close is focused; the same iframe keeps its available width.',...await capture('S04','Compact Files')});
  await page.keyboard.press('Escape');await expect(sidebar).not.toBeVisible();await expect(files).toBeFocused();
  await files.click();await page.getByRole('button',{name:'Return to workspace',exact:true}).click();await expect(sidebar).not.toBeVisible();
  await files.click();await page.getByRole('button',{name:'Close workspace navigation',exact:true}).click();await expect(sidebar).not.toBeVisible();
  await assertParity();
  await expect.poll(()=>page.evaluate(key=>JSON.parse(localStorage.getItem(key)).isSidebarCollapsed,layoutKey)).toBe(false);
  await record({id:'S05',state:'pass',label:'Compact return and keyboard focus',summary:'Escape, Close and clicking back to the workspace all dismiss navigation.',purpose:'Verify return controls and preservation of the desktop preference.',action:'Press Escape; reopen Files and click Return to workspace; reopen and click Close.',controls:['Workspace Files','Close workspace navigation','Return to workspace'],expected:'Navigation closes; Escape returns focus; desktop preference remains expanded.',actual:'All three return paths work; Escape restores Files focus; desktop preference and exact results are preserved.',...await capture('S05','Returned working view')});

  for(const width of [360,640]){
    await page.setViewportSize({width,height:900});
    await expect.poll(()=>processView.evaluate(e=>e.clientWidth)).toBeGreaterThan(width-55);
    await assertParity();
    await expect(sidebar).not.toBeVisible();
    await expect(processView.getByTestId('process-open-definition')).toBeVisible();
  }
  await record({id:'S06',state:'pass',label:'Small phone and wider compact workspace',summary:'The working view remains available at360px and640px.',purpose:'Check container-driven compact layout on both sides of480px.',action:'Resize to360px, then640px.',controls:['Workspace Files','Open workflow'],expected:'Available document width and same exact results.',actual:'Both compact sizes use the available width with navigation closed; result identities remain exact.',...await capture('S06','Compact size coverage')});
  await page.setViewportSize({width:1440,height:1000});
  await expect(sidebar).toBeVisible();
  await expect(files).toHaveAttribute('aria-expanded','true');
  expect(await sidebar.evaluate(e=>e.getBoundingClientRect().width)).toBe(desktopWidth);
  await assertParity();
  expect(await host.locator('iframe').evaluate((e,old)=>e===old,initialFrame)).toBe(true);
  await record({id:'S07',state:'pass',label:'Desktop layout restored without presentation replay',summary:'Returning to desktop restores the docked Files preference.',purpose:'Verify resizing is presentation-only and preserves existing preference/frame.',action:'Resize back to1440 by1000.',controls:['Workspace Files','Working tab'],expected:'Original sidebar width and same frame/results.',actual:'The original docked file panel returns; iframe identity and all result IDs are unchanged.',...await capture('S07','Restored desktop')});
  await page.setViewportSize({width:480,height:900});
  await files.click();
  const axe=await new AxeBuilder({page}).include('[data-testid="workspace-sidebar"]').withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa']).analyze();
  writeFileSync(path.join(privateRoot,'compact-'+kind+'-axe.json'),JSON.stringify(axe,null,2));
  expect(axe.violations).toEqual([]);
  await page.keyboard.press('Escape');
  await processView.getByTestId('process-open-definition').click();
  await expect(page.getByText('Diagram',{exact:true})).toBeVisible({timeout:45000});
  await expect(page.getByText('Source',{exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'Use saved process',exact:true})).toBeVisible();
  await record({id:'S08',state:'pass',label:'Compact accessibility and editor return',summary:'Navigation passes the scoped accessibility scan and Open workflow returns to the existing editor.',purpose:'Preserve the complementary editor journey and accessible compact controls.',action:'Open Files, scan navigation, close it and click Open workflow.',controls:['Workspace Files','Open workflow','Diagram','Source','Use saved process'],expected:'Zero scoped automated violations and existing editor available.',actual:'Navigation has zero WCAG A/AA violations; Diagram, Source and Use saved process remain available.',...await capture('S08','Compact editor return')});

  expect(authoringOrExecutionPosts).toEqual([]);
  expect(diagnostics.pageErrors).toEqual([]);
  expect(diagnostics.failedResponses.filter(value=>!(value.path==='/api/agent/models'&&value.status===503))).toEqual([]);
  expect(diagnostics.console.filter(value=>!value.includes('503 (Service Unavailable)')&&!value.startsWith('Failed to fetch Hermes model options Error: Failed to list Hermes models: Service Unavailable'))).toEqual([]);
  writeFileSync(path.join(privateRoot,'compact-'+kind+'-retention.json'),JSON.stringify({run_id:receipt.run_id,ui_id:saved.manifest.ui_id,revision_id:saved.manifest.revision_id,result_ids:ids,desktop_sidebar_width:desktopWidth,frameSize,authoringOrExecutionPosts,diagnostics},null,2));
  status.overall='pass';
}
 catch(error){
  status.overall='blocked';
  await record({id:'STOP',state:'blocked',label:'Entry stopped',summary:'The normal workspace entry did not meet the expected state.',purpose:'Retain the first stopping point.',action:'Stop at the unexpected entry state.',controls:['Workflows'],expected:'Workspace and established editor available.',actual:error.message,...await capture('STOP','Stopping point')});
  writeFileSync(path.join(privateRoot,'compact-installed-003-dom.json'),JSON.stringify({url:cleanUrl(),body:await page.locator('body').innerText(),buttons:await page.locator('button').evaluateAll(es=>es.map(e=>({text:e.textContent,label:e.getAttribute('aria-label'),id:e.getAttribute('data-testid')})))},null,2));
} finally {
  publish();
  writeFileSync(path.join(root,'browser-diagnostics.json'),JSON.stringify(diagnostics,null,2));
  writeFileSync(path.join(root,'presentation-request-timings.json'),JSON.stringify(observedRequests,null,2));
  await context.tracing.stop({path:path.join(privateRoot,'compact-installed-003-trace.zip')});
  await Promise.allSettled(presentationReplies);
  const cleanup=[];
  for(const value of ownedViews.values()){
    if(value.binding.process.workspace_id!==proof.workspace_id||value.binding.process.source_digest!==prepared.expected_storage_digest)throw new Error('Refuse cleanup outside this owned proof');
    const closeStatus=await page.evaluate(async data=>{try {const response=await fetch('/api/workspace/process-interfaces/presentations/close',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});return response.status;}catch{return 0;}},{session_id:proof.session_id,path:prepared.path,expected_storage_digest:prepared.expected_storage_digest,surface_id:value.descriptor.surfaceId,presentation_id:value.binding.presentation_id});
    cleanup.push({presentation_id:value.binding.presentation_id,status:closeStatus});
  }
  writeFileSync(path.join(privateRoot,'compact-installed-003-view-cleanup.json'),JSON.stringify(cleanup,null,2));
  await browser.close();
  console.log(JSON.stringify({status:status.overall,report:path.join(root,'report.html'),steps:status.steps.map(s=>({id:s.id,state:s.state,actual:s.actual}))}));
}


