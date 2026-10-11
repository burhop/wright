import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const privateRoot = path.resolve('.local-run/process-interfaces-083/t052-mounted-native-004');
const proof = JSON.parse(readFileSync(path.join(privateRoot, 'browser-context.json'), 'utf8'));
const prepared = JSON.parse(readFileSync(path.join(privateRoot, 'prepared-run.json'), 'utf8'));
const root = path.resolve('artifacts/process-interfaces/083/20261002-editor-native-003/workspace-walkthrough');
if (existsSync(root)) throw new Error('Preserve the previous walkthrough; select a fresh root');
for (const dir of ['playwright','screenshots/raw','screenshots/annotated','trace']) mkdirSync(path.join(root, dir), {recursive:true});
const status={title:'New workflow authoring through the installed workspace',summary:'A fresh empty verification workflow, preserved editor authoring and no execution; stop at the first confusing or failing state.',overall:'pending',updated:new Date().toISOString(),manualSteps:[{label:'Workspace',instruction:'Open the isolated workspace and click Workflows.'},{label:'New workflow',instruction:'Choose Workflow files, then New workflow.'},{label:'Author',instruction:'Read the creation instructions, provide a name and create the verification workflow.'}],steps:[]};
const escape = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function publish() {
  status.updated = new Date().toISOString();
  writeFileSync(path.join(root,'status.json'),JSON.stringify(status,null,2));
  writeFileSync(path.join(root,'report.html'),`<!doctype html><html><head><meta charset="utf-8"><title>${escape(status.title)}</title><style>body{font:16px system-ui;max-width:1100px;margin:24px auto;background:#101922;color:#e8f4f7}section{padding:18px;border:1px solid #647486;margin:16px 0}.pass{border-color:#64bda4}.blocked{border-color:#ee7373}img{max-width:100%}a{color:#7fe0cb}</style></head><body><h1>${escape(status.title)}</h1><p>${escape(status.summary)}</p><p>Status: ${escape(status.overall)}</p><h2>Manual steps</h2><ol>${status.manualSteps.map(s=>`<li>${escape(s.instruction)}</li>`).join('')}</ol>${status.steps.map(s=>`<section class="${s.state}"><h2>${escape(s.label)} Â· ${escape(s.state)}</h2><p>${escape(s.summary)}</p><p>Expected: ${escape(s.expected)}</p><p>Actual: ${escape(s.actual)}</p>${['raw','annotated'].filter(k=>s[k]).map(k=>`<p>${k}<a class="image-button" href="${escape(s[k])}" onclick="event.preventDefault();document.getElementById('full-image').src=this.href;document.getElementById('image-dialog').showModal()"><img src="${escape(s[k])}" alt="${escape(s.label)} ${k}"></a></p>`).join('')}</section>`).join('')}<dialog id="image-dialog"><button onclick="document.getElementById('image-dialog').close()">Close</button><img id="full-image" style="max-width:none" alt="Full-size walkthrough evidence"></dialog></body></html>`);
}
writeFileSync(path.join(root,'progress.md'),'# Installed workflow authoring continuation\n\nPrepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.\n');
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
async function record(step){status.steps.push(step);publish();appendFileSync(path.join(root,'progress.md'),`\n## ${new Date().toISOString()} UTC â€” ${step.label}\n\nURL: ${cleanUrl()}\nAction: ${step.action}\nControls: ${step.controls.join(', ')}\nExpected: ${step.expected}\nActual: ${step.actual}\nStatus: ${step.state}\nScreenshots: ${step.raw??''}; ${step.annotated??''}\n`);}


let stage='Workspace entry';
async function checkpoint(id,label,action,controls,expected,actual) {
  await record({id,state:'pass',label,summary:actual,purpose:'Preserve normal-workspace authoring behavior.',action,controls,expected,actual,...await capture(id,label)});
}
try {
  await page.goto(proof.frontend_url+'/workspace/'+proof.workspace_id);
  await expect(page.getByRole('button',{name:'Workflows',exact:true})).toBeVisible({timeout:60000});
  await page.getByRole('button',{name:'Workflows',exact:true}).click();
  await expect(page.getByTestId('workflow-file-menu')).toBeVisible({timeout:60000});
  await checkpoint('S01','Normal workspace editor entry','Click Workflows.',['Workflows','Workflow files'],'Existing editor opens within the workspace.','Existing editor and workflow file menu are visible.');
  stage='New workflow instructions';
  await page.getByTestId('workflow-file-menu').click();
  await page.getByRole('button',{name:'New workflow',exact:true}).click();
  const dialog=page.getByRole('dialog');
  await expect(dialog).toContainText('Starts with a blank workflow');
  await expect(dialog).not.toContainText('editable engineering example');
  await checkpoint('S02','Accurate new-workflow instructions','Open New workflow.',['Workflow name','Create workflow'],'Instructions describe a blank workflow.','The installed dialog describes blank-workflow creation and readiness.');
  stage='Blank workflow creation';
  await dialog.getByLabel('Workflow name').fill('Editor verification 083 002');
  await dialog.getByRole('button',{name:'Create workflow',exact:true}).click();
  await expect(dialog).toHaveCount(0);
  const concept=page.getByTestId('workflow-recovery-concept');
  await expect(concept).toBeVisible();
  await page.getByTestId('workflow-recovery-view-code').click();
  const sourceEditor=page.getByTestId('workflow-recovery-source-editor');
  await expect(sourceEditor).toHaveValue(/Editor verification 083 002/);
  expect(await sourceEditor.inputValue()).not.toMatch(/^\s*(task|input|connection|item)\s/m);
  await checkpoint('S03','Fresh blank source','Create Editor verification 083 002 and open Source.',['Workflow name','Create workflow','Source'],'A new, separate workflow has no prefilled engineering steps.','The scratch workflow source contains its name and no task/input/connection/item declarations.');
  await page.getByTestId('workflow-recovery-view-diagram').click();
  stage='Text input creation';
  await page.getByTestId('workflow-recovery-create-group-input').click();
  await page.getByTestId('workflow-recovery-create-template-text-input').click();
  const input=page.getByTestId('workflow-recovery-block-block.text-input-1');
  await expect(input).toBeVisible();
  await input.focus(); await input.press('Enter');
  const inputText=page.getByTestId('workflow-recovery-input-text-block.text-input-1');
  await expect(inputText).toBeVisible();
  await inputText.fill('Assess a 100 mm engineering specimen. Units: mm.');
  await checkpoint('S04','Direct input configuration','Create Text input and enter engineering text.',['Create','Text input','Text'],'Input inspector edits the same workflow.','Text input and its direct inspector field are visible and configured.');
  stage='Undo and redo';
  await page.getByTestId('workflow-recovery-undo').click();
  await expect(inputText).not.toHaveValue('Assess a 100 mm engineering specimen. Units: mm.');
  await page.getByTestId('workflow-recovery-redo').click();
  await expect(inputText).toHaveValue('Assess a 100 mm engineering specimen. Units: mm.');
  await checkpoint('S05','Undo and redo','Undo the text edit, then Redo.',['Undo','Redo'],'Both controls restore accepted editing state.','Undo removes the entered value and Redo restores it.');
  stage='AI prompt creation';
  for(let i=1;i<=2;i++) {
    await page.getByTestId('workflow-recovery-create-group-document').click();
    await page.getByTestId('workflow-recovery-create-template-ai-prompt').click();
    await expect(page.getByTestId('workflow-recovery-block-block.ai-prompt-'+i)).toBeVisible();
  }
  await checkpoint('S06','Individual AI steps','Create two AI prompt steps.',['Create','AI prompt'],'Both new steps appear in the established canvas.','Two separate AI prompt steps appear; no model work is started.');
  stage='Typed keyboard connection';
  const output=page.getByTestId('workflow-recovery-handle-port.ai-prompt-1-document-out');
  const target=page.getByTestId('workflow-recovery-handle-port.ai-prompt-2-prompt-in');
  await output.focus(); await output.press('Enter');
  await target.focus(); await target.press('Enter');
  await page.getByTestId('workflow-recovery-view-code').click();
  await expect(sourceEditor).toHaveValue(/connection /);
  await checkpoint('S07','Typed connection in source','Connect the first Response to the second Prompt using Enter.',['Response output','Prompt input','Source'],'A type-compatible connection appears in the same source.','The keyboard-created connection appears in canonical source.');
  stage='Save and reopen';
  const acceptedText=await sourceEditor.inputValue();
  await page.getByTestId('workflow-recovery-save').click();
  await expect(page.getByTestId('workflow-recovery-save-status')).toHaveText('Saved',{timeout:30000});
  await page.reload();
  await expect(page.getByTestId('workflow-recovery-view-code')).toBeVisible({timeout:60000});
  await page.getByTestId('workflow-recovery-view-code').click();
  await expect(page.getByTestId('workflow-recovery-source-editor')).toHaveValue(acceptedText);
  await checkpoint('S08','Saved source reopens','Save and reload the workspace.',['Save','Source'],'The exact saved workflow reopens without execution.','Reload restores the saved input, two AI steps and connection exactly.');
  stage='Invalid source containment';
  const revision=await page.getByTestId('workflow-recovery-concept').getAttribute('data-revision');
  await page.getByTestId('workflow-recovery-source-editor').fill('workflow editor_verification_083_002\n  revision: 99\nend\n');
  await page.getByTestId('workflow-recovery-source-apply').click();
  await expect(page.getByTestId('workflow-recovery-diagnostic-WFR-SOURCE-FIELD-MANAGED')).toBeVisible();
  await expect(page.getByTestId('workflow-recovery-concept')).toHaveAttribute('data-revision',revision);
  await expect(page.getByTestId('workflow-recovery-run-start')).toBeDisabled();
  await checkpoint('S09','Invalid draft stays isolated','Enter a source draft containing managed revision: 99 and Apply.',['Source','Apply','Run'],'Invalid source leaves accepted revision intact and blocks Run.','Managed-field diagnostic is visible, accepted revision is unchanged and Run is disabled.');
  const unexpected=diagnostics.failedResponses.filter(r=>!(r.path==='/api/agent/models'&&r.status===503));
  if(unexpected.length||diagnostics.pageErrors.length) throw new Error('Unexpected diagnostics: '+JSON.stringify({unexpected,pageErrors:diagnostics.pageErrors}));
  status.overall='pass';
} catch(error) {
  status.overall='blocked';
  await record({id:'STOP',state:'blocked',label:'Editor verification stopped at '+stage,summary:'First unexpected state retained; no execution or review action submitted.',purpose:'Preserve a real editor failure.',action:stage,controls:[stage],expected:'Normal editor action succeeds without guesses or workarounds.',actual:error.message,...await capture('STOP',stage)});
} finally {
  publish();writeFileSync(path.join(root,'browser-diagnostics.json'),JSON.stringify(diagnostics,null,2));
  await context.tracing.stop({path:path.join(privateRoot,'editor-trace-003.zip')});
  await browser.close();console.log(JSON.stringify({overall:status.overall,steps:status.steps.map(s=>({id:s.id,state:s.state,actual:s.actual}))}));
}
