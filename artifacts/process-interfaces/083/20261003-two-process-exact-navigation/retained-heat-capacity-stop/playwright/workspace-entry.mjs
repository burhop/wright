import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const privateRoot = path.resolve('.local-run/process-interfaces-083/t047-heat-latest-results-011');
const proof = JSON.parse(readFileSync(path.join(privateRoot, 'browser-context.json'), 'utf8'));
const prepared = JSON.parse(readFileSync(path.join(privateRoot, 'prepared-run.json'), 'utf8'));
const root = path.resolve('artifacts/ui-walkthrough/process-interfaces-083-heat/20261003T031359Z-heat-latest-results-011');
if (existsSync(root)) throw new Error('Preserve the previous walkthrough; select a fresh root');
for (const dir of ['playwright','screenshots/raw','screenshots/annotated','trace']) mkdirSync(path.join(root, dir), {recursive:true});
const status = {title:'Latest saved heat interface: exact outputs, field evidence and source navigation', summary:'A focused continuation of the verified normal-workspace journey using actual completed CAD/solver outputs. No process decision or physical action.', overall:'pending', updated:new Date().toISOString(), manualSteps:[
  {label:'Open saved comparison',instruction:'Open the latest saved heat working-interface link for the completed analysis run.'},
  {label:'Inspect field',instruction:'On revision_60_fine, click Open representation. Expand View numerical samples and select x_m, y_m and temperature_c.'},
  {label:'Inspect assessment',instruction:'Reopen the saved interface. On revision_60_fine, click Open assessment.'},
  {label:'Inspect producer',instruction:'Reopen the saved interface. On revision_60_fine, click Open producing step. Inspect the selected computation block.'},
  {label:'Reload',instruction:'Reopen the saved comparison and reload. Leave all reviews unchanged.'},
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
const diagnostics={console:[],pageErrors:[],failedResponses:[],mutations:[],representationHeaders:[],contexts:[]};
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


const expected=JSON.parse(readFileSync(path.join(privateRoot,'current-interaction.json'),'utf8'));
const saved=JSON.parse(readFileSync(path.join(privateRoot,'saved-view.json'),'utf8'));
const expectedIds=expected.outputs.map(output=>output.result_id).sort();
const output=expected.outputs.find(item=>item.result_id.endsWith(':revision_60_fine'));
expect(output).toBeTruthy();
const resultId=output.result_id;
const assessmentId='assessment-c1cc56ecf12341938996ff0fa1c07b4e';
const frame=page.locator('[data-testid="surface-panel-host"]:visible').frameLocator('iframe');
const card=frame.locator('article[data-result-id="'+resultId+'"]');
async function openSaved(){
  await page.goto(saved.url);
  expect(new URL(page.url()).searchParams.get('processUIKind')).toBe('working');
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:120000});
  await expect(frame.locator('article[data-result-id]')).toHaveCount(18,{timeout:120000});
  expect(await frame.locator('article[data-result-id]').evaluateAll(items=>items.map(item=>item.dataset.resultId).sort())).toEqual(expectedIds);
  await expect.poll(()=>diagnostics.contexts.at(-1)?.read_only,{timeout:30000}).toBe(false);
}
try {
  await openSaved();
  await expect(frame.getByRole('heading',{name:'Run inputs',exact:true})).toBeVisible();
  await expect(card.getByRole('button',{name:'Open assessment',exact:true})).toBeEnabled();
  await record({id:'S01',state:'pass',label:'Latest comparison matches completed engineering outputs',summary:'The saved shared-controls interface reads all eighteen actual CAD/solver results.',purpose:'Prove current saved UI against completed outputs rather than only a waiting basis result.',action:'Open the latest saved heat comparison for the completed run.',controls:['Run inputs','Open representation','Open assessment'],expected:'Exact eighteen-result parity and original held assessment in a working context.',actual:'All eighteen identities match; exact working context and shared controls are present.',...await capture('S01','Latest heat comparison')});
  await card.getByRole('button',{name:'Open representation',exact:true}).click();
  const common=page.getByTestId('common-process-view').filter({visible:true});
  await expect(common).toBeVisible({timeout:45000});
  await expect(common.locator('article[data-result-id]')).toHaveCount(18,{timeout:45000});
  expect(await common.locator('article[data-result-id]').evaluateAll(items=>items.map(item=>item.dataset.resultId).sort())).toEqual(expectedIds);
  await expect(common.getByRole('columnheader',{name:'temperature_c',exact:true})).toBeVisible({timeout:45000});
  await common.getByText('View numerical samples',{exact:true}).click();
  await common.getByLabel('Horizontal column').selectOption('x_m');
  await common.getByLabel('Vertical column').selectOption('y_m');
  await common.getByLabel('Value column').selectOption('temperature_c');
  const field=common.getByRole('img',{name:/Recorded field samples;/});
  await expect(field).toBeVisible();await expect(field.locator('circle')).toHaveCount(765);
  await record({id:'S02',state:'pass',label:'Actual fine-field evidence and common parity',summary:'The latest interface opens all 765 supplied solver samples in the common evidence view.',purpose:'Prove shared exact navigation and actual numerical data.',action:'Open revision_60_fine, expand View numerical samples and select x_m, y_m, temperature_c.',controls:['Open representation','View numerical samples','Horizontal column','Vertical column','Value column'],expected:'Exact common result parity and all 765 real supplied samples.',actual:'Eighteen exact common results and all fine-grid samples rendered; no interpolation or engineering approval.',...await capture('S02','Actual fine-field samples')});
  await openSaved();
  await card.getByRole('button',{name:'Open assessment',exact:true}).click();
  await expect(common).toBeVisible({timeout:45000});
  const assessment=common.locator('pre').filter({hasText:assessmentId});
  await expect(assessment).toBeVisible({timeout:45000});
  await expect(assessment).toContainText('"pass": 25');await expect(assessment).toContainText('"blocked": 1');
  expect(await page.evaluate(()=>document.activeElement?.closest('[data-result-id]')?.getAttribute('data-result-id'))).toBe(resultId);
  await record({id:'S03',state:'pass',label:'Exact full heat assessment remains held',summary:'The interface opens the original assessment with twenty-five passes and one required-review hold.',purpose:'Retain engineering verification and exact result focus.',action:'Reopen the comparison and click Open assessment on revision_60_fine.',controls:['Open assessment','Representation'],expected:'Original held assessment and exact fine-result focus.',actual:'Twenty-five passes, one blocked review and exact fine-result focus retained.',...await capture('S03','Held heat assessment')});
  await openSaved();
  await card.getByRole('button',{name:'Open producing step',exact:true}).click();
  const editor=page.locator('[data-workflow-file="'+prepared.path+'"]:visible');
  await expect(editor).toBeVisible({timeout:45000});
  const blockId='block.'+output.step_id.replaceAll('_','-');
  await expect(editor.locator('.react-flow__node.selected[data-id="'+blockId+'"]')).toBeVisible({timeout:45000});
  await expect(editor.getByTestId('workflow-recovery-inspector')).toBeVisible();
  await expect(editor.getByTestId('workflow-navigation-error')).toHaveCount(0);
  await record({id:'S04',state:'pass',label:'Exact computation block selected',summary:'The comparison returns to its actual computation producer and inspector.',purpose:'Verify the shared navigation correction on a substantially different engineering process.',action:'Reopen the comparison and click Open producing step on revision_60_fine.',controls:['Open producing step','Inspector'],expected:'The exact accepted computation block selected.',actual:'Exact computation block and inspector selected; no stale-source warning.',...await capture('S04','Heat computation producer')});
  await openSaved();await page.reload();
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:120000});
  await expect(frame.locator('article[data-result-id]')).toHaveCount(18,{timeout:120000});
  expect(await frame.locator('article[data-result-id]').evaluateAll(items=>items.map(item=>item.dataset.resultId).sort())).toEqual(expectedIds);
  expect(diagnostics.contexts.at(-1)).toMatchObject({read_only:false,run_id:expected.context.run_id,ui_id:saved.manifest.ui_id,revision_id:saved.manifest.revision_id});
  await record({id:'S05',state:'pass',label:'Latest saved completed-output reload',summary:'Reload restores the same saved revision and all actual completed outputs.',purpose:'Verify saved reuse/reconciliation without generation or engineering replay.',action:'Reopen the saved comparison and reload.',controls:['Run inputs','Open assessment'],expected:'Same exact saved UI and eighteen engineering results.',actual:'Current saved working revision and all exact results restored; review remains held.',...await capture('S05','Latest heat reload')});
  expect(diagnostics.console).toEqual([]);expect(diagnostics.pageErrors).toEqual([]);expect(diagnostics.failedResponses).toEqual([]);
  expect(diagnostics.mutations.some(row=>['/start','/respond','/actions/','/generate','/save'].some(part=>row.path.includes(part)))).toBe(false);
  writeFileSync(path.join(privateRoot,'parity.json'),JSON.stringify({run_id:expected.context.run_id,ui_id:saved.manifest.ui_id,revision_id:saved.manifest.revision_id,result_ids:expectedIds,assessment_id:assessmentId,working_context_read_only:false,field_samples:765,common_and_tailored_parity:true,reload:true,navigation:true,url:saved.url},null,2));
  status.overall='pass';
} catch(error){
  status.overall='blocked';
  await record({id:'STOP',state:'blocked',label:'Latest heat interface check stopped',summary:'The current saved comparison did not meet the exact evidence expectation.',purpose:'Retain the first failure.',action:'Stop at the unexpected comparison state.',controls:['Open representation','Open assessment','Open producing step'],expected:'Exact completed-output parity and useful navigation.',actual:error.message,...await capture('STOP','Heat stopping point')});
  writeFileSync(path.join(privateRoot,'stop-dom.json'),JSON.stringify({url:cleanUrl(),body:await page.locator('body').innerText()},null,2));
} finally {
  publish();writeFileSync(path.join(root,'browser-diagnostics.json'),JSON.stringify(diagnostics,null,2));
  await context.tracing.stop({path:path.join(privateRoot,'heat-latest-results-011-trace.zip')});await browser.close();
  console.log(JSON.stringify({status:status.overall,report:path.join(root,'report.html'),steps:status.steps.map(item=>({id:item.id,state:item.state,actual:item.actual}))}));
}
