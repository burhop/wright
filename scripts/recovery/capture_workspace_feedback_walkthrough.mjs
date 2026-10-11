import { chromium } from '@playwright/test';
import { mkdirSync, readFileSync, writeFileSync, appendFileSync } from 'node:fs';
import path from 'node:path';

const root = path.resolve(process.argv[2]);
const mode = process.argv[3] || 'baseline';
const config = JSON.parse(readFileSync(process.argv[4] || process.env.WRIGHT_WORKSPACE_TEST_CONTEXT || (()=>{throw Error('Supply an existing local browser context as the fourth argument.');})()));
for (const dir of ['playwright', 'screenshots/raw', 'screenshots/annotated', 'trace']) mkdirSync(path.join(root, dir), {recursive:true});
writeFileSync(path.join(root,'playwright/capture.mjs'),readFileSync(import.meta.filename));
const status = {title:'Workspace feedback: '+mode,summary:'Normal workspace verification',overall:'pending',updated:new Date().toISOString(),manualSteps:[],steps:[]};
writeFileSync(path.join(root,'progress.md'),'# Workspace feedback\n\nStarted '+status.updated+' UTC. Existing engineering reviews remain held.\n');
const diagnostics=[];
let completedRun=null;
let executionRequests=0;
const browser=await chromium.launch({headless:true});
const context=await browser.newContext({viewport:{width:1159,height:764}});
await context.addCookies([{name:'wright_session',value:config.browser_cookie,url:'http://127.0.0.1:5246/api',httpOnly:true,sameSite:'Strict'}]);
await context.tracing.start({screenshots:true,snapshots:true});
const page=await context.newPage();
page.on('request',r=>{if(r.method()==='POST' && r.url().includes('/workflow-sources/run'))executionRequests++;});
page.on('pageerror',e=>diagnostics.push({kind:'pageerror',message:e.message}));
page.on('console',m=>{if(m.type()==='error')diagnostics.push({kind:'console',message:m.text().slice(0,1000)});});
page.on('response',r=>{if(r.status()>=400)diagnostics.push({kind:'http',status:r.status(),url:r.url()});});
function report(){
  status.updated=new Date().toISOString();
  writeFileSync(path.join(root,'status.json'),JSON.stringify(status,null,2));
  const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
  writeFileSync(path.join(root,'report.html'),'<!doctype html><meta charset="utf-8"><title>Wright workspace verification</title><style>body{font:16px system-ui;max-width:1000px;margin:30px auto;background:#101624;color:#eee}article{padding:18px;border:1px solid #556;margin:12px 0}.pass{border-color:#5c9}.blocked{border-color:#e65}img{max-width:95%}</style><h1>'+esc(status.title)+'</h1><p>'+esc(status.summary)+'</p><h2>Manual repeat</h2><ol>'+status.manualSteps.map(x=>'<li>'+esc(x.instruction)+'</li>').join('')+'</ol>'+status.steps.map(s=>'<article class="'+s.state+'"><h2>'+esc(s.id+' '+s.label+' — '+s.state)+'</h2><p>Expected: '+esc(s.expected)+'</p><p>Observed: '+esc(s.actual)+'</p>'+[s.raw,s.annotated].filter(Boolean).map(p=>'<a href="'+p+'" target="_blank"><img src="'+p+'"></a>').join('')+'</article>').join('')+'<dialog id=fullimage style="width:95vw;max-width:none;background:#101624;color:white"><button onclick="this.closest(\'dialog\').close()">Close</button><img style="max-width:none;width:auto;max-height:90vh"></dialog><script>document.querySelectorAll(\'article a\').forEach(a=>a.onclick=e=>{e.preventDefault();let d=document.querySelector(\'dialog\');d.querySelector(\'img\').src=a.getAttribute(\'href\');d.showModal()})</script>');
}
async function capture(id){
  const raw='screenshots/raw/'+id+'.png',annotated='screenshots/annotated/'+id+'.png';
  await page.screenshot({path:path.join(root,raw)});
  await page.evaluate(()=>{const el=document.createElement('aside');el.id='feedback-markers';el.textContent='1 Workflows · 2 MCP Tools · 3 Git · 4 Workspace Settings';el.style.cssText='position:fixed;bottom:8px;right:8px;z-index:2147483647;padding:10px;background:#fff;color:#111;font:14px sans-serif';document.body.append(el);['workflows','mcp','git','settings'].forEach((name,i)=>{const target=document.querySelector('[data-testid="activity-bar-'+name+'-btn"]');if(!target)return;const r=target.getBoundingClientRect();const m=document.createElement('div');m.textContent=String(i+1);m.style.cssText='position:fixed;z-index:2147483647;background:#158be5;color:white;border:2px solid white;border-radius:20px;padding:3px;left:'+r.right+'px;top:'+r.top+'px';el.append(m);});});
  if(mode === 'image-handoff') await page.evaluate(() => {
    const legend=document.getElementById('feedback-markers'); legend.replaceChildren();
    legend.style.maxWidth='420px'; legend.style.fontSize='11px';
    const controls=[...document.querySelectorAll('[data-testid^="workflow-recovery-handle-port."], [data-testid="workflow-recovery-cad-add-image"], [data-testid="workflow-recovery-response-format"], [data-testid="workflow-recovery-reference-image"]')]
      .filter(element=>{const r=element.getBoundingClientRect();return r.width && r.height && r.top>0 && r.bottom<innerHeight && r.left>0 && r.right<innerWidth;});
    const names=[];
    controls.forEach((target,i)=>{const r=target.getBoundingClientRect();const name=target.closest('[title]')?.getAttribute('title') || target.closest('label')?.firstChild?.textContent?.trim() || target.textContent?.trim();names.push((i+1)+' '+name);const marker=document.createElement('div');marker.textContent=String(i+1);marker.style.cssText='position:fixed;z-index:2147483647;background:#158be5;color:white;border:2px solid white;border-radius:20px;padding:3px;left:'+r.right+'px;top:'+r.top+'px';legend.append(marker);});
    const text=document.createElement('div');text.textContent=names.join(' · ');legend.append(text);
  });
  await page.screenshot({path:path.join(root,annotated)});
  await page.evaluate(()=>document.getElementById('feedback-markers')?.remove());
  return {raw,annotated};
}
async function step(id,label,instruction,expected,action,check){
  status.manualSteps.push({label,instruction});
  if (page.url() !== 'about:blank') await capture(id+'-before');
  let actual='Verified through the served workspace.',state='pass';
  try{await action();await check();}catch(e){actual=e.message;state='blocked';}
  const shots=await capture(id);
  status.steps.push({id,state,label,summary:actual,purpose:label,action:instruction,controls:instruction,expected,actual,...shots});
  appendFileSync(path.join(root,'progress.md'),'\n## '+new Date().toISOString()+' UTC '+id+' '+state+'\nURL: '+page.url()+'\nAction/control: '+instruction+'\nExpected: '+expected+'\nActual: '+actual+'\nRaw: '+shots.raw+'\nAnnotated: '+shots.annotated+'\n');
  status.overall=state;status.summary=state==='blocked'?'Stopped at '+label:'Checks completed so far';report();
  if(state==='blocked')throw Error('Walkthrough stopped at '+id);
}
try{
  report();
  await step('S01','Ordinary workspace','Open the existing test workspace.','Workspace loads without retired Rivet tooling or a dedicated BREP launcher.',async()=>{await page.goto('http://127.0.0.1:5246/workspace/083-fresh-prompt-055');await page.locator('[data-testid="activity-bar-workflows-btn"]:visible').waitFor();await page.waitForTimeout(1800);},async()=>{if(await page.locator('[data-testid="activity-bar-brep-btn"]:visible').count())throw Error('Dedicated Start BREP launcher is still present.');if((await page.locator('body').innerText()).includes('Rivet Workflows'))throw Error('Retired Rivet workflow tool is still injected.');});
  await step('S02','Workspace tools','Click MCP Tools.','Configured installed MCP servers are listed without a loading error.',()=>page.locator('[data-testid="activity-bar-mcp-btn"]:visible').click(),async()=>{await page.getByText('Private repeated preparation proof-083-blender-prompt-055',{exact:true}).waitFor({timeout:10000});if((await page.locator('body').innerText()).includes('Workspace tools could not'))throw Error('Installed tool request failed.');});
  await step('S03','Workspace settings','Click Workspace Settings.','Settings load successfully.',()=>page.locator('[data-testid="activity-bar-settings-btn"]:visible').click(),async()=>{await page.getByText('Git Credentials',{exact:true}).waitFor();await page.waitForTimeout(600);if((await page.locator('body').innerText()).includes('Failed to load workspace settings'))throw Error('Settings request failed.');});
  await step('S04','Git controls','Click Git Version Control.','Status, history and available Git controls appear.',()=>page.locator('[data-testid="activity-bar-git-btn"]:visible').click(),async()=>{await page.locator('[data-testid="git-panel"]:visible').waitFor();if((await page.locator('body').innerText()).includes('Coming soon'))throw Error('Git is still disabled.');});
  await step('S05','New blank workflow','Click Workflows.','A new empty workflow opens, without mounting-bracket blocks.',()=>page.locator('[data-testid="activity-bar-workflows-btn"]:visible').click(),async()=>{await page.locator('[data-testid="page-workflow-recovery"]:visible').waitFor();await page.waitForTimeout(1200);if(await page.locator('.react-flow__node').count())throw Error('New workflow has unexpected existing blocks.');if((await page.locator('body').innerText()).includes('Mounting bracket development'))throw Error('Fixed example opened instead of a blank workflow.');});
  if(mode === 'image-handoff') {
    const installedResponse = await page.request.get('http://127.0.0.1:5246/api/mcp/servers');
    if (!installedResponse.ok()) throw Error('Configured server metadata could not be read.');
    const installed = await installedResponse.json();
    const solidEdge = (installed.servers ?? installed).find(server => server.name === 'Solid Edge (local)');
    if (!solidEdge) throw Error('Solid Edge is not configured in the test workspace.');
    const node = id => page.locator(`[data-testid="workflow-recovery-block-${id}"]:visible`);
    const socket = id => page.locator(`[data-testid="workflow-recovery-handle-${id}"]:visible`);
    async function draw(source, target) {
      await page.getByRole('button', {name:'Fit workflow to view',exact:true}).click();
      await page.waitForTimeout(350);
      const a=await socket(source).boundingBox(), b=await socket(target).boundingBox();
      if(!a || !b) throw Error('A socket needed for drawing is not visible.');
      await page.mouse.move(a.x+a.width/2,a.y+a.height/2);
      await page.mouse.down();
      await page.mouse.move(b.x+b.width/2,b.y+b.height/2,{steps:16});
      await page.mouse.up();
    }
    const prompt='Create a small spacer: 20 mm diameter, 5 mm thick, 6 mm through-hole.';
    await step('S06','Text input','Click Input, then Text input; enter '+prompt,'A reusable input provides the design instructions.',async()=>{
      await page.locator('[data-testid="workflow-recovery-create-group-input"]:visible').click();
      await page.locator('[data-testid="workflow-recovery-create-template-text-input"]:visible').click();
      await page.locator('[data-testid="workflow-recovery-input-text-block.text-input-1"]:visible').fill(prompt);
    },async()=>{if(await page.locator('.react-flow__node').count()!==1)throw Error('Expected one input block.');});
    await step('S07','Add the CAD task','Click MCP servers, then Solid Edge (local).','The new task immediately exposes Prompt and Reference image sockets.',async()=>{
      await page.locator('[data-testid="workflow-recovery-create-group-tool"]:visible').click();
      await page.locator(`[data-testid="workflow-recovery-create-server-${solidEdge.server_id}"]:visible`).click();
    },async()=>{await socket('port.mcp-task-1-prompt-in').waitFor();await socket('port.mcp-task-1-reference-image-in').waitFor();});
    await step('S08','Draw the prompt connection','Drag Text input’s Design text output to Solid Edge’s Prompt socket.','Drawing connects the instruction input without first using the Inspector selector.',()=>draw('port.text-input-1-text-out','port.mcp-task-1-prompt-in'),async()=>{
      await page.waitForFunction(()=>document.querySelectorAll('.react-flow__edge').length===1);
      if(await page.locator('[data-testid="workflow-recovery-prompt-source"]:visible').inputValue()!=='connection')throw Error('Drawing did not configure the prompt source.');
    });
    let imagePort;
    await step('S09','Declare a model screenshot','Select the Solid Edge task; in Exports, click Add model image.','The declared provider format is Image (JPEG), with a .jpg output address.',async()=>{
      await node('block.mcp-task-1').click();
      await page.locator('[data-testid="workflow-recovery-cad-add-image"]:visible').click();
    },async()=>{
      const format=page.locator('[data-testid="workflow-recovery-cad-export-format-0"]:visible');
      if(await format.inputValue()!=='screenshot_jpeg')throw Error('The provider’s JPEG format was not selected.');
      if(!/\.jpg$/.test(await page.locator('[data-testid="workflow-recovery-cad-export-path-0"]:visible').inputValue()))throw Error('Image export filename has the wrong extension.');
      imagePort=await node('block.mcp-task-1').locator('[data-testid*="-cad-export-"]').getAttribute('data-testid');
      imagePort=imagePort.replace('workflow-recovery-handle-','');
    });
    await step('S10','Final image result','Click AI prompt, add AI prompt, enter rendering instructions, then choose Response format: Image (PNG).','The final block declares an actual PNG file and asks for an image-capable MCP provider before running.',async()=>{
      await page.locator('[data-testid="workflow-recovery-create-group-document"]:visible').click();
      await page.locator('[data-testid="workflow-recovery-create-template-ai-prompt"]:visible').click();
      await page.locator('[data-testid="workflow-recovery-block-instructions-block.ai-prompt-1"]:visible').fill('Turn the reference CAD screenshot into a high quality realistic studio rendering. Preserve the part geometry, hole, proportions and viewing angle. Use brushed aluminium and a neutral background.');
      await page.locator('[data-testid="workflow-recovery-response-format"]:visible').selectOption('image-png');
    },async()=>{
      await page.getByText('Choose an MCP server with image editing or rendering tools before running.',{exact:true}).waitFor();
      if(await page.locator('[data-testid="workflow-recovery-image-output-path"]:visible').inputValue()!=='render.png')throw Error('Final image filename is missing.');
      if(await page.locator('[data-testid="workflow-recovery-save-response"]:visible').count())throw Error('A text response is still presented as the final deliverable.');
    });
    await step('S11','Draw the image handoff','Drag Solid Edge’s model-view image output to the AI step’s Reference image socket; select the AI step to inspect it.','The image is connected as reference material, while the written rendering prompt remains intact.',async()=>{await draw(imagePort,'port.ai-prompt-1-reference-image-in');await node('block.ai-prompt-1').click();},async()=>{
      await page.waitForFunction(()=>document.querySelectorAll('.react-flow__edge[data-id^="rel."]').length===2);
      if(await page.locator('[data-testid="workflow-recovery-reference-image"]:visible').inputValue()!==imagePort)throw Error('Image handoff was not reflected in the Inspector.');
      if(await page.locator('[data-testid="workflow-recovery-prompt-source"]:visible').inputValue()!=='inline')throw Error('The screenshot incorrectly replaced the task instructions.');
    });
    await step('S12','Undo and redo','Click Undo, then Redo.','The complete image connection can be removed and restored as one editor action.',async()=>{
      await page.locator('[data-testid="workflow-recovery-undo"]:visible').click();
      await page.waitForFunction(()=>document.querySelectorAll('.react-flow__edge[data-id^="rel."]').length===1);
      await page.locator('[data-testid="workflow-recovery-redo"]:visible').click();
    },async()=>{await page.waitForFunction(()=>document.querySelectorAll('.react-flow__edge[data-id^="rel."]').length===2);});
    await step('S13','Save and reopen','Click Save, reload, fit the workflow, and select the AI image step.','The screenshot-to-rendering handoff, provider requirements and exact PNG output binding survive reopening.',async()=>{
      await page.locator('[data-testid="workflow-recovery-save"]:visible').click();
      await page.waitForFunction(()=>[...document.querySelectorAll('[data-testid="workflow-recovery-save-status"]')].some(e=>e.textContent==='Saved'));
      const sourcePath=new URL(page.url()).searchParams.get('workflowPath');
      const response=await page.request.get('http://127.0.0.1:5246/api/workspace/workflow-sources?session_id=083-printed-prompt-session-055&path='+encodeURIComponent(sourcePath));
      if(!response.ok())throw Error('Saved source could not be read.');
      const stored=await response.json();writeFileSync(path.join(root,'trace/authored-image-workflow.json'),JSON.stringify(stored,null,2));
      if(!stored.source.includes('image_output') || !stored.source.includes('wright.run-path/1') || !stored.source.includes('screenshot_jpeg'))throw Error('Saved source lost the image contract.');
      await page.reload();await page.locator('[data-testid="page-workflow-recovery"]:visible').waitFor();
      await page.getByRole('button',{name:'Fit workflow to view',exact:true}).click();
      await node('block.ai-prompt-1').click();
    },async()=>{
      if(await page.locator('[data-testid="workflow-recovery-response-format"]:visible').inputValue()!=='image-png')throw Error('Reopened image result mode was lost.');
      if(await page.locator('[data-testid="workflow-recovery-reference-image"]:visible').inputValue()!==imagePort)throw Error('Reopened reference image connection was lost.');
      if(executionRequests)throw Error('Authoring unexpectedly started a workflow.');
    });
  }
  if(mode === 'image-handoff') {
    await step('S14','Resolve rendering readiness','Open Run readiness.','The exact image step is listed as unbound before any CAD or rendering execution.',async()=>{
      await page.locator('[data-testid="workflow-recovery-run-readiness-toggle"]:visible').click();
    },async()=>{
      await page.locator('[data-testid="workflow-recovery-readiness-task-block.ai-prompt-1"]:visible').waitFor();
      if(executionRequests)throw Error('Readiness inspection unexpectedly submitted execution.');
      writeFileSync(path.join(root,'trace/authoring-boundary.json'),JSON.stringify({execution_requests:executionRequests,scope:'Authoring and readiness only; image provider selection, live CAD export and photorealistic output remain unverified.'},null,2));
    });
  }
  if(mode !== 'baseline' && mode !== 'manual-authoring' && mode !== 'image-handoff' && mode !== 'native-image' && mode !== 'native-image-continuation') {
    const firstWorkflow = new URL(page.url()).searchParams.get('workflowPath');
    await step('S06','Separate workflow and reload','Click Workflows again, then reload the page.','A second unique empty workflow is retained; reload does not create another definition.',async()=>{
      await page.locator('[data-testid="activity-bar-workflows-btn"]:visible').click();
    },async()=>{
      await page.waitForFunction(first=>new URL(location.href).searchParams.get('workflowPath') !== first, firstWorkflow);
      const second = new URL(page.url()).searchParams.get('workflowPath');
      let writes=0;
      const count=r=>{if(r.method()==='POST' && r.url().includes('workflow-source'))writes++;};
      page.on('request',count);
      await page.reload(); await page.locator('[data-testid="page-workflow-recovery"]:visible').waitFor(); await page.waitForTimeout(1200);
      page.off('request',count);
      if(new URL(page.url()).searchParams.get('workflowPath') !== second || writes || await page.locator('.react-flow__node').count()) throw Error('Reload changed the workflow or created unexpected content.');
    });
    await step('S07','Open an existing workflow','Open Workflow files, click Open workflow, and choose printed-replacement-part-common-digital-083.workflow.wflow.','The selected saved engineering definition opens without being replaced by a sample.',async()=>{
      await page.locator('[data-testid="workflow-file-menu"]:visible').click(); await page.locator('[data-testid="workflow-file-open"]:visible').click();
      await page.locator('[data-testid="workflow-file-choice-workflows/printed-replacement-part-common-digital-083.workflow.wflow"]:visible').click();
    },async()=>{
      await page.getByRole('heading',{name:'Prepare and inspect a focus-wheel mesh',exact:true}).waitFor();
      if((await page.locator('body').innerText()).includes('Mounting bracket development'))throw Error('The wrong definition was opened.');
    });
    await step('S08','Model configuration','Open Agent Console and inspect its model selector.','The configured model list loads and the LLM connection responds.',async()=>{
      const opener=page.getByTitle('Open Agent Console'); if(await opener.count()) await opener.click();
    },async()=>{
      await page.getByText('Hermes models unavailable',{exact:false}).waitFor({state:'hidden',timeout:15000});
      const response=await page.request.get('http://127.0.0.1:5246/api/inference/health');
      if(!response.ok() || (await response.json()).state !== 'connected')throw Error('LLM connection is unavailable.');
      const close=page.getByTitle('Collapse Agent Console'); if(await close.count())await close.click();
    });
    if(mode === 'live-run') {
      await step('S09','Actual digital engineering run','Click Run and wait for the engineering outputs.','A fresh run completes construction and repair through the existing Blender MCP.',async()=>{
        const historyUrl='http://127.0.0.1:5246/api/workspace/workflow-sources/runs?session_id=083-printed-prompt-session-055&path=workflows%2Fprinted-replacement-part-common-digital-083.workflow.wflow&latest_only=true';
        const beforeResponse=await page.request.get(historyUrl);
        if(!beforeResponse.ok())throw Error('Could not inspect the prior run before submission.');
        const priorRun=(await beforeResponse.json()).runs[0]?.run_id;
        const responsePending=page.waitForResponse(r=>r.request().method()==='POST' && r.url().includes('/workflow-sources/run'));
        await page.locator('[data-testid="workflow-recovery-run-start"]:visible').click();
        const response=await responsePending;
        if(!response.ok())throw Error('Run submission failed: '+response.status());
        const deadline=Date.now()+180000;
        let freshRun;
        while(Date.now()<deadline){
          const historyResponse=await page.request.get(historyUrl);
          if(!historyResponse.ok())throw Error('Could not inspect the submitted run.');
          const latest=(await historyResponse.json()).runs[0];
          if(latest?.run_id && latest.run_id !== priorRun){
            if(latest.status==='completed'){freshRun=latest;break;}
            if(['failed','cancelled','blocked'].includes(latest.status))throw Error('Fresh run '+latest.run_id+' ended with '+latest.status);
          }
          await page.waitForTimeout(500);
        }
        if(!freshRun)throw Error('The normal service did not record a fresh completed run.');
        completedRun=freshRun;
        writeFileSync(path.join(root,'trace/accepted-run.json'),JSON.stringify({prior_run_id:priorRun,run_id:freshRun.run_id,run_log_path:freshRun.path,status:freshRun.status,submission_status:response.status(),identity_evidence:'A new durable run following the observed Run submission, also checked against visible output links.'},null,2));
      },async()=>{
        const summary=page.locator('[data-testid="workflow-native-run-summary"]:visible');
        await summary.waitFor({timeout:20000});
        await page.waitForFunction(()=>{const e=document.querySelector('[data-testid="workflow-native-run-summary"]');return e && /Workflow completed|Workflow failed|Run blocked|Workflow cancelled/.test(e.textContent)},undefined,{timeout:180000});
        const actual=await summary.innerText();
        if(!actual.includes('Workflow completed'))throw Error(actual);
        writeFileSync(path.join(root,'trace/completed-run-summary.txt'),actual);
        if(!await page.locator('[data-testid="workflow-recovery-native-run-output-link"]:visible').count())throw Error('Completed status did not expose output evidence.');
        const outputSubjects=await page.locator('[data-testid="workflow-recovery-native-run-output-link"]:visible').evaluateAll(controls=>controls.map(control=>control.getAttribute('title') ?? control.getAttribute('href')));
        if(!outputSubjects.some(subject=>subject?.includes(completedRun.run_id)))throw Error('Visible output controls do not identify the fresh completed run.');
        writeFileSync(path.join(root,'trace/visible-output-subjects.json'),JSON.stringify(outputSubjects,null,2));
      });
    }
  }
  if(mode==='manual-authoring') {
    const prompt='Create a rectangular spacer 20 mm long, 10 mm wide and 5 mm thick. Save the native part.';
    const registryResponse=await page.request.get('http://127.0.0.1:5246/api/mcp/servers');
    if(!registryResponse.ok())throw Error('The configured registry is unavailable.');
    const solidEdge=(await registryResponse.json()).servers.find(s=>s.name==='Solid Edge (local)' && s.is_installed);
    if(!solidEdge)throw Error('The existing Solid Edge MCP is not configured in this authoring workspace.');
    await step('S06','Prompt input','Click Input, then Text input, and enter: '+prompt,'The prompt remains an editable input; the working view waits for saved edits.',async()=>{
      await page.locator('[data-testid="workflow-recovery-create-group-input"]:visible').click();
      await page.locator('[data-testid="workflow-recovery-create-template-text-input"]:visible').click();
      await page.locator('[data-testid="workflow-recovery-input-text-block.text-input-1"]:visible').fill(prompt);
    },async()=>{
      await page.waitForFunction(()=>document.querySelector('[data-testid="workflow-working-view-open"]')?.disabled === true);
      await page.getByText('Save your changes to open the working view.',{exact:true}).waitFor();
    });
    await step('S07','Actual MCP server choices','Click MCP servers.','Configured MCP servers include Solid Edge; internal Wright operations are absent and choosing later is explicit.',async()=>{
      await page.locator('[data-testid="workflow-recovery-create-group-tool"]:visible').click();
    },async()=>{
      await page.locator(`[data-testid="workflow-recovery-create-server-${solidEdge.server_id}"]:visible`).waitFor();
      await page.getByRole('button',{name:/MCP task · choose server later/}).waitFor();
      const labels=await page.locator('#recovery-create-options .recovery-create-template b').allTextContents();
      if(labels.includes('MCP server') || labels.some(label=>/wright-workspace-files|wright-process-validation/.test(label)))throw Error('Internal services or indistinguishable generic choices are still in the MCP palette.');
      writeFileSync(path.join(root,'trace/server-palette-labels.json'),JSON.stringify(labels,null,2));
    });
    await step('S08','Connect input to Solid Edge','Choose Solid Edge (local), set Prompt source to From another block, and choose Text input · Design text.','A Solid Edge task consumes the prompt input and declares its native CAD output.',async()=>{
      await page.locator(`[data-testid="workflow-recovery-create-server-${solidEdge.server_id}"]:visible`).click();
      await page.locator('[data-testid="workflow-recovery-prompt-source"]:visible').selectOption('connection');
      await page.locator('[data-testid="workflow-recovery-prompt-from"]:visible').selectOption({label:'Text input · Design text'});
    },async()=>{
      const select=page.locator('[data-testid="workflow-recovery-task-server"]:visible');
      await select.waitFor();
      if(await select.inputValue() !== solidEdge.server_id)throw Error('The task is not bound to the chosen MCP.');
      if(!await page.getByLabel('Work with a CAD model',{exact:true}).isChecked())throw Error('The advertised native CAD operations were not configured.');
      if(!await page.locator('.react-flow__edge').count())throw Error('The prompt-to-task connection is missing.');
    });
    await step('S09','Save authored source','Click Save.','The exact two-block definition, input prompt, server binding and connection are saved.',async()=>{
      await page.locator('[data-testid="workflow-recovery-save"]:visible').click();
    },async()=>{
      await page.waitForFunction(()=>[...document.querySelectorAll('[data-testid="workflow-recovery-save-status"]')].some(e=>e.textContent==='Saved'));
      const workflowPath=new URL(page.url()).searchParams.get('workflowPath');
      const response=await page.request.get('http://127.0.0.1:5246/api/workspace/workflow-sources?session_id=083-printed-prompt-session-055&path='+encodeURIComponent(workflowPath));
      if(!response.ok())throw Error('Saved source could not be read back.');
      const stored=await response.json();
      if(!stored.source.includes(prompt) || !stored.source.includes(solidEdge.server_id))throw Error('Saved source lost the prompt or MCP binding.');
      writeFileSync(path.join(root,'trace/authored-workflow.json'),JSON.stringify(stored,null,2));
      await page.waitForFunction(()=>document.querySelector('[data-testid="workflow-working-view-open"]')?.disabled === false);
    });
    await step('S10','Reload the authored workflow','Reload, click Fit workflow to view, then select the Solid Edge task.','The saved input, server selection and prompt connection survive reopening.',async()=>{
      await page.reload();
      await page.locator('[data-testid="page-workflow-recovery"]:visible').waitFor();
      await page.getByRole('button',{name:'Fit workflow to view',exact:true}).click();
      await page.locator('[data-testid="workflow-recovery-block-block.mcp-task-1"]:visible').click();
    },async()=>{
      const select=page.locator('[data-testid="workflow-recovery-task-server"]:visible');
      await select.waitFor();
      if(await select.inputValue() !== solidEdge.server_id)throw Error('Reopened task lost its server binding.');
      if(await page.locator('[data-testid="workflow-recovery-prompt-source"]:visible').inputValue() !== 'connection')throw Error('Reopened task lost its connected prompt.');
    });
    await step('S11','Open the same workflow working view','Click Open working view.','The same saved workflow opens in a clearly named Wright workspace tab without running it.',async()=>{
      await page.locator('[data-testid="workflow-working-view-open"]:visible').click();
    },async()=>{
      await page.locator('[data-testid="common-process-view"]:visible').waitFor({timeout:20000});
      if(executionRequests)throw Error('Authoring or opening a view unexpectedly started execution.');
      const tabNames=await page.getByRole('tab').allTextContents();
      if(!tabNames.some(name=>name.includes('Working view')))throw Error('The working tab is indistinguishable from the authoring tab.');
    });
    await step('S12','Choose an MCP server later','Click Workflows to create a separate blank workflow; click MCP servers, then MCP task · choose server later.','An unbound task can be authored; its selector lists Solid Edge and has no internal service choices.',async()=>{
      await page.locator('[data-testid="activity-bar-workflows-btn"]:visible').click();
      await page.locator('[data-testid="workflow-recovery-create-group-tool"]:visible').click();
      await page.locator('[data-testid="workflow-recovery-create-template-mcp-task"]:visible').click();
    },async()=>{
      const select=page.locator('[data-testid="workflow-recovery-task-server"]:visible');
      await select.getByRole('option',{name:'Solid Edge (local)',exact:true}).waitFor({state:'attached'});
      await page.waitForFunction(()=>{
        const element=[...document.querySelectorAll('[data-testid="workflow-recovery-task-server"]')].find(e=>e.offsetParent);
        return element && !element.disabled;
      });
      if(await select.inputValue() !== '')throw Error('An MCP server was chosen without the user selecting it.');
      const options=await select.locator('option').allTextContents();
      if(!options.includes('Choose server later') || options.includes('MCP server'))throw Error('The deferred selector still has indistinguishable choices.');
      writeFileSync(path.join(root,'trace/server-selector-labels.json'),JSON.stringify(options,null,2));
    });
  }
  if(mode==='native-image') {
    const socket=id=>page.locator(`[data-testid="workflow-recovery-handle-${id}"]:visible`);
    const node=id=>page.locator(`[data-testid="workflow-recovery-block-${id}"]:visible`);
    const instructions='Make a high quality photorealistic studio rendering of the washer in the reference image. Preserve its shape, central through-hole, proportions and viewing angle. Change its surface to polished brass with soft realistic lighting and a white background. Return only the final image.';
    let sourcePath, referencePath, run;
    await step('S06','Reference image','Click Input, choose Image, then Upload image and select the saved washer image.','The selected image appears in the Inspector.',async()=>{
      await page.locator('[data-testid="workflow-recovery-create-group-input"]:visible').click();
      await page.locator('[data-testid="workflow-recovery-create-template-image-input"]:visible').click();
      await page.locator('[data-testid="workflow-recovery-input-upload"]:visible').setInputFiles(path.resolve('.local-run/process-interfaces-083/user-testing-20261007/codex-native-image-probe.png'));
    },async()=>{
      await page.waitForFunction(()=>[...document.querySelectorAll('[data-testid="workflow-recovery-input-selected-path"]')].some(e=>e.textContent.endsWith('.png')));
      referencePath=await page.locator('[data-testid="workflow-recovery-input-selected-path"]:visible').innerText();
      await page.waitForFunction(()=>[...document.querySelectorAll('img[alt^="Selected image:"]')].some(e=>e.complete && e.naturalWidth>0));
    });
    await step('S07','Rendering prompt','Click AI prompt, choose AI prompt, enter the brass rendering instructions, and choose Image (PNG).','The configured AI connection will receive text and image; no MCP selection is needed.',async()=>{
      await page.locator('[data-testid="workflow-recovery-create-group-document"]:visible').click();
      await page.locator('[data-testid="workflow-recovery-create-template-ai-prompt"]:visible').click();
      await page.locator('[data-testid="workflow-recovery-block-instructions-block.ai-prompt-1"]:visible').fill(instructions);
      await page.locator('[data-testid="workflow-recovery-response-format"]:visible').selectOption('image-png');
    },async()=>{
      await page.getByText('Wright sends the prompt and reference images to your configured AI connection, then saves and displays the returned image.',{exact:true}).waitFor();
      if(await page.locator('[data-testid="workflow-recovery-task-server"]:visible').count())throw Error('The AI image block unexpectedly requires an MCP server.');
    });
    await step('S08','Draw image connection','Drag the Image output to the AI prompt Reference image input.','The reference image is bound separately from the rendering text.',async()=>{
      await page.getByRole('button',{name:'Fit workflow to view',exact:true}).click();await page.waitForTimeout(400);
      const a=await socket('port.image-input-1-images-out').boundingBox(),b=await socket('port.ai-prompt-1-reference-image-in').boundingBox();
      if(!a||!b)throw Error('Image handoff sockets are not visible.');
      await page.mouse.move(a.x+a.width/2,a.y+a.height/2);await page.mouse.down();await page.mouse.move(b.x+b.width/2,b.y+b.height/2,{steps:16});await page.mouse.up();
    },async()=>{
      await page.waitForFunction(()=>document.querySelectorAll('.react-flow__edge[data-id^="rel."]').length===1);
      if(await page.locator('[data-testid="workflow-recovery-reference-image"]:visible').inputValue()!=='port.image-input-1-images-out')throw Error('The image connection was not accepted.');
      if(await page.locator('[data-testid="workflow-recovery-block-instructions-block.ai-prompt-1"]:visible').inputValue()!==instructions)throw Error('Image handoff changed the rendering instructions.');
    });
    await step('S09','Save and reopen','Click Save, reload the page, and select the AI prompt block.','The image input, prompt, PNG output and AI binding remain saved.',async()=>{
      await page.locator('[data-testid="workflow-recovery-save"]:visible').click();
      await page.waitForFunction(()=>[...document.querySelectorAll('[data-testid="workflow-recovery-save-status"]')].some(e=>e.textContent==='Saved'));
      sourcePath=new URL(page.url()).searchParams.get('workflowPath');
      const response=await page.request.get('http://127.0.0.1:5246/api/workspace/workflow-sources?session_id=083-printed-prompt-session-055&path='+encodeURIComponent(sourcePath));
      const stored=await response.json();if(!response.ok()||!stored.source.includes('image_output'))throw Error('The saved image declaration is missing.');
      writeFileSync(path.join(root,'trace/authored-image-workflow.json'),JSON.stringify(stored,null,2));
      await page.reload();await page.locator('[data-testid="page-workflow-recovery"]:visible').waitFor();await node('block.ai-prompt-1').click();
    },async()=>{
      if(await page.locator('[data-testid="workflow-recovery-response-format"]:visible').inputValue()!=='image-png')throw Error('The saved PNG output was lost.');
      if(await page.locator('[data-testid="workflow-recovery-reference-image"]:visible').inputValue()!=='port.image-input-1-images-out')throw Error('The saved reference image was lost.');
      if(executionRequests)throw Error('Saving unexpectedly started execution.');
    });
    await step('S10','Generate image','Click Run; wait for the configured Codex model to return the final image.','The same Wright workflow run completes with one real PNG, without MCP tools or extra questions.',async()=>{
      const pending=page.waitForResponse(r=>r.request().method()==='POST' && r.url().includes('/workflow-sources/run'),{timeout:180000});
      await page.locator('[data-testid="workflow-recovery-run-start"]:visible').click();
      const response=await pending;
      const data=response.headers()['content-type']?.includes('ndjson')
        ? (await response.text()).trim().split('\n').map(line=>JSON.parse(line)).at(-1)?.result
        : await response.json();
      if(!response.ok())throw Error('Workflow request failed: '+JSON.stringify(data));
      run=data.run??data;
      const deadline=Date.now()+180000;
      while(Date.now()<deadline){
        const state=await page.request.get('http://127.0.0.1:5246/api/workspace/workflow-sources/runs?session_id=083-printed-prompt-session-055&path='+encodeURIComponent(sourcePath)+'&latest_only=true');
        const items=await state.json();run=items.runs?.[0]??run;
        if(['completed','failed'].includes(run.status))break;
        await page.waitForTimeout(1000);
      }
      writeFileSync(path.join(root,'trace/generated-image-run.json'),JSON.stringify(run,null,2));
      if(run.status!=='completed')throw Error('Image workflow did not complete: '+JSON.stringify(run.failure??run));
    },async()=>{
      const image=(run.result?.results??run.results)?.find(r=>r.kind==='image');
      if(!image?.representations?.[0]?.location)throw Error('No image result was returned.');
      const representation=image.representations[0];
      const response=await page.request.get('http://127.0.0.1:5246/api/workspace/files/content?session_id=083-printed-prompt-session-055&path='+encodeURIComponent(representation.location));
      if(!response.ok())throw Error('Generated image cannot be read.');
      const content=await response.body();if(content.subarray(0,8).toString('hex')!=='89504e470d0a1a0a')throw Error('The final result is not actual PNG bytes.');
      writeFileSync(path.join(root,'trace/generated-render.png'),content);
      writeFileSync(path.join(root,'trace/result-link.json'),JSON.stringify({url:page.url(),run_id:run.run_id,reference_path:referencePath,image_result:image,scope:'Uploaded reference image and rendering text through normal workspace authoring and the durable Wright runtime; no live CAD operation.'},null,2));
      if(executionRequests!==1)throw Error('Expected exactly one workflow execution.');
    });
    await step('S11','Reload without replay','Reload the workflow and open Run details.','The completed image run is restored without generating another image.',async()=>{
      await page.reload();await page.locator('[data-testid="page-workflow-recovery"]:visible').waitFor();
      const details=page.locator('[data-testid="workflow-recovery-run-details-toggle"]:visible');await details.waitFor();if(await details.getAttribute('aria-expanded')!=='true')await details.click();
    },async()=>{
      await page.waitForFunction(()=>[...document.querySelectorAll('[data-testid="workflow-native-run-summary"]')].some(e=>e.textContent.includes('Workflow completed')),undefined,{timeout:20000});
      if(executionRequests!==1)throw Error('Reload repeated an image execution.');
    });
  }
  if(mode==='native-image-continuation') {
    const earlier=JSON.parse(readFileSync(path.resolve('artifacts/ui-walkthrough/workspace-feedback/20261007-native-image-001/trace/authored-image-workflow.json')));
    const sourcePath=earlier.path;
    let run, image, imagePath;
    await step('S06','Open saved image workflow','Open Workflow files, click Open workflow, and choose '+sourcePath.split('/').at(-1)+'.','The workflow authored in the first capture opens with its already completed image run.',async()=>{
      await page.locator('[data-testid="workflow-file-menu"]:visible').click();await page.locator('[data-testid="workflow-file-open"]:visible').click();
      await page.locator(`[data-testid="workflow-file-choice-${sourcePath}"]:visible`).click();
    },async()=>{
      await page.waitForFunction(path=>new URL(location.href).searchParams.get('workflowPath')===path,sourcePath);
      await page.waitForFunction(()=>document.querySelectorAll('.react-flow__node[data-id^="block."]').length===2);
    });
    await step('S07','Restore the completed run','Open Run details.','The original run is completed and contains a real PNG with an exact digest.',async()=>{
      const details=page.locator('[data-testid="workflow-recovery-run-details-toggle"]:visible');await details.waitFor();if(await details.getAttribute('aria-expanded')!=='true')await details.click();
    },async()=>{
      await page.waitForFunction(()=>[...document.querySelectorAll('[data-testid="workflow-native-run-summary"]')].some(e=>e.textContent.includes('Workflow completed')),undefined,{timeout:20000});
      const response=await page.request.get('http://127.0.0.1:5246/api/workspace/workflow-sources/runs?session_id=083-printed-prompt-session-055&path='+encodeURIComponent(sourcePath)+'&latest_only=true');
      const data=await response.json();run=data.runs?.[0];if(!response.ok()||run?.status!=='completed')throw Error('The previously submitted image run is not complete.');
      image=run.results?.find(result=>result.kind==='image');imagePath=image?.representations?.[0]?.location;
      if(!imagePath)throw Error('No image deliverable is recorded.');
      const contentResponse=await page.request.get('http://127.0.0.1:5246/api/workspace/files/content?session_id=083-printed-prompt-session-055&path='+encodeURIComponent(imagePath));
      if(!contentResponse.ok())throw Error('The recorded image file cannot be read.');
      const content=await contentResponse.body();if(content.subarray(0,8).toString('hex')!=='89504e470d0a1a0a')throw Error('The final deliverable is not a PNG.');
      writeFileSync(path.join(root,'trace/generated-render.png'),content);
      const logResponse=await page.request.get('http://127.0.0.1:5246/api/workspace/files/content?session_id=083-printed-prompt-session-055&path='+encodeURIComponent(run.path));
      if(!logResponse.ok())throw Error('The original run evidence is unavailable.');
      writeFileSync(path.join(root,'trace/generated-image-run.json'),await logResponse.body());
      writeFileSync(path.join(root,'trace/result-link.json'),JSON.stringify({url:page.url(),run_id:run.run_id,image_result:image,scope:'One real image-and-text generation through the durable Wright workflow runtime. First capture submitted it; this continuation observes without replay. No live CAD operation.'},null,2));
    });
    await step('S08','View final image','Click the render.png output in Run details.','The final brass rendering opens in Wright’s shared image viewer tab.',async()=>{
      await page.locator('[data-testid="workflow-recovery-native-run-output-link"]:visible').filter({hasText:'render.png'}).first().click();
    },async()=>{
      await page.waitForFunction(()=>[...document.querySelectorAll('img')].some(image=>image.complete && image.naturalWidth>=512 && image.src.includes('outputs')),{},{timeout:20000});
    });
    await step('S09','Reload without another generation','Reload; open the same saved workflow and Run details.','The exact completed run and image survive, with zero new execution requests.',async()=>{
      await page.reload();await page.locator('[data-testid="activity-bar-workflows-btn"]:visible').waitFor();
      await page.goto('http://127.0.0.1:5246/workspace/083-fresh-prompt-055?workflow=canonical&workflowPath='+encodeURIComponent(sourcePath));
      await page.locator('[data-testid="page-workflow-recovery"]:visible').waitFor();
      const details=page.locator('[data-testid="workflow-recovery-run-details-toggle"]:visible');await details.waitFor();if(await details.getAttribute('aria-expanded')!=='true')await details.click();
    },async()=>{
      await page.waitForFunction(()=>[...document.querySelectorAll('[data-testid="workflow-native-run-summary"]')].some(e=>e.textContent.includes('Workflow completed')),undefined,{timeout:20000});
      const response=await page.request.get('http://127.0.0.1:5246/api/workspace/workflow-sources/runs?session_id=083-printed-prompt-session-055&path='+encodeURIComponent(sourcePath)+'&latest_only=true');
      const current=await response.json();if(current.runs?.[0]?.run_id!==run.run_id || executionRequests)throw Error('Reload changed the run or submitted another generation.');
      writeFileSync(path.join(root,'trace/restored-run.json'),JSON.stringify(current,null,2));
    });
  }
  if(mode==='live-run') {
    await step('S10','Reload completed run','Reload the selected workflow and open Run details.','The latest completed run and its results are restored without another execution.',async()=>{
      await page.reload();
      await page.locator('[data-testid="page-workflow-recovery"]:visible').waitFor();
      const details=page.locator('[data-testid="workflow-recovery-run-details-toggle"]:visible');
      await details.waitFor({timeout:20000});
      if(await details.getAttribute('aria-expanded') !== 'true')await details.click();
    },async()=>{
      const summary=page.locator('[data-testid="workflow-native-run-summary"]:visible');
      await summary.waitFor({timeout:20000});
      await page.waitForFunction(()=>[...document.querySelectorAll('[data-testid="workflow-native-run-summary"]')].some(e=>e.textContent.includes('Workflow completed')),undefined,{timeout:20000});
      const response=await page.request.get('http://127.0.0.1:5246/api/workspace/workflow-sources/runs?session_id=083-printed-prompt-session-055&path=workflows%2Fprinted-replacement-part-common-digital-083.workflow.wflow&latest_only=true');
      const data=await response.json();
      if(!response.ok() || data.runs[0]?.run_id !== completedRun.run_id || data.runs[0]?.status !== 'completed')throw Error('Reload did not restore the exact latest run.');
      writeFileSync(path.join(root,'trace/restored-run.json'),JSON.stringify(data,null,2));
    });
  }
  status.summary='All requested served workspace checks passed for '+mode+'.';report();
}catch(e){appendFileSync(path.join(root,'progress.md'),'\nStopped: '+e.message+'\n');report();process.exitCode=1;}
finally{writeFileSync(path.join(root,'trace/diagnostics.json'),JSON.stringify(diagnostics,null,2));await context.tracing.stop({path:path.join(root,'trace/browser.zip')});await browser.close();console.log(JSON.stringify({root,overall:status.overall,steps:status.steps.map(s=>({id:s.id,state:s.state,actual:s.actual}))}));}
