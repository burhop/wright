import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const privateRoot = path.resolve('.local-run/process-interfaces-083/t047-heat-repeat-013');
const proof = JSON.parse(readFileSync(path.join(privateRoot, 'browser-context.json'), 'utf8'));
const prepared = JSON.parse(readFileSync(path.join(privateRoot, 'prepared-run.json'), 'utf8'));
const root = path.resolve('artifacts/ui-walkthrough/process-interfaces-083-heat/20261003T051700Z-heat-repeat-authoring-002');
if (existsSync(root)) throw new Error('Preserve the previous walkthrough; select a fresh root');
for (const dir of ['playwright','screenshots/raw','screenshots/annotated','trace']) mkdirSync(path.join(root, dir), {recursive:true});
const status = {title:'Heat-spreader interface authoring through Wright', summary:'Normal Wright workspace and actual isolated engineering run. No mocked routes or physical action.', overall:'pending', updated:new Date().toISOString(), manualSteps:[
  {label:'Open workspace', instruction:'Open the isolated Heat-spreader comparison proof workspace.'},
  {label:'Open workflows', instruction:'Click Workflows in the workspace activity bar.'},
  {label:'Choose process',instruction:'Click Workflow files, then Open workflow. Select the saved heat-spreader workflow.'},
  {label:'Use process',instruction:'Click Use saved process. Reopen the recorded run from its workspace link.'},
  {label:'Create an interface',instruction:'Click Create or choose interface. Enter Heat-spreader candidate comparison as the Interface title and request a reusable comparison with shared inputs, results, findings and review controls. Click Create interface.'},
  {label:'Preview',instruction:'Wait for Preview ready, then click Open preview and inspect the read-only interface.'},
  {label:'Save',instruction:'Return to the common working tab and click Save interface.'},
  {label:'Open saved interface',instruction:'Click Open saved interface. Confirm it opens in a Wright workspace tab on the existing run.'},
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
  const commonTab=await page.getByTestId('editor-tabs-container').locator('[role="tab"][aria-selected="true"]').getAttribute('data-testid');
  expect(commonTab).toBeTruthy();
  await page.getByRole('button',{name:'Create or choose interface',exact:true}).click();
  await expect(page.getByRole('textbox',{name:'Interface title',exact:true})).toBeVisible();
  await record({id:'S08',state:'pass',label:'Wright interface authoring',summary:'The process exposes Wright�s shared interface creation controls.',purpose:'Author the tailored experience through Wright, within the workspace.',action:'Click Create or choose interface.',controls:['Interface title','How should this interface help the user?','Create interface'],expected:'Native authoring controls tied to this exact process.',actual:'Wright interface authoring controls visible.',...await capture('S08','Interface authoring')});
  await page.getByRole('textbox',{name:'Interface title',exact:true}).fill('Heat-spreader candidate comparison');
  await page.getByRole('textbox',{name:'How should this interface help the user?',exact:true}).fill(
    'Create a reusable heat-spreader engineering comparison using the supplied reference template and current interaction contract. The layout must work across runs without depending on output filenames or the first run ID. '+
    'Keep the supplied manifest identities. Use public Wright components and ResultRepresentation for supported data. '+
    'Show actual progress, all current result cards arranged for comparing the two candidates, and pending findings/review. '+
    'Use snapshot data and the template callbacks for exact evidence/navigation. '+
    'Use shared input/readiness and pending-interaction controls, plus exact result/assessment/block navigation. Do not add native protocols, measurements, engineering verdicts or execution. '+
    'Return the required source/manifest JSON immediately.'
  );
  await expect(page.getByRole('button',{name:'Create interface',exact:true})).toBeEnabled({timeout:45000});
  const acceptedResponse=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/authoring-jobs'));
  await page.getByRole('button',{name:'Create interface',exact:true}).click();
  const accepted=await acceptedResponse; expect(accepted.status()).toBe(202);
  const job=await accepted.json();
  writeFileSync(path.join(privateRoot,'heat-ui-authoring-repeat-002-receipt.json'),JSON.stringify(job,null,2));
  await expect(page.getByRole('region',{name:'Interface creation progress'})).toBeVisible();
  await record({id:'S09',state:'pass',label:'Visible interface creation',summary:'Wright is creating the tailored interface using its actual configured default model.',purpose:'Follow the backend-owned authoring job.',action:'Enter Interface title: Heat-spreader candidate comparison. Request: '+await page.getByRole('textbox',{name:'How should this interface help the user?',exact:true}).inputValue()+'. Click Create interface.',controls:['Interface title','How should this interface help the user?','Create interface','Interface creation progress'],expected:'Accepted job and visible generation progress.',actual:'Actual interface job accepted; creation progress visible.',...await capture('S09','Creating comparison')});
  await expect(page.getByRole('heading',{name:/^(Preview ready|Interface needs attention|Interface creation cancelled)$/})).toBeVisible({timeout:330000});
  await expect(page.getByRole('heading',{name:'Preview ready',exact:true})).toBeVisible();
  await record({id:'S10',state:'pass',label:'Built comparison ready',summary:'The actual generated interface has passed Wright�s fixed local build.',purpose:'Inspect the built preview before saving.',action:'Wait for Preview ready.',controls:['Open preview'],expected:'Successful built revision ready for preview.',actual:'Preview ready is visible.',...await capture('S10','Preview ready')});
  const previewResponse=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/preview'));
  await page.getByRole('button',{name:'Open preview',exact:true}).click();
  const preview=await previewResponse; expect(preview.status()).toBe(200);
  writeFileSync(path.join(privateRoot,'heat-ui-repeat-002-preview-presentation.json'),JSON.stringify(await preview.json(),null,2));
  const frame=page.locator('[data-testid="surface-panel-host"]:visible').frameLocator('iframe');
  await expect(frame.getByText('Preview - process controls are read-only.',{exact:true})).toBeVisible({timeout:30000});
  await expect(frame.locator('#wright-process-ui')).not.toContainText('Interface unavailable');
  await expect(frame.locator('#wright-process-ui')).not.toBeEmpty();
  await record({id:'S11',state:'pass',label:'Managed heat comparison preview',summary:'The actual generated comparison renders in a Wright tab with read-only preview controls.',purpose:'Inspect the generated UI and its actual backend evidence.',action:'Click Open preview.',controls:['Open preview'],expected:'Isolated managed preview renders and reads the process contract.',actual:'Managed preview connected and rendered.',...await capture('S11','Heat comparison preview')});
  await page.getByTestId(commonTab).click();
  await expect(page.getByRole('button',{name:'Save interface',exact:true})).toBeEnabled({timeout:15000});
  const savedResponse=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/save'));
  await page.getByRole('button',{name:'Save interface',exact:true}).click();
  const saved=await savedResponse; expect(saved.status()).toBe(200);
  const revision=await saved.json();
  writeFileSync(path.join(privateRoot,'heat-ui-repeat-002-saved-revision.json'),JSON.stringify(revision,null,2));
  await expect(page.getByRole('heading',{name:'Interface saved',exact:true})).toBeVisible();
  await record({id:'S12',state:'pass',label:'Reusable heat interface saved',summary:'The previewed interface is retained as a versioned process asset.',purpose:'Save the exact checked source, bindings and build.',action:'Return to the common tab and click Save interface.',controls:['Save interface','Open saved interface'],expected:'The exact previewed revision is saved.',actual:'Interface saved with its built revision.',...await capture('S12','Saved heat comparison')});
  const presentedResponse=page.waitForResponse(r=>r.request().method()==='POST'&&new URL(r.url()).pathname.endsWith('/present'));
  await page.getByRole('button',{name:'Open saved interface',exact:true}).click();
  const presented=await presentedResponse; expect(presented.status()).toBe(200);
  writeFileSync(path.join(privateRoot,'heat-ui-repeat-002-working-presentation.json'),JSON.stringify(await presented.json(),null,2));
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:30000});
  await expect(frame.locator('#wright-process-ui')).not.toContainText('Interface unavailable');
  await record({id:'S13',state:'pass',label:'Saved heat comparison opens',summary:'The saved working interface opens within Wright and reads the existing run.',purpose:'Open saved built assets without UI regeneration.',action:'Click Open saved interface.',controls:['Open saved interface'],expected:'Saved working interface connected to the same process/run.',actual:'Saved comparison is connected in a workspace tab.',...await capture('S13','Saved working comparison')});
  writeFileSync(path.join(privateRoot,'heat-ui-authoring-repeat-002-dom.json'),JSON.stringify({url:cleanUrl(),body:await page.locator('body').innerText(),buttons:await page.locator('button').evaluateAll(es=>es.map(e=>({text:e.textContent,label:e.getAttribute('aria-label'),id:e.getAttribute('data-testid')})))},null,2));
  status.overall='pass';
} catch(error){
  status.overall='blocked';
  await record({id:'STOP',state:'blocked',label:'Entry stopped',summary:'The normal workspace entry did not meet the expected state.',purpose:'Retain the first stopping point.',action:'Stop at the unexpected entry state.',controls:['Workflows'],expected:'Workspace and established editor available.',actual:error.message,...await capture('STOP','Stopping point')});
  writeFileSync(path.join(privateRoot,'heat-ui-authoring-repeat-002-dom.json'),JSON.stringify({url:cleanUrl(),body:await page.locator('body').innerText(),buttons:await page.locator('button').evaluateAll(es=>es.map(e=>({text:e.textContent,label:e.getAttribute('aria-label'),id:e.getAttribute('data-testid')})))},null,2));
} finally {
  publish();
  writeFileSync(path.join(root,'browser-diagnostics.json'),JSON.stringify(diagnostics,null,2));
  await context.tracing.stop({path:path.join(privateRoot,'heat-ui-authoring-repeat-002-trace.zip')});
  await browser.close();
  console.log(JSON.stringify({status:status.overall,report:path.join(root,'report.html'),steps:status.steps.map(s=>({id:s.id,state:s.state,actual:s.actual}))}));
}


