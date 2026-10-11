import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const privateRoot = path.resolve('.local-run/process-interfaces-083/t052-mounted-native-009');
const proof = JSON.parse(readFileSync(path.join(privateRoot, 'browser-context.json'), 'utf8'));
const prepared = JSON.parse(readFileSync(path.join(privateRoot, 'prepared-run.json'), 'utf8'));
const root = path.resolve('artifacts/process-interfaces/083/20261003-current-printed-installed-011/workspace-walkthrough');
if (existsSync(root)) throw new Error('Preserve the previous walkthrough; select a fresh root');
for (const dir of ['playwright','screenshots/raw','screenshots/annotated','trace']) mkdirSync(path.join(root, dir), {recursive:true});
const status = {title:'Exact preparation geometry, toolpaths and held assessment in both working views', summary:'Normal Wright workspace and actual isolated engineering run. No mocked routes or physical action.', overall:'pending', updated:new Date().toISOString(), manualSteps:[
 {label:'Open process',instruction:'Open the proof workspace, click Workflows, choose the saved wheel process and click Use saved process.'},
 {label:'Inspect the held preparation run',instruction:'Open the recorded second-run link and inspect its preparation results and human-review hold.'},
 {label:'Reuse the interface',instruction:'Click Create or choose interface, select Focus-wheel configured preparation and click Open saved interface.'},
 {label:'Inspect geometry',instruction:'Reload the saved working interface, then click Open representation on repaired_mesh.stl.'},
 {label:'Inspect producer',instruction:'Return to the saved interface and click Open producing step on repaired_mesh.stl.'},
], steps:[]};
const escape = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function publish() {
  status.updated = new Date().toISOString();
  writeFileSync(path.join(root,'status.json'),JSON.stringify(status,null,2));
  writeFileSync(path.join(root,'report.html'),`<!doctype html><html><head><meta charset="utf-8"><title>${escape(status.title)}</title><style>body{font:16px system-ui;max-width:1100px;margin:24px auto;background:#101922;color:#e8f4f7}section{padding:18px;border:1px solid #647486;margin:16px 0}.pass{border-color:#64bda4}.blocked{border-color:#ee7373}img{max-width:100%}a{color:#7fe0cb}</style></head><body><h1>${escape(status.title)}</h1><p>${escape(status.summary)}</p><p>Status: ${escape(status.overall)}</p><h2>Manual steps</h2><ol>${status.manualSteps.map(s=>`<li>${escape(s.instruction)}</li>`).join('')}</ol>${status.steps.map(s=>`<section class="${s.state}"><h2>${escape(s.label)} · ${escape(s.state)}</h2><p>${escape(s.summary)}</p><p>Expected: ${escape(s.expected)}</p><p>Actual: ${escape(s.actual)}</p>${['raw','annotated'].filter(k=>s[k]).map(k=>`<p>${k}<a class="image-button" href="${escape(s[k])}" onclick="event.preventDefault();document.getElementById('full-image').src=this.href;document.getElementById('image-dialog').showModal()"><img src="${escape(s[k])}" alt="${escape(s.label)} ${k}"></a></p>`).join('')}</section>`).join('')}<dialog id="image-dialog"><button onclick="document.getElementById('image-dialog').close()">Close</button><img id="full-image" style="max-width:none" alt="Full-size walkthrough evidence"></dialog></body></html>`);
}
writeFileSync(path.join(root,'progress.md'),'# Printed second-run saved-interface walkthrough\n\nPrepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.\n');
publish();
writeFileSync(path.join(root,'playwright','workspace-entry.mjs'),readFileSync(new URL(import.meta.url)));
const browser = await chromium.launch({headless:true});
const context = await browser.newContext({viewport:{width:1440,height:1000}});
await context.addCookies([{name:'wright_session',value:proof.browser_cookie,url:proof.frontend_url+'/api',httpOnly:true,sameSite:'Strict'}]);
await context.tracing.start({screenshots:true,snapshots:true,sources:true});
const navigationReplies=[];
await context.exposeBinding('__wrightProofNavigation',({frame},value)=>{
  const origin=new URL(frame.url());
  if(!origin.hostname.startsWith('s-')||!origin.hostname.endsWith('.wright.localhost')||origin.port!==new URL(proof.frontend_url).port)throw new Error('Unexpected navigation observer origin');
  if(JSON.stringify(value).length>2097152)throw new Error('Navigation observation exceeds its supported bound');
  navigationReplies.push(value);
});
await context.addInitScript(()=>{
  const originalFetch=window.fetch.bind(window);
  window.fetch=async (...args)=>{
    const response=await originalFetch(...args);
    if(new URL(response.url).pathname==='/__wright/process/navigation'){
      const body=await response.clone().json();
      await window.__wrightProofNavigation({status:response.status,body});
    }
    return response;
  };
});
const page = await context.newPage();
const diagnostics={console:[],pageErrors:[],failedResponses:[]};
const authoringOrExecutionPosts=[];
const ownedViews=new Map();const presentationReplies=[];
page.on('response',response=>{const p=new URL(response.url()).pathname;if(response.status()===200&&response.request().method()==='POST'&&(p.endsWith('/present')||p.endsWith('/preview'))){const collecting=response.json().then(value=>{if(value.descriptor?.surfaceId&&value.binding?.presentation_id)ownedViews.set(value.binding.presentation_id,value);}).catch(()=>{});presentationReplies.push(collecting);}});
page.on('request',r=>{const p=new URL(r.url()).pathname;if(r.method()==='POST'&&(/\/authoring-jobs$|\/runs$|\/actions\/|\/save$|\/preview$/.test(p)))authoringOrExecutionPosts.push(p);});
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
  await record({id:'S01',state:'pass',label:'Installed preparation workspace',summary:'Continue the retained walkthrough at its first unverified assessment.',purpose:'Reuse the same isolated installed host without replaying preparation.',action:'Open the proof workspace.',controls:['Workflows'],expected:'Normal workspace available.',actual:'The existing workspace opens.',...await capture('S01','Preparation workspace')});
  const receipt=JSON.parse(readFileSync(path.join(privateRoot,'second-start-receipt.json'),'utf8')).body;
  const snapshot=JSON.parse(readFileSync(path.join(privateRoot,'second-current-interaction.json'),'utf8'));
  const saved=JSON.parse(readFileSync(path.join(privateRoot,'printed-ui-configured-update-001-saved-revision.json'),'utf8'));
  const ids=snapshot.outputs.map(value=>value.result_id).sort();
  const result=snapshot.outputs.find(value=>value.port_id==='repaired_mesh');expect(result).toBeTruthy();
  const toolpathOutput=snapshot.outputs.find(value=>value.port_id==='support_preview');expect(toolpathOutput).toBeTruthy();
  const toolpathDocument=JSON.parse(readFileSync(path.join(proof.workspace_root,toolpathOutput.representations[0].artifact_ref),'utf8'));
  const previousProgress=readFileSync('artifacts/process-interfaces/083/20261003-current-printed-installed-009/workspace-walkthrough/progress.md','utf8');
  const savedUrl=previousProgress.split('\n').filter(line=>line.startsWith('URL: ')&&line.includes('processUIKind=working')).at(-1).slice(5).trim();
  const savedBinding=new URL(savedUrl);
  expect(savedBinding.origin).toBe(proof.frontend_url);
  expect(savedBinding.searchParams.get('processDigest')).toBe(prepared.expected_storage_digest);
  expect(savedBinding.searchParams.get('processRun')).toBe(receipt.run_id);
  expect(savedBinding.searchParams.get('processUI')).toBe(saved.manifest.ui_id);
  expect(savedBinding.searchParams.get('processUIRevision')).toBe(saved.manifest.revision_id);
  const frame=page.locator('[data-testid="surface-panel-host"]:visible').frameLocator('iframe');
  const card=frame.locator('[data-result-id="'+result.result_id+'"]');
  await page.goto(savedUrl);
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:45000});
  const assessmentNavigationIndex=navigationReplies.length;
  await card.getByRole('button',{name:'Open assessment',exact:true}).click();
  const evidence=page.locator('[data-testid="common-process-view"]:visible');
  await expect(evidence.locator('pre').filter({hasText:'"pass": 17'})).toBeVisible({timeout:45000});
  await expect(evidence.locator('pre').filter({hasText:'"blocked": 1'})).toBeVisible();
  const gate=JSON.parse(readFileSync(path.join(privateRoot,'second-source-gate-event.json'),'utf8'));
  await expect(evidence.locator('pre').filter({hasText:gate.assessment_id})).toBeVisible();
  await expect.poll(()=>navigationReplies.length).toBeGreaterThan(assessmentNavigationIndex);const assessmentResponse=navigationReplies[assessmentNavigationIndex];expect(assessmentResponse.status).toBe(200);
  const assessmentResolution=assessmentResponse.body;
  const frozen=JSON.parse(readFileSync(path.join(privateRoot,'second-run-frozen.json'),'utf8'));
  const assessmentFile=frozen.files.find(f=>f.path===gate.assessment_path);expect(assessmentFile).toBeTruthy();
  expect(assessmentResolution.target.kind).toBe('assessment');
  expect(assessmentResolution.target.assessment_id).toBe(gate.assessment_id);
  expect(assessmentResolution.target.run_id).toBe(receipt.run_id);
  expect(assessmentResolution.target.result_id).toBe(result.result_id);
  expect(assessmentResolution.process.source_path).toBe(prepared.path);
  expect(assessmentResolution.process.source_digest).toBe(prepared.expected_storage_digest);
  expect(assessmentResolution.representation.artifact_ref).toBe(gate.assessment_path);
  expect(assessmentResolution.representation.sha256).toBe(assessmentFile.sha256);
  writeFileSync(path.join(privateRoot,'current-printed-installed-011-assessment-navigation.json'),JSON.stringify(assessmentResolution,null,2));
  expect(await page.evaluate(()=>document.activeElement?.closest('[data-result-id]')?.getAttribute('data-result-id'))).toBe(result.result_id);
  await record({id:'S10A',state:'pass',label:'The original exact held assessment opens',summary:'The digital checks and required human review remain distinct from release.',purpose:'Verify exact assessment navigation and requested result focus.',action:'Click Open assessment on repaired_mesh.stl.',controls:['Open assessment'],expected:'17 passed checks, one mandatory review hold, exact repaired result focus.',actual:'The original full source assessment opens on the exact requested result.',...await capture('S10A','Original held assessment')});
  await page.goto(savedUrl);await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:45000});
  await frame.locator('[data-result-id="'+toolpathOutput.result_id+'"]').getByRole('button',{name:'Open representation',exact:true}).click();
  const tailoredPaths=frame.getByRole('img',{name:'Rotatable 3D toolpaths from all supported layers',exact:true});
  await expect(tailoredPaths.locator('canvas')).toBeVisible({timeout:45000});
  await expect(frame.getByRole('slider')).toHaveAttribute('max',String(toolpathDocument.layers.length));
  await frame.getByRole('slider').focus();await page.keyboard.press('Home');await page.keyboard.press('ArrowRight');
  await expect(frame.getByRole('slider')).toHaveValue('2');
  await frame.getByLabel('Support paths',{exact:true}).uncheck();
  await expect(frame.getByLabel('Support paths',{exact:true})).not.toBeChecked();
  await frame.getByRole('slider').focus();await page.keyboard.press('End');
  await frame.getByLabel('Support paths',{exact:true}).check();
  await tailoredPaths.scrollIntoViewIfNeeded();
  await record({id:'S10T',state:'pass',label:'Saved interface exposes the same actual nominal toolpaths',summary:'The shared viewer retains the recorded layers and honest passive scope.',purpose:'Verify common/tailored actual toolpath identity and control parity.',action:'Reopen the saved interface, open support-preview.json and exercise layer and support visibility controls.',controls:['Open representation','Layers','Support paths'],expected:'The same '+toolpathDocument.layers.length+' recorded layers and controls.',actual:'Identical nominal toolpath evidence renders in the saved interface.',...await capture('S10T','Saved nominal paths')});
  await page.goto(savedUrl);await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:45000});
  const producerNavigationIndex=navigationReplies.length;
  await card.getByRole('button',{name:'Open producing step',exact:true}).click();
  const editor=page.locator('[data-workflow-file="'+prepared.path+'"]:visible');
  await expect(editor).toBeVisible({timeout:45000});
  await expect.poll(()=>navigationReplies.length).toBeGreaterThan(producerNavigationIndex);const navigationResponse=navigationReplies[producerNavigationIndex];expect(navigationResponse.status).toBe(200);
  const resolution=navigationResponse.body;
  expect(resolution.process.source_path).toBe(prepared.path);
  expect(resolution.process.source_digest).toBe(prepared.expected_storage_digest);
  expect(resolution.target.kind).toBe('block');
  expect(resolution.target.block_id).toBe(result.step_id);
  expect(resolution.target.run_id).toBe(receipt.run_id);
  const editorBlockId='block.'+result.step_id.replaceAll('_','-');
  await expect(editor.locator('[data-semantic-id="'+editorBlockId+'"]')).toHaveAttribute('data-selected','true',{timeout:45000});
  await expect(editor.getByTestId('workflow-recovery-inspector')).toBeVisible();
  await expect(editor.getByTestId('workflow-recovery-block-name')).toHaveValue('Repair, measure, and orient mesh');
  writeFileSync(path.join(privateRoot,'current-printed-installed-011-navigation.json'),JSON.stringify(resolution,null,2));
  await record({id:'S11',state:'pass',label:'Exact producer opens in the accepted editor',summary:'The partial result leads to its actual repair and orientation block.',purpose:'Retain the complementary working view and detailed engineering inspection.',action:'Return to the saved view and click Open producing step on repaired_mesh.stl.',controls:['Open producing step'],expected:'Accepted process and exact repaired-mesh producer selected.',actual:'The original producing block opens in the preserved editor.',...await capture('S11','Exact source producer')});
  expect(authoringOrExecutionPosts).toEqual([]);
  expect(diagnostics.pageErrors).toEqual([]);
  expect(diagnostics.failedResponses.filter(value=>!(value.path==='/api/agent/models'&&value.status===503))).toEqual([]);
  expect(diagnostics.console.filter(value=>!value.includes('503 (Service Unavailable)')&&!value.startsWith('Failed to fetch Hermes model options Error: Failed to list Hermes models: Service Unavailable'))).toEqual([]);
  writeFileSync(path.join(privateRoot,'current-printed-installed-011-retention.json'),JSON.stringify({run_id:receipt.run_id,ui_id:saved.manifest.ui_id,revision_id:saved.manifest.revision_id,common_result_ids:ids,tailored_result_ids:ids,diagnostic_codes:snapshot.diagnostics.map(d=>d.code),toolpath_layers:toolpathDocument.layers.length,toolpath_artifact:toolpathOutput.representations[0],authoringOrExecutionPosts,diagnostics},null,2));
  status.overall='pass';
} catch(error){
  status.overall='blocked';
  await record({id:'STOP',state:'blocked',label:'Entry stopped',summary:'The normal workspace entry did not meet the expected state.',purpose:'Retain the first stopping point.',action:'Stop at the unexpected entry state.',controls:['Workflows'],expected:'Workspace and established editor available.',actual:error.message,...await capture('STOP','Stopping point')});
  writeFileSync(path.join(privateRoot,'current-printed-installed-011-dom.json'),JSON.stringify({url:cleanUrl(),body:await page.locator('body').innerText(),buttons:await page.locator('button').evaluateAll(es=>es.map(e=>({text:e.textContent,label:e.getAttribute('aria-label'),id:e.getAttribute('data-testid')})))},null,2));
} finally {
  publish();
  writeFileSync(path.join(privateRoot,'current-printed-installed-011-fetch-navigation-observations.json'),JSON.stringify(navigationReplies,null,2));
  writeFileSync(path.join(root,'browser-diagnostics.json'),JSON.stringify(diagnostics,null,2));
  await context.tracing.stop({path:path.join(privateRoot,'current-printed-installed-011-trace.zip')});
  await Promise.allSettled(presentationReplies);
  const cleanup=[];
  for(const value of ownedViews.values()){
    if(value.binding.process.workspace_id!==proof.workspace_id||value.binding.process.source_digest!==prepared.expected_storage_digest)throw new Error('Refuse cleanup outside this owned proof');
    const closeStatus=await page.evaluate(async data=>{try {const response=await fetch('/api/workspace/process-interfaces/presentations/close',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});return response.status;}catch{return 0;}},{session_id:proof.session_id,path:prepared.path,expected_storage_digest:prepared.expected_storage_digest,surface_id:value.descriptor.surfaceId,presentation_id:value.binding.presentation_id});
    cleanup.push({presentation_id:value.binding.presentation_id,status:closeStatus});
  }
  writeFileSync(path.join(privateRoot,'current-printed-installed-011-view-cleanup.json'),JSON.stringify(cleanup,null,2));
  await browser.close();
  console.log(JSON.stringify({status:status.overall,report:path.join(root,'report.html'),steps:status.steps.map(s=>({id:s.id,state:s.state,actual:s.actual}))}));
}


