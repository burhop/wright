import AxeBuilder from '@axe-core/playwright';
import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const kind=process.argv[2]; if(!['heat','printed'].includes(kind))throw new Error('Select exact isolated proof kind');
const heat=kind==='heat';
const base=path.resolve('.local-run/process-interfaces-083');
const privateRoot=path.join(base,heat?'t052-mounted-native-014':'t052-mounted-native-015');
const readPrivate=name=>JSON.parse(readFileSync(path.join(privateRoot,name),'utf8')); 
const proof = JSON.parse(readFileSync(path.join(privateRoot, 'browser-context.json'), 'utf8'));
const prepared = JSON.parse(readFileSync(path.join(privateRoot, 'prepared-run.json'), 'utf8'));
const root=path.resolve('artifacts/process-interfaces/083/20261003-current-'+kind+'-zoom-installed-020/workspace-walkthrough');
if (existsSync(root)) throw new Error('Preserve the previous walkthrough; select a fresh root');
for (const dir of ['playwright','screenshots/raw','screenshots/annotated','trace']) mkdirSync(path.join(root, dir), {recursive:true});
const status = {title:'Compact '+kind+' editor, common view and read-only preview continuation', summary:'Normal Wright workspace and actual isolated engineering run. No mocked routes or physical action.', overall:'pending', updated:new Date().toISOString(), manualSteps:[{label:'Open saved interface',instruction:'Open the saved working-interface link for the proof run.'},{label:'Desktop preference',instruction:'At desktop width, open Workspace Files.'},{label:'Compact navigation',instruction:'Resize to480px. Open Files, then close with Escape, Close or clicking the shaded space to the right of Files.'},{label:'Restore',instruction:'Resize back to1440px and check the file panel returns.'},{label:'Editor',instruction:'At compact width click Open workflow and inspect Diagram and Source.'}], steps:[]};
const escape = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function publish() {
  status.updated = new Date().toISOString();
  writeFileSync(path.join(root,'status.json'),JSON.stringify(status,null,2));
  writeFileSync(path.join(root,'report.html'),`<!doctype html><html><head><meta charset="utf-8"><title>${escape(status.title)}</title><style>body{font:16px system-ui;max-width:1100px;margin:24px auto;background:#101922;color:#e8f4f7}section{padding:18px;border:1px solid #647486;margin:16px 0}.pass{border-color:#64bda4}.blocked{border-color:#ee7373}img{max-width:100%}a{color:#7fe0cb}</style></head><body><h1>${escape(status.title)}</h1><p>${escape(status.summary)}</p><p>Status: ${escape(status.overall)}</p><h2>Manual steps</h2><ol>${status.manualSteps.map(s=>`<li>${escape(s.instruction)}</li>`).join('')}</ol>${status.steps.map(s=>`<section class="${s.state}"><h2>${escape(s.label)} · ${escape(s.state)}</h2><p>${escape(s.summary)}</p><p>Expected: ${escape(s.expected)}</p><p>Actual: ${escape(s.actual)}</p>${['raw','annotated'].filter(k=>s[k]).map(k=>`<p>${k}<a class="image-button" href="${escape(s[k])}" onclick="event.preventDefault();document.getElementById('full-image').src=this.href;document.getElementById('image-dialog').showModal()"><img src="${escape(s[k])}" alt="${escape(s.label)} ${k}"></a></p>`).join('')}</section>`).join('')}<dialog id="image-dialog"><button onclick="document.getElementById('image-dialog').close()">Close</button><img id="full-image" style="max-width:none" alt="Full-size walkthrough evidence"></dialog></body></html>`);
}
writeFileSync(path.join(root,'progress.md'),'# Heat workspace entry walkthrough\n\nPrepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.\n');
publish();
writeFileSync(path.join(root,'playwright','workspace-entry.mjs'),readFileSync(new URL(import.meta.url)));
const zoomExtension=path.join(privateRoot,'zoom-extension-020');
const zoomProfile=path.join(privateRoot,'zoom-browser-profile-020');
if(existsSync(zoomExtension)||existsSync(zoomProfile))throw new Error('Fresh private extension/profile required');
mkdirSync(zoomExtension);
writeFileSync(path.join(zoomExtension,'manifest.json'),JSON.stringify({manifest_version:3,name:'Isolated Wright browser zoom measurement',version:'1.0',permissions:['tabs'],background:{service_worker:'background.js'}}));
writeFileSync(path.join(zoomExtension,'background.js'),'chrome.runtime.onInstalled.addListener(()=>{});');
const context=await chromium.launchPersistentContext(zoomProfile,{channel:'chromium',headless:true,viewport:{width:1440,height:1000},args:[`--disable-extensions-except=${zoomExtension}`,`--load-extension=${zoomExtension}`]});
const zoomWorker=context.serviceWorkers()[0]??await context.waitForEvent('serviceworker');
const browser={close:()=>context.close()};
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
  await files.click();
  const axe=await new AxeBuilder({page}).include('[data-testid="workspace-sidebar"]').withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa']).analyze();
  writeFileSync(path.join(privateRoot,'compact-'+kind+'-axe.json'),JSON.stringify(axe,null,2));
  expect(axe.violations).toEqual([]);
  await page.keyboard.press('Escape');
  await processView.getByTestId('process-open-definition').click();
  const viewSelect=page.getByTestId('workflow-recovery-view-select');
  await expect(viewSelect).toBeVisible({timeout:45000});
  await expect(viewSelect).toHaveValue('diagram');
  await viewSelect.selectOption('code');
  await expect(page.getByTestId('workflow-recovery-source-editor')).toBeVisible();
  const acceptedSource=await page.getByTestId('workflow-recovery-source-editor').inputValue();
  expect(acceptedSource.length).toBeGreaterThan(100);
  await viewSelect.selectOption('diagram');
  await expect(page.getByRole('button',{name:'Use saved process',exact:true})).toBeVisible();
  await record({id:'S08',state:'pass',label:'Compact accessibility and editor return',summary:'Navigation passes the scoped accessibility scan and Open workflow returns to the existing editor.',purpose:'Preserve the complementary editor journey and accessible compact controls.',action:'Open Files, scan navigation, close it and click Open workflow.',controls:['Workspace Files','Open workflow','Diagram','Source','Use saved process'],expected:'Zero scoped automated violations and existing editor available.',actual:'Navigation has zero WCAG A/AA violations; Diagram, Source and Use saved process remain available.',...await capture('S08','Compact editor return')});


  await page.goto(savedUrl.href);
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:90000});
  await assertParity();
  await page.getByRole('button',{name:'Use common working view',exact:true}).click();
  const common=page.locator('[data-testid="common-process-view"]:visible');
  await expect(common.locator('[data-result-id]')).toHaveCount(ids.length,{timeout:45000});
  expect((await common.locator('[data-result-id]').evaluateAll(es=>es.map(e=>e.getAttribute('data-result-id')))).sort()).toEqual(ids);
  const commonMeasurements=await page.locator('[data-testid="workspace-process-view"]:visible').evaluate(e=>({width:e.clientWidth,scrollWidth:e.scrollWidth}));
  const overflowNodes=await common.evaluate(root=>{const limit=root.getBoundingClientRect().right;return Array.from(root.querySelectorAll('*')).map(e=>({tag:e.tagName,classes:typeof e.className==='string'?e.className:'',right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width,overflowX:getComputedStyle(e).overflowX})).filter(v=>v.right>limit+1).slice(0,60);});
  writeFileSync(path.join(privateRoot,'compact-'+kind+'-common-width-diagnostic.json'),JSON.stringify({commonMeasurements,overflowNodes},null,2));
  expect(commonMeasurements.width).toBeGreaterThan(420);
  expect(commonMeasurements.scrollWidth).toBeLessThanOrEqual(commonMeasurements.width+1);
  await record({id:'S09',state:'pass',label:'Compact common working view',summary:'The common view shows the same exact engineering outputs at the available compact width.',purpose:'Prove shared layout applies to the common fallback as well as the saved interface.',action:'Open the saved working interface and click Use common working view.',controls:['Use common working view','Open workflow'],expected:'Same exact recorded results; full available width and no outer overflow.',actual:`${ids.length} exact common results; document ${commonMeasurements.width}px with ${commonMeasurements.scrollWidth}px scroll width.`,...await capture('S09','Compact common results')});
  const previewLocator=readPrivate('preview-locator.json');
  const previewUrl=new URL(savedUrl);previewUrl.searchParams.set('processUIKind','preview');previewUrl.searchParams.set('processUIJob',previewLocator.job_id);previewUrl.searchParams.set('processView','view-compact-'+kind+'-preview-006');
  const previewIssued=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/preview'),{timeout:90000}).then(async r=>({status:r.status(),body:await r.json()}));
  await page.goto(previewUrl.href);
  const preview=await previewIssued;
  expect(preview.status).toBe(200);
  expect(preview.body.binding).toMatchObject({read_only:true,run_id:receipt.run_id,ui_id:saved.manifest.ui_id,revision_id:saved.manifest.revision_id});
  const previewView=page.locator('[data-testid="workspace-process-view"]:visible');
  const previewFrame=previewView.getByTestId('surface-panel-host').frameLocator('iframe');
  await expect(previewFrame.getByText('Preview - process controls are read-only.',{exact:true})).toBeVisible({timeout:90000});
  await expect(previewFrame.locator('[data-result-id]')).toHaveCount(ids.length);
  expect((await previewFrame.locator('[data-result-id]').evaluateAll(es=>es.map(e=>e.getAttribute('data-result-id')))).sort()).toEqual(ids);
  expect(await previewView.evaluate(e=>e.clientWidth)).toBeGreaterThan(420);
  await files.click();await expect(sidebar).toBeVisible();
  await page.keyboard.press('Escape');await expect(sidebar).not.toBeVisible();await expect(files).toBeFocused();
  await record({id:'S10',state:'pass',label:'Compact read-only preview',summary:'The preview remains a workspace tab, with the same results and accessible Files navigation.',purpose:'Verify exact backend read-only scope and compact presentation without compilation or execution.',action:'Open the retained preview link; open Files and close with Escape.',controls:['Preview tab','Workspace Files','Open workflow'],expected:'Read-only preview of the same UI revision/run and exact results; navigation return works.',actual:`Backend read-only binding and ${ids.length} exact results verified; preview has the available width and Files returns focus.`,...await capture('S10','Compact read-only preview')});
  const frameSize={common:commonMeasurements,previewWidth:await previewView.evaluate(e=>e.clientWidth)};

  await page.setViewportSize({width:1440,height:1000});
  const beforeZoom=await capture('S11-before','Read-only preview before native browser zoom');
  const beforeMetrics=await page.evaluate(()=>({innerWidth,devicePixelRatio,pageScale:visualViewport.scale}));
  const zoom=await zoomWorker.evaluate(async ({url,factor})=>{
    const candidates=(await chrome.tabs.query({})).filter(t=>t.url===url);
    if(candidates.length!==1)throw new Error('Zoom must identify exactly the owned proof tab');
    await chrome.tabs.setZoom(candidates[0].id,factor);
    return {factor:await chrome.tabs.getZoom(candidates[0].id),settings:await chrome.tabs.getZoomSettings(candidates[0].id)};
  },{url:page.url(),factor:2});
  expect(zoom.factor).toBe(2);
  await expect.poll(()=>page.evaluate(()=>innerWidth)).toBe(beforeMetrics.innerWidth/2);
  const afterMetrics=await page.evaluate(()=>({innerWidth,devicePixelRatio,pageScale:visualViewport.scale}));
  expect(afterMetrics.pageScale).toBe(1);
  expect(afterMetrics.devicePixelRatio).toBe(beforeMetrics.devicePixelRatio*2);
  await expect(previewFrame.getByText('Preview - process controls are read-only.',{exact:true})).toBeVisible();
  expect((await previewFrame.locator('[data-result-id]').evaluateAll(es=>es.map(e=>e.getAttribute('data-result-id')))).sort()).toEqual(ids);
  await record({id:'S11',state:'pass',label:'Actual 200% browser zoom on read-only preview',summary:'The browser reports tab zoom two while its layout viewport halves and pinch scale remains one.',purpose:'Qualify native browser zoom rather than page-scale emulation.',action:'Set browser Zoom to 200%.',controls:['Browser Zoom','Preview tab','Open workflow'],expected:'Browser zoom 2, CSS viewport 720px, pinch scale 1, exact read-only preview results.',actual:`Browser zoom ${zoom.factor}; viewport ${afterMetrics.innerWidth}px; pixel ratio ${afterMetrics.devicePixelRatio}; page scale ${afterMetrics.pageScale}; ${ids.length} exact results.`,beforeRaw:beforeZoom.raw,beforeAnnotated:beforeZoom.annotated,...await capture('S11','Native 200% preview')});

  await page.goto(savedUrl.href);
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:90000});
  await assertParity();
  await files.click();
  await expect(page.getByRole('button',{name:'Close workspace navigation',exact:true})).toBeFocused();
  await page.keyboard.press('Escape');await expect(files).toBeFocused();
  await record({id:'S12',state:'pass',label:'Saved working interface at native 200% zoom',summary:'The same saved interface and keyboard navigation remain available at browser zoom two.',purpose:'Verify actual result and focus retention under browser zoom.',action:'Open the saved working interface; open Files and press Escape.',controls:['Saved interface tab','Workspace Files','Close workspace navigation'],expected:'Exact saved results; Files restores keyboard focus.',actual:`All ${ids.length} exact results remain available; Files opens and Escape restores focus.`,...await capture('S12','Native 200% saved working view')});

  await page.getByRole('button',{name:'Use common working view',exact:true}).click();
  const zoomCommon=page.locator('[data-testid="common-process-view"]:visible');
  await expect(zoomCommon.locator('[data-result-id]')).toHaveCount(ids.length,{timeout:45000});
  expect((await zoomCommon.locator('[data-result-id]').evaluateAll(es=>es.map(e=>e.getAttribute('data-result-id')))).sort()).toEqual(ids);
  const zoomCommonSize=await page.locator('[data-testid="workspace-process-view"]:visible').evaluate(e=>({width:e.clientWidth,scrollWidth:e.scrollWidth}));
  expect(zoomCommonSize.scrollWidth).toBeLessThanOrEqual(zoomCommonSize.width+1);
  const zoomAxe=await new AxeBuilder({page}).include('[data-testid="workspace-process-view"]:visible').withTags(['wcag2a','wcag2aa','wcag21a','wcag21aa']).analyze();
  writeFileSync(path.join(root,'axe-common-native-zoom.json'),JSON.stringify(zoomAxe,null,2));
  expect(zoomAxe.violations).toEqual([]);
  await record({id:'S13',state:'pass',label:'Common working interface at native 200% zoom',summary:'The common fallback preserves exact results and wraps its content within the available workspace.',purpose:'Verify general working UI at native browser zoom and scoped accessibility.',action:'Click Use common working view.',controls:['Use common working view','Open workflow'],expected:'Exact results, no outer overflow, no detected WCAG A/AA violations.',actual:`${ids.length} exact results; ${zoomCommonSize.width}px client and ${zoomCommonSize.scrollWidth}px scroll width; zero scoped automated violations.`,...await capture('S13','Native 200% common view')});

  await page.locator('[data-testid="workspace-process-view"]:visible').getByTestId('process-open-definition').click();
  await expect(viewSelect).toBeVisible({timeout:45000});
  await viewSelect.selectOption('code');
  await expect(page.getByTestId('workflow-recovery-source-editor')).toHaveValue(acceptedSource);
  await viewSelect.selectOption('diagram');
  await expect(page.getByRole('button',{name:'Use saved process',exact:true})).toBeVisible();
  const afterZoom=await zoomWorker.evaluate(async url=>{const tab=(await chrome.tabs.query({})).find(t=>t.url===url);return chrome.tabs.getZoom(tab.id);},page.url());
  expect(afterZoom).toBe(2);
  await record({id:'S14',state:'pass',label:'Editor and source at native 200% zoom',summary:'Open workflow returns to the unchanged accepted source and diagram within the zoomed workspace.',purpose:'Preserve the complementary editor experience at real browser zoom.',action:'Click Open workflow, select Source, then Diagram.',controls:['Open workflow','Source','Diagram','Use saved process'],expected:'Same accepted source; browser zoom still 2.',actual:'Exact accepted source and existing diagram remain available; browser tab zoom remains 200%.',...await capture('S14','Native 200% editor')});
  writeFileSync(path.join(privateRoot,'native-zoom-'+kind+'-020.json'),JSON.stringify({method:'chrome.tabs.setZoom/getZoom via isolated test-only extension; no application script, CSS zoom or CDP page-scale emulation',beforeMetrics,afterMetrics,zoom,afterZoom,zoomCommonSize,result_ids:ids,run_id:receipt.run_id,model_or_process_or_review_requests:authoringOrExecutionPosts},null,2));
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
  writeFileSync(path.join(privateRoot,'compact-installed-019-dom.json'),JSON.stringify({url:cleanUrl(),body:await page.locator('body').innerText(),buttons:await page.locator('button').evaluateAll(es=>es.map(e=>({text:e.textContent,label:e.getAttribute('aria-label'),id:e.getAttribute('data-testid')})))},null,2));
} finally {
  publish();
  writeFileSync(path.join(root,'browser-diagnostics.json'),JSON.stringify(diagnostics,null,2));
  writeFileSync(path.join(root,'presentation-request-timings.json'),JSON.stringify(observedRequests,null,2));
  await context.tracing.stop({path:path.join(privateRoot,'compact-installed-019-trace.zip')});
  await Promise.allSettled(presentationReplies);
  const cleanup=[];
  for(const value of ownedViews.values()){
    if(value.binding.process.workspace_id!==proof.workspace_id||value.binding.process.source_digest!==prepared.expected_storage_digest)throw new Error('Refuse cleanup outside this owned proof');
    const closeStatus=await page.evaluate(async data=>{try {const response=await fetch('/api/workspace/process-interfaces/presentations/close',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});return response.status;}catch{return 0;}},{session_id:proof.session_id,path:prepared.path,expected_storage_digest:prepared.expected_storage_digest,surface_id:value.descriptor.surfaceId,presentation_id:value.binding.presentation_id});
    cleanup.push({presentation_id:value.binding.presentation_id,status:closeStatus});
  }
  writeFileSync(path.join(privateRoot,'compact-installed-019-view-cleanup.json'),JSON.stringify(cleanup,null,2));
  await browser.close();
  console.log(JSON.stringify({status:status.overall,report:path.join(root,'report.html'),steps:status.steps.map(s=>({id:s.id,state:s.state,actual:s.actual}))}));
}


