import { chromium } from '@playwright/test';
import { mkdirSync, readFileSync, writeFileSync, appendFileSync } from 'node:fs';
import path from 'node:path';

const artifactRoot = path.resolve(process.argv[2]);
const privateContext = JSON.parse(readFileSync(process.argv[3], 'utf8'));
const workspace = JSON.parse(readFileSync(process.argv[4], 'utf8'))[0];
const receipt=JSON.parse(readFileSync(process.argv[6] || '.local-run/process-interfaces-083/instruction-portability/interaction-proofs/first-question-run-01.json','utf8')).body;
const record=JSON.parse(readFileSync(process.argv[5] || '.local-run/process-interfaces-083/instruction-portability/interaction-proofs/workflow-records.json','utf8')).find(value=>value.path===receipt.input_checkpoint.workflow_id);
if(!record || receipt.status!=='waiting_human')throw Error('The walkthrough requires an exact saved waiting-input receipt.');
workspace.url=record.url;
for (const dir of ['playwright', 'screenshots/raw', 'screenshots/annotated', 'trace']) mkdirSync(path.join(artifactRoot, dir), {recursive:true});
writeFileSync(path.join(artifactRoot, 'playwright/capture.mjs'), readFileSync(import.meta.filename));
const status = {title:'Portable workflow instructions — normal workspace entry', summary:'In progress; no workflow execution or review answer is submitted.', overall:'pending', updated:new Date().toISOString(), manualSteps:[], steps:[]};
const diagnostics=[];
writeFileSync(path.join(artifactRoot,'progress.md'),'# Portable workflow instructions walkthrough\n\nStarted '+status.updated+' UTC. Fresh isolated workspace. Existing runs remain untouched.\n');
const esc=value=>String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
function report(){
  status.updated=new Date().toISOString();
  writeFileSync(path.join(artifactRoot,'status.json'),JSON.stringify(status,null,2));
  writeFileSync(path.join(artifactRoot,'report.html'),'<!doctype html><meta charset="utf-8"><title>Wright instruction walkthrough</title><style>body{font:16px system-ui;max-width:1100px;margin:30px auto;background:#101624;color:#eee}article{padding:18px;border:1px solid #556;margin:12px 0}.pass{border-color:#5c9}.blocked{border-color:#e65}img{max-width:95%}a{color:#6de}</style><h1>'+esc(status.title)+'</h1><p>'+esc(status.summary)+'</p><h2>Manual repeat</h2><ol>'+status.manualSteps.map(s=>'<li>'+esc(s.instruction)+'</li>').join('')+'</ol>'+status.steps.map(s=>'<article class="'+s.state+'"><h2>'+esc(s.label+' — '+s.state)+'</h2><p>Purpose: '+esc(s.purpose)+'</p><p>Action: '+esc(s.action)+'</p><p>Expected: '+esc(s.expected)+'</p><p>Observed: '+esc(s.actual)+'</p>'+[s.raw,s.annotated].filter(Boolean).map(p=>'<a href="'+p+'" target="_blank"><img src="'+p+'"></a>').join('')+'</article>').join(''));
}
report();
let browser;
try { browser=await chromium.launch({headless:true}); }
catch(error) {
  status.overall='blocked';status.summary='The local browser could not start; no workspace action was performed.';
  status.steps.push({id:'00-browser',state:'blocked',label:'Start installed test browser',summary:status.summary,purpose:'Open an isolated browser for the approved walkthrough.',action:'Start headless Chromium.',controls:[],expected:'Browser starts.',actual:String(error.message||error).slice(0,3000)});
  appendFileSync(path.join(artifactRoot,'progress.md'),'\n## '+new Date().toISOString()+' UTC — BLOCKED browser launch\nNo navigation or data changes occurred. All workspace checks remain unreached.\n'+String(error.message||error)+'\n');report();process.exitCode=2;
  throw error;
}
const context=await browser.newContext({viewport:{width:1159,height:764}});
const authentication=await context.request.post('http://127.0.0.1:5248/api/auth/session',{data:{token:privateContext.api_token}});
if(authentication.status()!==204)throw Error('Local browser session could not be established: HTTP '+authentication.status());
await context.tracing.start({screenshots:true,snapshots:true});
const page=await context.newPage();
page.on('pageerror',error=>diagnostics.push({kind:'pageerror',message:error.message}));
page.on('console',message=>{if(message.type()==='error')diagnostics.push({kind:'console',message:message.text().slice(0,1000)});});
page.on('response',response=>{if(response.status()>=400)diagnostics.push({kind:'http',status:response.status(),url:response.url()});});
async function capture(id){
  const raw='screenshots/raw/'+id+'.png',annotated='screenshots/annotated/'+id+'.png';
  await page.screenshot({path:path.join(artifactRoot,raw)});
  await page.evaluate(()=>{
    const overlay=document.createElement('aside');overlay.id='wright-walkthrough-markers';overlay.style.cssText='position:fixed;bottom:8px;right:8px;z-index:2147483647;padding:10px;max-width:550px;background:#fff;color:#111;font:12px sans-serif';
    const selectors=['[data-testid="activity-bar-workflows-btn"]','[data-testid="workflow-recovery-instructions"]','[data-testid="workflow-recovery-modal-close"]','[data-testid="workflow-recovery-save"]','[data-testid="workflow-recovery-source-tab"]'];
    const labels=[];
    selectors.forEach((selector,index)=>{const element=document.querySelector(selector);if(!element)return;const box=element.getBoundingClientRect();if(!box.width||box.top<0||box.top>innerHeight)return;labels.push((index+1)+' '+(element.getAttribute('aria-label')||element.textContent?.trim()||selector));const marker=document.createElement('span');marker.textContent=String(index+1);marker.style.cssText='position:fixed;z-index:2147483647;background:#158be5;color:white;border:2px solid white;border-radius:20px;padding:3px;left:'+box.right+'px;top:'+box.top+'px';overlay.append(marker);});
    const legend=document.createElement('p');legend.textContent=labels.join(' · ');overlay.append(legend);document.body.append(overlay);
  });
  await page.screenshot({path:path.join(artifactRoot,annotated)});
  await page.evaluate(()=>document.getElementById('wright-walkthrough-markers')?.remove());
  return {raw,annotated};
}
async function step(id,label,action,expected,operation){
  const record={id,state:'pending',label,summary:label,purpose:expected,action,controls:[],expected,actual:'Not reached'};
  status.steps.push(record);status.manualSteps.push({label,instruction:action});report();
  const diagnosticsStart=diagnostics.length;
  try{
    if(id!=='01-entry')Object.assign(record,await capture(id+'-before'));
    await operation();
    Object.assign(record,await capture(id+'-after'));
    record.controls=await page.locator('button:visible,input:visible,select:visible,textarea:visible').evaluateAll(elements=>elements.map(element=>({role:element.tagName.toLowerCase(),name:element.getAttribute('aria-label')||element.getAttribute('title')||element.textContent?.trim().slice(0,120)||''})));
    record.state='pass';record.actual='Expected state verified.';
  }catch(error){
    record.state='blocked';record.actual=String(error.message||error).slice(0,3000);Object.assign(record,await capture(id+'-stopped'));status.overall='blocked';status.summary='Stopped at '+label+'. Failed evidence retained; repair is authorized by the saved goal.';throw error;
  }finally{
    appendFileSync(path.join(artifactRoot,'progress.md'),'\n## '+new Date().toISOString()+' UTC — '+id+' '+label+'\nURL: '+page.url()+'\nAction: '+action+'\nExpected: '+expected+'\nActual: '+record.actual+'\nDiagnostics: '+JSON.stringify(diagnostics.slice(diagnosticsStart))+'\nRaw: '+record.raw+'\nAnnotated: '+record.annotated+'\nStatus: '+(record.state==='pass'?'PASS':'STOPPED')+'\n');report();
  }
}
try{
  await step('01-entry','Open saved workflow','Open '+workspace.url,'The saved workflow loads through the ordinary workspace route.',async()=>{await page.goto(workspace.url);await page.getByRole('heading',{name:receipt.workflow_title,exact:true}).waitFor({timeout:30000});});
  await step('02-wait','Observe the declared wait','Read the Waiting for your input banner.','The existing waiting run is visible; it is not reported as failure.',async()=>{await page.getByTestId('workflow-run-input-wait').waitFor({timeout:30000});await page.getByTestId('workflow-run-answer-input').waitFor();});
  await step('03-open','Open the same run working view','Click Answer in working view.','A Wright workspace tab opens bound to the exact existing run.',async()=>{await page.getByTestId('workflow-run-answer-input').click();await page.getByRole('button',{name:'Submit response',exact:true}).waitFor({timeout:30000});if(new URL(page.url()).searchParams.get('processRun')!==receipt.run_id)throw Error('Working view has a different run identity');});
  await step('04-reload','Reopen pending input','Reload the working view.','The same pending input and run remain without executing another segment.',async()=>{await page.reload();await page.getByRole('button',{name:'Submit response',exact:true}).waitFor({timeout:30000});if(new URL(page.url()).searchParams.get('processRun')!==receipt.run_id)throw Error('Reload changed run identity');});
  status.overall='pass';status.summary='The declared input is visible in both views and survives a browser reload on the same run. This pass submits no answer and grants no engineering approval.';report();
}catch(error){process.exitCode=2;console.log(JSON.stringify({status:'stopped',reason:String(error.message||error).slice(0,800),report:path.join(artifactRoot,'report.html')}));}
finally{writeFileSync(path.join(artifactRoot,'playwright/diagnostics.json'),JSON.stringify(diagnostics,null,2));await context.tracing.stop({path:path.join(artifactRoot,'trace/trace.zip')});await browser.close();report();}
