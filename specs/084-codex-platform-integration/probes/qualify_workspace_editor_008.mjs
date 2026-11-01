import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const args=Object.fromEntries(process.argv.slice(2).map(value=>value.slice(2).split('=')));
const privateRoot=path.resolve(args.contextRoot);
const proof = JSON.parse(readFileSync(path.join(privateRoot, 'browser-context.json'), 'utf8'));
const root=path.resolve(args.output);
if (existsSync(root)) throw new Error('Preserve the previous walkthrough; select a fresh root');
for (const dir of ['playwright','screenshots/raw','screenshots/annotated','trace']) mkdirSync(path.join(root, dir), {recursive:true});
const status={title:'New workflow authoring through the served source workspace',summary:'Continue the newly saved scratch workflow through type rejection, layout persistence, zoom and concurrent-save protection. No process execution or engineering review.',overall:'pending',updated:new Date().toISOString(),manualSteps:[{label:'Workspace',instruction:'Open the isolated workspace and click Workflows.'},{label:'New workflow',instruction:'Choose Workflow files, then New workflow.'},{label:'Author',instruction:'Read the creation instructions, provide a name and create the verification workflow.'}],steps:[]};
const escape = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function publish() {
  status.updated = new Date().toISOString();
  writeFileSync(path.join(root,'status.json'),JSON.stringify(status,null,2));
  writeFileSync(path.join(root,'report.html'),`<!doctype html><html><head><meta charset="utf-8"><title>${escape(status.title)}</title><style>body{font:16px system-ui;max-width:1100px;margin:24px auto;background:#101922;color:#e8f4f7}section{padding:18px;border:1px solid #647486;margin:16px 0}.pass{border-color:#64bda4}.blocked{border-color:#ee7373}img{max-width:100%}a{color:#7fe0cb}</style></head><body><h1>${escape(status.title)}</h1><p>${escape(status.summary)}</p><p>Status: ${escape(status.overall)}</p><h2>Manual steps</h2><ol>${status.manualSteps.map(s=>`<li>${escape(s.instruction)}</li>`).join('')}</ol>${status.steps.map(s=>`<section class="${s.state}"><h2>${escape(s.label)} Â· ${escape(s.state)}</h2><p>${escape(s.summary)}</p><p>Expected: ${escape(s.expected)}</p><p>Actual: ${escape(s.actual)}</p>${['raw','annotated'].filter(k=>s[k]).map(k=>`<p>${k}<a class="image-button" href="${escape(s[k])}" onclick="event.preventDefault();document.getElementById('full-image').src=this.href;document.getElementById('image-dialog').showModal()"><img src="${escape(s[k])}" alt="${escape(s.label)} ${k}"></a></p>`).join('')}</section>`).join('')}<dialog id="image-dialog"><button onclick="document.getElementById('image-dialog').close()">Close</button><img id="full-image" style="max-width:none" alt="Full-size walkthrough evidence"></dialog></body></html>`);
}
writeFileSync(path.join(root,'progress.md'),'# Served workflow authoring continuation\n\nPrepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.\n');
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


const editor=page.locator('[data-testid="retained-workspace-workflow-panel"][aria-hidden="false"]');
let stage='Workspace entry';
async function checkpoint(id,label,action,controls,expected,actual) {
  await record({id,state:'pass',label,summary:actual,purpose:'Preserve normal-workspace authoring behavior.',action,controls,expected,actual,...await capture(id,label)});
}

try {
  const scratch='workflows/editor-verification-083-004.workflow.wflow';
  await page.goto(proof.frontend_url+'/workspace/'+proof.workspace_id+'?workflow=canonical&workflowPath='+encodeURIComponent(scratch));
  const concept=editor.getByTestId('workflow-recovery-concept');
  await expect(concept).toHaveAttribute('data-semantic-digest',/^sha256:[a-f0-9]{64}$/,{timeout:60000});
  await expect(editor.getByTestId('workflow-recovery-block-block.text-input-1')).toBeVisible();
  stage='Compact two-times page scale';
  await page.setViewportSize({width:720,height:550});
  const cdp=await context.newCDPSession(page);
  await cdp.send('Emulation.setPageScaleFactor',{pageScaleFactor:2});
  await expect.poll(()=>page.evaluate(()=>window.visualViewport?.scale??1)).toBe(2);
  await expect(editor.getByTestId('workflow-recovery-view-select')).toBeVisible();
  await expect(editor.getByRole('button',{name:'Fit workflow to view',exact:true})).toBeVisible();
  await editor.getByTestId('workflow-recovery-block-block.text-input-1').focus();
  await page.keyboard.press('Enter');
  await expect(editor.getByTestId('workflow-recovery-input-text-block.text-input-1')).toHaveValue('Assess a 100 mm engineering specimen. Units: mm.');
  const aria=await concept.ariaSnapshot();
  expect(aria).toContain('combobox "Workflow view"');
  expect(aria).toContain('button "Fit workflow to view"');
  await checkpoint('S13','Compact keyboard and scale','Use a 720 by 550 viewport at two-times page scale, then select Text input with Enter.',['Workflow view','Fit workflow to view','Text input'],'Compact view and keyboard inspector remain available.','Measured visual viewport scale is 2; view selector, Fit control and keyboard-selected input inspector are available.');
  await cdp.send('Emulation.setPageScaleFactor',{pageScaleFactor:1});
  await page.setViewportSize({width:1440,height:1000});
  stage='Concurrent save conflict';
  await editor.getByTestId('workflow-recovery-view-code').click();
  const src=editor.getByTestId('workflow-recovery-source-editor');
  const current=await src.inputValue();
  const local=current.replace('100 mm engineering specimen','102 mm engineering specimen');
  expect(local).not.toBe(current);
  await src.fill(local); await editor.getByTestId('workflow-recovery-source-apply').click();
  const query=new URLSearchParams({session_id:proof.session_id,path:scratch});
  const headers={Authorization:'Bearer '+proof.api_token};
  const response=await context.request.get(proof.api_url+'/api/workspace/workflow-sources?'+query,{headers});
  expect(response.ok()).toBeTruthy();
  const document=await response.json();
  const concurrent=document.source.replace('100 mm engineering specimen','101 mm engineering specimen');
  expect(concurrent).not.toBe(document.source);
  const update=await context.request.put(proof.api_url+'/api/workspace/workflow-sources',{headers,data:{session_id:proof.session_id,path:scratch,source:concurrent,expected_storage_revision:document.storage_revision,expected_storage_digest:document.storage_digest,semantic_change_validated:true}});
  expect(update.ok()).toBeTruthy();
  await editor.getByTestId('workflow-recovery-save').click();
  const saveState=editor.getByTestId('workflow-recovery-save-status');
  await expect(saveState).toContainText('changed elsewhere');
  await expect(saveState).toContainText('local edits are still here');
  await expect(src).toHaveValue(local);
  const readback=await context.request.get(proof.api_url+'/api/workspace/workflow-sources?'+query,{headers});
  expect((await readback.json()).source).toBe(concurrent);
  await checkpoint('S14','Concurrent save protects both edits','Change local specimen text, update the same scratch source through its real CAS endpoint, then Save.',['Source','Apply','Save'],'Conflict retains local text and does not overwrite the other saved edit.','A real 409 conflict preserves the 102 mm local edit and the 101 mm concurrent saved edit.');
  const unexpected=diagnostics.failedResponses.filter(r=>!(r.path==='/api/agent/models'&&r.status===503)&&!(r.path==='/api/workspace/workflow-sources'&&r.status===409));
  if(unexpected.length||diagnostics.pageErrors.length) throw new Error('Unexpected diagnostics: '+JSON.stringify({unexpected,pageErrors:diagnostics.pageErrors}));
  status.overall='pass';
} catch(error) {
  status.overall='blocked'; await record({id:'STOP',state:'blocked',label:'Editor continuation stopped at '+stage,summary:'First unexpected state retained; no execution or review submitted.',purpose:'Preserve real failure.',action:stage,controls:[stage],expected:'Editor action succeeds without guesses or workarounds.',actual:error.message,...await capture('STOP',stage)});
} finally {
  publish();writeFileSync(path.join(root,'browser-diagnostics.json'),JSON.stringify(diagnostics,null,2));
  await context.tracing.stop({path:path.join(privateRoot,'editor-trace-008.zip')});await browser.close();
  console.log(JSON.stringify({overall:status.overall,steps:status.steps.map(s=>({id:s.id,state:s.state,actual:s.actual}))}));
}
