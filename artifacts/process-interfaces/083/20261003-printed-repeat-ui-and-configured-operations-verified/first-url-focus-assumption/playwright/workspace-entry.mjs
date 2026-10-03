import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const privateRoot = path.resolve('.local-run/process-interfaces-083/t047-printed-repeat-015');
const proof = JSON.parse(readFileSync(path.join(privateRoot, 'browser-context.json'), 'utf8'));
const prepared = JSON.parse(readFileSync(path.join(privateRoot, 'prepared-run.json'), 'utf8'));
const root = path.resolve('artifacts/ui-walkthrough/process-interfaces-083-printed/20261003T065553Z-printed-failed-run-exact-parity-002');
if (existsSync(root)) throw new Error('Preserve the previous walkthrough; select a fresh root');
for (const dir of ['playwright','screenshots/raw','screenshots/annotated','trace']) mkdirSync(path.join(root, dir), {recursive:true});
const status = {title:'Recorded partial geometry and failure in both working views', summary:'Normal Wright workspace and actual isolated engineering run. No mocked routes or physical action.', overall:'pending', updated:new Date().toISOString(), manualSteps:[
 {label:'Open process',instruction:'Open the proof workspace, click Workflows, choose the saved wheel process and click Use saved process.'},
 {label:'Inspect the failed run',instruction:'Open the recorded first-run link and inspect its partial results and model timeout.'},
 {label:'Reuse the interface',instruction:'Click Create or choose interface, select Focus-wheel digital preparation and click Open saved interface.'},
 {label:'Inspect geometry',instruction:'Reload the saved working interface, then click Open representation on source_mesh.stl.'},
 {label:'Inspect producer',instruction:'Return to the saved interface and click Open producing step on source_mesh.stl.'},
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
const page = await context.newPage();
const diagnostics={console:[],pageErrors:[],failedResponses:[]};
const authoringOrExecutionPosts=[];
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
  await record({id:'S01',state:'pass',label:'Workspace offers Workflows',summary:'Entered the normal authenticated workspace.',purpose:'Verify the normal workspace route with real API owners.',action:'Open Repeated focus-wheel preparation proof workspace.',controls:['Workflows'],expected:'The workspace loads and offers Workflows.',actual:'Normal workspace and Workflows control visible.',...await capture('S01','Workspace')});
  await page.getByRole('button',{name:'Workflows',exact:true}).click();
  await expect(page.getByTestId('workflow-file-menu')).toBeVisible({timeout:45000});
  await record({id:'S02',state:'pass',label:'Workflows opens the editor',summary:'The established workflow editor is available inside the workspace.',purpose:'Verify actual workspace entry without mocking.',action:'Click Workflows.',controls:['Workflows','Use saved process'],expected:'Editor and working-view action appear.',actual:'Editor and working-view action visible.',...await capture('S02','Editor')});
  await page.getByTestId('workflow-file-menu').click();
  await record({id:'S03',state:'pass',label:'Workflow file controls',summary:'The workspace offers named saved workflows.',purpose:'Use the existing saved file chooser.',action:'Click Workflow files.',controls:['Workflow files','Open workflow'],expected:'Open workflow is offered.',actual:'Existing file actions are visible.',...await capture('S03','Workflow files')});
  await page.getByTestId('workflow-file-open').click();
  await expect(page.getByTestId('workflow-file-choice-'+prepared.path)).toBeVisible({timeout:45000});
  await record({id:'S04',state:'pass',label:'Choose the focus-wheel workflow',summary:'The exact accepted focus-wheel workflow appears in the saved files.',purpose:'Choose the engineering process by its saved file.',action:'Click Open workflow.',controls:['Open workflow',prepared.path],expected:'The accepted focus-wheel workflow is listed.',actual:'Exact accepted workflow choice visible.',...await capture('S04','Workflow chooser')});
  await page.getByTestId('workflow-file-choice-'+prepared.path).click();
  const heatEditor = page.locator('[data-workflow-file="'+prepared.path+'"]:visible');
  await expect(heatEditor).toBeVisible({timeout:45000});
  await expect(heatEditor.getByTestId('workflow-file-menu')).toBeVisible({timeout:45000});
  await expect(heatEditor.getByTestId('workflow-working-view-open')).toBeEnabled();
  await record({id:'S05',state:'pass',label:'Focus-wheel workflow diagram',summary:'The original focus-wheel assignment opens with its connected review, geometry and slicing stages.',purpose:'Keep authoring and working views on the accepted source.',action:'Choose the accepted focus-wheel workflow file.',controls:[prepared.path,'Use saved process'],expected:'Accepted heat diagram and working view action available.',actual:'Exact saved heat source is open.',...await capture('S05','Focus-wheel diagram')});
  await heatEditor.getByTestId('workflow-working-view-open').click();
  await expect(page.getByTestId('common-process-view')).toBeVisible({timeout:45000});
  await record({id:'S06',state:'pass',label:'Shared working view',summary:'The process working interface opens in another Wright workspace tab.',purpose:'Verify shared inputs and readiness without creating another executor.',action:'Click Use saved process.',controls:['Use saved process'],expected:'Common working view in a workspace tab.',actual:'Common working view visible.',...await capture('S06','Common view')});
  const receipt = JSON.parse(readFileSync(path.join(privateRoot,'first-start-receipt.json'),'utf8')).body;
  const attached = new URL(page.url()); attached.searchParams.set('processRun',receipt.run_id);
  await page.goto(attached.href);
  await expect(page.getByTestId('common-process-view')).toBeVisible({timeout:45000});

  await record({id:'S07',state:'pass',label:'Attach the actual focus-wheel run',summary:'The working view reads the same isolated backend run.',purpose:'Use actual process state for interface composition.',action:'Reopen the recorded focus-wheel run link.',controls:['Create or choose interface'],expected:'The common working view attaches without starting another run.',actual:'Existing focus-wheel run attached.',...await capture('S07','Attached focus-wheel run')});

  const snapshot=JSON.parse(readFileSync(path.join(privateRoot,'first-current-interaction.json'),'utf8'));
  expect(snapshot.context.run_id).toBe(receipt.run_id);
  expect(snapshot.state).toBe('failed');
  expect(snapshot.diagnostics.map(d=>d.code)).toEqual(['MODEL_UNAVAILABLE']);
  expect(snapshot.outputs).toHaveLength(2);
  const ids=snapshot.outputs.map(o=>o.result_id).sort();
  const common=page.locator('[data-testid="common-process-view"]:visible');
  await expect(common.locator('[data-result-id]')).toHaveCount(ids.length,{timeout:45000});
  expect((await common.locator('[data-result-id]').evaluateAll(es=>es.map(e=>e.getAttribute('data-result-id')))).sort()).toEqual(ids);
  await expect(common).toContainText('Hermes AI request timed out.');
  await record({id:'S08',state:'pass',label:'Common view retains the actual failure and partial results',summary:'The source geometry and requirements interpretation remain available; no repair or preparation completion is claimed.',purpose:'Check exact common-view identities and the real model-timeout diagnostic.',action:'Inspect the common working view of the recorded failed run.',controls:['Create or choose interface'],expected:'Two exact first-run results and the recorded model timeout.',actual:'Common results match the authoritative failed-run contract.',...await capture('S08','Common recorded failure')});

  const sourceOutput=snapshot.outputs.find(o=>o.port_id==='source_mesh');expect(sourceOutput).toBeTruthy();
  await common.locator('[data-result-id="'+sourceOutput.result_id+'"]').getByRole('button',{name:'Open representation',exact:true}).click();
  const commonGeometry=common.getByRole('img',{name:/Rotatable 3D/});
  await expect(commonGeometry.locator('canvas')).toBeVisible({timeout:45000});
  await commonGeometry.scrollIntoViewIfNeeded();
  await record({id:'S08G',state:'pass',label:'Common view reads the retained source geometry',summary:'The actual source STL is inspectable despite the later repair-model failure.',purpose:'Verify the exact common result uses the shared bounded geometry reader.',action:'Click Open representation on the source_mesh.stl result.',controls:['Open representation','Close representation'],expected:'A visible 3D canvas for the actual first-run source.',actual:'Actual partial source geometry is visible in the common view.',...await capture('S08G','Common actual geometry')});
  await common.getByRole('button',{name:'Close representation',exact:true}).click();
  await page.getByRole('button',{name:'Create or choose interface',exact:true}).click();
  const saved=JSON.parse(readFileSync(path.join(privateRoot,'printed-ui-update-001-saved-revision.json'),'utf8'));
  await page.getByRole('combobox',{name:'Saved interface',exact:true}).selectOption(saved.manifest.ui_id);
  const presented=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/present'));
  await page.getByRole('button',{name:'Open saved interface',exact:true}).click();
  const response=await presented;expect(response.status()).toBe(200);
  writeFileSync(path.join(privateRoot,'printed-ui-failed-parity-002-presentation.json'),JSON.stringify(await response.json(),null,2));
  const frame=page.locator('[data-testid="surface-panel-host"]:visible').frameLocator('iframe');
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:45000});
  await expect(frame.locator('[data-result-id]')).toHaveCount(ids.length,{timeout:45000});
  expect((await frame.locator('[data-result-id]').evaluateAll(es=>es.map(e=>e.getAttribute('data-result-id')))).sort()).toEqual(ids);
  await expect(frame.locator('#wright-process-ui')).toContainText('Hermes AI request timed out.');
  expect(new URL(page.url()).searchParams.get('processUIRevision')).toBe(saved.manifest.revision_id);
  expect(new URL(page.url()).searchParams.get('processUIKind')).toBe('working');
  const savedUrl=cleanUrl();
  await record({id:'S09',state:'pass',label:'Saved working interface agrees with the common view',summary:'The same built interface retains exact partial-result identities and the real failure.',purpose:'Verify common/tailored evidence and failure parity without authoring again.',action:'Select Focus-wheel digital preparation and click Open saved interface.',controls:['Saved interface','Open saved interface'],expected:'Exact same two result identities and model-timeout diagnostic.',actual:'Saved working interface agrees with the common view.',...await capture('S09','Saved recorded failure')});
  await page.reload();
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:45000});
  expect((await frame.locator('[data-result-id]').evaluateAll(es=>es.map(e=>e.getAttribute('data-result-id')))).sort()).toEqual(ids);
  await expect(frame.locator('#wright-process-ui')).toContainText('Hermes AI request timed out.');
  const result=snapshot.outputs.find(o=>o.port_id==='source_mesh');expect(result).toBeTruthy();
  const card=frame.locator('[data-result-id="'+result.result_id+'"]');
  await card.getByRole('button',{name:'Open representation',exact:true}).click();
  const geometry=frame.getByRole('img',{name:/Rotatable 3D/});
  await expect(geometry).toBeVisible({timeout:45000});
  await expect(geometry.locator('canvas')).toBeVisible();
  await geometry.scrollIntoViewIfNeeded();
  await record({id:'S10',state:'pass',label:'Actual source geometry remains inspectable',summary:'The exact constructed STL opens in the shared 3D viewer; it is not a repaired or accepted manufacturing package.',purpose:'Inspect real retained geometry through the scoped result reader.',action:'Reload the saved view and click Open representation on source_mesh.stl.',controls:['Open representation'],expected:'The exact first-run source STL and a visible 3D canvas.',actual:'The shared reader renders the exact source geometry within the tailored view.',...await capture('S10','Actual partial source geometry')});
  await page.goto(savedUrl);await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:45000});
  await card.getByRole('button',{name:'Open producing step',exact:true}).click();
  const editor=page.locator('[data-workflow-file="'+prepared.path+'"]:visible');
  await expect(editor).toBeVisible({timeout:45000});
  expect(new URL(page.url()).searchParams.get('workflowFocusNode')).toBe(result.step_id);
  await record({id:'S11',state:'pass',label:'Exact producer opens in the accepted editor',summary:'The partial result leads to its actual source-construction block.',purpose:'Retain the complementary working view and detailed engineering inspection.',action:'Return to the saved view and click Open producing step on source_mesh.stl.',controls:['Open producing step'],expected:'Accepted process and exact source-mesh producer selected.',actual:'The original producing block opens in the preserved editor.',...await capture('S11','Exact source producer')});
  expect(authoringOrExecutionPosts).toEqual([]);
  expect(diagnostics).toEqual({console:[],pageErrors:[],failedResponses:[]});
  writeFileSync(path.join(privateRoot,'printed-ui-failed-parity-002-retention.json'),JSON.stringify({run_id:receipt.run_id,ui_id:saved.manifest.ui_id,revision_id:saved.manifest.revision_id,common_result_ids:ids,tailored_result_ids:ids,diagnostic_codes:snapshot.diagnostics.map(d=>d.code),authoringOrExecutionPosts,diagnostics},null,2));
  status.overall='pass';
} catch(error){
  status.overall='blocked';
  await record({id:'STOP',state:'blocked',label:'Entry stopped',summary:'The normal workspace entry did not meet the expected state.',purpose:'Retain the first stopping point.',action:'Stop at the unexpected entry state.',controls:['Workflows'],expected:'Workspace and established editor available.',actual:error.message,...await capture('STOP','Stopping point')});
  writeFileSync(path.join(privateRoot,'printed-ui-failed-parity-002-dom.json'),JSON.stringify({url:cleanUrl(),body:await page.locator('body').innerText(),buttons:await page.locator('button').evaluateAll(es=>es.map(e=>({text:e.textContent,label:e.getAttribute('aria-label'),id:e.getAttribute('data-testid')})))},null,2));
} finally {
  publish();
  writeFileSync(path.join(root,'browser-diagnostics.json'),JSON.stringify(diagnostics,null,2));
  await context.tracing.stop({path:path.join(privateRoot,'printed-ui-failed-parity-002-trace.zip')});
  await browser.close();
  console.log(JSON.stringify({status:status.overall,report:path.join(root,'report.html'),steps:status.steps.map(s=>({id:s.id,state:s.state,actual:s.actual}))}));
}


