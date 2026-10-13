// Simulated MCP App host with real isolated Wright source storage. Not Windows acceptance.
import {createServer} from 'node:http';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {chromium,expect} from '@playwright/test';
const state=resolve(process.argv[2]);
const evidence=JSON.parse(readFileSync(resolve(state,'native-editor-reconciled.json')));
const scope=evidence.scope;
const preview=JSON.parse(readFileSync(resolve(state,'preview.json')));
const token=readFileSync(resolve(state,'.preview-api-token'),'utf8');
const bundle=readFileSync('prototypes/desktop-harness/native-editor.html','utf8');
const output=resolve(state,'browser-editor-'+Date.now());mkdirSync(output,{recursive:true});
const safe=value=>JSON.stringify(value).replaceAll('<','\\u003c');
const fixture=`<!doctype html><html><head><meta charset="utf-8"><title>Wright editor protocol fixture</title></head><body style="margin:0;background:#181818;color:#ddd;font:13px system-ui"><p style="margin:0;padding:10px">GB10 browser · simulated desktop host · real Wright source storage</p><iframe id="panel" title="Wright Workflows" style="border:0;width:100%;height:calc(100vh - 38px)"></iframe><script>
const frame=document.getElementById('panel');window.calls=[];
window.addEventListener('message',async event=>{
 if(event.source!==frame.contentWindow)return;
 const message=event.data;const send=data=>frame.contentWindow.postMessage({jsonrpc:'2.0',...data},'*');
 if(message.method==='ui/initialize')send({id:message.id,result:{protocolVersion:'2026-01-26',hostInfo:{name:'wright-browser-fixture',version:'0.1.0'},hostCapabilities:{serverTools:{}},hostContext:{theme:'dark'}}});
 if(message.method==='ui/notifications/initialized'){send({method:'ui/notifications/tool-input',params:{arguments:${safe(scope)}}});send({method:'ui/notifications/tool-result',params:{content:[],structuredContent:{workspace:${safe(evidence.workspace)}}}});}
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
 await expect(frame.getByTestId('workflow-recovery-source-editor')).toHaveCount(0);
 await expect(frame.getByTestId('workflow-recovery-save')).toBeVisible();
 expect(await frame.locator('.native-workflow-panel').count()).toBe(1);
 passed.push('official App SDK initializes and reads accepted source');
 await frame.getByTestId('workflow-recovery-view-code').click();
 const editor=frame.getByTestId('workflow-recovery-source-editor');await expect(editor).toContainText('');
 const before=await editor.inputValue();
 const savedTitle=before.includes('name: \"Native panel saved edit\"')?'Saved panel workflow':'Native panel saved edit';
 await editor.fill(before.replace(/^  name: \"[^\"]+\"/m, '  name: '+JSON.stringify(savedTitle)));
 await frame.getByTestId('workflow-recovery-source-apply').click();
 await expect(frame.getByTestId('workflow-recovery-save')).toBeEnabled();
 await frame.getByTestId('workflow-recovery-save').click();
 await expect(frame.getByTestId('workflow-recovery-save-status')).toHaveText('Saved');
 const accepted=await sourceCall('GET');expect(accepted.doc.source).toContain(savedTitle);expect(accepted.doc.layout_revision).toBeGreaterThan(0);
 passed.push('shared Source edit/apply/save and Wright source/layout readback');
 await page.reload();await frame.getByTestId('workflow-recovery-view-code').click();
 await expect(editor).toHaveValue(accepted.doc.source);
 passed.push('panel reload restores exact accepted source without save replay');
 await frame.getByTestId('workflow-recovery-view-diagram').click();
 await page.screenshot({path:resolve(output,'shared-native-editor-fixture.png')});
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
}catch(error){if(page)await page.screenshot({path:resolve(output,'failure.png')});writeFileSync(resolve(output,'failure.json'),JSON.stringify({passed,error:String(error)},null,2));throw error;
}finally{await browser.close();await new Promise(done=>server.close(done));}
