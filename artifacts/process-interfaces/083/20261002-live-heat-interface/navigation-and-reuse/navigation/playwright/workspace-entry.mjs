import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const privateRoot = path.resolve('.local-run/process-interfaces-083/t047-heat-live-005-rerun-002');
const proof = JSON.parse(readFileSync(path.join(privateRoot, 'browser-context.json'), 'utf8'));
const prepared = JSON.parse(readFileSync(path.join(privateRoot, 'prepared-run.json'), 'utf8'));
const root = path.resolve('artifacts/ui-walkthrough/process-interfaces-083-heat/20261002T050715Z-heat-saved-navigation-qualified');
if (existsSync(root)) throw new Error('Preserve the previous walkthrough; select a fresh root');
for (const dir of ['playwright','screenshots/raw','screenshots/annotated','trace']) mkdirSync(path.join(root, dir), {recursive:true});
const status = {title:'Exact evidence navigation from the saved heat comparison', summary:'Normal Wright workspace and actual isolated engineering run. No mocked routes or physical action.', overall:'pending', updated:new Date().toISOString(), manualSteps:[
  {label:'Open workspace', instruction:'Open the isolated Heat-spreader comparison proof workspace.'},
  {label:'Open workflows', instruction:'Click Workflows in the workspace activity bar.'},
  {label:'Choose process',instruction:'Click Workflow files, then Open workflow. Select the saved heat-spreader workflow.'},
  {label:'Use process',instruction:'Click Use saved process. Reopen the recorded run from its workspace link.'},
  {label:'Open saved comparison',instruction:'Open the saved heat comparison workspace link. On revision_60_fine click Open representation, Open assessment, then Open producing step, reopening the comparison between actions.'},
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
  const receipt = JSON.parse(readFileSync(path.join(privateRoot,'start-receipt.json'),'utf8')).body;
  const attached = new URL(page.url()); attached.searchParams.set('processRun',receipt.run_id);
  await page.goto(attached.href);
  await expect(page.getByTestId('common-process-view')).toBeVisible({timeout:45000});

  await record({id:'S07',state:'pass',label:'Attach the actual heat run',summary:'The working view reads the same isolated backend run.',purpose:'Use actual process state for interface composition.',action:'Reopen the recorded heat run link.',controls:['Create or choose interface'],expected:'The common working view attaches without starting another run.',actual:'Existing heat run attached.',...await capture('S07','Attached heat run')});
  const saved = JSON.parse(readFileSync(path.join(privateRoot,'heat-ui-focused-update-dom.json'),'utf8'));
  await page.goto(saved.url);
  const frame=page.locator('[data-testid="surface-panel-host"]:visible').frameLocator('iframe');
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:30000});
  await expect(frame.locator('[data-result-id]')).toHaveCount(18);
  const resultId='67abaa021ee44972a94e3c9cbaa3dbbe:compute_fields_live_default_model_002:revision_60_fine';
  const card=frame.locator('[data-result-id="'+resultId+'"]');
  await expect(card).toBeVisible();
  await record({id:'S08',state:'pass',label:'Reopen saved comparison',summary:'The saved revised comparison reads all actual heat results in a Wright workspace tab.',purpose:'Reuse compiled saved assets without regeneration.',action:'Open the recorded saved-interface workspace link.',controls:['Open representation','Open assessment','Open producing step'],expected:'Saved comparison connects and exposes all eighteen actual results.',actual:'Saved interface connected and eighteen actual results visible.',...await capture('S08','Saved comparison')});
  await card.getByRole('button',{name:'Open representation',exact:true}).click();
  const common=page.getByTestId('common-process-view');
  await expect(common).toBeVisible({timeout:30000});
  await expect(common.getByRole('heading',{name:'Representation',exact:true})).toBeVisible({timeout:30000});
  await expect(common.getByRole('table')).toBeVisible();
  await expect(common.getByRole('columnheader',{name:'temperature_c',exact:true})).toBeVisible();
  await record({id:'S09',state:'pass',label:'Exact fine-field evidence opens',summary:'The comparison opens the actual fine-grid temperature table through Wright’s common evidence view.',purpose:'Verify authorized evidence navigation from the generated interface.',action:'Click Open representation on revision_60_fine.',controls:['Open representation','View numerical samples'],expected:'Native common view shows the exact numerical CSV.',actual:'Actual numerical table and temperature column opened from the tailored interface.',...await capture('S09','Fine field evidence')});
  await common.getByText('View numerical samples',{exact:true}).click();
  await common.getByLabel('Horizontal column').selectOption('x_m');
  await common.getByLabel('Vertical column').selectOption('y_m');
  await common.getByLabel('Value column').selectOption('temperature_c');
  const field=common.getByRole('img',{name:/Recorded field samples;/});
  await expect(field).toBeVisible();
  await expect(field.locator('circle')).toHaveCount(765);
  await record({id:'S10',state:'pass',label:'All recorded field samples',summary:'The evidence viewer renders all 765 supplied samples using explicitly selected axes.',purpose:'Inspect actual solver outputs from the saved UI.',action:'Expand View numerical samples and select x_m, y_m, temperature_c.',controls:['View numerical samples','Horizontal column','Vertical column','Value column'],expected:'765 actual field samples.',actual:'All recorded samples rendered.',...await capture('S10','Field samples')});
  await page.goto(saved.url);
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:30000});
  await card.getByRole('button',{name:'Open assessment',exact:true}).click();
  await expect(common.getByRole('heading',{name:'Representation',exact:true})).toBeVisible({timeout:30000});
  await expect(common.locator('pre').filter({hasText:'"pass": 25'})).toBeVisible({timeout:30000});
  const focused=await page.evaluate(()=>document.activeElement?.closest('[data-result-id]')?.getAttribute('data-result-id'));
  expect(focused).toBe(resultId);
  await record({id:'S11',state:'pass',label:'Exact held assessment opens',summary:'The saved comparison opens its full recorded assessment and retains exact result focus.',purpose:'Preserve engineering verification and held human review.',action:'Reopen the saved comparison and click Open assessment on revision_60_fine.',controls:['Open assessment'],expected:'25 passed checks and one held review, focused on the requested result.',actual:'Exact assessment and fine-result focus retained.',...await capture('S11','Assessment')});
  await page.goto(saved.url);
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:30000});
  await card.getByRole('button',{name:'Open producing step',exact:true}).click();
  const editor=page.locator('[data-workflow-file="'+prepared.path+'"]:visible');
  await expect(editor).toBeVisible({timeout:30000});
  await expect(editor.getByTestId('workflow-file-menu')).toBeVisible();
  await record({id:'S12',state:'pass',label:'Producing engineering step opens',summary:'The saved comparison returns to the actual producing step in the accepted process editor.',purpose:'Keep the tailored interface and refined editor connected.',action:'Reopen the saved comparison and click Open producing step on revision_60_fine.',controls:['Open producing step','Workflow files'],expected:'The accepted heat process editor opens at its producer.',actual:'Accepted heat editor opened from the exact result.',...await capture('S12','Producing step')});
  status.overall='pass';
} catch(error){
  status.overall='blocked';
  await record({id:'STOP',state:'blocked',label:'Entry stopped',summary:'The normal workspace entry did not meet the expected state.',purpose:'Retain the first stopping point.',action:'Stop at the unexpected entry state.',controls:['Workflows'],expected:'Workspace and established editor available.',actual:error.message,...await capture('STOP','Stopping point')});
  writeFileSync(path.join(privateRoot,'heat-ui-saved-navigation-qualified-dom.json'),JSON.stringify({url:cleanUrl(),body:await page.locator('body').innerText(),buttons:await page.locator('button').evaluateAll(es=>es.map(e=>({text:e.textContent,label:e.getAttribute('aria-label'),id:e.getAttribute('data-testid')})))},null,2));
} finally {
  publish();
  writeFileSync(path.join(root,'browser-diagnostics.json'),JSON.stringify(diagnostics,null,2));
  await context.tracing.stop({path:path.join(privateRoot,'heat-ui-saved-navigation-qualified-trace.zip')});
  await browser.close();
  console.log(JSON.stringify({status:status.overall,report:path.join(root,'report.html'),steps:status.steps.map(s=>({id:s.id,state:s.state,actual:s.actual}))}));
}
