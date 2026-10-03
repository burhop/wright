import { chromium, expect } from '@playwright/test';
import { readFileSync, writeFileSync, appendFileSync, mkdirSync, existsSync } from 'node:fs';
import path from 'node:path';
import {spawnSync} from 'node:child_process';

const privateRoot = path.resolve('.local-run/process-interfaces-083/t037-theme-handshake-001');
const proof = JSON.parse(readFileSync(path.join(privateRoot, 'browser-context.json'), 'utf8'));
const root = path.resolve('artifacts/ui-walkthrough/process-interfaces-083-hosting/20261003T034435Z-theme-handshake-001');
if (existsSync(root)) throw new Error('Preserve the previous walkthrough; select a fresh root');
for (const dir of ['playwright','screenshots/raw','screenshots/annotated','trace']) mkdirSync(path.join(root, dir), {recursive:true});
const status = {title:'Saved engineering interfaces inherit Wright theme and reconnect their frame',summary:'Actual settings controls and saved model-created interfaces; no process start, review or global preference save.',overall:'pending',updated:new Date().toISOString(),manualSteps:[
 {label:'Open interface',instruction:'Open the saved Heat or Focus-wheel working-interface link.'},
 {label:'Choose light theme',instruction:'Click Back to Dashboard, then Settings. Choose Light Theme. Leave Save Preferences untouched.'},
 {label:'Return to interface',instruction:'Use browser Back twice to return to the saved working interface.'},
 {label:'Reload frame',instruction:'Reload the embedded page using the browser frame-reload action. Inspect the same exact results.'},
 {label:'Restore theme',instruction:'Repeat the Settings route, choose Dark Theme, then return. Leave all reviews unchanged.'},
],steps:[]};
const escape = value => String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function publish() {
  status.updated = new Date().toISOString();
  writeFileSync(path.join(root,'status.json'),JSON.stringify(status,null,2));
  writeFileSync(path.join(root,'report.html'),`<!doctype html><html><head><meta charset="utf-8"><title>${escape(status.title)}</title><style>body{font:16px system-ui;max-width:1100px;margin:24px auto;background:#101922;color:#e8f4f7}section{padding:18px;border:1px solid #647486;margin:16px 0}.pass{border-color:#64bda4}.blocked{border-color:#ee7373}img{max-width:100%}a{color:#7fe0cb}</style></head><body><h1>${escape(status.title)}</h1><p>${escape(status.summary)}</p><p>Status: ${escape(status.overall)}</p><h2>Manual steps</h2><ol>${status.manualSteps.map(s=>`<li>${escape(s.instruction)}</li>`).join('')}</ol>${status.steps.map(s=>`<section class="${s.state}"><h2>${escape(s.label)} Â· ${escape(s.state)}</h2><p>${escape(s.summary)}</p><p>Expected: ${escape(s.expected)}</p><p>Actual: ${escape(s.actual)}</p>${['raw','annotated'].filter(k=>s[k]).map(k=>`<p>${k}<a class="image-button" href="${escape(s[k])}" onclick="event.preventDefault();document.getElementById('full-image').src=this.href;document.getElementById('image-dialog').showModal()"><img src="${escape(s[k])}" alt="${escape(s.label)} ${k}"></a></p>`).join('')}</section>`).join('')}<dialog id="image-dialog"><button onclick="document.getElementById('image-dialog').close()">Close</button><img id="full-image" style="max-width:none" alt="Full-size walkthrough evidence"></dialog></body></html>`);
}
writeFileSync(path.join(root,'progress.md'),'# Latest saved Heat output and navigation continuation\n\nPrepared before navigation. Browser trace remains in the private proof root because authentication headers are sensitive.\n');
publish();
writeFileSync(path.join(root,'playwright','workspace-entry.mjs'),readFileSync(new URL(import.meta.url)));
const browser = await chromium.launch({headless:true});
const context = await browser.newContext({viewport:{width:1440,height:1000}});
await context.addCookies([{name:'wright_session',value:proof.browser_cookie,url:proof.frontend_url+'/api',httpOnly:true,sameSite:'Strict'}]);
await context.tracing.start({screenshots:true,snapshots:true,sources:true});
const page = await context.newPage();
const diagnostics={presentations:[],controlPlane:[],console:[],pageErrors:[],failedResponses:[],mutations:[],representationHeaders:[],contexts:[]};
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



const cases=JSON.parse(readFileSync(path.join(privateRoot,'cases.json'),'utf8'));
const frame=page.locator('[data-testid="surface-panel-host"]:visible').frameLocator('iframe');
function observe(){
  const reply=spawnSync(path.resolve('.venv/Scripts/python.exe'),[path.resolve('.local-run/process-interfaces-083/t034-observe-pagehide-proof-001.py')],{encoding:'utf8'});
  if(reply.status!==0)throw new Error('Immutable engineering/UI observation failed: '+reply.stderr);
  const value=JSON.parse(reply.stdout);diagnostics.controlPlane.push(value);return value;
}
async function current(item){
  await expect(frame.getByText('Connected to Wright.',{exact:true})).toBeVisible({timeout:120000});
  await expect(frame.locator('article[data-result-id]')).toHaveCount(item.expected_result_ids.length,{timeout:120000});
  expect(await frame.locator('article[data-result-id]').evaluateAll(rows=>rows.map(row=>row.dataset.resultId).sort())).toEqual(item.expected_result_ids);
  expect(diagnostics.contexts.at(-1)).toMatchObject({read_only:false,run_id:item.expected_result_ids[0].split(':')[0],ui_id:item.manifest.ui_id,revision_id:item.manifest.revision_id});
  observe();
}
async function chooseTheme(value){
  await page.getByTestId('activity-bar-back-btn').click();
  await page.getByTestId('nav-settings').click();
  await expect(page.getByTestId('settings-theme')).toBeEnabled({timeout:30000});
  await page.getByTestId('settings-theme').selectOption(value);
  await expect(page.locator('html')).toHaveAttribute('data-theme',value);
  await page.goBack();await page.goBack();
}
async function palette(){
  const parent=await page.locator('html').evaluate(element=>{
    const s=getComputedStyle(element);return {neutral:s.getPropertyValue('--color-neutral').trim(),primary:s.getPropertyValue('--color-primary').trim(),scheme:s.colorScheme};
  });
  const child=await frame.locator('html').evaluate(element=>{
    const s=getComputedStyle(element);return {neutral:s.getPropertyValue('--color-neutral').trim(),primary:s.getPropertyValue('--color-primary').trim(),scheme:s.colorScheme};
  });
  return {parent,child};
}
try{
  let index=0;
  for(const item of cases){
    await page.goto(item.url);await current(item);
    await record({id:'S'+String(++index).padStart(2,'0'),state:'pass',label:item.label+' saved working interface',summary:'The exact saved revision and engineering outputs are connected.',purpose:'Establish the real scoped working context.',action:'Open the saved working-interface link.',controls:['Back to Dashboard','Run inputs','Open assessment'],expected:'Exact saved revision and current results.',actual:item.expected_result_ids.length+' exact results in the current working context.',...await capture('S'+String(index).padStart(2,'0'),'Connected interface')});
    await chooseTheme('light');await current(item);
    await expect.poll(async()=>{const p=await palette();return p.child;},{timeout:30000}).toEqual((await palette()).parent);
    await record({id:'S'+String(++index).padStart(2,'0'),state:'pass',label:item.label+' light theme matches Wright',summary:'The saved isolated interface inherits Wright’s selected light theme.',purpose:'Check actual host theme transmission, not a screenshot-only approximation.',action:'Open Settings, choose Light Theme without saving preferences, and use browser Back twice.',controls:['Interface Theme','Run inputs','Open assessment'],expected:'Frame background/text theme tokens and color scheme match its parent.',actual:JSON.stringify(await palette()),...await capture('S'+String(index).padStart(2,'0'),'Light theme')});
    const count=diagnostics.contexts.length;
    const child=page.frames().find(value=>value!==page.mainFrame()&&value.url().includes('/__wright/'))??page.frames().find(value=>value!==page.mainFrame());
    expect(child).toBeTruthy();await child.evaluate(()=>location.reload());
    await expect.poll(()=>diagnostics.contexts.length,{timeout:30000}).toBeGreaterThan(count);
    await current(item);
    await expect.poll(async()=>{const p=await palette();return p.child;},{timeout:30000}).toEqual((await palette()).parent);
    await record({id:'S'+String(++index).padStart(2,'0'),state:'pass',label:item.label+' embedded page reconnects',summary:'The same presentation reconnects after its frame document reloads.',purpose:'Verify re-armed exact host handshake and current run binding.',action:'Reload the embedded page using the browser frame-reload operation.',controls:['Run inputs','Open assessment'],expected:'Fresh frame handshake, same saved UI/run/results and selected light theme.',actual:'New context read and '+item.expected_result_ids.length+' exact result identities restored; theme retained.',...await capture('S'+String(index).padStart(2,'0'),'Reconnected frame')});
    await chooseTheme('dark');await current(item);
    await expect.poll(async()=>{const p=await palette();return p.child;},{timeout:30000}).toEqual((await palette()).parent);
    await record({id:'S'+String(++index).padStart(2,'0'),state:'pass',label:item.label+' dark theme restored',summary:'Wright’s selected dark theme is restored without changing engineering work.',purpose:'Verify both supported theme values and no saved preference mutation.',action:'Use Settings to choose Dark Theme, then return through browser Back.',controls:['Interface Theme','Run inputs'],expected:'Exact dark parent/frame theme and unchanged outputs.',actual:JSON.stringify(await palette()),...await capture('S'+String(index).padStart(2,'0'),'Restored theme')});
    await page.goto('about:blank');
  }
  expect(diagnostics.console).toEqual([]);expect(diagnostics.pageErrors).toEqual([]);expect(diagnostics.failedResponses).toEqual([]);
  expect(diagnostics.mutations.some(row=>row.path==='/api/settings')).toBe(false);
  expect(diagnostics.mutations.filter(row=>row.path.includes('/process-interfaces/')&&!row.path.endsWith('/present')&&!row.path.endsWith('/presentations/close'))).toEqual([]);
  writeFileSync(path.join(privateRoot,'parity.json'),JSON.stringify({cases:cases.map(item=>({label:item.label,ui_id:item.manifest.ui_id,revision_id:item.manifest.revision_id,result_ids:item.expected_result_ids})),actual_settings_controls:true,preferences_saved:false,light_dark_theme:true,frame_reload:true,files_unchanged:observe().files_unchanged},null,2));
  status.overall='pass';
}catch(error){
  status.overall='blocked';
  await record({id:'STOP',state:'blocked',label:'Theme/handshake check stopped',summary:'The first unexpected interface behavior is preserved.',purpose:'Keep the real failure and exact current theme values.',action:'Stop at the current saved interface.',controls:['Use common working view','Reopen interface view'],expected:'Parent and saved interface have the same selected theme and exact run context.',actual:error.message,...await capture('STOP','Theme stopping point')});
  writeFileSync(path.join(privateRoot,'stop-observation.json'),JSON.stringify({url:cleanUrl(),palette:await palette(),files_unchanged:observe().files_unchanged},null,2));
}finally{
  publish();writeFileSync(path.join(root,'browser-diagnostics.json'),JSON.stringify(diagnostics,null,2));
  await context.tracing.stop({path:path.join(privateRoot,'theme-handshake-001-trace.zip')});await browser.close();
  console.log(JSON.stringify({status:status.overall,report:path.join(root,'report.html'),steps:status.steps.map(item=>({id:item.id,state:item.state,actual:item.actual}))}));
}
