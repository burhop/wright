import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';

const privateRoot=path.resolve('.local-run/process-interfaces-083/t047-fresh-mixed-071');
const load=name=>JSON.parse(readFileSync(path.join(privateRoot,name),'utf8'));
const proof=load('browser-context.json'),prepared=load('prepared-run.json');
const root=path.resolve('artifacts/ui-walkthrough/process-interfaces-083-original-inputs/20261004-assessment-readback-126');
if(existsSync(root))throw Error('Preserve prior evidence');
for(const dir of ['playwright','screenshots/raw','screenshots/annotated','trace'])mkdirSync(path.join(root,dir),{recursive:true});
const status={title:'Inspect the two original source assessments',summary:'Read-only exact assessment display for two completed digital preparation chains. Both remain held for required human engineering review. No new execution, decision or acceptance.',overall:'pending',updated:new Date().toISOString(),manualSteps:[
 {label:'Workspace',instruction:'Open the isolated workspace and click Workflows.'},
 {label:'Saved process',instruction:'Click Workflow files, Open workflow, then printed-replacement-part-common-digital-083.workflow.wflow.'},
 {label:'Common view',instruction:'Click Use saved process. Inspect the original inputs and any readiness reason.'},
 {label:'Run',instruction:'Click Prepare and check inputs, then Start process. Inspect the recorded digital results; reload to reconcile the same run.'}],steps:[]};
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function publish(){status.updated=new Date().toISOString();writeFileSync(path.join(root,'status.json'),JSON.stringify(status,null,2));writeFileSync(path.join(root,'report.html'),`<!doctype html><html><head><meta charset="utf-8"><title>${esc(status.title)}</title><style>body{font:16px system-ui;max-width:1100px;margin:24px auto;background:#101922;color:#e8f4f7}section{padding:18px;border:1px solid #647486;margin:16px 0}.pass{border-color:#64bda4}.blocked{border-color:#ee7373}img{max-width:100%}a{color:#7fe0cb}</style></head><body><h1>${esc(status.title)}</h1><p>${esc(status.summary)}</p><p>${esc(status.overall)}</p><h2>Manual steps</h2><ol>${status.manualSteps.map(s=>`<li>${esc(s.instruction)}</li>`).join('')}</ol>${status.steps.map(s=>`<section class="${s.state}"><h2>${esc(s.label)} · ${esc(s.state)}</h2><p>${esc(s.summary)}</p><p>Expected: ${esc(s.expected)}</p><p>Actual: ${esc(s.actual)}</p>${['raw','annotated'].filter(k=>s[k]).map(k=>`<a class="image-button" href="${esc(s[k])}" onclick="event.preventDefault();document.querySelector('#full').src=this.href;document.querySelector('dialog').showModal()"><img src="${esc(s[k])}" alt="${esc(s.label)} ${k}"></a>`).join('')}</section>`).join('')}<dialog><button onclick="document.querySelector('dialog').close()">Close</button><img id="full" style="max-width:none" alt="Full-size evidence"></dialog></body></html>`);}
writeFileSync(path.join(root,'progress.md'),'# Fresh common-view original-input walkthrough\n\nPrepared before navigation. Read-only continuation after the retained harness expected Completed instead of the actual Process completed label. The original common-view start and completed run are preserved; this continuation never starts or changes the process. Private authenticated trace is not published.\n');
writeFileSync(path.join(root,'trace/README.md'),'Tracing starts before navigation. The authenticated trace is retained in the private proof root; sanitized diagnostics accompany the report.\n');
writeFileSync(path.join(root,'playwright/common-view.mjs'),readFileSync(new URL(import.meta.url)));publish();
const browser=await chromium.launch({headless:true}),context=await browser.newContext({viewport:{width:1440,height:1000}});
await context.addCookies([{name:'wright_session',value:proof.browser_cookie,url:proof.frontend_url+'/api',httpOnly:true,sameSite:'Strict'}]);
await context.tracing.start({screenshots:true,snapshots:true,sources:true});
const page=await context.newPage(),diagnostics={console:[],pageErrors:[],failedResponses:[]},posts=[],snapshots=[],pending=[];
const clean=s=>String(s).replaceAll(proof.api_token,'<redacted>').replaceAll(proof.browser_cookie,'<redacted>');
page.on('console',m=>{if(m.type()==='error')diagnostics.console.push(clean(m.text()));});
page.on('pageerror',e=>diagnostics.pageErrors.push(clean(e.message)));
page.on('request',r=>{if(r.method()!=='GET')posts.push({path:new URL(r.url()).pathname,method:r.method()});});
page.on('response',r=>{const p=new URL(r.url()).pathname;if(r.status()>=400)diagnostics.failedResponses.push({path:p,status:r.status()});if(r.status()===200&&(p.endsWith('/interaction') || /\/runs\/[^/]+$/.test(p)))pending.push(r.json().then(v=>snapshots.push(v)).catch(()=>{}));});
async function capture(id){const raw=`screenshots/raw/${id}.png`,annotated=`screenshots/annotated/${id}.png`;await page.screenshot({path:path.join(root,raw),fullPage:true});await page.evaluate(()=>{const layer=document.createElement('div');layer.id='walkthrough-overlay';layer.style='position:fixed;inset:0;pointer-events:none;z-index:2147483647';const labels=[];for(const e of document.querySelectorAll('button,input,textarea,select')){const r=e.getBoundingClientRect();if(r.width<2||r.height<2||r.top<0||r.top>innerHeight)continue;const text=(e.getAttribute('aria-label')||e.textContent||e.getAttribute('placeholder')||'').trim().slice(0,70);if(!text)continue;const i=labels.length+1;labels.push(i+': '+text);const n=document.createElement('span');n.textContent=String(i);n.style=`position:absolute;left:${r.left}px;top:${r.top}px;background:#ffdf56;color:#111;padding:2px 5px;font:12px system-ui`;layer.appendChild(n);}const legend=document.createElement('div');legend.textContent=labels.join(' | ');legend.style='position:absolute;bottom:8px;right:8px;left:8px;background:#111e;color:white;padding:8px;font:12px system-ui';layer.appendChild(legend);document.body.appendChild(layer);});await page.screenshot({path:path.join(root,annotated),fullPage:true});await page.locator('#walkthrough-overlay').evaluate(e=>e.remove());return {raw,annotated};}
async function record(id,label,action,expected,actual){const step={id,state:'pass',label,summary:actual,purpose:expected,action,controls:[action],expected,actual,...await capture(id)};status.steps.push(step);publish();appendFileSync(path.join(root,'progress.md'),`\n## ${new Date().toISOString()} UTC — ${label}\n\nURL: ${clean(page.url())}\nAction: ${action}\nControls: ${action}\nExpected: ${expected}\nActual: ${actual}\nStatus: PASS\nScreenshots: ${step.raw}; ${step.annotated}\n`);}
const common=()=>page.locator('[data-testid="common-process-view"]:visible');



status.manualSteps=[{label:'Recorded run',instruction:'Open the exact recorded-run workspace link.'},{label:'Assessment',instruction:'Click Open assessment on repaired_mesh.stl, then scroll to the opened assessment.'},{label:'Review hold',instruction:'Inspect the digital findings and required human-review hold; leave decisions unanswered.'}];publish();
try {
 for(const [ordinal,id] of [['first','A01'],['second','A02']]) {
  const receipt=load(ordinal+'-start-receipt.json').body;
  const snapshot=load(ordinal+'-final-interaction.json'),gate=load(ordinal+'-source-gate-event.json');
  const result=snapshot.outputs.find(o=>o.port_id==='repaired_mesh');expect(result).toBeTruthy();
  const u=new URL(proof.frontend_url+'/workspace/'+proof.workspace_id);
  for(const[k,v]of Object.entries({processView:'view-mixed-assessment-126-'+ordinal,processPath:prepared.path,processDigest:prepared.expected_storage_digest,processRun:receipt.run_id}))u.searchParams.set(k,v);
  await page.goto(u.href);await expect(common()).toBeVisible({timeout:45000});
  await expect(common().locator('[data-result-id]')).toHaveCount(20,{timeout:45000});
  await capture(id+'-before');
  await common().locator('[data-result-id="'+result.result_id+'"]').getByRole('button',{name:'Open assessment',exact:true}).click();
  const assessment=common().locator('pre').filter({hasText:gate.assessment_id});
  await expect(assessment).toBeVisible({timeout:45000});
  await expect(assessment).toContainText('"pass": 17');await expect(assessment).toContainText('"blocked": 1');
  const value=JSON.parse(await assessment.innerText());
  expect(value.assessment_id).toBe(gate.assessment_id);
  await assessment.scrollIntoViewIfNeeded();
  writeFileSync(path.join(privateRoot,ordinal+'-assessment-126-dom.json'),JSON.stringify({run_id:receipt.run_id,source_digest:prepared.expected_storage_digest,result_id:result.result_id,assessment_id:gate.assessment_id,displayed_assessment:value},null,2));
  await record(id,'Exact '+ordinal+'-run assessment is readable','Click Open assessment and scroll to the opened assessment','The exact source assessment and mandatory human-review hold remain visible','The recorded '+ordinal+' run assessment shows 17 digital passes and one required human-review hold; no release or human acceptance is claimed.');
 }
 expect(posts.filter(r=>/\/authoring-jobs$|\/runs$|\/actions\/|\/decision$/.test(r.path))).toEqual([]);
 expect(diagnostics).toEqual({console:[],pageErrors:[],failedResponses:[]});
 writeFileSync(path.join(root,'diagnostics.json'),JSON.stringify({diagnostics,posts,new_execution_or_review:0},null,2));
 status.overall='pass';publish();
} catch(error) {
 status.overall='blocked';status.steps.push({id:'STOP',state:'blocked',label:'First stopping point',summary:clean(error.message),purpose:'Retain unexpected assessment display',action:'Stop at first error',controls:[],expected:'Exact source assessment remains readable',actual:clean(error.message),...await capture('STOP')});publish();
 appendFileSync(path.join(root,'progress.md'),'\nSTOPPED: '+clean(error.stack)+'\n');
 writeFileSync(path.join(root,'diagnostics.json'),JSON.stringify({diagnostics,posts},null,2));
 process.exitCode=1;
} finally {await context.tracing.stop({path:path.join(privateRoot,'assessment-126-trace.zip')});await browser.close();console.log(JSON.stringify({overall:status.overall,steps:status.steps.length,report:root}));}
