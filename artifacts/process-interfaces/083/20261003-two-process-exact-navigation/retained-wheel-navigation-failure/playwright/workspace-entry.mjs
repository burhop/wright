import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const privateRoot = path.resolve('.local-run/process-interfaces-083/t047-printed-retained-consumer-003');
const proof = JSON.parse(readFileSync(path.join(privateRoot, 'browser-context.json'), 'utf8'));
const prepared = JSON.parse(readFileSync(path.join(privateRoot, 'prepared-run.json'), 'utf8'));
const root = path.resolve('artifacts/ui-walkthrough/process-interfaces-083-wheel/20261003T030735Z-wheel-saved-navigation-012');
if (existsSync(root)) throw new Error('Preserve the previous walkthrough; select a fresh root');
for (const dir of ['playwright','screenshots/raw','screenshots/annotated','trace']) mkdirSync(path.join(root, dir), {recursive:true});
const status = {title:'Exact assessment and producing-step navigation from the saved wheel view', summary:'A focused continuation of the verified normal-workspace journey on the same actual isolated run. No engineering decisions or physical actions.', overall:'pending', updated:new Date().toISOString(), manualSteps:[
  {label:'Open saved view',instruction:'Open the saved wheel working-interface link.'},
  {label:'Inspect assessment',instruction:'On repaired_mesh.stl, click Open assessment. Inspect the held assessment in the common view.'},
  {label:'Inspect producer',instruction:'Reopen the saved interface link. On repaired_mesh.stl, click Open producing step. Inspect the selected repair block.'},
], steps:[]};
const escape = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function publish() {
  status.updated = new Date().toISOString();
  writeFileSync(path.join(root,'status.json'),JSON.stringify(status,null,2));
  writeFileSync(path.join(root,'report.html'),`<!doctype html><html><head><meta charset="utf-8"><title>${escape(status.title)}</title><style>body{font:16px system-ui;max-width:1100px;margin:24px auto;background:#101922;color:#e8f4f7}section{padding:18px;border:1px solid #647486;margin:16px 0}.pass{border-color:#64bda4}.blocked{border-color:#ee7373}img{max-width:100%}a{color:#7fe0cb}</style></head><body><h1>${escape(status.title)}</h1><p>${escape(status.summary)}</p><p>Status: ${escape(status.overall)}</p><h2>Manual steps</h2><ol>${status.manualSteps.map(s=>`<li>${escape(s.instruction)}</li>`).join('')}</ol>${status.steps.map(s=>`<section class="${s.state}"><h2>${escape(s.label)} Â· ${escape(s.state)}</h2><p>${escape(s.summary)}</p><p>Expected: ${escape(s.expected)}</p><p>Actual: ${escape(s.actual)}</p>${['raw','annotated'].filter(k=>s[k]).map(k=>`<p>${k}<a class="image-button" href="${escape(s[k])}" onclick="event.preventDefault();document.getElementById('full-image').src=this.href;document.getElementById('image-dialog').showModal()"><img src="${escape(s[k])}" alt="${escape(s.label)} ${k}"></a></p>`).join('')}</section>`).join('')}<dialog id="image-dialog"><button onclick="document.getElementById('image-dialog').close()">Close</button><img id="full-image" style="max-width:none" alt="Full-size walkthrough evidence"></dialog></body></html>`);
}
writeFileSync(path.join(root,'progress.md'),'# Wheel exact saved-navigation continuation\n\nPrepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.\n');
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
const saved=JSON.parse(readFileSync(path.resolve('.local-run/process-interfaces-083/t047-wheel-ui-update-006/parity.json'),'utf8'));
const output=expected.outputs.find(item=>item.representations.some(ref=>ref.artifact_ref.endsWith('/repaired_mesh.stl')));
expect(output).toBeTruthy();
const resultId=output.result_id;
const assessmentId='assessment-46f892fa42ae4a21950679d986815e55';
const frame=page.locator('[data-testid="surface-panel-host"]:visible').frameLocator('iframe');
const card=frame.locator('article[data-result-id="'+resultId+'"]');
try {
  await page.goto(saved.url);
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:120000});
  await expect(frame.locator('article[data-result-id]')).toHaveCount(19,{timeout:120000});
  await expect.poll(()=>diagnostics.contexts.at(-1)?.read_only,{timeout:30000}).toBe(false);
  await expect(card.getByRole('button',{name:'Open assessment',exact:true})).toBeEnabled();
  await expect(card.getByRole('button',{name:'Open producing step',exact:true})).toBeEnabled();
  await record({id:'S01',state:'pass',label:'Saved exact wheel working view',summary:'The saved interface reads the original results and held assessment.',purpose:'Use the verified saved working URL, not the preview.',action:'Open the saved wheel working-interface link.',controls:['Open assessment','Open producing step'],expected:'Nineteen results and exact repaired-mesh navigation in a working context.',actual:'Actual working context and both scoped navigation controls available.',...await capture('S01','Saved exact wheel view')});
  await card.getByRole('button',{name:'Open assessment',exact:true}).click();
  const common=page.getByTestId('common-process-view').filter({visible:true});
  await expect(common).toBeVisible({timeout:45000});
  await expect(common.getByRole('heading',{name:'Representation',exact:true})).toBeVisible({timeout:45000});
  const assessment=common.locator('pre').filter({hasText:assessmentId});
  await expect(assessment).toBeVisible({timeout:45000});
  await expect(assessment).toContainText('"pass": 17');
  await expect(assessment).toContainText('"blocked": 1');
  const focused=await page.evaluate(()=>document.activeElement?.closest('[data-result-id]')?.getAttribute('data-result-id'));
  expect(focused).toBe(resultId);
  await record({id:'S02',state:'pass',label:'Exact held assessment and result focus',summary:'The saved interface opens the original eighteen-check assessment in Wright’s common evidence view.',purpose:'Verify exact output-to-assessment identity without answering a review.',action:'Click Open assessment on repaired_mesh.stl.',controls:['Open assessment','Representation'],expected:'Seventeen passes, one blocked human review, exact repaired-mesh result focus.',actual:'Full held assessment opened with exact result focus; no review response submitted.',...await capture('S02','Held wheel assessment')});
  await page.goto(saved.url);
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:120000});
  await expect(card).toBeVisible({timeout:120000});
  await card.getByRole('button',{name:'Open producing step',exact:true}).click();
  const editor=page.locator('[data-workflow-file="'+prepared.path+'"]:visible');
  await expect(editor).toBeVisible({timeout:45000});
  await expect(editor.getByTestId('workflow-file-menu')).toBeVisible();
  const blockId='block.'+output.step_id.replaceAll('_','-');
  await expect(editor.locator('.react-flow__node.selected[data-id="'+blockId+'"]')).toBeVisible({timeout:45000});
  await expect(editor.getByTestId('workflow-recovery-inspector')).toBeVisible();
  await expect(editor.getByTestId('workflow-navigation-error')).toHaveCount(0);
  await record({id:'S03',state:'pass',label:'Exact producing repair block selected',summary:'The working interface returns to the accepted repair step and its inspector.',purpose:'Verify selected producer, not just that some diagram opened.',action:'Reopen the saved interface and click Open producing step on repaired_mesh.stl.',controls:['Open producing step','Inspector','Workflow files'],expected:'Exact accepted repair block selected with inspector and no stale-source warning.',actual:'Exact repair block selected in the established editor; accepted source and run remain unchanged.',...await capture('S03','Exact repair producer')});
  expect(diagnostics.console).toEqual([]);expect(diagnostics.pageErrors).toEqual([]);expect(diagnostics.failedResponses).toEqual([]);
  expect(diagnostics.mutations.some(row=>['/start','/respond','/actions/','/generate','/save'].some(part=>row.path.includes(part)))).toBe(false);
  status.overall='pass';
} catch(error){
  status.overall='blocked';
  await record({id:'STOP',state:'blocked',label:'Exact navigation stopped',summary:'The assessment or producing block did not meet its recorded subject.',purpose:'Preserve the first failure.',action:'Stop at the unexpected navigation state.',controls:['Open assessment','Open producing step'],expected:'Exact held assessment and selected producer.',actual:error.message,...await capture('STOP','Navigation stopping point')});
  writeFileSync(path.join(privateRoot,'wheel-saved-navigation-012-stop-dom.json'),JSON.stringify({url:cleanUrl(),body:await page.locator('body').innerText()},null,2));
} finally {
  publish();writeFileSync(path.join(root,'browser-diagnostics.json'),JSON.stringify(diagnostics,null,2));
  await context.tracing.stop({path:path.join(privateRoot,'wheel-saved-navigation-012-trace.zip')});
  await browser.close();
  console.log(JSON.stringify({status:status.overall,report:path.join(root,'report.html'),steps:status.steps.map(item=>({id:item.id,state:item.state,actual:item.actual}))}));
}
