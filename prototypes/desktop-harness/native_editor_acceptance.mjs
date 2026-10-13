// Simulated MCP App host with real isolated Wright source storage. Not Windows acceptance.
import {createServer} from 'node:http';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {chromium,expect} from '@playwright/test';
const state=resolve(process.argv[2]);
const checkpoint=process.argv.includes('--checkpoint');
const completed=process.argv.includes('--completed');
if(completed&&!checkpoint)throw Error('Completed readback requires the exact checkpoint fixture');
const submitTestChoice=process.argv.includes('--submit-test-choice');
if(submitTestChoice&&!checkpoint)throw Error('Test choice requires the exact checkpoint fixture');
const testChoice=submitTestChoice?JSON.parse(readFileSync(resolve(state,'checkpoint-test-choice.json'))):undefined;
if(submitTestChoice&&JSON.stringify(testChoice)!=='{"selection":"b"}')throw Error('This bounded test expects only synthetic selection b');
const working=checkpoint||process.argv.includes('--working');
const openWorking=checkpoint||process.argv.includes('--open-working');
if(openWorking&&!working)throw Error('Primary working-view check requires --working');
const evidence=JSON.parse(readFileSync(resolve(state,checkpoint?'checkpoint-probe.json':'native-editor-reconciled.json')));
const scope=checkpoint?{workspace_id:evidence.workspace.workspace_id,session_id:evidence.workspace.session_id,path:evidence.source.path}:evidence.scope;
const preview=JSON.parse(readFileSync(resolve(state,'preview.json')));
const token=readFileSync(resolve(state,'.preview-api-token'),'utf8');
const bundle=readFileSync('prototypes/desktop-harness/native-editor.html','utf8');
const output=resolve(state,'browser-editor-'+Date.now());mkdirSync(output,{recursive:true});
const safe=value=>JSON.stringify(value).replaceAll('<','\\u003c');
let primaryArgs=scope;
let primaryResult={workspace:evidence.workspace,working_view_enabled:working};
async function workingContext(){
 const current=await sourceCall('GET');if(!current.response.ok)throw Error('Cannot read current source for exact primary view');
 const request={...scope,operation:'snapshot',expected_storage_digest:current.doc.storage_digest};
 if(checkpoint)request.run_id=evidence.start_receipt.run_id;
 const url=new URL('/api/workspace/process-interfaces'+(request.run_id?'/runs/'+encodeURIComponent(request.run_id):'/interaction'),preview.api_url);
 for(const key of ['session_id','path','expected_storage_digest'])url.searchParams.set(key,request[key]);
 const reply=await fetch(url,{headers:{Authorization:'Bearer '+token}});if(!reply.ok)throw Error('Cannot read exact primary process context');
 return {arguments:{request},result:{content:[],structuredContent:{workspace:evidence.workspace,working_view_enabled:true,snapshot:await reply.json()}}};
}
if(openWorking){const context=await workingContext();primaryArgs=context.arguments;primaryResult=context.result.structuredContent;}
const fixture=`<!doctype html><html><head><meta charset="utf-8"><title>Wright editor protocol fixture</title></head><body style="margin:0;background:#181818;color:#ddd;font:13px system-ui"><p style="margin:0;padding:10px">GB10 browser · simulated desktop host · real Wright source storage</p><iframe id="panel" title="Wright Workflows" style="border:0;width:100%;height:calc(100vh - 38px)"></iframe><script>
const frame=document.getElementById('panel');window.calls=[];
window.addEventListener('message',async event=>{
 if(event.source!==frame.contentWindow)return;
 const message=event.data;const send=data=>frame.contentWindow.postMessage({jsonrpc:'2.0',...data},'*');
 if(message.method==='ui/initialize')send({id:message.id,result:{protocolVersion:'2026-01-26',hostInfo:{name:'wright-browser-fixture',version:'0.1.0'},hostCapabilities:{serverTools:{}},hostContext:{theme:'dark'}}});
 if(message.method==='ui/notifications/initialized'){send({method:'ui/notifications/tool-input',params:{arguments:${safe(primaryArgs)}}});send({method:'ui/notifications/tool-result',params:{content:[],structuredContent:${safe(primaryResult)}}});}
 if(message.method==='tools/call'){window.calls.push(message.params);try{const response=await fetch('/tool',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(message.params)});send({id:message.id,result:await response.json()});}catch{send({id:message.id,error:{code:-32000,message:'Fixture transport unavailable'}});}}
});frame.srcdoc=${safe(bundle)};
</script></body></html>`;
async function sourceCall(method,body){
 const url=new URL('/api/workspace/workflow-sources',preview.api_url);
 if(method==='GET'){url.searchParams.set('session_id',scope.session_id);url.searchParams.set('path',scope.path);}
 const response=await fetch(url,{method,headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},...(method==='PUT'?{body:JSON.stringify(body)}:{})});
 const doc=await response.json();
 return {response,doc};
}
const server=createServer(async(request,response)=>{
 try{
 if(request.method==='POST'&&request.url==='/tool'){
 let text='';for await(const chunk of request)text+=chunk;
 const {name,arguments:args}=JSON.parse(text);
 if(working&&['wright_process_ui_read','wright_process_ui_update'].includes(name)){
   const req=args.request;
   if(!req||Object.entries(scope).some(([key,value])=>req[key]!==value))throw Error('Fixture process scope denied');
   if(checkpoint){
     const interaction=evidence.checkpoint_snapshot.interactions.find(item=>item.kind==='input'&&item.state==='waiting');
     const read=name==='wright_process_ui_read'&&req.run_id===evidence.start_receipt.run_id;
     const answer=submitTestChoice&&name==='wright_process_ui_update'&&req.operation==='respond'&&req.checkpoint_id===interaction.checkpoint_id&&req.subject_digest===interaction.subject_digest&&JSON.stringify(req.value)===JSON.stringify(testChoice)&&req.auto!==true;
     if(!read&&!answer)throw Error('Checkpoint fixture permits exact-run reads and only its explicit scripted test choice');
   }
   const {workspace_id:_,operation,run_id,checkpoint_id,...body}=req;
   if(checkpoint&&operation==='representation'){
     const reference=req.reference;
     const expected=evidence.final_snapshot?.outputs.flatMap(output=>output.representations).some(item=>item.artifact_ref===reference?.artifact_ref&&item.sha256===reference?.sha256);
     if(!completed||!expected||req.preview)throw Error('Only recorded completed raw text representations are qualified here');
     const result=await fetch(new URL('/api/workspace/process-interfaces/representations/read',preview.api_url),{method:'POST',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},body:JSON.stringify({...body,run_id})});
     if(!result.ok)throw Error('Representation owner rejected exact read');
     const bytes=Buffer.from(await result.arrayBuffer());const media=result.headers.get('content-type').split(';',1)[0];
     if(bytes.length>1048576||result.headers.get('content-length')!==String(bytes.length)||result.headers.get('x-content-type-options')!=='nosniff'||result.headers.get('x-wright-artifact-sha256')!==reference.sha256||createHash('sha256').update(bytes).digest('hex')!==reference.sha256||!['text/plain','text/markdown','text/csv','application/json'].includes(media))throw Error('Recorded text identity was not confirmed');
     response.writeHead(200,{'Content-Type':'application/json'});response.end(JSON.stringify({content:[],structuredContent:{ok:true,document:{bytes_base64:bytes.toString('base64'),sha256:reference.sha256,media_type:media,size_bytes:bytes.length}}}));return;
   }
   if(checkpoint&&operation==='reasoning'){
     const saved=new URL('/api/workspace/process-interfaces/runs/'+encodeURIComponent(run_id),preview.api_url);
     for(const [key,value] of Object.entries(body))saved.searchParams.set(key,String(value));
     const authorized=await fetch(saved,{headers:{Authorization:'Bearer '+token}});if(!authorized.ok)throw Error('Exact run read denied');
     const url=new URL('/api/desktop/reasoning',preview.api_url);url.searchParams.set('workspace_id',scope.workspace_id);url.searchParams.set('session_id',scope.session_id);
     const read=await fetch(url,{headers:{Authorization:'Bearer '+token}});if(!read.ok)throw Error('Handoff read unavailable');
     const tasks=(await read.json()).filter(row=>row.request?.run_id===run_id);
     response.writeHead(200,{'Content-Type':'application/json'});response.end(JSON.stringify({content:[],structuredContent:{ok:true,document:tasks}}));return;
   }
   const paths={snapshot:run_id?'/runs/'+encodeURIComponent(run_id):'/interaction',inputs:'/inputs',readiness:'/readiness',...(submitTestChoice?{respond:'/interactions/'+encodeURIComponent(checkpoint_id)+'/response'}:{})};
   if(!paths[operation]||(name==='wright_process_ui_read')!==(operation==='snapshot'))throw Error('Fixture exposes preparation only; no run/action forwarding');
   const method=operation==='snapshot'?'GET':'POST';
   const url=new URL('/api/workspace/process-interfaces'+paths[operation],preview.api_url);
   if(method==='GET')for(const [key,value] of Object.entries(body))url.searchParams.set(key,String(value));
   const result=await fetch(url,{method,headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},...(method==='POST'?{body:JSON.stringify(body)}:{})});
   const doc=await result.json();
   response.writeHead(200,{'Content-Type':'application/json'});response.end(JSON.stringify({content:[],structuredContent:result.ok?{ok:true,document:doc}:{ok:false,http_status:result.status,reason:{code:result.status===409?'SUBJECT_STALE':'CAPABILITY_UNAVAILABLE',message:'Wright did not confirm this preparation.',correction:'Inspect the exact source or connection.'}}}));return;
 }
 if(!['wright_workflow_read','wright_workflow_save'].includes(name)||Object.entries(scope).some(([key,value])=>args[key]!==value))throw Error('Fixture scope denied');
 const method=name==='wright_workflow_read'?'GET':'PUT';const {workspace_id:_,...body}=args;
 const result=await sourceCall(method,body);
 const value=result.response.ok?(method==='PUT'?{ok:true,document:result.doc}:result.doc):{ok:false,error:{code:result.response.status===409?'WORKFLOW_SOURCE_CONFLICT':'SOURCE_UNAVAILABLE',outcome_known:result.response.status<500,message:'Wright rejected this save; your local draft is kept.'}};
 response.writeHead(200,{'Content-Type':'application/json'});response.end(JSON.stringify({content:[],structuredContent:value}));return;
 }
 response.writeHead(200,{'Content-Type':'text/html;charset=utf-8'});response.end(fixture);
 }catch{response.writeHead(400,{'Content-Type':'application/json'});response.end(JSON.stringify({content:[],isError:true}));}
});
await new Promise(done=>server.listen(0,'127.0.0.1',done));
const browser=await chromium.launch({headless:true});
const passed=[];let page;
try{
 page=await browser.newPage({viewport:{width:1100,height:820}});page.setDefaultTimeout(8000);
 const errors=[];page.on('pageerror',error=>errors.push(error.message));
 await page.goto(`http://127.0.0.1:${server.address().port}`);
 const frame=page.frameLocator('#panel');
 if(checkpoint){
   await expect(frame.getByTestId('common-process-view')).toBeVisible();
   if(completed){
     await expect(frame.getByText('Process completed',{exact:true})).toBeVisible();
     await frame.getByRole('button',{name:'Open file',exact:true}).nth(1).click();
     await expect(frame.getByText(/Carry forward alternative b, exactly as supplied/)).toBeVisible();
     await page.screenshot({path:resolve(output,'native-completed-owned-result-fixture.png')});
     await page.reload();await expect(frame.getByText('Process completed',{exact:true})).toBeVisible();
     const observed=await workingContext();const snapshot=observed.result.structuredContent.snapshot;
     expect(snapshot.context.run_id).toBe(evidence.start_receipt.run_id);expect(snapshot.outputs).toEqual(evidence.final_snapshot.outputs);
     const calls=await page.evaluate(()=>window.calls);expect(calls.some(call=>call.name==='wright_process_ui_update')).toBe(false);
     expect(errors).toEqual([]);passed.push('completed exact run, actual recorded text file displayed with verified bytes, reload without write/replay');
     writeFileSync(resolve(output,'report.json'),JSON.stringify({boundary:'GB10 browser simulated MCP App host; completed actual digital fixture and saved output',native_desktop_verified:false,actual_user_input:false,engineering_approval:false,passed,scope,run_id:snapshot.context.run_id,source_digest:snapshot.context.process.source_digest,calls,errors},null,2));
     console.log(JSON.stringify({passed,output}));
   } else {
   await expect(frame.getByLabel('selection (required)',{exact:true})).toBeVisible();
   await expect(frame.getByRole('button',{name:'Submit response',exact:true})).toBeVisible();
   await page.screenshot({path:resolve(output,'native-declared-input-fixture.png')});
   await page.reload();await expect(frame.getByLabel('selection (required)',{exact:true})).toBeVisible();
   const observed=await workingContext();const snapshot=observed.result.structuredContent.snapshot;
   expect(snapshot.state).toBe('waiting_human');expect(snapshot.context.run_id).toBe(evidence.start_receipt.run_id);expect(snapshot.outputs).toEqual(evidence.checkpoint_snapshot.outputs);
   passed.push('exact durable declared-input view, reload and stable prior outputs; no response/restart/cancel');
   if(submitTestChoice){
     await frame.getByLabel('selection (required)',{exact:true}).selectOption({label:'b'});
     await frame.getByRole('button',{name:'Submit response',exact:true}).click();
     await expect.poll(async()=> (await workingContext()).result.structuredContent.snapshot.state,{timeout:15000}).toBe('running');
     await expect(frame.getByText('Waiting for desktop chat',{exact:true})).toBeVisible({timeout:15000});
     await page.screenshot({path:resolve(output,'native-test-choice-waiting-for-chat.png')});
     passed.push('explicit scripted b submitted once through common UI against exact input subject; same run waits for desktop chat');
   }
   const calls=await page.evaluate(()=>window.calls);const changes=calls.filter(call=>call.name==='wright_process_ui_update');
   expect(changes.length).toBe(submitTestChoice?1:0);if(submitTestChoice)expect(changes[0].arguments.request.operation).toBe('respond');
   expect(errors).toEqual([]);
   writeFileSync(resolve(output,'report.json'),JSON.stringify({boundary:'GB10 browser simulated MCP App host; real declared-input durable run',native_desktop_verified:false,scripted_test_choice:testChoice??null,actual_user_input:false,engineering_approval:false,passed,scope,run_id:snapshot.context.run_id,source_digest:snapshot.context.process.source_digest,calls,errors},null,2));
   console.log(JSON.stringify({passed,output}));
   }
 } else {
 if(openWorking){await expect(frame.getByTestId('common-process-view')).toBeVisible();await frame.getByRole('button',{name:'Open workflow',exact:true}).click();passed.push('primary process opener reads exact preparing context with null run id');}
 await expect(frame.getByTestId('workflow-recovery-source-editor')).toHaveCount(0);
 await expect(frame.getByTestId('workflow-recovery-save')).toBeVisible();
 expect(await frame.locator('.native-workflow-panel').count()).toBe(1);
 passed.push('official App SDK initializes and reads accepted source');
 await frame.getByTestId('workflow-recovery-view-code').click();
 const editor=frame.getByTestId('workflow-recovery-source-editor');await expect(editor).toContainText('');
 const before=await editor.inputValue();
 let savedTitle=before.includes('name: \"Native panel saved edit\"')?'Saved panel workflow':'Native panel saved edit';
 await editor.fill(before.replace(/^  name: \"[^\"]+\"/m, '  name: '+JSON.stringify(savedTitle)));
 await frame.getByTestId('workflow-recovery-source-apply').click();
 await expect(frame.getByTestId('workflow-recovery-save')).toBeEnabled();
 await frame.getByTestId('workflow-recovery-save').click();
 await expect(frame.getByTestId('workflow-recovery-save-status')).toHaveText('Saved');
 let accepted=await sourceCall('GET');expect(accepted.doc.source).toContain(savedTitle);expect(accepted.doc.layout_revision).toBeGreaterThan(0);
 passed.push('shared Source edit/apply/save and Wright source/layout readback');
 await page.reload();
 if(openWorking){
   await expect(frame.getByText("This run's source changed. Reopen its exact accepted workflow; no action was repeated.",{exact:true})).toBeVisible();
   const context=await workingContext();
   await page.evaluate(context=>{const child=document.getElementById('panel').contentWindow;child.postMessage({jsonrpc:'2.0',method:'ui/notifications/tool-input',params:{arguments:context.arguments}},'*');child.postMessage({jsonrpc:'2.0',method:'ui/notifications/tool-result',params:context.result},'*');},context);
   await expect(frame.getByTestId('common-process-view')).toBeVisible();await frame.getByRole('button',{name:'Open workflow',exact:true}).click();
   passed.push('cached stale primary digest is rejected; explicit new source subject reopens');
 }
 await frame.getByTestId('workflow-recovery-view-code').click();
 await expect(editor).toHaveValue(accepted.doc.source);
 passed.push('panel reload restores exact accepted source without save replay');
 await frame.getByTestId('workflow-recovery-view-diagram').click();
 await page.screenshot({path:resolve(output,'shared-native-editor-fixture.png')});
 if(working){
   // Make an actual command after reload so return can prove retained Undo/Redo.
   await frame.getByTestId('workflow-recovery-view-code').click();savedTitle+=' retained';
   await editor.fill(accepted.doc.source.replace(/^  name: \"[^\"]+\"/m,'  name: '+JSON.stringify(savedTitle)));
   await frame.getByTestId('workflow-recovery-source-apply').click();await frame.getByTestId('workflow-recovery-save').click();
   await expect(frame.getByTestId('workflow-recovery-save-status')).toHaveText('Saved');accepted=await sourceCall('GET');
   await frame.getByTestId('workflow-recovery-view-diagram').click();
   await frame.getByRole('button',{name:'Run and results',exact:true}).click();
   await expect(frame.getByTestId('common-process-view')).toBeVisible();
   await frame.getByText('Saved defaults (1)',{exact:true}).click();
   const input=frame.getByLabel('Brief (required)',{exact:true});
   await expect(input).toBeVisible();await input.fill('A digital comparison for the saved native-panel workflow.');
   await frame.getByRole('button',{name:'Open workflow',exact:true}).click();
   await expect(frame.getByText('Finish or reconcile the pending change before leaving this working view.')).toBeVisible();
   await frame.getByRole('button',{name:'Prepare and check inputs',exact:true}).click();
   await expect.poll(()=>page.evaluate(()=>window.calls.filter(c=>c.name==='wright_process_ui_update'&&c.arguments.request.operation==='readiness').length)).toBe(1);
   await expect(frame.getByRole('button',{name:'Prepare and check inputs',exact:true})).toBeEnabled();
   await page.screenshot({path:resolve(output,'native-working-preparation-fixture.png')});
   await frame.getByRole('button',{name:'Open workflow',exact:true}).click();
   await expect(frame.getByTestId('workflow-recovery-save')).toBeVisible();
   await frame.getByRole('button',{name:'Run and results',exact:true}).click();
   await expect(frame.getByTestId('common-process-view')).toBeVisible();
   const calls=await page.evaluate(()=>window.calls);
   expect(calls.filter(c=>c.name==='wright_process_ui_update').map(c=>c.arguments.request.operation)).toEqual(['inputs','readiness']);
   await frame.getByRole('button',{name:'Open workflow',exact:true}).click();
   await expect(frame.getByTestId('workflow-recovery-undo')).toBeEnabled();
   await frame.getByTestId('workflow-recovery-undo').click();
   await frame.getByTestId('workflow-recovery-redo').click();
   await frame.getByTestId('workflow-recovery-view-code').click();
   await expect(editor).toHaveValue(accepted.doc.source);
   passed.push('saved editor to real common preparation, dirty-input guard, exact owner inputs/readiness, return/reopen without replay or run');
 }
 await page.evaluate(()=>document.getElementById('panel').contentWindow.postMessage({jsonrpc:'2.0',method:'ui/notifications/host-context-changed',params:{theme:'light',styles:{variables:{'--color-background-primary':'#fff','--color-text-primary':'#202020'}}}},'*'));
 await expect.poll(()=>frame.locator('.native-workflow-panel').evaluate(el=>getComputedStyle(el).backgroundColor)).toBe('rgb(255, 255, 255)');
 await page.setViewportSize({width:700,height:800});
 await expect(frame.getByTestId('workflow-recovery-save')).toBeVisible();
 await page.screenshot({path:resolve(output,'shared-native-editor-light-narrow.png')});
 passed.push('host light theme and narrow panel actions');
 await frame.getByTestId('workflow-recovery-view-select').selectOption('code');await editor.fill(accepted.doc.source.replace(savedTitle,'Retained local draft'));await frame.getByTestId('workflow-recovery-source-apply').click();
 const external=await sourceCall('PUT',{session_id:scope.session_id,path:scope.path,source:accepted.doc.source.replace(savedTitle,'Other saved edit'),expected_storage_revision:accepted.doc.storage_revision,expected_storage_digest:accepted.doc.storage_digest,semantic_change_validated:true});expect(external.response.ok).toBe(true);
 await frame.getByTestId('workflow-recovery-save').click();
 await expect(frame.getByTestId('workflow-recovery-conflict-actions')).toBeVisible();
 expect(await editor.inputValue()).toContain('Retained local draft');
 expect((await sourceCall('GET')).doc.source).toContain('Other saved edit');
 passed.push('stale source rejection preserves local draft and accepted external edit');
 expect(errors).toEqual([]);
 writeFileSync(resolve(output,'report.json'),JSON.stringify({boundary:'GB10 browser simulated MCP App host; real isolated Wright source owner',native_desktop_verified:false,passed,scope,errors},null,2));
 console.log(JSON.stringify({passed,output}));
 }
}catch(error){if(page)await page.screenshot({path:resolve(output,'failure.png')});writeFileSync(resolve(output,'failure.json'),JSON.stringify({passed,error:String(error)},null,2));throw error;
}finally{await browser.close();await new Promise(done=>server.close(done));}
