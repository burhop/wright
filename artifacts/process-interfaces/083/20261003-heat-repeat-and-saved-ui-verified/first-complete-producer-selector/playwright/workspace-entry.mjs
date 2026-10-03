import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const privateRoot = path.resolve('.local-run/process-interfaces-083/t047-heat-repeat-013');
const proof = JSON.parse(readFileSync(path.join(privateRoot, 'browser-context.json'), 'utf8'));
const prepared = JSON.parse(readFileSync(path.join(privateRoot, 'prepared-run.json'), 'utf8'));
const root = path.resolve('artifacts/ui-walkthrough/process-interfaces-083-heat/20261003T060201Z-heat-repeat-complete-002');
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
  await record({id:'S01',state:'pass',label:'Workspace offers Workflows',summary:'Entered the normal authenticated workspace.',purpose:'Verify the normal workspace route with real API owners.',action:'Open Heat-spreader comparison proof workspace.',controls:['Workflows'],expected:'The workspace loads and offers Workflows.',actual:'Normal workspace and Workflows control visible.',...await capture('S01','Workspace')});
  await page.getByRole('button',{name:'Workflows',exact:true}).click();
  await expect(page.getByTestId('workflow-file-menu')).toBeVisible({timeout:45000});
  await record({id:'S02',state:'pass',label:'Workflows opens the editor',summary:'The established workflow editor is available inside the workspace.',purpose:'Verify actual workspace entry without mocking.',action:'Click Workflows.',controls:['Workflows','Use saved process'],expected:'Editor and working-view action appear.',actual:'Editor and working-view action visible.',...await capture('S02','Editor')});
  await page.getByTestId('workflow-file-menu').click();
  await record({id:'S03',state:'pass',label:'Workflow file controls',summary:'The workspace offers named saved workflows.',purpose:'Use the existing saved file chooser.',action:'Click Workflow files.',controls:['Workflow files','Open workflow'],expected:'Open workflow is offered.',actual:'Existing file actions are visible.',...await capture('S03','Workflow files')});
  await page.getByTestId('workflow-file-open').click();
  await expect(page.getByTestId('workflow-file-choice-'+prepared.path)).toBeVisible({timeout:45000});
  await record({id:'S04',state:'pass',label:'Choose the heat workflow',summary:'The exact accepted heat workflow appears in the saved files.',purpose:'Choose the engineering process by its saved file.',action:'Click Open workflow.',controls:['Open workflow',prepared.path],expected:'The accepted heat workflow is listed.',actual:'Exact accepted workflow choice visible.',...await capture('S04','Workflow chooser')});
  await page.getByTestId('workflow-file-choice-'+prepared.path).click();
  const heatEditor = page.locator('[data-workflow-file="'+prepared.path+'"]:visible');
  await expect(heatEditor).toBeVisible({timeout:45000});
  await expect(heatEditor.getByTestId('workflow-file-menu')).toBeVisible({timeout:45000});
  await expect(heatEditor.getByTestId('workflow-working-view-open')).toBeEnabled();
  await record({id:'S05',state:'pass',label:'Heat workflow diagram',summary:'The original heat assignment opens with its connected review, CAD and analysis stages.',purpose:'Keep authoring and working views on the accepted source.',action:'Choose the accepted heat workflow file.',controls:[prepared.path,'Use saved process'],expected:'Accepted heat diagram and working view action available.',actual:'Exact saved heat source is open.',...await capture('S05','Heat diagram')});
  await heatEditor.getByTestId('workflow-working-view-open').click();
  await expect(page.getByTestId('common-process-view')).toBeVisible({timeout:45000});
  await record({id:'S06',state:'pass',label:'Shared working view',summary:'The process working interface opens in another Wright workspace tab.',purpose:'Verify shared inputs and readiness without creating another executor.',action:'Click Use saved process.',controls:['Use saved process'],expected:'Common working view in a workspace tab.',actual:'Common working view visible.',...await capture('S06','Common view')});
  const receipt = JSON.parse(readFileSync(path.join(privateRoot,'third-start-receipt.json'),'utf8')).body;
  const attached = new URL(page.url()); attached.searchParams.set('processRun',receipt.run_id);
  await page.goto(attached.href);
  await expect(page.getByTestId('common-process-view')).toBeVisible({timeout:45000});

  await record({id:'S07',state:'pass',label:'Attach the actual heat run',summary:'The working view reads the same isolated backend run.',purpose:'Use actual process state for interface composition.',action:'Reopen the recorded heat run link.',controls:['Create or choose interface'],expected:'The common working view attaches without starting another run.',actual:'Existing heat run attached.',...await capture('S07','Attached heat run')});

  const snapshot=JSON.parse(readFileSync(path.join(privateRoot,'third-current-interaction.json'),'utf8'));
  expect(snapshot.context.run_id).toBe(receipt.run_id);
  expect(snapshot.state).toBe('failed');
  expect(snapshot.diagnostics.map(d=>d.code)).toEqual(['PROCESS_VALIDATION_NEEDS_INPUT']);
  expect(snapshot.outputs).toHaveLength(18);
  const ids=snapshot.outputs.map(o=>o.result_id).sort();
  const common=page.locator('[data-testid="common-process-view"]:visible');
  await expect(common.locator('[data-result-id]')).toHaveCount(ids.length,{timeout:45000});
  expect((await common.locator('[data-result-id]').evaluateAll(es=>es.map(e=>e.getAttribute('data-result-id')))).sort()).toEqual(ids);
  await record({id:'S08',state:'pass',label:'Common view shows the exact completed digital chain',summary:'The recorded CAD and solver results are visible with the final human-review hold.',purpose:'Check common-view parity against the authoritative third-run contract.',action:'Inspect all recorded common-view result cards; leave reviews untouched.',controls:['Create or choose interface'],expected:'All eighteen exact third-run results, with no substituted earlier evidence.',actual:'All result identities match the third-run API contract.',...await capture('S08','Common result identities')});

  const commonFine=snapshot.outputs.find(o=>o.port_id==='revision_60_fine');
  await common.locator('[data-result-id="'+commonFine.result_id+'"]').getByRole('button',{name:'Open representation',exact:true}).click();
  await expect(common.getByRole('heading',{name:'Representation',exact:true})).toBeVisible({timeout:45000});
  await expect(common.getByRole('columnheader',{name:'temperature_c',exact:true})).toBeVisible();
  await common.getByText('View numerical samples',{exact:true}).click();
  for(const [label,value] of [['Horizontal column','x_m'],['Vertical column','y_m'],['Value column','temperature_c']])await common.getByLabel(label).selectOption(value);
  const commonRows=readFileSync(path.join(proof.workspace_root,commonFine.representations[0].artifact_ref),'utf8').trim().split(/\r?\n/).length-1;
  await expect(common.getByRole('img',{name:/Recorded field samples;/}).locator('circle')).toHaveCount(commonRows);
  await record({id:'S08B',state:'pass',label:'Common view opens the same actual solver samples',summary:'The common reader renders every fine-field sample before switching to the tailored interface.',purpose:'Compare common and tailored readers against the same exact recorded bytes.',action:'Open revision_60_fine in the common view and choose the recorded axes.',controls:['Open representation','View numerical samples','Horizontal column','Vertical column','Value column'],expected:commonRows+' samples from the exact fine-field CSV.',actual:'Common viewer renders all '+commonRows+' recorded samples.',...await capture('S08B','Common solver samples')});
  await page.getByRole('button',{name:'Create or choose interface',exact:true}).click();
  const saved=JSON.parse(readFileSync(path.join(privateRoot,'heat-ui-focused-update-013-saved-revision.json'),'utf8'));
  await page.getByRole('combobox',{name:'Saved interface',exact:true}).selectOption(saved.manifest.ui_id);
  const presentedResponse=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/present'));
  await page.getByRole('button',{name:'Open saved interface',exact:true}).click();
  const response=await presentedResponse;expect(response.status()).toBe(200);
  writeFileSync(path.join(privateRoot,'heat-ui-complete-013-002-presentation.json'),JSON.stringify(await response.json(),null,2));
  const frame=page.locator('[data-testid="surface-panel-host"]:visible').frameLocator('iframe');
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:45000});
  await expect(frame.locator('[data-result-id]')).toHaveCount(ids.length,{timeout:45000});
  expect((await frame.locator('[data-result-id]').evaluateAll(es=>es.map(e=>e.getAttribute('data-result-id')))).sort()).toEqual(ids);
  for(const heading of ['Baseline 40 mm','Revision 60 mm','Shared evidence and checks'])await expect(frame.getByRole('heading',{name:heading,exact:true})).toBeVisible();
  expect(new URL(page.url()).searchParams.get('processUIRevision')).toBe(saved.manifest.revision_id);
  expect(new URL(page.url()).searchParams.get('processUIKind')).toBe('working');
  const savedUrl=cleanUrl();
  await record({id:'S09',state:'pass',label:'Saved updated comparison shows identical evidence',summary:'The previously built comparison groups the actual third-run geometry, fields and checks.',purpose:'Prove unchanged saved-interface reuse with common/tailored result identity parity.',action:'Choose the saved Heat comparison and click Open saved interface.',controls:['Saved interface','Open saved interface'],expected:'The saved updated revision displays exactly the same eighteen third-run result identities.',actual:'Exact common/tailored identity parity and all three comparison groups are visible.',...await capture('S09','Saved third-run comparison')});
  await page.reload();
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:45000});
  await expect(frame.locator('[data-result-id]')).toHaveCount(ids.length,{timeout:45000});
  expect((await frame.locator('[data-result-id]').evaluateAll(es=>es.map(e=>e.getAttribute('data-result-id')))).sort()).toEqual(ids);
  const result=snapshot.outputs.find(o=>o.port_id==='revision_60_fine');expect(result).toBeTruthy();
  const resultId=result.result_id;
  const card=frame.locator('[data-result-id="'+resultId+'"]');
  await card.getByRole('button',{name:'Open representation',exact:true}).click();
  const evidence=page.locator('[data-testid="common-process-view"]:visible');

  const inline=frame.locator('.wp-result-representation');
  await expect(inline.getByRole('table')).toBeVisible({timeout:45000});
  await expect(inline.getByRole('columnheader',{name:'temperature_c',exact:true})).toBeVisible();
  const csv=readFileSync(path.join(proof.workspace_root,result.representations[0].artifact_ref),'utf8');
  const rows=csv.trim().split(/\r?\n/).length-1;
  expect(rows).toBeGreaterThan(0);
  await inline.getByText('View numerical samples',{exact:true}).click();
  await inline.getByLabel('Horizontal column').selectOption('x_m');
  await inline.getByLabel('Vertical column').selectOption('y_m');
  await inline.getByLabel('Value column').selectOption('temperature_c');
  const field=inline.getByRole('img',{name:/Recorded field samples;/});
  await expect(field).toBeVisible();await expect(field.locator('circle')).toHaveCount(rows);
  await inline.scrollIntoViewIfNeeded();
  await record({id:'S10',state:'pass',label:'Actual solver field opens inside the saved interface',summary:'Wright’s shared viewer shows the exact fine-field table and all recorded samples.',purpose:'Verify exact third-run rendering in the generated interface using the shared reader.',action:'Click Open representation on revision_60_fine; expand View numerical samples and select x_m, y_m and temperature_c.',controls:['Open representation','View numerical samples','Horizontal column','Vertical column','Value column'],expected:rows+' samples from the recorded third-run CSV.',actual:rows+' actual samples rendered in the saved interface.',...await capture('S10','Inline solver samples')});
  await page.goto(savedUrl);await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:45000});
  await card.getByRole('button',{name:'Open assessment',exact:true}).click();
  await expect(evidence.getByRole('heading',{name:'Representation',exact:true})).toBeVisible({timeout:45000});
  await expect(evidence.locator('pre').filter({hasText:'"pass": 25'})).toBeVisible();
  await expect(evidence.locator('pre').filter({hasText:'"blocked": 1'})).toBeVisible();
  expect(await page.evaluate(()=>document.activeElement?.closest('[data-result-id]')?.getAttribute('data-result-id'))).toBe(resultId);
  await record({id:'S11',state:'pass',label:'Exact held assessment opens',summary:'The comparison preserves all checks and the mandatory human-review hold.',purpose:'Verify assessment identity and honest engineering status.',action:'Reopen the saved comparison and click Open assessment on revision_60_fine.',controls:['Open assessment'],expected:'25 passed checks, one blocked review, exact requested result focus.',actual:'Full held assessment visible with the exact fine-field result focus.',...await capture('S11','Held assessment')});
  await page.goto(savedUrl);await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:45000});
  await card.getByRole('button',{name:'Open producing step',exact:true}).click();
  const editor=page.locator('[data-workflow-file="'+prepared.path+'"]:visible');
  await expect(editor).toBeVisible({timeout:45000});await expect(editor.getByTestId('workflow-file-menu')).toBeVisible();
  await expect(editor.locator('.react-flow__node.selected[data-id="'+result.step_id+'"]')).toBeVisible();
  await expect(editor.getByTestId('workflow-recovery-block-name')).toBeVisible();
  await record({id:'S12',state:'pass',label:'Exact producing step opens in the refined editor',summary:'Result navigation returns to the actual solver-output block in the accepted process.',purpose:'Preserve complementary engineering inspection and working views.',action:'Reopen the saved comparison and click Open producing step.',controls:['Open producing step','Workflow files'],expected:'The accepted source and exact compute_fields producer open.',actual:'Accepted process editor and exact producer focus restored.',...await capture('S12','Exact producer')});
  expect(authoringOrExecutionPosts).toEqual([]);
  expect(diagnostics).toEqual({console:[],pageErrors:[],failedResponses:[]});
  writeFileSync(path.join(privateRoot,'heat-ui-complete-013-002-retention.json'),JSON.stringify({saved_url:savedUrl,run_id:receipt.run_id,ui_id:saved.manifest.ui_id,revision_id:saved.manifest.revision_id,common_result_ids:ids,tailored_result_ids:ids,field_sample_count:rows,authoringOrExecutionPosts,diagnostics},null,2));
  status.overall='pass';
} catch(error){
  status.overall='blocked';
  await record({id:'STOP',state:'blocked',label:'Entry stopped',summary:'The normal workspace entry did not meet the expected state.',purpose:'Retain the first stopping point.',action:'Stop at the unexpected entry state.',controls:['Workflows'],expected:'Workspace and established editor available.',actual:error.message,...await capture('STOP','Stopping point')});
  writeFileSync(path.join(privateRoot,'heat-ui-complete-013-002-dom.json'),JSON.stringify({url:cleanUrl(),body:await page.locator('body').innerText(),buttons:await page.locator('button').evaluateAll(es=>es.map(e=>({text:e.textContent,label:e.getAttribute('aria-label'),id:e.getAttribute('data-testid')})))},null,2));
} finally {
  publish();
  writeFileSync(path.join(root,'browser-diagnostics.json'),JSON.stringify(diagnostics,null,2));
  await context.tracing.stop({path:path.join(privateRoot,'heat-ui-complete-013-002-trace.zip')});
  await browser.close();
  console.log(JSON.stringify({status:status.overall,report:path.join(root,'report.html'),steps:status.steps.map(s=>({id:s.id,state:s.state,actual:s.actual}))}));
}


